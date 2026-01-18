# GitHub Copilot Instructions for bpy-widget

## Project Overview

**bpy-widget** is an interactive Blender 3D viewport widget for Jupyter notebooks with real-time rendering powered by Blender 4.5+. The project combines Python backend (using Blender's bpy API) with a JavaScript/Vite frontend for interactive 3D visualization in notebooks.

## Core Commands

### Build & Development
```bash
# Install dependencies
uv sync --dev

# Build Python package
uv build

# Build frontend assets
cd frontend && npm install && npm run build

# Frontend development with Hot Module Reload (HMR)
cd frontend && npm run dev
export ANYWIDGET_HMR=1
export PYTHONPATH="$(pwd)/src"
uv run marimo edit examples/basic_usage.py
```

### Testing
```bash
# Run all tests
uv run pytest -v

# Run specific test file
uv run pytest tests/test_materials.py -v

# Run tests with coverage
uv run pytest --cov=src/bpy_widget --cov-report=html
```

### Linting & Type Checking
```bash
# Run ruff linter
uv run ruff check .

# Run ruff formatter
uv run ruff format .

# Run mypy type checker
uv run mypy src/bpy_widget
```

### Running Examples
```bash
# Run example notebooks (set PYTHONPATH for local development)
export PYTHONPATH="$(pwd)/src"
uv run marimo edit examples/basic_usage.py
```

## Project Structure

```
bpy-widget/
├── src/bpy_widget/         # Main Python package
│   ├── core/               # Core Blender functionality
│   │   ├── materials.py    # Material creation and management
│   │   ├── rendering.py    # Rendering and viewport logic
│   │   ├── scene.py        # Scene setup and management
│   │   └── io_handlers.py  # Import/export 3D formats
│   ├── widget.py           # Main BpyWidget class
│   └── static/             # Built frontend assets (generated)
├── frontend/               # JavaScript/Vite frontend
│   ├── src/
│   │   ├── controls/       # Camera and viewport controls
│   │   ├── rendering/      # Canvas rendering logic
│   │   ├── ui/             # UI components (stats overlay, etc.)
│   │   └── widget.js       # Main widget entry point
│   └── vite.config.js      # Vite build configuration
├── tests/                  # Pytest test suite
├── examples/               # Marimo/Jupyter example notebooks
├── pyproject.toml          # Python project configuration
└── .github/                # GitHub workflows and configuration
```

## Python Coding Conventions

### Style Guidelines
- **Python version**: 3.11+ (required by Blender 4.5)
- **Formatting**: Use `ruff format` for code formatting
- **Linting**: Use `ruff check` for linting
- **Type hints**: Always use type hints for function signatures
- **Docstrings**: Use clear docstrings for public APIs (Google style preferred)

### Blender API Usage
- Access Blender context through `widget.context`, `widget.scene`, `widget.data`
- Use convenience properties: `widget.objects`, `widget.camera`, `widget.active_object`
- Handle headless environments safely (no direct `bpy.context` access)
- Always clean up resources in tests using `clean_scene` fixture

### Color Conventions
- Always use RGB/RGBA tuples with 0.0-1.0 range: `(1.0, 0.5, 0.0)` or `(1.0, 0.5, 0.0, 1.0)`
- Never use 0-255 integer values for colors
- Examples: `base_color=(0.8, 0.2, 0.2, 1.0)`, `background=(0.05, 0.05, 0.1)`

### Error Handling
- Use informative error messages that help users troubleshoot
- Log important events using `loguru`
- Handle missing dependencies gracefully (e.g., Vulkan support)

## Frontend Coding Conventions

### Style Guidelines
- **JavaScript**: Use modern ES6+ syntax
- **Module system**: ES modules (import/export)
- **Build tool**: Vite for bundling and HMR
- **No TypeScript**: Project uses plain JavaScript

### Structure
- Keep components modular in separate files
- Camera controls in `controls/camera-controls.js`
- Rendering logic in `rendering/canvas-renderer.js`
- UI components in `ui/`
- Main entry point is `widget.js`

### Communication
- Use anywidget's model system for Python ↔ JavaScript communication
- Handle model changes reactively
- Debounce expensive operations (camera updates, rendering)

## Testing Guidelines

### Test Structure
- Use pytest for all tests
- Each module has corresponding test file: `test_<module>.py`
- Use `clean_scene` fixture for Blender scene cleanup
- Tests run in headless mode with Xvfb in CI

### Test Naming
- Test functions: `test_<functionality>_<scenario>`
- Examples: `test_create_material_basic()`, `test_render_with_vulkan()`

### Assertions
- Be specific with assertions
- Check both existence and properties
- Example: `assert mat.name == "TestMaterial"` not just `assert mat`

### CI Environment
- Tests run with `LIBGL_ALWAYS_SOFTWARE=1` for software rendering
- Use Cycles CPU renderer when `CI=true` environment variable is set
- Avoid GPU-specific features in CI tests

## Git Workflow

### Branches
- `main`: Stable releases
- `dev`: Development branch
- Feature branches: `feature/<name>`
- Bug fixes: `fix/<name>`

### Commit Messages
- Use clear, descriptive commit messages
- Start with verb in imperative mood: "Add", "Fix", "Update", "Remove"
- Examples: "Add Vulkan backend support", "Fix material color range validation"

## Boundaries & Protected Files

### Never Modify
- `.python-version` - Python version pinned to 3.11
- `uv.lock` - Dependency lock file (auto-managed by uv)
- `datafiles.zip` - Blender datafiles archive
- `src/bpy_widget/static/*` - Generated frontend assets (built from frontend/)
- `.github/workflows/*` - CI/CD workflows (without review)

### Never Commit
- Secrets or API keys
- Virtual environment directories (`.venv/`, `venv/`)
- Build artifacts (`dist/`, `build/`)
- Node modules (`node_modules/`)
- Python cache (`__pycache__/`, `*.pyc`)
- Temporary files in `/tmp`

### Careful With
- `pyproject.toml` - Dependencies and project metadata
- `frontend/package.json` - Frontend dependencies
- `frontend/vite.config.js` - Build configuration

## Dependencies

### Adding Python Dependencies
- Use `uv add <package>` for runtime dependencies
- Use `uv add --dev <package>` for dev dependencies
- Keep minimum Python version at 3.11
- Blender version pinned to 4.5.4 (do not change)

### Adding Frontend Dependencies
- Navigate to `frontend/` directory first
- Use `npm install <package>` for dependencies
- Keep dependencies minimal (currently only Vite & TypeScript types)

## Performance Considerations

### Rendering
- Vulkan backend provides 10-15% performance improvement over OpenGL
- EEVEE Next is faster for interactive work (~200ms at 512x512)
- Cycles provides higher quality but slower rendering
- Use appropriate render engine based on use case

### Frontend
- Debounce camera updates to avoid excessive re-renders
- Use requestAnimationFrame for smooth animations
- Minimize data transfer between Python and JavaScript

## Common Patterns

### Creating Blender Objects
```python
# Always use widget methods, not direct bpy calls
cube = widget.create_test_cube(location=(0, 0, 0))
material = widget.create_material("MyMaterial", base_color=(1.0, 0.5, 0.0, 1.0))
widget.assign_material(cube, material)
```

### Accessing Blender Data
```python
# Use convenience properties
scene = widget.scene
objects = widget.objects
camera = widget.camera
active = widget.active_object

# Not direct bpy access
# ❌ bpy.context.scene
# ✅ widget.scene
```

### Testing with Blender
```python
def test_my_feature(clean_scene):
    """Test description"""
    # clean_scene fixture ensures clean Blender state
    widget = BpyWidget()
    result = widget.some_method()
    assert result is not None
```

## Documentation

### When to Update Docs
- Always update README.md for new public API methods
- Add examples to `examples/` for significant features
- Document breaking changes clearly
- Keep API Reference section in README current

### Documentation Style
- Use clear, concise language
- Provide code examples for all features
- Include expected output or behavior
- Mention prerequisites (GPU drivers, Python version, etc.)

## Security Considerations

- Never commit `.env` files or environment variables with secrets
- Validate user input for file paths (avoid path traversal)
- Sanitize data import from external files (CSV, Parquet)
- Be cautious with `eval()` or `exec()` - avoid if possible

## Additional Resources

- [Blender Python API Docs](https://docs.blender.org/api/current/)
- [anywidget Documentation](https://anywidget.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [uv Documentation](https://docs.astral.sh/uv/)
