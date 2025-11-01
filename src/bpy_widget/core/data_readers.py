"""
Data reading utilities for various formats using Polars
"""
import polars as pl
from pathlib import Path
from typing import Optional, List


def read_data_file(file_path: Path, **kwargs) -> pl.DataFrame:
    """Read various data formats using Polars"""
    suffix = file_path.suffix.lower()
    
    readers = {
        '.csv': pl.read_csv,
        '.parquet': pl.read_parquet,
        '.json': pl.read_json,
        '.xlsx': pl.read_excel,
        '.xls': pl.read_excel,
        '.feather': pl.read_ipc,
        '.arrow': pl.read_ipc,
        '.avro': pl.read_avro,
    }
    
    reader = readers.get(suffix, pl.read_csv)  # Default to CSV
    return reader(file_path, **kwargs)


def detect_coordinate_column(df: pl.DataFrame, possible_names: List[str]) -> Optional[str]:
    """Auto-detect coordinate column from common names"""
    columns = df.columns
    for name in possible_names:
        if name in columns:
            return name
    return None


def auto_detect_columns(df: pl.DataFrame) -> dict:
    """Auto-detect common column types"""
    return {
        'x': detect_coordinate_column(df, ['x', 'X', 'x_coord', 'x_pos', 'longitude', 'lon']),
        'y': detect_coordinate_column(df, ['y', 'Y', 'y_coord', 'y_pos', 'latitude', 'lat']),
        'z': detect_coordinate_column(df, ['z', 'Z', 'z_coord', 'z_pos', 'elevation', 'height', 'altitude']),
        'time': detect_coordinate_column(df, ['time', 't', 'timestamp', 'date', 'datetime']),
        'value': detect_coordinate_column(df, ['value', 'val', 'y', 'Y', 'measurement']),
        'color': detect_coordinate_column(df, ['color', 'col', 'hue', 'category', 'class', 'label']),
    }
