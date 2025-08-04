"""
Node Utilities - Analog zu utils.py node functions
"""
import bpy
from typing import Optional, List, Tuple, Dict, Any


def setup_compositor():
    """Setup basic compositor - analog zu set_compositing_area"""
    scene = bpy.context.scene
    scene.use_nodes = True
    
    tree = scene.node_tree
    tree.nodes.clear()
    
    # Basic setup
    render_layers = tree.nodes.new('CompositorNodeRLayers')
    composite = tree.nodes.new('CompositorNodeComposite')
    
    tree.links.new(render_layers.outputs['Image'], composite.inputs['Image'])
    
    return render_layers, composite


def setup_compositor_denoising():
    """Setup new 4.4 compositor denoising"""
    scene = bpy.context.scene
    scene.use_nodes = True
    tree = scene.node_tree
    
    # Find or create basic nodes
    render_layers = None
    composite = None
    
    for node in tree.nodes:
        if node.type == 'R_LAYERS':
            render_layers = node
        elif node.type == 'COMPOSITE':
            composite = node
    
    if not render_layers or not composite:
        render_layers, composite = setup_compositor()
    
    # Add new Denoise node (improved in 4.4)
    denoise_node = tree.nodes.new('CompositorNodeDenoise')
    
    # Position between render layers and composite
    denoise_node.location = (150, 0)
    
    # Clear existing links and reconnect through denoise
    tree.links.clear()
    tree.links.new(render_layers.outputs['Image'], denoise_node.inputs['Image'])
    tree.links.new(denoise_node.outputs['Image'], composite.inputs['Image'])
    
    return denoise_node


def connect_nodes(node_tree, from_node, from_output, to_node, to_input):
    """Connect nodes - analog zu create_texture_node connection logic"""
    if isinstance(from_output, str):
        from_socket = from_node.outputs[from_output]
    else:
        from_socket = from_node.outputs[from_output]
        
    if isinstance(to_input, str):
        to_socket = to_node.inputs[to_input]  
    else:
        to_socket = to_node.inputs[to_input]
        
    node_tree.links.new(from_socket, to_socket)


def create_node_group(name, tree_type='ShaderNodeTree'):
    """Create node group - analog zu create_example_texture_node_trees"""
    node_group = bpy.data.node_groups.new(name, tree_type)
    
    # Add group input and output
    group_input = node_group.nodes.new('NodeGroupInput')
    group_output = node_group.nodes.new('NodeGroupOutput')
    
    group_input.location = (-200, 0)
    group_output.location = (200, 0)
    
    return node_group


def create_reusable_node_group(
    name: str, 
    type: str = 'GeometryNodeTree',
    force_new: bool = False
) -> bpy.types.NodeTree:
    """
    Create reusable node group with proper interface
    
    Args:
        name: Name for the node group
        type: Type of node tree ('GeometryNodeTree', 'ShaderNodeTree', etc.)
        force_new: Force creation of new group even if exists
        
    Returns:
        The node group
    """
    # Check if already exists
    if not force_new and name in bpy.data.node_groups:
        return bpy.data.node_groups[name]
    
    # Create new group
    group = bpy.data.node_groups.new(name, type)
    
    # Clear default nodes
    group.nodes.clear()
    
    # Add input/output nodes
    input_node = group.nodes.new('NodeGroupInput')
    output_node = group.nodes.new('NodeGroupOutput')
    
    input_node.location = (-300, 0)
    output_node.location = (300, 0)
    
    return group


def add_vector_input(
    node_group: bpy.types.NodeTree,
    name: str,
    default: Tuple[float, float, float] = (0.0, 0.0, 0.0)
) -> Any:
    """Add vector input socket to node group using 4.0+ API"""
    socket = node_group.interface.new_socket(
        name=name,
        in_out='INPUT',
        socket_type='NodeSocketVector'
    )
    # Set default value through the interface item
    if hasattr(socket, 'default_value'):
        socket.default_value = default
    return socket


