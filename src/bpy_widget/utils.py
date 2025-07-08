"""
Utility functions for Blender scene setup and rendering - CLEANED UP
"""
from typing import Tuple

import bpy

# Expose VFX libraries once
bpy.utils.expose_bundled_modules()

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
]


def clear_scene() -> None:
    """Clear all objects and orphaned data blocks from the scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Clean up orphaned data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)


def setup_camera(location: Tuple[float, float, float] = (6, -6, 5), 
                 rotation: Tuple[float, float, float] = (1.1, 0, 0.785)) -> bpy.types.Object:
    """Add and configure a camera object"""
    bpy.ops.object.camera_add(location=location)
    camera = bpy.context.object
    camera.rotation_euler = rotation
    bpy.context.scene.camera = camera
    return camera


def setup_lighting() -> bpy.types.Object:
    """Add a sun light to the scene."""
    bpy.ops.object.light_add(type='SUN', location=(3, -3, 5))
    sun = bpy.context.object
    sun.data.energy = 2.0
    sun.rotation_euler = (0.785, 0, 0.785)
    return sun


def create_material(
    name: str,
    base_color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    metallic: float = 0.0,
    roughness: float = 0.5
) -> bpy.types.Material:
    """Create a principled BSDF material with given properties."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # Create BSDF node
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (*base_color, 1.0)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    
    # Create output node
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (200, 0)
    
    # Link nodes
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat


def setup_world_background(color: Tuple[float, float, float] = (0.5, 0.6, 0.7), 
                          strength: float = 1.0) -> None:
    """Set up the world background with a solid color and strength."""
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    
    tree = world.node_tree
    tree.nodes.clear()
    
    # Background node
    bg_node = tree.nodes.new('ShaderNodeBackground')
    bg_node.inputs['Color'].default_value = (*color, 1.0)
    bg_node.inputs['Strength'].default_value = strength
    
    # Output node
    output = tree.nodes.new('ShaderNodeOutputWorld')
    
    # Link nodes
    tree.links.new(bg_node.outputs['Background'], output.inputs['Surface'])


def create_test_cube() -> bpy.types.Object:
    """Create a test cube with a bright material."""
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.object
    cube.name = "Cube"
    
    # Create and assign material
    mat = create_material("CubeMaterial", base_color=(1.0, 0.5, 0.1))
    cube.data.materials.clear()
    cube.data.materials.append(mat)
    
    return cube


def create_suzanne() -> bpy.types.Object:
    """Add Suzanne with chrome material on top of cube."""
    bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 2), scale=(1.2, 1.2, 1.2))
    suzanne = bpy.context.object
    suzanne.name = "Suzanne"
    
    # Smooth shading
    bpy.ops.object.shade_smooth()
    
    # Chrome material
    chrome_mat = create_material("Chrome", base_color=(0.8, 0.8, 0.8), metallic=1.0, roughness=0.0)
    suzanne.data.materials.clear()
    suzanne.data.materials.append(chrome_mat)
    
    return suzanne


def create_texture_image(name: str, width: int = 512, height: int = 512, 
                        color=(1.0, 1.0, 1.0, 1.0)) -> bpy.types.Image:
    """Create a new image texture with given name, size, and color."""
    img = bpy.data.images.new(name, width=width, height=height, alpha=True, float_buffer=False)
    pixels = [c for _ in range(width * height) for c in color]
    img.pixels = pixels
    return img


def create_texture_node(material: bpy.types.Material, image: bpy.types.Image) -> bpy.types.ShaderNodeTexImage:
    """Add an Image Texture node to the material and connect it to the BSDF base color."""
    if not material.use_nodes:
        material.use_nodes = True
    
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Create texture node
    tex_node = nodes.new('ShaderNodeTexImage')
    tex_node.image = image
    
    # Find BSDF node and connect
    bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf:
        links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
    
    return tex_node
