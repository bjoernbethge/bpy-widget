"""
Camera functions for bpy widget
"""
import math
from typing import Tuple

import bpy
import mathutils


def setup_camera(distance: float = 10.0, target: Tuple[float, float, float] = (0, 0, 1), 
                 width: int = 1920, height: int = 1080) -> bpy.types.Object:
    """Setup camera with spherical positioning around target
    
    Args:
        distance: Camera distance from target
        target: Target point to look at
        width: Render width (for aspect ratio calculation)
        height: Render height (for aspect ratio calculation)
    """
    # Remove existing camera if any
    if bpy.context.scene.camera:
        bpy.data.objects.remove(bpy.context.scene.camera, do_unlink=True)
    
    # Default spherical coordinates for better initial view
    angle_x = 0.8  # elevation (lower angle to see both objects better)
    angle_z = -0.785  # azimuth (45 degrees from side)
    
    # Convert to cartesian
    x = target[0] + distance * math.cos(angle_x) * math.cos(angle_z)
    y = target[1] + distance * math.cos(angle_x) * math.sin(angle_z)
    z = target[2] + distance * math.sin(angle_x)
    
    # Create camera
    bpy.ops.object.camera_add(location=(x, y, z))
    camera = getattr(bpy.context, 'object', None) or bpy.data.objects[-1]  # Get last created object
    camera.name = "InteractiveCamera"
    
    # Look at target
    camera_location = mathutils.Vector((x, y, z))
    target_location = mathutils.Vector(target)
    direction = target_location - camera_location
    camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    # Configure camera sensor to match render aspect ratio
    # Use 'AUTO' sensor fit to automatically adjust to render resolution
    camera.data.sensor_fit = 'AUTO'
    
    bpy.context.scene.camera = camera
    return camera


def update_camera_position(location: Tuple[float, float, float], target: Tuple[float, float, float] = (0, 0, 1)):
    """Update camera position and look at target"""
    camera = bpy.context.scene.camera
    
    if not camera:
        setup_camera()
        camera = bpy.context.scene.camera
    
    if camera:
        camera.location = location
        
        # Look at target
        camera_location = mathutils.Vector(location)
        target_location = mathutils.Vector(target)
        direction = target_location - camera_location
        camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


def update_camera_spherical(distance: float, angle_x: float, angle_z: float, 
                           target: Tuple[float, float, float] = (0, 0, 1),
                           width: int = 1920, height: int = 1080) -> bool:
    """Update camera position using spherical coordinates
    
    Args:
        distance: Camera distance from target
        angle_x: Elevation angle
        angle_z: Azimuth angle
        target: Target point to look at
        width: Render width (for aspect ratio calculation)
        height: Render height (for aspect ratio calculation)
    """
    camera = bpy.context.scene.camera
    
    if not camera:
        setup_camera(distance, target, width, height)
        camera = bpy.context.scene.camera
    
    if not camera:
        return False
    
    # Convert spherical to cartesian
    x = target[0] + distance * math.cos(angle_x) * math.cos(angle_z)
    y = target[1] + distance * math.cos(angle_x) * math.sin(angle_z)
    z = target[2] + distance * math.sin(angle_x)
    
    # Update position
    camera.location = (x, y, z)
    
    # Look at target
    camera_location = mathutils.Vector((x, y, z))
    target_location = mathutils.Vector(target)
    direction = target_location - camera_location
    camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    # Ensure sensor fit matches render aspect ratio
    camera.data.sensor_fit = 'AUTO'
    
    return True


def calculate_spherical_from_position(location: Tuple[float, float, float], target: Tuple[float, float, float] = (0, 0, 1)) -> Tuple[float, float, float]:
    """Calculate spherical coordinates from cartesian position relative to target"""
    x = location[0] - target[0]
    y = location[1] - target[1]
    z = location[2] - target[2]
    
    distance = math.sqrt(x*x + y*y + z*z)
    angle_x = math.atan2(z, math.sqrt(x*x + y*y)) if distance > 0 else 0
    angle_z = math.atan2(y, x) if distance > 0 else 0
    
    return distance, angle_x, angle_z
