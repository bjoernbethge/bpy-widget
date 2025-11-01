# bpy-widget

Interactive Blender 3D viewport widget for Jupyter/Marimo notebooks with real-time EEVEE Next rendering.

## Features

- 🎨 **Interactive 3D Viewport** - Real-time camera controls with mouse/touch
- ⚡ **EEVEE Next & Cycles** - Switch between render engines on the fly  
- 🎬 **Post-Processing** - Bloom, vignette, color correction, and more
- 📊 **Data Visualization** - Import CSV/Parquet data as 3D objects
- 🔄 **Live Updates** - Changes render immediately
- 📦 **Import/Export** - Support for GLTF, USD, Alembic formats
- 🧩 **Extension Management** - Manage Blender extensions and addons

## Installation

```bash
uv add bpy-widget
```

**Requirements:**
- Python 3.11 (required by Blender 4.5)
- Blender 4.5+ as Python module (installed automatically via pip)

## Quick Start

```python
from bpy_widget import BpyWidget
import marimo as mo

# Create widget
widget = BpyWidget(width=800, height=600)

# Display in notebook
widget
```

The widget automatically initializes with a test scene. You can interact with it immediately:
- **Drag** to rotate camera
- **Scroll** to zoom
- **Touch** gestures on mobile

## Detailed Usage

### Scene Setup

```python
# Clear and setup new scene
widget.clear_scene()
widget.setup_lighting(sun_energy=3.0, add_fill_light=True)
widget.setup_world_background(color=(0.05, 0.05, 0.1))

# Create objects
cube = widget.create_test_cube(location=(0, 0, 0))
suzanne = widget.create_suzanne(location=(0, 0, 2))
torus = widget.create_torus(location=(3, 0, 0))
```

### Material System

```python
# Use material presets
gold_mat = widget.create_preset_material("MyGold", "gold")
glass_mat = widget.create_preset_material("MyGlass", "glass")

# Or create custom materials
custom = widget.create_material(
    "Custom",
    base_color=(0.8, 0.2, 0.2),
    metallic=0.5,
    roughness=0.4,
    emission_strength=0.1
)

# Apply to objects
widget.assign_material(suzanne, gold_mat)
```

Available presets: `gold`, `silver`, `copper`, `chrome`, `glass`, `water`, `diamond`, `rubber`, `plastic`, `wood`, `concrete`, `neon_red`, `neon_blue`, `neon_green`

### Data Import

```python
# Import point cloud
widget.import_data("data.csv", as_type="points", point_size=0.1)

# Import as curve
widget.import_data("timeseries.csv", as_type="curve")

# Import multiple series
widget.import_data(
    "multi_series.csv", 
    as_type="series",
    value_columns=["col1", "col2", "col3"]
)

# Batch import
widget.batch_import(["*.csv", "*.parquet"], as_type="points")
```

### Post-Processing Effects

```python
# Setup compositor with effects
widget.setup_extended_compositor()

# Add individual effects
widget.add_bloom_glare(intensity=0.8, threshold=0.8)
widget.add_color_correction(brightness=0.1, contrast=0.1, saturation=1.1)
widget.add_vignette(amount=0.2)
widget.add_film_grain(amount=0.03)
widget.add_chromatic_aberration(amount=0.001)
widget.add_sharpen(amount=0.1)

# Camera effects
widget.add_depth_of_field(focus_distance=5.0, fstop=2.8)
widget.add_motion_blur(samples=8, shutter=0.5)
```

### Import/Export 3D Formats

```python
# GLTF/GLB
objects = widget.import_gltf("model.glb")
widget.export_gltf("output.glb")

# USD/USDZ
objects = widget.import_usd("scene.usd")
widget.export_usd("output.usd")

# Alembic
objects = widget.import_alembic("animation.abc")
widget.export_alembic("output.abc")

# Scene as Parquet (for data analysis)
widget.export_scene_as_parquet("scene_data.parquet")
objects = widget.import_scene_from_parquet("scene_data.parquet")
```

### Extension Management (Blender 4.2+)

```python
# List repositories and extensions
repos = widget.list_repositories()
extensions = widget.list_extensions()

# Enable/disable extensions
widget.enable_extension("node_wrangler")
widget.disable_extension("node_wrangler")

# Install from file
widget.install_extension_from_file("my_extension.zip")

# Sync and upgrade
widget.sync_repositories()
widget.upgrade_extensions()

# Legacy addon support
widget.enable_legacy_addon("space_view3d_copy_attributes")
```

### Performance Settings

```python
# Switch render engines
widget.set_render_engine("CYCLES")  # or "BLENDER_EEVEE_NEXT"
widget.render_device = "GPU"  # For Cycles

# Adjust resolution
widget.set_resolution(1920, 1080)

# Optimize for speed
widget.scene.eevee.taa_render_samples = 8
widget.scene.eevee.use_raytracing = False
```

## Direct Blender API Access

```python
# Access Blender's API directly
widget.ops.mesh.primitive_uv_sphere_add(location=(0, 0, 5))
widget.data.objects["Sphere"].scale = (2, 2, 2)
widget.context.view_layer.update()

# Access the scene
scene = widget.scene
scene.frame_set(1)
scene.render.fps = 30
```

## Development

```bash
# Clone repository
git clone https://github.com/bjoernbethge/bpy-widget.git
cd bpy-widget

# Install with dev dependencies
uv sync --dev

# Run example notebook
marimo edit examples/basic_usage.py
```

## Examples

- `examples/basic_usage.py` - Interactive Marimo notebook with all features
- `examples/data_import.py` - Data visualization examples

## Troubleshooting

### Import Errors
- Ensure Python 3.11 is installed (required by Blender 4.5)
- Check `bpy` module: `pip show bpy` (should be 4.5.x)

### Rendering Issues
- EEVEE Next requires OpenGL support (use Cycles for headless servers)
- For headless environments: `widget.set_render_engine("CYCLES")`

### Material Colors
- Always use RGB or RGBA tuples: `(1.0, 0.5, 0.0)` or `(1.0, 0.5, 0.0, 1.0)`
- Values should be 0.0-1.0 range

## License

MIT License - see LICENSE file for details.

## Credits

Built with:
- [Blender](https://www.blender.org/) - 3D creation suite
- [anywidget](https://anywidget.dev/) - Custom Jupyter widgets
- [Marimo](https://marimo.io/) - Reactive notebooks
