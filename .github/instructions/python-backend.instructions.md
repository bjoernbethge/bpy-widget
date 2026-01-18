---
applies_to:
  - "src/bpy_widget/**/*.py"
  - "pyproject.toml"
---

# Python Backend Instructions

You are a Python engineer specializing in Blender's Python API (bpy) and interactive widget development.

## Technology Stack

- **Python**: 3.11+ (required by Blender 4.5)
- **Blender**: 4.5.4+ as Python module
- **Widget Framework**: anywidget for Jupyter/notebook integration
- **Data Processing**: polars, numpy
- **Logging**: loguru

## Core Blender API Patterns

### Context Access
**ALWAYS** use widget convenience properties instead of direct `bpy.context`:

```python
# ✅ Correct - Safe in headless environments
scene = widget.scene
objects = widget.objects
camera = widget.camera
active = widget.active_object

# ❌ Wrong - May fail in headless mode
scene = bpy.context.scene
objects = bpy.data.objects
```

### Scene Management
```python
# Clear scene safely
def clear_scene(self):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
```

### Object Creation
```python
# Use widget methods that handle context properly
cube = widget.create_test_cube(location=(0, 0, 0))
suzanne = widget.create_suzanne(location=(0, 0, 2))

# Direct bpy.ops calls should handle context
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
```

## Color Handling

### RGB/RGBA Format
**ALWAYS** use 0.0-1.0 range for color values:

```python
# ✅ Correct
base_color = (1.0, 0.5, 0.0, 1.0)  # RGBA
background = (0.05, 0.05, 0.1)      # RGB

# ❌ Wrong - Never use 0-255 integer values
base_color = (255, 128, 0)  # Will cause incorrect colors
```

### Material Colors
```python
def create_material(
    name: str,
    base_color: tuple[float, float, float, float] = (0.8, 0.8, 0.8, 1.0),
    metallic: float = 0.0,
    roughness: float = 0.5,
    emission_strength: float = 0.0
) -> bpy.types.Material:
    """Create a PBR material with specified properties."""
    # Implementation...
```

## Type Hints

### Required Annotations
Always use type hints for:
- Function parameters
- Return values
- Class attributes

```python
from typing import Optional, Union
import bpy

def assign_material(
    obj: bpy.types.Object,
    material: bpy.types.Material
) -> None:
    """Assign material to object."""
    if not obj.data.materials:
        obj.data.materials.append(material)
    else:
        obj.data.materials[0] = material
```

### Common Blender Types
```python
import bpy.types as bpy_types

# Common types
scene: bpy_types.Scene
obj: bpy_types.Object
material: bpy_types.Material
camera: bpy_types.Camera
nodes: bpy_types.NodeTree
```

## Rendering

### GPU Backend Selection
```python
def set_gpu_backend(self, backend: str) -> None:
    """Set GPU backend (VULKAN or OPENGL)."""
    if backend not in ["VULKAN", "OPENGL"]:
        raise ValueError(f"Invalid backend: {backend}")
    
    # Vulkan requires Blender 4.5+
    if backend == "VULKAN" and bpy.app.version < (4, 5, 0):
        logger.warning("Vulkan requires Blender 4.5+, falling back to OpenGL")
        backend = "OPENGL"
    
    bpy.context.preferences.system.gpu_backend = backend
```

### Render Engine Configuration
```python
def set_render_engine(self, engine: str) -> None:
    """Set render engine (BLENDER_EEVEE_NEXT or CYCLES)."""
    valid_engines = ["BLENDER_EEVEE_NEXT", "CYCLES"]
    if engine not in valid_engines:
        raise ValueError(f"Engine must be one of {valid_engines}")
    
    self.scene.render.engine = engine
```

### Headless Rendering
```python
# Check for CI environment
import os
if os.getenv("CI"):
    # Use Cycles CPU in CI
    widget.set_render_engine("CYCLES")
    widget.scene.cycles.device = "CPU"
else:
    # Use EEVEE Next with Vulkan locally
    widget.set_render_engine("BLENDER_EEVEE_NEXT")
    widget.set_gpu_backend("VULKAN")
```

## Data Import/Export

