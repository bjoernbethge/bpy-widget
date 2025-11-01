"""
Blender widget for Marimo - Simplified high-performance version
"""
import base64
import multiprocessing
import os
import typing
from pathlib import Path

import anywidget
import numpy as np
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
from .core.geometry import (
    create_icosphere,
    create_suzanne,
    create_test_cube,
    create_torus,
)

# Import new modules
from .core.io_handlers import (
    export_alembic,
    export_gltf,
    export_scene_as_parquet,
    export_usd,
    import_alembic,
    import_gltf,
    import_scene_from_parquet,
    import_usd,
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
    render_to_pixels,
    setup_rendering,
)
from .core.scene import (
    clear_scene,
    get_scene,
)

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
    width = traitlets.Int(512).tag(sync=True)
    height = traitlets.Int(512).tag(sync=True)
    status = traitlets.Unicode('Not initialized').tag(sync=True)
    is_initialized = traitlets.Bool(False).tag(sync=True)
    
    # Interactive camera traits
    camera_distance = traitlets.Float(8.0).tag(sync=True)
    camera_angle_x = traitlets.Float(1.1).tag(sync=True)  
    camera_angle_z = traitlets.Float(0.785).tag(sync=True)
    
    # Render settings
    render_engine = traitlets.Unicode('BLENDER_EEVEE_NEXT').tag(sync=True)
    render_device = traitlets.Unicode('CPU').tag(sync=True)
    
    # Performance settings
    msg_throttle = traitlets.Int(2).tag(sync=True)

    def __init__(self, width: int = 512, height: int = 512, auto_init: bool = True, **kwargs):
        """Initialize widget"""
        super().__init__(**kwargs)

        # Check if we're in marimo (which uses multiprocessing but widgets should work)
        self._is_marimo_context = False
        try:
            import inspect
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
            logger.info("Detected marimo context - using full Blender functionality")
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

        logger.info(f"BpyWidget created: {width}x{height}")

        # Check extension support
        if hasattr(bpy.context.preferences, 'extensions'):
            repos = extension_manager.list_repositories()
            if repos:
                logger.info(f"Extensions Platform: {len(repos)} repositories available")

        if auto_init:
            self.initialize()

    def _init_error_mode(self, width: int, height: int):
        """Initialize error mode for multiprocessing contexts"""
        self.width = width
        self.height = height
        self.status = "Error: Multiprocessing not supported"
        self.is_initialized = False

        # Create an error message image
        import numpy as np
        error_image = np.full((height, width, 3), [128, 64, 64], dtype=np.uint8)  # Dark red background

        # Add error text
        try:
            import cv2
            cv2.putText(error_image, "BpyWidget Error", (width//2-120, height//2-40),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
            cv2.putText(error_image, "Cannot run in multiprocessing", (width//2-180, height//2),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1)
            cv2.putText(error_image, "Use separate Python script", (width//2-140, height//2+30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
        except ImportError:
            # Fallback without cv2
            pass

        # Convert to base64
        import base64
        _, buffer = cv2.imencode('.png', error_image) if 'cv2' in locals() else (None, error_image.tobytes())
        if _ is not None:
            self.image_data = 'data:image/png;base64,' + base64.b64encode(buffer).decode()
        else:
            # Simple fallback without opencv
            self.image_data = f'data:image/png;base64,{base64.b64encode(error_image.tobytes()).decode()}'

    def _init_marimo_mode(self, width: int, height: int):
        """Initialize marimo-compatible mode with actual Blender functionality"""
        logger.info("Initializing BpyWidget in marimo-compatible mode")

        # In marimo mode, we CAN use bpy because we're in the main process
        # The issue was that we were detecting multiprocessing incorrectly
        self._ensure_bpy_loaded()

        self.width = width
        self.height = height
        self._pixel_array: typing.Optional[np.ndarray] = None
        self._just_initialized = False
        self.status = "Marimo mode: Initializing Blender..."
        self.is_initialized = False

        logger.info(f"BpyWidget marimo mode created: {width}x{height}")

        # Check extension support
        if hasattr(bpy.context.preferences, 'extensions'):
            repos = extension_manager.list_repositories()
            if repos:
                logger.info(f"Extensions Platform: {len(repos)} repositories available")

        # Auto-initialize in marimo mode
        self.initialize()
        logger.info("BpyWidget marimo mode initialized successfully")

    def _ensure_bpy_loaded(self):
        """Ensure bpy is loaded safely"""
        global bpy
        if bpy is None:
            try:
                import bpy
                logger.debug("bpy imported successfully")
                # Test if bpy is functional
                _ = bpy.app.version_string  # This should work
            except ImportError as e:
                logger.error(f"Failed to import bpy: {e}")
                raise
            except Exception as e:
                logger.error(f"bpy import succeeded but is not functional: {e}")
                logger.info("This usually means bpy_types is missing. Try reinstalling bpy.")
                raise ImportError(f"bpy is not functional: {e}") from e

    @traitlets.observe('camera_distance', 'camera_angle_x', 'camera_angle_z')
    def _on_camera_change(self, change):
        """Handle camera parameter changes from frontend"""
        if self.is_initialized and not self._just_initialized:
            self._update_camera_and_render()
    
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
            
            # Re-render with new settings
            self._update_camera_and_render()

    def _update_camera_and_render(self):
        """Update camera and render"""
        try:
            # Update camera
            update_camera_spherical(
                self.camera_distance,
                self.camera_angle_x, 
                self.camera_angle_z
            )
            
            # Render
            import time
            start_time = time.time()
            pixels, w, h = render_to_pixels()
            render_time = int((time.time() - start_time) * 1000)
            
            if pixels is not None:
                self._update_display(pixels, w, h)
                self.status = f"Rendered {w}x{h} ({render_time}ms)"
            else:
                self.status = "Render failed"
                
        except Exception as e:
            logger.error(f"Camera update failed: {e}")
            self.status = f"Error: {str(e)}"

    def _update_display(self, pixels_array: np.ndarray, w: int, h: int):
        """Update display from pixel array"""
        try:
            self._pixel_array = pixels_array
            
            # Convert to base64
            pixels_bytes = pixels_array.tobytes()
            image_b64 = base64.b64encode(pixels_bytes).decode('ascii')
            
            # Update only the image data
            with self.hold_sync():
                self.image_data = image_b64
            
        except Exception as e:
            logger.error(f"Display update failed: {e}")
            raise

    def initialize(self):
        """Initialize scene"""
        if self.is_initialized:
            self.status = "Already initialized"
            return
        
        logger.info("Widget initialization started")
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
            camera = setup_camera()
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
            
            logger.info("Scene setup complete")
            logger.info(f"Camera initialized at distance={distance:.2f}")
            logger.info(f"Render engine: {self.render_engine}")
            
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
            import traceback
            traceback.print_exc()
        
        logger.info("Widget initialization finished")

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
        
        self.status = f"Resolution set to {width}x{height}"
        self.render()

    def set_render_engine(self, engine: str):
        """Set render engine (BLENDER_EEVEE_NEXT or CYCLES)"""
        if engine in ['BLENDER_EEVEE_NEXT', 'CYCLES']:
            self.render_engine = engine
        else:
            logger.warning(f"Invalid render engine: {engine}")

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
    
    def upgrade_extensions(self, active_only: bool = False) -> bool:
        """Upgrade extensions to latest versions"""
        try:
            extension_manager.upgrade_all_extensions(active_only)
            self.status = "Extensions upgraded"
            return True
        except Exception as e:
            self.status = f"Upgrade failed: {str(e)}"
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
                    import polars as pl

                    from .core.data_import import read_data_file
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
            import traceback
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
            import traceback
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



# Legacy alias
BlenderWidget = BpyWidget
