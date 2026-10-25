import { useMemo, useState } from 'react';
const data = {} as any;
import type {
  AoiCheckpoint,
  AoiIntelligence,
  AoiOpportunity,
  AoiSource,
  AoiNormalizedData,
} from '../../types/aoiSemantic';
import './AOIExplorer.css';

const AOI_DATA = data as unknown as AoiNormalizedData;
const NOT_PROVIDED = 'NOT PROVIDED';
const UNCLASSIFIED = 'UNCLASSIFIED';

type ExplorerView = 'company' | 'intelligence';

interface EnrichedIntelligence extends AoiIntelligence {
  opportunityId: string;
  company: string;
  opportunityTitle: string;
}

function display(value: string | null | undefined, fallback = NOT_PROVIDED): string {
  return value?.trim() || fallback;
}

function unique(values: string[]): string[] {
  return [...new Set(values.filter(Boolean))];
}

function opportunityTitle(opportunity: AoiOpportunity): string {
  return display(
    opportunity.metadata.title &&
      opportunity.metadata.title !== opportunity.metadata.opportunity_id
      ? opportunity.metadata.title
      : opportunity.metadata.original_opportunity || opportunity.metadata.refined_opportunity,
  );
}

function sourceMap(opportunity: AoiOpportunity): Map<string, AoiSource> {
  return new Map(opportunity.sources.map(source => [source.id, source]));
}

function SourceLinks({ ids, sources }: { ids: string[]; sources: Map<string, AoiSource> }) {
  const records = ids.map(id => sources.get(id)).filter((source): source is AoiSource => Boolean(source));
  if (records.length === 0) return <span className="aoi-muted">{NOT_PROVIDED}</span>;
  return (
    <div className="aoi-source-links">
      {records.map(source => (
        <a href={source.url} target="_blank" rel="noreferrer" key={source.id}>
          {display(source.name, source.url)}
        </a>
      ))}
    </div>
  );
}

function Badge({ children, tone = '' }: { children: string; tone?: string }) {
  return <span className={'aoi-badge ' + tone}>{children}</span>;
}



function CompanyView({
  opportunities,
  selectedOpportunityId,
  selectedCheckpointId,
  onSelectOpportunity,
  onSelectCheckpoint,
  onOpenIntelligence,
}: {
  opportunities: AoiOpportunity[];
  selectedOpportunityId: string;
  selectedCheckpointId: string | null;
  onSelectOpportunity: (id: string) => void;
  onSelectCheckpoint: (id: string | null) => void;
  onOpenIntelligence: () => void;
}) {
  const companies = unique(opportunities.map(opportunity => display(opportunity.metadata.company)));
  const [company, setCompany] = useState(companies[0] ?? NOT_PROVIDED);
  const companyOpportunities = opportunities.filter(opportunity => display(opportunity.metadata.company) === company);
  const selectedOpportunity = companyOpportunities.find(opportunity => opportunity.metadata.opportunity_id === selectedOpportunityId) ?? companyOpportunities[0] ?? null;
  const selectedCheckpoint = selectedOpportunity?.checkpoints.find(checkpoint => checkpoint.id === selectedCheckpointId) ?? null;
  const distribution = unique(companyOpportunities.map(opportunity => display(opportunity.metadata.aoi_decision))).map(decision => ({
    decision,
    count: companyOpportunities.filter(opportunity => display(opportunity.metadata.aoi_decision) === decision).length,
  }));
  const intelligence = companyOpportunities.flatMap(opportunity => opportunity.intelligence);
  const readyCount = companyOpportunities.filter(opportunity => opportunity.metadata.ail_status === 'READY FOR AIL').length;

  return (
    <main className="aoi-explorer-body">
      <header className="aoi-view-header">
        <div>
          <div className="aoi-kicker">AOI / COMPANY EXPLORATION</div>
          <h1>{company}</h1>
          <p>Company is a parent view. Each opportunity remains an independent investigation.</p>
        </div>
        {companies.length > 1 && (
          <label className="aoi-select-label">COMPANY
            <select value={company} onChange={event => setCompany(event.target.value)}>
              {companies.map(item => <option key={item}>{item}</option>)}
            </select>
          </label>
        )}
      </header>

      <section className="aoi-summary-grid" aria-label="Company summary">
        <div><span>OPPORTUNITIES</span><strong>{companyOpportunities.length}</strong></div>
        <div><span>DECISION DISTRIBUTION</span><strong>{distribution.map(item => item.count + ' ' + item.decision).join(' · ') || NOT_PROVIDED}</strong></div>
        <div><span>AIL-READY COUNT</span><strong>{readyCount}</strong></div>
        <div><span>REUSABLE INTELLIGENCE</span><strong>{intelligence.length}</strong></div>
      </section>

      <section className="aoi-company-grid">
        <div className="aoi-panel">
          <div className="aoi-panel-heading"><span>OPPORTUNITY REGISTER</span><small>{companyOpportunities.length} independent investigations</small></div>
          <div className="aoi-opportunity-list">
            {companyOpportunities.map(opportunity => (
              <button
                className={'aoi-opportunity-row ' + (selectedOpportunity?.metadata.opportunity_id === opportunity.metadata.opportunity_id ? 'selected' : '')}
                key={opportunity.metadata.opportunity_id}
                onClick={() => {
                  onSelectOpportunity(opportunity.metadata.opportunity_id);
                  onSelectCheckpoint(null);
                }}
              >
                <span className="aoi-id">{opportunity.metadata.opportunity_id}</span>
                <strong>{opportunityTitle(opportunity)}</strong>
                <span>{display(opportunity.metadata.aoi_decision)} · {display(opportunity.metadata.ail_status)}</span>
                <small>{opportunity.checkpoints.length} checkpoints</small>
              </button>
            ))}
          </div>
        </div>

        {selectedOpportunity && (
          <OpportunityDetail
            opportunity={selectedOpportunity}
            checkpoint={selectedCheckpoint}
            onSelectCheckpoint={onSelectCheckpoint}
            onOpenIntelligence={onOpenIntelligence}
          />
        )}
      </section>
    </main>
  );
}

