"""
Import/Export handlers for various 3D formats
"""
import os
from pathlib import Path
from typing import List, Optional, Union, Dict, Any

import bpy
import numpy as np
import polars as pl


def _validate_output_path(file_path: Path) -> Path:
    """
    Validate output file path for security and usability.

    Args:
        file_path: Path to validate

    Returns:
        Validated path

    Raises:
        ValueError: If parent directory does not exist
        PermissionError: If path is not writable
    """
    if not file_path.parent.exists():
        raise ValueError(f"Directory does not exist: {file_path.parent}")
    if file_path.exists() and not os.access(file_path, os.W_OK):
        raise PermissionError(f"Cannot write to {file_path}")
    return file_path


def import_gltf(
    file_path: Union[str, Path],
    use_custom_normals: bool = True,
    import_shading: str = "SMOOTH",
) -> List[bpy.types.Object]:
    """
    Import GLTF/GLB file
    
    Args:
        file_path: Path to GLTF/GLB file
        use_custom_normals: Import custom normals
        import_shading: Shading mode ('SMOOTH', 'FLAT', 'NORMALS')
    
    Returns:
        List of imported objects
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"GLTF file not found: {file_path}")
    
    # Store existing objects
    existing_objects = set(bpy.data.objects)
    
    # Import GLTF
    bpy.ops.import_scene.gltf(
        filepath=str(file_path),
        import_shading=import_shading,
        merge_vertices=False,
        import_pack_images=True,
    )
    
    # Get newly imported objects
    imported_objects = [obj for obj in bpy.data.objects if obj not in existing_objects]
    
    print(f"Imported {len(imported_objects)} objects from {file_path.name}")
    return imported_objects


def export_gltf(
    file_path: Union[str, Path],
    selected_only: bool = False,
    export_format: str = "GLB",
    export_textures: bool = True,
    export_normals: bool = True,
    export_colors: bool = True,
) -> None:
    """
    Export scene or selected objects as GLTF/GLB
    
    Args:
        file_path: Output file path
        selected_only: Export only selected objects
        export_format: 'GLB' or 'GLTF_SEPARATE' or 'GLTF_EMBEDDED'
        export_textures: Include textures
        export_normals: Include normals
        export_colors: Include vertex colors
    """
    file_path = Path(file_path)

    # Ensure correct extension
    if export_format == "GLB" and not file_path.suffix == ".glb":
        file_path = file_path.with_suffix(".glb")
    elif export_format.startswith("GLTF") and not file_path.suffix == ".gltf":
        file_path = file_path.with_suffix(".gltf")

    # Validate output path
    _validate_output_path(file_path)

    # Export
    bpy.ops.export_scene.gltf(
        filepath=str(file_path),
        export_format=export_format,
        use_selection=selected_only,
        export_image_format="AUTO",
        export_texture_dir="",
        export_texcoords=export_textures,
        export_normals=export_normals,
        export_colors=export_colors,
        export_cameras=True,
        export_lights=True,
    )
    
    print(f"Exported to {file_path}")


def import_usd(
    file_path: Union[str, Path],
    scale: float = 1.0,
    import_cameras: bool = True,
    import_lights: bool = True,
    import_materials: bool = True,
) -> List[bpy.types.Object]:
    """
    Import USD/USDZ file
    
    Args:
        file_path: Path to USD/USDZ file
        scale: Import scale factor
        import_cameras: Import cameras
        import_lights: Import lights
        import_materials: Import materials
    
    Returns:
        List of imported objects
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"USD file not found: {file_path}")
    
    # Store existing objects
    existing_objects = set(bpy.data.objects)
    
    # Import USD
    bpy.ops.wm.usd_import(
        filepath=str(file_path),
        scale=scale,
        import_cameras=import_cameras,
        import_lights=import_lights,
        import_materials=import_materials,
        import_meshes=True,
        import_volumes=True,
        set_frame_range=False,
        relative_path=True,
    )
    
    # Get newly imported objects
    imported_objects = [obj for obj in bpy.data.objects if obj not in existing_objects]
    
    print(f"Imported {len(imported_objects)} objects from {file_path.name}")
    return imported_objects


