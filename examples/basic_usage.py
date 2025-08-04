import marimo

__generated_with = "0.14.12"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    return mo,


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
    # BPY Widget Demo - Interactive Render Settings

    🐵 **Interactive Blender rendering with customizable settings!**

    **Features:**
    - 🎮 Mouse drag to orbit camera
    - 🔍 Scroll wheel to zoom
    - ⚡ Real-time rendering updates
    - 🎨 Switch between render engines
    - ⚙️ Adjust quality settings
    - 🎯 Performance monitoring
    """
    )
    return


@app.cell
def _():
    from bpy_widget import BpyWidget

    # Create widget with default settings
    widget = BpyWidget(width=800, height=600)
    return BpyWidget, widget


@app.cell(hide_code=True)
def _(mo):
    mo.md("""## 🎛️ Render Settings""")
    return


@app.cell
def _(mo, widget):
    # Create render engine selector
    engine_select = mo.ui.dropdown(
        options=["BLENDER_EEVEE_NEXT", "CYCLES"],
        value=widget.render_engine,
        label="🎨 Render Engine"
    )

    # Device selector (only relevant for Cycles)
    device_select = mo.ui.dropdown(
        options=["CPU", "GPU"],
        value=widget.render_device,
        label="🖥️ Device"
    )

    # Quality presets with actual resolution
    quality_select = mo.ui.dropdown(
        options={
            "Draft (400x300)": (400, 300),
            "Preview (800x600)": (800, 600),
            "Final (1600x1200)": (1600, 1200)
        },
        value="Preview (800x600)",
        label="⚡ Quality / Resolution"
    )

    # Safe render mode
    safe_render = mo.ui.checkbox(
        value=widget.use_safe_render,
        label="🛡️ Safe Render Mode (auto-fallback)"
    )

    mo.hstack([
        mo.vstack([engine_select, device_select]),
        mo.vstack([quality_select, safe_render])
    ], justify="start", gap=1)
    return device_select, engine_select, quality_select, safe_render


@app.cell(hide_code=True)
def _(mo):
    mo.md("""## 🎨 Scene Settings""")
    return


@app.cell
def _(mo):
    # Background color picker - correct slider syntax
    bg_color_r = mo.ui.slider(0, 1, step=0.05, value=0.8, label="Red")
    bg_color_g = mo.ui.slider(0, 1, step=0.05, value=0.8, label="Green")
    bg_color_b = mo.ui.slider(0, 1, step=0.05, value=0.9, label="Blue")

    # Lighting intensity
    light_intensity = mo.ui.slider(
        start=0.5,
        stop=5.0,
        step=0.5,
        value=1.0,
        label="💡 Light Intensity"
    )

    # Object materials
    material_type = mo.ui.dropdown(
        options=["Default", "Glass", "Metal", "Mixed"],
        value="Default",
        label="🎭 Material Type"
    )

    mo.hstack([
        mo.vstack([
            mo.md("**🌈 Background Color:**"),
            bg_color_r,
            bg_color_g,
            bg_color_b
        ]),
        mo.vstack([
            light_intensity,
            material_type
        ])
    ], justify="start", gap=2)
    return bg_color_b, bg_color_g, bg_color_r, light_intensity, material_type


