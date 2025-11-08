"""
Compositor Manager - Central management for Node-Chains and Post-Processing

Provides a robust system for managing Blender compositor node trees,
with support for effect chaining, Viewer Node integration, and GPU acceleration.

Architecture:
    Render Layers
        ↓
    Effect 1 (e.g., Bloom)
        ↓
    Effect 2 (e.g., Color Correction)
        ↓
    Effect 3 (e.g., Vignette)
        ├─→ Composite Output (for final render)
        └─→ Viewer Output (for live preview)
"""

from typing import Any, Dict, List, Optional, Tuple

import bpy
from loguru import logger


class CompositorChain:
    """
    Manages a linked post-processing pipeline with Viewer Node support.

    Key features:
    - Automatic parallel routing to Composite and Viewer nodes
    - Effect chaining without overwrites
    - GPU compositing support (Blender 4.5+)
    - Robust node connection management
    """

    def __init__(self):
        """Initialize compositor chain (not fully set up until initialize() is called)"""
        self.scene = bpy.context.scene
        self.tree: Optional[bpy.types.NodeTree] = None
        self.render_layers: Optional[bpy.types.Node] = None
        self.composite: Optional[bpy.types.Node] = None
        self.viewer: Optional[bpy.types.Node] = None
        self.effect_chain: List[bpy.types.Node] = []  # Effects in order
        self._initialized = False

    def initialize(self, clear_existing: bool = True) -> None:
        """
        Initialize compositor with basic node structure.

        Args:
            clear_existing: If True, deletes existing compositor nodes and effects.
                          If False, preserves existing setup.

        Raises:
            RuntimeError: If scene is invalid
        """
        if not bpy.context.scene:
            raise RuntimeError("No active scene")

        # Always update scene reference (scene may have changed)
        self.scene = bpy.context.scene
        self.scene.use_nodes = True
        self.scene.render.use_compositing = True

        # Enable GPU compositing if available (Blender 4.5+)
        if hasattr(self.scene.render, 'use_compositor_gpu'):
            self.scene.render.use_compositor_gpu = True

        # Always get fresh tree reference (may have changed if scene was reset)
        self.tree = self.scene.node_tree
        
        # Validate tree is still valid
        if not self.tree or not hasattr(self.tree, 'nodes'):
            raise RuntimeError("CompositorNodeTree is invalid")

        if clear_existing:
            self.tree.nodes.clear()
            self.effect_chain.clear()

        # Create base nodes
        self.render_layers = self.tree.nodes.new('CompositorNodeRLayers')
        self.composite = self.tree.nodes.new('CompositorNodeComposite')
        self.viewer = self.tree.nodes.new('CompositorNodeViewer')

        # Position nodes for clarity
        self.render_layers.location = (0, 0)
        self.composite.location = (800, 0)
        self.viewer.location = (800, -300)

        # Initial connection: Render Layers → Composite & Viewer
        self.tree.links.new(
            self.render_layers.outputs['Image'],
            self.composite.inputs['Image']
        )
        self.tree.links.new(
            self.render_layers.outputs['Image'],
            self.viewer.inputs['Image']
        )

        self._initialized = True

    def add_effect(
        self,
        effect_node: bpy.types.Node,
        name: str = "",
        position_offset: Tuple[int, int] = (200, 0)
    ) -> bpy.types.Node:
        """
        Add effect node to the chain.

        Automatically connects:
        - Previous node output → Effect input
        - Effect output → Composite input (parallel)
        - Effect output → Viewer input (parallel)

        Args:
            effect_node: The compositor node to add
            name: Optional name for the node (for debugging)
            position_offset: Position offset from previous node (x, y)

        Returns:
            The added effect node

        Raises:
            RuntimeError: If chain not initialized
        """
        if not self._initialized:
            raise RuntimeError("Chain not initialized. Call initialize() first.")

        if not self.tree:
            raise RuntimeError("Node tree not found")

        if name:
            effect_node.name = name

        # Find previous node in chain
        if self.effect_chain:
            last_node = self.effect_chain[-1]
            x, y = last_node.location
        else:
            last_node = self.render_layers
            x, y = last_node.location

        # Position new node
        effect_node.location = (x + position_offset[0], y + position_offset[1])

        # Connect previous node output to effect input
        try:
            last_output = last_node.outputs.get('Image') or last_node.outputs[0]
            effect_input = effect_node.inputs.get('Image') or effect_node.inputs[0]
            self.tree.links.new(last_output, effect_input)
        except (IndexError, AttributeError) as e:
            logger.warning(f"Could not connect previous node to effect: {e}")
            return effect_node

        # Get effect output
        try:
            effect_output = effect_node.outputs.get('Image') or effect_node.outputs[0]
        except IndexError:
            logger.warning(f"Effect node has no Image output")
            return effect_node

        # Remove old connections to Composite and Viewer
        for link in list(self.tree.links):
            if link.to_node == self.composite and link.to_socket.name == 'Image':
                self.tree.links.remove(link)
            elif link.to_node == self.viewer and link.to_socket.name == 'Image':
                self.tree.links.remove(link)

        # Create new parallel connections (effect → Composite AND Viewer)
        self.tree.links.new(effect_output, self.composite.inputs['Image'])
        self.tree.links.new(effect_output, self.viewer.inputs['Image'])

        # Add to chain
        self.effect_chain.append(effect_node)

        # Trigger node update
        if hasattr(effect_node, 'update'):
            try:
                effect_node.update()
            except:
                pass  # Some nodes don't support update

        return effect_node

    def remove_effect(self, effect_node: bpy.types.Node) -> bool:
        """
        Remove effect from chain and reconnect surrounding nodes.

        Args:
            effect_node: The node to remove

        Returns:
            True if successfully removed, False otherwise
        """
        if effect_node not in self.effect_chain:
            return False

        if not self.tree:
            return False

        index = self.effect_chain.index(effect_node)

        # Find previous and next nodes in chain
        prev_node = self.effect_chain[index - 1] if index > 0 else self.render_layers
        next_node = self.effect_chain[index + 1] if index < len(self.effect_chain) - 1 else None

        # Remove node from tree
        self.tree.nodes.remove(effect_node)
        self.effect_chain.remove(effect_node)

        # Reconnect chain
        try:
            prev_output = prev_node.outputs.get('Image') or prev_node.outputs[0]

            if next_node:
                # Connect to next effect in chain
                next_input = next_node.inputs.get('Image') or next_node.inputs[0]
                self.tree.links.new(prev_output, next_input)
            else:
                # Last effect removed, connect to outputs
                self.tree.links.new(prev_output, self.composite.inputs['Image'])
                self.tree.links.new(prev_output, self.viewer.inputs['Image'])
        except (IndexError, AttributeError) as e:
            logger.warning(f"Could not reconnect chain after removal: {e}")

        return True

    def clear_effects(self) -> None:
        """
        Remove all effects while keeping base compositor setup.

        Restores direct connection from Render Layers to Composite & Viewer.
        """
        if not self.tree:
            return

        for effect in list(self.effect_chain):
            self.tree.nodes.remove(effect)

        self.effect_chain.clear()

        # Restore direct connections
        for link in list(self.tree.links):
            if (link.from_node == self.render_layers and
                link.to_node in (self.composite, self.viewer)):
                self.tree.links.remove(link)

        self.tree.links.new(
            self.render_layers.outputs['Image'],
            self.composite.inputs['Image']
        )
        self.tree.links.new(
            self.render_layers.outputs['Image'],
            self.viewer.inputs['Image']
        )

        logger.info("All effects cleared")

    def get_chain_info(self) -> Dict[str, Any]:
        """
        Get information about current compositor chain.

        Returns:
            Dictionary with:
            - initialized: Whether chain is set up
            - effect_count: Number of active effects
            - effects: List of effect node names
            - gpu_compositing: Whether GPU compositing is enabled
        """
        gpu_compositing = False
        if hasattr(self.scene.render, 'use_compositor_gpu'):
            gpu_compositing = self.scene.render.use_compositor_gpu

        return {
            'initialized': self._initialized,
            'effect_count': len(self.effect_chain),
            'effects': [node.name or node.type for node in self.effect_chain],
            'gpu_compositing': gpu_compositing
        }