def export_usd(
    file_path: Union[str, Path],
    selected_only: bool = False,
    export_animation: bool = False,
    export_hair: bool = False,
    export_uvmaps: bool = True,
    export_normals: bool = True,
    export_materials: bool = True,
) -> None:
    """
    Export scene or selected objects as USD/USDZ
    
    Args:
        file_path: Output file path
        selected_only: Export only selected objects
        export_animation: Include animation
        export_hair: Include hair
        export_uvmaps: Include UV maps
        export_normals: Include normals
        export_materials: Include materials
    """
    file_path = Path(file_path)

    # Ensure correct extension
    if not file_path.suffix in [".usd", ".usda", ".usdc", ".usdz"]:
        file_path = file_path.with_suffix(".usd")

    # Validate output path
    _validate_output_path(file_path)

    # Export
    bpy.ops.wm.usd_export(
        filepath=str(file_path),
        selected_objects_only=selected_only,
        export_animation=export_animation,
        export_hair=export_hair,
        export_uvmaps=export_uvmaps,
        export_normals=export_normals,
        export_materials=export_materials,
        use_instancing=True,
        evaluation_mode='RENDER',
    )
    
    print(f"Exported to {file_path}")


def import_alembic(
    file_path: Union[str, Path],
    scale: float = 1.0,
    set_frame_range: bool = True,
    validate_meshes: bool = False,
    is_sequence: bool = False,
) -> List[bpy.types.Object]:
    """
    Import Alembic (.abc) file
    
    Args:
        file_path: Path to Alembic file
        scale: Import scale factor
        set_frame_range: Update frame range from Alembic
        validate_meshes: Validate mesh data
        is_sequence: Import as sequence
    
    Returns:
        List of imported objects
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Alembic file not found: {file_path}")
    
    # Store existing objects
    existing_objects = set(bpy.data.objects)
    
    # Import Alembic
    bpy.ops.wm.alembic_import(
        filepath=str(file_path),
        scale=scale,
        set_frame_range=set_frame_range,
        validate_meshes=validate_meshes,
        is_sequence=is_sequence,
        as_background_job=False,
    )
    
    # Get newly imported objects
    imported_objects = [obj for obj in bpy.data.objects if obj not in existing_objects]
    
    print(f"Imported {len(imported_objects)} objects from {file_path.name}")
    return imported_objects


def export_alembic(
    file_path: Union[str, Path],
    selected: bool = False,
    start_frame: Optional[int] = None,
    end_frame: Optional[int] = None,
    export_hair: bool = False,
    export_particles: bool = False,
    export_custom_properties: bool = True,
    use_instancing: bool = True,
) -> None:
    """
    Export scene as Alembic (.abc) file
    
    Args:
        file_path: Output file path
        selected: Export only selected objects
        start_frame: Animation start frame
        end_frame: Animation end frame
        export_hair: Include hair
        export_particles: Include particles
        export_custom_properties: Include custom properties
        use_instancing: Use instancing for duplicates
    """
    file_path = Path(file_path)

    # Ensure correct extension
    if not file_path.suffix == ".abc":
        file_path = file_path.with_suffix(".abc")

    # Validate output path
    _validate_output_path(file_path)

    # Set frame range
    scene = bpy.context.scene
    if start_frame is None:
        start_frame = scene.frame_start
    if end_frame is None:
        end_frame = scene.frame_end
    
    # Export
    bpy.ops.wm.alembic_export(
        filepath=str(file_path),
        selected=selected,
        start=start_frame,
        end=end_frame,
        export_hair=export_hair,
        export_particles=export_particles,
        export_custom_properties=export_custom_properties,
        use_instancing=use_instancing,
        global_scale=1.0,
        flatten=False,
    )
    
    print(f"Exported to {file_path}")


def export_scene_as_parquet(
    file_path: Union[str, Path],
    include_metadata: bool = True
) -> None:
    """
    Export entire scene data as Parquet file

    Args:
        file_path: Output file path
        include_metadata: Include object metadata
    """
    file_path = Path(file_path)
    if not file_path.suffix == ".parquet":
        file_path = file_path.with_suffix(".parquet")

    # Validate output path
    _validate_output_path(file_path)

    # Collect scene data
    data = []
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            mesh = obj.data
            for vertex in mesh.vertices:
                row = {
                    'object_name': obj.name,
                    'object_type': obj.type,
                    'vertex_index': vertex.index,
                    'x': vertex.co.x,
                    'y': vertex.co.y,
                    'z': vertex.co.z,
                    'normal_x': vertex.normal.x,
                    'normal_y': vertex.normal.y,
                    'normal_z': vertex.normal.z,
                }
                
                if include_metadata:
                    row.update({
                        'location_x': obj.location.x,
                        'location_y': obj.location.y,
                        'location_z': obj.location.z,
                        'rotation_x': obj.rotation_euler.x,
                        'rotation_y': obj.rotation_euler.y,
                        'rotation_z': obj.rotation_euler.z,
                        'scale_x': obj.scale.x,
                        'scale_y': obj.scale.y,
                        'scale_z': obj.scale.z,
                    })
                
                data.append(row)
    
    # Create DataFrame and save
    if data:
        df = pl.DataFrame(data)
        df.write_parquet(file_path)
        print(f"Exported {len(data)} vertices to {file_path}")
    else:
        print("No mesh data to export")


def import_scene_from_parquet(
    file_path: Union[str, Path]
) -> List[bpy.types.Object]:
    """
    Import scene data from Parquet file
    
    Args:
        file_path: Input Parquet file path
    
    Returns:
        List of created objects
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {file_path}")
    
    # Read data
    df = pl.read_parquet(file_path)
    
    # Group by object
    created_objects = []
    
    for object_name in df['object_name'].unique():
        obj_data = df.filter(pl.col('object_name') == object_name)
        
        # Create mesh
        mesh = bpy.data.meshes.new(name=object_name)
        
        # Get vertices
        vertices = []
        for row in obj_data.iter_rows(named=True):
            vertices.append((row['x'], row['y'], row['z']))
        
        # Create mesh from vertices
        mesh.from_pydata(vertices, [], [])
        mesh.update()
        
        # Create object
        obj = bpy.data.objects.new(object_name, mesh)
        bpy.context.collection.objects.link(obj)
        
        # Apply transform if available
        if 'location_x' in obj_data.columns:
            first_row = obj_data[0]
            obj.location = (
                first_row['location_x'][0],
                first_row['location_y'][0],
                first_row['location_z'][0]
            )
            obj.rotation_euler = (
                first_row['rotation_x'][0],
                first_row['rotation_y'][0],
                first_row['rotation_z'][0]
            )
            obj.scale = (
                first_row['scale_x'][0],
                first_row['scale_y'][0],
                first_row['scale_z'][0]
            )
        
        created_objects.append(obj)
    
    print(f"Imported {len(created_objects)} objects from {file_path.name}")
    return created_objects


