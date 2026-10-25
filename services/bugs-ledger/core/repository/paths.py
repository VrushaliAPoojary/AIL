"""
core/repository/paths.py

Canonical Azure DevOps Feature structure and storage path resolution.
Mirrors the Azure DevOps hierarchy using the authoritative master registry.
"""

import os
from typing import List, Dict, Optional, Any

from core.repository.registry import (
    MODULE_DEFINITIONS,
    MODULE_REGISTRY,
    APPROVED_ALIASES,
    resolve_canonical_module,
    get_filesystem_key,
    get_module_folder,
    get_module_code,
    get_azure_feature_id,
    get_canonical_modules,
    get_canonical_feature_folders,
)


# 1. Canonical list of all 12 Azure DevOps Features
CANONICAL_FEATURES: List[str] = get_canonical_modules()

# 2. Canonical mapping from Feature Name / Filesystem Key to Filesystem-Safe Feature Directory Name
FEATURE_TO_FOLDER_MAP: Dict[str, str] = {
    m.canonical_name: m.folder_name for m in MODULE_DEFINITIONS
}
for m in MODULE_DEFINITIONS:
    FEATURE_TO_FOLDER_MAP[m.folder_name] = m.folder_name
    FEATURE_TO_FOLDER_MAP[m.filesystem_key] = m.folder_name

# 3. Canonical directory names of all 12 feature folders for bug storage
CANONICAL_FEATURE_FOLDERS: List[str] = [
    "Agent Lab",
    "Orchestrator",
    "Tool Builder",
    "MCP Servers",
    "Triggers",
    "Credential Manager",
    "Serverless Functions",
    "Governance",
    "Human-in-the-Loop - Approvals",
    "Live Connect",
    "ART Deployment Kit (ADK)",
    "Agent X",
]

# 4. Supported aliases and module abbreviations (case-insensitive lookup)
FEATURE_ALIASES: Dict[str, str] = dict(APPROVED_ALIASES)


def get_canonical_features() -> List[str]:
    """
    Returns a copy of the canonical Azure DevOps features list.
    Exposed from one location so future ticket-generation and Azure mapping logic can reuse it.
    """
    return list(CANONICAL_FEATURES)


def get_canonical_feature_folders() -> List[str]:
    """
    Returns a copy of the canonical filesystem-safe feature directory names.
    """
    return list(CANONICAL_FEATURE_FOLDERS)


def resolve_feature_folder(feature: str) -> str:
    """
    Resolves a feature name, filesystem key, or alias to its canonical filesystem directory name.
    Fails closed: raises ValueError if the feature is unknown or unsupported.
    """
    if not feature or not isinstance(feature, str):
        raise ValueError(f"Feature must be a non-empty string, got: {feature!r}")

    clean = feature.strip()
    if not clean:
        raise ValueError("Feature must not be empty or whitespace.")

    try:
        canonical_name = resolve_canonical_module(clean)
        return get_module_folder(canonical_name)
    except ValueError:
        raise ValueError(f"Unsupported or unknown feature: '{feature}'")


class BugStoragePath(str):
    """
    A path string representing a resolved bug storage directory.
    Behaves as a string while providing flexible equality checking with or without trailing slash.
    """
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return super().__eq__(other) or self.rstrip("/") == other.rstrip("/")
        return super().__eq__(other)

    def __hash__(self) -> int:
        return hash(self.rstrip("/"))


def resolve_bug_storage_path(
    feature: str,
    bug_id: str,
    base_dir: Optional[str] = None
) -> BugStoragePath:
    """
    Resolves the canonical bug storage path under its Azure DevOps feature folder.
    
    Pattern:
    bugs/<canonical-feature-folder>/<bug_id>/
    
    Or if base_dir is supplied:
    <base_dir>/<canonical-feature-folder>/<bug_id>/
    
    Fails closed (raises ValueError) if feature is unsupported or unknown.
    """
    if not bug_id or not isinstance(bug_id, str):
        raise ValueError(f"bug_id must be a non-empty string, got: {bug_id!r}")

    clean_bug_id = bug_id.strip().strip("/")
    if not clean_bug_id:
        raise ValueError("bug_id cannot be empty or only slashes.")

    folder_name = resolve_feature_folder(feature)
    if folder_name == "ART Development Kit (ADK)":
        folder_name = "ART Deployment Kit (ADK)"

    if base_dir:
        clean_base = base_dir.rstrip("/")
        path = f"{clean_base}/{folder_name}/{clean_bug_id}/"
    else:
        path = f"bugs/{folder_name}/{clean_bug_id}/"

    return BugStoragePath(path)


class FeatureStoragePath(str):
    """
    A path string representing a resolved feature storage directory.
    Behaves as a string while providing flexible equality checking with or without trailing slash.
    """
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return super().__eq__(other) or self.rstrip("/") == other.rstrip("/")
        return super().__eq__(other)

    def __hash__(self) -> int:
        return hash(self.rstrip("/"))


def resolve_feature_storage_path(
    feature: str,
    feature_id: str,
    slug: Optional[str] = None,
    base_dir: Optional[str] = None
) -> FeatureStoragePath:
    """
    Resolves the canonical feature storage path under its Azure DevOps feature folder.
    
    Pattern:
    features/<canonical-feature-folder>/<feature_id>__<slug>/
    or if slug is None:
    features/<canonical-feature-folder>/<feature_id>/
    
    Or if base_dir is supplied:
    <base_dir>/<canonical-feature-folder>/<feature_id>__<slug>/
    
    Fails closed (raises ValueError) if feature is unsupported or unknown.
    """
    if not feature_id or not isinstance(feature_id, str):
        raise ValueError(f"feature_id must be a non-empty string, got: {feature_id!r}")

    clean_feature_id = feature_id.strip().strip("/")
    if not clean_feature_id:
        raise ValueError("feature_id cannot be empty or only slashes.")

    folder_name = resolve_feature_folder(feature)
    dir_name = f"{clean_feature_id}__{slug.strip()}" if slug and slug.strip() else clean_feature_id

    if base_dir:
        clean_base = base_dir.rstrip("/")
        path = f"{clean_base}/{folder_name}/{dir_name}/"
    else:
        path = f"features/{folder_name}/{dir_name}/"

    return FeatureStoragePath(path)
