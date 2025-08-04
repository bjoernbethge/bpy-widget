"""
Temporary file management for bpy widget - Windows-safe version
"""
import tempfile
import os
import atexit
import platform
import time
from typing import Optional, Set

# Module-level state
_temp_files: Set[str] = set()
_render_file: Optional[str] = None
_temp_dir: Optional[str] = None


def get_temp_dir() -> str:
    """Get or create a dedicated temp directory for the widget"""
    global _temp_dir
    
    if _temp_dir is None or not os.path.exists(_temp_dir):
        # Create a dedicated directory for all temp files
        _temp_dir = tempfile.mkdtemp(prefix='bpy_widget_')
        _temp_files.add(_temp_dir)
    
    return _temp_dir


def get_render_file() -> str:
    """Get path for render output file - Windows-safe version"""
    global _render_file
    
    # Use process ID and timestamp for unique naming
    pid = os.getpid()
    timestamp = int(time.time() * 1000)
    
    # Use system temp directory directly on Windows
    if platform.system() == 'Windows':
        temp_dir = tempfile.gettempdir()
        file_name = f'bpy_widget_{pid}_{timestamp}.png'
        _render_file = os.path.join(temp_dir, file_name)
    else:
        temp_dir = get_temp_dir()
        file_name = f'render_{timestamp}.png'
        _render_file = os.path.join(temp_dir, file_name)
    
    _temp_files.add(_render_file)
    return _render_file


def create_temp_file(suffix: str = '.tmp') -> str:
    """Create a new temporary file"""
    # Direct temp file creation for Windows
    if platform.system() == 'Windows':
        temp_dir = tempfile.gettempdir()
        pid = os.getpid()
        timestamp = int(time.time() * 1000)
        file_name = f'bpy_widget_{pid}_{timestamp}{suffix}'
        file_path = os.path.join(temp_dir, file_name)
    else:
        temp_dir = get_temp_dir()
        with tempfile.NamedTemporaryFile(
            suffix=suffix, 
            prefix='bpy_widget_', 
            dir=temp_dir,
            delete=False
        ) as temp_file:
            file_path = temp_file.name
    
    _temp_files.add(file_path)
    return file_path


def cleanup_file(file_path: str) -> bool:
    """Remove a specific file - Windows-safe version"""
    global _render_file
    
    try:
        if os.path.exists(file_path):
            # Windows: try multiple times with delays
            if platform.system() == 'Windows':
                for attempt in range(5):
                    try:
                        os.remove(file_path)
                        break
                    except (OSError, PermissionError):
                        if attempt < 4:
                            time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                        # Don't raise on last attempt - file might be locked
            else:
                os.remove(file_path)
                
        _temp_files.discard(file_path)
        if file_path == _render_file:
            _render_file = None
        return True
        
    except Exception as e:
        # On Windows, silently ignore cleanup errors
        if platform.system() == 'Windows':
            _temp_files.discard(file_path)
        else:
            print(f"Warning: Could not remove temp file {file_path}: {e}")
        return False


def cleanup_all() -> int:
    """Remove all temporary files and directories"""
    global _render_file, _temp_dir
    
    removed_count = 0
    
    # Clean individual files first
    for file_path in list(_temp_files):  # Use list() to avoid modification during iteration
        if os.path.isfile(file_path):
            if cleanup_file(file_path):
                removed_count += 1
    
    # Clean temp directory
    if _temp_dir and os.path.exists(_temp_dir):
        try:
            # Remove any remaining files
            for filename in os.listdir(_temp_dir):
                file_path = os.path.join(_temp_dir, filename)
                try:
                    os.remove(file_path)
                    removed_count += 1
                except:
                    pass  # Ignore errors
            
            # Try to remove directory
            try:
                os.rmdir(_temp_dir)
                _temp_files.discard(_temp_dir)
            except:
                pass  # Directory might still have locked files on Windows
                
        except Exception:
            pass  # Ignore all errors during cleanup
    
    _temp_files.clear()
    _render_file = None
    _temp_dir = None
    return removed_count


# Register cleanup but don't fail if it doesn't work
def safe_cleanup():
    """Safe cleanup that doesn't raise exceptions"""
    try:
        cleanup_all()
    except:
        pass  # Ignore all cleanup errors


atexit.register(safe_cleanup)
