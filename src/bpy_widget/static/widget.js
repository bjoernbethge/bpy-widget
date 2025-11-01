class g {
  constructor(t, e) {
    this.canvas = t, this.model = e, this.isDragging = !1, this.lastX = 0, this.lastY = 0, this.lastUpdateTime = 0, this.UPDATE_INTERVAL = 33, this.sensitivity = 0.01, this.bindEvents();
  }
  bindEvents() {
    this.bindMouseEvents(), this.bindTouchEvents(), this.bindWheelEvents(), this.bindContextMenu();
  }
  bindMouseEvents() {
    this.canvas.addEventListener("mousedown", (t) => this.handleMouseDown(t)), this.canvas.addEventListener("mousemove", (t) => this.handleMouseMove(t)), this.canvas.addEventListener("mouseup", (t) => this.handleMouseUp(t)), this.canvas.addEventListener("mouseleave", (t) => this.handleMouseLeave(t));
  }
  bindTouchEvents() {
    this.canvas.addEventListener("touchstart", (t) => this.handleTouchStart(t)), this.canvas.addEventListener("touchmove", (t) => this.handleTouchMove(t)), this.canvas.addEventListener("touchend", (t) => this.handleTouchEnd(t));
  }
  bindWheelEvents() {
    this.canvas.addEventListener("wheel", (t) => this.handleWheel(t));
  }
  bindContextMenu() {
    this.canvas.addEventListener("contextmenu", (t) => t.preventDefault());
  }
  handleMouseDown(t) {
    this.isDragging = !0;
    const e = this.canvas.getBoundingClientRect();
    this.lastX = t.clientX - e.left, this.lastY = t.clientY - e.top, this.canvas.style.cursor = "grabbing", t.preventDefault();
  }
  handleMouseMove(t) {
    if (!this.isDragging) return;
    const e = this.canvas.getBoundingClientRect(), s = t.clientX - e.left, n = t.clientY - e.top;
    this.updateCamera(s, n), t.preventDefault();
  }
  handleMouseUp(t) {
    this.isDragging && (this.isDragging = !1, this.canvas.style.cursor = "grab", this.forceSave());
  }
  handleMouseLeave(t) {
    this.isDragging && (this.isDragging = !1, this.canvas.style.cursor = "grab", this.forceSave());
  }
  handleTouchStart(t) {
    if (t.touches.length === 1) {
      this.isDragging = !0;
      const e = this.canvas.getBoundingClientRect(), s = t.touches[0];
      this.lastX = s.clientX - e.left, this.lastY = s.clientY - e.top, t.preventDefault();
    }
  }
  handleTouchMove(t) {
    if (!this.isDragging || t.touches.length !== 1) return;
    const e = this.canvas.getBoundingClientRect(), s = t.touches[0], n = s.clientX - e.left, i = s.clientY - e.top;
    this.updateCamera(n, i), t.preventDefault();
  }
  handleTouchEnd(t) {
    this.isDragging && (this.isDragging = !1, this.forceSave());
  }
  handleWheel(t) {
    t.preventDefault();
    const e = t.deltaY > 0 ? 1.1 : 0.9, s = Math.max(2, Math.min(
      20,
      this.model.get("camera_distance") * e
    ));
    this.model.set("camera_distance", s), this.forceSave();
  }
  updateCamera(t, e) {
    const s = t - this.lastX, n = e - this.lastY;
    if (s === 0 && n === 0) return;
    const i = this.model.get("camera_angle_z") - s * this.sensitivity, r = Math.max(-1.5, Math.min(
      1.5,
      this.model.get("camera_angle_x") + n * this.sensitivity
    ));
    this.model.set("camera_angle_z", i), this.model.set("camera_angle_x", r), this.lastX = t, this.lastY = e, this.throttledSave();
  }
  throttledSave() {
    const t = Date.now();
    t - this.lastUpdateTime >= this.UPDATE_INTERVAL && (this.model.save_changes(), this.lastUpdateTime = t);
  }
  forceSave() {
    this.model.save_changes();
  }
  destroy() {
  }
}
class v {
  constructor(t) {
    this.canvas = t, this.ctx = t.getContext("2d"), this.frameCount = 0, this.fpsTime = Date.now(), this.lastFps = 0, this.setupCanvas();
  }
  setupCanvas() {
    this.canvas.style.cursor = "grab";
  }
  updateDisplay(t, e, s) {
    t && e > 0 && s > 0 ? (this.renderImage(t, e, s), this.updateFps()) : this.renderPlaceholder(e || 512, s || 512);
  }
  renderImage(t, e, s) {
    (this.canvas.width !== e || this.canvas.height !== s) && (this.canvas.width = e, this.canvas.height = s);
    try {
      const n = atob(t), i = new Uint8Array(n.length);
      for (let c = 0; c < i.length; c++)
        i[c] = n.charCodeAt(c);
      const r = new ImageData(new Uint8ClampedArray(i), e, s);
      this.ctx.putImageData(r, 0, 0);
    } catch (n) {
      console.error("Failed to render image:", n), this.renderError(e, s, "Render Error");
    }
  }
  renderPlaceholder(t, e) {
    this.canvas.width = t, this.canvas.height = e, this.ctx.fillStyle = "#333", this.ctx.fillRect(0, 0, t, e), this.ctx.fillStyle = "#999", this.ctx.font = "14px monospace", this.ctx.textAlign = "center", this.ctx.fillText("Drag to rotate • Scroll to zoom", t / 2, e / 2);
  }
  renderError(t, e, s) {
    this.ctx.fillStyle = "#500", this.ctx.fillRect(0, 0, t, e), this.ctx.fillStyle = "#f99", this.ctx.font = "14px monospace", this.ctx.textAlign = "center", this.ctx.fillText(s, t / 2, e / 2);
  }
  updateFps() {
    this.frameCount++;
    const t = Date.now();
    t - this.fpsTime >= 1e3 && (this.lastFps = this.frameCount, this.frameCount = 0, this.fpsTime = t);
  }
  getFps() {
    return this.lastFps;
  }
  setCursor(t) {
    this.canvas.style.cursor = t;
  }
  destroy() {
    this.ctx = null;
  }
}
const f = {
  render({ model: a, el: t }) {
    t.innerHTML = `
            <div class="bpy-widget">
                <canvas class="viewer-canvas"></canvas>
                <div class="camera-info">
                    <span class="render-time">Render: --ms</span> | 
                    <span class="fps">-- FPS</span>
                </div>
            </div>
        `;
    const e = t.querySelector(".viewer-canvas"), s = t.querySelector(".render-time"), n = t.querySelector(".fps"), i = new v(e), r = new g(e, a);
    function c() {
      const l = a.get("image_data"), h = a.get("width"), u = a.get("height");
      i.updateDisplay(l, h, u);
      const d = i.getFps();
      d > 0 && (n.textContent = `${d} FPS`);
    }
    function o() {
      const h = a.get("status").match(/Rendered.*\((\d+)ms\)/);
      h && (s.textContent = `Render: ${h[1]}ms`);
    }
    return a.on("change:image_data", c), a.on("change:width", c), a.on("change:height", c), a.on("change:status", o), c(), o(), () => {
      r.destroy(), i.destroy();
    };
  }
};
export {
  f as default
};
