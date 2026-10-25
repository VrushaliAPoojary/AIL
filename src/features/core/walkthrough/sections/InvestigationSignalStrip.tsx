import type { InvestigationBrief } from '../../../../types/investigationBrief';

export function InvestigationSignalStrip({ brief }: { brief?: InvestigationBrief }) {
  if (!brief) return null;

  const signals = [
    {
      label: 'Sources',
      value: brief.sources?.length ?? 0,
      note: 'Referenced source records',
    },
    {
      label: 'Evidence items',
      value: brief.evidence?.length ?? 0,
      note: 'Explicit evidence cards',
    },
    {
      label: 'Key findings',
      value: brief.presentation?.key_findings?.length ?? 0,
      note: 'Summary findings',
    },
    {
      label: 'Checkpoints',
      value: brief.checkpoints?.length ?? 0,
      note: 'Recorded workflow steps',
    },
    {
      label: 'Falsification tests',
      value: brief.falsification?.length ?? 0,
      note: 'Claims tested against evidence',
    },
  ];

  return (
    <section className="walkthrough-signal-strip" aria-label="Investigation summary metrics">
      {signals.map(signal => (
        <article key={signal.label} className="walkthrough-signal-card">
          <span className="walkthrough-signal-label">{signal.label}</span>
          <strong className="walkthrough-signal-value">{signal.value}</strong>
          <span className="walkthrough-signal-note">{signal.note}</span>
        </article>
      ))}
    </section>
  );
}
