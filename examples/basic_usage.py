import marimo

__generated_with = "0.14.10"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
    # BPY Widget Demo - Clean API

    🐵 Interactive Blender rendering with EEVEE Next!

    **Features:**
    - Mouse drag to orbit camera
    - Scroll wheel to zoom
    - Real-time rendering updates
    - Clean functional API
    """
    )
    return


@app.cell(hide_code=True)
def _():
    from bpy_widget import BpyWidget

    # Create widget with clean functional approach
    widget = BpyWidget(width=800, height=600)

    # Display the widget
    widget
    return (widget,)


@app.cell
def _(widget):
    # Debug information
    widget.debug_info()
    return


@app.cell
def _(widget):
    # Access scene for advanced operations
    scene = widget.scene
    objects = widget.objects
    
    print(f"Scene has {len(objects)} objects:")
    for name, obj in objects.items():
        print(f"  - {name}: {obj.type}")
    return objects, scene


if __name__ == "__main__":
    app.run()
