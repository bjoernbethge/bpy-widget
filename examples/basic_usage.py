#!/usr/bin/env python
"""
BPY Widget - Basic Usage Example

Core features demonstration:
- Interactive 3D viewport with camera controls
- Material system with presets
- Post-processing effects
- Scene controls

Run with: marimo run examples/basic_usage.py
"""

import marimo

__generated_with = "0.17.6"
app = marimo.App()


@app.cell
def setup():
    """Setup"""
    import marimo as mo

    from bpy_widget import BpyWidget

    widget = BpyWidget(width=800, height=600)

    return BpyWidget, mo, widget


@app.cell
def viewport(mo, widget):
    """Main Viewport"""
    # Widget with interactive controls - drag to rotate, scroll to zoom
    widget
    return


@app.cell
def materials(mo, widget):
    """Materials"""
    from bpy_widget.core.materials import MATERIAL_PRESETS

    preset_dropdown = mo.ui.dropdown(
        options=list(MATERIAL_PRESETS.keys()),
        value="gold",
        label="Material Preset"
    )

    mo.vstack([
        mo.md("**Material Presets**"),
        preset_dropdown,
    ])

    return MATERIAL_PRESETS, preset_dropdown


@app.cell
def apply_material(preset_dropdown, widget):
    """Apply Material - automatically when preset changes"""
    suzanne_obj = widget.objects.get("Suzanne")
    if suzanne_obj:
        # Create material with unique name to avoid conflicts
        material_name = f"Suzanne_{preset_dropdown.value}"
        material = widget.create_preset_material(
            material_name,
            preset_dropdown.value
        )
        widget.assign_material(suzanne_obj, material)
        widget.render()
    return


@app.cell
def post_processing(mo, widget):
    """Post-Processing"""
    bloom_enabled = mo.ui.checkbox(True, label="Bloom/Glare")
    vignette_enabled = mo.ui.checkbox(True, label="Vignette")
    color_correction_enabled = mo.ui.checkbox(True, label="Color Correction")

    mo.vstack([
        mo.md("**Post-Processing Effects**"),
        bloom_enabled,
        vignette_enabled,
        color_correction_enabled,
    ])

    return (
        bloom_enabled,
        color_correction_enabled,
        vignette_enabled,
    )


@app.cell
def setup_effects(
    bloom_enabled,
    color_correction_enabled,
    vignette_enabled,
    widget,
):
    """Setup Effects - automatically when checkboxes change"""
    widget.setup_extended_compositor()

    if bloom_enabled.value:
        widget.add_bloom_glare(intensity=0.5, threshold=0.8)
    if vignette_enabled.value:
        widget.add_vignette(amount=0.15)
    if color_correction_enabled.value:
        widget.add_color_correction(saturation=1.1)

    widget.render()
    return


@app.cell
def scene_controls(mo):
    """Scene Controls"""
    sun_energy_slider = mo.ui.slider(
        start=0.5, stop=10.0, value=3.0, step=0.5,
        label="Sun Energy"
    )

    background_strength_slider = mo.ui.slider(
        start=0.0, stop=2.0, value=1.0, step=0.1,
        label="Background Strength"
    )

    render_engine_dropdown = mo.ui.dropdown(
        options=["BLENDER_EEVEE_NEXT", "CYCLES"],
        value="BLENDER_EEVEE_NEXT",
        label="Render Engine"
    )

    mo.vstack([
        mo.md("**Scene Settings**"),
        sun_energy_slider,
        background_strength_slider,
        render_engine_dropdown,
    ])

    return (
        background_strength_slider,
        render_engine_dropdown,
        sun_energy_slider,
    )


@app.cell
def update_scene(
    background_strength_slider,
    render_engine_dropdown,
    sun_energy_slider,
    widget,
):
    """Update Scene"""
    widget.setup_lighting(sun_energy=sun_energy_slider.value)
    widget.setup_world_background(
        color=(0.05, 0.05, 0.1),
        strength=background_strength_slider.value
    )
    widget.set_render_engine(render_engine_dropdown.value)
    widget.render()
    return


@app.cell
def object_creation(mo):
    """Objects"""
    create_torus_btn = mo.ui.button("Create Torus", kind="neutral")
    create_sphere_btn = mo.ui.button("Create Sphere", kind="neutral")
    clear_scene_btn = mo.ui.button("Clear Scene", kind="danger")

    mo.vstack([
        mo.md("**Object Creation**"),
        mo.hstack([create_torus_btn, create_sphere_btn]),
        clear_scene_btn,
    ])

    return clear_scene_btn, create_sphere_btn, create_torus_btn


@app.cell
def handle_objects(
    clear_scene_btn, create_sphere_btn, create_torus_btn, widget
):
    """Handle Object Creation"""
    if create_torus_btn.value:
        widget.create_torus(location=(3, 0, 1))
        widget.render()

    if create_sphere_btn.value:
        widget.create_icosphere(location=(-3, 0, 1))
        widget.render()

    if clear_scene_btn.value:
        widget.clear_scene()
        widget.setup_lighting()
        widget.setup_world_background()
        widget.create_suzanne()
        widget.create_test_cube()
        widget.render()
    return


@app.cell
def scene_info(mo, widget):
    """Scene Info"""
    mo.md(f"""
    **Scene Status:** {widget.status}

    Objects: {len(widget.objects)} |
    Camera: {widget.camera.name if widget.camera else 'None'}
    """)
    return


if __name__ == "__main__":
    app.run()