def load_blend(file_path: Union[str, Path], load_ui: bool = False) -> None:
    """
    Load a Blender (.blend) file
    
    Args:
        file_path: Path to .blend file
        load_ui: Load UI settings (window layout, etc.)
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Blend file not found: {file_path}")
    
    if not file_path.suffix.lower() == '.blend':
        raise ValueError(f"File must be a .blend file: {file_path}")
    
    # Load blend file
    bpy.ops.wm.open_mainfile(filepath=str(file_path), load_ui=load_ui)
    
    print(f"Loaded blend file: {file_path.name}")


def save_blend(file_path: Union[str, Path], compress: bool = True) -> None:
    """
    Save current scene as Blender (.blend) file
    
    Args:
        file_path: Output file path
        compress: Compress the blend file
    """
    file_path = Path(file_path)
    
    # Ensure correct extension
    if not file_path.suffix.lower() == '.blend':
        file_path = file_path.with_suffix('.blend')
    
    # Validate output path
    _validate_output_path(file_path)
    
    # Save blend file
    bpy.ops.wm.save_as_mainfile(filepath=str(file_path), compress=compress)
    
    print(f"Saved blend file: {file_path.name}")


def link_from_blend(
    file_path: Union[str, Path],
    category: str = 'Object',
    name: Optional[str] = None
) -> List[Any]:
    """
    Link data from another Blender file (reference, not copy)
    
    Args:
        file_path: Path to source .blend file
        category: Data category ('Object', 'Material', 'Mesh', 'Collection', etc.)
        name: Specific name to link (if None, links all of category)
    
    Returns:
        List of linked data blocks
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Blend file not found: {file_path}")
    
    if not file_path.suffix.lower() == '.blend':
        raise ValueError(f"File must be a .blend file: {file_path}")
    
    # Link data from blend file
    with bpy.data.libraries.load(str(file_path), link=True) as (data_from, data_to):
        if category == 'Object':
            if name:
                if name in data_from.objects:
                    data_to.objects = [name]
                else:
                    raise ValueError(f"Object '{name}' not found in {file_path.name}")
            else:
                data_to.objects = data_from.objects
        elif category == 'Material':
            if name:
                if name in data_from.materials:
                    data_to.materials = [name]
                else:
                    raise ValueError(f"Material '{name}' not found in {file_path.name}")
            else:
                data_to.materials = data_from.materials
        elif category == 'Mesh':
            if name:
                if name in data_from.meshes:
                    data_to.meshes = [name]
                else:
                    raise ValueError(f"Mesh '{name}' not found in {file_path.name}")
            else:
                data_to.meshes = data_from.meshes
        elif category == 'Collection':
            if name:
                if name in data_from.collections:
                    data_to.collections = [name]
                else:
                    raise ValueError(f"Collection '{name}' not found in {file_path.name}")
            else:
                data_to.collections = data_from.collections
        else:
            raise ValueError(f"Unsupported category: {category}")
    
    # Link objects/collections to scene
    linked_items = []
    if category == 'Object':
        for obj in data_to.objects:
            if obj:
                bpy.context.collection.objects.link(obj)
                linked_items.append(obj)
    elif category == 'Collection':
        for coll in data_to.collections:
            if coll:
                bpy.context.scene.collection.children.link(coll)
                linked_items.append(coll)
    elif category == 'Material':
        linked_items = list(data_to.materials)
    elif category == 'Mesh':
        linked_items = list(data_to.meshes)
    
    print(f"Linked {len(linked_items)} {category}(s) from {file_path.name}")
    return linked_items


