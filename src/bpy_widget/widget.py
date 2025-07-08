"""
Blender widget for Marimo - Clean functional approach
"""
import base64
import math
import os
import time
import typing

import anywidget
import numpy as np
import traitlets

# Clean function imports
from .core.camera import setup_camera, update_camera_spherical, calculate_spherical_from_position
from .core.rendering import setup_rendering, render_to_pixels, optimize_for_interactive
from .core.temp_files import cleanup_all

# Legacy utils for scene setup
from .utils import (
    bpy, clear_scene, setup_lighting, setup_world_background, 
    create_test_cube, create_suzanne
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')

__all__ = ['BpyWidget']


class BpyWidget(anywidget.AnyWidget):
    """Blender widget with interactive camera control"""
    
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
    
    # Static resources
    with open(os.path.join(STATIC_DIR, 'widget.css')) as f:
        _css = f.read()
    
    with open(os.path.join(STATIC_DIR, 'widget.js')) as f:
        _esm = f.read()

    def __init__(self, width: int = 512, height: int = 512, auto_init: bool = True, **kwargs):
        """Initialize widget"""
        super().__init__(**kwargs)
        self.width = width
        self.height = height
        self._pixel_array: typing.Optional[np.ndarray] = None
        self._just_initialized = False
        self._last_render_time = 0
        
        print(f"BpyWidget created: {width}x{height}")
        
        if auto_init:
            self.initialize()

    @traitlets.observe('camera_distance', 'camera_angle_x', 'camera_angle_z')
    def _on_camera_change(self, change):
        """Handle camera parameter changes from frontend"""
        if self.is_initialized and not self._just_initialized:
            self.update_camera_and_render()

    def update_camera_and_render(self):
        """Update camera and render - simple function calls"""
        try:
            start_time = time.time()
            
            # Simple function call, no object management
            update_camera_spherical(
                self.camera_distance,
                self.camera_angle_x, 
                self.camera_angle_z
            )
            
            # Simple function call
            pixels, w, h = render_to_pixels()
            
            if pixels is not None:
                self._update_display(pixels, w, h)
                render_time = (time.time() - start_time) * 1000  # ms
                self.status = f"Rendered {w}x{h} ({int(render_time)}ms)"
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
            
            # Batch update to reduce messages
            with self.hold_sync():
                self.image_data = image_b64
                if self.width != w:
                    self.width = w
                if self.height != h:
                    self.height = h
            
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
            
            clear_scene()
            setup_rendering(self.width, self.height)
            optimize_for_interactive()
            
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
            bpy.context.evaluated_depsgraph_get()
            
            print(f"✓ Scene setup complete")
            print(f"✓ Camera initialized at distance={distance:.2f}, angle_x={angle_x:.3f}, angle_z={angle_z:.3f}")
            
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
        print("==================\n")

    # Legacy properties for backward compatibility
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

    def __del__(self):
        """Cleanup on widget destruction"""
        cleanup_all()


# Legacy alias
BlenderWidget = BpyWidget
