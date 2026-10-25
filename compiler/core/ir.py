from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from enum import Enum

class EpistemicStatus(str, Enum):
    VERIFIED = "VERIFIED"
    OBSERVED = "OBSERVED"
    DIRECT = "DIRECT"
    TRIANGULATED = "TRIANGULATED"
    RECONSTRUCTED = "RECONSTRUCTED"
    INFERRED = "INFERRED"
    HYPOTHESIS = "HYPOTHESIS"
    PROPOSED = "PROPOSED"
    UNKNOWN = "UNKNOWN"
    UNVERIFIED = "UNVERIFIED"

class TimeScope(str, Enum):
    HISTORICAL = "HISTORICAL"
    CURRENT = "CURRENT"
    FUTURE = "FUTURE"

class WorkflowType(str, Enum):
    OBSERVED_EXISTING = "OBSERVED_EXISTING"
    RECONSTRUCTED = "RECONSTRUCTED"
    PROPOSED_ART = "PROPOSED_ART"

@dataclass
class Provenance:
    file: str
    section: Optional[str] = None
    position: Optional[str] = None  # e.g., line range "L10-L15"

@dataclass
class IRObject:
    id: str
    object_type: str
    title: str
    normalized: str
    raw: str
    epistemic_status: EpistemicStatus
    content_hash: str = ""
    time_scope: Optional[TimeScope] = None
    confidence: Optional[str] = None
    provenance: Optional[Provenance] = None
    parent_id: Optional[str] = None
    child_ids: List[str] = field(default_factory=list)
    related_refs: List[str] = field(default_factory=list)
    source_refs: List[str] = field(default_factory=list)
    
@dataclass
class Source(IRObject):
    url: str = ""
    source_type: str = ""
    publication_date: Optional[str] = None
    publisher: Optional[str] = None

@dataclass
class Metric(IRObject):
    value: float = 0.0
    unit: str = ""
    metric_type: str = ""

@dataclass
class Evidence(IRObject):
    pass

@dataclass
class Claim(IRObject):
    pass

@dataclass
class Decision(IRObject):
    decision_rationale: Optional[str] = None
    unresolved_questions: List[str] = field(default_factory=list)
    next_action: Optional[str] = None

@dataclass
class WorkflowStep(IRObject):
    actor: Optional[str] = None
    system: Optional[str] = None
    handoff_to: Optional[str] = None
    state_information: Optional[str] = None
    exception_refs: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)

@dataclass
class WorkflowModel(IRObject):
    workflow_type: WorkflowType = WorkflowType.OBSERVED_EXISTING
    steps: List[WorkflowStep] = field(default_factory=list)
    actors: List[str] = field(default_factory=list)
    systems: List[str] = field(default_factory=list)
    safety_boundaries: List[str] = field(default_factory=list)

@dataclass
class Checkpoint(IRObject):
    question: Optional[str] = None
    discovered: Optional[str] = None
    state_changed: Optional[str] = None

@dataclass
class Section(IRObject):
    level: int = 1

@dataclass
class Relationship(IRObject):
    source_id: str = ""
    target_id: str = ""
    rel_type: str = ""

@dataclass
class Investigation(IRObject):
    checkpoints: List[Checkpoint] = field(default_factory=list)
    sections: List[Section] = field(default_factory=list)
    workflows: List[WorkflowModel] = field(default_factory=list)
    sources: List[Source] = field(default_factory=list)
    metrics: List[Metric] = field(default_factory=list)
    decisions: List[Decision] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    claims: List[Claim] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)

@dataclass
class IRDocument:
    metadata: Dict[str, str] = field(default_factory=dict)
    investigation: Optional[Investigation] = None
    raw_markdown: str = ""