def append_from_blend(
    file_path: Union[str, Path],
    category: str = 'Object',
    name: Optional[str] = None
) -> List[Any]:
    """
    Append data from another Blender file (copy, not reference)
    
    Args:
        file_path: Path to source .blend file
        category: Data category ('Object', 'Material', 'Mesh', 'Collection', etc.)
        name: Specific name to append (if None, appends all of category)
    
    Returns:
        List of appended data blocks
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Blend file not found: {file_path}")
    
    if not file_path.suffix.lower() == '.blend':
        raise ValueError(f"File must be a .blend file: {file_path}")
    
    # Append data from blend file
    with bpy.data.libraries.load(str(file_path), link=False) as (data_from, data_to):
        if category == 'Object':
            if name:
                if name in data_from.objects:
                    data_to.objects = [name]
                else:
                    raise ValueError(f"Object '{name}' not found in {file_path.name}")
            else:
                data_to.objects = data_from.objects
        elif category == 'Material':
            if name:
                if name in data_from.materials:
                    data_to.materials = [name]
                else:
                    raise ValueError(f"Material '{name}' not found in {file_path.name}")
            else:
                data_to.materials = data_from.materials
        elif category == 'Mesh':
            if name:
                if name in data_from.meshes:
                    data_to.meshes = [name]
                else:
                    raise ValueError(f"Mesh '{name}' not found in {file_path.name}")
            else:
                data_to.meshes = data_from.meshes
        elif category == 'Collection':
            if name:
                if name in data_from.collections:
                    data_to.collections = [name]
                else:
                    raise ValueError(f"Collection '{name}' not found in {file_path.name}")
            else:
                data_to.collections = data_from.collections
        else:
            raise ValueError(f"Unsupported category: {category}")
    
    # Link objects/collections to scene
    appended_items = []
    if category == 'Object':
        for obj in data_to.objects:
            if obj:
                bpy.context.collection.objects.link(obj)
                appended_items.append(obj)
    elif category == 'Collection':
        for coll in data_to.collections:
            if coll:
                bpy.context.scene.collection.children.link(coll)
                appended_items.append(coll)
    elif category == 'Material':
        appended_items = list(data_to.materials)
    elif category == 'Mesh':
        appended_items = list(data_to.meshes)
    
    print(f"Appended {len(appended_items)} {category}(s) from {file_path.name}")
    return appended_items
