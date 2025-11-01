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

import marimo as mo

# Create app
app = mo.App()

# Cell 1: Imports
@app.cell
def imports():
    """Import required modules"""
    from bpy_widget import BpyWidget
    import marimo as mo

    return BpyWidget, mo

# Cell 2: Setup
@app.cell
def setup(BpyWidget, mo):
    """Create widget"""

    # Create widget with custom size
    widget = BpyWidget(width=800, height=600)

    mo.md("""
    # BPY Widget - Interactive Blender Viewport

    This example demonstrates the bpy-widget features. The viewport below is interactive:
    - **Drag** to rotate camera
    - **Scroll** to zoom
    - **Touch** gestures on mobile devices
    """)

    return widget,

# Cell 3: Display widget
@app.cell
def display(widget):
    """Display the interactive widget"""
    mo.md("## Interactive 3D Viewport")
    return widget,

# Cell 4: Material presets
@app.cell
def materials(widget):
    """Demonstrate material presets"""
    mo.md("""
    ## Material System
    
    Apply different material presets to objects:
    """)
    
    # Get Suzanne object
    suzanne = widget.objects.get("Suzanne")
    if suzanne:
        # Create material from preset
        gold_mat = widget.create_preset_material("Gold", "gold")
        widget.assign_material(suzanne, gold_mat)
        widget.render()
    
    # Show available presets
    from bpy_widget.core.materials import MATERIAL_PRESETS
    preset_list = ", ".join(f"`{p}`" for p in MATERIAL_PRESETS.keys())
    
    mo.md(f"""
    Available presets: {preset_list}
    
    Try changing the material:
    ```python
    mat = widget.create_preset_material("MyMaterial", "glass")
    widget.assign_material(suzanne, mat)
    widget.render()
    ```
    """)
    
    return MATERIAL_PRESETS,

# Cell 4: Post-processing
@app.cell
def post_processing(widget):
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

# Cell 5: Scene controls
@app.cell
def scene_controls(widget):
    """Interactive scene controls"""
    import marimo as mo
    
    # Create sliders
    sun_energy = mo.ui.slider(
        start=0.5, stop=10.0, value=3.0, step=0.5,
        label="Sun Energy"
    )
    
    background_strength = mo.ui.slider(
        start=0.0, stop=2.0, value=1.0, step=0.1,
        label="Background Strength"
    )
    
    render_engine = mo.ui.dropdown(
        options=["BLENDER_EEVEE_NEXT", "CYCLES"],
        value="BLENDER_EEVEE_NEXT",
        label="Render Engine"
    )
    
    mo.md("""
    ## Scene Controls
    
    Adjust scene settings interactively:
    """)
    
    controls = mo.vstack([
        sun_energy,
        background_strength,
        render_engine,
        mo.ui.button(label="Apply Settings", kind="primary")
    ])
    
    return sun_energy, background_strength, render_engine, controls

# Cell 6: Apply scene settings
@app.cell
def apply_settings(sun_energy, background_strength, render_engine, widget):
    """Apply scene control settings"""
    if sun_energy.value:
        # Update lighting
        widget.setup_lighting(sun_energy=sun_energy.value)
        
    if background_strength.value:
        # Update background
        widget.setup_world_background(
            color=(0.05, 0.05, 0.1),
            strength=background_strength.value
        )
    
    if render_engine.value:
        # Switch render engine
        widget.set_render_engine(render_engine.value)
    
    # Re-render
    widget.render()
    
    mo.md(f"""
    Settings applied:
    - Sun Energy: {sun_energy.value}
    - Background: {background_strength.value}
    - Engine: {render_engine.value}
    - Status: {widget.status}
    """)

# Cell 7: Object creation
@app.cell
def create_objects(widget):
    """Create new objects"""
    mo.md("""
    ## Object Creation
    
    Add new objects to the scene:
    """)
    
    # Create UI
    create_torus = mo.ui.button("Create Torus", kind="neutral")
    create_sphere = mo.ui.button("Create Sphere", kind="neutral")
    clear_scene = mo.ui.button("Clear Scene", kind="danger")
    
    buttons = mo.hstack([create_torus, create_sphere, clear_scene])
    
    # Handle button clicks
    if create_torus.value:
        widget.create_torus(location=(3, 0, 1))
        widget.render()
        
    if create_sphere.value:
        widget.create_icosphere(location=(-3, 0, 1))
        widget.render()
        
    if clear_scene.value:
        widget.clear_scene()
        widget.setup_lighting()
        widget.setup_world_background()
        widget.create_suzanne()
        widget.create_test_cube()
        widget.render()
    
    return buttons

