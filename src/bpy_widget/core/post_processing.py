"""
Extended post-processing effects for compositor - Blender 4.5 compatible
"""
from typing import Optional, Tuple

import bpy


def setup_extended_compositor() -> bpy.types.NodeTree:
    """Setup compositor with extended post-processing capabilities
    
    Enables GPU acceleration for compositor if available (Blender 4.5+)
    """
    scene = bpy.context.scene
    scene.use_nodes = True
    scene.render.use_compositing = True
    
    # Enable GPU compositing for better performance (Blender 4.5+)
    try:
        if hasattr(scene.render, 'use_compositor_gpu'):
            scene.render.use_compositor_gpu = True
    except Exception:
        pass  # GPU compositing not available in this version
    
    tree = scene.node_tree
    nodes = tree.nodes
    links = tree.links
    
    # Clear existing
    nodes.clear()
    
    # Create base nodes
    render_layers = nodes.new('CompositorNodeRLayers')
    composite = nodes.new('CompositorNodeComposite')
    viewer = nodes.new('CompositorNodeViewer')
    
    # Position base nodes
    render_layers.location = (0, 0)
    composite.location = (1200, 0)
    viewer.location = (1200, -200)
    
    # Basic connection
    links.new(render_layers.outputs['Image'], composite.inputs['Image'])
    
    return tree


def add_bloom_glare(intensity: float = 1.0, threshold: float = 1.0) -> Optional[bpy.types.Node]:
    """Add bloom/glare effect"""
    tree = bpy.context.scene.node_tree
    if not tree:
        return None
    
    nodes = tree.nodes
    links = tree.links
    
    # Find render layers
    render_layers = None
    for node in nodes:
        if node.type == 'R_LAYERS':
            render_layers = node
            break
    
    if not render_layers:
        return None
    
    # Create glare node
    glare = nodes.new('CompositorNodeGlare')
    glare.glare_type = 'FOG_GLOW'
    glare.quality = 'HIGH'
    glare.threshold = threshold
    glare.mix = intensity
    glare.location = (300, 0)
    
    # Find composite node
    composite = None
    for node in nodes:
        if node.type == 'COMPOSITE':
            composite = node
            break
    
    if composite:
        # Remove existing connection
        for link in list(links):
            if link.to_node == composite and link.to_socket.name == 'Image':
                links.remove(link)
        
        # Connect through glare
        links.new(render_layers.outputs['Image'], glare.inputs['Image'])
        links.new(glare.outputs['Image'], composite.inputs['Image'])
    
    return glare


def add_color_correction(
    brightness: float = 0.0,
    contrast: float = 0.0,
    saturation: float = 1.0,
    gain: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    gamma: float = 1.0
) -> Optional[bpy.types.Node]:
    """Add color correction node"""
    tree = bpy.context.scene.node_tree
    if not tree:
        return None
    
    nodes = tree.nodes
    links = tree.links
    
    # Create nodes
    bright_contrast = nodes.new('CompositorNodeBrightContrast')
    bright_contrast.location = (450, 0)
    bright_contrast.inputs['Bright'].default_value = brightness
    bright_contrast.inputs['Contrast'].default_value = contrast
    
    hue_sat = nodes.new('CompositorNodeHueSat')
    hue_sat.location = (600, 0)
    hue_sat.inputs['Saturation'].default_value = saturation
    
    color_balance = nodes.new('CompositorNodeColorBalance')
    color_balance.location = (750, 0)
    color_balance.correction_method = 'LIFT_GAMMA_GAIN'
    color_balance.gain = gain
    color_balance.gamma = (gamma, gamma, gamma)
    
    # Find nodes to connect
    source_node = None
    target_node = None
    
    for node in nodes:
        if node.type == 'GLARE':
            source_node = node
        elif node.type == 'R_LAYERS' and not source_node:
            source_node = node
        
        if node.type == 'COMPOSITE':
            target_node = node
    
    if source_node and target_node:
        # Remove existing connection to composite
        for link in list(links):
            if link.to_node == target_node and link.to_socket.name == 'Image':
                links.remove(link)
        
        # Connect color correction chain
        links.new(source_node.outputs['Image'], bright_contrast.inputs['Image'])
        links.new(bright_contrast.outputs['Image'], hue_sat.inputs['Image'])
        links.new(hue_sat.outputs['Image'], color_balance.inputs['Image'])
        links.new(color_balance.outputs['Image'], target_node.inputs['Image'])
    
    return color_balance


