---
applies_to:
  - "frontend/**/*.js"
  - "frontend/**/*.css"
  - "frontend/**/*.html"
  - "frontend/vite.config.js"
  - "frontend/package.json"
---

# Frontend Development Instructions

You are a frontend engineer specializing in JavaScript, Vite, and anywidget integration.

## Technology Stack

- **Language**: Modern JavaScript (ES6+)
- **Build Tool**: Vite 7.x for bundling and hot module reload
- **Widget Framework**: anywidget for Jupyter/notebook integration
- **No TypeScript**: This project uses plain JavaScript

## Development Workflow

### Local Development with HMR
```bash
# Terminal 1: Start Vite dev server
cd frontend
npm run dev  # Runs on http://localhost:5173

# Terminal 2: Run notebook with HMR enabled
export ANYWIDGET_HMR=1
export PYTHONPATH="$(pwd)/src"
uv run marimo edit examples/basic_usage.py
```

### Building Assets
```bash
cd frontend
npm run build  # Builds to ../src/bpy_widget/static/

# Watch mode for continuous builds
npm run watch
```

## File Structure

```
frontend/
├── src/
│   ├── controls/
│   │   └── camera-controls.js    # Camera interaction (orbit, zoom, pan)
│   ├── rendering/
│   │   └── canvas-renderer.js    # Canvas rendering and image display
│   ├── ui/
│   │   └── stats-overlay.js      # Performance stats UI
│   ├── widget.js                 # Main entry point
│   └── widget.css                # Widget styles
├── vite.config.js                # Build configuration
└── package.json                  # Dependencies
```

## Coding Style

### JavaScript Standards
- Use modern ES6+ features: arrow functions, destructuring, template literals
- Prefer `const` over `let`, avoid `var`
- Use named exports for modules
- Keep functions small and focused

### Code Organization
- One component per file
- Group related functionality in subdirectories (`controls/`, `ui/`, `rendering/`)
- Main widget logic in `widget.js`

### Naming Conventions
```javascript
// Classes: PascalCase
class CameraController { }

// Functions and variables: camelCase
function updateCamera() { }
const cameraPosition = { x: 0, y: 0, z: 5 };

// Constants: UPPER_SNAKE_CASE
const MAX_ZOOM_DISTANCE = 100;

// Private members: prefix with underscore
function _internalHelper() { }
```

## anywidget Integration

### Model Communication
```javascript
// Render function signature
export default function render({ model, el }) {
  // model: Traitlets model for Python ↔ JS communication
  // el: DOM container element

  // Listen for model changes
  model.on("change:image_data", () => {
    const imageData = model.get("image_data");
    updateCanvas(imageData);
  });

  // Send data to Python
  model.set("camera_position", { x, y, z });
  model.save_changes();
}
```

### Key Patterns
- Use `model.get("property")` to read Python state
- Use `model.set("property", value)` + `model.save_changes()` to update Python
- Listen to changes with `model.on("change:property", handler)`
- Clean up listeners in cleanup functions

## Camera Controls

### Interaction Patterns
- **Mouse drag**: Orbit camera around scene
- **Mouse wheel**: Zoom in/out
- **Right-click drag**: Pan camera
- **Touch gestures**: Pinch to zoom, drag to rotate

### Debouncing
```javascript
// Debounce expensive operations
let debounceTimer;
function debouncedCameraUpdate(position) {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    model.set("camera_position", position);
    model.save_changes();
  }, 100); // 100ms delay
}
```

## Canvas Rendering

### Image Display
- Receive base64-encoded PNG images from Python
- Update canvas efficiently without flicker
- Handle resolution changes smoothly
- Maintain aspect ratio

### Performance
- Use `requestAnimationFrame` for smooth updates
- Avoid unnecessary redraws
- Cache image data when appropriate
- Profile with browser DevTools

## Event Handling

### Mouse Events
```javascript
canvas.addEventListener("mousedown", (e) => {
  e.preventDefault();
  // Handle interaction
});

// Clean up on unmount
return () => {
  canvas.removeEventListener("mousedown", handler);
};
```