@app.cell
def _(
    bg_color_b,
    bg_color_g,
    bg_color_r,
    device_select,
    engine_select,
    light_intensity,
    material_type,
    quality_select,
    safe_render,
    widget,
):
    # Apply render engine settings
    if engine_select.value != widget.render_engine:
        widget.render_engine = engine_select.value

    if device_select.value != widget.render_device:
        widget.render_device = device_select.value

    # Apply safe render mode
    widget.use_safe_render = safe_render.value

    # Apply quality/resolution preset
    render_width, render_height = quality_select.value
    widget.set_resolution(render_width, render_height)

    # Apply sample settings based on resolution
    if render_width <= 400:  # Draft
        if widget.render_engine == "CYCLES":
            widget.scene.cycles.samples = 16
        else:
            widget.scene.eevee.taa_render_samples = 8
    elif render_width <= 800:  # Preview
        if widget.render_engine == "CYCLES":
            widget.scene.cycles.samples = 64
        else:
            widget.scene.eevee.taa_render_samples = 16
    else:  # Final
        if widget.render_engine == "CYCLES":
            widget.scene.cycles.samples = 256
        else:
            widget.scene.eevee.taa_render_samples = 64

    # Apply background color
    widget.setup_world_background(
        color=(bg_color_r.value, bg_color_g.value, bg_color_b.value),
        strength=1.0
    )

    # Apply lighting
    if 'Light' in widget.objects:
        widget.objects['Light'].data.energy = light_intensity.value * 1000

    # Apply materials
    if material_type.value != "Default":
        suzanne = widget.objects.get('Suzanne')
        cube = widget.objects.get('Cube')

        if material_type.value == "Glass":
            if suzanne:
                mat = widget.create_glass_material("SuzanneGlass", roughness=0.1)
                widget.assign_material(suzanne, mat)
            if cube:
                mat_cube = widget.create_glass_material("CubeGlass", roughness=0.2, base_color=(0.8, 0.9, 1.0, 1.0))
                widget.assign_material(cube, mat_cube)

        elif material_type.value == "Metal":
            if suzanne:
                mat = widget.create_metal_material("SuzanneMetal", roughness=0.3)
                widget.assign_material(suzanne, mat)
            if cube:
                mat_cube = widget.create_metal_material("CubeMetal", roughness=0.5, base_color=(0.8, 0.6, 0.2, 1.0))
                widget.assign_material(cube, mat_cube)

        elif material_type.value == "Mixed":
            if suzanne:
                mat = widget.create_glass_material("SuzanneGlass", roughness=0.1)
                widget.assign_material(suzanne, mat)
            if cube:
                mat_cube = widget.create_metal_material("CubeMetal", roughness=0.3, base_color=(0.7, 0.5, 0.9, 1.0))
                widget.assign_material(cube, mat_cube)

    print(f"✓ Applied settings: {widget.render_engine} @ {render_width}x{render_height}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""## 🖼️ Rendered Output""")
    return


@app.cell(hide_code=True)
def _(widget):
    # Display the widget
    widget
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""## 📊 Performance Stats""")
    return


@app.cell
def _(mo, widget):
    # Create auto-updating performance display
    stats = widget.get_performance_stats()

    perf_info = mo.md(f"""
    **Render Performance:**
    - ⏱️ Last render: **{widget.render_time_ms:.1f}ms**
    - 📊 Average: **{widget.avg_render_time_ms:.1f}ms**
    - 🔢 Total renders: **{stats['total_renders']}**
    - 🎯 Engine: **{widget.render_engine}** on **{widget.render_device}**
    - 📐 Resolution: **{widget.scene.render.resolution_x}x{widget.scene.render.resolution_y}**
    - 🖼️ Widget size: **{widget.width}x{widget.height}**
    """)

    perf_info
    return perf_info, stats


@app.cell(hide_code=True)
def _(mo):
    mo.md("""## 🎬 Actions""")
    return


@app.cell
def _(widget):
    def cam_reset(val):
        widget.setup_camera(distance=8.0)
        widget.render()
    return cam_reset,


@app.cell
def _(cam_reset, mo):
    # Create action buttons
    reset_camera_btn = mo.ui.button(
        label="📷 Reset Camera",
        kind="neutral",
        on_click=cam_reset
    )

    add_compositor_btn = mo.ui.button(
        label="✨ Add Glare Effect",
        kind="neutral"
    )

    clear_scene_btn = mo.ui.button(
        label="🗑️ Clear Scene",
        kind="danger"
    )

    reset_stats_btn = mo.ui.button(
        label="📊 Reset Stats",
        kind="neutral"
    )

    mo.hstack([
        reset_camera_btn,
        add_compositor_btn,
        clear_scene_btn,
        reset_stats_btn
    ], align="center", justify="center")
    return (
        add_compositor_btn,
        clear_scene_btn,
        reset_camera_btn,
        reset_stats_btn,
    )