# Global singleton instance
_compositor_chain: Optional[CompositorChain] = None


def get_compositor_chain() -> CompositorChain:
    """
    Get or create the global compositor chain instance.

    Returns:
        The global CompositorChain instance
    """
    global _compositor_chain
    
    # Check if chain exists and is still valid
    if _compositor_chain is not None:
        # Validate that the tree is still valid (scene may have been reset)
        try:
            if _compositor_chain.tree and hasattr(_compositor_chain.tree, 'nodes'):
                # Tree is valid, but check if scene changed
                if _compositor_chain.scene != bpy.context.scene:
                    # Scene changed, reset chain
                    _compositor_chain = None
                else:
                    # Tree exists and scene matches, but verify it's still accessible
                    _ = _compositor_chain.tree.nodes  # Test access
            else:
                # Tree is invalid, reset chain
                _compositor_chain = None
        except (ReferenceError, AttributeError, RuntimeError):
            # Tree was removed or invalidated, reset chain
            _compositor_chain = None
    
    if _compositor_chain is None:
        _compositor_chain = CompositorChain()
    
    return _compositor_chain


def reset_compositor_chain() -> None:
    """
    Reset the global compositor chain instance.

    Useful for testing or complete reinitialization.
    """
    global _compositor_chain
    _compositor_chain = None
