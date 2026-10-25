'use client';

import { useState, useMemo, useEffect, useRef } from 'react';
import { useSearchParams } from 'next/navigation';
import './Walkthrough.css';
import { loadAllInvestigationBriefs } from '../../../data/investigationBriefLoader';
import type { InvestigationBrief, Provenance, IntelligenceObject } from '../../../types/investigationBrief';
import { NOT_PROVIDED, PresentationText, SourceAuditList, SourceIndicator, ProvenanceDetails, opportunityLabel } from './Presentation';
import { MarkdownRenderer } from './MarkdownRenderer';
import { InvestigationSignalStrip } from './sections/InvestigationSignalStrip';


// --------------------------------------------------
// UTILS
// --------------------------------------------------

function getStatusClass(status?: string) {
  if (!status) return '';
  return `status-${status.toLowerCase().replace(/\s+/g, '-')}`;
}

function getCitationUrls(statement?: string, traceability?: InvestigationBrief['traceability']) {
  if (!statement || !traceability) return [];
  const trace = traceability.find(t => t.statement === statement || statement.includes(t.statement));
  return trace?.source_urls || [];
}

function previewDecisionReason(reason: string): string {
  const lines = reason
    .split(/\r?\n/)
    .map(line => line.trim())
    .filter(Boolean);

  const filtered = lines.filter(line =>
    !/^#{1,6}\s+/.test(line) &&
    line !== '---' &&
    !/^```/.test(line) &&
    !/^###\s+Official/i.test(line) &&
    !/^\*\*?Official/i.test(line)
  );

  const joined = filtered.join(' ');
  return joined || reason;
}

function normalizeDecisionOutcome(decision?: string): string {
  if (!decision) return 'NOT PROVIDED';

  const raw = decision.replace(/\*\*/g, '').trim();
  const upper = raw.toUpperCase();

  if (/CONDITIONAL PASS/.test(upper)) return 'CONDITIONAL PASS';
  if (/\bKILL(?:ED)?\b/.test(upper)) return 'KILLED';
  if (/\bNOT VALIDATED\b/.test(upper)) return 'NOT VALIDATED';
  if (/\bREFINE\b/.test(upper)) return 'REFINE';
  if (/\bCOMPLETE\b/.test(upper)) return 'COMPLETE';
  if (/\bCONTINUE\b/.test(upper)) return 'CONTINUE';
  if (/\bPASS\b/.test(upper)) return 'PASS';

  const firstClause = raw
    .replace(/^OPP-[0-9]+(?:-[0-9]+)*\s*[—-]\s*/i, '')
    .split(/\s+[—–-]\s+|\s*→\s*/)[0]
    .trim();

  return firstClause || raw;
}

function getHeroConfidence(brief?: InvestigationBrief): string {
  if (!brief?.decision?.reusable_intelligence?.length) return NOT_PROVIDED;

  const confidences = [...new Set(brief.decision.reusable_intelligence.map(item => item.confidence).filter(Boolean))];
  return confidences.length === 1 ? confidences[0] : NOT_PROVIDED;
}



// --------------------------------------------------
// COMMON COMPONENTS
// --------------------------------------------------

function StatusBadge({ status }: { status?: string }) {
  if (!status) return null;
  return <span className={`badge ${getStatusClass(status)}`}>{status}</span>;
}

interface NodeData {
  type: string;
  id?: string;
  title?: string;
  content?: string;
  status?: string;
  classification?: string;
  source?: string;
  basis?: string[];
  supports?: string[];
  contradicts?: string[];
  provenance?: Provenance;
  what_changed?: string;
  resulting_state?: string;
  what_was_tested?: string;
  implication?: string;
  investigation_question?: string;
  evidence_refs?: string[];
  source_refs?: string[];
  source_urls?: string[];
}

function ResearchNode({
  node,
  onDetail,
  hideType = false,
  traceability
}: {
  node: NodeData;
  onDetail: (n: NodeData) => void;
  hideType?: boolean;
  traceability?: InvestigationBrief['traceability'];
}) {
  const citationCount = getCitationUrls(node.content, traceability).length;
  const sourceCount = node.source_refs?.length ?? (node.source_urls?.length ?? (citationCount > 0 ? citationCount : node.source ? 1 : 0));

  const openDetails = () => onDetail(node);

  return (
    <article
      className="research-node"
      role="button"
      tabIndex={0}
      onClick={openDetails}
      onKeyDown={event => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          openDetails();
        }
      }}
    >
      <div className="node-header">
        <div className="node-topline">
          {!hideType && <span className="node-type">{node.type}</span>}
          {node.id && <span className="node-id">{node.id}</span>}
        </div>
      </div>
      <div className="node-content">
        {(node.status || node.classification) && (
          <div className="node-badges">
            {node.status && <StatusBadge status={node.status} />}
            {node.classification && <span className="badge badge-class">{node.classification}</span>}
          </div>
        )}
        {node.title && <strong className="node-title">{node.title}</strong>}
        {node.content && <PresentationText lines={2} className="node-excerpt">{node.content}</PresentationText>}
      </div>
      <div className="node-footer">
        <SourceIndicator count={sourceCount} />
        <button className="btn-detail" onClick={event => { event.stopPropagation(); openDetails(); }}>
          VIEW DETAILS →
        </button>
      </div>
    </article>
  );
}

// --------------------------------------------------
// ZONES
// --------------------------------------------------

function InvestigationHero({
  brief,
  opportunityId,
  onOpportunityChange,
  companies,
  selectedCompany,
  onCompanyChange,
  companyBriefs,
}: {
  brief?: InvestigationBrief;
  opportunityId: string;
  onOpportunityChange: (id: string) => void;
  companies: string[];
  selectedCompany: string;
  onCompanyChange: (company: string) => void;
  companyBriefs: InvestigationBrief[];
}) {
  const heroTitle = brief ? opportunityLabel(brief) : 'Yet to explore';
  const heroCompany = brief?.company ?? NOT_PROVIDED;
  const heroIndustry = brief?.industry ?? NOT_PROVIDED;
  const heroDecision = normalizeDecisionOutcome(brief?.decision?.decision);
  const heroConfidence = getHeroConfidence(brief);



  return (
    <section className="investigation-hero">
      <div className="hero-toolbar">
        <div className="hero-toolbar-copy">
          <span className="hero-kicker">INVESTIGATION / CONTEXT</span>
          <p className="hero-toolbar-note">Browse the loaded investigations without leaving the page.</p>
        </div>

        <div className="hero-control-strip">
          <div className="hero-control">
            <span className="hero-control-label">Company</span>
            <div className="hero-select-wrap">
              <select
                className="hero-select"
                value={selectedCompany}
                onChange={e => onCompanyChange(e.target.value)}
              >
                {companies.length > 0
                  ? companies.map(c => <option key={c} value={c}>{c}</option>)
                  : <option value="">Yet to explore</option>}
              </select>
              <span className="hero-select-arrow">▼</span>
            </div>
          </div>

          <div className="hero-control">
            <span className="hero-control-label">Opportunity</span>
            <div className="hero-select-wrap">
              <select
                className="hero-select"
                value={brief ? opportunityId : ''}
                disabled={companyBriefs.length === 0}
                onChange={e => onOpportunityChange(e.target.value)}
              >
                {companyBriefs.length > 0
                  ? companyBriefs.map(b => (
                    <option key={b.investigation_id} value={b.investigation_id}>
                      {opportunityLabel(b)}
                    </option>
                  ))
                  : <option value="">Yet to explore</option>}
              </select>
              <span className="hero-select-arrow">▼</span>
            </div>
          </div>
        </div>
      </div>

      <div className="hero-grid">
        <div className="hero-main">
          <div className="hero-id-row">
            <span className="hero-id-pill">{brief?.investigation_id ?? 'NO INVESTIGATION DATA'}</span>
            <span className="hero-type-text">{brief?.investigation_type ?? 'YET TO EXPLORE'}</span>
          </div>

          <h1 className="hero-title">{heroTitle}</h1>
          <div className="hero-company-line">{heroCompany} · {heroIndustry}</div>

          <div className="hero-meta-row">
            <div className="hero-meta-item">
              <span className="hero-meta-label">Research status</span>
              <div className="hero-meta-value">
                {brief ? <StatusBadge status={brief.research_status} /> : <span className="hero-muted-value">{NOT_PROVIDED}</span>}
              </div>
            </div>
            <div className="hero-meta-item">
              <span className="hero-meta-label">Decision</span>
              <div className={`hero-decision-value ${getStatusClass(heroDecision)}`}>{heroDecision}</div>
            </div>
            <div className="hero-meta-item">
              <span className="hero-meta-label">Confidence</span>
              <div className="hero-meta-value hero-confidence-value">{heroConfidence}</div>
            </div>
            <div className="hero-meta-item">
              <span className="hero-meta-label">Last updated</span>
              <div className="hero-meta-value hero-muted-value">NOT PROVIDED</div>
            </div>
          </div>



        </div>
      </div>
    </section>
  );
}

function InvestigationOverview({ brief, onDetail }: { brief: InvestigationBrief, onDetail: (n: NodeData) => void }) {
  const p = brief.presentation;
  const d = brief.decision;
  const summaryRef = useRef<HTMLDivElement>(null);
  const [showSummaryBtn, setShowSummaryBtn] = useState(false);

  useEffect(() => {
    if (summaryRef.current) {
      // Check if text is overflowing its clamped height
      setShowSummaryBtn(summaryRef.current.scrollHeight > summaryRef.current.clientHeight);
    }
  }, [p?.investigation_summary]);

  if (!p) return null;

  return (
    <section className="zone zone-overview">
      <h2 className="zone-title" style={{ fontSize: '10px', letterSpacing: '0.2em' }}>INVESTIGATION OVERVIEW</h2>

      <div className="overview-layout">
        <div className="overview-top-row">
          <div className="overview-summary-box">
            <h3 className="section-label">INVESTIGATION SUMMARY</h3>
            <PresentationText className="summary-text" lines={10} ref={summaryRef}>{p.investigation_summary}</PresentationText>
            {showSummaryBtn && (
              <button
                className="ap-detail-btn primary-detail-action"
                style={{ marginTop: 'auto', paddingTop: '16px' }}
                onClick={() => onDetail({
                  type: 'INVESTIGATION SUMMARY',
                  id: brief.investigation_id + '-SUMMARY',
                  content: p.investigation_summary,
                  source_urls: getCitationUrls(p.investigation_summary, brief.traceability),
                  provenance: d.provenance,
                })}
              >
                VIEW FULL SUMMARY →
              </button>
            )}
          </div>

          <div className="overview-decision-box">
            <h3 className="section-label">FINAL DECISION</h3>
            <div className="decision-content">
              <div className={'decision-callout ' + getStatusClass(normalizeDecisionOutcome(d.decision))}>
                {normalizeDecisionOutcome(d.decision)}
              </div>
              <div className="decision-reason">
                <h4>REASONING</h4>
                <PresentationText lines={4}>{previewDecisionReason(d.reason)}</PresentationText>
                <button
                  className="ap-detail-btn primary-detail-action"
                  onClick={() => onDetail({
                    type: 'DECISION',
                    id: brief.investigation_id + '-DECISION',
                    status: d.decision,
                    content: d.reason,
                    source_urls: getCitationUrls(d.reason, brief.traceability),
                    provenance: d.provenance,
                  })}
                >
                  VIEW DECISION DETAILS →
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="overview-findings-section">
          <h3 className="section-label">KEY FINDINGS</h3>
          <div className="findings-grid">
            {p.key_findings.map((finding, idx) => {
              const node = {
                type: 'KEY FINDING',
                id: finding.id,
                content: finding.statement,
                classification: finding.classification,
                source_refs: finding.source_refs,
                source_urls: getCitationUrls(finding.statement, brief.traceability),
              };

              return (
                <article
                  key={finding.id}
                  className="finding-card"
                  role="button"
                  tabIndex={0}
                  onClick={() => onDetail(node)}
                  onKeyDown={event => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault();
                      onDetail(node);
                    }
                  }}
                >
                  <div className="finding-header">
                    <span className="finding-num">{String(idx + 1).padStart(2, '0')}</span>
                    {finding.classification && <span className="badge badge-class">{finding.classification}</span>}
                  </div>
                  <PresentationText className="finding-text" lines={4}>{finding.statement}</PresentationText>
                  <div className="primary-card-footer">
                    <SourceIndicator count={finding.source_refs?.length ?? 0} />
                    <button className="ap-detail-btn" onClick={event => { event.stopPropagation(); onDetail(node); }}>
                      VIEW DETAILS →
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

function InvestigationProgression({ brief, onDetail }: { brief: InvestigationBrief, onDetail: (n: NodeData) => void }) {
  const checkpoints = brief.checkpoints;
  if (!checkpoints || checkpoints.length === 0) return null;

  return (
    <section className="zone zone-progression">
      <h2 className="zone-title" style={{ fontSize: '10px', letterSpacing: '0.2em', marginBottom: 'var(--spacing-md)' }}>INVESTIGATION PROGRESSION</h2>

      <div className="audit-track-scroll">
        <div className="audit-track">
          {checkpoints.map((cp, idx) => {
            const node: NodeData = {
              type: 'CHECKPOINT',
              id: cp.id,
              title: cp.title,
              status: cp.status,
              investigation_question: cp.investigation_question,
              what_was_tested: cp.tested,
              what_changed: cp.what_changed,
              resulting_state: cp.resulting_state,
              content: cp.found,
              evidence_refs: cp.evidence_refs,
              source_refs: cp.source_refs,
              source_urls: getCitationUrls(cp.found, brief.traceability),
              provenance: cp.provenance,
            };
            const question = cp.investigation_question || cp.tested;
            const sourceCount = cp.source_refs?.length ?? (cp.provenance?.source_file ? 1 : 0);

            return (
              <article
                className="audit-panel clickable-panel"
                key={cp.id}
                role="button"
                tabIndex={0}
                onClick={() => onDetail(node)}
                onKeyDown={event => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    onDetail(node);
                  }
                }}
              >
                <div className="ap-header">
                  <div className="ap-num">{String(idx + 1).padStart(2, '0')}</div>
                  <div className="ap-title-wrapper">
                    <span className="ap-id">{cp.id}</span>
                    <h3 className="ap-title">{cp.title}</h3>
                  </div>
                </div>

                <div className="ap-body">
                  {cp.status && (
                    <div className="ap-primary-status"><StatusBadge status={cp.status} /></div>
                  )}
                  <div className="ap-field">
                    <span className="ap-label">QUESTION</span>
                    <PresentationText className="ap-value" lines={3}>{question}</PresentationText>
                  </div>
                  <div className="ap-field">
                    <span className="ap-label">FOUND</span>
                    <PresentationText className="ap-value" lines={4}>{cp.found}</PresentationText>
                  </div>
                  <div className="ap-field">
                    <span className="ap-label">STATE</span>
                    <div className="ap-value"><StatusBadge status={cp.resulting_state} /></div>
                  </div>
                  <div className="primary-card-footer ap-card-footer">
                    <SourceIndicator count={sourceCount} />
                    <button className="ap-detail-btn" onClick={event => { event.stopPropagation(); onDetail(node); }}>
                      VIEW DETAILS →
                    </button>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}


type GraphCategory = {
  id: string;
  label: string;
  nodes: NodeData[];
};

function ReasoningGraph({ brief, onDetail }: { brief: InvestigationBrief, onDetail: (n: NodeData) => void }) {
  const [activeCategory, setActiveCategory] = useState('ALL');
  const categories: GraphCategory[] = [
    {
      id: 'EVIDENCE',
      label: 'Evidence',
      nodes: (brief.evidence ?? []).map(e => ({
        type: 'EVIDENCE',
        id: e.id,
        content: e.statement,
        classification: e.classification,
        source: e.source,
        source_refs: e.source ? [e.source] : undefined,
        source_urls: getCitationUrls(e.statement, brief.traceability),
        provenance: e.provenance,
      })),
    },
    {
      id: 'CLAIMS',
      label: 'Claims',
      nodes: (brief.claims ?? []).map(c => ({
        type: 'CLAIM',
        id: c.id,
        content: c.statement,
        basis: c.evidence_basis,
        source_urls: getCitationUrls(c.statement, brief.traceability),
        provenance: c.provenance,
      })),
    },
    {
      id: 'INFERENCES',
      label: 'Inferences',
      nodes: (brief.inferences ?? []).map(i => ({
        type: 'INFERENCE',
        id: i.id,
        content: i.statement,
        basis: i.basis,
        implication: i.implication,
        source_urls: getCitationUrls(i.statement, brief.traceability),
        provenance: i.provenance,
      })),
    },
    {
      id: 'HYPOTHESES',
      label: 'Hypotheses',
      nodes: (brief.hypotheses ?? []).map(h => ({
        type: 'HYPOTHESIS',
        id: h.id,
        content: h.statement,
        status: h.status,
        basis: [...(h.supporting_basis || []), ...(h.falsification_basis || [])],
        source_urls: getCitationUrls(h.statement, brief.traceability),
        provenance: h.provenance,
      })),
    },
    {
      id: 'RESULTS',
      label: 'Results',
      nodes: (brief.results ?? []).map(r => ({
        type: 'RESULT',
        id: r.id,
        content: r.statement,
        status: r.status,
        source_urls: getCitationUrls(r.statement, brief.traceability),
        provenance: r.provenance,
      })),
    },
    {
      id: 'FALSIFICATION',
      label: 'Falsification',
      nodes: (brief.falsification ?? []).map((f, i) => ({
        type: 'FALSIFICATION',
        id: 'falsification-' + (i + 1),
        content: f.statement,
        status: f.outcome,
        basis: f.basis,
        source_urls: getCitationUrls(f.statement, brief.traceability),
        provenance: f.provenance,
      })),
    },
  ];
  const availableCategories = categories.filter(category => category.nodes.length > 0);
  const visibleCategories = activeCategory === 'ALL'
    ? availableCategories
    : availableCategories.filter(category => category.id === activeCategory);

  return (
    <div className="reasoning-graph">
      <div className="reasoning-graph-toolbar">
        <div>
          <div className="rap-label">REASONING GRAPH</div>
          <p className="reasoning-graph-help">Choose a category to scan the evidence chain. Open any card for the complete record.</p>
        </div>
        <div className="graph-category-tabs" role="tablist" aria-label="Reasoning graph categories">
          <button
            className={activeCategory === 'ALL' ? 'active' : ''}
            role="tab"
            aria-selected={activeCategory === 'ALL'}
            onClick={() => setActiveCategory('ALL')}
          >
            All <span>{availableCategories.reduce((total, category) => total + category.nodes.length, 0)}</span>
          </button>
          {availableCategories.map(category => (
            <button
              key={category.id}
              className={activeCategory === category.id ? 'active' : ''}
              role="tab"
              aria-selected={activeCategory === category.id}
              onClick={() => setActiveCategory(category.id)}
            >
              {category.label} <span>{category.nodes.length}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="reasoning-graph-grid">
        {visibleCategories.map(category => (
          <section className="reasoning-category" key={category.id} aria-label={category.label}>
            <h4 className="col-title">{category.label}</h4>
            <div className="reasoning-category-list">
              {category.nodes.map(node => (
                <ResearchNode
                  key={node.id}
                  onDetail={onDetail}
                  traceability={brief.traceability}
                  node={node}
                />
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

function ReasoningAuditPanel({
  brief,
  activeNode,
  onDetail,
  onClear,
  isOpen,
  onToggle
}: {
  brief: InvestigationBrief,
  activeNode: NodeData | null,
  onDetail: (n: NodeData) => void,
  onClear: () => void,
  isOpen: boolean,
  onToggle: () => void
}) {
  const hasEpistemic = brief.evidence?.length > 0 || brief.claims?.length > 0 || brief.inferences?.length > 0 || brief.hypotheses?.length > 0 || brief.results?.length > 0 || brief.falsification?.length > 0;
  const activeSourceIsKnownReference = Boolean(activeNode?.source && brief.sources.some(source => source.id === activeNode.source));
  const activeSourceText = activeNode?.source && !activeSourceIsKnownReference ? activeNode.source : undefined;
  const activeSourceRefs = activeNode
    ? [...new Set([
      ...(activeNode.source_refs ?? []),
      ...(activeNode.source && activeSourceIsKnownReference ? [activeNode.source] : []),
    ])]
    : [];
  if (!hasEpistemic && !activeNode) return null;

  return (
    <div className={`workspace-sidebar ${isOpen ? 'open' : 'closed'} audit-panel-sidebar`}>
      <button className="sidebar-toggle" onClick={onToggle}>
        {isOpen ? '◀ CLOSE REASONING GRAPH' : '▶ REASONING GRAPH'}
      </button>

      {isOpen && (
        <div className="sidebar-content rap-content">

          {activeNode ? (
            /* AUDIT DETAIL VIEW */
            <div className="rap-detail-view">
              <div className="rap-detail-header">
                <div className="rap-label">SELECTED OBJECT</div>
                <button className="rap-back-btn" onClick={onClear}>← Back to Graph</button>
              </div>

              <div className="rap-object-header">
                <div className="rap-object-type">{activeNode.type}</div>
                <div className="rap-object-id">{activeNode.id}</div>
                {activeNode.title && <div className="rap-object-title">{activeNode.title}</div>}
              </div>

              {activeNode.status && (
                <div className="rap-status-block">
                  <span className={`badge ${getStatusClass(activeNode.status)}`}>{activeNode.status}</span>
                </div>
              )}

              {activeNode.classification && (
                <div className="rap-status-block">
                  <span className="badge badge-class">{activeNode.classification}</span>
                </div>
              )}

              {(activeNode.content || activeNode.investigation_question) && (
                <div className="rap-block">
                  <div className="rap-label">{activeNode.type === 'CHECKPOINT' ? 'INVESTIGATION QUESTION' : 'WHAT THIS OBJECT SAYS'}</div>
                  <div className="rap-statement">
                    <MarkdownRenderer content={activeNode.type === 'CHECKPOINT' ? (activeNode.investigation_question || activeNode.content || '') : (activeNode.content || '')} />
                  </div>
                </div>
              )}

              {activeNode.type === 'CHECKPOINT' && activeNode.content && (
                <div className="rap-block">
                  <div className="rap-label">KEY FINDING</div>
                  <div className="rap-statement">
                    <MarkdownRenderer content={activeNode.content} />
                  </div>
                </div>
              )}

              {activeNode.what_was_tested && (
                <div className="rap-block">
                  <div className="rap-label">WHAT WAS TESTED</div>
                  <div className="rap-value"><MarkdownRenderer content={activeNode.what_was_tested} /></div>
                </div>
              )}

              {activeNode.what_changed && (
                <div className="rap-block">
                  <div className="rap-label">WHAT CHANGED</div>
                  <div className="rap-value"><MarkdownRenderer content={activeNode.what_changed} /></div>
                </div>
              )}

              {activeNode.resulting_state && (
                <div className="rap-block">
                  <div className="rap-label">RESULTING STATE</div>
                  <div className="rap-value"><MarkdownRenderer content={activeNode.resulting_state} /></div>
                </div>
              )}

              {activeNode.evidence_refs && activeNode.evidence_refs.length > 0 && (
                <div className="rap-block">
                  <div className="rap-label">EVIDENCE REFS</div>
                  <div className="rap-links">
                    {activeNode.evidence_refs.map(ref => (
                      <div key={ref} className="rap-link-card">
                        <span className="rap-link-id">← {ref}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeNode.implication && (
                <div className="rap-block">
                  <div className="rap-label">IMPLICATION</div>
                  <div className="rap-statement"><MarkdownRenderer content={activeNode.implication} /></div>
                </div>
              )}

              {/* DYNAMIC RELATIONSHIPS BASED ON TYPE */}
              <div className="rap-relationships">

                {activeNode.basis && activeNode.basis.length > 0 && (
                  <div className="rap-block">
                    <div className="rap-label">{activeNode.type === 'CLAIM' ? 'WHAT SUPPORTS THIS CLAIM' : activeNode.type === 'HYPOTHESIS' ? 'BASIS' : 'SUPPORTED BY'}</div>
                    <div className="rap-links">
                      {activeNode.basis.map(bId => {
                        const bNode =
                          brief.evidence?.find(x => x.id === bId) ||
                          brief.claims?.find(x => x.id === bId) ||
                          brief.inferences?.find(x => x.id === bId) ||
                          brief.hypotheses?.find(x => x.id === bId);
                        return (
                          <div key={bId} className="rap-link-card" onClick={() => {
                            if (bNode) onDetail({
                              type: brief.evidence?.some(x => x.id === bId) ? 'EVIDENCE' : brief.claims?.some(x => x.id === bId) ? 'CLAIM' : brief.inferences?.some(x => x.id === bId) ? 'INFERENCE' : 'HYPOTHESIS',
                              id: bId,
                              content: bNode.statement,
                              basis: (bNode as any).basis || (bNode as any).evidence_basis || [...((bNode as any).supporting_basis || []), ...((bNode as any).falsification_basis || [])],
                              provenance: bNode.provenance,
                              source: (bNode as any).source,
                              source_refs: (bNode as any).source ? [(bNode as any).source] : undefined,
                              source_urls: getCitationUrls(bNode.statement, brief.traceability),
                              classification: (bNode as any).classification,
                              status: (bNode as any).status
                            });
                          }}>
                            <span className="rap-link-id">← {bId}</span>
                            <div className="rap-link-desc">{bNode ? <MarkdownRenderer content={bNode.statement} className="markdown-compact" /> : null}</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Find what this object supports/leads to */}
                {(() => {
                  if (activeNode.type === 'EVIDENCE' || activeNode.type === 'CLAIM') {
                    const targets = activeNode.type === 'EVIDENCE'
                      ? brief.claims?.filter(c => c.evidence_basis?.includes(activeNode.id!))
                      : brief.inferences?.filter(i => i.basis?.includes(activeNode.id!));

                    if (targets && targets.length > 0) {
                      return (
                        <div className="rap-block">
                          <div className="rap-label">{activeNode.type === 'EVIDENCE' ? 'SUPPORTS' : 'WHAT DOES THIS CLAIM AFFECT?'}</div>
                          <div className="rap-links">
                            {targets.map(t => (
                              <div key={t.id} className="rap-link-card" onClick={() => {
                                onDetail({
                                  type: activeNode.type === 'EVIDENCE' ? 'CLAIM' : 'INFERENCE',
                                  id: t.id,
                                  content: t.statement,
                                  basis: (t as any).basis || (t as any).evidence_basis,
                                  source_urls: getCitationUrls(t.statement, brief.traceability),
                                  provenance: t.provenance
                                });
                              }}>
                                <span className="rap-link-id">→ {t.id}</span>
                                <div className="rap-link-desc"><MarkdownRenderer content={t.statement} className="markdown-compact" /></div>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    }
                  }

                  if (activeNode.type === 'INFERENCE') {
                    const targets = brief.hypotheses?.filter(h => h.supporting_basis?.includes(activeNode.id!) || h.falsification_basis?.includes(activeNode.id!));
                    if (targets && targets.length > 0) {
                      return (
                        <div className="rap-block">
                          <div className="rap-label">LEADS TO</div>
                          <div className="rap-links">
                            {targets.map(t => (
                              <div key={t.id} className="rap-link-card" onClick={() => {
                                onDetail({
                                  type: 'HYPOTHESIS', id: t.id, content: t.statement, status: t.status, basis: [...(t.supporting_basis || []), ...(t.falsification_basis || [])], source_urls: getCitationUrls(t.statement, brief.traceability), provenance: t.provenance
                                });
                              }}>
                                <span className="rap-link-id">→ {t.id}</span>
                                <div className="rap-link-desc"><MarkdownRenderer content={t.statement} className="markdown-compact" /></div>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    }
                  }

                  if (activeNode.type === 'HYPOTHESIS') {
                    // Just show all results for now if they are related
                    if (brief.results && brief.results.length > 0) {
                      return (
                        <div className="rap-block">
                          <div className="rap-label">RESULTS AFFECTING THIS HYPOTHESIS</div>
                          <div className="rap-links">
                            {brief.results.map(t => (
                              <div key={t.id} className="rap-link-card" onClick={() => {
                                onDetail({
                                  type: 'RESULT', id: t.id, content: t.statement, status: t.status, source_urls: getCitationUrls(t.statement, brief.traceability), provenance: t.provenance
                                });
                              }}>
                                <span className="rap-link-id">→ {t.id}</span>
                                <div className="rap-link-desc"><MarkdownRenderer content={t.statement} className="markdown-compact" /></div>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    }
                  }

                  if (activeNode.type === 'FALSIFICATION') {
                    // Show basis as 'WHAT WAS FALSIFIED'
                  }

                  return null;
                })()}

              </div>

              {/* SOURCES / EVIDENCE TRAY */}
              <div className="rap-divider"></div>

              {(activeNode.source || (activeNode.source_refs && activeNode.source_refs.length > 0) || (activeNode.source_urls && activeNode.source_urls.length > 0)) && (
                <div className="rap-block">
                  <div className="rap-label">ORIGINAL SOURCE</div>
                  <SourceAuditList
                    brief={brief}
                    sourceRefs={activeSourceRefs}
                    sourceUrls={activeNode.source_urls}
                    fallbackText={activeSourceText}
                  />
                </div>
              )}

              {activeNode.evidence_refs && activeNode.evidence_refs.length > 0 && (
                <div className="rap-block">
                  <div className="rap-label">EVIDENCE</div>
                  <div className="rap-sources">
                    {activeNode.evidence_refs.map(ref => {
                      const ev = brief.evidence?.find(e => e.id === ref);
                      return (
                        <div key={ref} className="rap-source-card" onClick={() => {
                          if (ev) onDetail({
                            type: 'EVIDENCE', id: ev.id, content: ev.statement, classification: ev.classification, source: ev.source, source_refs: ev.source ? [ev.source] : undefined, source_urls: getCitationUrls(ev.statement, brief.traceability), provenance: ev.provenance
                          });
                        }} style={{ cursor: 'pointer' }}>
                          <div className="rap-source-id">{ref}</div>
                          <div className="rap-source-title">{ev ? <MarkdownRenderer content={ev.statement} className="markdown-compact" /> : ''}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {activeNode.provenance && (
                <div className="rap-block rap-provenance-block">
                  <div className="rap-label">PROVENANCE</div>
                  <ProvenanceDetails provenance={activeNode.provenance} />
                </div>
              )}

            </div>
          ) : (
            <div className="rap-graph-view">
              <ReasoningGraph brief={brief} onDetail={onDetail} />
            </div>
          )}

        </div>
      )}
    </div>
  );
}

function buildServiceNowReusableIntelligence(brief: InvestigationBrief): IntelligenceObject[] {
  const objects = brief.decision?.reusable_intelligence || [];

  if (brief.investigation_id !== 'OPP-007' || !/servicenow/i.test(brief.company) || objects.length <= 1) {
    return objects;
  }

  const sourcesById = new Map(brief.sources.map(source => [source.id, source]));
  const firstExternalUrl = (refs?: string[]) => {
    if (!refs) return undefined;
    for (const ref of refs) {
      const url = sourcesById.get(ref)?.url;
      if (url && (url.startsWith('http://') || url.startsWith('https://'))) return url;
    }
    return undefined;
  };

  const sequence = [
    {
      id: 'SR-09',
      label: 'Exception-to-alternative-supplier workflow',
      insight: 'ServiceNow turns supplier shortfall into a guided exception path that finds an alternative supplier, reviews open orders, adjusts quantity or date, and revises the purchase order.'
    },
    {
      id: 'SR-10',
      label: 'Risk-integrated supplier record',
      insight: 'Risk and performance are brought into the same supplier record so the workflow can act on the current state, not on a stale snapshot.'
    },
    {
      id: 'SR-11',
      label: 'Qualification before execution',
      insight: 'Risk playbooks and supplier qualification occur before execution, which keeps control points inside the workflow instead of outside it.'
    },
    {
      id: 'SR-17',
      label: 'Native agentic procurement',
      insight: 'ServiceNow uses an agentic pattern where data produces an opportunity signal, an agent ranks it, and a human review step remains in the loop.'
    },
    {
      id: 'SR-22',
      label: 'State-change trigger',
      insight: 'The workflow is triggered by state change, which is the important design clue for ART.'
    },
    {
      id: 'SR-23',
      label: 'External-state integration',
      insight: 'Availability, shipment, and order-state data can be integrated into the procurement workflow as decision input.'
    },
    {
      id: 'SR-24',
      label: 'Reassessment workflow',
      insight: 'Risk reassessment is a named workflow step, not an implicit side effect.'
    },
  ];

  const sourceRows = sequence
    .map(item => {
      const obj = objects.find(candidate => candidate.id === item.id);
      const url = firstExternalUrl(obj?.source_refs);
      return url ? `| ${item.label} | [Open source ↗](${url}) |` : null;
    })
    .filter((row): row is string => Boolean(row));

  const sourceRefs = [...new Set(objects.flatMap(obj => obj.source_refs || []))];
  const provenance = objects[0]?.provenance ?? brief.decision?.provenance;

  return [{
    id: 'SN-OPP-007-CONCEPT',
    type: 'IMPLEMENTATION_PATTERN',
    title: 'ServiceNow — supplier-disruption decision continuity',
    domain: 'Supplier-Disruption Decision Continuity',
    description: [
      '# ServiceNow supplier-disruption implementation concept',
      '',
      `> Distilled from ${objects.length} raw reusable-intelligence items in the ServiceNow OPP-007 decision record.`,
      '',
      '## How ServiceNow implemented it',
      ...sequence.map(item => `- ${item.insight}`),
      '',
      '## What ART must learn',
      '- Model the trigger, exception, reassessment, and execution as one loop.',
      '- Treat external state as a first-class decision input.',
      '- Keep human review in the loop even when an agent assists the workflow.',
      '- Preserve provenance and source links from the raw JSON and Markdown sources.',
      '',
      '## Source anchors',
      '| Concept | Link |',
      '|---|---|',
      ...sourceRows,
    ].join('\n'),
    pattern: [
      '```text',
      'SUPPLIER SHORTFALL',
      '↓',
      'OPEN EXCEPTION',
      '↓',
      'FIND ALTERNATIVE SUPPLIERS',
      '↓',
      'REVIEW OPEN ORDERS',
      '↓',
      'UPDATE QUANTITY / DATE',
      '↓',
      'PO REVISION',
      '```',
    ].join('\n'),
    lesson: 'ServiceNow implements a stateful decision loop, not a one-shot feature list.',
    art_learning: 'ART should model the trigger, the exception, the reassessment, and the execution step as one loop with traceable sources.',
    art_improvement: 'One concept card is more honest than 14 fragmented cards when the raw JSON is describing a single implementation pattern.',
    conditions: [
      'State change must be first-class.',
      'External system data must enter the workflow.',
      'Human review stays in the loop.',
      'Reassessment must be explicit.',
    ],
    evidence_status: 'VERIFIED',
    status: 'ACTIVE',
    confidence: 'HIGH',
    reuse_potential: 'HIGH',
    applications: [
      'Supplier disruption response',
      'Procurement exception orchestration',
      'Dynamic reassessment workflows',
    ],
    source_checkpoint: 'OPP-007 raw reusable intelligence',
    source_refs: sourceRefs,
    source_location: 'Distilled from the raw ServiceNow OPP-007 reusable-intelligence cluster.',
    original_source: 'src/data/investigations/industries/IT & Business Services/servicenow/OPP-007.json',
    tags: ['servicenow', 'supplier-disruption', 'workflow-pattern', 'reassessment', 'agentic-procurement'],
    provenance,
  }];
}

