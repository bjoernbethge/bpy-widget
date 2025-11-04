/**
 * Camera Controls - OO pattern for mouse/touch camera interaction
 */
export class CameraControls {
    constructor(canvas, model) {
        this.canvas = canvas;
        this.model = model;
        
        // State
        this.isDragging = false;
        this.isPanning = false;
        this.lastX = 0;
        this.lastY = 0;
        this.lastUpdateTime = 0;
        
        // Settings
        this.UPDATE_INTERVAL = 33; // ~30 FPS
        this.rotationSensitivity = 0.01;
        this.panSensitivity = 0.01; // Pan is typically slower than rotation
        
        this.bindEvents();
    }
    
    bindEvents() {
        this.bindMouseEvents();
        this.bindTouchEvents();
        this.bindWheelEvents();
        this.bindContextMenu();
    }
    
    bindMouseEvents() {
        // Canvas events
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        this.canvas.addEventListener('mouseleave', (e) => this.handleMouseLeave(e));
        // Middle mouse button for panning
        this.canvas.addEventListener('auxclick', (e) => this.handleAuxClick(e));
        
        // Global events to catch mouseup outside canvas
        // Use capture phase to ensure we catch it before other handlers
        // Store references for cleanup
        this._globalMouseUpHandler = (e) => this.handleMouseUp(e);
        this._globalBlurHandler = () => this.cancelDrag();
        window.addEventListener('mouseup', this._globalMouseUpHandler, true);
        window.addEventListener('blur', this._globalBlurHandler, true);
    }
    
    bindTouchEvents() {
        this.canvas.addEventListener('touchstart', (e) => this.handleTouchStart(e));
        this.canvas.addEventListener('touchmove', (e) => this.handleTouchMove(e));
        this.canvas.addEventListener('touchend', (e) => this.handleTouchEnd(e));
    }
    
    bindWheelEvents() {
        this.canvas.addEventListener('wheel', (e) => this.handleWheel(e));
    }
    
    bindContextMenu() {
        this.canvas.addEventListener('contextmenu', (e) => e.preventDefault());
    }
    
    handleMouseDown(e) {
        const rect = this.canvas.getBoundingClientRect();
        this.lastX = e.clientX - rect.left;
        this.lastY = e.clientY - rect.top;
        
        // Right-click or middle-click = pan, left-click = rotate
        if (e.button === 1 || e.button === 2) { // Middle (1) or Right (2) mouse button
            this.isPanning = true;
            this.canvas.style.cursor = 'move';
        } else if (e.button === 0) { // Left mouse button
            this.isDragging = true;
            this.canvas.style.cursor = 'grabbing';
        }
        
        e.preventDefault();
    }
    
    handleMouseMove(e) {
        // Only process if we're actually dragging/panning
        if (!this.isDragging && !this.isPanning) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const currentX = e.clientX - rect.left;
        const currentY = e.clientY - rect.top;
        
        // Check if mouse is still over canvas
        const isOverCanvas = (
            currentX >= 0 && currentX <= rect.width &&
            currentY >= 0 && currentY <= rect.height
        );
        
        // If mouse left canvas, cancel drag
        if (!isOverCanvas) {
            this.cancelDrag();
            return;
        }
        
        if (this.isPanning) {
            this.updatePan(currentX, currentY);
        } else if (this.isDragging) {
            this.updateCamera(currentX, currentY);
        }
        
        e.preventDefault();
    }
    
    handleMouseUp(e) {
        // Only process if we're actually dragging/panning
        if (!this.isDragging && !this.isPanning) return;
        
        // Cancel drag/pan state
        this.cancelDrag();
    }
    
    cancelDrag() {
        if (this.isDragging || this.isPanning) {
            this.isDragging = false;
            this.isPanning = false;
            this.canvas.style.cursor = 'grab';
            // Force immediate save and ensure final render
            this.forceSave();
            // Trigger a final update to ensure last state is rendered
            // The backend _update() will handle debouncing
            setTimeout(() => this.forceSave(), 50); // Small delay to ensure backend processed
        }
    }
    
