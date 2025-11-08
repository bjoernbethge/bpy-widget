"""
Copy missing datafiles (OCIO config, LUTs, fonts) from bundled package to bpy package
"""
import shutil
import site
import sys
import zipfile
from pathlib import Path
from typing import Tuple

import bpy
from loguru import logger


def get_package_datafiles_zip() -> Path:
    """Get path to datafiles ZIP archive bundled with this package"""
    package_dir = Path(__file__).parent.parent
    return package_dir / "datafiles.zip"


def get_package_datafiles_path() -> Path:
    """Get path to extracted datafiles directory (temporary cache)
    
    If ZIP exists, extracts it to a cache directory on first access.
    """
    package_dir = Path(__file__).parent.parent
    zip_path = package_dir / "datafiles.zip"
    cache_dir = package_dir / "_datafiles_cache"
    
    # If ZIP exists, extract to cache if needed
    if zip_path.exists():
        # Check if extraction is needed (ZIP contains 'datafiles/' root)
        extracted_datafiles = cache_dir / "datafiles"
        if not cache_dir.exists() or not extracted_datafiles.exists():
            try:
                logger.debug("Extracting datafiles from ZIP...")
                cache_dir.mkdir(exist_ok=True)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(cache_dir)
                logger.debug("Datafiles extracted successfully")
            except Exception as e:
                logger.error(f"Failed to extract datafiles ZIP: {e}")
                return package_dir / "datafiles"  # Fallback to directory if it exists
        
        # ZIP extracts with 'datafiles/' root, so return that subdirectory
        if extracted_datafiles.exists():
            return extracted_datafiles
    
    # Return cache if it exists (even if empty)
    if cache_dir.exists():
        return cache_dir
    
    # Final fallback: check if datafiles directory exists
    datafiles_dir = package_dir / "datafiles"
    if datafiles_dir.exists():
        return datafiles_dir
    
    return cache_dir  # Return cache_dir even if empty (will fail later)


def get_bpy_datafiles_path(require_bpy_import: bool = True) -> Path:
    """Get path to bpy package datafiles
    
    bpy looks for datafiles at: .../bpy/4.5/datafiles
    This is where we need to copy the files, even if the directory doesn't exist yet.
    
    Args:
        require_bpy_import: If True, import bpy to find path. If False, try to find path
            without importing bpy (may return None if not found).
    """
    if require_bpy_import:
        
        # Get bpy installation path
        bpy_module_path = Path(bpy.__file__).parent
        # bpy.__file__ is usually: .../bpy/4.5/scripts/modules/bpy/__init__.py
        # bpy looks for datafiles at: .../bpy/4.5/datafiles
        # So we need to go up from .../bpy/4.5/scripts/modules/bpy to .../bpy/4.5
        
        # Go up: bpy -> modules -> scripts -> 4.5
        bpy_base = bpy_module_path.parent.parent.parent  # .../bpy/4.5
        datafiles = bpy_base / "datafiles"
        
        return datafiles
    else:
        # Try to find bpy path without importing it
        
        # Check common site-packages locations
        search_paths = site.getsitepackages()
        if site.getusersitepackages():
            search_paths.append(site.getusersitepackages())
        
        for site_packages in search_paths:
            if not site_packages:
                continue
            
            bpy_path = Path(site_packages) / "bpy"
            if not bpy_path.exists():
                continue
            
            # Look for version directories (4.5, etc.)
            for version_dir in sorted(bpy_path.glob("4.*"), reverse=True):
                # bpy looks for datafiles at: .../bpy/4.5/datafiles
                datafiles = version_dir / "datafiles"
                # Return path even if it doesn't exist yet (we'll create it)
                return datafiles
        
        # If not found, raise error - don't fallback to import (defeats the purpose)
        raise ValueError("Could not determine bpy datafiles path without importing bpy")


def copy_ocio_config(source_path: Path, bpy_datafiles: Path, force: bool = False) -> bool:
    """Copy OCIO config.ocio to bpy package"""
    try:
        # Find OCIO config in bundled package
        ocio_path = source_path / "colormanagement" / "config.ocio"
        
        if not ocio_path.exists():
            logger.warning(f"OCIO config not found: {ocio_path}")
            return False
        
        # Target path in bpy
        target_dir = bpy_datafiles / "colormanagement"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / "config.ocio"
        
        # Skip if already exists and not forcing
        if target_file.exists() and not force:
            return False  # Not copied, already exists
        
        # Copy file
        shutil.copy2(ocio_path, target_file)
        return True
        
    except Exception as e:
        logger.error(f"Failed to copy OCIO config: {e}")
        return False


def copy_ocio_luts(source_path: Path, bpy_datafiles: Path, force: bool = False) -> bool:
    """Copy OCIO LUT files (luts/ and filmic/ directories) to bpy package"""
    try:
        source_colormanagement = source_path / "colormanagement"
        target_colormanagement = bpy_datafiles / "colormanagement"
        
        if not source_colormanagement.exists():
            return False
        
        copied = 0
        
        # Copy luts/ directory
        source_luts = source_colormanagement / "luts"
        target_luts = target_colormanagement / "luts"
        
        if source_luts.exists():
            target_luts.mkdir(parents=True, exist_ok=True)
            for lut_file in source_luts.iterdir():
                if lut_file.is_file():
                    target_file = target_luts / lut_file.name
                    if not target_file.exists() or force:
                        shutil.copy2(lut_file, target_file)
                        copied += 1
        
        # Copy filmic/ directory
        source_filmic = source_colormanagement / "filmic"
        target_filmic = target_colormanagement / "filmic"
        
        if source_filmic.exists():
            target_filmic.mkdir(parents=True, exist_ok=True)
            for lut_file in source_filmic.iterdir():
                if lut_file.is_file():
                    target_file = target_filmic / lut_file.name
                    if not target_file.exists() or force:
                        shutil.copy2(lut_file, target_file)
                        copied += 1
        
        return copied > 0
        
    except Exception as e:
        logger.error(f"Failed to copy OCIO LUTs: {e}")
        return False