const CATEGORY_LABELS: Record<string, string> = {
  'WORKFLOW_PATTERN': 'Workflow Patterns',
  'STRATEGY_PATTERN': 'Strategies',
  'DECISION_PATTERN': 'Decision Patterns',
  'IMPLEMENTATION_PATTERN': 'Implementation Patterns',
  'ARCHITECTURE_PATTERN': 'Architecture Patterns',
  'GUARDRAIL': 'Guardrails',
  'METRIC_PATTERN': 'Metrics',
  'RESEARCH_METHOD': 'Research Methods',
  'DESIGN_PRINCIPLE': 'Design Principles',
  'NEGATIVE_INTELLIGENCE': 'Negative Intelligence',
  'ART_IMPROVEMENT': 'ART Improvement',
};

function ReusableIntelligenceSidebar({ brief, isOpen, onToggle }: { brief: InvestigationBrief, isOpen: boolean, onToggle: () => void }) {
  const objects = useMemo(() => buildServiceNowReusableIntelligence(brief), [brief]);

  const [activeObject, setActiveObject] = useState<IntelligenceObject | null>(null);

  useEffect(() => {
    setActiveObject(null);
  }, [brief.investigation_id]);

  // Group objects by type
  const groups = objects.reduce((acc, obj) => {
    if (!acc[obj.type]) acc[obj.type] = [];
    acc[obj.type].push(obj);
    return acc;
  }, {} as Record<string, IntelligenceObject[]>);

  if (!objects.length) return null;

  return (
    <div className={`workspace-sidebar sidebar-right ${isOpen ? 'open' : 'closed'} audit-panel-sidebar`}>
      <button className="sidebar-toggle" onClick={onToggle}>
        {isOpen ? '▶ CLOSE INTELLIGENCE' : '◀ REUSABLE INTELLIGENCE'}
      </button>

      {isOpen && (
        <div className="sidebar-content rap-content" style={{ padding: '32px 24px 24px 24px' }}>
          <h2 className="zone-title" style={{ fontSize: '11px', letterSpacing: '0.1em', marginBottom: '24px' }}>REUSABLE INTELLIGENCE</h2>

          {!activeObject && (
            <div className="intel-overview">
              <div className="intel-category-list">
                {Object.keys(CATEGORY_LABELS).map(key => {
                  if (key === 'ART_IMPROVEMENT') return null;
                  const items = groups[key] || [];
                  if (items.length === 0) return null;

                  return (
                    <div key={key} className="intel-category-group" style={{ marginBottom: '16px' }}>
                      <div className="intel-object-list">
                        {items.map(obj => (
                          <div key={obj.id} className="intel-object-card" onClick={() => setActiveObject(obj)}>
                            <div className="intel-obj-id">{obj.id}</div>
                            <h4 className="intel-obj-title">{obj.title}</h4>
                            <div className="intel-card-footer">
                              <SourceIndicator count={obj.source_refs?.length ?? 0} />
                              <span>VIEW DETAILS →</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}

                {groups['ART_IMPROVEMENT']?.length > 0 && (
                  <div key="ART_IMPROVEMENT" className="intel-category-group art-improvement" style={{ marginBottom: '16px' }}>
                    <div className="intel-object-list">
                      {groups['ART_IMPROVEMENT'].map(obj => (
                        <div key={obj.id} className="intel-object-card" onClick={() => setActiveObject(obj)}>
                          <div className="intel-obj-id">{obj.id}</div>
                          <h4 className="intel-obj-title">{obj.title}</h4>
                          <div className="intel-card-footer">
                            <SourceIndicator count={obj.source_refs?.length ?? 0} />
                            <span>VIEW DETAILS →</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeObject && (
            <div className="intel-object-detail">
              <button className="intel-back-btn" onClick={() => setActiveObject(null)}>
                &larr; BACK TO LIBRARY
              </button>

              <div className="intel-detail-header">
                <span className="intel-detail-type">{CATEGORY_LABELS[activeObject.type]}</span>
                <span className="intel-detail-id">{activeObject.id}</span>
                <h2 className="intel-detail-title">{activeObject.title}</h2>
              </div>

              {activeObject.domain && (
                <div className="rap-block">
                  <div className="rap-label">DOMAIN</div>
                  <div className="rap-value"><MarkdownRenderer content={activeObject.domain} /></div>
                </div>
              )}

              {activeObject.description && (
                <div className="rap-block">
                  <div className="rap-label">DESCRIPTION</div>
                  <div className="rap-statement"><MarkdownRenderer content={activeObject.description} /></div>
                </div>
              )}

              {activeObject.pattern && (
                <div className="rap-block">
                  <div className="rap-label">PATTERN</div>
                  <div className="intel-pattern-block"><MarkdownRenderer content={activeObject.pattern} className="markdown-compact" /></div>
                </div>
              )}

              {activeObject.lesson && (
                <div className="rap-block">
                  <div className="rap-label">ART LESSON</div>
                  <div className="rap-value" style={{ fontStyle: 'italic' }}><MarkdownRenderer content={activeObject.lesson} /></div>
                </div>
              )}

              {activeObject.art_learning && (
                <div className="rap-block">
                  <div className="rap-label">ART LEARNING</div>
                  <div className="rap-value"><MarkdownRenderer content={activeObject.art_learning} /></div>
                </div>
              )}

              {activeObject.art_improvement && (
                <div className="rap-block">
                  <div className="rap-label">ART IMPROVEMENT</div>
                  <div className="rap-value"><MarkdownRenderer content={activeObject.art_improvement} /></div>
                </div>
              )}

              {activeObject.anti_pattern && (
                <div className="rap-block">
                  <div className="rap-label">ANTI-PATTERN</div>
                  <div className="rap-value"><MarkdownRenderer content={activeObject.anti_pattern} /></div>
                </div>
              )}

              {activeObject.do_not_assume && (
                <div className="rap-block">
                  <div className="rap-label">DO NOT ASSUME</div>
                  {Array.isArray(activeObject.do_not_assume) ? (
                    <ul style={{ margin: 0, paddingLeft: '1.2rem', color: 'var(--color-text)' }}>
                      {activeObject.do_not_assume.map((dna, idx) => <li key={idx} style={{ marginBottom: '4px' }}><MarkdownRenderer content={dna} /></li>)}
                    </ul>
                  ) : (
                    <div className="rap-value"><MarkdownRenderer content={activeObject.do_not_assume} /></div>
                  )}
                </div>
              )}

              {activeObject.conditions && activeObject.conditions.length > 0 && (
                <div className="rap-block">
                  <div className="rap-label">CONDITIONS</div>
                  <ul style={{ margin: 0, paddingLeft: '1.2rem', color: 'var(--color-text)' }}>
                    {activeObject.conditions.map((cond, idx) => <li key={idx} style={{ marginBottom: '4px' }}><MarkdownRenderer content={cond} /></li>)}
                  </ul>
                </div>
              )}

              {activeObject.applications && activeObject.applications.length > 0 && (
                <div className="rap-block">
                  <div className="rap-label">APPLICATIONS</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                    {activeObject.applications.map((app, idx) => (
                      <span key={idx} style={{ background: 'var(--color-bg-secondary)', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', color: 'var(--color-text)' }}>{app}</span>
                    ))}
                  </div>
                </div>
              )}

              {activeObject.tags && activeObject.tags.length > 0 && (
                <div className="rap-block">
                  <div className="rap-label">TAGS</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                    {activeObject.tags.map((tag, idx) => (
                      <span key={idx} style={{ background: 'var(--color-border)', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontFamily: 'monospace' }}>#{tag}</span>
                    ))}
                  </div>
                </div>
              )}

              <div className="rap-divider"></div>

              <div className="intel-meta-grid">
                {activeObject.status && (
                  <div className="intel-meta-item">
                    <span className="rap-label">STATUS</span>
                    <span className="intel-meta-val">{activeObject.status}</span>
                  </div>
                )}
                {activeObject.evidence_status && (
                  <div className="intel-meta-item">
                    <span className="rap-label">EVIDENCE</span>
                    <span className="intel-meta-val">{activeObject.evidence_status}</span>
                  </div>
                )}
                {activeObject.reuse_potential && (
                  <div className="intel-meta-item">
                    <span className="rap-label">REUSE</span>
                    <span className="intel-meta-val">{activeObject.reuse_potential}</span>
                  </div>
                )}
                {activeObject.source_checkpoint && (
                  <div className="intel-meta-item">
                    <span className="rap-label">SOURCE</span>
                    <span className="intel-meta-val">{activeObject.source_checkpoint}</span>
                  </div>
                )}
                {activeObject.confidence && (
                  <div className="intel-meta-item">
                    <span className="rap-label">CONFIDENCE</span>
                    <span className="intel-meta-val">{activeObject.confidence}</span>
                  </div>
                )}
              </div>

              {activeObject.source_location && (
                <div className="rap-block">
                  <div className="rap-label">SOURCE LOCATION</div>
                  <div className="rap-value"><MarkdownRenderer content={activeObject.source_location} /></div>
                </div>
              )}

              {activeObject.original_source && (
                <div className="rap-block">
                  <div className="rap-label">ORIGINAL SOURCE</div>
                  <div className="rap-value"><MarkdownRenderer content={activeObject.original_source} /></div>
                </div>
              )}

              <div className="rap-block intel-source-audit-block">
                <div className="rap-label">SOURCE REFERENCES</div>
                <SourceAuditList
                  brief={brief}
                  sourceRefs={activeObject.source_refs}
                />
              </div>

              <div className="rap-block rap-provenance-block">
                <div className="rap-label">PROVENANCE</div>
                <ProvenanceDetails provenance={activeObject.provenance} />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// NodeDetailPanel removed in favor of integrated ReasoningAuditPanel

// --------------------------------------------------
// MAIN WORKSPACE
// --------------------------------------------------

export function Walkthrough() {
  const searchParams = useSearchParams();
  const selectedIndustry = searchParams.get('industry')?.trim() ?? '';
  const [allBriefs, setAllBriefs] = useState<InvestigationBrief[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    try {
      setAllBriefs(loadAllInvestigationBriefs());
      setLoadError(null);
    } catch (error) {
      console.error('Failed to load investigation briefs for walkthrough:', error);
      setLoadError('Unable to load investigation briefs right now.');
    }
  }, []);

  const loadErrorBanner = loadError ? (
    <section className="investigation-hero" style={{ padding: '48px', minHeight: '60vh' }}>
      <div className="hero-grid">
        <div className="hero-main">
          <div className="hero-id-row">
            <span className="hero-id-pill">UNAVAILABLE</span>
            <span className="hero-type-text">LOAD ERROR</span>
          </div>
          <h1 className="hero-title">Walkthrough unavailable</h1>
          <div className="hero-company-line">{loadError}</div>
          <div className="hero-meta-row">
            <div className="hero-meta-item">
              <span className="hero-meta-label">What happened</span>
              <div className="hero-meta-value">One or more investigation briefs failed validation during load.</div>
            </div>
            <div className="hero-meta-item">
              <span className="hero-meta-label">Next step</span>
              <div className="hero-meta-value">Fix the invalid brief data, then refresh the page.</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  ) : null;

  const industryBriefs = useMemo(() => {
    if (!selectedIndustry) return allBriefs;
    return allBriefs.filter(b =>
      b.industry === selectedIndustry || b.industry.startsWith(selectedIndustry + ' /')
    );
  }, [allBriefs, selectedIndustry]);

  const companies = useMemo(
    () => [...new Set(industryBriefs.map(b => b.company))],
    [industryBriefs],
  );
  const [selectedCompany, setSelectedCompany] = useState(companies[0] ?? '');

  useEffect(() => {
    setSelectedCompany(current =>
      companies.includes(current) ? current : (companies[0] ?? '')
    );
  }, [companies]);

  const companyBriefs = useMemo(
    () => industryBriefs.filter(b => b.company === selectedCompany),
    [industryBriefs, selectedCompany],
  );
  const [opportunityId, setOpportunityId] = useState(companyBriefs[0]?.investigation_id ?? '');

  useEffect(() => {
    setOpportunityId(companyBriefs[0]?.investigation_id ?? '');
  }, [selectedCompany, companyBriefs]);

  const brief = useMemo(
    () => companyBriefs.find(b => b.investigation_id === opportunityId) ?? companyBriefs[0],
    [opportunityId, companyBriefs],
  );

  const [activeNode, setActiveNode] = useState<NodeData | null>(null);
  const [isReasoningOpen, setIsReasoningOpen] = useState(false);
  const openDetail = (node: NodeData) => {
    setActiveNode(node);
    setIsReasoningOpen(true);
  };
  const [isIntelligenceOpen, setIsIntelligenceOpen] = useState(false);

  return (
    <div className="investigation-workspace">
      {loadErrorBanner}
      <div className="workspace-layout">
        {brief && (
          <ReasoningAuditPanel
            brief={brief}
            activeNode={activeNode}
            onDetail={openDetail}
            onClear={() => setActiveNode(null)}
            isOpen={isReasoningOpen}
            onToggle={() => setIsReasoningOpen(!isReasoningOpen)}
          />
        )}

        <main className="workspace-main">
          <InvestigationHero
            brief={brief}
            opportunityId={opportunityId}
            onOpportunityChange={(id) => {
              setOpportunityId(id);
              setActiveNode(null);
            }}
            companies={companies}
            selectedCompany={selectedCompany}
            onCompanyChange={setSelectedCompany}
            companyBriefs={companyBriefs}
          />
          <InvestigationSignalStrip brief={brief} />
          <div className="main-content-scroll">
            {brief ? (
              <>
                <InvestigationOverview brief={brief} onDetail={openDetail} />
                <InvestigationProgression brief={brief} onDetail={openDetail} />
              </>
            ) : (
              <section className="zone walkthrough-empty-state">
                <h2 className="zone-title">YET TO EXPLORE</h2>
                <p>No investigation workflow is available for this industry yet.</p>
              </section>
            )}
          </div>
        </main>

        {brief && (
          <ReusableIntelligenceSidebar
            brief={brief}
            isOpen={isIntelligenceOpen}
            onToggle={() => setIsIntelligenceOpen(!isIntelligenceOpen)}
          />
        )}
      </div>
    </div>
  );
}
