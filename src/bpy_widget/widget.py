"""
Blender widget for Marimo - Simplified high-performance version
"""
import base64
import inspect
import io
import multiprocessing
import os
import sys
import time
import traceback
import typing
import warnings
from pathlib import Path
from typing import Optional

import anywidget
import numpy as np
import polars as pl
import traitlets
from loguru import logger

# Lazy import bpy only when needed and safe
bpy = None

# Extension management
from .core import extension_manager

# Core imports only
from .core.camera import (
    calculate_spherical_from_position,
    setup_camera,
    update_camera_spherical,
)
from .core.data_import import (
    batch_import_data,
    import_data_as_points,
    import_data_with_metadata,
    import_dataframe_as_curve,
    import_multiple_series,
)
from .core.data_readers import read_data_file
from .core.geometry import (
    create_icosphere,
    create_suzanne,
    create_test_cube,
    create_torus,
)

# Import new modules
from .core.io_handlers import (
    append_from_blend,
    export_alembic,
    export_gltf,
    export_scene_as_parquet,
    export_usd,
    import_alembic,
    import_gltf,
    import_scene_from_parquet,
    import_usd,
    link_from_blend,
    load_blend,
    save_blend,
)
from .core.lighting import (
    setup_lighting,
    setup_world_background,
)
from .core.materials import (
    assign_material,
    create_material,
    create_preset_material,
)
from .core.nodes import add_glare_node, setup_compositor
from .core.post_processing import (
    add_bloom_glare,
    add_chromatic_aberration,
    add_color_correction,
    add_depth_of_field,
    add_film_grain,
    add_motion_blur,
    add_sharpen,
    add_vignette,
    reset_compositor,
    setup_extended_compositor,
)
from .core.rendering import (
    get_gpu_backend,
    initialize_gpu,
    render_to_pixels,
    set_gpu_backend,
    setup_rendering,
)
from .core.scene import (
    clear_scene,
    get_scene,
)
from .core.setup_datafiles import setup_datafiles_if_needed

STATIC_DIR = Path(__file__).parent / 'static'

__all__ = ['BpyWidget', 'BlenderWidget']


