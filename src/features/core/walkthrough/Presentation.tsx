import { forwardRef, type CSSProperties, type ReactNode } from 'react';
import type { InvestigationBrief, InvestigationSource, Provenance } from '../../../types/investigationBrief';
import { MarkdownRenderer } from './MarkdownRenderer';

export const NOT_PROVIDED = 'NOT PROVIDED';

function stripOpportunityMetadata(value: string): string {
  return value.replace(/^\s*OPP-[0-9]+(?:-[0-9]+)*\s*[—-]\s*/i, '').trim();
}

export function hasWorkflow(brief: InvestigationBrief): boolean {
  const workflows = (brief as InvestigationBrief & { workflows?: { nodes?: unknown[] }[] }).workflows;
  return Array.isArray(workflows) && workflows.some(workflow => Boolean(
    workflow && Array.isArray(workflow.nodes) && workflow.nodes.length > 0,
  ));
}

export function opportunityLabel(brief: InvestigationBrief): string {
  const title = brief.opportunity || brief.investigation_id || 'Yet to explore';
  return stripOpportunityMetadata(title);
}

export const PresentationText = forwardRef<HTMLDivElement, {
  children: ReactNode;
  lines?: number;
  className?: string;
}>(({ children, lines = 3, className = '' }, ref) => {
  const content = typeof children === 'string'
    ? <MarkdownRenderer content={children} className="markdown-compact" />
    : children;

  return (
    <div
      className={'presentation-text ' + className}
      style={{ '--presentation-lines': lines } as CSSProperties}
      ref={ref}
    >
      {content}
    </div>
  );
});

export function SourceIndicator({ count }: { count: number }) {
  return (
    <span className="source-indicator" aria-label={count + ' source' + (count === 1 ? '' : 's')}>
      {count} {count === 1 ? 'SOURCE' : 'SOURCES'}
    </span>
  );
}

function sourceKind(source: InvestigationSource): 'external' | 'internal' | 'unknown' | 'unverified' {
  if (source.source_type === 'UNKNOWN' || source.url === 'UNKNOWN') return 'unknown';
  if (source.url === 'UNVERIFIED') return 'unverified';
  if (source.url.startsWith('http://') || source.url.startsWith('https://')) return 'external';
  return 'internal';
}

function SourceAction({ source }: { source: InvestigationSource }) {
  const kind = sourceKind(source);

  if (kind === 'external') {
    return (
      <a className="source-action source-action-link" href={source.url} target="_blank" rel="noreferrer">
        [OPEN SOURCE ↗]
      </a>
    );
  }
  if (kind === 'unknown') return <span className="source-action source-action-muted">[UNRESOLVED]</span>;
  if (kind === 'unverified') return <span className="source-action source-action-muted">[UNVERIFIED]</span>;
  return <span className="source-action source-action-muted">[OPEN RESEARCH →]</span>;
}

function TraceabilitySourceCard({ url }: { url: string }) {
  const isUnknown = url === 'UNKNOWN';
  const isUnverified = url === 'UNVERIFIED';
  const isExternal = url.startsWith('http://') || url.startsWith('https://');

  return (
    <article className="source-audit-card source-audit-card-traceability">
      <div className="source-audit-heading">
        <strong>TRACEABILITY SOURCE</strong>
        <span>{isExternal ? 'EXTERNAL' : isUnknown ? 'UNKNOWN' : isUnverified ? 'UNVERIFIED' : 'INTERNAL RESEARCH'}</span>
      </div>
      {isExternal
        ? <a className="source-action source-action-link" href={url} target="_blank" rel="noreferrer">[OPEN SOURCE ↗]</a>
        : <span className="source-action source-action-muted">{isUnknown ? '[UNRESOLVED]' : isUnverified ? '[UNVERIFIED]' : '[OPEN RESEARCH →]'}</span>}
      <div className="source-audit-url">
        <span>{isExternal ? 'SOURCE URL' : 'RESEARCH REFERENCE'}</span>
        <code>{url}</code>
      </div>
    </article>
  );
}

function SourceAuditCard({ source }: { source: InvestigationSource }) {
  const kind = sourceKind(source);
  const urlLabel = kind === 'external' ? 'SOURCE URL' : 'INTERNAL RESEARCH PATH';

  return (
    <article className="source-audit-card">
      <div className="source-audit-heading">
        <div className="source-audit-title"><MarkdownRenderer content={source.title} className="markdown-compact" /></div>
        <span>{source.source_type}</span>
      </div>
      <SourceAction source={source} />
      <div className="source-audit-url">
        <span>{urlLabel}</span>
        <code>{source.url}</code>
      </div>
      <div className="source-audit-usage">
        <span>USED BY</span>
        <div className="source-audit-refs">
          {source.used_by.length > 0
            ? source.used_by.map(reference => <code key={reference}>{reference}</code>)
            : <code>{NOT_PROVIDED}</code>}
        </div>
      </div>
    </article>
  );
}

export function SourceAuditList({
  brief,
  sourceRefs = [],
  sourceUrls = [],
  fallbackText,
}: {
  brief: InvestigationBrief;
  sourceRefs?: string[];
  sourceUrls?: string[];
  fallbackText?: string;
}) {
  const sourcesById = new Map(brief.sources.map(source => [source.id, source]));
  const uniqueRefs = [...new Set(sourceRefs)];
  const matchedSources = uniqueRefs
    .map(reference => sourcesById.get(reference))
    .filter((source): source is InvestigationSource => Boolean(source));
  const missingRefs = uniqueRefs.filter(reference => !sourcesById.has(reference));
  const uniqueSourceUrls = [...new Set(sourceUrls)].filter(url =>
    !matchedSources.some(source => source.url === url)
  );

  return (
    <div className="source-audit-list">
      {matchedSources.map(source => <SourceAuditCard key={source.id} source={source} />)}
      {uniqueSourceUrls.map(url => <TraceabilitySourceCard key={url} url={url} />)}
      {missingRefs.map(reference => (
        <article className="source-audit-card source-audit-card-missing" key={reference}>
          <div className="source-audit-heading"><strong>{reference}</strong><span>REFERENCE NOT FOUND</span></div>
          <div className="source-action source-action-muted">[UNRESOLVED]</div>
        </article>
      ))}
      {matchedSources.length === 0 && missingRefs.length === 0 && uniqueSourceUrls.length === 0 && fallbackText && (
        <div className="source-audit-fallback"><MarkdownRenderer content={fallbackText} /></div>
      )}
      {matchedSources.length === 0 && missingRefs.length === 0 && uniqueSourceUrls.length === 0 && !fallbackText && (
        <div className="source-audit-fallback">{NOT_PROVIDED}</div>
      )}
    </div>
  );
}

export function ProvenanceDetails({ provenance }: { provenance?: Provenance }) {
  if (!provenance) return <div className="provenance-empty">{NOT_PROVIDED}</div>;

  return (
    <dl className="provenance-details">
      <div><dt>SOURCE FILE</dt><dd>{provenance.source_file}</dd></div>
      <div><dt>SECTION</dt><dd>{provenance.section}</dd></div>
      <div><dt>LINE START</dt><dd>{provenance.line_start ?? NOT_PROVIDED}</dd></div>
      <div><dt>LINE END</dt><dd>{provenance.line_end ?? NOT_PROVIDED}</dd></div>
    </dl>
  );
}
