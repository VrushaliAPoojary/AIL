"""
core/features/models.py

Domain models and contracts for Feature Requests and Enhancements
in the ART Product Resolution System.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone


class FeatureClassification(str, Enum):
    NEW_FEATURE = "NEW_FEATURE"
    ENHANCEMENT = "ENHANCEMENT"


class FeatureStatus(str, Enum):
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    IN_PROGRESS = "IN_PROGRESS"
    IMPLEMENTED = "IMPLEMENTED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"


class AzureSyncStatus(str, Enum):
    NOT_SYNCED = "NOT_SYNCED"
    SYNCED = "SYNCED"
    FAILED = "FAILED"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class FeatureRecord:
    feature_id: str
    title: str
    module: str
    classification: str = FeatureClassification.NEW_FEATURE.value
    status: str = FeatureStatus.PROPOSED.value
    problem_opportunity: str = ""
    current_behavior: str = ""
    proposed_behavior: str = ""
    business_impact: str = ""
    user_experience: str = ""
    acceptance_criteria: List[str] = field(default_factory=list)
    implementation_guidance: str = ""
    related_bugs: List[str] = field(default_factory=list)
    evidence_files: List[Dict[str, Any]] = field(default_factory=list)
    provenance: str = "HUMAN_SUPPLIED"
    priority: int = 2
    azure_work_item_id: Optional[int] = None
    azure_sync_status: str = AzureSyncStatus.NOT_SYNCED.value
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    slug: str = "feature"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature_id": self.feature_id,
            "title": self.title,
            "module": self.module,
            "classification": self.classification,
            "status": self.status,
            "priority": self.priority,
            "problem_opportunity": self.problem_opportunity,
            "current_behavior": self.current_behavior,
            "proposed_behavior": self.proposed_behavior,
            "business_impact": self.business_impact,
            "user_experience": self.user_experience,
            "acceptance_criteria": self.acceptance_criteria,
            "implementation_guidance": self.implementation_guidance,
            "related_bugs": self.related_bugs,
            "evidence_files": self.evidence_files,
            "provenance": self.provenance,
            "azure_work_item_id": self.azure_work_item_id,
            "azure_sync_status": self.azure_sync_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "slug": self.slug,
        }
