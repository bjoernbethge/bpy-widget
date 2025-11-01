// Import CSS for bundling
import './widget.css';

// NOTE: This module requires an import map for correct module resolution in the browser.
// Example usage in your HTML:

import { CameraControls } from './controls/camera-controls.js';
import { CanvasRenderer } from './rendering/canvas-renderer.js';
import { StatsOverlay } from './ui/stats-overlay.js';

export default {
    render({ model, el }) {
        // Create widget structure
        el.innerHTML = `
            <div class="bpy-widget">
                <canvas class="viewer-canvas"></canvas>
            </div>
        `;
        
        // Get widget container and canvas
        const widgetContainer = el.querySelector('.bpy-widget');
        const canvas = el.querySelector('.viewer-canvas');
        
        // Create components
        const renderer = new CanvasRenderer(canvas);
        const controls = new CameraControls(canvas, model);
        const statsOverlay = new StatsOverlay(widgetContainer);
        
        // Update display function
        function updateDisplay() {
            const imageData = model.get('image_data');
            const width = model.get('width');
            const height = model.get('height');
            
            renderer.updateDisplay(imageData, width, height);
            
            // Update stats overlay
            const fps = renderer.getFps();
            const status = model.get('status');
            statsOverlay.update(status, fps);
        }
        
        // Bind model events
        model.on('change:image_data', updateDisplay);
        model.on('change:width', updateDisplay);
        model.on('change:height', updateDisplay);
        model.on('change:status', updateDisplay);
        
        // Initial display
        updateDisplay();
        
        // Cleanup function (called when widget is destroyed)
        return () => {
            controls.destroy();
            renderer.destroy();
            statsOverlay.destroy();
        };
    }
};