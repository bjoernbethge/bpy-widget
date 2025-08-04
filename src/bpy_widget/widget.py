"""
Blender widget for Marimo - Simplified high-performance version
"""
import base64
import os
from pathlib import Path
import typing

import anywidget
import numpy as np
import traitlets

import bpy

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
from .core.materials import (
    assign_material,
    create_glass_material,
    create_metal_material,
    create_pbr_material,
)
from .core.nodes import add_glare_node, setup_compositor
from .core.rendering import (
    render_to_pixels,
    setup_rendering,
)
from .utils import (
    clear_scene,
    create_suzanne,
    create_test_cube,
    setup_lighting,
    setup_world_background,
)

STATIC_DIR = Path(__file__).parent / 'static'

__all__ = ['BpyWidget']


class BpyWidget(anywidget.AnyWidget):
    """Blender widget with interactive camera control"""
    
    _esm = (STATIC_DIR / 'widget.js').read_text()
    _css = (STATIC_DIR / 'widget.css').read_text()
    
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
    
    # Performance settings
    msg_throttle = traitlets.Int(2).tag(sync=True)

    def __init__(self, width: int = 512, height: int = 512, auto_init: bool = True, **kwargs):
        """Initialize widget"""
        super().__init__(**kwargs)
        self.width = width
        self.height = height
        self._pixel_array: typing.Optional[np.ndarray] = None
        self._just_initialized = False
        
        print(f"BpyWidget created: {width}x{height}")
        
        if auto_init:
            self.initialize()

    @traitlets.observe('camera_distance', 'camera_angle_x', 'camera_angle_z')
    def _on_camera_change(self, change):
        """Handle camera parameter changes from frontend"""
        if self.is_initialized and not self._just_initialized:
            self.update_camera_and_render()

    def update_camera_and_render(self):
        """Update camera and render"""
        try:
            # Update camera
            update_camera_spherical(
                self.camera_distance,
                self.camera_angle_x, 
                self.camera_angle_z
            )
            
            # Render
            pixels, w, h = render_to_pixels()
            
            if pixels is not None:
                self._update_display(pixels, w, h)
                self.status = f"Rendered {w}x{h}"
            else:
                self.status = "Render failed"
                
        except Exception as e:
            print(f"Camera update failed: {e}")
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
            print(f"Display update failed: {e}")
            raise

    def initialize(self):
        """Initialize scene"""
        if self.is_initialized:
            self.status = "Already initialized"
            return
        
        print("\n=== WIDGET INITIALIZATION START ===")
        try:
            self.status = "Setting up scene..."
            
            # Clean slate
            clear_scene()
            
            # Setup rendering - always EEVEE for performance
            setup_rendering(self.width, self.height, 'BLENDER_EEVEE_NEXT')
            
            # Fast EEVEE settings
            scene = bpy.context.scene
            scene.eevee.taa_render_samples = 16
            scene.eevee.use_raytracing = False
            
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
            
            print(f"✓ Scene setup complete")
            print(f"✓ Camera initialized at distance={distance:.2f}")
            
            self.is_initialized = True
            
            # Initial render
            self.update_camera_and_render()
            self._just_initialized = False
            print("✓ Widget initialization complete")
            
        except Exception as e:
            self.is_initialized = False
            self._just_initialized = False
            self.status = f"Error: {str(e)}"
            print(f"✗ Initialization failed: {e}")
            import traceback
            traceback.print_exc()
        
        print("=== WIDGET INITIALIZATION END ===\n")

    def render(self):
        """Render with error handling"""
        if not self.is_initialized:
            print("Widget not initialized, initializing now...")
            self.initialize()
            return
            
        self.update_camera_and_render()

    def set_resolution(self, width: int, height: int):
        """Set render resolution"""
        self.width = width
        self.height = height
        
        # Update Blender render settings
        scene = bpy.context.scene
        scene.render.resolution_x = width
        scene.render.resolution_y = height
        
        self.status = f"Resolution set to {width}x{height}"
        self.render()

    # ========== Scene Management Methods ==========
    
    def clear_scene(self):
        """Clear all objects from the scene"""
        clear_scene()
        self.status = "Scene cleared"
        
    def setup_lighting(self, **kwargs):
        """Setup scene lighting"""
        setup_lighting(**kwargs)
        self.status = "Lighting updated"
        
    def setup_world_background(self, color=(0.05, 0.05, 0.05), strength=1.0):
        """Setup world background"""
        setup_world_background(color=color, strength=strength)
        self.status = "Background updated"
        
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
        
    # ========== Object Creation Methods ==========
    
    def create_test_cube(self, **kwargs):
        """Create a test cube"""
        return create_test_cube(**kwargs)
        
    def create_suzanne(self, **kwargs):
        """Create Suzanne monkey head"""
        return create_suzanne(**kwargs)
        
    # ========== Material Methods ==========
    
    def create_glass_material(self, name="Glass", **kwargs):
        """Create glass material"""
        return create_glass_material(name, **kwargs)
        
    def create_metal_material(self, name="Metal", **kwargs):
        """Create metal material"""
        return create_metal_material(name, **kwargs)
        
    def create_pbr_material(self, name="PBR", **kwargs):
        """Create comprehensive PBR material"""
        return create_pbr_material(name, **kwargs)
        
    def assign_material(self, obj, material):
        """Assign material to object"""
        assign_material(material, obj)
        
    # ========== Compositor Methods ==========
    
    def setup_compositor(self):
        """Setup basic compositor"""
        return setup_compositor()
        
    def add_glare(self, intensity=1.0):
        """Add glare effect to compositor"""
        return add_glare_node(intensity)
        
    # ========== Data Import Methods ==========

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
            self.update_camera_and_render()
            
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
            self.update_camera_and_render()
            
        except Exception as e:
            self.status = f"Batch import failed: {str(e)}"
            print(f"Batch import error: {e}")
            import traceback
            traceback.print_exc()

    def import_data_with_metadata(self, file_path: typing.Union[str, Path], **kwargs):
        """Import data with metadata stored as custom properties"""
        return import_data_with_metadata(file_path, **kwargs)

    # ========== Utility Methods ==========

    def update_view(self):
        """Update view layer and dependency graph"""
        bpy.context.view_layer.update()
        bpy.context.evaluated_depsgraph_get()

    def debug_info(self):
        """Print debug information"""
        print("\n=== DEBUG INFO ===")
        print(f"Widget initialized: {self.is_initialized}")
        print(f"Widget status: {self.status}")
        print(f"Widget size: {self.width}x{self.height}")
        print(f"Camera: distance={self.camera_distance}, angles=({self.camera_angle_x}, {self.camera_angle_z})")
        
        scene = bpy.context.scene
        if scene.camera:
            print(f"\nCamera location: {scene.camera.location}")
            print(f"Camera rotation: {scene.camera.rotation_euler}")
        print(f"Scene objects: {[obj.name for obj in bpy.data.objects]}")
        print(f"Render engine: {scene.render.engine}")
        print(f"Resolution: {scene.render.resolution_x}x{scene.render.resolution_y}")
        print("==================\n")

    # ========== Legacy properties for backward compatibility ==========
    
    @property
    def scene(self) -> bpy.types.Scene:
        return bpy.context.scene

    @property
    def objects(self) -> dict:
        return {obj.name: obj for obj in bpy.data.objects}

    @property
    def ops(self):
        return bpy.ops

    @property
    def data(self):
        return bpy.data

    @property
    def context(self):
        return bpy.context


# Legacy alias
BlenderWidget = BpyWidget
