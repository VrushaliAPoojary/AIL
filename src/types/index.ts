export type NodeType = 'S' | 'E' | 'C' | 'I' | 'H' | 'X' | 'R' | 'D';
export type EpistemicState = 'EVIDENCE' | 'CLAIM' | 'INFERENCE' | 'HYPOTHESIS' | 'UNKNOWN' | 'PENDING';

export interface GraphNode {
  id: string;
  type: NodeType;
  status: 'verified' | 'unverified' | 'testing' | 'rejected';
  epistemicState: EpistemicState;
  title: string;
  description: string;
  upstream: { id: string; label: string }[];
  downstream: { id: string; label: string }[];
  
  whyExists?: string;
  whatWeKnow?: string;
  whatWeInfer?: string;
  whatWeDoNotKnow?: string;
  whatWouldSupportIt?: string;
  whatWouldContradictIt?: string;
  whatWouldKillIt?: string;
  nextTest?: string;
}
