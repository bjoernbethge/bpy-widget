# bpy-widget Test Suite

## Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_rendering.py -v

# Run with coverage
uv run pytest tests/ --cov=bpy_widget --cov-report=html
```

## Test Structure

- `conftest.py` - Pytest fixtures and configuration
- `test_rendering.py` - Tests for rendering module (render_to_pixels, temp file cleanup)
- `test_scene.py` - Tests for scene management (clear_scene, race condition fixes)
- `test_materials.py` - Tests for material creation and presets
- `test_io_handlers.py` - Tests for I/O validation and file handling

## Fixtures

- `clean_scene` - Ensures clean Blender scene before each test
- `test_cube` - Creates a test cube object
- `test_camera` - Creates a test camera

## Requirements

Tests require:
- `pytest` (included in dev dependencies)
- Blender 4.5+ with bpy module
- All project dependencies
