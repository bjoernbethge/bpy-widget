/**
 * Camera Controls - OO pattern for mouse/touch camera interaction
 */
export class CameraControls {
    constructor(canvas, model) {
        this.canvas = canvas;
        this.model = model;
        
        // State
        this.isDragging = false;
        this.lastX = 0;
        this.lastY = 0;
        this.lastUpdateTime = 0;
        
        // Settings
        this.UPDATE_INTERVAL = 33; // ~30 FPS
        this.sensitivity = 0.01;
        
        this.bindEvents();
    }
    
    bindEvents() {
        this.bindMouseEvents();
        this.bindTouchEvents();
        this.bindWheelEvents();
        this.bindContextMenu();
    }
    
    bindMouseEvents() {
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        this.canvas.addEventListener('mouseleave', (e) => this.handleMouseLeave(e));
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
        this.isDragging = true;
        const rect = this.canvas.getBoundingClientRect();
        this.lastX = e.clientX - rect.left;
        this.lastY = e.clientY - rect.top;
        this.canvas.style.cursor = 'grabbing';
        e.preventDefault();
    }
    
    handleMouseMove(e) {
        if (!this.isDragging) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const currentX = e.clientX - rect.left;
        const currentY = e.clientY - rect.top;
        
        this.updateCamera(currentX, currentY);
        e.preventDefault();
    }
    
    handleMouseUp(e) {
        if (this.isDragging) {
            this.isDragging = false;
            this.canvas.style.cursor = 'grab';
            this.forceSave();
        }
    }
    
    handleMouseLeave(e) {
        if (this.isDragging) {
            this.isDragging = false;
            this.canvas.style.cursor = 'grab';
            this.forceSave();
        }
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
            this.forceSave();
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
        
        // Update camera angles
        const newAngleZ = this.model.get('camera_angle_z') - deltaX * this.sensitivity;
        const newAngleX = Math.max(-1.5, Math.min(1.5, 
            this.model.get('camera_angle_x') + deltaY * this.sensitivity));
        
        this.model.set('camera_angle_z', newAngleZ);
        this.model.set('camera_angle_x', newAngleX);
        
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
        // Remove event listeners if needed
        // (In practice, not usually necessary for widget cleanup)
    }
}
