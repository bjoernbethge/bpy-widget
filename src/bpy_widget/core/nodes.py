"""
Node Utilities - Analog zu utils.py node functions
"""
import bpy


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
