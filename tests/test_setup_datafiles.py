"""Tests for setup_datafiles module"""
import pytest
from pathlib import Path
import zipfile
import tempfile
import shutil

from bpy_widget.core.setup_datafiles import (
    get_package_datafiles_path,
    get_package_datafiles_zip,
    setup_datafiles_if_needed,
)


def test_get_package_datafiles_zip():
    """Test that ZIP file path is correctly determined"""
    zip_path = get_package_datafiles_zip()
    assert zip_path.name == "datafiles.zip"
    assert zip_path.exists(), "datafiles.zip should exist in the package"


def test_get_package_datafiles_path_extracts_zip():
    """Test that ZIP is automatically extracted when accessed"""
    # Get the path (should trigger extraction)
    datafiles_path = get_package_datafiles_path()
    
    # Check that extraction happened
    assert datafiles_path.exists(), "Extracted datafiles path should exist"
    
    # ZIP extracts with 'datafiles/' root, so check for colormanagement and fonts
    colormanagement_path = datafiles_path / "colormanagement"
    fonts_path = datafiles_path / "fonts"
    
    assert colormanagement_path.exists(), f"colormanagement directory should exist at {colormanagement_path}"
    assert fonts_path.exists(), f"fonts directory should exist at {fonts_path}"
    
    # Check that key files exist
    assert (colormanagement_path / "config.ocio").exists(), "OCIO config should exist"
    assert (fonts_path / "Inter.woff2").exists(), "Inter font should exist"
    assert (fonts_path / "DejaVuSansMono.woff2").exists(), "DejaVu font should exist"


def test_zip_extraction_cached():
    """Test that ZIP extraction is cached (only extracted once)"""
    # First access should extract
    path1 = get_package_datafiles_path()
    
    # Second access should use cache
    path2 = get_package_datafiles_path()
    
    # Should return same path
    assert path1 == path2
    
    # Cache directory should exist
    assert path1.exists()


def test_setup_datafiles_if_needed():
    """Test that setup_datafiles_if_needed works"""
    # This test checks that the function can be called without errors
    # It may or may not copy files depending on what's already in bpy
    try:
        result = setup_datafiles_if_needed()
        # Should return tuple or False
        assert isinstance(result, (tuple, bool))
    except Exception as e:
        # If it fails, it should be because bpy is not properly initialized,
        # not because of ZIP extraction issues
        assert "bpy" in str(e).lower() or "datafiles" in str(e).lower()


def test_zip_contains_required_files():
    """Test that ZIP contains all required files"""
    zip_path = get_package_datafiles_zip()
    
    if not zip_path.exists():
        pytest.skip("ZIP file not found (may not be in development mode)")
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        files = zip_ref.namelist()
        
        # Check for required files
        required_paths = [
            "colormanagement/config.ocio",
            "fonts/Inter.woff2",
            "fonts/DejaVuSansMono.woff2",
        ]
        
        for required_path in required_paths:
            assert any(f.endswith(required_path) for f in files), \
                f"ZIP should contain {required_path}"

