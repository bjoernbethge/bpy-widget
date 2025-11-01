#!/usr/bin/env python
"""
BPY Widget - Data Import Example

This example demonstrates data visualization capabilities:
- Import CSV/Parquet files as point clouds
- Create curves from time series data
- Batch import multiple files
- Apply materials to data visualizations

Run with: marimo edit examples/data_import.py
"""

from pathlib import Path

import marimo as mo
import numpy as np
import polars as pl

# Create app
app = mo.App()

# Cell 1: Setup and sample data
@app.cell
def setup():
    """Create widget and sample data"""
    from pathlib import Path

    import numpy as np
    import polars as pl

    from bpy_widget import BpyWidget
    
    # Create widget
    widget = BpyWidget(width=800, height=600)
    
    # Create sample data directory
    data_dir = Path("sample_data")
    data_dir.mkdir(exist_ok=True)
    
    mo.md("""
    # Data Import Example
    
    This example shows how to import and visualize data in 3D.
    We'll create some sample data files and import them as point clouds and curves.
    """)
    
    return widget, pl, np, Path, data_dir

# Cell 2: Create sample datasets
@app.cell
def create_sample_data(pl, np, data_dir):
    """Generate sample CSV and Parquet files"""
    
    # Create spiral dataset
    t = np.linspace(0, 4 * np.pi, 100)
    spiral_data = pl.DataFrame({
        'x': np.cos(t) * t / 4,
        'y': np.sin(t) * t / 4,
        'z': t / 4,
        'value': np.sin(t * 2),
        'category': ['A' if i < 50 else 'B' for i in range(100)]
    })
    spiral_data.write_csv(data_dir / "spiral.csv")
    
    # Create random point cloud
    n_points = 500
    point_cloud = pl.DataFrame({
        'x': np.random.randn(n_points),
        'y': np.random.randn(n_points),
        'z': np.random.randn(n_points) * 0.5,
        'intensity': np.random.rand(n_points)
    })
    point_cloud.write_parquet(data_dir / "points.parquet")
    
    # Create time series
    time_series = pl.DataFrame({
        'time': range(50),
        'signal1': np.sin(np.linspace(0, 2*np.pi, 50)) * 10,
        'signal2': np.cos(np.linspace(0, 2*np.pi, 50)) * 8,
        'signal3': np.sin(np.linspace(0, 4*np.pi, 50)) * 6
    })
    time_series.write_csv(data_dir / "timeseries.csv")
    
    mo.md(f"""
    ## Sample Data Created
    
    Created 3 sample datasets in `{data_dir}`:
    - **spiral.csv**: 3D spiral with categories
    - **points.parquet**: Random point cloud with intensity
    - **timeseries.csv**: Multiple time series signals
    """)
    
    return spiral_data, point_cloud, time_series

# Cell 3: Import as point cloud
@app.cell
def import_points(widget, data_dir):
    """Import data as point cloud"""
    
    mo.md("""
    ## Point Cloud Visualization
    
    Import the spiral data as a point cloud:
    """)
    
    # Clear scene
    widget.clear_scene()
    widget.setup_lighting()
    widget.setup_world_background(color=(0.02, 0.02, 0.05))
    
    # Import spiral as points
    collection = widget.import_data(
        data_dir / "spiral.csv",
        as_type="points",
        point_size=0.05,
        x_col="x",
        y_col="y", 
        z_col="z",
        color_col="value"
    )
    
    # Add camera
    widget.setup_camera(distance=12, target=(0, 0, 2))
    
    # Apply emission material to points
    if collection and collection.objects:
        for obj in collection.objects:
            mat = widget.create_material(
                "PointMaterial",
                emission_color=(0.3, 0.7, 1.0),
                emission_strength=2.0
            )
            widget.assign_material(obj, mat)
    
    widget.render()
    
    mo.md(f"""
    ✓ Imported spiral.csv as point cloud
    - Points: 100
    - Colored by: value column
    - Status: {widget.status}
    """)

# Cell 4: Import as curve
@app.cell
def import_curve(widget, data_dir):
    """Import time series as curves"""
    
    mo.md("""
    ## Time Series as Curves
    
    Import multiple time series as 3D curves:
    """)
    
    # Import multiple series
    curves = widget.import_data(
        data_dir / "timeseries.csv",
        as_type="series",
        value_columns=["signal1", "signal2", "signal3"],
        x_col="time",
        spacing=5.0  # Space between curves
    )
    
    # Apply different materials to each curve
    colors = [(1, 0.2, 0.2), (0.2, 1, 0.2), (0.2, 0.2, 1)]
    
    for curve, color in zip(curves, colors):
        mat = widget.create_material(
            f"Curve_{curve.name}",
            emission_color=color,
            emission_strength=3.0
        )
        widget.assign_material(curve, mat)
    
    widget.render()
    
    mo.md(f"""
    ✓ Imported timeseries.csv as curves
    - Series: {len(curves)}
    - Each curve represents one signal
    - Status: {widget.status}
    """)
    
    return curves

# Cell 5: Batch import
@app.cell
def batch_import(widget, data_dir):
    """Demonstrate batch import"""
    
    mo.md("""
    ## Batch Import
    
    Import multiple files at once:
    """)
    
    # Clear and setup
    widget.clear_scene()
    widget.setup_lighting()
    widget.setup_world_background()
    
    # Batch import all CSV and Parquet files
    collections = widget.batch_import(
        [str(data_dir / "*.csv"), str(data_dir / "*.parquet")],
        collection_prefix="Data",
        point_size=0.03
    )
    
    # Position collections
    for i, collection in enumerate(collections):
        if collection.objects:
            for obj in collection.objects:
                obj.location.x += i * 5  # Spread out horizontally
    
    # Setup camera to see all
    widget.setup_camera(distance=20, target=(5, 0, 0))
    widget.render()
    
    mo.md(f"""
    ✓ Batch imported {len(collections)} files
    - Each file in separate collection
    - Collections spread horizontally
    - Status: {widget.status}
    """)
    
    return collections