    handleAuxClick(e) {
        // Middle mouse button (auxclick event)
        if (e.button === 1) {
            this.isPanning = true;
            const rect = this.canvas.getBoundingClientRect();
            this.lastX = e.clientX - rect.left;
            this.lastY = e.clientY - rect.top;
            this.canvas.style.cursor = 'move';
            e.preventDefault();
        }
    }
    
    handleMouseLeave(e) {
        // Cancel drag when mouse leaves canvas
        this.cancelDrag();
    }
    
    handleTouchStart(e) {
        if (e.touches.length === 1) {
            this.isDragging = true;
            const rect = this.canvas.getBoundingClientRect();
            const touch = e.touches[0];
            this.lastX = touch.clientX - rect.left;
            this.lastY = touch.clientY - rect.top;
            e.preventDefault();
        }
    }
    
    handleTouchMove(e) {
        if (!this.isDragging || e.touches.length !== 1) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const touch = e.touches[0];
        const currentX = touch.clientX - rect.left;
        const currentY = touch.clientY - rect.top;
        
        this.updateCamera(currentX, currentY);
        e.preventDefault();
    }
    
    handleTouchEnd(e) {
        if (this.isDragging) {
            this.isDragging = false;
            // Force immediate save and ensure final render
            this.forceSave();
            // Trigger a final update to ensure last state is rendered
            setTimeout(() => this.forceSave(), 50); // Small delay to ensure backend processed
        }
    }
    
    handleWheel(e) {
        e.preventDefault();
        
        const delta = e.deltaY > 0 ? 1.1 : 0.9;
        const newDistance = Math.max(2.0, Math.min(20.0, 
            this.model.get('camera_distance') * delta));
        
        this.model.set('camera_distance', newDistance);
        this.forceSave();
    }
    
    updateCamera(currentX, currentY) {
        const deltaX = currentX - this.lastX;
        const deltaY = currentY - this.lastY;
        
        if (deltaX === 0 && deltaY === 0) return;
        
        // Update camera angles (rotation)
        const newAngleZ = this.model.get('camera_angle_z') - deltaX * this.rotationSensitivity;
        const newAngleX = Math.max(-1.5, Math.min(1.5, 
            this.model.get('camera_angle_x') + deltaY * this.rotationSensitivity));
        
        this.model.set('camera_angle_z', newAngleZ);
        this.model.set('camera_angle_x', newAngleX);
        
        this.lastX = currentX;
        this.lastY = currentY;
        
        // Throttled save
        this.throttledSave();
    }
    
    updatePan(currentX, currentY) {
        const deltaX = currentX - this.lastX;
        const deltaY = currentY - this.lastY;
        
        if (deltaX === 0 && deltaY === 0) return;
        
        // Get current target or default
        const currentTarget = this.model.get('camera_target') || [0, 0, 1];
        const distance = this.model.get('camera_distance') || 10.0;
        
        // Pan is relative to camera view direction
        // Convert screen delta to world space movement
        // For simplicity, pan in camera-relative XY plane
        const panScale = distance * this.panSensitivity;
        const newTarget = [
            currentTarget[0] - deltaX * panScale,
            currentTarget[1] + deltaY * panScale, // Y inverted for intuitive panning
            currentTarget[2]
        ];
        
        this.model.set('camera_target', newTarget);
        
        this.lastX = currentX;
        this.lastY = currentY;
        
        // Throttled save
        this.throttledSave();
    }
    
    throttledSave() {
        const now = Date.now();
        if (now - this.lastUpdateTime >= this.UPDATE_INTERVAL) {
            this.model.save_changes();
            this.lastUpdateTime = now;
        }
    }
    
    forceSave() {
        this.model.save_changes();
    }
    
    destroy() {
        // Remove global event listeners
        if (this._globalMouseUpHandler) {
            window.removeEventListener('mouseup', this._globalMouseUpHandler, true);
        }
        if (this._globalBlurHandler) {
            window.removeEventListener('blur', this._globalBlurHandler, true);
        }
    }
}