def add_vignette(amount: float = 0.3, center: Tuple[float, float] = (0.5, 0.5)) -> Optional[bpy.types.Node]:
    """Add vignette effect - Simplified for Blender 4.5"""
    tree = bpy.context.scene.node_tree
    if not tree:
        return None
    
    nodes = tree.nodes
    links = tree.links
    
    # Find what's connected to composite
    composite = None
    source_socket = None
    
    for node in nodes:
        if node.type == 'COMPOSITE':
            composite = node
            break
    
    if not composite:
        return None
    
    # Find the current input to composite
    for link in links:
        if link.to_node == composite and link.to_socket.name == 'Image':
            source_socket = link.from_socket
            links.remove(link)
            break
    
    if not source_socket:
        # Nothing connected to composite, find any output node
        for node in nodes:
            if 'Image' in node.outputs:
                source_socket = node.outputs['Image']
                break
    
    if not source_socket:
        return None
    
    # Create vignette nodes
    ellipse = nodes.new('CompositorNodeEllipseMask')
    ellipse.location = (800, -200)
    ellipse.x = center[0]
    ellipse.y = center[1]
    ellipse.width = 1.0
    ellipse.height = 0.75
    
    invert = nodes.new('CompositorNodeInvert')
    invert.location = (950, -200)
    
    mix = nodes.new('CompositorNodeMixRGB')
    mix.location = (1100, 0)
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Fac'].default_value = amount
    
    # Connect vignette chain
    links.new(ellipse.outputs['Mask'], invert.inputs['Color'])
    # Connect inverted mask directly to mix (skip color ramp for simplicity)
    links.new(invert.outputs['Color'], mix.inputs[2])  # Second Image input (mask)
    links.new(source_socket, mix.inputs[1])  # First Image input (original image)
    links.new(mix.outputs['Image'], composite.inputs['Image'])
    
    return mix


def add_film_grain(amount: float = 0.05) -> Optional[bpy.types.Node]:
    """Add film grain effect - Simplified for Blender 4.5"""
    tree = bpy.context.scene.node_tree
    if not tree:
        return None
    
    nodes = tree.nodes
    links = tree.links
    
    # Find composite and source
    composite = None
    source_socket = None
    
    for node in nodes:
        if node.type == 'COMPOSITE':
            composite = node
            break
    
    if not composite:
        return None
    
    # Find current input
    for link in links:
        if link.to_node == composite and link.to_socket.name == 'Image':
            source_socket = link.from_socket
            links.remove(link)
            break
    
    if not source_socket:
        return None
    
    # Create noise texture
    texture = nodes.new('CompositorNodeTexture')
    texture.location = (900, -400)
    
    # Create new texture if needed
    if not texture.texture:
        tex = bpy.data.textures.new("FilmGrain", type='NOISE')
        tex.noise_scale = 0.1
        texture.texture = tex
    
    # Mix node for grain
    mix = nodes.new('CompositorNodeMixRGB')
    mix.location = (1050, 0)
    mix.blend_type = 'OVERLAY'
    mix.inputs['Fac'].default_value = amount
    
    # Connect
    links.new(source_socket, mix.inputs[1])  # Original image
    links.new(texture.outputs['Color'], mix.inputs[2])  # Noise
    links.new(mix.outputs['Image'], composite.inputs['Image'])
    
    return mix


