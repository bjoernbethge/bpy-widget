"""
Test script for rendering performance optimization
Tests different rendering methods to find the fastest approach
"""
import tempfile
import time
import traceback
from pathlib import Path
from typing import Optional, Tuple

import bpy
import numpy as np

from bpy_widget.core.rendering import (
    setup_rendering,
    initialize_gpu,
    set_gpu_backend,
    get_gpu_backend,
    enable_compositor_gpu,
)
from bpy_widget.core.scene import clear_scene
from bpy_widget.core.camera import setup_camera
from bpy_widget.core.geometry import create_test_cube


def render_to_pixels_file_based() -> Tuple[Optional[np.ndarray], int, int]:
    """Current method: File-based rendering"""
    
    if not bpy.context.scene.camera:
        return None, 0, 0
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        temp_file = tmp.name
    
    try:
        bpy.context.scene.render.filepath = temp_file
        bpy.ops.render.render(write_still=True)
        
        temp_path = Path(temp_file)
        if not temp_path.exists():
            return None, 0, 0
        
        temp_image = bpy.data.images.load(temp_file)
        width, height = temp_image.size
        
        if width <= 0 or height <= 0 or not temp_image.pixels:
            bpy.data.images.remove(temp_image)
            return None, 0, 0
        
        pixel_count = height * width * 4
        pixel_data = np.empty(pixel_count, dtype=np.float32)
        temp_image.pixels.foreach_get(pixel_data)
        
        pixels_array = pixel_data.reshape((height, width, 4))
        pixels_array = (np.clip(pixels_array, 0, 1) * 255).astype(np.uint8)
        pixels_array = np.flipud(pixels_array)
        
        bpy.data.images.remove(temp_image)
        return pixels_array, width, height
    
    except Exception as e:
        print(f"Render failed: {e}")
        return None, 0, 0
    finally:
        Path(temp_file).unlink(missing_ok=True)


def render_to_pixels_memory_based() -> Tuple[Optional[np.ndarray], int, int]:
    """Memory-based: Render to internal buffer without file I/O"""
    if not bpy.context.scene.camera:
        return None, 0, 0
    
    try:
        # Render to internal buffer (no file write)
        # Use render.render() without write_still, then access render result
        scene = bpy.context.scene
        
        # Check if we can use render result directly
        # In Blender 4.5+, we might be able to access render result without file
        bpy.ops.render.render(write_still=False)  # Render to memory
        
        # Try to get render result from render engine
        # This might work in headless mode
        render_result = scene.render
        if hasattr(render_result, 'result'):
            result = render_result.result
            if result and hasattr(result, 'save_render'):
                # Try to access pixels directly
                pass
        
        # Alternative: Use bpy.data.images.new() and render to it
        # This avoids file I/O
        width = scene.render.resolution_x
        height = scene.render.resolution_y
        
        # Create image in memory
        render_image = bpy.data.images.new("_render_temp", width=width, height=height)
        
        # Set as render target
        scene.render.filepath = ""
        
        # Render
        bpy.ops.render.render(write_still=False)
        
        # Try to get pixels from render result
        # This is tricky - we might need to use gpu module
        if hasattr(bpy.context, 'blend_data'):
            # Check if render result is available
            pass
        
        # Fallback: Use file-based for now
        return render_to_pixels_file_based()
        
    except Exception as e:
        print(f"Memory render failed: {e}")
        traceback.print_exc()
        return None, 0, 0


def render_to_pixels_gpu_direct() -> Tuple[Optional[np.ndarray], int, int]:
    """GPU direct: Try to read directly from GPU buffer using gpu module"""
    if not bpy.context.scene.camera:
        return None, 0, 0
    
    try:
        import gpu
        from gpu_extras.presets import draw_texture_2d  # noqa: F401
        
        scene = bpy.context.scene
        width = scene.render.resolution_x
        height = scene.render.resolution_y
        
        # Render to memory first
        bpy.ops.render.render(write_still=False)
        
        # Try to access GPU texture/framebuffer
        # This is experimental and may not work in headless mode
        # GPU module might not have access to render result in headless
        
        # Fallback to file-based for now
        return render_to_pixels_file_based()
        
    except Exception as e:
        print(f"GPU direct render failed: {e}")
        return render_to_pixels_file_based()


