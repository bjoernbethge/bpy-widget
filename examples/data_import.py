#!/usr/bin/env python
"""
BPY Widget - Data Import Example

Data visualization capabilities:
- Import CSV/Parquet files as point clouds
- Create curves from time series data
- Batch import multiple files
- Apply materials to data visualizations

Run with: marimo run examples/data_import.py
"""

import marimo

__generated_with = "0.17.6"
app = marimo.App()

with app.setup:
    """Setup widget and data directory"""
    from pathlib import Path

    import marimo as mo
    import numpy as np
    import polars as pl

    from bpy_widget import BpyWidget

    widget = BpyWidget(width=800, height=600)
    data_dir = Path("sample_data")
    data_dir.mkdir(exist_ok=True)


@app.cell
def viewport():
    """Main Viewport"""
    widget
    return


@app.cell
def create_sample_data():
    """Generate sample datasets"""
    # Spiral dataset
    t = np.linspace(0, 4 * np.pi, 100)
    spiral_data = pl.DataFrame({
        'x': np.cos(t) * t / 4,
        'y': np.sin(t) * t / 4,
        'z': t / 4,
        'value': np.sin(t * 2),
        'category': ['A' if i < 50 else 'B' for i in range(100)]
    })
    spiral_data.write_csv(data_dir / "spiral.csv")

    # Random point cloud
    n_points = 500
    point_cloud = pl.DataFrame({
        'x': np.random.randn(n_points),
        'y': np.random.randn(n_points),
        'z': np.random.randn(n_points) * 0.5,
        'intensity': np.random.rand(n_points)
    })
    point_cloud.write_parquet(data_dir / "points.parquet")

    # Time series
    time_series = pl.DataFrame({
        'time': range(50),
        'signal1': np.sin(np.linspace(0, 2*np.pi, 50)) * 10,
        'signal2': np.cos(np.linspace(0, 2*np.pi, 50)) * 8,
        'signal3': np.sin(np.linspace(0, 4*np.pi, 50)) * 6
    })
    time_series.write_csv(data_dir / "timeseries.csv")

    mo.md(f"""
    **Sample Data Created:**
    - spiral.csv ({len(spiral_data)} points)
    - points.parquet ({len(point_cloud)} points)
    - timeseries.csv ({len(time_series)} rows)
    """)
    return


@app.cell
def import_options():
    """Import Options"""
    import_type = mo.ui.dropdown(
        options=["points", "series", "batch"],
        value="points",
        label="Import Type"
    )

    file_dropdown = mo.ui.dropdown(
        options=["spiral.csv", "points.parquet", "timeseries.csv"],
        value="spiral.csv",
        label="File"
    )

    mo.vstack([
        mo.md("**Import Data**"),
        import_type,
        file_dropdown,
    ])
    return file_dropdown, import_type


@app.cell
def apply_import(file_dropdown, import_type):
    """Apply Import based on selection"""
    file_path = data_dir / file_dropdown.value

    widget.clear_scene()
    widget.setup_lighting()
    widget.setup_world_background(color=(0.02, 0.02, 0.05))

    if import_type.value == "points":
        collection = widget.import_data(
            file_path,
            as_type="points",
            point_size=0.05,
            x_col="x",
            y_col="y",
            z_col="z",
            color_col="value" if "spiral" in file_dropdown.value else None
        )
        if collection and collection.objects:
            for obj in collection.objects:
                point_mat = widget.create_material(
                    "PointMaterial",
                    emission_color=(0.3, 0.7, 1.0),
                    emission_strength=2.0
                )
                widget.assign_material(obj, point_mat)
        widget.setup_camera(distance=12, target=(0, 0, 2))

    elif import_type.value == "series":
        curves = widget.import_data(
            file_path,
            as_type="series",
            value_columns=["signal1", "signal2", "signal3"],
            x_col="time",
            spacing=5.0
        )
        colors = [(1, 0.2, 0.2), (0.2, 1, 0.2), (0.2, 0.2, 1)]
        for curve, color in zip(curves, colors):
            curve_mat = widget.create_material(
                f"Curve_{curve.name}",
                emission_color=color,
                emission_strength=3.0
            )
            widget.assign_material(curve, curve_mat)

    elif import_type.value == "batch":
        collections = widget.batch_import(
            [str(data_dir / "*.csv"), str(data_dir / "*.parquet")],
            collection_prefix="Data",
            point_size=0.03
        )
        for i, collection in enumerate(collections):
            if collection.objects:
                for obj in collection.objects:
                    obj.location.x += i * 5
        widget.setup_camera(distance=20, target=(5, 0, 0))

    widget.render()
    return


@app.cell
def visualization_controls():
    """Visualization Controls"""
    point_size = mo.ui.slider(
        start=0.01, stop=0.2, value=0.05, step=0.01,
        label="Point Size"
    )

    emission_strength = mo.ui.slider(
        start=0.0, stop=10.0, value=2.0, step=0.5,
        label="Emission Strength"
    )

    mo.vstack([
        mo.md("**Visualization**"),
        point_size,
        emission_strength,
    ])
    return (emission_strength,)


@app.cell
def apply_viz_settings(emission_strength):
    """Apply Visualization Settings"""
    # Update emission strength for all emission materials
    for material in widget.data.materials:
        if material.use_nodes:
            bsdf = material.node_tree.nodes.get("Principled BSDF")
            if bsdf and bsdf.inputs.get("Emission Strength"):
                bsdf.inputs["Emission Strength"].default_value = (
                    emission_strength.value
                )

    widget.render()
    return


@app.cell
def scene_info():
    """Scene Info"""
    mo.md(f"""
    **Scene:** {len(widget.objects)} objects |
    {len(widget.data.materials)} materials |
    Status: {widget.status}
    """)
    return


if __name__ == "__main__":
    app.run()
