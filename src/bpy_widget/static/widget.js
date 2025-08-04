class CameraController {
  constructor(canvas, model) {
    this.canvas = canvas;
    this.model = model;
    this.isDragging = false;
    this.lastX = 0;
    this.lastY = 0;
    this.lastUpdateTime = 0;
    this.UPDATE_INTERVAL = 33;
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
    this.canvas.addEventListener("mousedown", (e) => this.handleMouseDown(e));
    this.canvas.addEventListener("mousemove", (e) => this.handleMouseMove(e));
    this.canvas.addEventListener("mouseup", (e) => this.handleMouseUp(e));
    this.canvas.addEventListener("mouseleave", (e) => this.handleMouseLeave(e));
  }
  
  bindTouchEvents() {
    this.canvas.addEventListener("touchstart", (e) => this.handleTouchStart(e));
    this.canvas.addEventListener("touchmove", (e) => this.handleTouchMove(e));
    this.canvas.addEventListener("touchend", (e) => this.handleTouchEnd(e));
  }
  
  bindWheelEvents() {
    this.canvas.addEventListener("wheel", (e) => this.handleWheel(e));
  }
  
  bindContextMenu() {
    this.canvas.addEventListener("contextmenu", (e) => e.preventDefault());
  }
  
  handleMouseDown(e) {
    this.isDragging = true;
    const rect = this.canvas.getBoundingClientRect();
    this.lastX = e.clientX - rect.left;
    this.lastY = e.clientY - rect.top;
    this.canvas.style.cursor = "grabbing";
    e.preventDefault();
  }
  
  handleMouseMove(e) {
    if (!this.isDragging) return;
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    this.updateCamera(x, y);
    e.preventDefault();
  }
  
  handleMouseUp(e) {
    if (this.isDragging) {
      this.isDragging = false;
      this.canvas.style.cursor = "grab";
      this.forceSave();
    }
  }
  
  handleMouseLeave(e) {
    if (this.isDragging) {
      this.isDragging = false;
      this.canvas.style.cursor = "grab";
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
    const x = touch.clientX - rect.left;
    const y = touch.clientY - rect.top;
    this.updateCamera(x, y);
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
    const newDistance = Math.max(2, Math.min(20, this.model.get("camera_distance") * delta));
    this.model.set("camera_distance", newDistance);
    this.forceSave();
  }
  
  updateCamera(x, y) {
    const deltaX = x - this.lastX;
    const deltaY = y - this.lastY;
    
    if (deltaX === 0 && deltaY === 0) return;
    
    const angleZ = this.model.get("camera_angle_z") - deltaX * this.sensitivity;
    const angleX = Math.max(-1.5, Math.min(1.5, 
      this.model.get("camera_angle_x") + deltaY * this.sensitivity
    ));
    
    this.model.set("camera_angle_z", angleZ);
    this.model.set("camera_angle_x", angleX);
    
    this.lastX = x;
    this.lastY = y;
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
  
  destroy() {}
}

class CanvasRenderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.frameCount = 0;
    this.fpsTime = Date.now();
    this.lastFps = 0;
    this.setupCanvas();
  }
  
  setupCanvas() {
    this.canvas.style.cursor = "grab";
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
    if (this.canvas.width !== width || this.canvas.height !== height) {
      this.canvas.width = width;
      this.canvas.height = height;
    }
    
    try {
      const binaryString = atob(imageData);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < bytes.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      const imageDataObj = new ImageData(new Uint8ClampedArray(bytes), width, height);
      this.ctx.putImageData(imageDataObj, 0, 0);
    } catch (e) {
      console.error("Failed to render image:", e);
      this.renderError(width, height, "Render Error");
    }
  }
  
  renderPlaceholder(width, height) {
    this.canvas.width = width;
    this.canvas.height = height;
    this.ctx.fillStyle = "#333";
    this.ctx.fillRect(0, 0, width, height);
    this.ctx.fillStyle = "#999";
    this.ctx.font = "14px monospace";
    this.ctx.textAlign = "center";
    this.ctx.fillText("Drag to rotate • Scroll to zoom", width / 2, height / 2);
  }
  
  renderError(width, height, message) {
    this.ctx.fillStyle = "#500";
    this.ctx.fillRect(0, 0, width, height);
    this.ctx.fillStyle = "#f99";
    this.ctx.font = "14px monospace";
    this.ctx.textAlign = "center";
    this.ctx.fillText(message, width / 2, height / 2);
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
    this.ctx = null;
  }
}

export default {
  render({ model, el }) {
    el.innerHTML = `
      <div class="bpy-widget">
        <div class="widget-controls">
          <select class="engine-select">
            <option value="BLENDER_EEVEE_NEXT">EEVEE Next</option>
            <option value="CYCLES">Cycles</option>
          </select>
          <select class="device-select">
            <option value="CPU">CPU</option>
            <option value="GPU">GPU</option>
          </select>
        </div>
        <canvas class="viewer-canvas"></canvas>
        <div class="camera-info">
          <span class="render-time">Render: --ms</span> | 
          <span class="fps">-- FPS</span> |
          <span class="engine-info">EEVEE Next</span>
        </div>
      </div>
    `;
    
    const canvas = el.querySelector(".viewer-canvas");
    const renderTime = el.querySelector(".render-time");
    const fps = el.querySelector(".fps");
    const engineSelect = el.querySelector('.engine-select');
    const deviceSelect = el.querySelector('.device-select');
    const engineInfo = el.querySelector('.engine-info');
    
    const renderer = new CanvasRenderer(canvas);
    const controller = new CameraController(canvas, model);
    
    // Set initial values
    engineSelect.value = model.get('render_engine');
    deviceSelect.value = model.get('render_device');
    engineInfo.textContent = model.get('render_engine').replace('BLENDER_', '').replace('_', ' ');
    
    // Handle engine change
    engineSelect.addEventListener('change', (e) => {
      model.set('render_engine', e.target.value);
      model.save_changes();
      engineInfo.textContent = e.target.value.replace('BLENDER_', '').replace('_', ' ');
    });
    
    // Handle device change
    deviceSelect.addEventListener('change', (e) => {
      model.set('render_device', e.target.value);
      model.save_changes();
    });
    
    function updateDisplay() {
      const imageData = model.get("image_data");
      const width = model.get("width");
      const height = model.get("height");
      renderer.updateDisplay(imageData, width, height);
      
      const currentFps = renderer.getFps();
      if (currentFps > 0) {
        fps.textContent = `${currentFps} FPS`;
      }
    }
    
    function updateStatus() {
      const status = model.get("status");
      const match = status.match(/Rendered.*\((\d+)ms\)/);
      if (match) {
        renderTime.textContent = `Render: ${match[1]}ms`;
      }
    }
    
    model.on("change:image_data", updateDisplay);
    model.on("change:width", updateDisplay);
    model.on("change:height", updateDisplay);
    model.on("change:status", updateStatus);
    
    updateDisplay();
    updateStatus();
    
    return () => {
      controller.destroy();
      renderer.destroy();
    };
  }
};
