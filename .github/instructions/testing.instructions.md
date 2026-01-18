---
applies_to:
  - "tests/**/*.py"
  - "tests/conftest.py"
---

# Testing Instructions

You are a test engineer specializing in pytest and Blender Python testing.

## Testing Framework

- **Framework**: pytest
- **Fixtures**: Defined in `tests/conftest.py`
- **Environment**: Headless Blender with Xvfb in CI
- **Render Engine**: Cycles CPU when `CI=true` environment variable is set

## Running Tests

### Local Testing
```bash
# Run all tests
uv run pytest -v

# Run specific test file
uv run pytest tests/test_materials.py -v

# Run specific test
uv run pytest tests/test_materials.py::test_create_material_basic -v

# Run with coverage
uv run pytest --cov=src/bpy_widget --cov-report=html

# Run with verbose output and stop on first failure
uv run pytest -v -x
```

### CI Testing
Tests run automatically in GitHub Actions with:
- Xvfb for headless display (`:99`)
- Software rendering (`LIBGL_ALWAYS_SOFTWARE=1`)
- Cycles CPU renderer (when `CI=true`)
- 5-minute timeout

## Test Structure

### File Organization
- Test files mirror source structure: `src/bpy_widget/core/materials.py` → `tests/test_materials.py`
- All test files prefixed with `test_`
- Group related tests in the same file

### Naming Conventions
```python
# Test function naming: test_<functionality>_<scenario>
def test_create_material_basic():
    """Basic material creation."""

def test_create_material_with_emission():
    """Material with emission properties."""

def test_create_preset_material_gold():
    """Gold preset material."""

def test_assign_material_to_object():
    """Material assignment to object."""
```

## Essential Fixtures

### clean_scene Fixture
**ALWAYS** use `clean_scene` fixture for tests that manipulate Blender scene:

```python
def test_create_cube(clean_scene):
    """Test cube creation with clean scene."""
    widget = BpyWidget()
    cube = widget.create_test_cube(location=(0, 0, 0))
    
    assert cube is not None
    assert len(widget.scene.objects) == 1
```

The fixture ensures:
- Clean scene state before each test
- No leftover objects from previous tests
- Proper cleanup after test completion

### Fixture Definition (conftest.py)
```python
import pytest
import bpy

@pytest.fixture
def clean_scene():
    """Provide a clean Blender scene for each test."""
    # Clear all objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Clear materials
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)
    
    # Reset scene settings
    bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
    
    yield
    
    # Cleanup after test
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
```

## Testing Patterns

### Testing Object Creation
```python
def test_create_suzanne(clean_scene):
    """Test Suzanne monkey head creation."""
    widget = BpyWidget()
    suzanne = widget.create_suzanne(location=(0, 0, 2))
    
    assert suzanne is not None
    assert suzanne.type == 'MESH'
    assert "Suzanne" in suzanne.name
    assert suzanne.location.z == 2.0
```

### Testing Materials
```python
def test_create_material_basic(clean_scene):
    """Test basic material creation."""
    mat = create_material(
        name="TestMaterial",
        base_color=(1.0, 0.0, 0.0, 1.0),
        metallic=0.5,
        roughness=0.3
    )
    
    assert mat is not None
    assert mat.name == "TestMaterial"
    assert mat.use_nodes is True
    
    # Check node properties
    nodes = mat.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    assert principled is not None
    assert principled.inputs["Metallic"].default_value == 0.5
    assert principled.inputs["Roughness"].default_value == 0.3
```

### Testing Preset Materials
```python
def test_create_preset_material_gold(clean_scene):
    """Test gold preset material properties."""
    mat = create_preset_material("GoldMaterial", "gold")
    
    assert mat is not None
    assert mat.name == "GoldMaterial"
    
    # Gold should be metallic
    nodes = mat.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    assert principled.inputs["Metallic"].default_value > 0.9
    
    # Check color range (gold is yellow-ish)
    color = principled.inputs["Base Color"].default_value
    assert color[0] > 0.8  # Red high
    assert color[1] > 0.6  # Green medium
    assert color[2] < 0.3  # Blue low
```

### Testing Material Assignment
```python
def test_assign_material(clean_scene):
    """Test material assignment to object."""
    widget = BpyWidget()
    cube = widget.create_test_cube(location=(0, 0, 0))
    mat = widget.create_material("TestMat", base_color=(1.0, 0.0, 0.0, 1.0))
    
    widget.assign_material(cube, mat)
    
    assert cube.active_material is not None
    assert cube.active_material.name == "TestMat"
```

