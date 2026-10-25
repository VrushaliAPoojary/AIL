export type ResearchStatus = 'UNKNOWN' | 'UNVERIFIED' | 'PENDING' | 'ACTIVE' | 'PASSED' | 'FAILED' | 'BLOCKED' | 'SURVIVED' | 'KILLED';

export interface Provenance {
  source_file: string;
  section: string | null;
  line_start: number | null;
  line_end: number | null;
  url?: string | null;
}

export interface InvestigationSource {
  id: string;
  title: string;
  url: string;
  source_type: string;
  used_by: string[];
}

export type IntelligenceType =
  | 'WORKFLOW_PATTERN'
  | 'STRATEGY_PATTERN'
  | 'DECISION_PATTERN'
  | 'IMPLEMENTATION_PATTERN'
  | 'ARCHITECTURE_PATTERN'
  | 'GUARDRAIL'
  | 'METRIC_PATTERN'
  | 'RESEARCH_METHOD'
  | 'DESIGN_PRINCIPLE'
  | 'NEGATIVE_INTELLIGENCE'
  | 'ART_IMPROVEMENT';

export type IntelligenceEvidenceStatus = 'VERIFIED' | 'PARTIAL' | 'HYPOTHESIS' | 'UNKNOWN' | 'REJECTED';
export type IntelligenceStatus = 'ACTIVE' | 'EXPERIMENTAL' | 'RETIRED';
export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW';
export type ReusePotential = 'HIGH' | 'MEDIUM' | 'LOW';
export type EpistemicClassification = 'EVIDENCE' | 'CLAIM' | 'INFERENCE' | 'HYPOTHESIS' | 'FALSIFICATION' | 'RESULT' | 'DECISION';
export type WorkflowType = 'OBSERVED' | 'RECONSTRUCTED' | 'PROPOSED_ART';
export type RelationshipType = 'CONTRADICTS' | 'SUPPORTS' | 'DEPENDS_ON';

export interface IntelligenceObject {
  id: string;
  type: IntelligenceType;
  title: string;
  domain: string;
  description: string;
  pattern?: string;
  lesson?: string;
  art_learning?: string;
  art_improvement?: string;
  conditions?: string[];
  anti_pattern?: string;
  do_not_assume?: string[] | string;
  evidence_status: IntelligenceEvidenceStatus;
  status: IntelligenceStatus;
  confidence: ConfidenceLevel;
  reuse_potential: ReusePotential;
  applications: string[];
  source_checkpoint?: string;
  source_refs: string[];
  source_location?: string;
  original_source?: string;
  tags: string[];
  provenance: Provenance;
}

export interface PresentationKeyFinding {
  id: string;
  statement: string;
  classification: EpistemicClassification;
  source_refs: string[];
}

export interface Presentation {
  investigation_summary: string;
  key_findings: PresentationKeyFinding[];
}

export interface Decision {
  decision: string;
  reason: string;
  reusable_intelligence: IntelligenceObject[];
  provenance: Provenance;
}

export interface InvestigationCheckpoint {
  id: string;
  title: string;
  status?: string | null;
  investigation_question?: string | null;
  tested?: string | null;
  found?: string | null;
  what_changed: string;
  resulting_state?: string | null;
  evidence_refs?: string[] | null;
  source_refs?: string[] | null;
  provenance: Provenance;
}

export interface InvestigationEvidence {
  id: string;
  statement: string;
  classification: string;
  source: string;
  provenance: Provenance;
}

export interface InvestigationClaim {
  id: string;
  statement: string;
  evidence_basis: string[];
  provenance: Provenance;
}

export interface InvestigationInference {
  id: string;
  statement: string;
  basis: string[];
  implication: string;
  provenance: Provenance;
}

export interface InvestigationHypothesis {
  id: string;
  statement: string;
  status: ResearchStatus;
  supporting_basis: string[];
  falsification_basis: string[];
  provenance: Provenance;
}

export interface InvestigationResult {
  id: string;
  statement: string;
  status: ResearchStatus;
  provenance: Provenance;
}

export interface Traceability {
  statement: string;
  research_location: string;
  source_urls: string[];
  provenance: Provenance;
}

export interface InvestigationSection {
  id: string;
  title: string;
  summary?: string | null;
  evidence_refs?: string[] | null;
  source_refs?: string[] | null;
  provenance: Provenance;
}

export interface WorkflowStep {
  id: string;
  title: string;
  description: string;
  actor?: string | null;
  system?: string | null;
  handoff_to?: string | null;
  state_information?: string | null;
  exception_refs?: string[] | null;
  evidence_refs?: string[] | null;
  source_refs?: string[] | null;
  provenance: Provenance;
}

export interface InvestigationWorkflow {
  id: string;
  title: string;
  workflow_type: WorkflowType;
  summary?: string | null;
  steps: WorkflowStep[];
  nodes?: WorkflowStep[] | null;
  actors?: string[] | null;
  systems?: string[] | null;
  safety_boundaries?: string[] | null;
  source_refs?: string[] | null;
  provenance: Provenance;
}

export interface InvestigationRelationship {
  id: string;
  source_id: string;
  target_id: string;
  relationship_type: RelationshipType;
  provenance: Provenance;
}

export interface InvestigationFalsification {
  statement: string;
  targetRef?: string | null;
  whatWasTested?: string | null;
  evidence?: string | null;
  outcome: 'KILLED' | 'WEAKENED' | 'UNRESOLVED' | 'SURVIVED';
  reason?: string | null;
  basis: string[];
  provenance: Provenance;
}

export interface InvestigationBrief {
  investigation_id: string;
  company: string;
  industry: string;
  opportunity: string;
  investigation_type: string;
  research_status: ResearchStatus;
  presentation: Presentation;
  decision: Decision;
  primary_question: string;
  sources: InvestigationSource[];
  checkpoints: InvestigationCheckpoint[];
  evidence: InvestigationEvidence[];
  claims: InvestigationClaim[];
  inferences: InvestigationInference[];
  hypotheses: InvestigationHypothesis[];
  results: InvestigationResult[];
  traceability: Traceability[];
  workflows?: InvestigationWorkflow[];
  sections?: InvestigationSection[];
  relationships?: InvestigationRelationship[];
  falsification?: InvestigationFalsification[];
}
