"""
Curve creation and manipulation utilities
"""
import bpy
import polars as pl
from typing import Optional, List, Union
from pathlib import Path
from .data_readers import read_data_file, auto_detect_columns


def import_dataframe_as_curve(
    df: pl.DataFrame,
    curve_name: str = "DataCurve",
    x_col: str = None,
    y_col: str = None,
    z_col: str = None,
    sort_by: Optional[str] = None
) -> bpy.types.Object:
    """
    Import dataframe as a curve object
    
    Args:
        df: Polars DataFrame
        curve_name: Name for the curve
        x_col, y_col, z_col: Column names for coordinates
        sort_by: Column to sort by before creating curve
        
    Returns:
        The created curve object
    """
    # Auto-detect columns if not specified
    detected = auto_detect_columns(df)
    x_col = x_col or detected.get('x') or detected.get('time')
    y_col = y_col or detected.get('y') or detected.get('value')
    z_col = z_col or detected.get('z')
    
    # Sort if requested
    if sort_by and sort_by in df.columns:
        df = df.sort(sort_by)
    elif x_col and x_col in df.columns:
        df = df.sort(x_col)
    
    # Get coordinate data
    x_data = df[x_col].to_numpy() if x_col and x_col in df.columns else list(range(len(df)))
    y_data = df[y_col].to_numpy() if y_col and y_col in df.columns else [0.0] * len(df)
    z_data = df[z_col].to_numpy() if z_col and z_col in df.columns else [0.0] * len(df)
    
    # Create curve
    curve = bpy.data.curves.new(name=curve_name, type='CURVE')
    curve.dimensions = '3D'
    
    # Create spline
    spline = curve.splines.new('NURBS')
    spline.points.add(len(df) - 1)
    
    # Set points
    for i, (x, y, z) in enumerate(zip(x_data, y_data, z_data)):
        point = spline.points[i]
        point.co = (float(x), float(y), float(z), 1.0)
    
    # Create object
    obj = bpy.data.objects.new(curve_name, curve)
    bpy.context.collection.objects.link(obj)
    
    return obj


def import_multiple_series(
    file_path: Union[str, Path],
    value_columns: List[str],
    x_col: Optional[str] = None,
    spacing: float = 2.0,
    **read_kwargs
) -> List[bpy.types.Object]:
    """
    Import multiple data series as separate curves
    
    Args:
        file_path: Path to data file
        value_columns: List of column names to import as separate series
        x_col: Column for X axis (shared)
        spacing: Spacing between curves in Y direction
        **read_kwargs: Arguments for reading the file
        
    Returns:
        List of created curve objects
    """
    df = read_data_file(Path(file_path), **read_kwargs)
    
    curves = []
    for i, col in enumerate(value_columns):
        if col in df.columns:
            curve = import_dataframe_as_curve(
                df,
                curve_name=f"Series_{col}",
                x_col=x_col,
                y_col=col,
                z_col=None
            )
            # Offset each curve
            curve.location.y = i * spacing
            curves.append(curve)
    
    return curves
