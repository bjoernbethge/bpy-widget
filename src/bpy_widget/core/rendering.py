"""
Rendering functions for bpy widget - Fast & simple
"""
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import bpy
import numpy as np


def setup_rendering(width: int = 512, height: int = 512, engine: str = 'BLENDER_EEVEE_NEXT'):
    """Configure render settings - simple and fast"""
    scene = bpy.context.scene
    
    # Basic settings
    scene.render.engine = engine
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '8'
    
    if engine == 'CYCLES':
        # Cycles settings
        scene.cycles.samples = 64
        scene.cycles.device = 'CPU'  # Most compatible
    else:
        # EEVEE Next settings - optimized for speed
        scene.eevee.taa_render_samples = 16
        scene.eevee.use_raytracing = False
        
    # Simple color management
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'


def render_to_pixels() -> Tuple[Optional[np.ndarray], int, int]:
    """Render scene and return pixel array - fast version"""
    if not bpy.context.scene.camera:
        print("Warning: No camera found")
        return None, 0, 0

    # Create secure temporary file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        temp_file = tmp.name

    try:
        bpy.context.scene.render.filepath = temp_file
        bpy.ops.render.render(write_still=True)

        temp_path = Path(temp_file)
        if not temp_path.exists():
            return None, 0, 0

        # Load image data
        temp_image = bpy.data.images.load(temp_file)
        width, height = temp_image.size

        if width <= 0 or height <= 0 or not temp_image.pixels:
            bpy.data.images.remove(temp_image)
            return None, 0, 0

        # Get pixel data efficiently
        pixel_count = height * width * 4
        pixel_data = np.empty(pixel_count, dtype=np.float32)
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
    finally:
        # Always clean up temporary file
        Path(temp_file).unlink(missing_ok=True)
