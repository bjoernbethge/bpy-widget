"""
Lighting - Analog zu utils.py setup_lighting
"""
import bpy


def setup_three_point_lighting():
    """Setup three point lighting - erweitert setup_lighting"""
    # Key Light
    bpy.ops.object.light_add(type='SUN', location=(4, -4, 6))
    key_light = bpy.context.object
    key_light.data.energy = 3.0
    key_light.name = "KeyLight"
    
    # Fill Light  
    bpy.ops.object.light_add(type='AREA', location=(-3, -2, 4))
    fill_light = bpy.context.object
    fill_light.data.energy = 1.0
    fill_light.data.size = 2.0
    fill_light.name = "FillLight"
    
    # Rim Light
    bpy.ops.object.light_add(type='SPOT', location=(2, 4, 5))
    rim_light = bpy.context.object
    rim_light.data.energy = 2.0
    rim_light.data.spot_size = 1.0
    rim_light.name = "RimLight"
    
    return key_light, fill_light, rim_light


def setup_environment_lighting(strength=1.0):
    """Setup environment lighting - erweitert setup_world_background"""
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    
    world.use_nodes = True
    tree = world.node_tree
    tree.nodes.clear()
    
    env_node = tree.nodes.new('ShaderNodeTexEnvironment')
    bg_node = tree.nodes.new('ShaderNodeBackground')
    output = tree.nodes.new('ShaderNodeOutputWorld')
    
    bg_node.inputs['Strength'].default_value = strength
    
    tree.links.new(env_node.outputs['Color'], bg_node.inputs['Color'])
    tree.links.new(bg_node.outputs['Background'], output.inputs['Surface'])
    
    return env_node


def setup_sun_light(energy=2.0, angle=0.785):
    """Setup sun light - analog zu setup_lighting"""
    bpy.ops.object.light_add(type='SUN', location=(3, -3, 5))
    sun = bpy.context.object
    sun.data.energy = energy
    sun.rotation_euler = (angle, 0, angle)
    return sun
