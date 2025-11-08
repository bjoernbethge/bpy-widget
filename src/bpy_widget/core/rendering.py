"""
Rendering functions for bpy widget - Fast & simple
"""
import os
import tempfile
from typing import Optional, Tuple

import bpy
import numpy as np
from loguru import logger

from .compositor_manager import get_compositor_chain

# GPU module - available after bpy import
gpu = None


def set_gpu_backend(backend: str = 'VULKAN') -> bool:
    """Set GPU backend (VULKAN or OPENGL)
    
    Blender 4.5+ supports Vulkan backend for improved performance.
    Note: Requires restart or re-initialization to take full effect.
    
    Args:
        backend: Either 'VULKAN' or 'OPENGL'
        
    Returns:
        True if backend was set successfully, False otherwise
    """
    try:
        if not hasattr(bpy.context.preferences, 'system'):
            return False
        
        sys_prefs = bpy.context.preferences.system
        
        if not hasattr(sys_prefs, 'gpu_backend'):
            return False
        
        # Set backend
        backend_upper = backend.upper()
        if backend_upper not in ('VULKAN', 'OPENGL'):
            return False
        
        sys_prefs.gpu_backend = backend_upper
        
        # Verify it was set
        return sys_prefs.gpu_backend == backend_upper
        
    except Exception:
        return False


def get_gpu_backend() -> Optional[str]:
    """Get current GPU backend
    
    Returns:
        Current backend ('VULKAN' or 'OPENGL') or None if unavailable
    """
    try:
        if not hasattr(bpy.context.preferences, 'system'):
            return None
        
        sys_prefs = bpy.context.preferences.system
        
        if not hasattr(sys_prefs, 'gpu_backend'):
            return None
        
        return sys_prefs.gpu_backend
        
    except Exception:
        return None


def initialize_gpu():
    """Initialize GPU module for OpenGL rendering
    
    This must be called after bpy is imported. The gpu module provides
    OpenGL access needed for EEVEE rendering and GPU Offscreen.
    
    In headless mode, OpenGL context may not be available unless:
    - EGL is configured (Linux)
    - OSMesa is available (Software rendering)
    - Xvfb is running (virtual X11 display)
    
    Returns:
        True if GPU module was initialized successfully, False otherwise
    """
    global gpu
    try:
        if gpu is None:
            import gpu
        
        # Try to check if OpenGL context is available (silently fail in headless mode)
        try:
            test_offscreen = gpu.types.GPUOffScreen(1, 1)
            test_offscreen.free()
        except SystemError:
            # OpenGL context not available - expected in headless mode, no need to log
            pass
        
        return True
    except ImportError:
        logger.warning("GPU module not available - OpenGL rendering may be limited")
        return False
    except Exception:
        return False


def ensure_gpu_for_eevee():
    """Ensure GPU is properly configured for EEVEE rendering
    
    This function:
    - Initializes the GPU module if not already done
    - Verifies OpenGL backend is available
    - Configures EEVEE to use GPU acceleration
    
    Returns:
        True if GPU is ready for EEVEE, False otherwise
    """
    try:
        # Initialize GPU module
        if not initialize_gpu():
            return False
        
        # Check if OpenGL backend is set (for EEVEE)
        backend = get_gpu_backend()
        if backend is None:
            # Try to set OpenGL as fallback if no backend is set
            # EEVEE works best with OpenGL
            set_gpu_backend('OPENGL')
            backend = get_gpu_backend()
        
        # Verify EEVEE can use GPU
        scene = bpy.context.scene
        if scene.render.engine == 'BLENDER_EEVEE' or scene.render.engine == 'BLENDER_EEVEE_NEXT':
            # EEVEE automatically uses GPU when available
            # Just verify the backend is set
            if backend in ('OPENGL', 'VULKAN'):
                return True
        
        return backend is not None
        
    except Exception as e:
        logger.debug(f"GPU setup for EEVEE failed: {e}")
        return False


def enable_compositor_gpu():
    """Enable GPU acceleration for compositor (Blender 4.5+)
    
    The compositor can use GPU for faster post-processing.
    This should be called after GPU is initialized.
    
    Returns:
        True if GPU compositing was enabled, False otherwise
    """
    try:
        scene = bpy.context.scene
        
        # Enable GPU compositing if available (Blender 4.5+)
        if hasattr(scene.render, 'use_compositor_gpu'):
            scene.render.use_compositor_gpu = True
            logger.debug("GPU compositing enabled")
            return True
        elif hasattr(scene.render, 'use_compositor'):
            # Fallback: just enable compositing
            scene.render.use_compositor = 'GPU' if hasattr(scene.render, 'compositor_gpu') else True
            logger.debug("Compositing enabled")
            return True
        
        return False
    except Exception as e:
        logger.debug(f"Failed to enable GPU compositing: {e}")
        return False


