"""
core/identity/generator.py

Phase 01E — Pure Identity Generator
Implements deterministic, isolated generation rules for:
1. Investigation IDs: INV-<YYYYMMDD>-<4-DIGIT-SEQUENCE>
2. Confirmed ART Bug IDs: ART-<MODULE>-<3-DIGIT-SEQUENCE>
3. Evidence IDs: EVD-<UUID12>

Concurrency Notice:
This module provides pure candidate ID generation from a supplied set of existing IDs.
It does not guarantee multi-process atomic allocation; atomicity must be enforced at the
persistence/transaction boundary in later phases.
"""

import re
import uuid
from typing import Set, Iterable, Optional
from datetime import datetime, timezone

# Canonical approved module codes recognized from repository evidence
CANONICAL_MODULES = {
    "AGENT", "GOV", "SFN", "ORCHESTRATOR", "ORC", "TOOL", "TOOLBUILDER",
    "AGENTX", "ADK", "MCP", "TRIGGER", "TRIGGERS", "CRED", "CREDENTIAL",
    "CREDENTIALS", "LIVE", "HIL"
}

from core.repository.registry import (
    MODULE_DEFINITIONS,
    MODULE_REGISTRY,
    APPROVED_ALIASES,
)

FEATURE_MODULE_CODES = {
    m.canonical_name.upper(): m.module_code for m in MODULE_DEFINITIONS
}
for m in MODULE_DEFINITIONS:
    FEATURE_MODULE_CODES[m.canonical_name] = m.module_code
    FEATURE_MODULE_CODES[m.filesystem_key.upper()] = m.module_code
    FEATURE_MODULE_CODES[m.filesystem_key] = m.module_code
for alias, canon in APPROVED_ALIASES.items():
    FEATURE_MODULE_CODES[alias] = MODULE_REGISTRY[canon].module_code

# Patterns
INV_ID_REGEX = re.compile(r"^INV-(?P<date>\d{8})-(?P<seq>\d{4})$")
BUG_ID_REGEX = re.compile(r"^ART-(?P<mod>[A-Z]+)-(?P<seq>\d{3})$")
FEAT_ID_REGEX = re.compile(r"^ART-FEAT-(?P<mod>[A-Z]+)-(?P<seq>\d{3})$")
EVD_ID_REGEX = re.compile(r"^EVD-[A-Z0-9]{12}$")


def generate_investigation_id(existing_ids: Iterable[str], date_str: Optional[str] = None) -> str:
    """
    Generates the next available Investigation ID for a given date in format:
    INV-<YYYYMMDD>-<4-DIGIT-SEQUENCE>
    
    If date_str is omitted, current UTC date in YYYYMMDD is used.
    Existing allocated IDs are inspected to select the next sequential number.
    """
    if not date_str:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    else:
        if not re.match(r"^\d{8}$", date_str):
            raise ValueError(f"Invalid date_str format '{date_str}'. Expected YYYYMMDD.")

    highest_seq = 0
    for eid in existing_ids:
        if not isinstance(eid, str):
            continue
        m = INV_ID_REGEX.match(eid.strip())
        if m and m.group("date") == date_str:
            seq = int(m.group("seq"))
            if seq > highest_seq:
                highest_seq = seq

    next_seq = highest_seq + 1
    if next_seq > 9999:
        raise OverflowError(f"Sequence overflow for date {date_str}. Exceeded 9999.")

    candidate_id = f"INV-{date_str}-{next_seq:04d}"
    if candidate_id in existing_ids:
        raise ValueError(f"Candidate ID '{candidate_id}' already exists in allocated set.")
    return candidate_id