def copy_fonts(source_path: Path, bpy_datafiles: Path, force: bool = False) -> bool:
    """Copy missing fonts to bpy package"""
    try:
        # Find fonts in bundled package
        fonts_path = source_path / "fonts"
        
        if not fonts_path.exists():
            logger.warning(f"Fonts directory not found: {fonts_path}")
            return False
        
        # Target directory in bpy
        target_fonts = bpy_datafiles / "fonts"
        target_fonts.mkdir(parents=True, exist_ok=True)
        
        # Copy missing font files
        required_fonts = ["DejaVuSansMono.woff2", "Inter.woff2"]
        copied = 0
        
        for font_file in required_fonts:
            source = fonts_path / font_file
            target = target_fonts / font_file
            
            if source.exists():
                if not target.exists() or force:
                    shutil.copy2(source, target)
                    copied += 1
        
        return copied > 0
        
    except Exception as e:
        logger.error(f"Failed to copy fonts: {e}")
        return False


def setup_datafiles(force: bool = False) -> Tuple[bool, bool]:
    """
    Copy missing datafiles (OCIO config, LUTs, fonts) to bpy package.
    
    Copies from bundled package datafiles (always available after installation).
    Tries to find bpy path without importing it first to avoid font warnings.
    
    Args:
        force: If True, overwrite existing files
        
    Returns:
        Tuple of (ocio_copied, fonts_copied) booleans
    """
    try:
        # Get bpy datafiles path (try without import first to avoid warnings)
        try:
            bpy_datafiles = get_bpy_datafiles_path(require_bpy_import=False)
        except (ValueError, Exception):
            # Fallback to import if we can't find path otherwise
            try:
                bpy_datafiles = get_bpy_datafiles_path(require_bpy_import=True)
            except Exception as e:
                logger.error(f"Cannot access bpy datafiles path: {e}")
                return False, False
        
        if not bpy_datafiles.exists():
            bpy_datafiles.mkdir(parents=True, exist_ok=True)
        
        # Try to get bundled package datafiles (from ZIP or directory)
        try:
            package_datafiles = get_package_datafiles_path()
            source_path = package_datafiles
            
            if not source_path.exists():
                # Package datafiles not available - this should not happen after installation
                logger.error("Bundled package datafiles not found. Package may be incorrectly installed.")
                return False, False
        except Exception as e:
            logger.error(f"Failed to get package datafiles: {e}")
            return False, False
        
        # Copy files
        ocio_copied = copy_ocio_config(source_path, bpy_datafiles, force=force)
        if ocio_copied:
            logger.info("OCIO config done")
        
        luts_copied = copy_ocio_luts(source_path, bpy_datafiles, force=force)
        if luts_copied:
            logger.info("OCIO LUTs done")
        
        fonts_copied = copy_fonts(source_path, bpy_datafiles, force=force)
        if fonts_copied:
            logger.info("Fonts done")
        
        return ocio_copied, fonts_copied
        
    except Exception as e:
        logger.error(f"Failed to setup datafiles: {e}")
        return False, False


def setup_datafiles_if_needed():
    """Setup datafiles only if they are missing
    
    Uses bundled package datafiles (always available after installation).
    Tries to find bpy path without importing it first, to avoid font warnings during import.
    """
    try:
        # Try to find path without importing bpy (to avoid warnings)
        try:
            bpy_datafiles = get_bpy_datafiles_path(require_bpy_import=False)
        except (ValueError, Exception):
            # Fallback: import bpy if we can't find path otherwise
            bpy_datafiles = get_bpy_datafiles_path(require_bpy_import=True)
        
        # Check if OCIO config exists
        ocio_config = bpy_datafiles / "colormanagement" / "config.ocio"
        ocio_needed = not ocio_config.exists()
        
        # Check if LUTs exist (check for at least one file in luts/ and filmic/)
        # Note: get_package_datafiles_path() returns path with 'datafiles/' root
        luts_dir = bpy_datafiles / "colormanagement" / "luts"
        filmic_dir = bpy_datafiles / "colormanagement" / "filmic"
        
        luts_needed = False
        try:
            if not luts_dir.exists() or not list(luts_dir.glob("*.*")):
                luts_needed = True
            elif not filmic_dir.exists() or not list(filmic_dir.glob("*.*")):
                luts_needed = True
        except Exception:
            luts_needed = True
        
        # Check if fonts exist
        fonts_dir = bpy_datafiles / "fonts"
        required_fonts = ["DejaVuSansMono.woff2", "Inter.woff2"]
        fonts_needed = False
        for font in required_fonts:
            if not (fonts_dir / font).exists():
                fonts_needed = True
                break
        
        if ocio_needed or luts_needed or fonts_needed:
            logger.info("Configuring datafiles...")
            # setup_datafiles will try without bpy import first automatically
            return setup_datafiles()
        else:
            # All datafiles present - no action needed
            # Don't log here to avoid Marimo export issues with structured logs
            return False, False
            
    except Exception:
        # If we can't check, don't try to copy
        return False, False

