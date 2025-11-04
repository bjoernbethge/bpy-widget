"""
BPY Widget - Interactive Blender widget for Marimo
"""

# Setup datafiles BEFORE any bpy imports to avoid font warnings
# This ensures fonts and OCIO config are available when bpy is first imported
# Suppress all output during import to avoid Marimo export issues
try:
    import sys
    from io import StringIO
    from .core.setup_datafiles import setup_datafiles_if_needed
    
    # Temporarily redirect stderr to suppress loguru output during import
    _old_stderr = sys.stderr
    sys.stderr = StringIO()
    try:
        setup_datafiles_if_needed()
    finally:
        sys.stderr = _old_stderr
except Exception:
    # Silently fail - datafiles setup is optional and will be retried when widget is created
    pass

from .widget import BpyWidget, BlenderWidget

__version__ = "0.1.1"
__all__ = ['BpyWidget', 'BlenderWidget']