function OpportunityDetail({
  opportunity,
  checkpoint,
  onSelectCheckpoint,
  onOpenIntelligence,
}: {
  opportunity: AoiOpportunity;
  checkpoint: AoiCheckpoint | null;
  onSelectCheckpoint: (id: string | null) => void;
  onOpenIntelligence: () => void;
}) {
  const sources = sourceMap(opportunity);
  const evidence = checkpoint
    ? checkpoint.evidence_ids.map(id => opportunity.evidence.find(item => item.id === id)).filter(Boolean)
    : [];
  const decisions = checkpoint
    ? checkpoint.decision_ids.map(id => opportunity.decisions.find(item => item.id === id)).filter(Boolean)
    : [];

  return (
    <div className="aoi-panel aoi-opportunity-detail">
      <div className="aoi-panel-heading"><span>OPPORTUNITY DETAIL</span><small>{opportunity.metadata.opportunity_id}</small></div>
      <h2>{opportunityTitle(opportunity)}</h2>
      <div className="aoi-detail-badges">
        <Badge tone="danger">{display(opportunity.metadata.aoi_decision)}</Badge>
        <Badge>{display(opportunity.metadata.ail_status)}</Badge>
      </div>
      <p className="aoi-detail-copy">{display(opportunity.metadata.investigation_scope, opportunity.metadata.original_opportunity)}</p>

      <div className="aoi-subsection">
        <div className="aoi-subsection-heading">CHECKPOINTS / SELECT TO INSPECT</div>
        <div className="aoi-checkpoint-list">
          {opportunity.checkpoints.map(item => (
            <button className={checkpoint?.id === item.id ? 'selected' : ''} key={item.id} onClick={() => onSelectCheckpoint(checkpoint?.id === item.id ? null : item.id)}>
              <span>{String(item.sequence).padStart(2, '0')}</span>
              <strong>{item.id}</strong>
              <small>{display(item.title)}</small>
            </button>
          ))}
        </div>
      </div>

      {checkpoint && (
        <div className="aoi-checkpoint-detail">
          <div className="aoi-subsection-heading">CHECKPOINT / {checkpoint.id}</div>
          <p>{display(checkpoint.title)}</p>
          <div className="aoi-detail-line"><span>TYPE</span><strong>{display(checkpoint.investigation_type)}</strong></div>
          <div className="aoi-detail-line"><span>STATUS</span><strong>{display(checkpoint.status)}</strong></div>
          <div className="aoi-detail-line"><span>EVIDENCE</span><strong>{evidence.length}</strong></div>
          {evidence.map(item => item && (
            <div className="aoi-evidence-record" key={item.id}>
              <Badge>{display(item.classification)}</Badge>
              <p>{display(item.statement)}</p>
              <SourceLinks ids={item.source_ids} sources={sources} />
            </div>
          ))}
          {decisions.map(item => item && (
            <div className="aoi-evidence-record" key={item.id}>
              <Badge tone="danger">{display(item.value)}</Badge>
              <p>{display(item.statement)}</p>
            </div>
          ))}
        </div>
      )}

      <div className="aoi-subsection">
        <div className="aoi-subsection-heading">WORKFLOW RECORDS / NOT AGGREGATED</div>
        {opportunity.workflows.map(workflow => (
          <div className="aoi-record-line" key={workflow.id}>
            <strong>{workflow.title}</strong>
            <span>{display(workflow.status)} · {display(workflow.classification)}</span>
            <small>{workflow.checkpoint_ids.length ? workflow.checkpoint_ids.join(' · ') : NOT_PROVIDED}</small>
          </div>
        ))}
      </div>

      <div className="aoi-subsection">
        <div className="aoi-subsection-heading">ASSOCIATED INTELLIGENCE</div>
        {opportunity.intelligence.length ? opportunity.intelligence.slice(0, 6).map(item => (
          <button className="aoi-intelligence-link" key={item.id} onClick={onOpenIntelligence}>
            <strong>{item.name}</strong><span>{display(item.classification, UNCLASSIFIED)}</span>
          </button>
        )) : <span className="aoi-muted">{NOT_PROVIDED}</span>}
      </div>
    </div>
  );
}