def add_float_input(
    node_group: bpy.types.NodeTree,
    name: str,
    default: float = 0.0,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None
) -> Any:
    """Add float input socket to node group"""
    socket = node_group.interface.new_socket(
        name=name,
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    )
    # Set default and limits if available
    if hasattr(socket, 'default_value'):
        socket.default_value = default
    if min_value is not None and hasattr(socket, 'min_value'):
        socket.min_value = min_value
    if max_value is not None and hasattr(socket, 'max_value'):
        socket.max_value = max_value
    return socket


def add_color_input(
    node_group: bpy.types.NodeTree,
    name: str,
    default: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
) -> Any:
    """Add color input socket to node group"""
    socket = node_group.interface.new_socket(
        name=name,
        in_out='INPUT',
        socket_type='NodeSocketColor'
    )
    if hasattr(socket, 'default_value'):
        socket.default_value = default
    return socket


def add_geometry_input(node_group: bpy.types.NodeTree, name: str = "Geometry") -> Any:
    """Add geometry input socket"""
    return node_group.interface.new_socket(
        name=name,
        in_out='INPUT',
        socket_type='NodeSocketGeometry'
    )


def add_float_output(node_group: bpy.types.NodeTree, name: str) -> Any:
    """Add float output socket to node group"""
    return node_group.interface.new_socket(
        name=name,
        in_out='OUTPUT',
        socket_type='NodeSocketFloat'
    )


def add_vector_output(node_group: bpy.types.NodeTree, name: str) -> Any:
    """Add vector output socket to node group"""
    return node_group.interface.new_socket(
        name=name,
        in_out='OUTPUT',
        socket_type='NodeSocketVector'
    )


def add_geometry_output(node_group: bpy.types.NodeTree, name: str = "Geometry") -> Any:
    """Add geometry output socket"""
    return node_group.interface.new_socket(
        name=name,
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry'
    )


def create_math_node_group(name: str = "MathOperations") -> bpy.types.NodeTree:
    """Create a reusable math operations node group"""
    group = create_reusable_node_group(name, 'ShaderNodeTree')
    
    # Add inputs
    add_float_input(group, "Value A", default=0.0)
    add_float_input(group, "Value B", default=1.0)
    add_float_input(group, "Factor", default=0.5, min_value=0.0, max_value=1.0)
    
    # Add output
    add_float_output(group, "Result")
    
    # Get nodes
    input_node = next(n for n in group.nodes if n.type == 'GROUP_INPUT')
    output_node = next(n for n in group.nodes if n.type == 'GROUP_OUTPUT')
    
    # Add math nodes
    multiply = group.nodes.new('ShaderNodeMath')
    multiply.operation = 'MULTIPLY'
    multiply.location = (0, 100)
    
    add = group.nodes.new('ShaderNodeMath')
    add.operation = 'ADD'
    add.location = (200, 0)
    
    # Connect nodes
    group.links.new(input_node.outputs['Value A'], multiply.inputs[0])
    group.links.new(input_node.outputs['Factor'], multiply.inputs[1])
    group.links.new(multiply.outputs['Value'], add.inputs[0])
    group.links.new(input_node.outputs['Value B'], add.inputs[1])
    group.links.new(add.outputs['Value'], output_node.inputs['Result'])
    
    return group


