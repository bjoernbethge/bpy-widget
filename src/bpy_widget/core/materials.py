"""
Materials - Simple and functional
"""
import bpy
from typing import Tuple, Optional, Union, List


def create_material(name: str) -> bpy.types.Material:
    """Create a basic material with nodes"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    return mat


def create_simple_material(
    name: str,
    color: Tuple[float, float, float, float] = (0.8, 0.8, 0.8, 1.0)
) -> bpy.types.Material:
    """Create a simple material with just color"""
    mat = create_material(name)
    nodes = mat.node_tree.nodes
    
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs['Base Color'].default_value = color
    
    return mat


def create_emission_material(
    name: str,
    color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
    strength: float = 1.0
) -> bpy.types.Material:
    """Create an emission material"""
    mat = create_material(name)
    nodes = mat.node_tree.nodes
    
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs['Emission Color'].default_value = color
    bsdf.inputs['Emission Strength'].default_value = strength
    
    return mat


def create_glass_material(
    name: str,
    transmission: float = 1.0,
    ior: float = 1.45,
    roughness: float = 0.0,
    base_color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
) -> bpy.types.Material:
    """Create glass material"""
    mat = create_material(name)
    nodes = mat.node_tree.nodes
    
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs['Base Color'].default_value = base_color
    bsdf.inputs['Transmission Weight'].default_value = transmission
    bsdf.inputs['IOR'].default_value = ior
    bsdf.inputs['Roughness'].default_value = roughness
    
    return mat


def create_metal_material(
    name: str,
    base_color: Tuple[float, float, float, float] = (0.8, 0.8, 0.8, 1.0),
    roughness: float = 0.1,
    metallic: float = 1.0
) -> bpy.types.Material:
    """Create metal material"""
    mat = create_material(name)
    nodes = mat.node_tree.nodes
    
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs['Base Color'].default_value = base_color
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    
    return mat


def create_transparent_material(
    name: str,
    alpha: float = 0.5,
    base_color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
) -> bpy.types.Material:
    """Create transparent material"""
    mat = create_material(name)
    mat.blend_method = 'BLEND'
    nodes = mat.node_tree.nodes
    
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs['Base Color'].default_value = base_color
    bsdf.inputs['Alpha'].default_value = alpha
    
    return mat


def create_gradient_material(
    name: str,
    color1: Tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0),
    color2: Tuple[float, float, float, float] = (1.0, 0.0, 0.0, 1.0)
) -> bpy.types.Material:
    """Create material with gradient"""
    mat = create_material(name)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Add gradient texture
    tex_coord = nodes.new('ShaderNodeTexCoord')
    gradient = nodes.new('ShaderNodeTexGradient')
    color_ramp = nodes.new('ShaderNodeValToRGB')
    
    # Position nodes
    tex_coord.location = (-400, 0)
    gradient.location = (-200, 0)
    color_ramp.location = (0, 0)
    
    # Set colors
    color_ramp.color_ramp.elements[0].color = color1
    color_ramp.color_ramp.elements[1].color = color2
    
    # Connect nodes
    links.new(tex_coord.outputs['Generated'], gradient.inputs['Vector'])
    links.new(gradient.outputs['Fac'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], nodes['Principled BSDF'].inputs['Base Color'])
    
    return mat


def create_toon_material(
    name: str,
    base_color: Tuple[float, float, float, float] = (0.8, 0.8, 0.8, 1.0),
    roughness: float = 0.5
) -> bpy.types.Material:
    """Create toon-style material"""
    mat = create_material(name)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Clear existing
    nodes.clear()
    
    # Create nodes
    output = nodes.new('ShaderNodeOutputMaterial')
    diffuse = nodes.new('ShaderNodeBsdfDiffuse')
    color_ramp = nodes.new('ShaderNodeValToRGB')
    shader_to_rgb = nodes.new('ShaderNodeShaderToRGB')
    
    # Position
    diffuse.location = (-200, 0)
    shader_to_rgb.location = (0, 0)
    color_ramp.location = (200, 0)
    output.location = (400, 0)
    
    # Set values
    diffuse.inputs['Color'].default_value = base_color
    diffuse.inputs['Roughness'].default_value = roughness
    
    # Configure color ramp for toon effect
    color_ramp.color_ramp.interpolation = 'CONSTANT'
    
    # Connect
    links.new(diffuse.outputs['BSDF'], shader_to_rgb.inputs['Shader'])
    links.new(shader_to_rgb.outputs['Color'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], output.inputs['Surface'])
    
    return mat


def create_pbr_material(
    name: str,
    base_color: Tuple[float, float, float, float] = (0.8, 0.8, 0.8, 1.0),
    metallic: float = 0.0,
    roughness: float = 0.5,
    specular: float = 0.5,
    transmission: float = 0.0,
    ior: float = 1.45,
    emission_color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
    emission_strength: float = 0.0
) -> bpy.types.Material:
    """Create comprehensive PBR material"""
    mat = create_material(name)
    nodes = mat.node_tree.nodes
    
    bsdf = nodes["Principled BSDF"]
    
    # Set all PBR properties
    bsdf.inputs['Base Color'].default_value = base_color
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Specular IOR Level'].default_value = specular
    bsdf.inputs['Transmission Weight'].default_value = transmission
    bsdf.inputs['IOR'].default_value = ior
    bsdf.inputs['Emission Color'].default_value = emission_color
    bsdf.inputs['Emission Strength'].default_value = emission_strength
    
    return mat


def assign_material(
    material: bpy.types.Material,
    objects: Optional[Union[bpy.types.Object, List[bpy.types.Object]]] = None
):
    """Assign material to objects"""
    if objects is None:
        objects = bpy.context.selected_objects
    
    # Handle single object or list
    if hasattr(objects, 'type'):  # Single object
        objects = [objects]
    
    for obj in objects:
        if obj.type == 'MESH':
            if not obj.data.materials:
                obj.data.materials.append(material)
            else:
                obj.data.materials[0] = material


def set_material_color(
    material: bpy.types.Material,
    color: Tuple[float, float, float, float]
):
    """Set the base color of a material"""
    if material.use_nodes:
        nodes = material.node_tree.nodes
        if "Principled BSDF" in nodes:
            nodes["Principled BSDF"].inputs['Base Color'].default_value = color
