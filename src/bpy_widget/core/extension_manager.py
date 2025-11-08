"""
Extension Management for bpy-widget
Direct access to Blender 4.5+ Extensions Platform

The Extensions Platform was introduced in Blender 4.2 and fully integrated in 4.5.
This module provides Python API access to manage extensions programmatically.
"""
import json
import os
import traceback
from pathlib import Path
from typing import Dict, List, Optional

import addon_utils
import bpy
import httpx

try:
    from bl_pkg import repo_cache_store_ensure
except ImportError:
    repo_cache_store_ensure = None

# Direct access to extension repos
def get_repos() -> List:
    """Get all extension repositories"""
    return list(bpy.context.preferences.extensions.repos)

def list_repositories() -> List[Dict]:
    """List all configured repositories"""
    repos = []
    for repo in get_repos():
        repos.append({
            'name': repo.name,
            'enabled': repo.enabled,
            'module': repo.module,
            'directory': repo.directory,
            'use_remote_url': repo.use_remote_url,
            'remote_url': repo.remote_url if repo.use_remote_url else None,
            'source': repo.source,  # 'USER' or 'SYSTEM'
        })
    return repos

def list_extensions(repo_name: Optional[str] = None) -> List[Dict]:
    """List extensions from repositories"""
    extensions = []
    
    # Import bl_pkg directly if available
    try:
        # This is internal but the way to access extension metadata
        if repo_cache_store_ensure is None:
            raise ImportError("bl_pkg not available")
        repo_cache_store = repo_cache_store_ensure()
        
        repos = get_repos()
        for repo_index, pkg_manifest in enumerate(
            repo_cache_store.pkg_manifest_from_local_ensure(
                error_fn=print,
                ignore_missing=True,
            )
        ):
            if pkg_manifest is None:
                continue
                
            repo = repos[repo_index] if repo_index < len(repos) else None
            if repo_name and repo and repo.name != repo_name:
                continue
            
            for pkg_id, item in pkg_manifest.items():
                extensions.append({
                    'id': pkg_id,
                    'name': item.name,
                    'version': item.version,
                    'type': item.type,  # 'add-on', 'theme', etc.
                    'tagline': item.tagline,
                    'repository': repo.name if repo else 'Unknown',
                    'enabled': is_extension_enabled(repo.module if repo else None, pkg_id),
                })
    except ImportError:
        # Fallback - just list enabled extensions
        for addon in bpy.context.preferences.addons:
            if addon.module.startswith('bl_ext.'):
                parts = addon.module.split('.')
                if len(parts) >= 3:
                    extensions.append({
                        'id': parts[2],
                        'repository': parts[1],
                        'enabled': True,
                    })
    
    return extensions

def is_extension_enabled(repo_module: Optional[str], pkg_id: str) -> bool:
    """Check if an extension is enabled"""
    if not repo_module:
        return False
    
    addon_name = f"bl_ext.{repo_module}.{pkg_id}"
    loaded_default, loaded_state = addon_utils.check(addon_name)
    return loaded_default or loaded_state

def enable_extension(repo_module: str, pkg_id: str) -> bool:
    """Enable an extension"""
    addon_name = f"bl_ext.{repo_module}.{pkg_id}"
    bpy.ops.preferences.addon_enable(module=addon_name)
    return True

def disable_extension(repo_module: str, pkg_id: str) -> bool:
    """Disable an extension"""
    addon_name = f"bl_ext.{repo_module}.{pkg_id}"
    bpy.ops.preferences.addon_disable(module=addon_name)
    return True

def sync_repository(repo_index: int = -1) -> bool:
    """Sync a repository to get latest extensions"""
    bpy.ops.extensions.repo_sync(repo_index=repo_index)
    return True

def sync_all_repositories() -> bool:
    """Sync all remote repositories"""
    bpy.ops.extensions.repo_sync_all()
    return True