def setup_rendering(width: int = 1920, height: int = 1080, engine: str = 'BLENDER_EEVEE_NEXT', gpu_backend: Optional[str] = None):
    """Configure render settings - simple and fast
    
    Args:
        width: Render width in pixels
        height: Render height in pixels
        engine: Render engine ('BLENDER_EEVEE_NEXT' or 'CYCLES')
        gpu_backend: GPU backend to use ('VULKAN' or 'OPENGL'). If None, uses current setting.
    """
    scene = bpy.context.scene
    
    # Set GPU backend if specified (Blender 4.5+ supports Vulkan)
    if gpu_backend is not None:
        set_gpu_backend(gpu_backend)
    elif engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
        # For EEVEE, ensure GPU is initialized and backend is available
        ensure_gpu_for_eevee()
    
    # Enable GPU compositing for better performance (Blender 4.5+)
    enable_compositor_gpu()
    
    # Initialize CompositorChain - Post-Processing is ALWAYS active
    chain = get_compositor_chain()
    if not chain._initialized:
        chain.initialize(clear_existing=False)  # Don't clear existing effects if any
    
    # Basic settings
    scene.render.engine = engine
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    
    # Set pixel aspect ratio to 1:1 (square pixels)
    scene.render.pixel_aspect_x = 1.0
    scene.render.pixel_aspect_y = 1.0
    
    # Update camera aspect ratio if camera exists
    if scene.camera:
        scene.camera.data.sensor_fit = 'AUTO'
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
        
    # Configure color management properly for headless operation
    # This prevents "AgX not found" and OpenColorIO warnings
    try:
        # Set view transform to Standard (always available, unlike AgX)
        # Must be set BEFORE any rendering operations
        if hasattr(scene.view_settings, 'view_transform'):
            scene.view_settings.view_transform = 'Standard'
        
        # Set look to None (no look modification)
        if hasattr(scene.view_settings, 'look'):
            scene.view_settings.look = 'None'
        
        # Configure display device (sRGB is most compatible for headless)
        if hasattr(scene.display_settings, 'display_device'):
            scene.display_settings.display_device = 'sRGB'
        
        # Configure sequencer color space (if available)
        if hasattr(scene, 'sequencer_colorspace_settings'):
            if hasattr(scene.sequencer_colorspace_settings, 'name'):
                scene.sequencer_colorspace_settings.name = 'sRGB'
            
    except Exception:
        # If color management setup fails, silently continue
        # Standard transform should always work as fallback
        pass