### CSV/Parquet Import
```python
import polars as pl

def import_data(
    self,
    filepath: str,
    as_type: str = "points",
    point_size: float = 0.1
) -> list[bpy.types.Object]:
    """Import data from CSV/Parquet as 3D objects.
    
    Args:
        filepath: Path to data file
        as_type: Type of object ('points', 'curve', 'series')
        point_size: Size of point objects
        
    Returns:
        List of created Blender objects
    """
    # Use polars for efficient data loading
    df = pl.read_csv(filepath) if filepath.endswith('.csv') else pl.read_parquet(filepath)
    
    # Create objects from data
    objects = []
    for row in df.iter_rows():
        # Create point or curve based on type
        pass
    
    return objects
```

### 3D Format Import
```python
def import_gltf(self, filepath: str) -> list[bpy.types.Object]:
    """Import GLTF/GLB file."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=filepath)
    after = set(bpy.data.objects)
    return list(after - before)
```

## Error Handling

### Informative Errors
```python
from loguru import logger

def create_preset_material(name: str, preset: str) -> bpy.types.Material:
    """Create material from preset."""
    valid_presets = ["gold", "silver", "glass", "rubber"]
    
    if preset not in valid_presets:
        logger.error(f"Invalid preset: {preset}")
        raise ValueError(
            f"Preset '{preset}' not found. "
            f"Valid presets: {', '.join(valid_presets)}"
        )
    
    # Create material
    logger.info(f"Creating {preset} material: {name}")
    return _create_material_impl(name, preset)
```

### Graceful Degradation
```python
def set_gpu_backend(self, backend: str) -> None:
    """Set GPU backend with fallback."""
    try:
        bpy.context.preferences.system.gpu_backend = backend
        logger.info(f"GPU backend set to {backend}")
    except Exception as e:
        logger.warning(f"Failed to set {backend} backend: {e}")
        logger.info("Falling back to OpenGL")
        bpy.context.preferences.system.gpu_backend = "OPENGL"
```

## Widget Integration

### Traitlets Properties
```python
import traitlets

class BpyWidget(anywidget.AnyWidget):
    # Synced with JavaScript
    image_data = traitlets.Unicode("").tag(sync=True)
    camera_position = traitlets.Dict(default_value={}).tag(sync=True)
    
    # Python-only (not synced)
    _scene_objects = traitlets.List()
```

### Rendering Pipeline
```python
def render(self) -> None:
    """Render scene and update widget."""
    # Render to image
    bpy.context.scene.render.filepath = "/tmp/render.png"
    bpy.ops.render.render(write_still=True)
    
    # Convert to base64
    with open("/tmp/render.png", "rb") as f:
        import base64
        img_data = base64.b64encode(f.read()).decode()
    
    # Update widget
    self.image_data = img_data
```

## Performance Optimization

### Debouncing
```python
import threading

class BpyWidget:
    def __init__(self):
        self._render_timer = None
        self._render_delay = 0.1  # 100ms
    
    def _debounced_render(self):
        """Render with debouncing to avoid excessive updates."""
        if self._render_timer:
            self._render_timer.cancel()
        
        self._render_timer = threading.Timer(
            self._render_delay,
            self.render
        )
        self._render_timer.start()
```

### Efficient Scene Updates
```python
def update_material_color(self, obj: bpy.types.Object, color: tuple):
    """Update material without full scene refresh."""
    if not obj.active_material:
        return
    
    # Update only changed properties
    nodes = obj.active_material.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    if principled:
        principled.inputs["Base Color"].default_value = color
    
    # Trigger minimal update
    bpy.context.view_layer.update()
```

## Logging

### Use loguru
```python
from loguru import logger

# Info level for user-facing operations
logger.info(f"Created material: {name}")

# Debug for internal details
logger.debug(f"Material nodes: {len(material.node_tree.nodes)}")

# Warning for recoverable issues
logger.warning("Vulkan not available, using OpenGL")

# Error for failures
logger.error(f"Failed to load file: {filepath}")
```

### Context in Logs
```python
logger.info(
    f"Rendering scene with {len(self.scene.objects)} objects "
    f"at {width}x{height} using {self.scene.render.engine}"
)
```

## Testing

### Use clean_scene Fixture
```python
def test_create_cube(clean_scene):
    """Test cube creation."""
    widget = BpyWidget()
    cube = widget.create_test_cube(location=(0, 0, 0))
    
    assert cube is not None
    assert cube.name.startswith("Cube")
    assert len(widget.scene.objects) == 1
```

