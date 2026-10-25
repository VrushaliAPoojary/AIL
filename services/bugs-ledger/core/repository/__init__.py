"""
core/repository/__init__.py
"""

from core.repository.registry import (
    ModuleDefinition,
    MODULE_DEFINITIONS,
    MODULE_REGISTRY,
    FILESYSTEM_KEY_TO_MODULE,
    APPROVED_ALIASES,
    AZURE_BACKLOG_EPIC_ID,
    AZURE_BACKLOG_EPIC_TITLE,
    resolve_canonical_module,
    get_filesystem_key,
    get_module_folder,
    get_module_code,
    get_azure_feature_id,
    get_canonical_modules,
    get_canonical_feature_folders,
    get_canonical_filesystem_keys,
    get_module_definition,
)

from core.repository.paths import (
    CANONICAL_FEATURES,
    CANONICAL_FEATURE_FOLDERS,
    FEATURE_TO_FOLDER_MAP,
    FEATURE_ALIASES,
    BugStoragePath,
    FeatureStoragePath,
    resolve_feature_folder,
    resolve_bug_storage_path,
    resolve_feature_storage_path,
)

from core.repository.writer import (
    format_azure_devops_section,
    append_or_update_azure_section,
    render_ledger,
)

__all__ = [
    "ModuleDefinition",
    "MODULE_DEFINITIONS",
    "MODULE_REGISTRY",
    "FILESYSTEM_KEY_TO_MODULE",
    "APPROVED_ALIASES",
    "AZURE_BACKLOG_EPIC_ID",
    "AZURE_BACKLOG_EPIC_TITLE",
    "resolve_canonical_module",
    "get_filesystem_key",
    "get_module_folder",
    "get_module_code",
    "get_azure_feature_id",
    "get_canonical_modules",
    "get_canonical_feature_folders",
    "get_canonical_filesystem_keys",
    "get_module_definition",
    "CANONICAL_FEATURES",
    "CANONICAL_FEATURE_FOLDERS",
    "FEATURE_TO_FOLDER_MAP",
    "FEATURE_ALIASES",
    "BugStoragePath",
    "FeatureStoragePath",
    "resolve_feature_folder",
    "resolve_bug_storage_path",
    "resolve_feature_storage_path",
    "format_azure_devops_section",
    "append_or_update_azure_section",
    "render_ledger",
]
