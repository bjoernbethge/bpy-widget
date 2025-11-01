"""
Point cloud creation and visualization
"""
import bpy
import numpy as np
import polars as pl
from typing import Optional, Any


def create_points_from_dataframe(
    df: pl.DataFrame,
    collection: bpy.types.Collection,
    x_col: Optional[str],
    y_col: Optional[str],
    z_col: Optional[str],
    color_col: Optional[str],
    point_size: float
) -> bpy.types.Object:
    """Create point objects from dataframe"""
    # Get coordinate data with fallback to 0
    x_data = df[x_col].to_numpy() if x_col and x_col in df.columns else np.zeros(len(df))
    y_data = df[y_col].to_numpy() if y_col and y_col in df.columns else np.zeros(len(df))
    z_data = df[z_col].to_numpy() if z_col and z_col in df.columns else np.zeros(len(df))
    
    # Get color data if available
    color_data = df[color_col].to_numpy() if color_col and color_col in df.columns else None
    
    # Create a single mesh with all points (more efficient than individual objects)
    mesh = bpy.data.meshes.new(name=f"{collection.name}_PointCloud")
    
    # Create vertices
    vertices = [(float(x), float(y), float(z)) for x, y, z in zip(x_data, y_data, z_data)]
    mesh.from_pydata(vertices, [], [])
    mesh.update()
    
    # Create object
    obj = bpy.data.objects.new(name=f"{collection.name}_Points", object_data=mesh)
    collection.objects.link(obj)
    
    # Set up point cloud visualization using geometry nodes
    setup_point_cloud_geometry_nodes(obj, point_size, color_data)
    
    return obj


def setup_point_cloud_geometry_nodes(obj: bpy.types.Object, point_size: float, color_data: Optional[Any]):
    """Set up geometry nodes for point cloud visualization"""
    # Add geometry nodes modifier
    modifier = obj.modifiers.new(name="PointCloudViz", type='NODES')
    
    # Create new node group
    node_group = bpy.data.node_groups.new(name="PointCloudNodes", type='GeometryNodeTree')
    modifier.node_group = node_group
    
    # Clear default nodes
    node_group.nodes.clear()
    
    # Create nodes
    input_node = node_group.nodes.new('NodeGroupInput')
    output_node = node_group.nodes.new('NodeGroupOutput')
    
    # Add sockets using new 4.0+ API
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
    
    # Create instance on points node
    instance_node = node_group.nodes.new('GeometryNodeInstanceOnPoints')
    
    # Create sphere for points
    sphere_node = node_group.nodes.new('GeometryNodeMeshUVSphere')
    sphere_node.inputs['Radius'].default_value = point_size
    sphere_node.inputs['Segments'].default_value = 8
    sphere_node.inputs['Rings'].default_value = 6
    
    # Position nodes
    input_node.location = (-200, 0)
    instance_node.location = (0, 0)
    sphere_node.location = (-200, -150)
    output_node.location = (200, 0)
    
    # Create links
    links = node_group.links
    links.new(input_node.outputs[0], instance_node.inputs['Points'])
    links.new(sphere_node.outputs['Mesh'], instance_node.inputs['Instance'])
    links.new(instance_node.outputs['Instances'], output_node.inputs[0])
    
    # Apply color if available
    if color_data is not None:
        apply_point_colors(obj, color_data)


def apply_point_colors(obj: bpy.types.Object, color_data: np.ndarray):
    """Apply colors to point cloud vertices"""
    mesh = obj.data
    color_attr = mesh.attributes.new(name="color", type='FLOAT_COLOR', domain='POINT')
    
    # Normalize color data to 0-1 range if needed
    colors = np.array(color_data)
    if colors.max() > 1.0:
        colors = colors / colors.max()
    
    # Set colors (assuming single value, create gradient)
    for i, val in enumerate(colors):
        if i < len(color_attr.data):
            color_attr.data[i].color = (val, 1.0 - val, 0.5, 1.0)
