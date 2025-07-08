"""
Camera functions for bpy widget
"""
import math
from typing import Tuple

import bpy
import mathutils


def setup_camera(location: Tuple[float, float, float] = (6, -6, 5), 
                rotation: Tuple[float, float, float] = (1.1, 0, 0.785)) -> bpy.types.Object:
    """Setup camera with default positioning"""
    bpy.ops.object.camera_add(location=location)
    camera = bpy.context.object
    camera.rotation_euler = rotation
    camera.name = "InteractiveCamera"
    bpy.context.scene.camera = camera
    return camera


def update_camera_spherical(distance: float, angle_x: float, angle_z: float) -> bool:
    """Update camera position using spherical coordinates"""
    camera = bpy.context.scene.camera
    
    if not camera:
        setup_camera()
        camera = bpy.context.scene.camera
    
    if not camera:
        return False
    
    # Convert spherical to cartesian
    x = distance * math.cos(angle_x) * math.cos(angle_z)
    y = distance * math.cos(angle_x) * math.sin(angle_z)
    z = distance * math.sin(angle_x)
    
    # Update position
    camera.location = (x, y, z)
    
    # Look at origin
    camera_location = mathutils.Vector((x, y, z))
    target_location = mathutils.Vector((0, 0, 0))
    direction = target_location - camera_location
    camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    return True


def calculate_spherical_from_position(location: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Calculate spherical coordinates from cartesian position"""
    x, y, z = location
    
    distance = math.sqrt(x*x + y*y + z*z)
    angle_x = math.atan2(z, math.sqrt(x*x + y*y))
    angle_z = math.atan2(y, x)
    
    return distance, angle_x, angle_z
