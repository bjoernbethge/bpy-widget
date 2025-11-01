/**
 * Stats Overlay Component - Shows render time and FPS (top-left corner)
 * Extracted from widget.js for better separation of concerns
 */
export class StatsOverlay {
    constructor(parentEl) {
        this.parentEl = parentEl;
        this.container = null;
        this.renderTimeEl = null;
        this.fpsEl = null;
        
        this.create();
    }
    
    create() {
        // Create stats container
        this.container = document.createElement('div');
        this.container.className = 'camera-info'; // Keep existing class name
        
        // Create render time element
        this.renderTimeEl = document.createElement('span');
        this.renderTimeEl.className = 'render-time';
        this.renderTimeEl.textContent = 'Render: --ms';
        
        // Create separator
        const separator = document.createTextNode(' | ');
        
        // Create FPS element
        this.fpsEl = document.createElement('span');
        this.fpsEl.className = 'fps';
        this.fpsEl.textContent = '-- FPS';
        
        // Assemble
        this.container.appendChild(this.renderTimeEl);
        this.container.appendChild(separator);
        this.container.appendChild(this.fpsEl);
        
        // Append to parent
        this.parentEl.appendChild(this.container);
    }
    
    updateRenderTime(status) {
        const match = status.match(/Rendered.*\((\d+)ms\)/);
        if (match) {
            this.renderTimeEl.textContent = `Render: ${match[1]}ms`;
        }
    }
    
    updateFps(fps) {
        if (fps > 0) {
            this.fpsEl.textContent = `${fps} FPS`;
        }
    }
    
    update(status, fps) {
        this.updateRenderTime(status);
        this.updateFps(fps);
    }
    
    destroy() {
        if (this.container && this.container.parentNode) {
            this.container.parentNode.removeChild(this.container);
        }
        this.container = null;
        this.renderTimeEl = null;
        this.fpsEl = null;
    }
}