function IntelligenceView({
  opportunities,
  selectedIntelligenceId,
  onSelectIntelligence,
  onOpenOrigin,
}: {
  opportunities: AoiOpportunity[];
  selectedIntelligenceId: string | null;
  onSelectIntelligence: (id: string) => void;
  onOpenOrigin: (opportunityId: string, checkpointId: string | null) => void;
}) {
  const [category, setCategory] = useState('ALL');
  const [company, setCompany] = useState('ALL');
  const [opportunityId, setOpportunityId] = useState('ALL');
  const records = useMemo<EnrichedIntelligence[]>(
    () => opportunities.flatMap(opportunity => opportunity.intelligence.map(item => ({
      ...item,
      opportunityId: opportunity.metadata.opportunity_id,
      company: display(opportunity.metadata.company),
      opportunityTitle: opportunityTitle(opportunity),
    }))),
    [opportunities],
  );
  const categories = unique(records.map(item => item.category?.trim() || UNCLASSIFIED));
  const companies = unique(records.map(item => item.company));
  const filteredOpportunities = opportunities.filter(item => company === 'ALL' || display(item.metadata.company) === company);
  const filtered = records.filter(item =>
    (category === 'ALL' || (item.category?.trim() || UNCLASSIFIED) === category) &&
    (company === 'ALL' || item.company === company) &&
    (opportunityId === 'ALL' || item.opportunityId === opportunityId),
  );
  const selected = filtered.find(item => item.id === selectedIntelligenceId) ?? records.find(item => item.id === selectedIntelligenceId) ?? null;
  const selectedOpportunity = selected ? opportunities.find(item => item.metadata.opportunity_id === selected.opportunityId) : null;
  const selectedSources = selectedOpportunity ? sourceMap(selectedOpportunity) : new Map<string, AoiSource>();

  return (
    <main className="aoi-explorer-body">
      <header className="aoi-view-header">
        <div>
          <div className="aoi-kicker">AOI / REUSABLE INTELLIGENCE</div>
          <h1>Intelligence register</h1>
          <p>Only intelligence records present in the normalized AOI model are shown. Categories are not inferred.</p>
        </div>
      </header>

      <section className="aoi-filter-bar" aria-label="Intelligence filters">
        <label>CATEGORY
          <select value={category} onChange={event => setCategory(event.target.value)}>
            <option value="ALL">ALL CATEGORIES</option>
            {categories.map(item => <option key={item} value={item}>{item}</option>)}
          </select>
        </label>
        <label>COMPANY
          <select value={company} onChange={event => {
            setCompany(event.target.value);
            setOpportunityId('ALL');
          }}>
            <option value="ALL">ALL COMPANIES</option>
            {companies.map(item => <option key={item} value={item}>{item}</option>)}
          </select>
        </label>
        <label>OPPORTUNITY
          <select value={opportunityId} onChange={event => setOpportunityId(event.target.value)}>
            <option value="ALL">ALL OPPORTUNITIES</option>
            {filteredOpportunities.map(item => <option key={item.metadata.opportunity_id} value={item.metadata.opportunity_id}>{item.metadata.opportunity_id}</option>)}
          </select>
        </label>
      </section>

      <section className="aoi-intelligence-grid">
        <div className="aoi-panel">
          <div className="aoi-panel-heading"><span>INTELLIGENCE ITEMS</span><small>{filtered.length} records</small></div>
          <div className="aoi-intelligence-list">
            {filtered.map(item => (
              <button className={'aoi-intelligence-card ' + (item.id === selected?.id ? 'selected' : '')} key={item.id} onClick={() => onSelectIntelligence(item.id)}>
                <div><Badge>{item.category?.trim() || UNCLASSIFIED}</Badge><Badge tone="status">{display(item.classification)}</Badge></div>
                <strong>{item.name}</strong>
                <span>{item.company} · {item.opportunityId}</span>
              </button>
            ))}
            {filtered.length === 0 && <p className="aoi-muted">No normalized intelligence records match these filters.</p>}
          </div>
        </div>

        {selected && selectedOpportunity && (
          <aside className="aoi-panel aoi-intelligence-detail" aria-label="Reusable intelligence detail">
            <div className="aoi-panel-heading"><span>INTELLIGENCE DETAIL</span><small>{selected.id}</small></div>
            <h2>{selected.name}</h2>
            <div className="aoi-detail-badges">
              <Badge>{selected.category?.trim() || UNCLASSIFIED}</Badge>
              <Badge tone="status">{display(selected.classification)}</Badge>
            </div>
            <div className="aoi-origin-block">
              <span>SOURCE OPPORTUNITY</span>
              <button onClick={() => onOpenOrigin(selected.opportunityId, selected.checkpoint_ids[0] ?? null)}>{selected.opportunityId} · {selected.company}</button>
              <small>{selected.opportunityTitle}</small>
            </div>
            <div className="aoi-origin-block">
              <span>SOURCE CHECKPOINT</span>
              {selected.checkpoint_ids.length ? selected.checkpoint_ids.map(checkpointId => (
                <button key={checkpointId} onClick={() => onOpenOrigin(selected.opportunityId, checkpointId)}>{checkpointId}</button>
              )) : <small>{NOT_PROVIDED}</small>}
            </div>
            <div className="aoi-detail-copy">{display(selected.implementation_mechanism, selected.workflow || selected.problem)}</div>
            <div className="aoi-field-block"><span>APPLICABILITY</span><p>{display(selected.applicability)}</p></div>
            <div className="aoi-field-block"><span>LIMITATIONS</span><p>{display(selected.limitations)}</p></div>
            <div className="aoi-field-block"><span>SOURCE REFERENCES</span><SourceLinks ids={selected.source_ids} sources={selectedSources} /></div>
          </aside>
        )}
      </section>
    </main>
  );
}

