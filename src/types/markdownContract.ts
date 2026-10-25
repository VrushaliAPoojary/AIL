export const CONTROLLED_RESEARCH_STATUSES = [
  'UNKNOWN',
  'UNVERIFIED',
  'PENDING',
  'ACTIVE',
  'PASSED',
  'FAILED',
  'BLOCKED',
  'SURVIVED',
  'KILLED',
] as const;

export type ResearchStatus = (typeof CONTROLLED_RESEARCH_STATUSES)[number];
export type SourceDocument = 'walkthrough' | 'workflow';

export interface Provenance {
  document: SourceDocument;
  sourcePath: string;
  section: string | null;
  sourceIdentifier: string | null;
  reference: string | null;
  excerpt: string | null;
  lineStart: number | null;
  lineEnd: number | null;
}

export interface MarkdownSection {
  id: string;
  heading: string;
  level: number;
  parentHeading: string | null;
  content: string;
  startLine: number;
  endLine: number;
}

export interface ResearchFragment {
  id: string;
  text: string;
  status: ResearchStatus;
  sourceValue: string | null;
  provenance: Provenance;
}

export interface ContractIssue {
  severity: 'INFO' | 'WARNING' | 'ERROR';
  code: string;
  message: string;
  nodeId: string | null;
  provenance: Provenance | null;
}

export interface WalkthroughMarkdownInput {
  sourcePath: string;
  markdown: string;
}

export interface WorkflowMarkdownInput {
  sourcePath: string;
  markdown: string;
}

export interface WalkthroughIdentity {
  id: string | null;
  title: string | null;
  target: string | null;
  status: ResearchStatus;
  sourceStatus: string | null;
  finalDecision: string | null;
  provenance: Provenance;
}

export interface WalkthroughNode {
  id: string;
  type: string;
  title: string | null;
  status: ResearchStatus;
  sourceStatus: string | null;
  purpose: string | null;
  content: string;
  evidence: ResearchFragment[];
  source: ResearchFragment[];
  supports: string[];
  contradicts: string[];
  unknowns: ResearchFragment[];
  nextQuestion: string | null;
  relationships: string[];
  provenance: Provenance;
}

export interface WorkflowMarkdownNode {
  sourceId: string | null;
  fields: Record<string, string>;
  provenance: Provenance;
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
  status: ResearchStatus;
  sourceStatus: string | null;
  demoInteraction: string | null;
  relationships: string[];
  provenance: Provenance;
}

export interface WalkthroughMarkdownDocument {
  kind: 'walkthrough';
  sourcePath: string;
  title: string | null;
  sections: MarkdownSection[];
  identity: WalkthroughIdentity;
  nodes: WalkthroughNode[];
  issues: ContractIssue[];
}

export interface WorkflowMarkdownDocument {
  kind: 'workflow';
  sourcePath: string;
  title: string | null;
  sections: MarkdownSection[];
  sourceNodes: WorkflowMarkdownNode[];
  nodes: WorkflowNode[];
  issues: ContractIssue[];
}

export interface Relationship {
  id: string;
  sourceNode: string;
  targetNode: string;
  relationshipType: string;
  label: string | null;
  provenance: Provenance;
}
