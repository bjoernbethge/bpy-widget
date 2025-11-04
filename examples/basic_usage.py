#!/usr/bin/env python
"""
BPY Widget - Basic Usage Example

Core features demonstration:
- Interactive 3D viewport with camera controls
- Material system with presets
- Post-processing effects
- Scene controls
- Extension Management (search & install from extensions.blender.org)

Run with: marimo run examples/basic_usage.py
"""

import marimo

__generated_with = "0.17.6"
app = marimo.App(
    app_title="bpy-widget-demo",
    layout_file="layouts/basic_usage.grid.json",
    auto_download=["ipynb"],
)

with app.setup:
    """Setup"""
    import marimo as mo

    from bpy_widget import BpyWidget

    widget = BpyWidget(width=1920, height=1080)


@app.cell
def viewport():
    """Main Viewport"""
    # Widget with interactive controls - drag to rotate, scroll to zoom
    widget
    return


@app.cell
def materials():
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
    return (preset_dropdown,)


@app.cell
def apply_material(preset_dropdown):
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
def post_processing():
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
    return bloom_enabled, color_correction_enabled, vignette_enabled


@app.cell
def setup_effects(bloom_enabled, color_correction_enabled, vignette_enabled):
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
def scene_controls():
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

    gpu_backend_dropdown = mo.ui.dropdown(
        options=["VULKAN", "OPENGL"],
        value="VULKAN",
        label="GPU Backend"
    )

    mo.vstack([
        mo.md("**Scene Settings**"),
        sun_energy_slider,
        background_strength_slider,
        render_engine_dropdown,
        gpu_backend_dropdown,
    ])
    return (
        background_strength_slider,
        gpu_backend_dropdown,
        render_engine_dropdown,
        sun_energy_slider,
    )


@app.cell
def update_scene(
    background_strength_slider,
    gpu_backend_dropdown,
    render_engine_dropdown,
    sun_energy_slider,
):
    """Update Scene"""
    widget.setup_lighting(sun_energy=sun_energy_slider.value)
    widget.setup_world_background(
        color=(0.05, 0.05, 0.1),
        strength=background_strength_slider.value
    )
    widget.set_render_engine(render_engine_dropdown.value)

    # Update GPU backend if changed
    current_backend = widget.get_gpu_backend()
    if current_backend != gpu_backend_dropdown.value:
        widget.set_gpu_backend(gpu_backend_dropdown.value)

    widget.render()
    return


@app.cell
def object_creation():
    """Objects"""
    create_torus_btn = mo.ui.button(label="Create Torus", kind="neutral")
    create_sphere_btn = mo.ui.button(label="Create Sphere", kind="neutral")
    clear_scene_btn = mo.ui.button(label="Clear Scene", kind="danger")

    mo.vstack([
        mo.md("**Object Creation**"),
        mo.hstack([create_torus_btn, create_sphere_btn]),
        clear_scene_btn,
    ])
    return clear_scene_btn, create_sphere_btn, create_torus_btn


@app.cell
def handle_objects(clear_scene_btn, create_sphere_btn, create_torus_btn):
    """Handle Object Creation"""
    if create_torus_btn.value is not None and create_torus_btn.value > 0:
        widget.create_torus(location=(3, 0, 1))
        widget.render()

    if create_sphere_btn.value is not None and create_sphere_btn.value > 0:
        widget.create_icosphere(location=(-3, 0, 1))
        widget.render()

    if clear_scene_btn.value is not None and clear_scene_btn.value > 0:
        widget.clear_scene()
        widget.setup_lighting()
        widget.setup_world_background()
        widget.create_suzanne()
        widget.create_test_cube()
        widget.render()
    return


@app.cell
def scene_info():
    """Scene Info"""
    mo.md(f"""
    **Scene Status:** {widget.status}

    Objects: {len(widget.objects)} |
    Camera: {widget.camera.name if widget.camera else 'None'}
    """)
    return