### Testing Rendering
```python
def test_render_basic(clean_scene):
    """Test basic rendering."""
    widget = BpyWidget(width=256, height=256)
    
    # Setup simple scene
    widget.create_test_cube()
    widget.setup_lighting()
    
    # Render
    widget.render()
    
    # Check image data is generated
    assert widget.image_data != ""
    assert len(widget.image_data) > 100  # Base64 encoded image
```

### Testing with CI Environment
```python
import os

def test_render_performance(clean_scene):
    """Test rendering performance."""
    widget = BpyWidget(width=512, height=512)
    
    # Use appropriate renderer for environment
    if os.getenv("CI"):
        # CI: Use Cycles CPU (reliable)
        widget.set_render_engine("CYCLES")
        widget.scene.cycles.device = "CPU"
        widget.scene.cycles.samples = 8  # Lower samples for speed
    else:
        # Local: Use EEVEE Next with Vulkan
        widget.set_render_engine("BLENDER_EEVEE_NEXT")
        widget.set_gpu_backend("VULKAN")
    
    # Test rendering
    start_time = time.time()
    widget.render()
    elapsed = time.time() - start_time
    
    assert widget.image_data != ""
    # CI is slower, be lenient with timing
    max_time = 10.0 if os.getenv("CI") else 2.0
    assert elapsed < max_time
```

### Testing File Import
```python
import tempfile
import csv

def test_import_csv_data(clean_scene, tmp_path):
    """Test CSV data import."""
    # Create temporary CSV file
    csv_file = tmp_path / "test_data.csv"
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["x", "y", "z"])
        writer.writerow([0.0, 0.0, 0.0])
        writer.writerow([1.0, 1.0, 1.0])
        writer.writerow([2.0, 2.0, 2.0])
    
    widget = BpyWidget()
    objects = widget.import_data(str(csv_file), as_type="points")
    
    assert len(objects) == 3
    assert all(obj.type == 'MESH' for obj in objects)
```

## Mocking and Patching

### Mocking External Dependencies
```python
from unittest.mock import patch, MagicMock

@patch("bpy_widget.core.io_handlers.pl.read_csv")
def test_import_csv_with_mock(mock_read_csv, clean_scene):
    """Test CSV import with mocked polars."""
    # Setup mock data
    mock_df = MagicMock()
    mock_df.iter_rows.return_value = [
        (0.0, 0.0, 0.0),
        (1.0, 1.0, 1.0)
    ]
    mock_read_csv.return_value = mock_df
    
    widget = BpyWidget()
    objects = widget.import_data("test.csv", as_type="points")
    
    assert mock_read_csv.called
    assert len(objects) == 2
```

### Mocking File Operations
```python
@patch("builtins.open", create=True)
@patch("os.path.exists")
def test_render_to_file(mock_exists, mock_open, clean_scene):
    """Test render with mocked file operations."""
    mock_exists.return_value = True
    mock_open.return_value.__enter__.return_value.read.return_value = b"fake_png_data"
    
    widget = BpyWidget()
    widget.render()
    
    assert widget.image_data != ""
```

## Assertions

### Be Specific
```python
# ✅ Good - Specific assertions
assert mat.name == "TestMaterial"
assert mat.use_nodes is True
assert len(widget.scene.objects) == 1

# ❌ Bad - Vague assertions
assert mat
assert widget.scene.objects
```

### Check Multiple Properties
```python
def test_material_properties(clean_scene):
    """Test all material properties are set correctly."""
    mat = create_material(
        "Test",
        base_color=(0.8, 0.2, 0.1, 1.0),
        metallic=0.7,
        roughness=0.3,
        emission_strength=0.5
    )
    
    principled = mat.node_tree.nodes.get("Principled BSDF")
    
    # Check all properties
    assert principled.inputs["Metallic"].default_value == 0.7
    assert principled.inputs["Roughness"].default_value == 0.3
    assert principled.inputs["Emission Strength"].default_value == 0.5
    
    # Check color
    color = principled.inputs["Base Color"].default_value
    assert abs(color[0] - 0.8) < 0.01
    assert abs(color[1] - 0.2) < 0.01
    assert abs(color[2] - 0.1) < 0.01
```

## Error Testing