class BpyWidget(anywidget.AnyWidget):
    """Blender widget with interactive camera control"""
    
    # Development mode support (ANYWIDGET_HMR=1) - dynamic loading
    @property
    def _esm(self):
        if os.getenv("ANYWIDGET_HMR") == "1":
            return "http://localhost:5173/src/widget.js?anywidget"
        else:
            return (STATIC_DIR / 'widget.js').read_text()

    @property
    def _css(self):
        if os.getenv("ANYWIDGET_HMR") == "1":
            return ""
        else:
            return (STATIC_DIR / 'widget.css').read_text()
    
    # Widget display traits
    image_data = traitlets.Unicode('').tag(sync=True)
    width = traitlets.Int(1920).tag(sync=True)
    height = traitlets.Int(1080).tag(sync=True)
    status = traitlets.Unicode('Not initialized').tag(sync=True)
    is_initialized = traitlets.Bool(False).tag(sync=True)
    
    # Interactive camera traits
    camera_distance = traitlets.Float(8.0).tag(sync=True)
    camera_angle_x = traitlets.Float(1.1).tag(sync=True)  
    camera_angle_z = traitlets.Float(0.785).tag(sync=True)
    camera_target = traitlets.Tuple(
        traitlets.Float(0.0),
        traitlets.Float(0.0),
        traitlets.Float(1.0),
        default_value=(0.0, 0.0, 1.0)
    ).tag(sync=True)
    
    # Render settings
    render_engine = traitlets.Unicode('BLENDER_EEVEE_NEXT').tag(sync=True)
    render_device = traitlets.Unicode('CPU').tag(sync=True)
    
    # Performance settings
    msg_throttle = traitlets.Int(2).tag(sync=True)

    def __init__(self, width: int = 1920, height: int = 1080, auto_init: bool = True, **kwargs):
        """Initialize widget"""
        super().__init__(**kwargs)

        # Check if we're in marimo (which uses multiprocessing but widgets should work)
        self._is_marimo_context = False
        try:
            frame = inspect.currentframe()
            while frame:
                if 'marimo' in str(frame.f_code.co_filename).lower():
                    self._is_marimo_context = True
                    break
                frame = frame.f_back
        except:
            pass

        # If we're in marimo, use full functionality
        if self._is_marimo_context:
            pass  # marimo context detected
        else:
            # Check for regular multiprocessing conflict
            self._is_multiprocessing_context = (
                hasattr(multiprocessing, 'current_process') and
                multiprocessing.current_process().name != 'MainProcess'
            )
            if self._is_multiprocessing_context:
                logger.warning("BpyWidget cannot be used in multiprocessing contexts!")
                logger.info("This is a known conflict between Blender and multiprocessing.")
                self._init_error_mode(width, height)
                return

        # Safe to import bpy now
        self._ensure_bpy_loaded()

        self.width = width
        self.height = height
        self._pixel_array: typing.Optional[np.ndarray] = None
        self._just_initialized = False
        
        # Update infrastructure following Three.js pattern:
        # - Mark updates as needed (like camera controls)
        # - Only render when update() returns True and enough time has passed
        self._last_render_time = 0.0
        self._update_needed = False  # Flag: camera/state changed, render needed
        self._render_debounce_ms = 20  # Minimum time between renders (~50 FPS max, rendering is ~16ms)
        
        if auto_init:
            self.initialize()

    def _init_error_mode(self, width: int, height: int):
        """Initialize error mode for multiprocessing contexts"""
        self.width = width
        self.height = height
        self.status = "Error: Multiprocessing not supported"
        self.is_initialized = False

        # Create an error message image (simple colored background)
        error_image = np.full((height, width, 3), [128, 64, 64], dtype=np.uint8)  # Dark red background

        # Convert to base64 (raw pixel data)
        pixels_bytes = error_image.tobytes()
        image_b64 = base64.b64encode(pixels_bytes).decode('ascii')
        self.image_data = image_b64

    def _init_marimo_mode(self, width: int, height: int):
        """Initialize marimo-compatible mode with actual Blender functionality"""

        # In marimo mode, we CAN use bpy because we're in the main process
        # The issue was that we were detecting multiprocessing incorrectly
        self._ensure_bpy_loaded()

        self.width = width
        self.height = height
        self._pixel_array: typing.Optional[np.ndarray] = None
        self._just_initialized = False
        self.status = "Marimo mode: Initializing Blender..."
        self.is_initialized = False

        # Auto-initialize in marimo mode
        self.initialize()

    def _ensure_bpy_loaded(self):
        """Ensure bpy is loaded safely"""
        global bpy
        if bpy is None:
            try:
                # Setup missing datafiles BEFORE importing bpy (avoids font warnings)
                # This fixes "OpenColorIO Error" and "Can't find font" warnings
                try:
                    setup_datafiles_if_needed()
                except Exception as e:
                    logger.debug(f"Could not setup datafiles (optional): {e}")
                
                # Now import bpy - fonts should already be in place
                import bpy
                
                # Initialize GPU module after bpy import (required for OpenGL/EEVEE)
                # This makes the gpu module available for EEVEE rendering
                try:
                    initialize_gpu()
                except Exception as e:
                    logger.debug(f"GPU initialization skipped: {e}")
                
                # Configure color management IMMEDIATELY after import
                # This prevents "AgX not found" warnings by setting Standard transform
                # Must happen BEFORE any scene operations
                self._configure_color_management()
                
                # Suppress font and other warnings in headless mode (fallback)
                self._configure_blender_warnings()
                
                # Test if bpy is functional
                _ = bpy.app.version_string  # This should work
            except ImportError as e:
                logger.error(f"Failed to import bpy: {e}")
                raise
            except Exception as e:
                logger.error(f"bpy import succeeded but is not functional: {e}")
                logger.info("This usually means bpy_types is missing. Try reinstalling bpy.")
                raise ImportError(f"bpy is not functional: {e}") from e
    
    @staticmethod
    def _configure_color_management():
        """Configure Blender color management for headless operation
        
        This must be called immediately after bpy import, before any scene access.
        Prevents "AgX not found" and OpenColorIO warnings in headless mode.
        """
        try:
            import bpy
            
            # Access scene to trigger initialization if needed
            # Then immediately configure color management BEFORE any operations
            scene = bpy.context.scene
            
            # Set view transform to Standard (always available, unlike AgX)
            # This prevents Blender from trying to use AgX and showing warnings
            if hasattr(scene.view_settings, 'view_transform'):
                try:
                    scene.view_settings.view_transform = 'Standard'
                except (AttributeError, KeyError, TypeError):
                    # If setting fails, try to read what's available
                    pass
            
            # Set look to None (no look modification)  
            if hasattr(scene.view_settings, 'look'):
                try:
                    scene.view_settings.look = 'None'
                except (AttributeError, KeyError, TypeError):
                    pass
            
            # Configure display device (sRGB is most compatible for headless)
            if hasattr(scene.display_settings, 'display_device'):
                try:
                    scene.display_settings.display_device = 'sRGB'
                except (AttributeError, KeyError, TypeError):
                    pass
                    
        except Exception:
            # Silently fail - this is best effort configuration
            # If it fails, we'll still have stderr filtering as fallback
            pass
    
    @staticmethod
    def _configure_blender_warnings():
        """Configure Blender to suppress non-critical warnings"""
        
        # Suppress Python warnings for missing fonts (blender internal)
        warnings.filterwarnings('ignore', category=UserWarning, module='imbuf')
        
        # Suppress Python warnings for color management
        warnings.filterwarnings('ignore', message='.*Color management.*', category=UserWarning)
        warnings.filterwarnings('ignore', message='.*OpenColorIO.*', category=UserWarning)
        
        # Filter stderr to suppress Blender's C++ warnings (fonts, color management)
        # These come from C++ code and can't be caught with Python warnings
        if not hasattr(sys.stderr, '_bpy_widget_filtered'):
            class FilteredStderr:
                """Filter stderr to suppress Blender internal warnings"""
                def __init__(self, original):
                    self.original = original
                    self._bpy_widget_filtered = True
                
                def __getattr__(self, name):
                    return getattr(self.original, name)
                
                def write(self, text):
                    # Filter out known Blender warnings from C++ code
                    if any(keyword in text.lower() for keyword in [
                        "can't find font",
                        "blf_load_font_default",
                        "font data directory",
                        "fonts\" data path not found",
                        "color management:",
                        "opencolorio error",
                        "colormanagement",
                        "scene view",
                        "using fallback mode",
                    ]):
                        return len(text)  # Return length to prevent errors
                    return self.original.write(text)
            
            sys.stderr = FilteredStderr(sys.stderr)
        
        # Try to configure bpy.app.debug if available
        try:
            import bpy
            # Reduce debug verbosity for headless operation
            if hasattr(bpy.app, 'debug'):
                # Only enable critical errors, suppress warnings
                if isinstance(bpy.app.debug, bool):
                    # Can't fully disable, but we can suppress Python-level warnings
                    pass
            elif hasattr(bpy.app, 'debug_value'):
                # Some versions use debug_value
                # Lower values = less verbose (0 = minimal, 1 = normal, 2 = verbose)
                try:
                    bpy.app.debug_value = 0
                except (AttributeError, TypeError):
                    pass
        except Exception:
            # Ignore errors in warning configuration
            pass

    @traitlets.observe('camera_distance', 'camera_angle_x', 'camera_angle_z', 'camera_target')
    def _on_camera_change(self, change):
        """Handle camera parameter changes from frontend - mark update as needed"""
        if self.is_initialized and not self._just_initialized:
            # Mark that an update is needed (Three.js pattern)
            self._update_needed = True
            # Try to update immediately if enough time has passed
            self._update()
    
    @traitlets.observe('render_engine', 'render_device')
    def _on_render_settings_change(self, change):
        """Handle render settings changes"""
        if self.is_initialized:
            scene = get_scene()
            
            # Update render engine
            if change['name'] == 'render_engine':
                scene.render.engine = change['new']
                print(f"Render engine changed to: {change['new']}")
            
            # Update device (only for Cycles)
            elif change['name'] == 'render_device' and scene.render.engine == 'CYCLES':
                scene.cycles.device = change['new']
                print(f"Render device changed to: {change['new']}")
            
            # Mark update as needed and try to render
            self._update_needed = True
            self._update()

    def _update(self, force: bool = False) -> bool:
        """Update and render if needed (Three.js pattern: returns True if rendered)
        
        Similar to camera-controls.update(delta) which returns True if camera changed.
        Only renders if:
        1. Update is needed (_update_needed = True)
        2. Enough time has passed since last render (debounce) OR force=True
        
        Args:
            force: If True, render immediately regardless of debounce time
            
        Returns:
            bool: True if rendering occurred, False otherwise
        """
        if not self._update_needed:
            return False
        
        current_time = time.time()
        time_since_last_render = (current_time - self._last_render_time) * 1000.0  # ms
        
        # Check if enough time has passed since last render OR force render
        if force or time_since_last_render >= self._render_debounce_ms:
            # Update camera and render
            self._last_render_time = current_time
            self._update_needed = False  # Clear flag after rendering
            self._update_camera_and_render()
            return True
        
        # Not enough time has passed, but update is still needed
        return False

    def _update_camera_and_render(self):
        """Update camera and render (called after debounce or immediately)"""
        try:
            # Get camera target (default if not set)
            target = tuple(self.camera_target) if hasattr(self, 'camera_target') else (0, 0, 1)
            
            # Update camera
            update_camera_spherical(
                self.camera_distance,
                self.camera_angle_x, 
                self.camera_angle_z,
                target=target,
                width=self.width,
                height=self.height
            )
            
            # Render (now uses Viewer Node with write_still=False - no file I/O!)
            start_time = time.time()
            pixels, w, h = render_to_pixels()
            render_time = int((time.time() - start_time) * 1000)
            
            if pixels is not None:
                # Update display with actual rendered dimensions
                # (Viewer Node may return different size than requested)
                self._update_display(pixels, w, h)
                self.status = f"Rendered {w}x{h} ({render_time}ms)"
            else:
                self.status = "Render failed"
                
        except Exception as e:
            logger.error(f"Camera update failed: {e}")
            self.status = f"Error: {str(e)}"
            traceback.print_exc()

    def _update_display(self, pixels_array: np.ndarray, w: int, h: int):
        """Update display from pixel array - synchronizes width/height with actual rendered dimensions
        
        The Viewer Node may return different dimensions than requested (e.g., 256x256 instead of 512x512).
        We need to synchronize the widget traits to match the actual rendered dimensions.
        """
        try:
            self._pixel_array = pixels_array
            
            # Convert to base64 (raw RGBA pixel data, not PNG)
            # Frontend expects raw pixel bytes, not a PNG image
            pixels_bytes = pixels_array.tobytes()
            image_b64 = base64.b64encode(pixels_bytes).decode('ascii')
            
            # Store original requested dimensions for debug message
            original_w = self.width
            original_h = self.height
            
            # Update ALL traits together within hold_sync to prevent race conditions
            # This ensures width/height/image_data are all updated atomically
            with self.hold_sync():
                # Update dimensions if they changed (Viewer Node may return different size)
                if original_w != w or original_h != h:
                    self.width = w
                    self.height = h
                    logger.debug(f"Render dimensions adjusted: {w}x{h} (requested: {original_w}x{original_h})")
                
                # Update image data - this triggers the frontend update with all data ready
                self.image_data = image_b64
            
        except Exception as e:
            logger.error(f"Display update failed: {e}")
            raise

    def initialize(self):
        """Initialize scene"""
        if self.is_initialized:
            self.status = "Already initialized"
            return
        
        try:
            self.status = "Setting up scene..."
            
            # Clean slate
            clear_scene()
            
            # Setup rendering with current engine
            setup_rendering(self.width, self.height, self.render_engine)
            
            # Fast EEVEE settings
            scene = get_scene()
            if self.render_engine == 'BLENDER_EEVEE_NEXT':
                scene.eevee.taa_render_samples = 16
                scene.eevee.use_raytracing = False
                # Feature detection instead of version checks
                if hasattr(scene.eevee, 'use_ssr'):
                    scene.eevee.use_ssr = True  # Screen Space Reflections
                if hasattr(scene.eevee, 'use_sss'):
                    scene.eevee.use_sss = True  # Subsurface Scattering
            elif self.render_engine == 'CYCLES':
                scene.cycles.samples = 64
                scene.cycles.device = self.render_device
                # Feature detection instead of version checks
                if hasattr(scene.cycles, 'use_adaptive_sampling'):
                    scene.cycles.use_adaptive_sampling = True
            
            # Setup camera and get initial position
            camera = setup_camera(width=self.width, height=self.height)
            distance, angle_x, angle_z = calculate_spherical_from_position(camera.location)
            
            # Set widget traits from actual camera
            self._just_initialized = True
            with self.hold_sync():
                self.camera_distance = distance
                self.camera_angle_x = angle_x
                self.camera_angle_z = angle_z
            
            # Scene setup
            setup_lighting()
            setup_world_background(color=(0.8, 0.8, 0.9), strength=1.0)
            create_test_cube()
            create_suzanne()
            
            bpy.context.view_layer.update()
            
            self.is_initialized = True
            
            # Initial render
            self._update_camera_and_render()
            self._just_initialized = False
            
            logger.info("Widget initialization complete")
            
        except Exception as e:
            self.is_initialized = False
            self._just_initialized = False
            self.status = f"Error: {str(e)}"
            logger.error(f"Initialization failed: {e}")
            traceback.print_exc()

    def render(self):
        """Render with error handling"""
        if not self.is_initialized:
            logger.info("Widget not initialized, initializing now...")
            self.initialize()
            return
            
        self._update_camera_and_render()

    def set_resolution(self, width: int, height: int):
        """Set render resolution"""
        self.width = width
        self.height = height
        
        # Update Blender render settings
        scene = get_scene()
        scene.render.resolution_x = width
        scene.render.resolution_y = height
        
        # Set pixel aspect ratio to 1:1 (square pixels)
        scene.render.pixel_aspect_x = 1.0
        scene.render.pixel_aspect_y = 1.0
        
        # Update camera sensor fit to match new aspect ratio
        if scene.camera:
            scene.camera.data.sensor_fit = 'AUTO'
        
        self.status = f"Resolution set to {width}x{height}"
        self.render()

    def set_render_engine(self, engine: str):
        """Set render engine (BLENDER_EEVEE_NEXT or CYCLES)"""
        if engine in ['BLENDER_EEVEE_NEXT', 'CYCLES']:
            self.render_engine = engine
        else:
            logger.warning(f"Invalid render engine: {engine}")
    
    def set_gpu_backend(self, backend: str = 'VULKAN') -> bool:
        """Set GPU backend (VULKAN or OPENGL)
        
        Blender 4.5+ supports Vulkan backend for improved performance.
        Note: May require widget re-initialization for full effect.
        
        Args:
            backend: Either 'VULKAN' or 'OPENGL'
            
        Returns:
            True if backend was set successfully
        """
        result = set_gpu_backend(backend)
        if result:
            self.status = f"GPU backend set to {backend}"
        else:
            self.status = f"Failed to set GPU backend to {backend}"
        return result
    
    def get_gpu_backend(self) -> Optional[str]:
        """Get current GPU backend
        
        Returns:
            Current backend ('VULKAN' or 'OPENGL') or None if unavailable
        """
        return get_gpu_backend()

    # ========== Extension Management ==========
    
    def list_repositories(self) -> typing.List[typing.Dict]:
        """List all extension repositories"""
        return extension_manager.list_repositories()
    
    def list_extensions(self, repo_name: typing.Optional[str] = None) -> typing.List[typing.Dict]:
        """List extensions from repositories"""
        return extension_manager.list_extensions(repo_name)
    
    def enable_extension(self, pkg_id: str, repo_module: typing.Optional[str] = None) -> bool:
        """Enable an extension"""
        if repo_module:
            return extension_manager.enable_extension(repo_module, pkg_id)
        
        # Find extension in repositories
        for ext in self.list_extensions():
            if ext['id'] == pkg_id:
                repos = self.list_repositories()
                for repo in repos:
                    if repo['name'] == ext.get('repository'):
                        if extension_manager.enable_extension(repo['module'], pkg_id):
                            self.status = f"Enabled: {ext.get('name', pkg_id)}"
                            return True
        
        self.status = f"Extension not found: {pkg_id}"
        return False
    
    def disable_extension(self, pkg_id: str, repo_module: typing.Optional[str] = None) -> bool:
        """Disable an extension"""
        if repo_module:
            return extension_manager.disable_extension(repo_module, pkg_id)
        
        # Find extension in repositories
        for ext in self.list_extensions():
            if ext['id'] == pkg_id:
                repos = self.list_repositories()
                for repo in repos:
                    if repo['name'] == ext.get('repository'):
                        if extension_manager.disable_extension(repo['module'], pkg_id):
                            self.status = f"Disabled: {ext.get('name', pkg_id)}"
                            return True
        
        self.status = f"Extension not found: {pkg_id}"
        return False
    
    def sync_repositories(self):
        """Sync all repositories"""
        if not bpy.app.online_access:
            self.status = "Online access required"
            return False
        
        try:
            extension_manager.sync_all_repositories()
            self.status = "Repositories synced"
            return True
        except Exception as e:
            self.status = f"Sync failed: {str(e)}"
            return False
    
    def install_extension_from_file(
        self, 
        filepath: typing.Union[str, Path], 
        repo_module: typing.Optional[str] = None,
        enable_on_install: bool = True
    ) -> bool:
        """Install extension from local file"""
        repos = self.list_repositories()
        if not repos:
            self.status = "No repositories available"
            return False
        
        # Use first user repository if not specified
        if not repo_module:
            user_repos = [r for r in repos if r['source'] == 'USER']
            if not user_repos:
                self.status = "No user repository available"
                return False
            repo_module = user_repos[0]['module']
        
        try:
            extension_manager.install_from_file(str(filepath), repo_module, enable_on_install)
            self.status = f"Installed from {Path(filepath).name}"
            return True
        except Exception as e:
            self.status = f"Install failed: {str(e)}"
            return False
    
    def install_extension(
        self,
        source: str,
        pkg_id: str = "",
        enable_on_install: bool = True
    ) -> bool:
        """Install extension from any source

        Universal installation method. Automatically enables online access if needed.

        Examples:
            # Install by package ID (searches and installs)
            widget.install_extension("molecularnodes")

            # Install from URL
            widget.install_extension("https://extensions.blender.org/...", pkg_id="molecularnodes")

            # Install from local file
            widget.install_extension("/path/to/extension.zip", pkg_id="my_extension")

        Args:
            source: Package ID, download URL, or local file path
            pkg_id: Package ID (required for URLs and files)
            enable_on_install: Enable the extension after installation

        Returns:
            True if installation succeeded
        """
        try:
            self.status = f"Installing extension..."
            result = extension_manager.install_extension(source, pkg_id, enable_on_install)
            if result:
                self.status = f"Installation complete"
            else:
                self.status = "Installation failed"
            return result
        except Exception as e:
            self.status = f"Install failed: {str(e)}"
            return False
    
    def upgrade_extensions(self, active_only: bool = False) -> bool:
        """Upgrade extensions to latest versions"""
        try:
            extension_manager.upgrade_all_extensions(active_only)
            self.status = "Extensions upgraded"
            return True
        except Exception as e:
            self.status = f"Upgrade failed: {str(e)}"
            return False
    
    def search_extensions(self, query: str, limit: int = 50, category: typing.Optional[str] = None) -> typing.List[typing.Dict]:
        """Search extensions online

        Automatically enables online access if needed.

        Args:
            query: Search query string
            limit: Maximum number of results (default: 50)
            category: Optional category filter (e.g., 'add-on', 'theme')

        Returns:
            List of extension dictionaries with id, name, tagline, version, type, download_url, homepage_url
        """
        try:
            self.status = "Searching extensions..."
            results = extension_manager.search_extensions(query, limit, category)
            
            if results:
                self.status = f"Found {len(results)} extensions"
            else:
                self.status = "No extensions found"
            
            return results
        except Exception as e:
            self.status = f"Search failed: {str(e)}"
            return []
    
    def search_and_install(
        self,
        query: str,
        index: int = 0,
        enable_on_install: bool = True
    ) -> bool:
        """Search and install extension in one step
        
        This is the most convenient way to install extensions - just provide a search query
        and it will install the first result.
        
        Example:
            widget.search_and_install("molecular nodes")
            widget.search_and_install("node wrangler", index=0)
        
        Args:
            query: Search query string
            index: Index of result to install (default: 0 = first result)
            enable_on_install: Enable the extension after installation
        
        Returns:
            True if installation started successfully, False otherwise
        """
        if not bpy.app.online_access:
            self.status = "Online access required"
            return False
        
        # Search extensions
        results = self.search_extensions(query, limit=20)
        
        if not results:
            self.status = f"No extensions found for: {query}"
            return False
        
        if index >= len(results):
            self.status = f"Index {index} out of range. Found {len(results)} results"
            return False
        
        # Get selected extension
        selected = results[index]
        download_url = selected.get('download_url', '')
        pkg_id = selected.get('id', '')

        if not download_url:
            self.status = f"No download URL available for: {selected.get('name', 'Unknown')}"
            return False

        if not pkg_id:
            self.status = f"No package ID available for: {selected.get('name', 'Unknown')}"
            return False

        # Install extension
        self.status = f"Installing: {selected.get('name', 'Unknown')}..."
        result = self.install_extension(download_url, pkg_id=pkg_id, enable_on_install=enable_on_install)
        
        if result:
            self.status = f"Installed: {selected.get('name', 'Unknown')}"
        else:
            self.status = f"Installation failed for: {selected.get('name', 'Unknown')}"
        
        return result
    
    def uninstall_extension(self, pkg_id: str, repo_index: int = -1) -> bool:
        """Uninstall an extension
        
        Args:
            pkg_id: Extension package ID
            repo_index: Repository index (-1 for auto-select)
        
        Returns:
            True if uninstallation started successfully
        """
        try:
            extension_manager.uninstall_extension(pkg_id, repo_index)
            self.status = f"Uninstalled: {pkg_id}"
            return True
        except Exception as e:
            self.status = f"Uninstall failed: {str(e)}"
            return False
    
    # Legacy addon support
    def list_legacy_addons(self) -> typing.List[typing.Dict]:
        """List legacy addons (pre-4.2 style)"""
        return extension_manager.list_legacy_addons()
    
    def enable_legacy_addon(self, module_name: str) -> bool:
        """Enable a legacy addon"""
        try:
            extension_manager.enable_legacy_addon(module_name)
            self.status = f"Enabled legacy: {module_name}"
            return True
        except Exception as e:
            self.status = f"Failed: {str(e)}"
            return False
    
    def disable_legacy_addon(self, module_name: str) -> bool:
        """Disable a legacy addon"""
        try:
            extension_manager.disable_legacy_addon(module_name)
            self.status = f"Disabled legacy: {module_name}"
            return True
        except Exception as e:
            self.status = f"Failed: {str(e)}"
            return False

    # ========== Scene Management Methods ==========
    
    def clear_scene(self):
        """Clear all objects from the scene"""
        clear_scene()
        self.status = "Scene cleared"
        
    def setup_camera(self, distance=8.0, target=(0, 0, 0)):
        """Setup or reset camera"""
        camera = setup_camera(distance=distance, target=target)
        # Update widget camera parameters
        distance, angle_x, angle_z = calculate_spherical_from_position(camera.location)
        with self.hold_sync():
            self.camera_distance = distance
            self.camera_angle_x = angle_x
            self.camera_angle_z = angle_z
        self.status = "Camera reset"
        return camera
        
    def setup_lighting(self, **kwargs):
        """Setup basic lighting"""
        setup_lighting(**kwargs)
        self.status = "Lighting setup"

    def setup_world_background(self, **kwargs):
        """Setup world background"""
        setup_world_background(**kwargs)
        self.status = "World background setup"

    # ========== Object Creation Methods ==========
    
    def create_icosphere(self, **kwargs):
        """Create an icosphere"""
        return create_icosphere(**kwargs)
    
    def create_torus(self, **kwargs):
        """Create a torus"""
        return create_torus(**kwargs)
        
    # ========== Material Methods ==========
    
    def create_material(self, name: str, **kwargs):
        """Create material with PBR parameters"""
        return create_material(name, **kwargs)
        
    def create_preset_material(self, name: str, preset: str):
        """Create material from preset (gold, glass, etc.)"""
        return create_preset_material(name, preset)
        
    def assign_material(self, obj, material):
        """Assign material to object"""
        assign_material(obj, material)
        
    # ========== Compositor Methods ==========
    
    def setup_compositor(self):
        """Setup basic compositor"""
        return setup_compositor()
    
    def setup_extended_compositor(self):
        """Setup compositor with extended post-processing capabilities"""
        return setup_extended_compositor()
        
    def add_glare(self, intensity=1.0):
        """Add glare effect to compositor (legacy)"""
        return add_glare_node(intensity)
    
    def add_bloom_glare(self, intensity=1.0, threshold=1.0):
        """Add bloom/glare effect with more control"""
        return add_bloom_glare(intensity, threshold)
    
    def add_color_correction(
        self, 
        brightness=0.0, 
        contrast=0.0, 
        saturation=1.0,
        gain=(1.0, 1.0, 1.0),
        gamma=1.0
    ):
        """Add comprehensive color correction"""
        return add_color_correction(brightness, contrast, saturation, gain, gamma)
    
    def add_vignette(self, amount=0.3, center=(0.5, 0.5)):
        """Add vignette effect"""
        return add_vignette(amount, center)
    
    def add_film_grain(self, amount=0.05):
        """Add film grain effect"""
        return add_film_grain(amount)
    
    def add_chromatic_aberration(self, amount=0.001):
        """Add chromatic aberration effect"""
        return add_chromatic_aberration(amount)
    
    def add_sharpen(self, amount=0.1):
        """Add sharpening filter"""
        return add_sharpen(amount)
    
    def add_motion_blur(self, samples=8, shutter=0.5):
        """Enable motion blur in render settings"""
        add_motion_blur(samples, shutter)
        self.status = "Motion blur enabled"
    
    def add_depth_of_field(
        self, 
        focus_object=None,
        focus_distance=10.0,
        fstop=2.8
    ):
        """Setup depth of field for camera"""
        add_depth_of_field(focus_object, focus_distance, fstop)
        self.status = f"DOF enabled: f/{fstop}"
    
    def reset_compositor(self):
        """Reset compositor to default state"""
        reset_compositor()
        self.status = "Compositor reset"
        
    # ========== Import/Export Methods ==========
    
    def import_gltf(self, file_path: typing.Union[str, Path], **kwargs):
        """Import GLTF/GLB file"""
        if not self.is_initialized:
            self.initialize()
        
        try:
            objects = import_gltf(file_path, **kwargs)
            self.status = f"Imported {len(objects)} objects from GLTF"
            self._update_view()
            self._update_camera_and_render()
            return objects
        except Exception as e:
            self.status = f"GLTF import failed: {str(e)}"
            logger.error(f"GLTF import error: {e}")
            return []
    
    def export_gltf(self, file_path: typing.Union[str, Path], selected_only=False, **kwargs):
        """Export scene or selected objects as GLTF/GLB"""
        try:
            export_gltf(file_path, selected_only=selected_only, **kwargs)
            self.status = f"Exported to {Path(file_path).name}"
        except Exception as e:
            self.status = f"GLTF export failed: {str(e)}"
            print(f"GLTF export error: {e}")
    
    def import_usd(self, file_path: typing.Union[str, Path], **kwargs):
        """Import USD/USDZ file"""
        if not self.is_initialized:
            self.initialize()
        
        try:
            objects = import_usd(file_path, **kwargs)
            self.status = f"Imported {len(objects)} objects from USD"
            self._update_view()
            self._update_camera_and_render()
            return objects
        except Exception as e:
            self.status = f"USD import failed: {str(e)}"
            print(f"USD import error: {e}")
            return []
    
    def export_usd(self, file_path: typing.Union[str, Path], selected_only=False, **kwargs):
        """Export scene or selected objects as USD/USDZ"""
        try:
            export_usd(file_path, selected_only=selected_only, **kwargs)
            self.status = f"Exported to {Path(file_path).name}"
        except Exception as e:
            self.status = f"USD export failed: {str(e)}"
            print(f"USD export error: {e}")
    
    def import_alembic(self, file_path: typing.Union[str, Path], **kwargs):
        """Import Alembic (.abc) file"""
        if not self.is_initialized:
            self.initialize()
        
        try:
            objects = import_alembic(file_path, **kwargs)
            self.status = f"Imported {len(objects)} objects from Alembic"
            self._update_view()
            self._update_camera_and_render()
            return objects
        except Exception as e:
            self.status = f"Alembic import failed: {str(e)}"
            print(f"Alembic import error: {e}")
            return []
    
    def export_alembic(self, file_path: typing.Union[str, Path], selected_only=False, **kwargs):
        """Export scene as Alembic (.abc) file"""
        try:
            export_alembic(file_path, selected=selected_only, **kwargs)
            self.status = f"Exported to {Path(file_path).name}"
        except Exception as e:
            self.status = f"Alembic export failed: {str(e)}"
            print(f"Alembic export error: {e}")
    
    def export_scene_as_parquet(self, file_path: typing.Union[str, Path], include_metadata=True):
        """Export entire scene data as Parquet file"""
        try:
            export_scene_as_parquet(file_path, include_metadata)
            self.status = f"Scene exported to {Path(file_path).name}"
        except Exception as e:
            self.status = f"Parquet export failed: {str(e)}"
            print(f"Parquet export error: {e}")
    
    def import_scene_from_parquet(self, file_path: typing.Union[str, Path]):
        """Import scene data from Parquet file"""
        if not self.is_initialized:
            self.initialize()
        
        try:
            objects = import_scene_from_parquet(file_path)
            self.status = f"Imported {len(objects)} objects from Parquet"
            self._update_view()
            self._update_camera_and_render()
            return objects
        except Exception as e:
            self.status = f"Parquet import failed: {str(e)}"
            print(f"Parquet import error: {e}")
            return []
    
    # ========== Blender File Methods ==========
    
    def load_blend(self, file_path: typing.Union[str, Path], load_ui: bool = False):
        """Load a Blender (.blend) file"""
        if not self.is_initialized:
            self.initialize()
        
        try:
            load_blend(file_path, load_ui=load_ui)
            self.status = f"Loaded {Path(file_path).name}"
            self._update_camera_and_render()
        except Exception as e:
            self.status = f"Load failed: {str(e)}"
            logger.error(f"Blend load error: {e}")
    
    def save_blend(self, file_path: typing.Union[str, Path], compress: bool = True):
        """Save current scene as Blender (.blend) file"""
        try:
            save_blend(file_path, compress=compress)
            self.status = f"Saved {Path(file_path).name}"
        except Exception as e:
            self.status = f"Save failed: {str(e)}"
            logger.error(f"Blend save error: {e}")
    
    def link_from_blend(
        self,
        file_path: typing.Union[str, Path],
        category: str = 'Object',
        name: Optional[str] = None
    ):
        """Link data from another Blender file (reference, not copy)"""
        if not self.is_initialized:
            self.initialize()
        
        try:
            linked = link_from_blend(file_path, category=category, name=name)
            self.status = f"Linked {len(linked)} {category}(s) from {Path(file_path).name}"
            self._update_camera_and_render()
            return linked
        except Exception as e:
            self.status = f"Link failed: {str(e)}"
            logger.error(f"Blend link error: {e}")
            return []
    
    def append_from_blend(
        self,
        file_path: typing.Union[str, Path],
        category: str = 'Object',
        name: Optional[str] = None
    ):
        """Append data from another Blender file (copy, not reference)"""
        if not self.is_initialized:
            self.initialize()
        
        try:
            appended = append_from_blend(file_path, category=category, name=name)
            self.status = f"Appended {len(appended)} {category}(s) from {Path(file_path).name}"
            self._update_camera_and_render()
            return appended
        except Exception as e:
            self.status = f"Append failed: {str(e)}"
            logger.error(f"Blend append error: {e}")
            return []
        
    # ========== Data Import Methods (existing) ==========

    def import_data(
        self, 
        file_path: typing.Union[str, Path],
        as_type: str = "points",
        **kwargs
    ):
        """Import data from various formats"""
        if not self.is_initialized:
            self.initialize()
        
        file_path = Path(file_path)
        
        try:
            if as_type == "points":
                collection = import_data_as_points(file_path, **kwargs)
                self.status = f"Imported {file_path.name} as point cloud"
                
            elif as_type == "curve":
                if 'df' in kwargs:
                    df = kwargs.pop('df')
                    obj = import_dataframe_as_curve(df, **kwargs)
                else:
                    df = read_data_file(file_path)
                    obj = import_dataframe_as_curve(df, curve_name=file_path.stem, **kwargs)
                self.status = f"Imported {file_path.name} as curve"
                
            elif as_type == "series":
                value_columns = kwargs.pop('value_columns', None)
                if not value_columns:
                    raise ValueError("value_columns required for series import")
                curves = import_multiple_series(file_path, value_columns, **kwargs)
                self.status = f"Imported {len(curves)} series from {file_path.name}"
                
            else:
                raise ValueError(f"Unknown as_type: {as_type}. Use 'points', 'curve', or 'series'")
            
            # Update view and render
            bpy.context.view_layer.update()
            self._update_camera_and_render()
            
        except Exception as e:
            self.status = f"Import failed: {str(e)}"
            print(f"Import error: {e}")
            traceback.print_exc()

    def batch_import(
        self,
        file_patterns: typing.List[str],
        **kwargs
    ):
        """Import multiple files at once"""
        if not self.is_initialized:
            self.initialize()
        
        try:
            collections = batch_import_data(file_patterns, **kwargs)
            self.status = f"Batch imported {len(collections)} files"
            
            # Update view and render
            bpy.context.view_layer.update()
            self._update_camera_and_render()
            
        except Exception as e:
            self.status = f"Batch import failed: {str(e)}"
            print(f"Batch import error: {e}")
            traceback.print_exc()

    def import_data_with_metadata(self, file_path: typing.Union[str, Path], **kwargs):
        """Import data with metadata stored as custom properties"""
        return import_data_with_metadata(file_path, **kwargs)

    # ========== Utility Methods ==========

    def _update_view(self):
        """Update view layer and dependency graph"""
        bpy.context.view_layer.update()
        bpy.context.evaluated_depsgraph_get()

    # ========== Convenience Properties ==========

    @property
    def context(self):
        """Access to bpy.context."""
        self._ensure_bpy_loaded()
        return bpy.context

    @property
    def scene(self):
        """Access to bpy.context.scene."""
        self._ensure_bpy_loaded()
        return bpy.context.scene

    @property
    def active_object(self):
        """Access to bpy.context.active_object."""
        self._ensure_bpy_loaded()
        return getattr(bpy.context, 'active_object', None)

    @property
    def selected_objects(self):
        """Access to bpy.context.selected_objects."""
        self._ensure_bpy_loaded()
        return getattr(bpy.context, 'selected_objects', [])

    @property
    def data(self):
        """Access to bpy.data."""
        self._ensure_bpy_loaded()
        return bpy.data

    @property
    def ops(self):
        """Access to bpy.ops."""
        self._ensure_bpy_loaded()
        return bpy.ops

    @property
    def objects(self):
        """Access to bpy.data.objects."""
        self._ensure_bpy_loaded()
        return bpy.data.objects

    @property
    def camera(self):
        """Access to bpy.context.scene.camera."""
        self._ensure_bpy_loaded()
        return bpy.context.scene.camera

    def _debug_info(self):
        """Print debug information"""
        print("\n=== DEBUG INFO ===")
        print(f"Widget initialized: {self.is_initialized}")
        print(f"Widget status: {self.status}")
        print(f"Widget size: {self.width}x{self.height}")
        print(f"Camera: distance={self.camera_distance}, angles=({self.camera_angle_x}, {self.camera_angle_z})")
        
        scene = get_scene()
        if scene.camera:
            print(f"\nCamera location: {scene.camera.location}")
            print(f"Camera rotation: {scene.camera.rotation_euler}")
        print(f"Scene objects: {[obj.name for obj in bpy.data.objects]}")
        print(f"Render engine: {scene.render.engine}")
        print(f"Resolution: {scene.render.resolution_x}x{scene.render.resolution_y}")
        print("==================\n")

    def __repr__(self):
        """Ensure initialization before display"""
        # Lazy initialization check - ensure widget is initialized when displayed
        # This helps in cases where auto_init might have failed or wasn't called
        if not self.is_initialized and not hasattr(self, '_initialization_failed'):
            try:
                self.initialize()
            except Exception as e:
                # Mark as failed to avoid repeated attempts
                self._initialization_failed = True
                logger.error(f"Auto-initialization failed in __repr__: {e}")
                return f"<BpyWidget: Initialization failed - {str(e)}>"
        
        # Return standard representation
        return super().__repr__()

    def __del__(self):
        """Cleanup on widget destruction - reset update flag"""
        if hasattr(self, '_update_needed'):
            self._update_needed = False


# Legacy alias
BlenderWidget = BpyWidget
