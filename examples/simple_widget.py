#!/usr/bin/env python
"""
Simple BPY Widget Demo

Minimal example showing just the interactive 3D widget.
Run with: marimo run examples/simple_widget.py
"""

import marimo

__generated_with = "0.17.6"
app = marimo.App()


@app.cell
def main():
    """Main cell - create and display widget"""
    import marimo as mo

    from bpy_widget import BpyWidget

    # Create widget
    widget = BpyWidget(width=800, height=600)

    # Show title
    mo.md("""
    # Simple BPY Widget Demo

    **Interactive 3D Viewport**
    - Drag to rotate camera
    - Scroll to zoom
    """)

    # Show info
    mo.md(f"""
    **Widget Status:** {widget.status}

    **Scene Info:**
    - Objects: {len(widget.objects)}
    - Camera: {widget.camera.name if widget.camera else 'None'}
    - Active Object: {widget.active_object.name if widget.active_object else 'None'}
    """)

    # Ensure widget is rendered before display
    if not widget.is_initialized:
        widget.initialize()

    # Force a render
    widget._update_camera_and_render()

    # Display widget
    widget


if __name__ == "__main__":
    app.run()
