#!/usr/bin/env python
"""
BPY Widget - Basic Usage Example

This example demonstrates the core features of the bpy-widget:
- Interactive 3D viewport with camera controls
- Material system with presets
- Post-processing effects
- Data import capabilities
- Extension management

Run with: marimo edit examples/basic_usage.py
"""

import marimo

__generated_with = "0.17.6"
app = marimo.App()

with app.setup:
    """Import and create widget"""
    import marimo as mo

    from bpy_widget import BpyWidget

    # Create widget with custom size
    widget = BpyWidget(width=800, height=600)

    mo.md("""
    # BPY Widget - Interactive Blender Viewport

    This example demonstrates the bpy-widget features. The viewport below is interactive:
    - **Drag** to rotate camera
    - **Scroll** to zoom
    - **Touch** gestures on mobile devices
    """)


@app.cell
def display():
    """Display the interactive widget"""
    mo.md("## Interactive 3D Viewport")
    return


@app.cell
def materials():
    """Demonstrate material presets"""
    mo.md("""
    ## Material System

    Apply different material presets to objects:
    """)

    # Get Suzanne object
    suzanne_obj = widget.objects.get("Suzanne")
    if suzanne_obj:
        # Create material from preset
        gold_material = widget.create_preset_material("Gold", "gold")
        widget.assign_material(suzanne_obj, gold_material)
        widget.render()

    # Show available presets
    from bpy_widget.core.materials import MATERIAL_PRESETS
    preset_names = ", ".join(f"`{p}`" for p in MATERIAL_PRESETS.keys())

    mo.md(f"""
    Available presets: {preset_names}

    Try changing the material:
    ```python
    mat = widget.create_preset_material("MyMaterial", "glass")
    widget.assign_material(suzanne, mat)
    widget.render()
    ```
    """)
    return


@app.cell
def post_processing():
    """Add post-processing effects"""
    mo.md("""
    ## Post-Processing Effects

    Adding compositor effects for enhanced visuals:
    """)

    # Setup extended compositor
    widget.setup_extended_compositor()

    # Add effects
    widget.add_bloom_glare(intensity=0.5, threshold=0.8)
    widget.add_vignette(amount=0.15)
    widget.add_color_correction(saturation=1.1)

    widget.render()

    mo.md("""
    Effects applied:
    - ✓ Bloom/Glare
    - ✓ Vignette
    - ✓ Color correction

    Try adding more:
    ```python
    widget.add_film_grain(amount=0.02)
    widget.add_chromatic_aberration(amount=0.0005)
    widget.add_sharpen(amount=0.05)
    ```
    """)
    return


@app.cell
def scene_controls():
    """Interactive scene controls"""

    # Create sliders
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

    mo.md("""
    ## Scene Controls

    Adjust scene settings interactively:
    """)

    controls_ui = mo.vstack([
        sun_energy_slider,
        background_strength_slider,
        render_engine_dropdown,
        mo.ui.button(label="Apply Settings", kind="primary")
    ])
    return (
        background_strength_slider,
        render_engine_dropdown,
        sun_energy_slider,
    )


@app.cell
def apply_settings(
    background_strength_slider,
    render_engine_dropdown,
    sun_energy_slider,
):
    """Apply scene control settings"""
    if sun_energy_slider.value:
        # Update lighting
        widget.setup_lighting(sun_energy=sun_energy_slider.value)

    if background_strength_slider.value:
        # Update background
        widget.setup_world_background(
            color=(0.05, 0.05, 0.1),
            strength=background_strength_slider.value
        )

    if render_engine_dropdown.value:
        # Switch render engine
        widget.set_render_engine(render_engine_dropdown.value)

    # Re-render
    widget.render()

    mo.md(f"""
    Settings applied:
    - Sun Energy: {sun_energy_slider.value}
    - Background: {background_strength_slider.value}
    - Engine: {render_engine_dropdown.value}
    - Status: {widget.status}
    """)
    return