### Test Material Properties
```python
def test_gold_material(clean_scene):
    """Test gold material properties."""
    widget = BpyWidget()
    mat = widget.create_preset_material("Gold", "gold")
    
    # Check metallic value
    nodes = mat.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    assert principled.inputs["Metallic"].default_value > 0.9
    
    # Check color is gold-ish
    color = principled.inputs["Base Color"].default_value
    assert color[0] > 0.8  # Red channel high
    assert color[1] > 0.6  # Green channel medium
    assert color[2] < 0.3  # Blue channel low
```

### Mock External Dependencies
```python
from unittest.mock import patch, MagicMock

@patch("bpy_widget.core.io_handlers.pl.read_csv")
def test_import_csv(mock_read_csv, clean_scene):
    """Test CSV import with mocked data."""
    mock_df = MagicMock()
    mock_df.iter_rows.return_value = [(0, 0, 0), (1, 1, 1)]
    mock_read_csv.return_value = mock_df
    
    widget = BpyWidget()
    objects = widget.import_data("test.csv", as_type="points")
    
    assert len(objects) == 2
```

## Docstrings

### Google Style
```python
def create_material(
    name: str,
    base_color: tuple[float, float, float, float] = (0.8, 0.8, 0.8, 1.0),
    metallic: float = 0.0,
    roughness: float = 0.5
) -> bpy.types.Material:
    """Create a PBR material with specified properties.
    
    Creates a material with Principled BSDF shader node configured
    with the specified PBR properties. The material uses Blender's
    standard material system.
    
    Args:
        name: Material name (must be unique)
        base_color: RGBA color tuple (0.0-1.0 range)
        metallic: Metallic value (0.0-1.0, 0=dielectric, 1=metal)
        roughness: Roughness value (0.0-1.0, 0=smooth, 1=rough)
    
    Returns:
        Created Blender material object
    
    Raises:
        ValueError: If color values are out of range
    
    Example:
        >>> mat = widget.create_material(
        ...     "Copper",
        ...     base_color=(0.95, 0.64, 0.54, 1.0),
        ...     metallic=1.0,
        ...     roughness=0.2
        ... )
    """
```

## Common Patterns

### Extension Management (Blender 4.5+)
```python
def install_extension(self, pkg_id: str) -> bool:
    """Install Blender extension by package ID.
    
    Searches online repositories and installs the extension.
    """
    try:
        bpy.ops.extensions.package_install(pkg_id=pkg_id)
        logger.info(f"Installed extension: {pkg_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to install {pkg_id}: {e}")
        return False
```

### Compositor Setup
```python
def setup_extended_compositor(self) -> None:
    """Setup compositor with node tree."""
    scene = self.scene
    scene.use_nodes = True
    tree = scene.node_tree
    
    # Clear existing nodes
    tree.nodes.clear()
    
    # Add render layers and composite nodes
    render_layers = tree.nodes.new("CompositorNodeRLayers")
    composite = tree.nodes.new("CompositorNodeComposite")
    
    # Link nodes
    tree.links.new(render_layers.outputs[0], composite.inputs[0])
```

## Security

### Path Validation
```python
import os
from pathlib import Path

def import_file(self, filepath: str) -> None:
    """Import file with path validation."""
    path = Path(filepath).resolve()
    
    # Prevent path traversal
    if ".." in str(path):
        raise ValueError("Path traversal detected")
    
    # Check file exists
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    # Validate extension
    allowed_extensions = [".csv", ".parquet", ".gltf", ".glb"]
    if path.suffix not in allowed_extensions:
        raise ValueError(f"Unsupported file type: {path.suffix}")
```

### Input Sanitization
```python
def set_object_name(self, obj: bpy.types.Object, name: str) -> None:
    """Set object name with sanitization."""
    # Remove special characters
    safe_name = "".join(c for c in name if c.isalnum() or c in "._- ")
    obj.name = safe_name[:63]  # Blender name limit
```

## Resources

- [Blender Python API Docs](https://docs.blender.org/api/current/)
- [anywidget Documentation](https://anywidget.dev/)
- [polars Documentation](https://pola-rs.github.io/polars/)
- [loguru Documentation](https://loguru.readthedocs.io/)