def install_extension(source: str, pkg_id: str = "", enable_on_install: bool = True, repo_index: int = -1) -> bool:
    """Install extension from URL or local file

    Universal installation method that handles both online URLs and local ZIP files.
    Automatically enables online access if needed.

    Examples:
        # Install from online repository
        install_extension("molecularnodes")

        # Install from direct URL
        install_extension("https://extensions.blender.org/download/...", pkg_id="molecularnodes")

        # Install from local ZIP file
        install_extension("/path/to/extension.zip", pkg_id="my_extension")

    Args:
        source: Package ID, download URL, or local file path
        pkg_id: Package ID (required for URLs and files, optional if source is pkg_id)
        enable_on_install: Enable the extension after installation
        repo_index: Repository index (-1 for auto-select user repo)

    Returns:
        True if installation succeeded
    """
    # Enable online access if needed
    if not bpy.app.online_access:
        try:
            bpy.context.preferences.system.use_online_access = True
            try:
                bpy.ops.wm.save_userpref()
            except:
                pass
            print("⚠ Online access was disabled. Enabled it for this session.")
            print("   To persist: Edit → Preferences → System → Allow Online Access")
        except Exception as e:
            print(f"⚠ Could not enable online access: {e}")

    # Determine source type
    is_url = source.startswith('http://') or source.startswith('https://')
    is_file = os.path.isfile(source) if not is_url else False
    is_pkg_id = not is_url and not is_file

    try:
        # Find writable user repository
        if repo_index == -1:
            repos = get_repos()
            for idx, repo in enumerate(repos):
                if repo.source == 'USER' and not repo.use_remote_url:
                    repo_index = idx
                    break
            if repo_index == -1:
                repo_index = 1

        # Install based on source type
        if is_file:
            # Local file installation
            if not pkg_id:
                print("Error: pkg_id required for file installation")
                return False
            result = bpy.ops.extensions.package_install_files(
                filepath=source,
                repo=get_repos()[repo_index].module,
                enable_on_install=enable_on_install
            )
        elif is_url:
            # URL installation
            if not pkg_id:
                print("Error: pkg_id required for URL installation")
                return False
            result = bpy.ops.extensions.package_install(
                url=source,
                pkg_id=pkg_id,
                enable_on_install=enable_on_install,
                repo_index=repo_index
            )
        else:
            # Package ID - search and install
            results = search_extensions(source, limit=1)
            if not results:
                print(f"Extension not found: {source}")
                return False

            ext = results[0]
            result = bpy.ops.extensions.package_install(
                url=ext['download_url'],
                pkg_id=ext['id'],
                enable_on_install=enable_on_install,
                repo_index=repo_index
            )

        return result == {'FINISHED'}

    except Exception as e:
        print(f"Installation failed: {e}")
        traceback.print_exc()
        return False

def uninstall_extension(pkg_id: str, repo_index: int = -1) -> bool:
    """Uninstall an extension"""
    bpy.ops.extensions.package_uninstall(
        pkg_id=pkg_id,
        repo_index=repo_index
    )
    return True

def upgrade_all_extensions(use_active_only: bool = False) -> bool:
    """Upgrade all extensions to latest versions"""
    bpy.ops.extensions.package_upgrade_all(use_active_only=use_active_only)
    return True

