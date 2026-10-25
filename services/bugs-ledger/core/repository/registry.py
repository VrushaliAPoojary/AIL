"""
core/repository/registry.py

Authoritative Master Module Registry for ART Product Validation & Feature Backlog.
Single source of truth for:
- Canonical Azure DevOps Module Names
- Filesystem Storage Keys
- Local Filesystem Directory Names
- Azure Backlog Feature Work Item IDs (under Epic #69099)
- Canonical Feature Identity Module Codes (e.g. AGENT, ORCHESTRATOR)
- Input Aliases & Normalization
"""

from typing import Dict, List, Optional, NamedTuple


class ModuleDefinition(NamedTuple):
    canonical_name: str
    filesystem_key: str
    folder_name: str
    azure_feature_id: int
    azure_feature_title: str
    azure_epic_id: int
    module_code: str


AZURE_BACKLOG_EPIC_ID: int = 69099
AZURE_BACKLOG_EPIC_TITLE: str = "Backlog Tickets"


# Authoritative 12-Module Hierarchy matching Azure DevOps Backlog Tickets #69099
MODULE_DEFINITIONS: List[ModuleDefinition] = [
    ModuleDefinition(
        canonical_name="Agent Lab",
        filesystem_key="agent-lab",
        folder_name="Agent Lab",
        azure_feature_id=69102,
        azure_feature_title="Agent Lab",
        azure_epic_id=AZURE_BACKLOG_EPIC_ID,
        module_code="AGENT",
    ),
    ModuleDefinition(
        canonical_name="Orchestrator",
        filesystem_key="orchestrator",
        folder_name="Orchestrator",
        azure_feature_id=69103,
        azure_feature_title="Orchestrator",
        azure_epic_id=AZURE_BACKLOG_EPIC_ID,
        module_code="ORCHESTRATOR",
    ),
    ModuleDefinition(
        canonical_name="Tool Builder",
        filesystem_key="tool-builder",
        folder_name="Tool Builder",
        azure_feature_id=69104,
        azure_feature_title="Tool Builder",
        azure_epic_id=AZURE_BACKLOG_EPIC_ID,
        module_code="TOOL",
    ),
    ModuleDefinition(
        canonical_name="MCP Servers",
        filesystem_key="mcp-servers",
        folder_name="MCP Servers",
        azure_feature_id=69105,
        azure_feature_title="MCP Servers",
        azure_epic_id=AZURE_BACKLOG_EPIC_ID,
        module_code="MCP",
    ),
    ModuleDefinition(
        canonical_name="Triggers",
        filesystem_key="triggers",
        folder_name="Triggers",
        azure_feature_id=69106,
        azure_feature_title="Triggers",
        azure_epic_id=AZURE_BACKLOG_EPIC_ID,
        module_code="TRIGGER",
    ),
    ModuleDefinition(
        canonical_name="Credential Manager",
        filesystem_key="credential-manager",
        folder_name="Credential Manager",
        azure_feature_id=69107,
        azure_feature_title="Credential Manager",
        azure_epic_id=AZURE_BACKLOG_EPIC_ID,
        module_code="CREDENTIAL",
    ),
    ModuleDefinition(
        canonical_name="Serverless Functions",
        filesystem_key="serverless-functions",
        folder_name="Serverless Functions",
        azure_feature_id=69108,
        azure_feature_title="Serverless Functions",
        azure_epic_id=AZURE_BACKLOG_EPIC_ID,
        module_code="SFN",
    ),
    ModuleDefinition(
        canonical_name="Governance",
        filesystem_key="governance",
        folder_name="Governance",
        azure_feature_id=69109,
        azure_feature_title="Governance",
        azure_epic_id=AZURE_BACKLOG_EPIC_ID,
        module_code="GOV",
    ),
    ModuleDefinition(
        canonical_name="Human-in-the-Loop / Approvals",
        filesystem_key="human-in-the-loop-approvals",
        folder_name="Human-in-the-Loop - Approvals",
        azure_feature_id=69110,
        azure_feature_title="Human-in-the-Loop / Approvals",
        azure_epic_id=AZURE_BACKLOG_EPIC_ID,
        module_code="HIL",
    ),
    ModuleDefinition(
        canonical_name="Live Connect",
        filesystem_key="live-connect",
        folder_name="Live Connect",
        azure_feature_id=69111,
        azure_feature_title="Live Connect",
        azure_epic_id=AZURE_BACKLOG_EPIC_ID,
        module_code="LIVE",
    ),
    ModuleDefinition(
        canonical_name="ART Development Kit (ADK)",
        filesystem_key="art-development-kit-adk",
        folder_name="ART Development Kit (ADK)",
        azure_feature_id=69112,
        azure_feature_title="ART Development Kit (ADK)",
        azure_epic_id=AZURE_BACKLOG_EPIC_ID,
        module_code="ADK",
    ),
    ModuleDefinition(
        canonical_name="Agent X",
        filesystem_key="agent-x",
        folder_name="Agent X",
        azure_feature_id=69113,
        azure_feature_title="Agent X",
        azure_epic_id=AZURE_BACKLOG_EPIC_ID,
        module_code="AGENTX",
    ),
]

