"""
Lighting - Analog zu utils.py setup_lighting
"""
from typing import Tuple

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


def setup_lighting(
    sun_energy: float = 3.0,
    sun_location: Tuple[float, float, float] = (4, 4, 10),
    add_fill_light: bool = False
) -> None:
    """
    Setup basic lighting for the scene.

    Args:
        sun_energy: Energy of the sun light
        sun_location: Location of the sun light
        add_fill_light: Add a fill light for better illumination
    """
    # Add key light
    bpy.ops.object.light_add(type='SUN', location=sun_location)
    sun = getattr(bpy.context, 'object', None) or bpy.data.objects[-1]  # Get last created object
    if sun:
        sun.data.energy = sun_energy
        sun.rotation_euler = (0.3, 0.3, 0)

    if add_fill_light:
        # Add fill light
        bpy.ops.object.light_add(type='AREA', location=(-4, -4, 6))
        fill = getattr(bpy.context, 'object', None) or bpy.data.objects[-1]  # Get last created object
        if fill:
            fill.data.energy = sun_energy * 0.3
        fill.data.size = 5
        fill.rotation_euler = (-0.3, -0.3, 0)


def setup_world_background(
    color: Tuple[float, float, float] = (0.8, 0.8, 0.9),
    strength: float = 1.0
) -> None:
    """
    Setup world background color.

    Args:
        color: Background color (R, G, B)
        strength: Background strength
    """
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    world.use_nodes = True
    bg_node = world.node_tree.nodes["Background"]
    bg_node.inputs["Color"].default_value = (*color, 1.0)
    bg_node.inputs["Strength"].default_value = strength


def setup_sun_light(energy=2.0, angle=0.785):
    """Setup sun light - analog zu setup_lighting"""
    bpy.ops.object.light_add(type='SUN', location=(3, -3, 5))
    sun = getattr(bpy.context, 'object', None) or bpy.data.objects[-1]  # Get last created object
    sun.data.energy = energy
    sun.rotation_euler = (angle, 0, angle)
    return sun
