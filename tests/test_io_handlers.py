"""Tests for I/O handlers module"""
import pytest
from pathlib import Path
import tempfile

from bpy_widget.core.io_handlers import _validate_output_path


def test_validate_output_path_valid():
    """Test validation of valid output path"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir) / "test_output.glb"
        validated = _validate_output_path(test_path)
        assert validated == test_path


def test_validate_output_path_nonexistent_directory():
    """Test validation fails for non-existent directory"""
    invalid_path = Path("/nonexistent/directory/file.glb")
    with pytest.raises(ValueError, match="Directory does not exist"):
        _validate_output_path(invalid_path)


def test_validate_output_path_readonly_file():
    """Test validation fails for read-only file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "readonly.glb"
        test_file.touch()
        test_file.chmod(0o444)  # Read-only

        try:
            with pytest.raises(PermissionError, match="Cannot write to"):
                _validate_output_path(test_file)
        finally:
            # Clean up - restore write permissions
            test_file.chmod(0o644)
