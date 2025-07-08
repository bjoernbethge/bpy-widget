"""
Rendering functions for bpy widget
"""
import os
import time
from typing import Optional, Tuple

import bpy
import numpy as np


def setup_rendering(width: int = 512, height: int = 512, engine: str = 'BLENDER_EEVEE_NEXT'):
    """Configure render settings"""
    scene = bpy.context.scene
    
    scene.render.engine = engine
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '8'
    
    # Compositing
    scene.use_nodes = True
    scene.render.use_compositing = True
    
    # Color management
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    
    # EEVEE Next optimizations
    if engine == 'BLENDER_EEVEE_NEXT':
        scene.eevee.taa_render_samples = 16
        scene.eevee.use_raytracing = False


def render_to_pixels() -> Tuple[Optional[np.ndarray], int, int]:
    """Render scene and return pixel array"""
    from .temp_files import get_render_file
    
    if not bpy.context.scene.camera:
        print("Warning: No camera found")
        return None, 0, 0
    
    render_file = get_render_file()
    
    try:
        bpy.context.scene.render.filepath = render_file
        bpy.ops.render.render(write_still=True)
        
        if not os.path.exists(render_file):
            return None, 0, 0
        
        # Load and convert pixels
        temp_image = bpy.data.images.load(render_file)
        width, height = temp_image.size
        
        if width <= 0 or height <= 0 or not temp_image.pixels:
            bpy.data.images.remove(temp_image)
            return None, 0, 0
        
        # Get pixel data
        pixel_data = np.zeros((height * width * 4), dtype=np.float32)
        temp_image.pixels.foreach_get(pixel_data)
        
        # Convert to uint8 array
        pixels_array = pixel_data.reshape((height, width, 4))
        pixels_array = (np.clip(pixels_array, 0, 1) * 255).astype(np.uint8)
        pixels_array = np.flipud(pixels_array)
        
        # Cleanup
        bpy.data.images.remove(temp_image)
        
        return pixels_array, width, height
        
    except Exception as e:
        print(f"Render failed: {e}")
        return None, 0, 0


def optimize_for_interactive():
    """Optimize render settings for interactive use"""
    scene = bpy.context.scene
    
    if scene.render.engine == 'BLENDER_EEVEE_NEXT':
        scene.eevee.taa_render_samples = 8
        scene.eevee.use_raytracing = False
        scene.render.resolution_percentage = 75
    elif scene.render.engine == 'CYCLES':
        scene.cycles.samples = 32


def set_render_samples(samples: int):
    """Set render samples for current engine"""
    scene = bpy.context.scene
    
    if scene.render.engine == 'CYCLES':
        scene.cycles.samples = samples
    elif scene.render.engine == 'BLENDER_EEVEE_NEXT':
        scene.eevee.taa_render_samples = samples