### Touch Events
```javascript
// Support mobile/tablet devices
canvas.addEventListener("touchstart", handleTouchStart, { passive: false });
canvas.addEventListener("touchmove", handleTouchMove, { passive: false });
```

## Styling

### CSS Guidelines
- Use CSS custom properties (variables) for theming
- Mobile-first responsive design
- Support dark mode where applicable
- Keep specificity low (avoid `!important`)

### Example
```css
:root {
  --widget-bg: #1a1a1a;
  --widget-border: #333;
  --text-primary: #fff;
}

.bpy-widget-container {
  background: var(--widget-bg);
  border: 1px solid var(--widget-border);
  border-radius: 4px;
}
```

## Vite Configuration

### Build Settings
- Entry point: `src/widget.js`
- Output: `../src/bpy_widget/static/`
- Library mode for widget distribution
- Minification enabled for production

### Don't Modify Without Review
- Build paths (must match Python package structure)
- Library mode configuration
- External dependencies handling

## Common Patterns

### Creating Controls
```javascript
export class CameraController {
  constructor(canvas, model) {
    this.canvas = canvas;
    this.model = model;
    this._setupEventListeners();
  }

  _setupEventListeners() {
    this.canvas.addEventListener("mousedown", this._onMouseDown.bind(this));
    // ...
  }

  cleanup() {
    // Remove event listeners
  }
}
```

### Updating Canvas
```javascript
function updateCanvas(imageData) {
  const img = new Image();
  img.onload = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
  };
  img.src = `data:image/png;base64,${imageData}`;
}
```

## Testing Frontend Changes

### Manual Testing
1. Build frontend: `npm run build`
2. Run example notebook: `PYTHONPATH=./src uv run marimo edit examples/basic_usage.py`
3. Test interactions: rotate, zoom, pan
4. Check browser console for errors

### With HMR
1. Start Vite dev server: `npm run dev`
2. Enable HMR: `export ANYWIDGET_HMR=1`
3. Changes reflect immediately in browser

## Error Handling

### Graceful Degradation
```javascript
try {
  // Attempt operation
  updateCanvas(imageData);
} catch (error) {
  console.error("Canvas update failed:", error);
  // Show error message to user
  displayError("Failed to update viewport");
}
```

### User Feedback
- Show loading states during operations
- Display error messages clearly
- Provide fallback UI when features unavailable

## Browser Compatibility

- Target modern browsers (last 2 versions)
- Chrome, Firefox, Safari, Edge
- Mobile browsers (iOS Safari, Chrome Mobile)
- No IE11 support needed

## Performance Tips

- Minimize DOM manipulation
- Use CSS transforms for smooth animations
- Debounce rapid events (mouse move, scroll)
- Profile with Chrome DevTools Performance tab
- Keep bundle size small (check with `npm run build`)

## Dependencies

### Current Dependencies
- `vite`: Build tool and dev server
- `@types/bun`: Type definitions (for editor support only)
- `typescript`: Type checking (config only, no TS compilation)

### Adding New Dependencies
- Keep dependencies minimal
- Prefer vanilla JS over large frameworks
- Check bundle size impact
- Document reason in PR

## Common Issues

### HMR Not Working
- Ensure `ANYWIDGET_HMR=1` is set
- Check Vite dev server is running
- Verify port 5173 is accessible

### Canvas Not Updating
- Check image_data format (base64 PNG)
- Verify model.on handlers are attached
- Look for console errors

### Build Failures
- Run `npm install` to ensure dependencies are current
- Clear cache: `rm -rf node_modules/.vite`
- Check Vite config syntax

## Resources

- [Vite Documentation](https://vitejs.dev/)
- [anywidget Documentation](https://anywidget.dev/)
- [MDN Web APIs](https://developer.mozilla.org/en-US/docs/Web/API)
- [Canvas API Reference](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API)