### Testing Exceptions
```python
def test_invalid_preset_raises_error(clean_scene):
    """Test that invalid preset raises ValueError."""
    with pytest.raises(ValueError, match="not found"):
        create_preset_material("Test", "invalid_preset")

def test_invalid_color_range_raises_error(clean_scene):
    """Test that invalid color range raises ValueError."""
    with pytest.raises(ValueError, match="range"):
        create_material("Test", base_color=(255, 128, 0))  # Wrong range
```

### Testing Error Messages
```python
def test_helpful_error_message(clean_scene):
    """Test that error messages are helpful."""
    try:
        create_preset_material("Test", "nonexistent")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        # Check error message includes valid options
        assert "Valid presets:" in str(e)
        assert "gold" in str(e)
        assert "silver" in str(e)
```

## Performance Testing

### Timing Tests
```python
import time

def test_render_performance(clean_scene):
    """Test rendering completes in reasonable time."""
    widget = BpyWidget(width=512, height=512)
    widget.setup_lighting()
    widget.create_test_cube()
    
    start = time.time()
    widget.render()
    elapsed = time.time() - start
    
    # Should render in under 2 seconds locally
    if not os.getenv("CI"):
        assert elapsed < 2.0
```

### Memory Tests
```python
def test_no_memory_leak(clean_scene):
    """Test that repeated operations don't leak memory."""
    widget = BpyWidget()
    
    initial_count = len(bpy.data.materials)
    
    # Create and delete materials multiple times
    for i in range(100):
        mat = widget.create_material(f"Test{i}")
        bpy.data.materials.remove(mat)
    
    final_count = len(bpy.data.materials)
    assert final_count == initial_count
```

## Test Organization

### Group Related Tests
```python
class TestMaterialCreation:
    """Tests for material creation functions."""
    
    def test_basic_material(self, clean_scene):
        """Test basic material."""
        pass
    
    def test_material_with_emission(self, clean_scene):
        """Test material with emission."""
        pass

class TestMaterialPresets:
    """Tests for material presets."""
    
    def test_gold_preset(self, clean_scene):
        """Test gold preset."""
        pass
    
    def test_glass_preset(self, clean_scene):
        """Test glass preset."""
        pass
```

## Parametrized Tests

### Testing Multiple Inputs
```python
@pytest.mark.parametrize("preset,expected_metallic", [
    ("gold", 1.0),
    ("silver", 1.0),
    ("copper", 1.0),
    ("glass", 0.0),
    ("rubber", 0.0),
])
def test_preset_metallic_values(clean_scene, preset, expected_metallic):
    """Test metallic values for different presets."""
    mat = create_preset_material("Test", preset)
    principled = mat.node_tree.nodes.get("Principled BSDF")
    
    actual = principled.inputs["Metallic"].default_value
    assert abs(actual - expected_metallic) < 0.1
```

## Skip Conditions

### Skip Tests Based on Environment
```python
@pytest.mark.skipif(
    os.getenv("CI") == "true",
    reason="GPU-specific test, skip in CI"
)
def test_vulkan_backend(clean_scene):
    """Test Vulkan backend (requires GPU)."""
    widget = BpyWidget()
    widget.set_gpu_backend("VULKAN")
    assert widget.get_gpu_backend() == "VULKAN"
```

## Test Documentation

### Clear Docstrings
```python
def test_create_material_with_custom_color(clean_scene):
    """Test creating material with custom RGBA color.
    
    Verifies that:
    1. Material is created successfully
    2. Color values are set correctly (0.0-1.0 range)
    3. RGBA components match input
    """
    mat = create_material(
        "CustomColor",
        base_color=(0.8, 0.4, 0.2, 0.9)
    )
    
    # Test implementation...
```

## Common Issues

### Scene Not Cleaned
```python
# ❌ Wrong - No clean_scene fixture
def test_create_cube():
    cube = widget.create_test_cube()
    # May fail if scene has existing objects

# ✅ Correct - Use clean_scene fixture
def test_create_cube(clean_scene):
    cube = widget.create_test_cube()
    assert len(widget.scene.objects) == 1  # Exact count
```

### Floating Point Comparisons
```python
# ❌ Wrong - Direct comparison
assert value == 0.7

# ✅ Correct - Use tolerance
assert abs(value - 0.7) < 0.01
# or use pytest.approx
assert value == pytest.approx(0.7, abs=0.01)
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Blender Python API Testing](https://docs.blender.org/api/current/info_testing.html)
- [pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [pytest Parametrize](https://docs.pytest.org/en/stable/parametrize.html)