export function AOIExplorer({ view, onViewChange }: { view: ExplorerView; onViewChange: (view: ExplorerView) => void }) {
  const opportunities = AOI_DATA.opportunities;
  const [selectedOpportunityId, setSelectedOpportunityId] = useState(opportunities[0]?.metadata.opportunity_id ?? '');
  const [selectedCheckpointId, setSelectedCheckpointId] = useState<string | null>(null);
  const [selectedIntelligenceId, setSelectedIntelligenceId] = useState<string | null>(null);

  return (
    <section className="aoi-explorer" aria-label="AOI company and intelligence explorer">
      {view === 'company' ? (
        <CompanyView
          opportunities={opportunities}
          selectedOpportunityId={selectedOpportunityId}
          selectedCheckpointId={selectedCheckpointId}
          onSelectOpportunity={setSelectedOpportunityId}
          onSelectCheckpoint={setSelectedCheckpointId}
          onOpenIntelligence={() => onViewChange('intelligence')}
        />
      ) : (
        <IntelligenceView
          opportunities={opportunities}
          selectedIntelligenceId={selectedIntelligenceId}
          onSelectIntelligence={setSelectedIntelligenceId}
          onOpenOrigin={(opportunityId, checkpointId) => {
            setSelectedOpportunityId(opportunityId);
            setSelectedCheckpointId(checkpointId);
            onViewChange('company');
          }}
        />
      )}
    </section>
  );
}
