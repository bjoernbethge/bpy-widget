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
            
            // Update widget container aspect ratio to match render resolution
            if (width && height && width > 0 && height > 0) {
                const aspectRatio = width / height;
                widgetContainer.style.aspectRatio = `${aspectRatio} / 1`;
            }
            
            // Only update display if we have valid image data
            // This prevents clearing the canvas when width/height change before new image_data arrives
            if (imageData && imageData.length > 0) {
                renderer.updateDisplay(imageData, width, height);
            } else if (width && height && width > 0 && height > 0) {
                // Only show placeholder if we have dimensions but no image data yet
                renderer.renderPlaceholder(width, height);
            }
            
            // Update stats overlay
            const fps = renderer.getFps();
            const status = model.get('status');
            statsOverlay.update(status, fps);
        }
        
        // Bind model events
        // Only update canvas when image_data changes (width/height updates are handled via aspect ratio)
        model.on('change:image_data', updateDisplay);
        
        // For width/height changes, only update aspect ratio, don't re-render canvas
        model.on('change:width', () => {
            const width = model.get('width');
            const height = model.get('height');
            if (width && height && width > 0 && height > 0) {
                const aspectRatio = width / height;
                widgetContainer.style.aspectRatio = `${aspectRatio} / 1`;
            }
            // Update stats overlay
            const fps = renderer.getFps();
            const status = model.get('status');
            statsOverlay.update(status, fps);
        });
        
        model.on('change:height', () => {
            const width = model.get('width');
            const height = model.get('height');
            if (width && height && width > 0 && height > 0) {
                const aspectRatio = width / height;
                widgetContainer.style.aspectRatio = `${aspectRatio} / 1`;
            }
            // Update stats overlay
            const fps = renderer.getFps();
            const status = model.get('status');
            statsOverlay.update(status, fps);
        });
        
        model.on('change:status', () => {
            const fps = renderer.getFps();
            const status = model.get('status');
            statsOverlay.update(status, fps);
        });
        
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