# Cell 6: Data with metadata
@app.cell
def import_with_metadata(widget, data_dir):
    """Import data with metadata preservation"""
    
    mo.md("""
    ## Metadata Preservation
    
    Import data while preserving metadata as custom properties:
    """)
    
    # Import with metadata
    collection = widget.import_data_with_metadata(
        data_dir / "points.parquet",
        metadata_columns=["intensity"],
        collection_name="PointsWithMeta",
        point_size=0.02
    )
    
    # Display metadata
    if collection:
        metadata = {
            "Source": collection.get("source_file", "Unknown"),
            "Rows": collection.get("row_count", 0),
            "Columns": collection.get("column_count", 0),
            "Intensity Mean": f"{collection.get('meta_intensity_mean', 0):.3f}",
            "Intensity Min": f"{collection.get('meta_intensity_min', 0):.3f}",
            "Intensity Max": f"{collection.get('meta_intensity_max', 0):.3f}",
        }
        
        metadata_text = "\n".join([f"- **{k}:** {v}" for k, v in metadata.items()])
        
        mo.md(f"""
        ### Metadata from points.parquet:
        
        {metadata_text}
        
        Custom properties are stored on the collection and can be accessed later.
        """)

# Cell 7: Interactive data controls
@app.cell
def data_controls(widget):
    """Interactive controls for data visualization"""
    
    point_size = mo.ui.slider(
        start=0.01, stop=0.2, value=0.05, step=0.01,
        label="Point Size"
    )
    
    emission_strength = mo.ui.slider(
        start=0.0, stop=10.0, value=2.0, step=0.5,
        label="Emission Strength"
    )
    
    mo.md("""
    ## Visualization Controls
    
    Adjust visualization parameters:
    """)
    
    controls = mo.vstack([point_size, emission_strength])
    
    return point_size, emission_strength, controls

# Cell 8: Apply visualization settings
@app.cell
def apply_viz_settings(point_size, emission_strength, widget):
    """Apply visualization control settings"""
    
    if point_size.value:
        # Update point sizes (would need to recreate geometry nodes)
        pass
    
    if emission_strength.value:
        # Update emission strength for all emission materials
        for mat in widget.data.materials:
            if mat.use_nodes:
                bsdf = mat.node_tree.nodes.get("Principled BSDF")
                if bsdf and bsdf.inputs.get("Emission Strength"):
                    bsdf.inputs["Emission Strength"].default_value = emission_strength.value
        
        widget.render()
    
    mo.md(f"""
    Visualization updated:
    - Point Size: {point_size.value}
    - Emission: {emission_strength.value}
    """)

# Cell 9: Convenience Properties Demo
@app.cell
def convenience_demo(widget):
    """Show convenience properties for data work"""
    mo.md("""
    ## Convenience Properties for Data Work

    Easy access to Blender internals when working with imported data:
    """)

    # Show current state
    info = f"""
    **Scene Status:**
    - Total Objects: `{len(widget.objects)}`
    - Active Object: `{widget.active_object.name if widget.active_object else 'None'}`
    - Selected Objects: `{len(widget.selected_objects)}`
    - Available Materials: `{len(widget.data.materials)}`

    **Quick Access Examples:**
    ```python
    # Instead of bpy.context.scene
    scene = widget.scene

    # Instead of bpy.context.active_object
    active = widget.active_object

    # Instead of bpy.data.materials
    materials = widget.data.materials

    # Instead of bpy.context.selected_objects
    selected = widget.selected_objects

    # Instead of bpy.ops
    widget.ops.object.select_all(action='DESELECT')
    ```
    """

    mo.md(info)

    return info

# Cell 10: Export options
@app.cell
def export_options(widget, data_dir):
    """Show export capabilities"""
    
    mo.md("""
    ## Export Options
    
    Export the visualized data in various formats:
    
    ```python
    # Export as 3D model
    widget.export_gltf(data_dir / "visualization.glb")
    
    # Export scene data as Parquet
    widget.export_scene_as_parquet(data_dir / "scene_data.parquet")
    
    # Export as USD for use in other 3D applications
    widget.export_usd(data_dir / "visualization.usd")
    ```
    
    The exported files preserve:
    - Object positions and transformations
    - Material properties
    - Collection structure
    - Custom properties (in Parquet export)
    """)

# Cell 11: Tips
@app.cell
def tips():
    """Data visualization tips"""
    
    mo.md("""
    ## Tips for Data Visualization
    
    ### Performance
    - Use Parquet format for large datasets (faster loading)
    - Limit point cloud size to <10,000 points for interactive performance
    - Use `CYCLES` engine for high-quality renders of data
    
    ### Visual Design
    - Use emission materials for data points to make them visible
    - Apply color gradients based on data values
    - Space multiple datasets using collections
    
    ### Data Preparation
    - Ensure coordinate columns are numeric
    - Normalize data to reasonable 3D space (-10 to 10)
    - Use categories for color mapping
    
    ### Advanced Features
    ```python
    # Custom column detection
    widget.import_data(
        "data.csv",
        x_col="longitude",
        y_col="latitude", 
        z_col="elevation",
        color_col="temperature"
    )
    
    # Merge multiple imports
    from bpy_widget.core.data_import import merge_imported_collections
    merged = merge_imported_collections(collections, "AllData")
    ```
    """)

if __name__ == "__main__":
    app.run()