def add_chromatic_aberration(amount: float = 0.001) -> Optional[bpy.types.Node]:
    """Add chromatic aberration effect"""
    tree = bpy.context.scene.node_tree
    if not tree:
        return None
    
    nodes = tree.nodes
    links = tree.links
    
    # Find composite and source
    composite = None
    source_socket = None
    
    for node in nodes:
        if node.type == 'COMPOSITE':
            composite = node
            break
    
    if not composite:
        return None
    
    # Find current input
    for link in links:
        if link.to_node == composite and link.to_socket.name == 'Image':
            source_socket = link.from_socket
            links.remove(link)
            break
    
    if not source_socket:
        return None
    
    # Create lens distortion node
    lens = nodes.new('CompositorNodeLensdist')
    lens.location = (1100, 0)
    lens.use_projector = False
    lens.inputs['Distort'].default_value = 0.0
    lens.inputs['Dispersion'].default_value = amount
    
    # Connect
    links.new(source_socket, lens.inputs['Image'])
    links.new(lens.outputs['Image'], composite.inputs['Image'])
    
    return lens


def add_motion_blur(samples: int = 8, shutter: float = 0.5) -> None:
    """Enable motion blur in render settings"""
    scene = bpy.context.scene
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = shutter
    
    if scene.render.engine == 'BLENDER_EEVEE_NEXT':
        scene.eevee.motion_blur_samples = samples
    elif scene.render.engine == 'CYCLES':
        scene.cycles.motion_blur_position = 'CENTER'


def add_depth_of_field(
    focus_object: Optional[bpy.types.Object] = None,
    focus_distance: float = 10.0,
    fstop: float = 2.8
) -> None:
    """Setup depth of field for camera"""
    camera = bpy.context.scene.camera
    if not camera or camera.type != 'CAMERA':
        print("No camera found in scene")
        return
    
    cam_data = camera.data
    cam_data.dof.use_dof = True
    cam_data.dof.aperture_fstop = fstop
    
    if focus_object:
        cam_data.dof.focus_object = focus_object
    else:
        cam_data.dof.focus_distance = focus_distance
    
    print(f"Depth of field enabled: f/{fstop}")


def add_sharpen(amount: float = 0.1) -> Optional[bpy.types.Node]:
    """Add sharpening filter - Simplified for Blender 4.5"""
    tree = bpy.context.scene.node_tree
    if not tree:
        return None
    
    nodes = tree.nodes
    links = tree.links
    
    # Find composite and source
    composite = None
    source_socket = None
    
    for node in nodes:
        if node.type == 'COMPOSITE':
            composite = node
            break
    
    if not composite:
        return None
    
    # Find current input
    for link in links:
        if link.to_node == composite and link.to_socket.name == 'Image':
            source_socket = link.from_socket
            links.remove(link)
            break
    
    if not source_socket:
        return None
    
    # Create filter node
    filter_node = nodes.new('CompositorNodeFilter')
    filter_node.location = (1000, 200)
    filter_node.filter_type = 'SHARPEN'
    
    # Create mix node to control amount
    mix = nodes.new('CompositorNodeMixRGB')
    mix.location = (1150, 200)
    mix.blend_type = 'MIX'
    mix.inputs['Fac'].default_value = amount
    
    # Connect
    links.new(source_socket, filter_node.inputs['Image'])
    links.new(source_socket, mix.inputs[1])  # Original
    links.new(filter_node.outputs['Image'], mix.inputs[2])  # Sharpened
    links.new(mix.outputs['Image'], composite.inputs['Image'])
    
    return mix


def reset_compositor() -> None:
    """Reset compositor to default state"""
    scene = bpy.context.scene
    if scene.use_nodes:
        tree = scene.node_tree
        tree.nodes.clear()
        
        # Create minimal setup
        render_layers = tree.nodes.new('CompositorNodeRLayers')
        composite = tree.nodes.new('CompositorNodeComposite')
        
        render_layers.location = (0, 0)
        composite.location = (300, 0)
        
        tree.links.new(render_layers.outputs['Image'], composite.inputs['Image'])
        
        print("Compositor reset to default")
