"""Pytest configuration and fixtures for bpy-widget tests"""
import sys
import warnings

import bpy
import pytest

# Suppress Blender font and color management warnings in tests
warnings.filterwarnings('ignore', category=UserWarning, module='imbuf')
warnings.filterwarnings('ignore', message='.*Color management.*', category=UserWarning)
warnings.filterwarnings('ignore', message='.*OpenColorIO.*', category=UserWarning)

# Suppress stderr output from Blender's C++ code (font warnings, etc.)
# These warnings come from C++ and can't be caught with Python warnings

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
            "color management:",
            "opencolorio error",
            "colormanagement",
            "scene view",
            "using fallback mode",
        ]):
            return len(text)  # Return length to prevent errors
        return self.original.write(text)

# Apply filter only if stderr is not already wrapped
if not hasattr(sys.stderr, '_bpy_widget_filtered'):
    sys.stderr = FilteredStderr(sys.stderr)


@pytest.fixture
def clean_scene():
    """Fixture that ensures a clean Blender scene for each test"""
    # Configure color management FIRST to prevent AgX warnings
    scene = bpy.context.scene
    if hasattr(scene.view_settings, 'view_transform'):
        scene.view_settings.view_transform = 'Standard'
    if hasattr(scene.view_settings, 'look'):
        scene.view_settings.look = 'None'
    if hasattr(scene.display_settings, 'display_device'):
        scene.display_settings.display_device = 'sRGB'
    
    # Clear scene before test
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # Re-configure color management after factory settings
    scene = bpy.context.scene
    if hasattr(scene.view_settings, 'view_transform'):
        scene.view_settings.view_transform = 'Standard'
    if hasattr(scene.view_settings, 'look'):
        scene.view_settings.look = 'None'
    if hasattr(scene.display_settings, 'display_device'):
        scene.display_settings.display_device = 'sRGB'
    
    yield
    
    # Clean up after test
    bpy.ops.wm.read_factory_settings(use_empty=True)


@pytest.fixture
def test_cube(clean_scene):
    """Fixture that creates a test cube"""
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    # Use last created object as fallback for headless environments
    cube = getattr(bpy.context, 'active_object', None) or bpy.data.objects[-1]
    yield cube


@pytest.fixture
def test_camera(clean_scene):
    """Fixture that creates a test camera"""
    bpy.ops.object.camera_add(location=(7, -7, 5))
    # Use last created object as fallback for headless environments
    camera = getattr(bpy.context, 'active_object', None) or bpy.data.objects[-1]
    bpy.context.scene.camera = camera
    yield camera
