'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { KeyboardEvent as ReactKeyboardEvent, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import './WorkflowCanvas.css';
import type { ResearchStatus } from '../../../types/markdownContract';
import type { AoiOpportunity, WorkflowNode } from '../../../types/aoiSemantic';

const NOT_PROVIDED = 'NOT PROVIDED';
const EXPERIMENT_STATUSES: ResearchStatus[] = ['PENDING', 'ACTIVE', 'PASSED', 'FAILED', 'BLOCKED', 'UNKNOWN', 'UNVERIFIED'];

interface WorkflowCanvasProps {
  investigation: AoiOpportunity;
  onReturnToNarrative?: () => void;
}

function display(value: string | null | undefined): string {
  return value?.trim() || NOT_PROVIDED;
}

function statusClass(status: string): string {
  return 'status-' + status.toLowerCase().replace(/\s+/g, '-');
}

function statusCounts(nodes: WorkflowNode[]): string {
  const counts = new Map<string, number>();
  nodes.forEach(node => counts.set(node.status, (counts.get(node.status) ?? 0) + 1));
  return [...counts.entries()].map(([status, count]) => count + ' ' + status).join(' · ') || NOT_PROVIDED;
}

function buildColumns(nodes: WorkflowNode[]): WorkflowNode[][] {
  const nodeIds = new Set(nodes.map(node => node.id));
  const incoming = new Map<string, number>();
  const downstream = new Map<string, string[]>();

  nodes.forEach(node => {
    const targets = node.nextNode.filter(target => nodeIds.has(target));
    downstream.set(node.id, targets);
    targets.forEach(target => incoming.set(target, (incoming.get(target) ?? 0) + 1));
  });

  const roots = nodes.filter(node => !incoming.has(node.id));
  const depth = new Map<string, number>();
  const queue = roots.map(node => ({ id: node.id, level: 0 }));
  while (queue.length > 0) {
    const current = queue.shift();
    if (!current) break;
    const previous = depth.get(current.id);
    if (previous !== undefined && previous >= current.level) continue;
    depth.set(current.id, current.level);
    (downstream.get(current.id) ?? []).forEach(target => queue.push({ id: target, level: current.level + 1 }));
  }

  const maxDepth = Math.max(-1, ...depth.values());
  nodes.forEach((node, index) => {
    if (!depth.has(node.id)) depth.set(node.id, maxDepth + 1 + index);
  });

  const columns: WorkflowNode[][] = [];
  nodes.forEach(node => {
    const level = depth.get(node.id) ?? 0;
    columns[level] ??= [];
    columns[level].push(node);
  });
  return columns.filter(Boolean);
}

function Field({ label, value, children }: { label: string; value?: string | null; children?: ReactNode }) {
  return (
    <div className="wf-field">
      <label>{label}</label>
      <div>{children ?? display(value)}</div>
    </div>
  );
}

function Provenance({ node }: { node: WorkflowNode }) {
  const source = node.provenance;
  return (
    <div className="wf-provenance">
      <span>{display(source.sourcePath)}</span>
      <span>{display(source.section)}</span>
      <span>{'LINES ' + (source.lineStart ?? '?') + (source.lineEnd && source.lineEnd !== source.lineStart ? '–' + source.lineEnd : '')}</span>
    </div>
  );
}

function NodeCard({
  node,
  selected,
  focused,
  demoState,
  onSelect,
  onFocus,
  nodeRef,
}: {
  node: WorkflowNode;
  selected: boolean;
  focused: boolean;
  demoState: ResearchStatus | null;
  onSelect: () => void;
  onFocus: () => void;
  nodeRef: (element: HTMLButtonElement | null) => void;
}) {
  return (
    <button
      ref={nodeRef}
      className={'wf-node-card ' + (selected ? 'selected ' : '') + (focused ? 'focused ' : '') + statusClass(node.status)}
      onClick={onSelect}
      onFocus={onFocus}
      aria-pressed={selected}
      aria-label={'Inspect workflow node ' + node.id + ', ' + display(node.title)}
    >
      <div className="wf-node-header">
        <span className="wf-node-type">{display(node.type)}</span>
        <span className="wf-node-id">{node.id}</span>
      </div>
      <div className="wf-node-title">{display(node.title)}</div>
      <div className={'wf-node-status ' + statusClass(node.status)}>SOURCE: {node.status}</div>
      {demoState && <div className={'wf-node-demo-status ' + statusClass(demoState)}>DEMO: {demoState}</div>}
      <div className="wf-node-next">NEXT: {node.nextNode.length > 0 ? node.nextNode.join(' · ') : NOT_PROVIDED}</div>
    </button>
  );
}