@app.cell
def extension_search():
    """Extension Search"""
    search_query = mo.ui.text(
        value="",
        placeholder="Search extensions (e.g., 'molecular', 'node wrangler')",
        label="Search Extensions"
    )

    search_btn = mo.ui.button(label="Search", kind="neutral")
    install_first_btn = mo.ui.button(label="Install", kind="success")

    mo.vstack([
        mo.md("**Extension Management**"),
        mo.md("Search and install extensions from [extensions.blender.org](https://extensions.blender.org)"),
        search_query,
        mo.hstack([search_btn, install_first_btn]),
    ])
    return install_first_btn, search_btn, search_query


@app.cell
def handle_extension_search(install_first_btn, search_btn, search_query):
    """Handle Extension Search"""
    # Search when button is clicked
    search_results = []
    if search_btn.value is not None and search_btn.value > 0 and search_query.value:
        search_results = widget.search_extensions(search_query.value, limit=10)

    # Install when install button is clicked
    install_message = None
    if install_first_btn.value is not None and install_first_btn.value > 0 and search_query.value:
        success = widget.search_and_install(search_query.value, index=0)
        if success:
            install_message = mo.md("✓ Installation started! Click 'Refresh List' below to see installed extensions.")
        else:
            install_message = mo.md(f"⚠ Installation failed. Status: {widget.status}")

    # Format search results
    if not search_results:
        if search_btn.value is not None and search_btn.value > 0:
            results_display = mo.md("No extensions found. Try a different search term.")
        else:
            results_display = mo.md("Enter a search term and click 'Search'")
    else:
        result_text = "**Search Results:**\n\n"
        for i, extension in enumerate(search_results[:5]):
            result_text += f"{i+1}. **{extension['name']}** ({extension['type']})\n"
            result_text += f"   {extension['tagline']}\n"
            result_text += f"   Version: {extension['version']}\n\n"
        if len(search_results) > 5:
            result_text += f"*... and {len(search_results) - 5} more*"
        results_display = mo.md(result_text)

    # Show results and install message
    mo.vstack([
        results_display,
        install_message if install_message else mo.md(""),
    ])
    return


@app.cell
def _():
    refresh_btn = mo.ui.button(label="Refresh List", kind="neutral")
    return (refresh_btn,)


@app.cell
def installed_extensions(refresh_btn):
    """Installed Extensions"""
    # Load extensions when button is clicked (or initially to show what's there)
    # Always load on first render and when button is clicked
    installed_exts = []
    if refresh_btn.value is None or refresh_btn.value >= 0:  # Initial load or after click
        installed_exts = widget.list_extensions()

    # Format extensions list
    if not installed_exts:
        formatted = mo.md("No extensions installed. Use the search above to find and install extensions.")
    else:
        ext_text = "**Installed Extensions:**\n\n"
        for ext in installed_exts[:10]:
            status = "✓ Enabled" if ext.get('enabled', False) else "○ Disabled"
            ext_text += f"- **{ext.get('name', ext.get('id', 'Unknown'))}** {status}\n"
            if ext.get('version'):
                ext_text += f"  Version: {ext['version']}\n"
            if ext.get('repository'):
                ext_text += f"  Repository: {ext['repository']}\n"
            ext_text += "\n"
        if len(installed_exts) > 10:
            ext_text += f"*... and {len(installed_exts) - 10} more*"
        formatted = mo.md(ext_text)

    mo.vstack([
        mo.md("**Installed Extensions**"),
        refresh_btn,
        formatted,
    ])
    return


@app.cell
def file_management():
    """File Management"""
    file_input = mo.ui.file(
        filetypes=[".blend", ".obj", ".fbx", ".gltf", ".glb", ".usd", ".usda", ".usdc", ".abc", ".stl", ".ply", ".x3d", ".dae", ".svg", ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".exr", ".hdr"],
        multiple=True,
        label="Import Files"
    )

    import_btn = mo.ui.button(label="Import Selected Files", kind="success")
    clear_imports_btn = mo.ui.button(label="Clear Imported Objects", kind="neutral")

    mo.vstack([
        mo.md("**File Import**"),
        mo.md("Upload 3D models (.obj, .fbx, .gltf, .blend), images, or other supported files"),
        file_input,
        mo.hstack([import_btn, clear_imports_btn]),
    ])
    return clear_imports_btn, file_input, import_btn