def create_geometry_transform_group(name: str = "TransformGeometry") -> bpy.types.NodeTree:
    """Create a reusable geometry transform node group"""
    group = create_reusable_node_group(name, 'GeometryNodeTree')
    
    # Add inputs
    add_geometry_input(group, "Geometry")
    add_vector_input(group, "Translation", default=(0.0, 0.0, 0.0))
    add_vector_input(group, "Rotation", default=(0.0, 0.0, 0.0))
    add_vector_input(group, "Scale", default=(1.0, 1.0, 1.0))
    
    # Add output
    add_geometry_output(group, "Geometry")
    
    # Get nodes
    input_node = next(n for n in group.nodes if n.type == 'GROUP_INPUT')
    output_node = next(n for n in group.nodes if n.type == 'GROUP_OUTPUT')
    
    # Add transform node
    transform = group.nodes.new('GeometryNodeTransform')
    transform.location = (0, 0)
    
    # Connect
    group.links.new(input_node.outputs['Geometry'], transform.inputs['Geometry'])
    group.links.new(input_node.outputs['Translation'], transform.inputs['Translation'])
    group.links.new(input_node.outputs['Rotation'], transform.inputs['Rotation'])
    group.links.new(input_node.outputs['Scale'], transform.inputs['Scale'])
    group.links.new(transform.outputs['Geometry'], output_node.inputs['Geometry'])
    
    return group


def add_glare_node(intensity=1.0):
    """Add glare node to compositor"""
    scene = bpy.context.scene
    if not scene.use_nodes:
        setup_compositor()
    
    tree = scene.node_tree
    
    # Find existing nodes
    render_layers = None
    composite = None
    for node in tree.nodes:
        if node.type == 'R_LAYERS':
            render_layers = node
        elif node.type == 'COMPOSITE':
            composite = node
    
    if render_layers and composite:
        glare = tree.nodes.new('CompositorNodeGlare')
        glare.glare_type = 'FOG_GLOW'
        glare.quality = 'MEDIUM'
        glare.mix = intensity
        
        # Re-connect
        tree.links.clear()
        tree.links.new(render_layers.outputs['Image'], glare.inputs['Image'])
        tree.links.new(glare.outputs['Image'], composite.inputs['Image'])
        
        return glare


def list_node_group_sockets(node_group: bpy.types.NodeTree) -> Dict[str, List[str]]:
    """List all sockets of a node group using 4.0+ API"""
    sockets = {
        'inputs': [],
        'outputs': []
    }
    
    # Iterate through interface items
    for item in node_group.interface.items_tree:
        if hasattr(item, 'item_type') and item.item_type == 'SOCKET':
            if hasattr(item, 'in_out'):
                if item.in_out == 'INPUT':
                    sockets['inputs'].append(item.name)
                elif item.in_out == 'OUTPUT':
                    sockets['outputs'].append(item.name)
    
    return sockets


def duplicate_node_group(
    source_name: str,
    new_name: str
) -> Optional[bpy.types.NodeTree]:
    """Duplicate an existing node group"""
    if source_name not in bpy.data.node_groups:
        print(f"Source node group '{source_name}' not found")
        return None
    
    source = bpy.data.node_groups[source_name]
    
    # Create new group of same type
    new_group = bpy.data.node_groups.new(new_name, type=source.bl_idname)
    
    # Copy interface using 4.0+ API
    for item in source.interface.items_tree:
        if hasattr(item, 'item_type') and item.item_type == 'SOCKET':
            new_group.interface.new_socket(
                name=item.name,
                in_out=item.in_out,
                socket_type=item.socket_type
            )
    
    # Copy nodes
    node_map = {}
    for node in source.nodes:
        new_node = new_group.nodes.new(node.bl_idname)
        new_node.location = node.location
        new_node.name = node.name
        
        # Copy settings
        for prop in node.bl_rna.properties:
            if not prop.is_readonly and prop.identifier not in ['type', 'location']:
                try:
                    setattr(new_node, prop.identifier, getattr(node, prop.identifier))
                except:
                    pass
        
        node_map[node] = new_node
    
    # Copy links
    for link in source.links:
        from_node = node_map.get(link.from_node)
        to_node = node_map.get(link.to_node)
        
        if from_node and to_node:
            # Find sockets by index
            from_socket = from_node.outputs[link.from_socket.index]
            to_socket = to_node.inputs[link.to_socket.index]
            new_group.links.new(from_socket, to_socket)
    
    return new_group
