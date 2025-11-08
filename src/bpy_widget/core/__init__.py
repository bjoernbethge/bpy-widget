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
    create_suzanne,
    create_test_cube,
    create_torus,
    instance_on_points,
    join_objects,
    merge_vertices,
    set_smooth_shading,
)
from .io_handlers import (
    append_from_blend,
    export_alembic,
    export_gltf,
    export_scene_as_parquet,
    export_usd,
    import_alembic,
    import_gltf,
    import_scene_from_parquet,
    import_usd,
    link_from_blend,
    load_blend,
    save_blend,
)
from .lighting import (
    setup_environment_lighting,
    setup_lighting,
    setup_sun_light,
    setup_three_point_lighting,
    setup_world_background,
)
from .materials import (
    MATERIAL_PRESETS,
    assign_material,
    create_material,
    create_preset_material,
    get_or_create_material,
)
from .nodes import add_glare_node, setup_compositor
from .post_processing import (
    add_bloom_glare,
    add_chromatic_aberration,
    add_color_correction,
    add_depth_of_field,
    add_film_grain,
    add_motion_blur,
    add_sharpen,
    add_vignette,
    reset_compositor,
    setup_extended_compositor,
)
from .rendering import (
    enable_compositor_gpu,
    ensure_gpu_for_eevee,
    get_gpu_backend,
    initialize_gpu,
    render_to_pixels,
    set_gpu_backend,
    setup_rendering,
)

# Extension manager imports (handled directly in widget)
from .scene import (
    clear_scene,
    get_scene,
)
from .setup_datafiles import setup_datafiles, setup_datafiles_if_needed
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
    'create_test_cube',
    'create_suzanne',
    'create_collection',
    'instance_on_points',
    'join_objects',
    'convert_to_mesh',
    'merge_vertices',
    'set_smooth_shading',
    'add_subdivision_modifier',
    'create_geometry_nodes_modifier',
    'apply_modifiers',
    # IO Handlers
    'import_gltf',
    'export_gltf',
    'import_usd',
    'export_usd',
    'import_alembic',
    'export_alembic',
    'export_scene_as_parquet',
    'import_scene_from_parquet',
    'load_blend',
    'save_blend',
    'link_from_blend',
    'append_from_blend',
    # Materials
    'create_material',
    'create_preset_material',
    'MATERIAL_PRESETS',
    'get_or_create_material',
    'assign_material',
    # Nodes
    'setup_compositor',
    'add_glare_node',
    # Post Processing
    'setup_extended_compositor',
    'add_bloom_glare',
    'add_color_correction',
    'add_vignette',
    'add_film_grain',
    'add_chromatic_aberration',
    'add_motion_blur',
    'add_depth_of_field',
    'add_sharpen',
    'reset_compositor',
    # Rendering
    'setup_rendering',
    'render_to_pixels',
    'set_gpu_backend',
    'get_gpu_backend',
    'initialize_gpu',
    'ensure_gpu_for_eevee',
    'enable_compositor_gpu',
    # Scene
    'clear_scene',
    'get_scene',
    # Lighting
    'setup_lighting',
    'setup_world_background',
    'setup_three_point_lighting',
    'setup_environment_lighting',
    'setup_sun_light',
    # Temp Files
    'get_render_file',
    'create_temp_file',
    'cleanup_file',
    'cleanup_all',
    # Setup
    'setup_datafiles',
    'setup_datafiles_if_needed',
    # Extensions
    'install_extension',
    'search_extensions',
]