@app.cell
def handle_file_imports(clear_imports_btn, file_input, import_btn):
    """Handle File Imports"""
    import os
    import tempfile
    from pathlib import Path

    import_status = []
    imported_objects = []

    # Import files when button is clicked
    if import_btn.value is not None and import_btn.value > 0 and file_input.value:
        for uploaded_file in file_input.value:
            try:
                # Save to temp file
                suffix = Path(uploaded_file.name).suffix
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_file.contents)
                    tmp_path = tmp.name

                # Import based on file extension
                _ext = suffix.lower()

                if _ext == '.gltf' or _ext == '.glb':
                    widget.import_gltf(tmp_path)
                    import_status.append(f"✓ Imported GLTF: {uploaded_file.name}")
                elif _ext in ['.usd', '.usda', '.usdc']:
                    widget.import_usd(tmp_path)
                    import_status.append(f"✓ Imported USD: {uploaded_file.name}")
                elif _ext == '.abc':
                    widget.import_alembic(tmp_path)
                    import_status.append(f"✓ Imported Alembic: {uploaded_file.name}")
                elif _ext == '.obj':
                    import bpy
                    bpy.ops.wm.obj_import(filepath=tmp_path)
                    import_status.append(f"✓ Imported OBJ: {uploaded_file.name}")
                elif _ext == '.fbx':
                    import bpy
                    bpy.ops.import_scene.fbx(filepath=tmp_path)
                    import_status.append(f"✓ Imported FBX: {uploaded_file.name}")
                elif _ext == '.blend':
                    import bpy
                    with bpy.data.libraries.load(tmp_path, link=False) as (data_from, data_to):
                        data_to.objects = data_from.objects
                    for obj in data_to.objects:
                        if obj:
                            bpy.context.collection.objects.link(obj)
                    import_status.append(f"✓ Imported Blender file: {uploaded_file.name}")
                elif _ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.exr', '.hdr']:
                    import bpy
                    # Create plane and apply image as texture
                    bpy.ops.mesh.primitive_plane_add()
                    plane = bpy.context.active_object
                    plane.name = f"Image_{uploaded_file.name}"

                    # Create material with image texture
                    mat = bpy.data.materials.new(name=f"Mat_{uploaded_file.name}")
                    mat.use_nodes = True
                    bsdf = mat.node_tree.nodes["Principled BSDF"]

                    # Load image
                    img = bpy.data.images.load(tmp_path)
                    tex_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
                    tex_node.image = img
                    mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_node.outputs['Color'])

                    plane.data.materials.append(mat)
                    import_status.append(f"✓ Imported image as plane: {uploaded_file.name}")
                else:
                    import_status.append(f"⚠ Unsupported file type: {uploaded_file.name}")

                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except:
                    pass

            except Exception as e:
                import_status.append(f"✗ Failed to import {uploaded_file.name}: {str(e)}")

        # Render after imports
        widget.render()

    # Clear imported objects
    if clear_imports_btn.value is not None and clear_imports_btn.value > 0:
        import bpy
        # Remove all objects except camera and light
        for obj in bpy.data.objects:
            if obj.type not in ['CAMERA', 'LIGHT']:
                bpy.data.objects.remove(obj, do_unlink=True)
        widget.render()
        import_status.append("✓ Cleared all imported objects")

    # Display import status
    if import_status:
        status_text = "\n".join(import_status)
        mo.md(status_text)
    else:
        mo.md("Select files above and click 'Import Selected Files'")
    return


if __name__ == "__main__":
    app.run()
