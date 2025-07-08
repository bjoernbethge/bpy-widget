"""
Materials - Analog zu utils.py create_material
"""
import bpy


def create_glass_material(name, transmission=1.0, ior=1.45):
    """Create glass material - analog zu create_chrome_material"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs['Transmission Weight'].default_value = transmission
    bsdf.inputs['IOR'].default_value = ior
    bsdf.inputs['Roughness'].default_value = 0.0
    
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (200, 0)
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat


def create_metal_material(name, color=(0.8, 0.8, 0.8), roughness=0.1):
    """Create metal material - analog zu create_chrome_material"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = roughness
    
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (200, 0)
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat


def assign_material(material, objects=None):
    """Assign material to objects - usability helper"""
    if objects is None:
        objects = bpy.context.selected_objects
    
    for obj in objects:
        if obj.type == 'MESH':
            if not obj.data.materials:
                obj.data.materials.append(material)
            else:
                obj.data.materials[0] = material
