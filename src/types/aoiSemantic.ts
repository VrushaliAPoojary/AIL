export interface AoiMetadata {
  object_id: string;
  opportunity_id: string;
  directory_name: string;
  directory: string;
  company: string | null;
  title: string | null;
  original_opportunity: string | null;
  refined_opportunity: string | null;
  investigation_scope: string | null;
  research_status: string | null;
  aoi_decision: string | null;
  ail_status: string | null;
  checkpoint_ids: string[];
  source_files: Record<string, string>;
  evidence_classification: string | null;
  conflicts: string[];
  missing_checkpoints: string[];
}

export interface AoiSection {
  id: string;
  heading: string;
  level: number;
  parentHeading: string | null;
  content: string;
  startLine: number;
  endLine: number;
}

export interface AoiCheckpoint {
  id: string;
  sequence: number;
  title: string;
  company: string | null;
  opportunity: string | null;
  status: string | null;
  investigation_type: string | null;
  metadata: Record<string, string>;
  conflicts: string[];
  evidence_ids: string[];
  hypothesis_ids: string[];
  decision_ids: string[];
  source_ids: string[];
  sha256: string | null;
  // Included to retain compatibility with new parser output
  content?: string;
  purpose?: string | null;
  nextQuestion?: string | null;
  supports?: string[];
  contradicts?: string[];
  unknowns?: any[];
  evidence?: any[];
  source?: any[];
  provenance?: any;
}

export interface AoiEvidence {
  id: string;
  checkpoint_id: string | null;
  classification: string | null;
  statement: string;
  section: string | null;
  source_ids: string[];
}

export interface AoiHypothesis {
  id: string;
  checkpoint_id: string | null;
  statement: string;
  classification: string | null;
  status: string | null;
  section: string | null;
  source_ids: string[];
}

export interface AoiDecision {
  id: string;
  checkpoint_id: string | null;
  value: string | null;
  statement: string;
  section: string | null;
  source_ids: string[];
  raw_value: string | null;
}

export interface WorkflowNode {
  id: string;
  type: string | null;
  title: string | null;
  purpose: string | null;
  input: string | null;
  operation: string | null;
  aiCapability: string | null;
  automationCapability: string | null;
  humanInvolvement: string | null;
  decisionLogic: string | null;
  expectedOutput: string | null;
  failureCondition: string | null;
  researchBasis: string | null;
  nextNode: string[];
  status: string;
  sourceStatus: string | null;
  demoInteraction: string | null;
  relationships?: string[];
  provenance?: any;
}

export interface AoiWorkflowModel {
  id: string;
  title: string;
  status: string | null;
  classification?: string | null;
  checkpoint_ids?: string[];
  source_ids?: string[];
  source_file?: string;
  nodes: WorkflowNode[];
  edges: AoiRelationship[];
}

export interface AoiIntelligence {
  id: string;
  name: string;
  category?: string | null;
  source_file: string;
  problem: string | null;
  workflow: string | null;
  implementation_mechanism: string | null;
  classification: string | null;
  applicability: string | null;
  limitations: string | null;
  checkpoint_ids: string[];
  source_ids: string[];
}

export interface AoiSource {
  id: string;
  name: string | null;
  url: string;
  references: string[];
}

export interface AoiReference {
  from_id: string;
  relation: string;
  to_id: string;
  checkpoint_id: string | null;
  source_ids: string[];
}

export interface AoiRelationship {
  id: string;
  sourceNode: string;
  targetNode: string | null;
  relationshipType: string;
  label: string | null;
  status?: string;
  rawReference?: string | null;
  provenance?: any;
}

export interface AoiOpportunity {
  metadata: AoiMetadata;
  checkpoints: AoiCheckpoint[];
  sections: AoiSection[];
  evidence: AoiEvidence[];
  hypotheses: AoiHypothesis[];
  decisions: AoiDecision[];
  workflows: AoiWorkflowModel[];
  intelligence: AoiIntelligence[];
  sources: AoiSource[];
  references: AoiReference[];
  relationships: AoiRelationship[];
  ingestion_errors: string[];
  ingestion_warnings: string[];
  issues?: any[]; // To track contract issues from the parser
}

export interface AoiNormalizedData {
  schemaVersion: string;
  generatedFrom: string;
  opportunities: AoiOpportunity[];
  ingestion: { errors?: string[]; warnings?: string[] };
}
