"""
Scene management functions for bpy widget
"""
import bpy


def get_scene() -> bpy.types.Scene:
    """Get the current scene safely."""
    return bpy.context.scene


def clear_scene() -> None:
    """Clear all objects and orphaned data blocks from the scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Clean up orphaned data blocks - create list copy to avoid iteration issues
    for collection in [
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.textures,
        bpy.data.images,
        bpy.data.curves,
        bpy.data.cameras,
        bpy.data.lights,
    ]:
        for block in list(collection):  # Create copy to avoid race condition
            if block.users == 0:
                collection.remove(block)
