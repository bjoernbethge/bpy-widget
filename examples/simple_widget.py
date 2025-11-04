#!/usr/bin/env python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo>=0.17.0",
#     "pyzmq",
# ]
# ///
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

    # Display widget - automatic initialization happens via auto_init=True and __repr__
    widget
    return


if __name__ == "__main__":
    app.run()
