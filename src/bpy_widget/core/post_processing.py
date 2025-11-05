"""
Extended post-processing effects for compositor - Blender 4.5 compatible

Uses CompositorChain for robust effect management with automatic
Viewer Node integration and effect chaining without overwrites.
"""
from typing import Optional, Tuple

import bpy
from loguru import logger

from .compositor_manager import get_compositor_chain


def setup_extended_compositor() -> bpy.types.NodeTree:
    """Setup compositor with extended post-processing capabilities

    DEPRECATED: Now uses CompositorChain internally.
    This function is kept for backward compatibility.

    Enables GPU acceleration for compositor if available (Blender 4.5+)
    """
    chain = get_compositor_chain()
    if not chain._initialized:
        chain.initialize(clear_existing=True)

    return chain.tree or bpy.context.scene.node_tree


def add_bloom_glare(intensity: float = 1.0, threshold: float = 1.0) -> Optional[bpy.types.Node]:
    """Add bloom/glare effect to the compositor chain.

    The effect will automatically:
    - Connect to previous effects in chain
    - Route to both Composite and Viewer outputs
    - Stack with other effects (no overwrites)

    Args:
        intensity: Bloom/glare intensity (0.0-2.0, default 1.0)
        threshold: Threshold for glow detection (0.0-100.0, default 1.0)

    Returns:
        The created Glare node, or None if setup fails
    """
    try:
        chain = get_compositor_chain()

        # Initialize if needed
        if not chain._initialized:
            chain.initialize()

        # Create glare node
        glare = chain.tree.nodes.new('CompositorNodeGlare')
        glare.glare_type = 'FOG_GLOW'
        glare.quality = 'HIGH'
        glare.threshold = threshold
        glare.mix = intensity

        # Add to chain (automatically connects)
        chain.add_effect(glare, name="Bloom_Glare")

        return glare

    except Exception as e:
        logger.error(f"Failed to add bloom/glare effect: {e}")
        return None


def add_color_correction(
    brightness: float = 0.0,
    contrast: float = 0.0,
    saturation: float = 1.0,
    gain: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    gamma: float = 1.0
) -> Optional[bpy.types.Node]:
    """Add color correction effect chain to compositor.

    Creates 3 nodes (Brightness/Contrast → HueSat → ColorBalance) that
    are automatically chained together and connected to outputs.

    Args:
        brightness: Brightness adjustment (-100 to 100, default 0)
        contrast: Contrast adjustment (-100 to 100, default 0)
        saturation: Saturation multiplier (0.0-2.0, default 1.0)
        gain: RGB gain tuple (0.0-2.0 each, default 1.0)
        gamma: Gamma correction (0.5-2.0, default 1.0)

    Returns:
        The final ColorBalance node (root of the color correction chain)
    """
    try:
        chain = get_compositor_chain()

        # Initialize if needed
        if not chain._initialized:
            chain.initialize()

        # Create color correction chain
        # Create nodes first, then set values, then link
        bright_contrast = chain.tree.nodes.new('CompositorNodeBrightContrast')
        hue_sat = chain.tree.nodes.new('CompositorNodeHueSat')
        color_balance = chain.tree.nodes.new('CompositorNodeColorBalance')
        
        # Set node properties BEFORE linking (prevents RNA errors)
        try:
            bright_contrast.inputs['Bright'].default_value = brightness
            bright_contrast.inputs['Contrast'].default_value = contrast
        except Exception:
            pass  # Some nodes may not have these inputs
        
        try:
            hue_sat.inputs['Saturation'].default_value = saturation
        except Exception:
            pass
        
        try:
            color_balance.correction_method = 'LIFT_GAMMA_GAIN'
            color_balance.gain = gain
            color_balance.gamma = (gamma, gamma, gamma)
        except Exception:
            pass

        # Position nodes
        bright_contrast.location = (200, 0)
        hue_sat.location = (400, 0)
        color_balance.location = (600, 0)

        # Chain them: BrightContrast → HueSat → ColorBalance
        chain.tree.links.new(bright_contrast.outputs['Image'], hue_sat.inputs['Image'])
        chain.tree.links.new(hue_sat.outputs['Image'], color_balance.inputs['Image'])

        # Connect final output to Composite and Viewer
        chain.tree.links.new(color_balance.outputs['Image'], chain.composite.inputs['Image'])
        chain.tree.links.new(color_balance.outputs['Image'], chain.viewer.inputs['Image'])

        # Add to chain tracking
        chain.effect_chain.append(bright_contrast)
        chain.effect_chain.append(hue_sat)
        chain.effect_chain.append(color_balance)

        return color_balance

    except Exception as e:
        logger.error(f"Failed to add color correction: {e}")
        return None


