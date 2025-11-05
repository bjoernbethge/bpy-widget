class p {
  constructor(t, e) {
    this.canvas = t, this.model = e, this.isDragging = !1, this.isPanning = !1, this.lastX = 0, this.lastY = 0, this.lastUpdateTime = 0, this.UPDATE_INTERVAL = 33, this.rotationSensitivity = 0.01, this.panSensitivity = 0.01, this.bindEvents();
  }
  bindEvents() {
    this.bindMouseEvents(), this.bindTouchEvents(), this.bindWheelEvents(), this.bindContextMenu();
  }
  bindMouseEvents() {
    this.canvas.addEventListener("mousedown", (t) => this.handleMouseDown(t)), this.canvas.addEventListener("mousemove", (t) => this.handleMouseMove(t)), this.canvas.addEventListener("mouseup", (t) => this.handleMouseUp(t)), this.canvas.addEventListener("mouseleave", (t) => this.handleMouseLeave(t)), this.canvas.addEventListener("auxclick", (t) => this.handleAuxClick(t)), this._globalMouseUpHandler = (t) => this.handleMouseUp(t), this._globalBlurHandler = () => this.cancelDrag(), window.addEventListener("mouseup", this._globalMouseUpHandler, !0), window.addEventListener("blur", this._globalBlurHandler, !0);
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
    const e = this.canvas.getBoundingClientRect();
    this.lastX = t.clientX - e.left, this.lastY = t.clientY - e.top, t.button === 1 || t.button === 2 ? (this.isPanning = !0, this.canvas.style.cursor = "move") : t.button === 0 && (this.isDragging = !0, this.canvas.style.cursor = "grabbing"), t.preventDefault();
  }
  handleMouseMove(t) {
    if (!this.isDragging && !this.isPanning) return;
    const e = this.canvas.getBoundingClientRect(), s = t.clientX - e.left, n = t.clientY - e.top;
    if (!(s >= 0 && s <= e.width && n >= 0 && n <= e.height)) {
      this.cancelDrag();
      return;
    }
    this.isPanning ? this.updatePan(s, n) : this.isDragging && this.updateCamera(s, n), t.preventDefault();
  }
  handleMouseUp(t) {
    !this.isDragging && !this.isPanning || this.cancelDrag();
  }
  cancelDrag() {
    (this.isDragging || this.isPanning) && (this.isDragging = !1, this.isPanning = !1, this.canvas.style.cursor = "grab", this.forceSave(), setTimeout(() => this.forceSave(), 50));
  }
  handleAuxClick(t) {
    if (t.button === 1) {
      this.isPanning = !0;
      const e = this.canvas.getBoundingClientRect();
      this.lastX = t.clientX - e.left, this.lastY = t.clientY - e.top, this.canvas.style.cursor = "move", t.preventDefault();
    }
  }
  handleMouseLeave(t) {
    this.cancelDrag();
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
    const e = this.canvas.getBoundingClientRect(), s = t.touches[0], n = s.clientX - e.left, h = s.clientY - e.top;
    this.updateCamera(n, h), t.preventDefault();
  }
  handleTouchEnd(t) {
    this.isDragging && (this.isDragging = !1, this.forceSave(), setTimeout(() => this.forceSave(), 50));
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
    const h = this.model.get("camera_angle_z") - s * this.rotationSensitivity, o = Math.max(-1.5, Math.min(
      1.5,
      this.model.get("camera_angle_x") + n * this.rotationSensitivity
    ));
    this.model.set("camera_angle_z", h), this.model.set("camera_angle_x", o), this.lastX = t, this.lastY = e, this.throttledSave();
  }
  updatePan(t, e) {
    const s = t - this.lastX, n = e - this.lastY;
    if (s === 0 && n === 0) return;
    const h = this.model.get("camera_target") || [0, 0, 1], l = (this.model.get("camera_distance") || 10) * this.panSensitivity, a = [
      h[0] - s * l,
      h[1] + n * l,
      // Y inverted for intuitive panning
      h[2]
    ];
    this.model.set("camera_target", a), this.lastX = t, this.lastY = e, this.throttledSave();
  }
  throttledSave() {
    const t = Date.now();
    t - this.lastUpdateTime >= this.UPDATE_INTERVAL && (this.model.save_changes(), this.lastUpdateTime = t);
  }
  forceSave() {
    this.model.save_changes();
  }
  destroy() {
    this._globalMouseUpHandler && window.removeEventListener("mouseup", this._globalMouseUpHandler, !0), this._globalBlurHandler && window.removeEventListener("blur", this._globalBlurHandler, !0);
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
    console.log("CanvasRenderer.updateDisplay called with:", t ? t.substring(0, 50) + "..." : "null", e, s), t && e > 0 && s > 0 ? (this.renderImage(t, e, s), this.updateFps()) : (console.log("CanvasRenderer: No image data, showing placeholder"), this.renderPlaceholder(e || 512, s || 512));
  }
  renderImage(t, e, s) {
    (this.canvas.width !== e || this.canvas.height !== s) && (this.canvas.width = e, this.canvas.height = s);
    try {
      let n = t;
      t.startsWith("data:image") && (n = t.split(",")[1]), console.log("renderImage: Decoding base64 data, length:", n.length, "expected pixels:", e * s * 4);
      const h = atob(n);
      console.log("renderImage: Binary string length:", h.length);
      const o = new Uint8Array(h.length);
      for (let a = 0; a < o.length; a++)
        o[a] = h.charCodeAt(a);
      console.log("renderImage: Created Uint8Array with length:", o.length);
      const l = new ImageData(new Uint8ClampedArray(o), e, s);
      this.ctx.putImageData(l, 0, 0), console.log("renderImage: Image rendered successfully!");
    } catch (n) {
      console.error("Failed to render image:", n), this.renderError(e, s, "Render Error");
    }
  }
  renderPlaceholder(t, e) {
    (this.canvas.width !== t || this.canvas.height !== e) && (this.canvas.width = t, this.canvas.height = e), this.ctx.fillStyle = "#333", this.ctx.fillRect(0, 0, t, e), this.ctx.fillStyle = "#999", this.ctx.font = "14px monospace", this.ctx.textAlign = "center", this.ctx.fillText("Left-drag: rotate • Right/Middle-drag: pan • Scroll: zoom", t / 2, e / 2);
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
class f {
  constructor(t) {
    this.parentEl = t, this.container = null, this.renderTimeEl = null, this.fpsEl = null, this.create();
  }
  create() {
    this.container = document.createElement("div"), this.container.className = "camera-info", this.renderTimeEl = document.createElement("span"), this.renderTimeEl.className = "render-time", this.renderTimeEl.textContent = "Render: --ms";
    const t = document.createTextNode(" | ");
    this.fpsEl = document.createElement("span"), this.fpsEl.className = "fps", this.fpsEl.textContent = "-- FPS", this.container.appendChild(this.renderTimeEl), this.container.appendChild(t), this.container.appendChild(this.fpsEl), this.parentEl.appendChild(this.container);
  }
  updateRenderTime(t) {
    const e = t.match(/Rendered.*\((\d+)ms\)/);
    e && (this.renderTimeEl.textContent = `Render: ${e[1]}ms`);
  }
  updateFps(t) {
    t > 0 && (this.fpsEl.textContent = `${t} FPS`);
  }
  update(t, e) {
    this.updateRenderTime(t), this.updateFps(e);
  }
  destroy() {
    this.container && this.container.parentNode && this.container.parentNode.removeChild(this.container), this.container = null, this.renderTimeEl = null, this.fpsEl = null;
  }
}
const m = {
  render({ model: i, el: t }) {
    t.innerHTML = `
            <div class="bpy-widget">
                <canvas class="viewer-canvas"></canvas>
            </div>
        `;
    const e = t.querySelector(".bpy-widget"), s = t.querySelector(".viewer-canvas"), n = new v(s), h = new p(s, i), o = new f(e);
    function l() {
      const a = i.get("image_data"), r = i.get("width"), c = i.get("height");
      if (r && c && r > 0 && c > 0) {
        const g = r / c;
        e.style.aspectRatio = `${g} / 1`;
      }
      a && a.length > 0 ? n.updateDisplay(a, r, c) : r && c && r > 0 && c > 0 && n.renderPlaceholder(r, c);
      const d = n.getFps(), u = i.get("status");
      o.update(u, d);
    }
    return i.on("change:image_data", l), i.on("change:width", () => {
      const a = i.get("width"), r = i.get("height");
      if (a && r && a > 0 && r > 0) {
        const u = a / r;
        e.style.aspectRatio = `${u} / 1`;
      }
      const c = n.getFps(), d = i.get("status");
      o.update(d, c);
    }), i.on("change:height", () => {
      const a = i.get("width"), r = i.get("height");
      if (a && r && a > 0 && r > 0) {
        const u = a / r;
        e.style.aspectRatio = `${u} / 1`;
      }
      const c = n.getFps(), d = i.get("status");
      o.update(d, c);
    }), i.on("change:status", () => {
      const a = n.getFps(), r = i.get("status");
      o.update(r, a);
    }), l(), () => {
      h.destroy(), n.destroy(), o.destroy();
    };
  }
};
export {
  m as default
};