def render_to_pixels_image_target() -> Tuple[Optional[np.ndarray], int, int]:
    """Render to Image datablock: Use bpy.data.images as render target"""
    if not bpy.context.scene.camera:
        return None, 0, 0
    
    try:
        scene = bpy.context.scene
        width = scene.render.resolution_x
        height = scene.render.resolution_y
        
        # Create or get render image
        render_image_name = "_render_temp"
        if render_image_name in bpy.data.images:
            render_image = bpy.data.images[render_image_name]
            render_image.scale(width, height)
        else:
            render_image = bpy.data.images.new(render_image_name, width=width, height=height)
        
        # Set render filepath to empty (render to memory)
        old_filepath = scene.render.filepath
        scene.render.filepath = ""
        
        # Render
        bpy.ops.render.render(write_still=False)
        
        # Check if image was updated
        # In some cases, render might update the image directly
        if render_image.pixels:
            pixel_count = height * width * 4
            pixel_data = np.empty(pixel_count, dtype=np.float32)
            render_image.pixels.foreach_get(pixel_data)
            
            pixels_array = pixel_data.reshape((height, width, 4))
            pixels_array = (np.clip(pixels_array, 0, 1) * 255).astype(np.uint8)
            pixels_array = np.flipud(pixels_array)
            
            scene.render.filepath = old_filepath
            return pixels_array, width, height
        
        # Fallback to file-based
        scene.render.filepath = old_filepath
        return render_to_pixels_file_based()
        
    except Exception as e:
        print(f"Image target render failed: {e}")
        traceback.print_exc()
        return render_to_pixels_file_based()


def benchmark_rendering_method(method_name: str, method_func, iterations: int = 5):
    """Benchmark a rendering method"""
    times = []
    success_count = 0
    
    print(f"\n{'='*60}")
    print(f"Testing: {method_name}")
    print(f"{'='*60}")
    
    for i in range(iterations):
        start_time = time.time()
        pixels, width, height = method_func()
        render_time = time.time() - start_time
        
        if pixels is not None:
            times.append(render_time)
            success_count += 1
            print(f"  Iteration {i+1}: {render_time*1000:.2f}ms - {width}x{height}")
        else:
            print(f"  Iteration {i+1}: FAILED")
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        print(f"\n  Average: {avg_time*1000:.2f}ms")
        print(f"  Min: {min_time*1000:.2f}ms")
        print(f"  Max: {max_time*1000:.2f}ms")
        print(f"  Success rate: {success_count}/{iterations}")
        return avg_time, min_time, max_time
    else:
        print(f"\n  All iterations failed!")
        return None, None, None


def test_rendering_methods():
    """Test different rendering methods"""
    print("="*60)
    print("RENDERING PERFORMANCE TEST")
    print("="*60)
    
    # Setup scene
    clear_scene()
    setup_camera()
    create_test_cube()
    
    # Test different configurations
    configs = [
        ("EEVEE Next + OpenGL", "BLENDER_EEVEE_NEXT", "OPENGL"),
        ("EEVEE Next + Vulkan", "BLENDER_EEVEE_NEXT", "VULKAN"),
    ]
    
    results = {}
    
    for config_name, engine, backend in configs:
        print(f"\n{'='*60}")
        print(f"Configuration: {config_name}")
        print(f"{'='*60}")
        
        # Setup rendering
        setup_rendering(width=512, height=512, engine=engine, gpu_backend=backend)
        initialize_gpu()
        enable_compositor_gpu()
        
        # Check GPU backend
        actual_backend = get_gpu_backend()
        print(f"GPU Backend: {actual_backend}")
        
        # Test methods
        methods = [
            ("File-based (current)", render_to_pixels_file_based),
            ("Memory-based (image target)", render_to_pixels_image_target),
            # ("GPU Direct", render_to_pixels_gpu_direct),  # Disabled for now
        ]
        
        config_results = {}
        for method_name, method_func in methods:
            avg, min_t, max_t = benchmark_rendering_method(method_name, method_func, iterations=3)
            if avg is not None:
                config_results[method_name] = {
                    'avg': avg,
                    'min': min_t,
                    'max': max_t
                }
        
        results[config_name] = config_results
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    for config_name, config_results in results.items():
        print(f"\n{config_name}:")
        for method_name, method_stats in config_results.items():
            print(f"  {method_name}:")
            print(f"    Avg: {method_stats['avg']*1000:.2f}ms")
            print(f"    Min: {method_stats['min']*1000:.2f}ms")
            print(f"    Max: {method_stats['max']*1000:.2f}ms")


if __name__ == "__main__":
    test_rendering_methods()

