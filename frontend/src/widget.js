// Import CSS for bundling
import './widget.css';

// NOTE: This module requires an import map for correct module resolution in the browser.
// Example usage in your HTML:

import { CameraControls } from './controls/camera-controls.js';
import { CanvasRenderer } from './rendering/canvas-renderer.js';

export default {
    render({ model, el }) {
        // Create widget structure
        el.innerHTML = `
            <div class="bpy-widget">
                <canvas class="viewer-canvas"></canvas>
                <div class="camera-info">
                    <span class="render-time">Render: --ms</span> | 
                    <span class="fps">-- FPS</span>
                </div>
            </div>
        `;
        
        // Get elements
        const canvas = el.querySelector('.viewer-canvas');
        const renderTimeEl = el.querySelector('.render-time');
        const fpsEl = el.querySelector('.fps');
        
        // Create components
        const renderer = new CanvasRenderer(canvas);
        const controls = new CameraControls(canvas, model);
        
        // Update display function
        function updateDisplay() {
            const imageData = model.get('image_data');
            const width = model.get('width');
            const height = model.get('height');
            
            renderer.updateDisplay(imageData, width, height);
            
            // Update FPS display
            const fps = renderer.getFps();
            if (fps > 0) {
                fpsEl.textContent = `${fps} FPS`;
            }
        }
        
        // Update render time display
        function updateRenderTime() {
            const status = model.get('status');
            const match = status.match(/Rendered.*\((\d+)ms\)/);
            if (match) {
                renderTimeEl.textContent = `Render: ${match[1]}ms`;
            }
        }
        
        // Bind model events
        model.on('change:image_data', updateDisplay);
        model.on('change:width', updateDisplay);
        model.on('change:height', updateDisplay);
        model.on('change:status', updateRenderTime);
        
        // Initial display
        updateDisplay();
        updateRenderTime();
        
        // Cleanup function (called when widget is destroyed)
        return () => {
            controls.destroy();
            renderer.destroy();
        };
    }
};