# Cell 8: Convenience Properties
@app.cell
def convenience_properties(widget):
    """Show convenience properties for easy access"""
    mo.md("""
    ## Convenience Properties

    Easy access to Blender's core objects:
    """)

    # Show current state
    convenience_info = f"""
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

    mo.md(convenience_info)

    return convenience_info

# Cell 5: Material presets
@app.cell
def materials(widget):
    """Demonstrate material presets"""
    mo.md("""
    ## Material System

    Apply different material presets to objects:
    """)

    # Get Suzanne object
    suzanne = widget.objects.get("Suzanne")
    if suzanne:
        # Create material from preset
        gold_mat = widget.create_preset_material("Gold", "gold")
        widget.assign_material(suzanne, gold_mat)
        widget.render()

    # Show available presets
    from bpy_widget.core.materials import MATERIAL_PRESETS
    preset_list = ", ".join(f"`{p}`" for p in MATERIAL_PRESETS.keys())

    mo.md(f"""
    Available presets: {preset_list}

    Try changing the material:
    ```python
    mat = widget.create_preset_material("MyMaterial", "glass")
    widget.assign_material(suzanne, mat)
    widget.render()
    ```
    """)

    return MATERIAL_PRESETS,

# Cell 6: Post-processing
@app.cell
def post_processing(widget):
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

# Cell 7: Scene controls
@app.cell
def scene_controls(widget):
    """Interactive scene controls"""
    import marimo as mo

    # Create sliders
    sun_energy = mo.ui.slider(
        start=0.5, stop=10.0, value=3.0, step=0.5,
        label="Sun Energy"
    )

    background_strength = mo.ui.slider(
        start=0.0, stop=2.0, value=1.0, step=0.1,
        label="Background Strength"
    )

    render_engine = mo.ui.dropdown(
        options=["BLENDER_EEVEE_NEXT", "CYCLES"],
        value="BLENDER_EEVEE_NEXT",
        label="Render Engine"
    )

    mo.md("""
    ## Scene Controls

    Adjust scene settings interactively:
    """)

    controls = mo.vstack([
        sun_energy,
        background_strength,
        render_engine,
        mo.ui.button(label="Apply Settings", kind="primary")
    ])

    return sun_energy, background_strength, render_engine, controls

# Cell 8: Apply scene settings
@app.cell
def apply_settings(sun_energy, background_strength, render_engine, widget):
    """Apply scene control settings"""
    if sun_energy.value:
        # Update lighting
        widget.setup_lighting(sun_energy=sun_energy.value)

    if background_strength.value:
        # Update background
        widget.setup_world_background(
            color=(0.05, 0.05, 0.1),
            strength=background_strength.value
        )

    if render_engine.value:
        # Switch render engine
        widget.set_render_engine(render_engine.value)

    # Re-render
    widget.render()

    mo.md(f"""
    Settings applied:
    - Sun Energy: {sun_energy.value}
    - Background: {background_strength.value}
    - Engine: {render_engine.value}
    - Status: {widget.status}
    """)

# Cell 9: Object creation
@app.cell
def create_objects(widget):
    """Create new objects"""
    mo.md("""
    ## Object Creation

    Add new objects to the scene:
    """)

    # Create UI
    create_torus = mo.ui.button("Create Torus", kind="neutral")
    create_sphere = mo.ui.button("Create Sphere", kind="neutral")
    clear_scene = mo.ui.button("Clear Scene", kind="danger")

    buttons = mo.hstack([create_torus, create_sphere, clear_scene])

    # Handle button clicks
    if create_torus.value:
        widget.create_torus(location=(3, 0, 1))
        widget.render()

    if create_sphere.value:
        widget.create_icosphere(location=(-3, 0, 1))
        widget.render()

    if clear_scene.value:
        widget.clear_scene()
        widget.setup_lighting()
        widget.setup_world_background()
        widget.create_suzanne()
        widget.create_test_cube()
        widget.render()

    return buttons

# Cell 10: Convenience Properties
@app.cell
def convenience_properties(widget):
    """Show convenience properties for easy access"""
    mo.md("""
    ## Convenience Properties

    Easy access to Blender's core objects:
    """)

    # Show current state
    convenience_info = f"""
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

    mo.md(convenience_info)

    return convenience_info

# Cell 11: Extension management
@app.cell
def extensions(widget):
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
        extensions = widget.list_extensions()[:5]  # Show first 5
        ext_info = "\n".join([f"- {e.get('name', e['id'])} ({'✓' if e.get('enabled') else '✗'})"
                              for e in extensions])

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

# Cell 13: Performance info
@app.cell
def performance(widget):
    """Show performance information"""
    scene = widget.scene
    
    info = f"""
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
    
    mo.md(info)

# Cell 14: Export capabilities
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

if __name__ == "__main__":
    app.run()
