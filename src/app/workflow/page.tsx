import { WorkflowCanvas } from '../../features/core/workflow/WorkflowCanvas';

const defaultInvestigation = {
  metadata: {
    title: 'Workflow preview unavailable',
    opportunity_id: 'NOT PROVIDED',
    aoi_decision: 'NOT PROVIDED',
  },
  workflows: [],
} as any;

export default function WorkflowPage() {
  return <WorkflowCanvas investigation={defaultInvestigation} />;
}
