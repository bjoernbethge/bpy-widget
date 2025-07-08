/**
 * Canvas Renderer - OO pattern for widget display rendering
 */
export class CanvasRenderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        
        // Performance tracking
        this.frameCount = 0;
        this.fpsTime = Date.now();
        this.lastFps = 0;
        
        this.setupCanvas();
    }
    
    setupCanvas() {
        this.canvas.style.cursor = 'grab';
    }
    
    updateDisplay(imageData, width, height) {
        if (imageData && width > 0 && height > 0) {
            this.renderImage(imageData, width, height);
            this.updateFps();
        } else {
            this.renderPlaceholder(width || 512, height || 512);
        }
    }
    
    renderImage(imageData, width, height) {
        // Update canvas size if needed
        if (this.canvas.width !== width || this.canvas.height !== height) {
            this.canvas.width = width;
            this.canvas.height = height;
        }
        
        try {
            // Decode base64 to binary
            const binaryString = atob(imageData);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < bytes.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            
            // Create ImageData and render
            const imgData = new ImageData(new Uint8ClampedArray(bytes), width, height);
            this.ctx.putImageData(imgData, 0, 0);
            
        } catch (error) {
            console.error('Failed to render image:', error);
            this.renderError(width, height, 'Render Error');
        }
    }
    
    renderPlaceholder(width, height) {
        this.canvas.width = width;
        this.canvas.height = height;
        
        this.ctx.fillStyle = '#333';
        this.ctx.fillRect(0, 0, width, height);
        this.ctx.fillStyle = '#999';
        this.ctx.font = '14px monospace';
        this.ctx.textAlign = 'center';
        this.ctx.fillText('Drag to rotate • Scroll to zoom', width/2, height/2);
    }
    
    renderError(width, height, message) {
        this.ctx.fillStyle = '#500';
        this.ctx.fillRect(0, 0, width, height);
        this.ctx.fillStyle = '#f99';
        this.ctx.font = '14px monospace';
        this.ctx.textAlign = 'center';
        this.ctx.fillText(message, width/2, height/2);
    }
    
    updateFps() {
        this.frameCount++;
        const now = Date.now();
        
        if (now - this.fpsTime >= 1000) {
            this.lastFps = this.frameCount;
            this.frameCount = 0;
            this.fpsTime = now;
        }
    }
    
    getFps() {
        return this.lastFps;
    }
    
    setCursor(cursor) {
        this.canvas.style.cursor = cursor;
    }
    
    destroy() {
        // Cleanup if needed
        this.ctx = null;
    }
}