@app.cell
def _(
    add_compositor_btn,
    clear_scene_btn,
    reset_camera_btn,
    reset_stats_btn,
    widget,
):
    # Handle button actions
    if reset_camera_btn.value:
        widget.setup_camera(distance=8.0)
        widget.render()
        print("✓ Camera reset")

    if add_compositor_btn.value:
        widget.setup_compositor()
        widget.add_glare(intensity=0.8)
        widget.render()
        print("✓ Added glare effect")

    if clear_scene_btn.value:
        widget.clear_scene()
        # Re-create basic scene
        widget.setup_camera()
        widget.setup_lighting()
        widget.create_test_cube()
        widget.create_suzanne()
        widget.render()
        print("✓ Scene cleared and rebuilt")

    if reset_stats_btn.value:
        widget.reset_performance_stats()
        print("✓ Performance stats reset")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""## 🔍 Debug Information""")
    return


@app.cell
def _(mo):
    # Debug info toggle
    show_debug = mo.ui.checkbox(label="Show debug info")
    show_debug
    return show_debug,


@app.cell
def _(show_debug, widget):
    if show_debug.value:
        widget.debug_info()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
    ---

    ### 💡 Tips

    - **EEVEE Next** is great for real-time preview (5-10x faster)
    - **Cycles** provides more accurate lighting and reflections
    - **GPU rendering** is much faster for Cycles (if available)
    - **Safe Render Mode** automatically falls back if rendering fails
    - **Resolution Presets** control the actual render resolution:
      - Draft (400x300) = Fastest, good for testing
      - Preview (800x600) = Balanced quality/speed
      - Final (1600x1200) = Best quality, slower

    ### 🎮 Controls

    - **Left Mouse Drag**: Orbit camera
    - **Scroll Wheel**: Zoom in/out
    - **Middle Mouse Drag**: Pan view (if supported)
    
    ### 🪟 Windows Users
    
    - Safe Render Mode is automatically enabled on Windows
    - Temporary files are managed with Windows-specific handling
    - If you experience issues, try restarting the Marimo kernel
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion({
        "🎨 Available UI Elements": mo.md("""
        **Inputs:**
        - `mo.ui.slider(start, stop, step=None, value=None)` - Numeric slider
        - `mo.ui.dropdown(options, value=None)` - Selection dropdown
        - `mo.ui.checkbox(value=False)` - Boolean checkbox
        - `mo.ui.button(label="Click")` - Action button
        - `mo.ui.text(value="")` - Text input
        - `mo.ui.number(start, stop, value=None)` - Number input
        - `mo.ui.radio(options, value=None)` - Radio buttons
        - `mo.ui.switch(value=False)` - Toggle switch

        **Layouts:**
        - `mo.hstack([...], justify="start", gap=1)` - Horizontal stack
        - `mo.vstack([...], gap=1)` - Vertical stack
        - `mo.accordion({...})` - Collapsible sections
        - `mo.ui.tabs({...})` - Tabbed interface
        - `mo.callout("text", kind="info")` - Highlighted box
        """),
        "🛠️ Widget Methods": mo.md("""
        **Scene Management:**
        - `widget.clear_scene()`
        - `widget.setup_lighting()`
        - `widget.setup_camera()`
        - `widget.setup_world_background()`
        - `widget.set_resolution(width, height)`

        **Object Creation:**
        - `widget.create_test_cube()`
        - `widget.create_suzanne()`

        **Materials:**
        - `widget.create_glass_material()`
        - `widget.create_metal_material()`
        - `widget.assign_material()`

        **Compositor:**
        - `widget.setup_compositor()`
        - `widget.add_glare()`
        """),
        "📊 Performance Features": mo.md("""
        - **Real-time monitoring** of render times
        - **Average calculation** over multiple renders
        - **Safe render mode** with automatic fallbacks
        - **Resolution control** for performance vs quality
        - **Quality presets** for quick adjustments
        - Blender always renders at 100% resolution
        - **Windows optimization** for file handling
        """)
    })
    return


if __name__ == "__main__":
    app.run()