def search_extensions(query: str, limit: int = 50, category: Optional[str] = None) -> List[Dict]:
    """Search extensions online via Blender's native extension cache

    Uses Blender's built-in bl_pkg module to access extension repository data.
    Automatically enables online access if needed.

    Args:
        query: Search query string
        limit: Maximum number of results (default: 50)
        category: Optional category filter (e.g., 'add-on', 'theme')

    Returns:
        List of extension dictionaries with:
        - id: Extension ID
        - name: Display name
        - tagline: Short description
        - version: Version string
        - type: Extension type ('add-on', 'theme', etc.)
        - download_url: Direct download URL
        - homepage_url: Extension homepage URL

    Raises:
        No exceptions raised - returns empty list on error
    """
    # Enable online access if not already enabled
    if not bpy.app.online_access:
        try:
            # Set the preference directly
            bpy.context.preferences.system.use_online_access = True
            # Try to save preferences (may not work in headless mode)
            try:
                bpy.ops.wm.save_userpref()
            except:
                pass  # Ignore errors in headless mode
            print("⚠ Online access was disabled. Enabled it for this session.")
            print("   To persist: Edit → Preferences → System → Allow Online Access")
        except Exception as e:
            print(f"⚠ Could not enable online access: {e}")
            print("   Please enable manually: Edit → Preferences → System → Allow Online Access")
            return []

    try:
        # Use Blender's native bl_pkg module
        if repo_cache_store_ensure is None:
            raise ImportError("bl_pkg not available")

        # Get repository cache
        cache = repo_cache_store_ensure()
        repos = get_repos()

        # Get remote manifests for all repos
        manifests = cache.pkg_manifest_from_remote_ensure(
            error_fn=lambda msg: print(f"Repo sync warning: {msg}"),
            ignore_missing=True
        )

        # Filter by query (client-side search in name and tagline)
        query_lower = query.lower() if query else ''
        filtered = []

        for repo_index, manifest in enumerate(manifests):
            if manifest is None:
                continue

            repo = repos[repo_index] if repo_index < len(repos) else None

            for pkg_id, item in manifest.items():
                name = item.name.lower() if item.name else ''
                tagline = item.tagline.lower() if item.tagline else ''

                # Match query in name, tagline, or ID
                if query_lower in name or query_lower in tagline or query_lower in pkg_id.lower():
                    # Filter by category if specified
                    if category and item.type != category:
                        continue

                    filtered.append({
                        'id': pkg_id,
                        'name': item.name,
                        'tagline': item.tagline,
                        'version': item.version,
                        'type': item.type,
                        'download_url': item.archive_url if hasattr(item, 'archive_url') else '',
                        'homepage_url': item.website if hasattr(item, 'website') else '',
                    })

                    # Limit results
                    if len(filtered) >= limit:
                        break

            if len(filtered) >= limit:
                break

        return filtered

    except ImportError:
        print("bl_pkg module not available - falling back to httpx")
        # Fallback to httpx if bl_pkg is not available
        try:
            api_url = "https://extensions.blender.org/api/v1/extensions/"
            with httpx.Client(timeout=10.0) as client:
                response = client.get(api_url)
                response.raise_for_status()
                data = response.json()

            all_extensions = data.get('data', [])
            query_lower = query.lower() if query else ''
            filtered = []

            for item in all_extensions:
                name = item.get('name', '').lower()
                tagline = item.get('tagline', '').lower()
                ext_id = item.get('id', '').lower()

                if query_lower in name or query_lower in tagline or query_lower in ext_id:
                    if category and item.get('type', '') != category:
                        continue

                    filtered.append({
                        'id': item.get('id', ''),
                        'name': item.get('name', ''),
                        'tagline': item.get('tagline', ''),
                        'version': item.get('version', ''),
                        'type': item.get('type', 'add-on'),
                        'download_url': item.get('archive_url', ''),
                        'homepage_url': item.get('website', ''),
                    })

                    if len(filtered) >= limit:
                        break

            return filtered

        except Exception as e:
            print(f"httpx fallback failed: {e}")
            return []

    except Exception as e:
        print(f"Error searching extensions: {e}")
        traceback.print_exc()
        return []

# Legacy addon support (pre-4.2)
def list_legacy_addons() -> List[Dict]:
    """List legacy addons (not using extension system)"""
    addons = []
    
    for mod in addon_utils.modules():
        # Skip new extensions
        if mod.__name__.startswith('bl_ext.'):
            continue
            
        addons.append({
            'module': mod.__name__,
            'name': mod.bl_info.get('name', mod.__name__),
            'version': '.'.join(str(v) for v in mod.bl_info.get('version', (0, 0, 0))),
            'category': mod.bl_info.get('category', 'Unknown'),
            'enabled': addon_utils.check(mod.__name__)[1],
        })
    
    return addons

def enable_legacy_addon(module_name: str) -> bool:
    """Enable a legacy addon"""
    bpy.ops.preferences.addon_enable(module=module_name)
    return True

def disable_legacy_addon(module_name: str) -> bool:
    """Disable a legacy addon"""
    bpy.ops.preferences.addon_disable(module=module_name)
    return True
