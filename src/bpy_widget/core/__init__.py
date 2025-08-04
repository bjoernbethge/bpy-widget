"""
Core functionality for bpy_widget
"""

from .camera import (
    calculate_spherical_from_position,
    setup_camera,
    update_camera_position,
    update_camera_spherical,
)

from .data_import import (
    batch_import_data,
    import_data_as_points,
    import_data_with_metadata,
    import_dataframe_as_curve,
    import_multiple_series,
    read_data_file,
)

from .geometry import (
    add_subdivision_modifier,
    apply_modifiers,
    convert_to_mesh,
    create_collection,
    create_curve_object,
    create_geometry_nodes_modifier,
    create_icosphere,
    create_point_cloud,
    create_torus,
    instance_on_points,
    join_objects,
    merge_vertices,
    set_smooth_shading,
)

from .materials import (
    assign_material,
    create_emission_material,
    create_glass_material,
    create_gradient_material,
    create_material,
    create_metal_material,
    create_pbr_material,
    create_simple_material,
    create_toon_material,
    create_transparent_material,
    set_material_color,
)

from .nodes import add_glare_node, setup_compositor

from .rendering import (
    render_to_pixels,
    setup_rendering,
)

from .temp_files import cleanup_all, cleanup_file, create_temp_file, get_render_file

__all__ = [
    # Camera
    'setup_camera',
    'update_camera_position',
    'update_camera_spherical',
    'calculate_spherical_from_position',
    # Data Import
    'read_data_file',
    'import_data_as_points',
    'import_dataframe_as_curve',
    'import_multiple_series',
    'batch_import_data',
    'import_data_with_metadata',
    # Geometry
    'create_point_cloud',
    'create_curve_object',
    'create_icosphere',
    'create_torus',
    'create_collection',
    'instance_on_points',
    'join_objects',
    'convert_to_mesh',
    'merge_vertices',
    'set_smooth_shading',
    'add_subdivision_modifier',
    'create_geometry_nodes_modifier',
    'apply_modifiers',
    # Materials
    'create_material',
    'create_simple_material',
    'create_emission_material',
    'create_glass_material',
    'create_metal_material',
    'create_transparent_material',
    'create_gradient_material',
    'create_toon_material',
    'create_pbr_material',
    'assign_material',
    'set_material_color',
    # Nodes
    'setup_compositor',
    'add_glare_node',
    # Rendering
    'setup_rendering',
    'render_to_pixels',
    # Temp Files
    'get_render_file',
    'create_temp_file',
    'cleanup_file',
    'cleanup_all',
]