# Canonical mappings indexed by canonical name
MODULE_REGISTRY: Dict[str, ModuleDefinition] = {
    m.canonical_name: m for m in MODULE_DEFINITIONS
}

# Filesystem key to module mapping (for round-trip: canonical -> filesystem_key -> canonical)
FILESYSTEM_KEY_TO_MODULE: Dict[str, ModuleDefinition] = {
    m.filesystem_key: m for m in MODULE_DEFINITIONS
}

# Folder name to module mapping
FOLDER_TO_MODULE: Dict[str, ModuleDefinition] = {
    m.folder_name: m for m in MODULE_DEFINITIONS
}

# Approved input aliases (case-insensitive keys mapping to canonical module names)
APPROVED_ALIASES: Dict[str, str] = {
    # Agent Lab
    "AGENT LAB": "Agent Lab",
    "AGENT": "Agent Lab",
    "AGENTLAB": "Agent Lab",
    "AGENT-LAB": "Agent Lab",
    # Orchestrator
    "ORCHESTRATOR": "Orchestrator",
    "ORC": "Orchestrator",
    # Tool Builder
    "TOOL BUILDER": "Tool Builder",
    "TOOL": "Tool Builder",
    "TOOLBUILDER": "Tool Builder",
    "TB": "Tool Builder",
    # MCP Servers
    "MCP SERVERS": "MCP Servers",
    "MCP": "MCP Servers",
    # Triggers
    "TRIGGERS": "Triggers",
    "TRIGGER": "Triggers",
    # Credential Manager
    "CREDENTIAL MANAGER": "Credential Manager",
    "CREDENTIAL": "Credential Manager",
    "CREDENTIALS": "Credential Manager",
    "CRED": "Credential Manager",
    "CREDS": "Credential Manager",
    # Serverless Functions
    "SERVERLESS FUNCTIONS": "Serverless Functions",
    "SERVERLESS": "Serverless Functions",
    "SFN": "Serverless Functions",
    # Governance
    "GOVERNANCE": "Governance",
    "GOV": "Governance",
    # Human-in-the-Loop / Approvals
    "HUMAN-IN-THE-LOOP / APPROVALS": "Human-in-the-Loop / Approvals",
    "HUMAN-IN-THE-LOOP - APPROVALS": "Human-in-the-Loop / Approvals",
    "HUMAN-IN-THE-LOOP": "Human-in-the-Loop / Approvals",
    "HUMAN IN THE LOOP": "Human-in-the-Loop / Approvals",
    "HUMAN IN LOOP": "Human-in-the-Loop / Approvals",
    "HUMAN-IN-LOOP": "Human-in-the-Loop / Approvals",
    "HITL": "Human-in-the-Loop / Approvals",
    "HIL": "Human-in-the-Loop / Approvals",
    "APPROVALS": "Human-in-the-Loop / Approvals",
    # Live Connect
    "LIVE CONNECT": "Live Connect",
    "LIVE": "Live Connect",
    # ART Development Kit (ADK)
    "ART DEVELOPMENT KIT (ADK)": "ART Development Kit (ADK)",
    "ART DEPLOYMENT KIT (ADK)": "ART Development Kit (ADK)",
    "ADK": "ART Development Kit (ADK)",
    "ART ADK": "ART Development Kit (ADK)",
    "DEVELOPMENT KIT": "ART Development Kit (ADK)",
    # Agent X
    "AGENT X": "Agent X",
    "AGENTX": "Agent X",
}


