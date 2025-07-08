# BPY Widget Frontend

This is the frontend build setup for the BPY Widget using Vite and Bun.

## Structure

```
frontend/
├── src/
│   ├── widget.js          # Main widget module
│   ├── widget.css         # Widget styles
│   ├── controls/          # Camera control modules
│   │   └── camera-controls.js
│   └── rendering/         # Rendering modules
│       └── canvas-renderer.js
├── vite.config.js         # Vite configuration
└── package.json           # Build scripts
```

## Development

```bash
# Install dependencies (if needed)
bun install

# Start development server
bun run dev

# Build for production
bun run build

# Watch mode (auto-rebuild on changes)
bun run watch
```

## Build Output

The build process creates:
- `../src/bpy_widget/static/widget.js` - Bundled JavaScript module
- `../src/bpy_widget/static/widget.css` - Compiled CSS

These files are automatically loaded by the Python widget.

## How it Works

1. **Vite** bundles all JavaScript modules into a single ES module
2. **CSS** is extracted to a separate file
3. **Output** goes directly to the Python package's static directory
4. **Anywidget** loads these files at runtime

## Notes

- All imports are bundled inline for anywidget compatibility
- The widget exports a default object with a `render` function
- CSS is automatically extracted and minified
- Source maps are disabled for cleaner output