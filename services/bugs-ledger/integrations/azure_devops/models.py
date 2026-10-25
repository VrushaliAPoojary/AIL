"""
integrations/azure_devops/models.py

Typed models for Azure DevOps integration.
Contains configuration, patch request structures, and work item responses.
"""

import os
import json
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass(frozen=True)
class AzureDevOpsConfig:
    organization: str
    project: str
    pat: str
    api_version: str = "7.0"
    timeout_seconds: float = 15.0
    assigned_to: Optional[str] = None

    @classmethod
    def from_env(cls, env: Optional[Dict[str, str]] = None) -> "AzureDevOpsConfig":
        import os
        source = dict(os.environ) if env is None else dict(env)

        # Automatically load from local .env if env was None and keys not already set in environ
        if env is None:
            candidate_env_paths = [
                os.path.join(os.getcwd(), ".env"),
                os.path.join(os.getcwd(), "services", "bugs-ledger", ".env"),
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")),
            ]
            for env_file_path in candidate_env_paths:
                if os.path.exists(env_file_path):
                    try:
                        with open(env_file_path, "r", encoding="utf-8") as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith("#") and "=" in line:
                                    k, v = line.split("=", 1)
                                    k, v = k.strip(), v.strip()
                                    if k == "AZURE_DEVOPS_ASSIGNED_TO":
                                        continue
                                    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                                        v = v[1:-1]
                                    if k not in source or not source[k]:
                                        source[k] = v
                        break
                    except Exception:
                        pass

        org = source.get("AZURE_DEVOPS_ORGANIZATION", "").strip()
        project = source.get("AZURE_DEVOPS_PROJECT", "").strip()
        pat = source.get("AZURE_DEVOPS_PAT", "").strip()
        api_ver = source.get("AZURE_DEVOPS_API_VERSION", "7.0").strip() or "7.0"
        # Only assign if AZURE_DEVOPS_ASSIGNED_TO is explicitly provided in source (e.g. from callers)
        assigned_to = source.get("AZURE_DEVOPS_ASSIGNED_TO", "").strip() or None


        missing = []
        if not org:
            missing.append("AZURE_DEVOPS_ORGANIZATION")
        if not project:
            missing.append("AZURE_DEVOPS_PROJECT")
        if not pat:
            missing.append("AZURE_DEVOPS_PAT")

        if missing:
            raise ValueError(f"Missing required Azure DevOps configuration: {', '.join(missing)}")

        return cls(
            organization=org,
            project=project,
            pat=pat,
            api_version=api_ver,
            assigned_to=assigned_to
        )


@dataclass(frozen=True)
class AzureWorkItemResult:
    work_item_id: int
    work_item_url: str
    canonical_bug_id: str
    is_existing: bool = False


class AzureDevOpsError(Exception):
    """Base sanitized Azure DevOps integration exception."""
    def __init__(self, code: str, message: str, status_code: int = 502):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class EvidenceSyncError(AzureDevOpsError):
    """Raised when an evidence file fails Azure DevOps synchronization."""
    def __init__(self, filename: str, reason: str, status_code: int = 502):
        self.filename = filename
        self.reason = reason
        message = f"EVIDENCE_SYNC_FAILED: {filename} — {reason}"
        super().__init__(code="EVIDENCE_SYNC_FAILED", message=message, status_code=status_code)


# Confirmed Epic ID for Bug Bounty
AZURE_BUG_BOUNTY_EPIC_ID: int = 68782

# Confirmed Feature Work Item IDs under Epic 68782 (ART - Internal Bug Bounty)
AZURE_MODULE_FEATURE_MAP: Dict[str, int] = {
    "Agent Lab": 68783,
    "Orchestrator": 68806,
    "Tool Builder": 68807,
    "MCP Servers": 68808,
    "Triggers": 68809,
    "Credential Manager": 68810,
    "Serverless Functions": 68811,
    "Governance": 68812,
    "Human-in-the-Loop / Approvals": 68813,
    "Live Connect": 68814,
    "ART Development Kit (ADK)": 68815,
    "Agent X": 68960,
}

from core.repository.registry import (
    AZURE_BACKLOG_EPIC_ID,
    MODULE_DEFINITIONS,
    get_azure_feature_id,
)

AZURE_BACKLOG_MODULE_FEATURE_MAP: Dict[str, int] = {
    m.canonical_name: m.azure_feature_id for m in MODULE_DEFINITIONS
}

