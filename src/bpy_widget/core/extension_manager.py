"""
Extension Management for bpy-widget
Direct access to Blender 4.2+ Extensions Platform
"""
import bpy
from pathlib import Path
from typing import List, Dict, Optional
import os

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
        from bl_pkg import repo_cache_store_ensure
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
        import addon_utils
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
    
    import addon_utils
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

def install_from_file(filepath: str, repo_module: str, enable_on_install: bool = True) -> bool:
    """Install extension from local file"""
    bpy.ops.extensions.package_install_files(
        filepath=filepath,
        repo=repo_module,
        enable_on_install=enable_on_install
    )
    return True

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

# Legacy addon support (pre-4.2)
def list_legacy_addons() -> List[Dict]:
    """List legacy addons (not using extension system)"""
    import addon_utils
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
