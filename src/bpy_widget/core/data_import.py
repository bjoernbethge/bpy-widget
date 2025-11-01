"""
Data import functionality - Simplified and DRY
"""
import glob
import bpy
import polars as pl
from pathlib import Path
from typing import Union, Optional, List

from .data_readers import read_data_file, auto_detect_columns
from .point_cloud import create_points_from_dataframe
from .curve_utils import import_dataframe_as_curve, import_multiple_series

# Re-export for compatibility
__all__ = [
    'import_data_as_points',
    'batch_import_data',
    'import_data_with_metadata',
    'import_dataframe_as_curve',
    'import_multiple_series',
    'merge_imported_collections',
    'read_data_file',
]


def import_data_as_points(
    file_path: Union[str, Path],
    collection_name: str = "ImportedData",
    point_size: float = 0.1,
    x_col: Optional[str] = None,
    y_col: Optional[str] = None, 
    z_col: Optional[str] = None,
    color_col: Optional[str] = None,
    **read_kwargs
) -> bpy.types.Collection:
    """
    Import data from various formats and create point cloud in Blender
    
    Args:
        file_path: Path to data file (CSV, Parquet, JSON, Excel, etc.)
        collection_name: Name for the new collection
        point_size: Size of each point
        x_col: Column name for X coordinate (auto-detect if None)
        y_col: Column name for Y coordinate (auto-detect if None)
        z_col: Column name for Z coordinate (auto-detect if None)
        color_col: Column name for color values (optional)
        **read_kwargs: Additional arguments for Polars read functions
        
    Returns:
        The created collection containing the point cloud
    """
    file_path = Path(file_path)
    
    # Read data based on file extension
    df = read_data_file(file_path, **read_kwargs)
    
    # Auto-detect coordinate columns if not specified
    detected = auto_detect_columns(df)
    x_col = x_col or detected.get('x')
    y_col = y_col or detected.get('y')
    z_col = z_col or detected.get('z')
    color_col = color_col or detected.get('color')
    
    # Create collection
    collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(collection)
    
    # Create points from data
    create_points_from_dataframe(df, collection, x_col, y_col, z_col, color_col, point_size)
    
    return collection


def batch_import_data(
    file_patterns: List[str],
    collection_prefix: str = "Batch",
    **kwargs
) -> List[bpy.types.Collection]:
    """
    Import multiple data files at once
    
    Args:
        file_patterns: List of file patterns (supports wildcards)
        collection_prefix: Prefix for collection names
        **kwargs: Additional arguments passed to import_data_as_points
        
    Returns:
        List of created collections
    """
    collections = []
    
    for i, pattern in enumerate(file_patterns):
        for file_path in glob.glob(pattern):
            try:
                file_name = Path(file_path).stem
                collection_name = f"{collection_prefix}_{i:03d}_{file_name}"
                
                collection = import_data_as_points(
                    file_path,
                    collection_name=collection_name,
                    **kwargs
                )
                collections.append(collection)
                print(f"✓ Imported: {file_path}")
                
            except Exception as e:
                print(f"✗ Failed: {file_path}: {e}")
    
    print(f"Batch complete: {len(collections)} files imported")
    return collections


def import_data_with_metadata(
    file_path: Union[str, Path],
    metadata_columns: Optional[List[str]] = None,
    **kwargs
) -> bpy.types.Collection:
    """
    Import data with metadata stored as custom properties
    
    Args:
        file_path: Path to data file
        metadata_columns: Columns to store as metadata
        **kwargs: Arguments for import_data_as_points
        
    Returns:
        Collection with metadata attached
    """
    file_path = Path(file_path)
    
    # Import the data normally
    collection = import_data_as_points(file_path, **kwargs)
    
    # Read the data again for metadata
    df = read_data_file(file_path)
    
    # Store file info as custom properties
    collection["source_file"] = str(file_path)
    collection["row_count"] = len(df)
    collection["column_count"] = len(df.columns)
    collection["columns"] = df.columns
    
    # Store metadata columns if specified
    if metadata_columns:
        for col in metadata_columns:
            if col in df.columns:
                # Store summary statistics for numeric columns
                if df[col].dtype in [pl.Float32, pl.Float64, pl.Int32, pl.Int64]:
                    collection[f"meta_{col}_mean"] = float(df[col].mean())
                    collection[f"meta_{col}_min"] = float(df[col].min())
                    collection[f"meta_{col}_max"] = float(df[col].max())
                    collection[f"meta_{col}_std"] = float(df[col].std())
                else:
                    # For non-numeric, store unique count
                    collection[f"meta_{col}_unique"] = df[col].n_unique()
    
    return collection


def merge_imported_collections(
    collections: List[bpy.types.Collection],
    merged_name: str = "MergedData"
) -> bpy.types.Collection:
    """
    Merge multiple collections into a single collection
    
    Args:
        collections: List of collections to merge
        merged_name: Name for the merged collection
        
    Returns:
        The merged collection
    """
    # Create new collection
    merged = bpy.data.collections.new(merged_name)
    bpy.context.scene.collection.children.link(merged)
    
    # Move all objects to merged collection
    for col in collections:
        for obj in col.objects:
            merged.objects.link(obj)
            col.objects.unlink(obj)
        
        # Remove empty collection
        bpy.data.collections.remove(col)
    
    return merged
