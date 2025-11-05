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
        console.log('CanvasRenderer.updateDisplay called with:', imageData ? imageData.substring(0, 50) + '...' : 'null', width, height);
        if (imageData && width > 0 && height > 0) {
            this.renderImage(imageData, width, height);
            this.updateFps();
        } else {
            console.log('CanvasRenderer: No image data, showing placeholder');
            this.renderPlaceholder(width || 512, height || 512);
        }
    }
    
    renderImage(imageData, width, height) {
        // Update canvas internal size (actual pixel dimensions)
        // This must match the render resolution to avoid stretching
        if (this.canvas.width !== width || this.canvas.height !== height) {
            this.canvas.width = width;
            this.canvas.height = height;
        }
        
        // CSS will handle the display scaling with object-fit: contain
        // which preserves aspect ratio

        try {
            // Handle both raw base64 and data URIs
            let base64Data = imageData;
            if (imageData.startsWith('data:image')) {
                base64Data = imageData.split(',')[1];
            }

            console.log('renderImage: Decoding base64 data, length:', base64Data.length, 'expected pixels:', width * height * 4);

            // Decode base64 to binary
            const binaryString = atob(base64Data);
            console.log('renderImage: Binary string length:', binaryString.length);

            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < bytes.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }

            console.log('renderImage: Created Uint8Array with length:', bytes.length);

            // Create ImageData and render
            const imgData = new ImageData(new Uint8ClampedArray(bytes), width, height);
            this.ctx.putImageData(imgData, 0, 0);

            console.log('renderImage: Image rendered successfully!');

        } catch (error) {
            console.error('Failed to render image:', error);
            this.renderError(width, height, 'Render Error');
        }
    }
    
    renderPlaceholder(width, height) {
        if (this.canvas.width !== width || this.canvas.height !== height) {
            this.canvas.width = width;
            this.canvas.height = height;
        }
        
        this.ctx.fillStyle = '#333';
        this.ctx.fillRect(0, 0, width, height);
        this.ctx.fillStyle = '#999';
        this.ctx.font = '14px monospace';
        this.ctx.textAlign = 'center';
        this.ctx.fillText('Left-drag: rotate • Right/Middle-drag: pan • Scroll: zoom', width/2, height/2);
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
