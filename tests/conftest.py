"""Pytest configuration and fixtures for bpy-widget tests"""
import pytest
import bpy


@pytest.fixture
def clean_scene():
    """Fixture that ensures a clean Blender scene for each test"""
    # Clear scene before test
    bpy.ops.wm.read_factory_settings(use_empty=True)
    yield
    # Clean up after test
    bpy.ops.wm.read_factory_settings(use_empty=True)


@pytest.fixture
def test_cube(clean_scene):
    """Fixture that creates a test cube"""
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    cube = bpy.context.active_object
    yield cube


@pytest.fixture
def test_camera(clean_scene):
    """Fixture that creates a test camera"""
    bpy.ops.object.camera_add(location=(7, -7, 5))
    camera = bpy.context.active_object
    bpy.context.scene.camera = camera
    yield camera
