# BPY Widget

Interactive Blender 3D viewport widget for notebooks with real-time Eevee Next rendering.

![BPY Widget Demo](https://img.shields.io/badge/Blender-4.4-orange.svg)
![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🚀 Features

- **Interactive 3D Viewport**: Real-time camera control with mouse/touch
  - 🖱️ **Drag** to rotate camera
  - 📏 **Scroll** to zoom in/out
  - 📱 **Touch** support for mobile devices
- **High-Performance Rendering**: Powered by Blender's Eevee Next engine
- **Live Performance Metrics**: FPS counter and render time display
- **Seamless Notebook Integration**: Reactive updates and state synchronization
- **Easy to Use**: Simple API with automatic scene setup

## 📋 Requirements

- Python 3.11+

## 🛠️ Installation

### From Source

```bash
git clone https://github.com/yourusername/bpy-widget.git
cd bpy-widget
pip install -e .
```

### Using UV (Recommended)

```bash
uv sync
```

## 🎯 Quick Start

```python
import marimo as mo
from bpy_widget import BpyWidget

# Create widget with custom size
widget = BpyWidget(width=800, height=600)

# Display in notebook
widget
```

## 📚 Examples

### Basic Usage

Run the example notebook:

```bash
marimo edit examples/basic_usage.py
```

### Custom Scene

```python
from bpy_widget import BlenderWidget

# Create widget
widget = BlenderWidget(width=1024, height=768)

# Access Blender API
widget.clear_scene()
widget.setup_camera(location=(10, -10, 8))
widget.setup_lighting()

# Add objects
widget.create_suzanne()
widget.create_test_cube()

# Render
widget.render()
```

### Material Creation

```python
# Apply to object
widget.objects["Suzanne"].data.materials.clear()
widget.objects["Suzanne"].data.materials.append(chrome)

# Update view
widget.render()
```

## 🔧 API Reference

### BlenderWidget

Main widget class for interactive 3D viewport.

#### Constructor

```python
BlenderWidget(width=512, height=512, auto_init=True)
```

- `width`: Viewport width in pixels
- `height`: Viewport height in pixels  
- `auto_init`: Automatically initialize scene with defaults

#### Properties

- `scene`: Current Blender scene
- `objects`: Dictionary of scene objects
- `context`: Blender context
- `data`: Blender data
- `ops`: Blender operators

#### Methods

- `clear_scene()`: Remove all objects from scene
- `setup_camera(location, rotation)`: Position camera
- `setup_lighting()`: Add default lighting
- `create_material(name, base_color, metallic, roughness)`: Create PBR material
- `create_suzanne()`: Add Suzanne mesh
- `create_test_cube()`: Add test cube
- `render()`: Update viewport rendering
- `debug_info()`: Print scene information

## 🎨 Architecture

The widget uses a modular architecture:

- `widget.py`: Main widget class with AnyWidget integration
- `core/`: Core Blender functionality modules
  - `camera.py`: Camera positioning and controls
  - `rendering.py`: Render pipeline setup
  - `lighting.py`: Scene lighting utilities
  - `materials.py`: Material creation helpers
- `static/`: Frontend assets
  - `widget.js`: Interactive controls and display
  - `widget.css`: Styling

## ⚡ Performance

- ** Rendering**: ~3 FPS interactive performance
- **Smart Throttling**: Updates batched
- **Minimal Overhead**: Direct pixel buffer access
- **Responsive Controls**: Local state for instant feedback

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Blender Foundation for the amazing bpy module
- Marimo team for the reactive notebook platform
- AnyWidget for the widget framework

## 🐛 Known Issues

- Initial audio warning from Blender can be ignored
- Performance may vary based on scene complexity
- Touch controls require modern browser support

## 📮 Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Include system info and error messages

---

Made with ❤️ for the Blender and Marimo communities