def resolve_canonical_module(name_or_alias: Optional[str]) -> str:
    """
    Resolves any valid canonical name, filesystem key, folder name, or approved alias
    to the exact canonical module name.
    Fails closed: raises ValueError if the input is unknown or empty.
    """
    if not name_or_alias or not isinstance(name_or_alias, str):
        raise ValueError(f"Module name must be a non-empty string, got: {name_or_alias!r}")

    clean = name_or_alias.strip()
    if not clean:
        raise ValueError("Module name cannot be blank or whitespace.")

    # 1. Exact canonical name match
    if clean in MODULE_REGISTRY:
        return clean

    # 2. Exact filesystem key match
    if clean.lower() in FILESYSTEM_KEY_TO_MODULE:
        return FILESYSTEM_KEY_TO_MODULE[clean.lower()].canonical_name

    # 3. Exact folder name match
    if clean in FOLDER_TO_MODULE:
        return FOLDER_TO_MODULE[clean].canonical_name

    # 4. Approved alias match (case-insensitive)
    norm = clean.upper()
    if norm in APPROVED_ALIASES:
        return APPROVED_ALIASES[norm]

    # 5. Case-insensitive canonical match
    for m in MODULE_DEFINITIONS:
        if m.canonical_name.upper() == norm:
            return m.canonical_name

    raise ValueError(f"Unsupported or unknown feature module: '{name_or_alias}'")


def get_filesystem_key(module_name: str) -> str:
    """
    Resolves canonical module to its deterministic filesystem storage key.
    Fails closed if the module is unknown.
    """
    canonical = resolve_canonical_module(module_name)
    return MODULE_REGISTRY[canonical].filesystem_key


def get_azure_feature_id(module_name: str) -> int:
    """
    Resolves canonical module to its verified Azure Feature Work Item ID under Epic #69099.
    Fails closed if the module is unknown.
    """
    canonical = resolve_canonical_module(module_name)
    return MODULE_REGISTRY[canonical].azure_feature_id


def get_module_folder(module_name: str) -> str:
    """
    Resolves canonical module to its filesystem directory folder name.
    Fails closed if the module is unknown.
    """
    canonical = resolve_canonical_module(module_name)
    return MODULE_REGISTRY[canonical].folder_name


def get_module_code(module_name: str) -> str:
    """
    Resolves canonical module to its Feature ID module code (e.g. AGENT, ORCHESTRATOR).
    Fails closed if the module is unknown.
    """
    canonical = resolve_canonical_module(module_name)
    return MODULE_REGISTRY[canonical].module_code


def get_canonical_modules() -> List[str]:
    """Returns the ordered list of all 12 approved canonical module names."""
    return [m.canonical_name for m in MODULE_DEFINITIONS]


def get_canonical_feature_folders() -> List[str]:
    """Returns the ordered list of all 12 canonical filesystem folder names."""
    return [m.folder_name for m in MODULE_DEFINITIONS]


def get_canonical_filesystem_keys() -> List[str]:
    """Returns the ordered list of all 12 canonical filesystem storage keys."""
    return [m.filesystem_key for m in MODULE_DEFINITIONS]


def get_module_definition(module_name: str) -> ModuleDefinition:
    """Retrieves the full ModuleDefinition record for a canonical module."""
    canonical = resolve_canonical_module(module_name)
    return MODULE_REGISTRY[canonical]
