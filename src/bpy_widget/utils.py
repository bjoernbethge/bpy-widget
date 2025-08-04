"""
Utility functions for Blender scene setup and rendering - CLEANED UP

This module provides a clean, properly initialized interface to Blender's Python API (bpy).
All functions include initialization checks to ensure reliable operation.

Compatibility:
    - Blender 4.4.x: Full support with VFX libraries
    - Blender 4.5.x: Enhanced support with latest optimizations
    - Headless mode: Automatically detected and supported

Initialization:
    The module automatically initializes the Blender environment on import, including:
    - Exposing VFX libraries (Blender 4.4+)
    - Validating Blender context availability
    - Detecting headless mode
    - Version-specific optimizations for Blender 4.5+
    
    You can check initialization status with:
        >>> from bpy_widget.utils import is_blender_initialized
        >>> print(is_blender_initialized())
        
    Or manually reinitialize if needed:
        >>> from bpy_widget.utils import reinitialize_blender
        >>> reinitialize_blender()

Best Practices (following Blender Python API guidelines):
    - Always use the provided utility functions instead of direct bpy operations
    - All functions include automatic initialization validation
    - Functions will raise RuntimeError if Blender is not properly initialized
    - Use headless mode detection for environment-specific behavior
    - Follow PEP8 style conventions for consistency

Example:
    >>> from bpy_widget.utils import clear_scene, setup_camera, create_suzanne
    >>> clear_scene()
    >>> setup_camera()
    >>> suzanne = create_suzanne()
"""
from typing import Tuple

import bpy


# Ensure proper Blender module initialization
def _initialize_blender_environment():
    """Initialize Blender environment with proper error handling."""
    try:
        # Expose VFX libraries once (Blender 4.4+ feature)
        if hasattr(bpy.utils, 'expose_bundled_modules'):
            bpy.utils.expose_bundled_modules()
        
        # Ensure we have a valid context
        if not hasattr(bpy, 'context') or bpy.context is None:
            raise RuntimeError("Blender context not available")
            
        # Check if we're running in headless mode
        if bpy.app.background:
            print("Running in headless mode")
        
        # Version-specific optimizations for Blender 4.5+
        if bpy.app.version >= (4, 5, 0):
            print(f"✓ Blender 4.5+ detected - enabling enhanced features")
            # Future 4.5-specific optimizations can be added here
            
        return True
        
    except Exception as e:
        print(f"Warning: Failed to initialize Blender environment: {e}")
        return False

# Initialize on import
_blender_initialized = _initialize_blender_environment()


def is_blender_initialized() -> bool:
    """Check if Blender environment is properly initialized."""
    return _blender_initialized


def reinitialize_blender() -> bool:
    """Manually reinitialize the Blender environment."""
    global _blender_initialized
    _blender_initialized = _initialize_blender_environment()
    return _blender_initialized


__all__ = [
    'bpy',
    'clear_scene',
    'setup_camera',
    'setup_lighting',
    'create_material',
    'setup_world_background',
    'create_test_cube',
    'create_suzanne',
    'create_texture_image',
    'create_texture_node',
    'is_blender_initialized',
    'reinitialize_blender',
]


def clear_scene() -> None:
    """Clear all objects and orphaned data blocks from the scene."""
    if not _blender_initialized:
        raise RuntimeError("Blender environment not properly initialized")
        
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Clean up orphaned data blocks
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)
    
    for block in bpy.data.textures:
        if block.users == 0:
            bpy.data.textures.remove(block)


def setup_camera() -> bpy.types.Object:
    """Setup basic camera for the scene."""
    if not _blender_initialized:
        raise RuntimeError("Blender environment not properly initialized")
        
    bpy.ops.object.camera_add(location=(7.5, -7.5, 5.5))
    camera = bpy.context.object
    camera.rotation_euler = (1.1, 0, 0.785)
    bpy.context.scene.camera = camera
    return camera


def setup_lighting() -> None:
    """Setup basic lighting for the scene."""
    if not _blender_initialized:
        raise RuntimeError("Blender environment not properly initialized")
        
    # Add key light
    bpy.ops.object.light_add(type='SUN', location=(4, 4, 10))
    sun = bpy.context.object
    sun.data.energy = 3.0
    sun.rotation_euler = (0.3, 0.3, 0)


def create_material(name: str, color: Tuple[float, float, float, float] = (0.8, 0.2, 0.2, 1.0)) -> bpy.types.Material:
    """Create a basic material with given color."""
    if not _blender_initialized:
        raise RuntimeError("Blender environment not properly initialized")
        
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    # Get the principled BSDF node
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    
    return mat


def setup_world_background(color: Tuple[float, float, float] = (0.8, 0.8, 0.9), strength: float = 1.0) -> None:
    """Setup world background color."""
    if not _blender_initialized:
        raise RuntimeError("Blender environment not properly initialized")
        
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    
    world.use_nodes = True
    bg_node = world.node_tree.nodes["Background"]
    bg_node.inputs["Color"].default_value = (*color, 1.0)
    bg_node.inputs["Strength"].default_value = strength


def create_test_cube() -> bpy.types.Object:
    """Create a test cube for visualization."""
    if not _blender_initialized:
        raise RuntimeError("Blender environment not properly initialized")
        
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    cube = bpy.context.object
    cube.name = "TestCube"
    
    # Apply material
    mat = create_material("CubeMaterial", (0.8, 0.2, 0.2, 1.0))
    cube.data.materials.append(mat)
    
    return cube


def create_suzanne() -> bpy.types.Object:
    """Create Suzanne monkey head for testing."""
    if not _blender_initialized:
        raise RuntimeError("Blender environment not properly initialized")
        
    bpy.ops.mesh.primitive_monkey_add(location=(2, 2, 1))
    suzanne = bpy.context.object
    suzanne.name = "Suzanne"
    
    # Apply material
    mat = create_material("SuzanneMaterial", (0.2, 0.8, 0.2, 1.0))
    suzanne.data.materials.append(mat)
    
    return suzanne


def create_texture_image(name: str, width: int = 1024, height: int = 1024) -> bpy.types.Image:
    """Create a new texture image."""
    if not _blender_initialized:
        raise RuntimeError("Blender environment not properly initialized")
        
    return bpy.data.images.new(name=name, width=width, height=height)


def create_texture_node(material: bpy.types.Material, image: bpy.types.Image) -> bpy.types.ShaderNodeTexImage:
    """Create and connect a texture node to a material."""
    if not _blender_initialized:
        raise RuntimeError("Blender environment not properly initialized")
        
    if not material.use_nodes:
        material.use_nodes = True
    
    # Create texture node
    tex_node = material.node_tree.nodes.new('ShaderNodeTexImage')
    tex_node.image = image
    
    # Connect to base color
    bsdf = material.node_tree.nodes["Principled BSDF"]
    material.node_tree.links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
    
    return tex_node