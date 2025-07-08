"""
Temporary file management for bpy widget
"""
import tempfile
import os
import atexit
from typing import Optional, Set

# Module-level state
_temp_files: Set[str] = set()
_render_file: Optional[str] = None


def get_render_file() -> str:
    """Get path for render output file"""
    global _render_file
    
    if _render_file is None or not os.path.exists(_render_file):
        temp_file = tempfile.NamedTemporaryFile(
            suffix='.png', 
            prefix='bpy_widget_render_', 
            delete=False
        )
        _render_file = temp_file.name
        _temp_files.add(_render_file)
        temp_file.close()
    
    return _render_file


def create_temp_file(suffix: str = '.tmp') -> str:
    """Create a new temporary file"""
    temp_file = tempfile.NamedTemporaryFile(
        suffix=suffix, 
        prefix='bpy_widget_', 
        delete=False
    )
    file_path = temp_file.name
    _temp_files.add(file_path)
    temp_file.close()
    return file_path


def cleanup_file(file_path: str) -> bool:
    """Remove a specific file"""
    global _render_file
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        _temp_files.discard(file_path)
        if file_path == _render_file:
            _render_file = None
        return True
    except OSError as e:
        print(f"Warning: Could not remove temp file {file_path}: {e}")
        return False


def cleanup_all() -> int:
    """Remove all temporary files"""
    global _render_file
    
    removed_count = 0
    for file_path in _temp_files.copy():
        if cleanup_file(file_path):
            removed_count += 1
    
    _temp_files.clear()
    _render_file = None
    return removed_count


# Cleanup on module exit
atexit.register(cleanup_all)
