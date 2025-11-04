"""Tests for scene management module"""
import pytest
import bpy

from bpy_widget.core.scene import clear_scene, get_scene


def test_get_scene(clean_scene):
    """Test getting current scene"""
    scene = get_scene()
    assert scene is not None
    assert isinstance(scene, bpy.types.Scene)


def test_clear_scene_removes_objects(clean_scene):
    """Test that clear_scene removes all objects"""
    # Create multiple objects
    bpy.ops.mesh.primitive_cube_add()
    bpy.ops.mesh.primitive_uv_sphere_add(location=(2, 0, 0))
    bpy.ops.mesh.primitive_cylinder_add(location=(-2, 0, 0))

    assert len(bpy.data.objects) == 3

    # Clear scene
    clear_scene()

    # Verify all objects removed
    assert len(bpy.data.objects) == 0


def test_clear_scene_removes_orphaned_data(clean_scene):
    """Test that clear_scene removes orphaned data blocks"""
    # Create object with mesh and material
    bpy.ops.mesh.primitive_cube_add()
    # Use last created object as fallback for headless environments
    cube = getattr(bpy.context, 'active_object', None) or bpy.data.objects[-1]

    # Create material
    mat = bpy.data.materials.new(name="TestMaterial")
    cube.data.materials.append(mat)

    # Create extra mesh that's not used
    orphan_mesh = bpy.data.meshes.new(name="OrphanMesh")
    orphan_material = bpy.data.materials.new(name="OrphanMaterial")

    initial_mesh_count = len(bpy.data.meshes)
    initial_mat_count = len(bpy.data.materials)

    # Clear scene
    clear_scene()

    # Check orphaned data is removed
    assert len(bpy.data.meshes) < initial_mesh_count
    assert len(bpy.data.materials) < initial_mat_count


def test_clear_scene_iteration_safety(clean_scene):
    """Test that clear_scene handles iteration correctly (no race condition)"""
    # Create many objects of different types
    for i in range(10):
        bpy.ops.mesh.primitive_cube_add(location=(i, 0, 0))

    # Create orphaned data blocks
    for i in range(5):
        bpy.data.meshes.new(name=f"OrphanMesh{i}")
        bpy.data.materials.new(name=f"OrphanMat{i}")

    # This should not raise any errors
    try:
        clear_scene()
        success = True
    except RuntimeError as e:
        success = False
        pytest.fail(f"clear_scene raised RuntimeError (iteration issue): {e}")

    assert success
    assert len(bpy.data.objects) == 0