def generate_bug_id(
    module: str,
    existing_ids: Iterable[str],
    approved_modules: Optional[Set[str]] = None,
    prefix: str = "ART",
    is_test: bool = False
) -> str:
    """
    Generates the next sequential Canonical ART Bug ID:
    ART-<MODULE>-<3-DIGIT-SEQUENCE> or TEST-ART-<MODULE>-<3-DIGIT-SEQUENCE>
    
    Rules:
    - Scoped by module code (e.g. AGENT, GOV, SFN).
    - Module must be in the approved_modules set (defaults to CANONICAL_MODULES).
    - 'Not provided' or unapproved modules are strictly rejected.
    - Never reuses an existing ID.
    - Test/harness records can specify is_test=True or prefix='TEST-ART' to isolate from production canonical ART IDs.
    """
    valid_modules = approved_modules if approved_modules is not None else CANONICAL_MODULES

    if not module or not isinstance(module, str):
        raise ValueError("Module must be a non-empty string.")

    module_norm = module.strip().upper()
    if module_norm not in valid_modules or module_norm == "NOT PROVIDED":
        raise ValueError(f"Module '{module}' is not an approved canonical module code. Allowed: {sorted(list(valid_modules))}")

    effective_prefix = "TEST-ART" if is_test else (prefix or "ART").strip().upper()
    regex = re.compile(rf"^{re.escape(effective_prefix)}-(?P<mod>[A-Z]+)-(?P<seq>\d{{3}})$")

    highest_seq = 0
    for eid in existing_ids:
        if not isinstance(eid, str):
            continue
        m = regex.match(eid.strip())
        if m and m.group("mod") == module_norm:
            seq = int(m.group("seq"))
            if seq > highest_seq:
                highest_seq = seq

    next_seq = highest_seq + 1
    if next_seq > 999:
        raise OverflowError(f"Sequence overflow for module '{module_norm}'. Exceeded 999.")

    candidate_id = f"{effective_prefix}-{module_norm}-{next_seq:03d}"
    if candidate_id in existing_ids:
        raise ValueError(f"Candidate ID '{candidate_id}' already exists in allocated set.")
    return candidate_id


def generate_feature_id(
    module: str,
    existing_ids: Iterable[str],
    approved_modules: Optional[Set[str]] = None,
    prefix: str = "ART-FEAT",
    is_test: bool = False
) -> str:
    """
    Generates the next sequential Canonical ART Feature ID:
    ART-FEAT-<MODULE>-<3-DIGIT-SEQUENCE> or TEST-ART-FEAT-<MODULE>-<3-DIGIT-SEQUENCE>
    
    Rules:
    - Scoped by module code (e.g. AGENT, GOV, SFN, ORCHESTRATOR).
    - Module may be passed as module code or full feature name; resolved via FEATURE_MODULE_CODES.
    - Module must be in the approved_modules set (defaults to CANONICAL_MODULES).
    - Never reuses an existing ID.
    - Test/harness records can specify is_test=True or prefix='TEST-ART-FEAT'.
    """
    valid_modules = approved_modules if approved_modules is not None else CANONICAL_MODULES

    if not module or not isinstance(module, str):
        raise ValueError("Module must be a non-empty string.")

    raw_mod = module.strip().upper()
    module_norm = FEATURE_MODULE_CODES.get(raw_mod, raw_mod)
    if module_norm not in valid_modules or module_norm == "NOT PROVIDED":
        raise ValueError(f"Module '{module}' is not an approved canonical module code. Allowed: {sorted(list(valid_modules))}")

    effective_prefix = "TEST-ART-FEAT" if is_test else (prefix or "ART-FEAT").strip().upper()
    regex = re.compile(rf"^{re.escape(effective_prefix)}-(?P<mod>[A-Z]+)-(?P<seq>\d{{3}})$")

    highest_seq = 0
    for eid in existing_ids:
        if not isinstance(eid, str):
            continue
        m = regex.match(eid.strip())
        if m and m.group("mod") == module_norm:
            seq = int(m.group("seq"))
            if seq > highest_seq:
                highest_seq = seq

    next_seq = highest_seq + 1
    if next_seq > 999:
        raise OverflowError(f"Sequence overflow for feature module '{module_norm}'. Exceeded 999.")

    candidate_id = f"{effective_prefix}-{module_norm}-{next_seq:03d}"
    if candidate_id in existing_ids:
        raise ValueError(f"Candidate Feature ID '{candidate_id}' already exists in allocated set.")
    return candidate_id


def generate_evidence_id(existing_ids: Optional[Iterable[str]] = None) -> str:
    """
    Generates a collision-resistant, stable Evidence ID independent of investigation or bug promotion:
    EVD-<12-CHAR-HEX>
    """
    allocated = set(existing_ids or [])
    while True:
        candidate = f"EVD-{uuid.uuid4().hex[:12].upper()}"
        if candidate not in allocated:
            return candidate
