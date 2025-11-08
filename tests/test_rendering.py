"""Tests for rendering module"""
import os
import tempfile
from pathlib import Path

import bpy
import numpy as np
import pytest

from bpy_widget.core.rendering import render_to_pixels, setup_rendering

# Use Cycles CPU in CI environments (EEVEE requires GPU)
CI_ENGINE = 'CYCLES' if os.getenv('CI') else 'BLENDER_EEVEE_NEXT'


def test_setup_rendering_eevee(clean_scene):
    """Test EEVEE rendering setup"""
    setup_rendering(width=800, height=600, engine='BLENDER_EEVEE_NEXT')

    scene = bpy.context.scene

    assert scene.render.engine == 'BLENDER_EEVEE_NEXT'
    assert scene.render.resolution_x == 800
    assert scene.render.resolution_y == 600
    assert scene.eevee.taa_render_samples == 16


def test_setup_rendering_cycles(clean_scene):
    """Test Cycles rendering setup"""
    setup_rendering(width=1920, height=1080, engine='CYCLES')

    scene = bpy.context.scene

    assert scene.render.engine == 'CYCLES'
    assert scene.render.resolution_x == 1920
    assert scene.render.resolution_y == 1080
    assert scene.cycles.samples == 64


def test_render_to_pixels_with_camera(test_camera, test_cube):
    """Test rendering with camera returns valid pixel array"""
    setup_rendering(width=512, height=512, engine=CI_ENGINE)
    
    # Ensure CPU device for Cycles in CI
    if CI_ENGINE == 'CYCLES':
        scene = bpy.context.scene
        scene.cycles.device = 'CPU'

    pixels, width, height = render_to_pixels()

    assert pixels is not None
    assert width == 512
    assert height == 512
    assert isinstance(pixels, np.ndarray)
    assert pixels.shape == (512, 512, 4)
    assert pixels.dtype == np.uint8


def test_render_to_pixels_no_camera(clean_scene):
    """Test rendering without camera returns None"""
    pixels, width, height = render_to_pixels()

    assert pixels is None
    assert width == 0
    assert height == 0


def test_temporary_file_cleanup(test_camera, test_cube):
    """Test that temporary files are properly cleaned up"""
    setup_rendering(width=256, height=256, engine=CI_ENGINE)
    
    # Ensure CPU device for Cycles in CI
    if CI_ENGINE == 'CYCLES':
        scene = bpy.context.scene
        scene.cycles.device = 'CPU'

    # Get temp directory before render
    temp_dir = Path(tempfile.gettempdir())
    temp_files_before = set(temp_dir.glob("*.png"))

    # Render
    pixels, _, _ = render_to_pixels()

    # Check temp files after render
    temp_files_after = set(temp_dir.glob("*.png"))

    # Should not have created persistent temp files
    new_files = temp_files_after - temp_files_before
    assert len(new_files) == 0, "Temporary files were not cleaned up"
    assert pixels is not None, "Render should have succeeded"