function Inspector({
  node,
  demoState,
  onChangeDemoState,
  onClose,
  onOpenNode,
}: {
  node: WorkflowNode;
  demoState: ResearchStatus | null;
  onChangeDemoState: (status: ResearchStatus) => void;
  onClose: () => void;
  onOpenNode: (id: string) => void;
}) {
  const fields: Array<[string, string | null | undefined]> = [
    ['PURPOSE', node.purpose],
    ['INPUT', node.input],
    ['OPERATION', node.operation],
    ['AI CAPABILITY', node.aiCapability],
    ['AUTOMATION CAPABILITY', node.automationCapability],
    ['HUMAN INVOLVEMENT', node.humanInvolvement],
    ['DECISION LOGIC', node.decisionLogic],
    ['EXPECTED OUTPUT', node.expectedOutput],
    ['FAILURE CONDITION', node.failureCondition],
    ['RESEARCH BASIS', node.researchBasis],
    ['STATUS', node.status],
    ['DEMO INTERACTION', node.demoInteraction],
  ];

  return (
    <aside className="wf-inspector" aria-label="Workflow node inspector">
      <div className="wf-inspector-header">
        <div>
          <span className="wf-inspector-kicker">NODE INSPECTOR</span>
          <h2>{node.id}</h2>
        </div>
        <button className="wf-close-btn" onClick={onClose} aria-label="Close node inspector">×</button>
      </div>
      <div className="wf-inspector-content">
        <div className="wf-inspector-title">{display(node.title)}</div>
        <div className="wf-inspector-meta">
          <span>{display(node.type)}</span>
          <span className={'wf-status-chip ' + statusClass(node.status)}>{node.status}</span>
        </div>
        {fields.map(([label, value]) => <Field label={label} value={value} key={label} />)}
        <Field label="NEXT NODE">
          {node.nextNode.length > 0 ? (
            <div className="wf-next-links">
              {node.nextNode.map(target => <button className="wf-next-link" key={target} onClick={() => onOpenNode(target)}>{target} →</button>)}
            </div>
          ) : NOT_PROVIDED}
        </Field>
        <Field label="PROVENANCE"><Provenance node={node} /></Field>
        <section className="wf-demo-control">
          <label htmlFor="wf-demo-state">LOCAL EXPERIMENT STATE</label>
          <p>Local canvas state only. It does not execute automation or change research status.</p>
          <select id="wf-demo-state" value={demoState ?? ''} onChange={event => onChangeDemoState(event.target.value as ResearchStatus)}>
            <option value="">NOT SET</option>
            {EXPERIMENT_STATUSES.map(status => <option value={status} key={status}>{status}</option>)}
          </select>
          <div className="wf-demo-note">{node.demoInteraction ? 'DOCUMENTED DEMO INTERACTION AVAILABLE' : 'DEMO NOT IMPLEMENTED'}</div>
        </section>
      </div>
    </aside>
  );
}

