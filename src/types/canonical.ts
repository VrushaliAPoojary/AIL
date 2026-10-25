import type { ResearchStatus, Provenance } from './markdownContract';

export interface CanonicalIdentity {
  investigationId: string | null;
  company: string | null;
  opportunity: string | null;
  investigationType: string | null;
  researchStatus: ResearchStatus | 'UNKNOWN';
  sourceStatus: string | null;
  decision: string | null;
  sourceResearchFiles: string[];
}

export interface CanonicalQuestion {
  primaryQuestion: string | null;
  causalChain: string | null;
  whyInvestigationExists: string | null;
  provenance: Provenance | null;
}

export interface CanonicalHypothesis {
  id: string;
  statement: string;
  status: ResearchStatus | 'UNKNOWN';
  rationale: string | null;
  basisRefs: string[];
  provenance: Provenance | null;
}

export interface CanonicalCheckpoint {
  checkpointId: string;
  question: string | null;
  whatChanged: string;
  evidence: string;
  resultingState: string;
  decision: string | null;
  provenance: Provenance | null;
}

export interface CanonicalEvidence {
  id: string;
  statement: string;
  classification: string | null;
  source: string | null;
  provenance: Provenance | null;
}

export interface CanonicalClaim {
  id: string;
  statement: string;
  evidenceRefs: string[];
  provenance: Provenance | null;
}

export interface CanonicalInference {
  id: string;
  statement: string;
  basisRefs: string[];
  provenance: Provenance | null;
}

export interface CanonicalFalsification {
  id: string;
  targetRef: string | null;
  whatWasTested: string;
  evidence: string | null;
  outcome: string | null;
  reason: string | null;
  provenance: Provenance | null;
}

export interface CanonicalFinding {
  id: string;
  statement: string;
  supportingRefs: string[];
  confidence: string | null;
  provenance: Provenance | null;
}

export interface CanonicalDecision {
  decision: string | null;
  decisionReason: string | null;
  supportingRefs: string[];
  remainingUnknowns: string | null;
  decisionStatus: string | null;
  provenance: Provenance | null;
}

export interface CanonicalIntelligence {
  id: string;
  statement: string;
  applicability: string | null;
  sourceRefs: string[];
  provenance: Provenance | null;
}

export interface CanonicalLimitations {
  unknowns: string[];
  evidenceLimitations: string[];
  unverifiedAssumptions: string[];
  unresolvedQuestions: string[];
  validationDebt: string[];
  provenance: Provenance | null;
}

export interface CanonicalInvestigation {
  identity: CanonicalIdentity;
  researchQuestion: CanonicalQuestion;
  initialHypothesis: CanonicalHypothesis;
  progression: CanonicalCheckpoint[];
  evidence: CanonicalEvidence[];
  claims: CanonicalClaim[];
  inferences: CanonicalInference[];
  hypotheses: CanonicalHypothesis[];
  falsifications: CanonicalFalsification[];
  findings: CanonicalFinding[];
  decision: CanonicalDecision;
  intelligence: CanonicalIntelligence[];
  limitations: CanonicalLimitations;
  issues: any[]; // Validation issues
}