@app.cell
def _():
    """Create object creation UI"""
    mo.md("""
    ## Object Creation

    Add new objects to the scene:
    """)

    # Create UI
    create_torus_btn = mo.ui.button("Create Torus", kind="neutral")
    create_sphere_btn = mo.ui.button("Create Sphere", kind="neutral")
    clear_scene_btn = mo.ui.button("Clear Scene", kind="danger")

    button_group = mo.hstack([create_torus_btn, create_sphere_btn, clear_scene_btn])
    return clear_scene_btn, create_sphere_btn, create_torus_btn


@app.cell
def create_objects(clear_scene_btn, create_sphere_btn, create_torus_btn):
    """Handle object creation button clicks"""

    # Handle button clicks
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
def convenience_properties():
    """Show convenience properties for easy access"""
    mo.md("""
    ## Convenience Properties

    Easy access to Blender's core objects:
    """)

    # Show current state
    scene_info = f"""
    **Current Scene Info:**
    - Active Object: `{widget.active_object.name if widget.active_object else 'None'}`
    - Selected Objects: `{len(widget.selected_objects)}`
    - Total Objects: `{len(widget.objects)}`
    - Scene Camera: `{widget.camera.name if widget.camera else 'None'}`

    **Available Properties:**
    ```python
    # Direct access to Blender internals
    ctx = widget.context      # bpy.context
    scene = widget.scene      # bpy.context.scene
    camera = widget.camera    # bpy.context.scene.camera
    active = widget.active_object    # bpy.context.active_object
    selected = widget.selected_objects  # bpy.context.selected_objects
    data = widget.data        # bpy.data
    ops = widget.ops          # bpy.ops
    objects = widget.objects  # bpy.data.objects
    ```

    These properties provide convenient access without typing long paths!
    """

    mo.md(scene_info)
    return


@app.cell
def extensions():
    """Show extension management"""
    mo.md("""
    ## Extension Management

    Manage Blender extensions and addons:
    """)

    # List repositories
    repos = widget.list_repositories()

    if repos:
        repo_info = "\n".join([f"- {r['name']} ({'enabled' if r['enabled'] else 'disabled'})"
                               for r in repos])

        # List extensions
        extensions_list = widget.list_extensions()[:5]  # Show first 5
        ext_info = "\n".join([f"- {e.get('name', e['id'])} ({'✓' if e.get('enabled') else '✗'})"
                              for e in extensions_list])

        mo.md(f"""
        **Repositories:**
        {repo_info}

        **Sample Extensions:**
        {ext_info}

        ```python
        # Enable an extension
        widget.enable_extension("node_wrangler")

        # Install from file
        widget.install_extension_from_file("addon.zip")
        ```
        """)
    else:
        mo.md("*Extension system not available in this Blender version*")
    return


@app.cell
def performance():
    """Show performance information"""
    scene = widget.scene

    performance_info = f"""
    ## Performance Information

    - **Resolution:** {widget.width} × {widget.height}
    - **Render Engine:** {scene.render.engine}
    - **Status:** {widget.status}
    - **Blender Version:** {widget.data.version_string if hasattr(widget.data, 'version_string') else 'Unknown'}

    ### Tips for Better Performance:
    - Use `BLENDER_EEVEE_NEXT` for interactive work
    - Reduce `taa_render_samples` for faster updates
    - Disable raytracing when not needed
    - Use lower resolution for previews
    """

    mo.md(performance_info)
    return


@app.cell
def export_info():
    """Information about import/export"""
    mo.md("""
    ## Import/Export Capabilities

    The widget supports various 3D formats:

    ### Import
    ```python
    # GLTF/GLB models
    widget.import_gltf("model.glb")

    # USD scenes
    widget.import_usd("scene.usd")

    # Alembic animations
    widget.import_alembic("animation.abc")

    # Data files (CSV, Parquet)
    widget.import_data("data.csv", as_type="points")
    ```

    ### Export
    ```python
    # Export scene
    widget.export_gltf("output.glb")
    widget.export_usd("output.usd")

    # Export scene data
    widget.export_scene_as_parquet("scene_data.parquet")
    ```
    """)
    return


if __name__ == "__main__":
    app.run()
