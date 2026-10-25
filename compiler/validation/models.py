from typing import List, Optional, Literal, Union
from pydantic import BaseModel, Field

class Provenance(BaseModel):
    source_file: str
    section: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    url: Optional[str] = None

class IntelligenceObject(BaseModel):
    id: str
    type: Literal['WORKFLOW_PATTERN', 'STRATEGY_PATTERN', 'DECISION_PATTERN', 'IMPLEMENTATION_PATTERN', 'ARCHITECTURE_PATTERN', 'GUARDRAIL', 'METRIC_PATTERN', 'RESEARCH_METHOD', 'DESIGN_PRINCIPLE', 'NEGATIVE_INTELLIGENCE', 'ART_IMPROVEMENT']
    title: str
    domain: str
    description: str
    pattern: Optional[str] = None
    lesson: Optional[str] = None
    art_learning: Optional[str] = None
    art_improvement: Optional[str] = None
    conditions: Optional[List[str]] = None
    anti_pattern: Optional[str] = None
    do_not_assume: Optional[Union[List[str], str]] = None
    evidence_status: Literal['VERIFIED', 'PARTIAL', 'HYPOTHESIS', 'UNKNOWN', 'REJECTED']
    status: Literal['ACTIVE', 'EXPERIMENTAL', 'RETIRED']
    confidence: Literal['HIGH', 'MEDIUM', 'LOW']
    reuse_potential: Literal['HIGH', 'MEDIUM', 'LOW']
    applications: List[str]
    source_checkpoint: Optional[str] = None
    source_refs: List[str]
    source_location: Optional[str] = None
    original_source: Optional[str] = None
    tags: List[str]
    provenance: Provenance

class PresentationKeyFinding(BaseModel):
    id: str
    statement: str
    classification: Literal['EVIDENCE', 'CLAIM', 'INFERENCE', 'HYPOTHESIS', 'FALSIFICATION', 'RESULT', 'DECISION']
    source_refs: List[str]

class Presentation(BaseModel):
    investigation_summary: str
    key_findings: List[PresentationKeyFinding]

class Decision(BaseModel):
    decision: str
    reason: str
    reusable_intelligence: List[IntelligenceObject]
    provenance: Provenance

class InvestigationSource(BaseModel):
    id: str
    title: str
    url: str
    source_type: str
    used_by: List[str]

class InvestigationCheckpoint(BaseModel):
    id: str
    title: str
    what_changed: str
    provenance: Provenance
    status: Optional[str] = None
    investigation_question: Optional[str] = None
    tested: Optional[str] = None
    found: Optional[str] = None
    resulting_state: Optional[str] = None
    evidence_refs: Optional[List[str]] = None
    source_refs: Optional[List[str]] = None

class Evidence(BaseModel):
    id: str
    statement: str
    classification: str
    source: str
    provenance: Provenance

class Claim(BaseModel):
    id: str
    statement: str
    evidence_basis: List[str]
    provenance: Provenance

class Inference(BaseModel):
    id: str
    statement: str
    basis: List[str]
    implication: str
    provenance: Provenance

class Hypothesis(BaseModel):
    id: str
    statement: str
    status: Literal['UNKNOWN', 'UNVERIFIED', 'PENDING', 'ACTIVE', 'PASSED', 'FAILED', 'BLOCKED', 'SURVIVED', 'KILLED']
    supporting_basis: List[str]
    falsification_basis: List[str]
    provenance: Provenance

class Result(BaseModel):
    id: str
    statement: str
    status: Literal['UNKNOWN', 'UNVERIFIED', 'PENDING', 'ACTIVE', 'PASSED', 'FAILED', 'BLOCKED', 'SURVIVED', 'KILLED']
    provenance: Provenance

class Traceability(BaseModel):
    statement: str
    research_location: str
    source_urls: List[str]
    provenance: Provenance

class Section(BaseModel):
    id: str
    title: str
    provenance: Provenance
    summary: Optional[str] = None
    evidence_refs: Optional[List[str]] = None
    source_refs: Optional[List[str]] = None

class WorkflowStep(BaseModel):
    id: str
    title: str
    description: str
    provenance: Provenance
    actor: Optional[str] = None
    system: Optional[str] = None
    handoff_to: Optional[str] = None
    state_information: Optional[str] = None
    exception_refs: Optional[List[str]] = None
    evidence_refs: Optional[List[str]] = None
    source_refs: Optional[List[str]] = None

class Workflow(BaseModel):
    id: str
    title: str
    workflow_type: Literal['OBSERVED', 'RECONSTRUCTED', 'PROPOSED_ART']
    steps: List[WorkflowStep] = Field(default_factory=list)
    provenance: Provenance
    summary: Optional[str] = None
    actors: Optional[List[str]] = None
    systems: Optional[List[str]] = None
    safety_boundaries: Optional[List[str]] = None
    source_refs: Optional[List[str]] = None

class Relationship(BaseModel):
    id: str
    source_id: str
    target_id: str
    relationship_type: Literal['CONTRADICTS', 'SUPPORTS', 'DEPENDS_ON']
    provenance: Provenance

class Falsification(BaseModel):
    statement: str
    outcome: Literal['KILLED', 'WEAKENED', 'UNRESOLVED', 'SURVIVED']
    basis: List[str]
    provenance: Provenance
    targetRef: Optional[str] = None
    whatWasTested: Optional[str] = None
    evidence: Optional[str] = None
    reason: Optional[str] = None

class InvestigationBrief(BaseModel):
    investigation_id: str
    company: str
    industry: str
    opportunity: str
    investigation_type: str
    research_status: Literal['UNKNOWN', 'UNVERIFIED', 'PENDING', 'ACTIVE', 'PASSED', 'FAILED', 'BLOCKED', 'SURVIVED', 'KILLED']
    presentation: Presentation
    decision: Decision
    primary_question: str
    sources: List[InvestigationSource]
    checkpoints: List[InvestigationCheckpoint]
    evidence: List[Evidence]
    claims: List[Claim]
    inferences: List[Inference]
    hypotheses: List[Hypothesis]
    results: List[Result]
    traceability: List[Traceability]
    workflows: Optional[List[Workflow]] = None
    sections: Optional[List[Section]] = None
    relationships: Optional[List[Relationship]] = None
    falsification: Optional[List[Falsification]] = None
