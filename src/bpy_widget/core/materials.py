"""
Materials - DRY and functional
"""
import bpy
from typing import Dict, Tuple, Union

ColorType = Union[Tuple[float, float, float], Tuple[float, float, float, float]]


def _ensure_rgba(color: ColorType) -> Tuple[float, float, float, float]:
    """Ensure color is RGBA format"""
    return (*color, 1.0) if len(color) == 3 else color


def create_material(
    name: str,
    base_color: ColorType = (0.8, 0.8, 0.8),
    metallic: float = 0.0,
    roughness: float = 0.5,
    specular: float = 0.5,
    transmission: float = 0.0,
    ior: float = 1.45,
    emission_color: ColorType = (0.0, 0.0, 0.0),
    emission_strength: float = 0.0,
    alpha: float = 1.0,
    blend_method: str = 'OPAQUE'
) -> bpy.types.Material:
    """
    Universal material creation with all PBR parameters.
    
    Args:
        name: Material name
        base_color: Base color RGB(A)
        metallic: Metallic value (0-1)
        roughness: Roughness value (0-1)
        specular: Specular IOR level
        transmission: Transmission weight for glass
        ior: Index of refraction
        emission_color: Emission color RGB(A)
        emission_strength: Emission strength
        alpha: Alpha transparency
        blend_method: Blend mode ('OPAQUE', 'BLEND', 'CLIP', 'HASHED')
    """
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.blend_method = blend_method
    
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    
    # Set all parameters
    bsdf.inputs['Base Color'].default_value = _ensure_rgba(base_color)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Specular IOR Level'].default_value = specular
    bsdf.inputs['Transmission Weight'].default_value = transmission
    bsdf.inputs['IOR'].default_value = ior
    bsdf.inputs['Emission Color'].default_value = _ensure_rgba(emission_color)
    bsdf.inputs['Emission Strength'].default_value = emission_strength
    bsdf.inputs['Alpha'].default_value = alpha
    
    return mat


# Material presets dictionary for quick access
MATERIAL_PRESETS: Dict[str, Dict] = {
    # Metals
    'gold': {'base_color': (1.0, 0.766, 0.336), 'metallic': 1.0, 'roughness': 0.1},
    'silver': {'base_color': (0.972, 0.960, 0.915), 'metallic': 1.0, 'roughness': 0.1},
    'copper': {'base_color': (0.955, 0.637, 0.538), 'metallic': 1.0, 'roughness': 0.2},
    'chrome': {'base_color': (0.550, 0.556, 0.554), 'metallic': 1.0, 'roughness': 0.05},
    'iron': {'base_color': (0.560, 0.570, 0.580), 'metallic': 1.0, 'roughness': 0.4},
    
    # Non-metals
    'rubber': {'base_color': (0.1, 0.1, 0.1), 'roughness': 0.8},
    'plastic': {'base_color': (0.5, 0.5, 0.5), 'roughness': 0.4, 'specular': 0.5},
    'wood': {'base_color': (0.4, 0.25, 0.1), 'roughness': 0.7},
    'concrete': {'base_color': (0.5, 0.5, 0.5), 'roughness': 0.9},
    
    # Glass/Transparent
    'glass': {'transmission': 1.0, 'ior': 1.45, 'roughness': 0.0},
    'water': {'transmission': 1.0, 'ior': 1.33, 'roughness': 0.0, 'base_color': (0.8, 0.95, 1.0)},
    'diamond': {'transmission': 1.0, 'ior': 2.42, 'roughness': 0.0},
    
    # Emissive
    'neon_red': {'emission_color': (1.0, 0.0, 0.0), 'emission_strength': 5.0},
    'neon_blue': {'emission_color': (0.0, 0.5, 1.0), 'emission_strength': 5.0},
    'neon_green': {'emission_color': (0.0, 1.0, 0.3), 'emission_strength': 5.0},
}


def create_preset_material(name: str, preset: str) -> bpy.types.Material:
    """Create material from preset"""
    if preset not in MATERIAL_PRESETS:
        raise ValueError(f"Unknown preset: {preset}. Available: {list(MATERIAL_PRESETS.keys())}")
    
    return create_material(name, **MATERIAL_PRESETS[preset])


def assign_material(obj: bpy.types.Object, material: bpy.types.Material):
    """Assign material to object"""
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)


def get_or_create_material(name: str, **kwargs) -> bpy.types.Material:
    """Get existing material or create new one"""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    return create_material(name, **kwargs)