def add_vignette(amount: float = 0.3, center: Tuple[float, float] = (0.5, 0.5)) -> Optional[bpy.types.Node]:
    """Add vignette effect to compositor chain.

    Creates vignette using Ellipse Mask → Invert → Mix blend.
    Automatically chains with other effects.

    Args:
        amount: Vignette strength (0.0-1.0, default 0.3)
        center: Center point as (x, y) tuple (0.0-1.0, default 0.5, 0.5)

    Returns:
        The Mix node controlling vignette blending
    """
    try:
        chain = get_compositor_chain()

        # Initialize if needed
        if not chain._initialized:
            chain.initialize()

        # Create vignette nodes
        ellipse = chain.tree.nodes.new('CompositorNodeEllipseMask')
        ellipse.x = center[0]
        ellipse.y = center[1]
        ellipse.width = 1.0
        ellipse.height = 0.75

        invert = chain.tree.nodes.new('CompositorNodeInvert')

        mix = chain.tree.nodes.new('CompositorNodeMixRGB')
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Fac'].default_value = amount

        # Chain internally: Ellipse → Invert
        chain.tree.links.new(ellipse.outputs['Mask'], invert.inputs['Color'])

        # Add to chain (will connect mix to previous output)
        chain.add_effect(mix, name="Vignette")

        # Update internal connections
        # Find last node before mix in effect_chain
        mix_index = chain.effect_chain.index(mix)
        if mix_index > 0:
            prev_node = chain.effect_chain[mix_index - 1]
        else:
            prev_node = chain.render_layers

        # Connect: previous → mix image input, invert mask → mix mask input
        prev_output = prev_node.outputs.get('Image') or prev_node.outputs[0]

        # Remove old links to mix from prev_node
        for link in list(chain.tree.links):
            if link.to_node == mix and link.from_node == prev_node:
                chain.tree.links.remove(link)

        # Connect properly: image to Image input, mask to second Image (Fac)
        chain.tree.links.new(prev_output, mix.inputs[1])  # Original image
        chain.tree.links.new(invert.outputs['Color'], mix.inputs[2])  # Inverted mask

        return mix

    except Exception as e:
        logger.error(f"Failed to add vignette: {e}")
        return None


def add_film_grain(amount: float = 0.05) -> Optional[bpy.types.Node]:
    """Add film grain effect to compositor chain.

    Args:
        amount: Grain strength (0.0-1.0, default 0.05)

    Returns:
        The Mix node controlling grain blending
    """
    try:
        chain = get_compositor_chain()

        # Initialize if needed
        if not chain._initialized:
            chain.initialize()

        # Create noise texture
        texture = chain.tree.nodes.new('CompositorNodeTexture')

        # Create new texture if needed
        if not texture.texture:
            tex = bpy.data.textures.new("FilmGrain", type='NOISE')
            tex.noise_scale = 0.1
            texture.texture = tex

        # Mix node for grain
        mix = chain.tree.nodes.new('CompositorNodeMixRGB')
        mix.blend_type = 'OVERLAY'
        mix.inputs['Fac'].default_value = amount

        # Add to chain (handles main connection)
        chain.add_effect(mix, name="FilmGrain")

        # Connect texture to mix
        chain.tree.links.new(texture.outputs['Color'], mix.inputs[2])  # Noise as second input

        return mix

    except Exception as e:
        logger.error(f"Failed to add film grain: {e}")
        return None