# Supported aliases mapping canonical ticket module codes to Azure Feature names
AZURE_MODULE_ALIASES: Dict[str, str] = {
    # Canonical 3-letter codes used in ART Product Resolution System:
    "AGENT": "Agent Lab",
    "SFN": "Serverless Functions",
    "GOV": "Governance",
    "ORC": "Orchestrator",
    "ORCHESTRATOR": "Orchestrator",
    "TOOL": "Tool Builder",
    "TOOLBUILDER": "Tool Builder",
    "TB": "Tool Builder",
    "TOOL BUILDER": "Tool Builder",
    "MCP": "MCP Servers",
    "MCP SERVERS": "MCP Servers",
    "TRIGGER": "Triggers",
    "TRIGGERS": "Triggers",
    "CRED": "Credential Manager",
    "CREDENTIAL": "Credential Manager",
    "CREDENTIALS": "Credential Manager",
    "CREDENTIAL MANAGER": "Credential Manager",
    "SERVERLESS": "Serverless Functions",
    "SERVERLESS FUNCTIONS": "Serverless Functions",
    "GOVERNANCE": "Governance",
    "HIL": "Human-in-the-Loop / Approvals",
    "HUMAN-IN-THE-LOOP": "Human-in-the-Loop / Approvals",
    "HUMAN-IN-THE-LOOP / APPROVALS": "Human-in-the-Loop / Approvals",
    "HUMAN-IN-THE-LOOP - APPROVALS": "Human-in-the-Loop / Approvals",
    "LIVE": "Live Connect",
    "LIVE CONNECT": "Live Connect",
    "ADK": "ART Development Kit (ADK)",
    "ART DEVELOPMENT KIT (ADK)": "ART Development Kit (ADK)",
    "ART DEPLOYMENT KIT (ADK)": "ART Development Kit (ADK)",
    "AGENTX": "Agent X",
    "AGENT X": "Agent X",
    "AGENT LAB": "Agent Lab",
}


class AzureFeatureRouter:
    """
    Dedicated Azure DevOps module-to-Feature routing boundary.
    Fails closed if the module cannot be resolved to an Azure Feature Work Item ID.
    Supports both Bug Bounty (Epic #68782) and Backlog Tickets (Epic #69099).
    """

    @classmethod
    def resolve_feature_id(cls, module_name: Optional[str]) -> int:
        if not module_name or not isinstance(module_name, str):
            raise AzureDevOpsError(
                code="AZURE_PARENT_NOT_CONFIGURED",
                message="Cannot export bug to Azure DevOps: Module is not provided or empty.",
                status_code=400
            )

        norm_key = module_name.strip().upper()
        feature_name = AZURE_MODULE_ALIASES.get(norm_key)
        if not feature_name:
            # Check if exact casing matched AZURE_MODULE_FEATURE_MAP
            for fn in AZURE_MODULE_FEATURE_MAP:
                if fn.upper() == norm_key:
                    feature_name = fn
                    break

        if not feature_name or feature_name not in AZURE_MODULE_FEATURE_MAP:
            raise AzureDevOpsError(
                code="AZURE_PARENT_NOT_CONFIGURED",
                message=f"Cannot export bug to Azure DevOps: No Azure Feature mapping configured for module '{module_name}'.",
                status_code=400
            )

        return AZURE_MODULE_FEATURE_MAP[feature_name]

    @classmethod
    def resolve_backlog_feature_id(cls, module_name: Optional[str]) -> int:
        if not module_name or not isinstance(module_name, str):
            raise AzureDevOpsError(
                code="AZURE_PARENT_NOT_CONFIGURED",
                message="Cannot export feature request to Azure DevOps: Module is not provided or empty.",
                status_code=400
            )

        try:
            return get_azure_feature_id(module_name)
        except ValueError:
            raise AzureDevOpsError(
                code="AZURE_PARENT_NOT_CONFIGURED",
                message=f"Cannot export feature request to Azure DevOps: No Azure Backlog Feature mapping configured for module '{module_name}'.",
                status_code=400
            )


class ArtAssigneeRegistry:
    """
    Deterministic local ART assignee registry and alias resolver.
    Resolves user-facing first-name aliases and full names to verified Azure identities.
    """
    _REGISTRY_PATH = os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")),
        "config/art_assignees.json"
    )

    @classmethod
    def load_registry(cls, registry_path: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        path = registry_path or cls._REGISTRY_PATH
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def resolve_assignee(
        cls,
        user_input: Optional[str],
        registry_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Resolves an optional user-provided assignee string to a verified Azure identity email.
        If user_input is None or empty -> returns None (unassigned is valid).
        If user_input is provided but cannot be resolved -> raises AzureDevOpsError.
        """
        if not user_input or not isinstance(user_input, str):
            return None

        clean_input = user_input.strip()
        if not clean_input:
            return None

        norm_key = clean_input.lower()
        registry = cls.load_registry(registry_path=registry_path)

        # 1. Exact alias match (case-insensitive)
        if norm_key in registry:
            entry = registry[norm_key]
            if entry.get("verified"):
                return entry["azure_identity"]

        # 2. Match against full display name or identity
        for key, entry in registry.items():
            dn = entry.get("display_name", "").strip().lower()
            ident = entry.get("azure_identity", "").strip().lower()
            if norm_key == dn or norm_key == ident:
                if entry.get("verified"):
                    return entry["azure_identity"]

        raise AzureDevOpsError(
            code="ASSIGNEE_NOT_RESOLVED",
            message=f"Cannot assign bug: '{user_input}' could not be resolved uniquely in the ART Assignee Registry.",
            status_code=400
        )

