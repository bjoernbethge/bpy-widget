"""
Geometry functions for bpy widget
"""
from typing import List, Optional, Tuple, Union

import bpy

from .materials import create_material


def create_point_cloud(
    points: List[Tuple[float, float, float]],
    name: str = "PointCloud"
) -> bpy.types.Object:
    """Create a point cloud from a list of points"""
    mesh = bpy.data.meshes.new(name=name)
    mesh.from_pydata(points, [], [])
    mesh.update()
    
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    
    return obj


def create_curve_object(
    points: List[Tuple[float, float, float]],
    name: str = "Curve",
    curve_type: str = 'NURBS'
) -> bpy.types.Object:
    """Create a curve from points"""
    curve = bpy.data.curves.new(name=name, type='CURVE')
    curve.dimensions = '3D'
    
    spline = curve.splines.new(curve_type)
    spline.points.add(len(points) - 1)
    
    for i, (x, y, z) in enumerate(points):
        point = spline.points[i]
        point.co = (x, y, z, 1.0)
    
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    
    return obj


def create_icosphere(
    subdivisions: int = 2,
    radius: float = 1.0,
    location: Tuple[float, float, float] = (0, 0, 0)
) -> bpy.types.Object:
    """Create an icosphere"""
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=subdivisions,
        radius=radius,
        location=location
    )
    return getattr(bpy.context, 'object', None) or bpy.data.objects[-1]  # Get last created object


def create_torus(
    major_radius: float = 1.0,
    minor_radius: float = 0.25,
    location: Tuple[float, float, float] = (0, 0, 0)
) -> bpy.types.Object:
    """Create a torus"""
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius,
        minor_radius=minor_radius,
        location=location
    )
    return getattr(bpy.context, 'object', None) or bpy.data.objects[-1]  # Get last created object


def create_collection(name: str) -> bpy.types.Collection:
    """Create a new collection"""
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def instance_on_points(
    points_obj: bpy.types.Object,
    instance_obj: bpy.types.Object,
    scale: float = 1.0
) -> bpy.types.Object:
    """Instance objects on points using geometry nodes"""
    # Add geometry nodes modifier
    modifier = points_obj.modifiers.new(name="InstanceOnPoints", type='NODES')
    
    # Create node group
    node_group = bpy.data.node_groups.new(name="InstanceNodes", type='GeometryNodeTree')
    modifier.node_group = node_group
    
    # Create nodes
    input_node = node_group.nodes.new('NodeGroupInput')
    output_node = node_group.nodes.new('NodeGroupOutput')
    instance_node = node_group.nodes.new('GeometryNodeInstanceOnPoints')
    
    # Add sockets
    node_group.interface.new_socket(
        name="Geometry",
        in_out='INPUT',
        socket_type='NodeSocketGeometry'
    )
    node_group.interface.new_socket(
        name="Geometry", 
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry'
    )
    
    # Set positions
    input_node.location = (-200, 0)
    instance_node.location = (0, 0)
    output_node.location = (200, 0)
    
    # Create links
    links = node_group.links
    links.new(input_node.outputs[0], instance_node.inputs['Points'])
    links.new(instance_node.outputs['Instances'], output_node.inputs[0])
    
    # Set instance
    instance_node.inputs['Instance'].default_value = instance_obj
    instance_node.inputs['Scale'].default_value = (scale, scale, scale)
    
    return points_obj


def join_objects(objects: List[bpy.types.Object]) -> bpy.types.Object:
    """Join multiple objects into one"""
    if not objects:
        return None
    
    # Select objects
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    
    # Set active
    bpy.context.view_layer.objects.active = objects[0]
    
    # Join
    bpy.ops.object.join()

    return getattr(bpy.context, 'object', None) or bpy.data.objects[-1]  # Get last created object


def convert_to_mesh(obj: bpy.types.Object) -> bpy.types.Object:
    """Convert object to mesh"""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')
    return obj


def merge_vertices(obj: bpy.types.Object, distance: float = 0.0001):
    """Merge vertices by distance"""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=distance)
    bpy.ops.object.mode_set(mode='OBJECT')


def set_smooth_shading(obj: bpy.types.Object):
    """Set smooth shading on object"""
    for face in obj.data.polygons:
        face.use_smooth = True
    obj.data.update()


def add_subdivision_modifier(
    obj: bpy.types.Object,
    levels: int = 2,
    render_levels: int = 3
) -> bpy.types.Modifier:
    """Add subdivision surface modifier"""
    modifier = obj.modifiers.new(name="Subdivision", type='SUBSURF')
    modifier.levels = levels
    modifier.render_levels = render_levels
    return modifier


def create_geometry_nodes_modifier(
    obj: bpy.types.Object,
    name: str = "GeometryNodes"
) -> bpy.types.Modifier:
    """Create a geometry nodes modifier"""
    modifier = obj.modifiers.new(name=name, type='NODES')
    node_group = bpy.data.node_groups.new(name=f"{name}Group", type='GeometryNodeTree')
    modifier.node_group = node_group
    
    # Add basic input/output
    input_node = node_group.nodes.new('NodeGroupInput')
    output_node = node_group.nodes.new('NodeGroupOutput')
    
    node_group.interface.new_socket(
        name="Geometry",
        in_out='INPUT',
        socket_type='NodeSocketGeometry'
    )
    node_group.interface.new_socket(
        name="Geometry", 
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry'
    )
    
    input_node.location = (-200, 0)
    output_node.location = (200, 0)
    
    # Link
    node_group.links.new(input_node.outputs[0], output_node.inputs[0])
    
    return modifier


def apply_modifiers(obj: bpy.types.Object):
    """Apply all modifiers on object"""
    bpy.context.view_layer.objects.active = obj
    for modifier in obj.modifiers:
        bpy.ops.object.modifier_apply(modifier=modifier.name)


def create_test_cube(
    location: Tuple[float, float, float] = (0, 0, 0),
    size: float = 2.0,
    material_color: Optional[Tuple[float, float, float, float]] = None
) -> bpy.types.Object:
    """
    Create a test cube for visualization.

    Args:
        location: Cube location
        size: Cube size
        material_color: Optional material color

    Returns:
        Created cube object
    """
    bpy.ops.mesh.primitive_cube_add(location=location, size=size)
    cube = getattr(bpy.context, 'object', None) or bpy.data.objects[-1]  # Get last created object
    cube.name = "TestCube"

    # Apply material
    if material_color:
        mat = create_material(f"CubeMat_{id(cube)}", base_color=material_color)
        cube.data.materials.append(mat)

    return cube


def create_suzanne(
    location: Tuple[float, float, float] = (0, 0, 2),
    size: float = 1.0,
    material_color: Optional[Tuple[float, float, float, float]] = None
) -> bpy.types.Object:
    """
    Create Suzanne monkey head for testing.

    Args:
        location: Suzanne location
        size: Suzanne size
        material_color: Optional material color

    Returns:
        Created Suzanne object
    """
    bpy.ops.mesh.primitive_monkey_add(location=location, size=size)
    suzanne = getattr(bpy.context, 'object', None) or bpy.data.objects[-1]  # Get last created object
    suzanne.name = "Suzanne"

    # Apply material
    if material_color:
        mat = create_material(f"SuzanneMat_{id(suzanne)}", base_color=material_color)
        suzanne.data.materials.append(mat)

    return suzanne