def add_chromatic_aberration(amount: float = 0.001) -> Optional[bpy.types.Node]:
    """Add chromatic aberration effect"""
    tree = bpy.context.scene.node_tree
    if not tree:
        return None
    
    nodes = tree.nodes
    links = tree.links
    
    # Find composite and source
    composite = None
    source_socket = None
    
    for node in nodes:
        if node.type == 'COMPOSITE':
            composite = node
            break
    
    if not composite:
        return None
    
    # Find current input
    for link in links:
        if link.to_node == composite and link.to_socket.name == 'Image':
            source_socket = link.from_socket
            links.remove(link)
            break
    
    if not source_socket:
        return None
    
    # Create lens distortion node
    lens = nodes.new('CompositorNodeLensdist')
    lens.location = (1100, 0)
    lens.use_projector = False
    lens.inputs['Distort'].default_value = 0.0
    lens.inputs['Dispersion'].default_value = amount
    
    # Connect
    links.new(source_socket, lens.inputs['Image'])
    links.new(lens.outputs['Image'], composite.inputs['Image'])
    
    return lens


def add_motion_blur(samples: int = 8, shutter: float = 0.5) -> None:
    """Enable motion blur in render settings"""
    scene = bpy.context.scene
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = shutter
    
    if scene.render.engine == 'BLENDER_EEVEE_NEXT':
        scene.eevee.motion_blur_samples = samples
    elif scene.render.engine == 'CYCLES':
        scene.cycles.motion_blur_position = 'CENTER'


def add_depth_of_field(
    focus_object: Optional[bpy.types.Object] = None,
    focus_distance: float = 10.0,
    fstop: float = 2.8
) -> None:
    """Setup depth of field for camera"""
    camera = bpy.context.scene.camera
    if not camera or camera.type != 'CAMERA':
        print("No camera found in scene")
        return
    
    cam_data = camera.data
    cam_data.dof.use_dof = True
    cam_data.dof.aperture_fstop = fstop
    
    if focus_object:
        cam_data.dof.focus_object = focus_object
    else:
        cam_data.dof.focus_distance = focus_distance
    
    print(f"Depth of field enabled: f/{fstop}")


def add_sharpen(amount: float = 0.1) -> Optional[bpy.types.Node]:
    """Add sharpening filter - Simplified for Blender 4.5"""
    tree = bpy.context.scene.node_tree
    if not tree:
        return None
    
    nodes = tree.nodes
    links = tree.links
    
    # Find composite and source
    composite = None
    source_socket = None
    
    for node in nodes:
        if node.type == 'COMPOSITE':
            composite = node
            break
    
    if not composite:
        return None
    
    # Find current input
    for link in links:
        if link.to_node == composite and link.to_socket.name == 'Image':
            source_socket = link.from_socket
            links.remove(link)
            break
    
    if not source_socket:
        return None
    
    # Create filter node
    filter_node = nodes.new('CompositorNodeFilter')
    filter_node.location = (1000, 200)
    filter_node.filter_type = 'SHARPEN'
    
    # Create mix node to control amount
    mix = nodes.new('CompositorNodeMixRGB')
    mix.location = (1150, 200)
    mix.blend_type = 'MIX'
    mix.inputs['Fac'].default_value = amount
    
    # Connect
    links.new(source_socket, filter_node.inputs['Image'])
    links.new(source_socket, mix.inputs[1])  # Original
    links.new(filter_node.outputs['Image'], mix.inputs[2])  # Sharpened
    links.new(mix.outputs['Image'], composite.inputs['Image'])
    
    return mix


def reset_compositor() -> None:
    """Reset compositor to default state"""
    scene = bpy.context.scene
    if scene.use_nodes:
        tree = scene.node_tree
        tree.nodes.clear()
        
        # Create minimal setup
        render_layers = tree.nodes.new('CompositorNodeRLayers')
        composite = tree.nodes.new('CompositorNodeComposite')
        
        render_layers.location = (0, 0)
        composite.location = (300, 0)
        
        tree.links.new(render_layers.outputs['Image'], composite.inputs['Image'])
        
        print("Compositor reset to default")