function CapabilitySurface({ nodes }: { nodes: WorkflowNode[] }) {
  const capabilityRows: Array<[string, (node: WorkflowNode) => string | null | undefined]> = [
    ['AI CAPABILITY', node => node.aiCapability],
    ['AUTOMATION CAPABILITY', node => node.automationCapability],
    ['HUMAN INVOLVEMENT', node => node.humanInvolvement],
    ['DECISION LOGIC', node => node.decisionLogic],
    ['INPUT → OUTPUT', node => node.input && node.expectedOutput ? node.input + ' → ' + node.expectedOutput : null],
    ['FAILURE HANDLING', node => node.failureCondition],
    ['VERIFICATION', node => /VERIF|CHECK|VALID/i.test((node.type ?? '') + ' ' + (node.operation ?? '')) ? node.operation : null],
    ['AUDITABILITY', node => node.researchBasis || node.provenance.sourcePath],
  ];

  return (
    <section className="wf-capability-surface" aria-label="ART capability surface">
      <div className="wf-section-kicker">CAPABILITY SURFACE / RESEARCH-DERIVED</div>
      <div className="wf-capability-grid">
        {capabilityRows.map(([label, getter]) => {
          const supported = nodes.filter(node => Boolean(getter(node))).length;
          return (
            <div className="wf-capability-item" key={label}>
              <span>{label}</span>
              <strong>{supported > 0 ? supported + ' / ' + nodes.length + ' NODES' : NOT_PROVIDED}</strong>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export function WorkflowCanvas({ investigation, onReturnToNarrative }: WorkflowCanvasProps) {
  const router = useRouter();
  const nodes = investigation.workflows?.[0]?.nodes ?? [];
  const nodeMap = useMemo(() => new Map(nodes.map(node => [node.id, node])), [nodes]);
  const columns = useMemo(() => buildColumns(nodes), [nodes]);
  const relationships = useMemo(
    () => nodes.flatMap(node => node.nextNode.filter(target => nodeMap.has(target)).map(target => ({ source: node.id, target }))),
    [nodeMap, nodes],
  );
  const upstream = useMemo(() => {
    const map = new Map<string, string[]>();
    relationships.forEach(({ source, target }) => map.set(target, [...(map.get(target) ?? []), source]));
    return map;
  }, [relationships]);

  const rootRef = useRef<HTMLElement>(null);
  const nodeRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [focusedId, setFocusedId] = useState<string | null>(nodes[0]?.id ?? null);
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [experimentMode, setExperimentMode] = useState(false);
  const [demoStates, setDemoStates] = useState<Record<string, ResearchStatus>>({});

  const selectedNode = selectedId ? nodeMap.get(selectedId) ?? null : null;

  const focusNode = useCallback((id: string | null) => {
    if (!id || !nodeMap.has(id)) return;
    setFocusedId(id);
    window.requestAnimationFrame(() => nodeRefs.current[id]?.focus());
  }, [nodeMap]);

  const openNode = useCallback((id: string) => {
    if (!nodeMap.has(id)) return;
    setSelectedId(id);
    setFocusedId(id);
    setInspectorOpen(true);
  }, [nodeMap]);

  const closeInspector = useCallback(() => {
    setInspectorOpen(false);
    setSelectedId(null);
  }, []);

  const navigateNodes = useCallback((direction: 'next' | 'previous') => {
    const current = focusedId ?? nodes[0]?.id;
    if (!current) return;
    const candidates = direction === 'next'
      ? (nodeMap.get(current)?.nextNode.filter(id => nodeMap.has(id)) ?? [])
      : (upstream.get(current) ?? []);
    const fallbackIndex = nodes.findIndex(node => node.id === current);
    const target = candidates[0] ?? nodes[Math.max(0, fallbackIndex + (direction === 'next' ? 1 : -1))]?.id;
    focusNode(target ?? null);
  }, [focusNode, focusedId, nodeMap, nodes, upstream]);

  const handleKeyDown = useCallback((event: ReactKeyboardEvent<HTMLElement>) => {
    if (event.key === 'Escape') {
      if (inspectorOpen) closeInspector();
      return;
    }
    if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement || event.target instanceof HTMLSelectElement) return;
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
      navigateNodes('next');
      event.preventDefault();
    } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
      navigateNodes('previous');
      event.preventDefault();
    } else if (event.key === 'Enter') {
      if (focusedId) openNode(focusedId);
      event.preventDefault();
    }
  }, [closeInspector, focusedId, inspectorOpen, navigateNodes, openNode]);

  useEffect(() => {
    if (selectedId && !nodeMap.has(selectedId)) closeInspector();
  }, [closeInspector, nodeMap, selectedId]);

  const sourceStatus = statusCounts(nodes);
  const demoStatus = Object.keys(demoStates).length > 0
    ? Object.keys(demoStates).length + ' LOCAL STATES SET'
    : 'NO LOCAL STATES SET';

  if (nodes.length === 0) {
    return (
      <main className="wf-container wf-empty" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', textAlign: 'center' }}>
        <div style={{ maxWidth: '600px', padding: '40px', background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)', borderRadius: '8px' }}>
          <div className="wf-section-kicker" style={{ marginBottom: '16px' }}>WORKFLOW EXPERIMENTATION</div>
          <h1 style={{ fontSize: '24px', letterSpacing: '0.1em', marginBottom: '16px', color: 'var(--color-text)' }}>COMING SOON</h1>
          <p style={{ color: 'var(--color-text-muted)', marginBottom: '32px', lineHeight: '1.6' }}>
            The Workflow Canvas is being rebuilt to support our latest research standards.
            Advanced interactive workflows and automated simulation will be available in the next major update.
          </p>
          <button
            className="ap-detail-btn"
            onClick={() => onReturnToNarrative ? onReturnToNarrative() : router.push('/walkthrough')}
            style={{ margin: '0 auto', display: 'inline-block' }}
          >
            RETURN TO WALKTHROUGH &rarr;
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className={'wf-container ' + (inspectorOpen ? 'inspector-open' : '')} ref={rootRef} tabIndex={0} onKeyDown={handleKeyDown} aria-label="Workflow experimentation canvas">
      <section className="wf-canvas">
        <header className="wf-toolbar">
          <div>
            <div className="wf-section-kicker">ART INVESTIGATION / WORKFLOW EXPERIMENTATION</div>
            <h1>{display(investigation.metadata.title)}</h1>
            <div className="wf-identity-meta">
              <span>IDENTITY <strong>{display(investigation.metadata.opportunity_id)}</strong></span>
              <span>WORKFLOW STATUS <strong>{display(investigation.workflows[0]?.status)}</strong></span>
              <span>INVESTIGATION DECISION <strong>{display(investigation.metadata.aoi_decision)}</strong></span>
            </div>
          </div>
          {onReturnToNarrative && <button className="wf-return-button" onClick={onReturnToNarrative}>← NARRATIVE WALKTHROUGH</button>}
        </header>

        <section className="wf-summary-strip">
          <div><span>WORKFLOW NODES</span><strong>{nodes.length}</strong></div>
          <div><span>RELATIONSHIPS</span><strong>{relationships.length}</strong></div>
          <div><span>SOURCE STATUS</span><strong>{sourceStatus}</strong></div>
          <div><span>EXPERIMENT STATE</span><strong>{demoStatus}</strong></div>
        </section>

        <div className="wf-experiment-bar">
          <div>
            <strong>{experimentMode ? 'LOCAL EXPERIMENT MODE ACTIVE' : 'EXPERIMENT MODE AVAILABLE'}</strong>
            <span>{experimentMode ? 'Use the inspector to set a local node state. No external automation is connected.' : 'Source statuses remain unchanged; local state is optional and reversible.'}</span>
          </div>
          <div className="wf-experiment-actions">
            <button className="wf-experiment-button" onClick={() => setExperimentMode(value => !value)}>{experimentMode ? 'EXIT EXPERIMENT MODE' : 'ENTER EXPERIMENT MODE'}</button>
            <button className="wf-experiment-button secondary" onClick={() => setDemoStates({})} disabled={Object.keys(demoStates).length === 0}>RESET LOCAL STATES</button>
          </div>
        </div>

        <CapabilitySurface nodes={nodes} />

        <section className="wf-graph-section" aria-label="Workflow graph">
          <div className="wf-graph-heading">
            <div><div className="wf-section-kicker">PRIMARY CANVAS</div><h2>What this workflow actually does</h2></div>
            <span>Select a node · Arrow keys navigate · Enter inspects · Escape closes</span>
          </div>
          <div className="wf-graph">
            {columns.map((column, index) => (
              <div className="wf-graph-column" key={'column-' + index}>
                <div className="wf-column-label">STAGE {String(index + 1).padStart(2, '0')}</div>
                {column.map(node => (
                  <NodeCard
                    key={node.id}
                    node={node}
                    selected={selectedId === node.id}
                    focused={focusedId === node.id}
                    demoState={demoStates[node.id] ?? null}
                    onSelect={() => openNode(node.id)}
                    onFocus={() => setFocusedId(node.id)}
                    nodeRef={element => { nodeRefs.current[node.id] = element; }}
                  />
                ))}
              </div>
            ))}
          </div>
        </section>

        <section className="wf-relationship-section" aria-label="Workflow relationships">
          <div className="wf-section-kicker">RELATIONSHIPS / SOURCE-DERIVED</div>
          {relationships.length > 0 ? (
            <div className="wf-relationship-list">
              {relationships.map(({ source, target }) => (
                <button className="wf-relationship" key={source + '-' + target} onClick={() => openNode(target)}>
                  <span>{source}</span><b>→</b><span>{target}</span>
                </button>
              ))}
            </div>
          ) : <span className="wf-not-provided">NOT PROVIDED</span>}
        </section>

        <div className="wf-demo-notice">
          <strong>EXECUTION DEMO</strong>
          <span>DEMO NOT IMPLEMENTED — this canvas does not execute external, AI, or automation operations.</span>
        </div>
      </section>

      {inspectorOpen && selectedNode && (
        <Inspector
          node={selectedNode}
          demoState={demoStates[selectedNode.id] ?? null}
          onChangeDemoState={status => setDemoStates(current => ({ ...current, [selectedNode.id]: status }))}
          onClose={closeInspector}
          onOpenNode={openNode}
        />
      )}
    </main>
  );
}
