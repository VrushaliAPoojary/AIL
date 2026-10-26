import React from 'react';
import { IconWorkflow, IconShieldCheck, IconInfo, IconCheckCircle } from './Icons';

interface WorkflowViewProps {
  stages: any[];
}

export function WorkflowView({ stages = [] }: WorkflowViewProps) {
  const lifecycleStates = [
    { label: 'SPECIFIED', desc: 'Documented in architectural brief' },
    { label: 'IMPLEMENTED', desc: 'Code committed & functions wired' },
    { label: 'TESTED', desc: 'Automated test suite passing' },
    { label: 'PARTIALLY VALIDATED', desc: 'Schema verified against sample reports' },
    { label: 'OPERATIONAL', desc: 'Live multi-node production verified' },
  ];

  return (
    <div className="workflow-container">
      {/* Overview Intro Banner */}
      <section className="workflow-intro-panel" aria-labelledby="workflow-intro-heading">
        <div className="intro-header-row">
          <div className="intro-icon-box">
            <IconWorkflow size={28} />
          </div>
          <div>
            <span className="eyebrow-tag">SPECIFICATION VS. IMPLEMENTATION GOVERNANCE</span>
            <h2 id="workflow-intro-heading" className="intro-title">
              P02 Delivery Lifecycle: 6 Operational Stages
            </h2>
          </div>
        </div>

        <p className="intro-description">
          The P02 operating model establishes deterministic boundaries from purchase order acknowledgment through dock receipt handoff. Stage badges reflect actual repository capabilities—never inflated beyond verified evidence.
        </p>

        {/* State Badges Legend */}
        <div className="lifecycle-legend">
          <div className="legend-label">Verification State Maturity:</div>
          <div className="legend-badges-wrap">
            {lifecycleStates.map((st) => (
              <div key={st.label} className="legend-item" title={st.desc}>
                <span className={`stage-state-badge state-${st.label.toLowerCase().replace(/\s+/g, '-')}`}>
                  {st.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 6 Stage Timeline Cards */}
      <div className="stages-timeline-grid">
        {stages.map((stage: any, index: number) => {
          const stageState = stage.state || 'SPECIFIED';
          const isPartiallyValidated = stageState === 'PARTIALLY VALIDATED';

          return (
            <article
              key={stage.id}
              className={`stage-timeline-card ${isPartiallyValidated ? 'is-validated-stage' : ''}`}
            >
              <div className="stage-card-left">
                <div className="stage-number-bubble">
                  {String(index + 1).padStart(2, '0')}
                </div>
                <div className="stage-connector-line" aria-hidden="true" />
              </div>

              <div className="stage-card-body">
                <div className="stage-card-top-row">
                  <h3 className="stage-name-heading">{stage.name}</h3>
                  <span
                    className={`stage-state-badge state-${stageState
                      .toLowerCase()
                      .replace(/\s+/g, '-')}`}
                  >
                    {stageState}
                  </span>
                </div>

                <p className="stage-detail-text">{stage.detail}</p>

                <div className="stage-provenance-box">
                  <div className="provenance-item">
                    <span className="prov-label">Design Contract:</span>
                    <strong className="prov-value monospace">
                      workflow.md · WF-P02-{String(index + 1).padStart(3, '0')}
                    </strong>
                  </div>
                  <div className="provenance-item">
                    <span className="prov-label">Audit Evidence:</span>
                    <strong className="prov-value">
                      {isPartiallyValidated
                        ? 'P02 normalized report schema (live response pending)'
                        : 'Architectural specification only'}
                    </strong>
                  </div>
                </div>
              </div>
            </article>
          );
        })}
      </div>

      {/* Safety Policy Footnote */}
      <div className="workflow-safety-footnote">
        <IconShieldCheck size={18} className="footnote-shield" />
        <span>
          <strong>Operational Boundary:</strong> Human review remains mandatory for delivery delays, partial receipts, conflicting promise dates, and any supplier escalation. Autonomous supplier messaging and ERPNext writebacks are intentionally not implemented.
        </span>
      </div>
    </div>
  );
}
