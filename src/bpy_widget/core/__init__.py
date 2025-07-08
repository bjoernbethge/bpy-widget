"""
Core functions for bpy widget
"""

# Camera functions
from .camera import (
    setup_camera,
    update_camera_spherical, 
    calculate_spherical_from_position
)

# Rendering functions
from .rendering import (
    setup_rendering,
    render_to_pixels,
    optimize_for_interactive,
    set_render_samples
)

# Temp file management
from .temp_files import (
    get_render_file,
    create_temp_file,
    cleanup_file,
    cleanup_all
)

__all__ = [
    # Camera
    'setup_camera',
    'update_camera_spherical', 
    'calculate_spherical_from_position',
    # Rendering
    'setup_rendering',
    'render_to_pixels',
    'optimize_for_interactive',
    'set_render_samples',
    # Temp files
    'get_render_file',
    'create_temp_file',
    'cleanup_file',
    'cleanup_all',
]