def render_to_pixels() -> Tuple[Optional[np.ndarray], int, int]:
    """Render scene and return pixel array - via Viewer Node (no file I/O!)
    
    Clean implementation following working example:
    - Remove all nodes, create fresh compositor setup
    - Render to Viewer Node
    - Read pixels directly from Viewer Node image datablock
    - Falls back to save_render() if Viewer Node doesn't work in headless mode
    """
    if not bpy.context.scene.camera:
        logger.warning("No camera found")
        return None, 0, 0

    scene = bpy.context.scene
    
    # Compositing is ALWAYS active - ensure it's enabled
    scene.use_nodes = True
    scene.render.use_compositing = True  # Critical: must be enabled!
    
    # Use CompositorChain nodes if available (Post-Processing infrastructure)
    chain = get_compositor_chain()
    
    # Ensure CompositorChain is initialized
    if not chain._initialized:
        chain.initialize(clear_existing=False)
    
    # Use CompositorChain nodes (they're always available when Post-Processing is active)
    render_layers = chain.render_layers
    viewer = chain.viewer
    tree = chain.tree
    
    # Validate tree is still valid (may be invalidated if scene changed)
    if not tree or not hasattr(tree, 'links'):
        logger.error("CompositorNodeTree is invalid or has been removed")
        # Re-initialize chain if tree is invalid
        chain.initialize(clear_existing=False)
        tree = chain.tree
        render_layers = chain.render_layers
        viewer = chain.viewer
    
    if not tree or not hasattr(tree, 'links'):
        logger.error("Failed to get valid compositor tree")
        return None, 0, 0
    
    links = tree.links
    
    # Ensure Viewer Node is properly configured
    # Check if Viewer Node has the correct input socket
    if 'Image' not in viewer.inputs:
        logger.error("Viewer Node missing Image input socket")
        return None, 0, 0
    
    # Set Viewer Node as active (important for compositor!)
    tree.nodes.active = viewer
    
    # Connect Render Layers to Viewer
    # If there are Post-Processing effects (CompositorChain), they should already be connected to Viewer
    # If not, connect Render Layers directly to Viewer
    # Check if Viewer already has a connection from effects
    viewer_has_input = False
    for link in tree.links:
        if link.to_node == viewer and link.to_socket.name == 'Image':
            viewer_has_input = True
            break
    
    # Only connect Render Layers if Viewer has no input (no effects active)
    if not viewer_has_input:
        # Remove any existing connections to Viewer's Image input first
        for link in list(tree.links):
            if link.to_node == viewer and link.to_socket.name == 'Image':
                tree.links.remove(link)
        
        try:
            links.new(render_layers.outputs['Image'], viewer.inputs['Image'])
        except Exception as e:
            logger.error(f"Failed to connect Render Layers to Viewer: {e}")
            return None, 0, 0
    
    # Get Viewer Node image datablock and set resolution BEFORE rendering
    # This ensures the Viewer Node uses the correct resolution
    viewer_pixels_img = bpy.data.images.get('Viewer Node')
    if not viewer_pixels_img:
        # Viewer Node image doesn't exist yet - it will be created on first render
        # We'll handle resolution after render
        pass
    else:
        # Scale Viewer Node image to match render resolution if it exists
        viewer_pixels_img.scale(scene.render.resolution_x, scene.render.resolution_y)
    
    # Store original filepath
    old_filepath = scene.render.filepath
    
    try:
        # Set filepath to empty to render to memory
        scene.render.filepath = ""
        
        # Render (without writing to disk)
        bpy.ops.render.render(write_still=False)
        
        # Get pixel data from Viewer Node (as in working example)
        viewer_pixels = bpy.data.images['Viewer Node']
        width, height = viewer_pixels.size
        
        # Verify connection is correct - check if Viewer actually received data
        # In headless mode, Viewer Node might not populate even if connected
        if not viewer_pixels.pixels or len(viewer_pixels.pixels) == 0:
            logger.warning("Viewer Node has no pixel data - connection might be broken or Viewer Node doesn't work in headless mode")
            scene.render.filepath = old_filepath
            return None, 0, 0
        
        # Convert to NumPy array (RGBA format, float 0-1)
        # Use direct slice access as in working example: pixels[:]
        pixels_float = np.array(viewer_pixels.pixels[:], dtype=np.float32)
        pixels_float = pixels_float.reshape((height, width, 4))
        
        # Check if all pixels are black (0.0) - Viewer Node might not be receiving data in headless mode
        # In this case, we need to use save_render() to access the internal render buffer
        if pixels_float.max() == 0.0:
            logger.warning("Viewer Node pixels are all black - using save_render() fallback")
            # Use save_render() to access internal render buffer (only reliable method in headless mode)
            return _render_to_pixels_via_save_render(scene, width, height, old_filepath)
        
        # Convert to 8-bit (0-255)
        pixels_uint8 = (np.clip(pixels_float, 0.0, 1.0) * 255).astype(np.uint8)
        
        # Flip vertically (Blender uses bottom-up, we need top-down for display)
        pixels_array = np.flipud(pixels_uint8)
        
        # Restore filepath
        scene.render.filepath = old_filepath
        
        # Successfully read pixels from Viewer Node
        return pixels_array, width, height
        
    except KeyError:
        logger.error("Viewer Node image not found after render")
        scene.render.filepath = old_filepath
        return None, 0, 0
    except Exception as e:
        logger.error(f"Render failed: {e}")
        scene.render.filepath = old_filepath
        return None, 0, 0


def _render_to_pixels_via_save_render(scene, width: int, height: int, old_filepath: str) -> Tuple[Optional[np.ndarray], int, int]:
    """Fallback: Use save_render() to access internal render buffer (only reliable method in headless mode)
    
    save_render() accesses Blender's internal render buffer and writes to file.
    This is the only reliable way to get pixel data in headless mode when Viewer Node doesn't work.
    """
    
    render_result = bpy.data.images.get("Render Result")
    if not render_result:
        logger.warning("Render Result not found")
        scene.render.filepath = old_filepath
        return None, 0, 0
    
    # Use NamedTemporaryFile with delete=False so we can read it after save_render
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as tmp:
        temp_file = tmp.name
    
    try:
        # save_render() accesses internal render buffer and writes to file
        render_result.save_render(temp_file)
        
        # Load buffer from file into temporary image datablock
        temp_img = bpy.data.images.load(temp_file)
        
        # Read pixels directly from the loaded buffer
        pixel_count = temp_img.size[0] * temp_img.size[1] * 4
        pixels_array_float = np.empty(pixel_count, dtype=np.float32)
        temp_img.pixels.foreach_get(pixels_array_float)
        img_data = (pixels_array_float.reshape((temp_img.size[1], temp_img.size[0], 4)) * 255).astype(np.uint8)
        
        # Clean up temp image and file immediately
        bpy.data.images.remove(temp_img)
        os.unlink(temp_file)
        
        # Convert to RGBA if needed (should already be RGBA)
        if img_data.shape[2] == 3:  # RGB -> RGBA
            alpha = np.full((img_data.shape[0], img_data.shape[1], 1), 255, dtype=np.uint8)
            img_data = np.concatenate([img_data, alpha], axis=2)
        
        # Flip vertically (Blender uses bottom-up, we need top-down for display)
        pixels_array = np.flipud(img_data)
        
        result_width, result_height = pixels_array.shape[1], pixels_array.shape[0]
        
        scene.render.filepath = old_filepath
        return pixels_array, result_width, result_height
        
    except Exception as e:
        logger.error(f"save_render fallback failed: {e}")
        # Clean up temp file if it exists
        if os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass
        scene.render.filepath = old_filepath
        return None, 0, 0
