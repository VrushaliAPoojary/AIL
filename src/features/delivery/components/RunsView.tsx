import React from 'react';
import {
  IconRuns,
  IconCheckCircle,
  IconAlertTriangle,
  IconClock,
  IconShieldCheck,
  IconInfo,
  IconLock,
} from './Icons';
import { RunStatusBadge } from './StatusBadges';

interface RunsViewProps {
  data: any;
  onRun: () => void;
  busy: boolean;
  authenticated: boolean;
  onSignIn: () => void;
  onViewReport: () => void;
}

const fmtTime = (value?: string | null) =>
  value
    ? new Date(value).toLocaleString('en-IN', {
        dateStyle: 'medium',
        timeStyle: 'short',
      })
    : '—';

export function RunsView({
  data,
  onRun,
  busy,
  authenticated,
  onSignIn,
  onViewReport,
}: RunsViewProps) {
  const latest = data.latestRun;
  const isConfigured = data.settings?.mode === 'configured';
  const runs = data.runs || [];

  return (
    <div className="run-center-container">
      <div className="run-center-grid">
        {/* Run Launch Action Panel */}
        <section className="run-panel run-launch-panel" aria-labelledby="launch-heading">
          <div className="launch-header">
            <div className="launch-icon-wrapper">
              <IconRuns size={28} className="launch-icon" />
            </div>
            <div>
              <span className="eyebrow-tag">READ-ONLY AUTOMATION PIPELINE</span>
              <h2 id="launch-heading" className="launch-title">
                Run Supplier Delivery Monitoring
              </h2>
            </div>
          </div>

          <p className="launch-description">
            The configured ART agent queries ERPNext purchase orders and submitted receipts using its verified connector tools. Configuration presence alone does not establish connectivity. This action does NOT send supplier messages or write to ERPNext.
          </p>

          <div className="launch-action-box">
            {isConfigured ? (
              <button
                type="button"
                className="primary-run-btn"
                disabled={busy}
                onClick={onRun}
              >
                <IconRuns size={20} />
                <span>{busy ? 'Monitoring In Progress…' : 'Execute Live ART Monitoring Now'}</span>
              </button>
            ) : (
              <div className="launch-demo-action">
                <div className="demo-action-intro">
                  <IconInfo size={18} className="notice-icon" />
                  <div>
                    <strong>Demonstration Environment Active</strong>
                    <p>
                      Execute a simulated monitoring run using synthetic purchase orders and receipt evidence contracts. Results are clearly recorded as synthetic demo data.
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  className="primary-run-btn"
                  disabled={busy}
                  onClick={onRun}
                >
                  <IconRuns size={20} />
                  <span>{busy ? 'Simulating Run…' : 'Run Simulated Monitoring'}</span>
                </button>
              </div>
            )}
          </div>

          <div className="read-only-disclaimer">
            <IconShieldCheck size={16} />
            <span>
              <strong>Guaranteed Read-Only:</strong> The ADK agent runs with strict read-only tool scopes.
            </span>
          </div>
        </section>

        {/* Current / Active Run Result Panel */}
        <section className="run-panel active-run-panel" aria-labelledby="active-run-heading">
          <div className="active-run-header">
            <div>
              <h2 id="active-run-heading" className="panel-title">Latest Execution Status</h2>
              <p className="panel-subtitle">Results are schema-validated before completion</p>
            </div>
            <RunStatusBadge status={latest?.status} />
          </div>

          {latest ? (
            <div className="active-run-content">
              <div className="run-specs-matrix">
                <div className="spec-tile">
                  <span className="spec-tile-label">Run Reference</span>
                  <strong className="spec-tile-value monospace">{latest.id}</strong>
                </div>
                <div className="spec-tile">
                  <span className="spec-tile-label">Execution Mode</span>
                  <strong className="spec-tile-value">
                    {data.settings?.mode === 'configured' ? 'Live ART Agent' : 'Synthetic Demo'}
                  </strong>
                </div>
                <div className="spec-tile">
                  <span className="spec-tile-label">Started At</span>
                  <strong className="spec-tile-value">{fmtTime(latest.startedAt)}</strong>
                </div>
                <div className="spec-tile">
                  <span className="spec-tile-label">Finished At</span>
                  <strong className="spec-tile-value">{fmtTime(latest.finishedAt)}</strong>
                </div>
              </div>

              {latest.status === 'RUNNING' || latest.status === 'QUEUED' ? (
                <div className="run-in-progress-banner">
                  <span className="spinning-dot" />
                  <div>
                    <strong>Monitoring run in progress…</strong>
                    <p>Contacting ART agent and awaiting thread execution promise.</p>
                  </div>
                </div>
              ) : null}

              {latest.error && (
                <div className="run-failure-banner">
                  <IconAlertTriangle size={18} />
                  <div>
                    <strong>Execution Issue:</strong>
                    <p>{latest.error}</p>
                  </div>
                </div>
              )}

              {latest.status === 'SUCCEEDED' && (
                <div className="run-success-card">
                  <div className="success-header">
                    <IconCheckCircle size={18} className="text-green" />
                    <strong>Evidence Contract Verified</strong>
                  </div>
                  <p>
                    Final ART response satisfied the P02 report contract. {latest.result?.purchaseOrders?.length ?? 0} purchase orders verified.
                  </p>
                  <button type="button" className="view-orders-btn" onClick={onViewReport}>
                    Review Validated Order Report →
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="no-run-state">
              <IconClock size={32} className="no-run-icon" />
              <p>No monitoring run has been executed yet in this session.</p>
            </div>
          )}
        </section>

        {/* Run History List */}
        <section className="run-panel history-panel" aria-labelledby="history-heading">
          <div className="panel-top-bar">
            <div>
              <h2 id="history-heading" className="panel-title">Execution Audit History</h2>
              <p className="panel-subtitle">Persisted log of manual monitoring executions and outcomes</p>
            </div>
            <span className="history-count-badge">{runs.length} Runs</span>
          </div>

          <div className="history-table-wrapper">
            {runs.length > 0 ? (
              <table className="history-table">
                <thead>
                  <tr>
                    <th scope="col">Status</th>
                    <th scope="col">Reference ID</th>
                    <th scope="col">Execution Mode</th>
                    <th scope="col">Started Timestamp</th>
                    <th scope="col" className="text-right">Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map((run: any) => {
                    const durationSec = run.finishedAt
                      ? Math.max(
                          0,
                          Math.round(
                            (Date.parse(run.finishedAt) - Date.parse(run.startedAt)) / 1000
                          )
                        )
                      : null;

                    return (
                      <tr key={run.id} className="history-row">
                        <td>
                          <RunStatusBadge status={run.status} />
                        </td>
                        <td>
                          <strong className="monospace history-id-text">{run.id.slice(0, 10)}…</strong>
                        </td>
                        <td>
                          <span className="mode-text">
                            {run.source === 'art' && data.settings?.mode === 'configured'
                              ? 'Live ART Execution'
                              : 'Demo Execution'}
                          </span>
                        </td>
                        <td>
                          <span className="timestamp-text">{fmtTime(run.startedAt)}</span>
                        </td>
                        <td className="text-right">
                          <span className="duration-text">
                            {durationSec != null ? `${durationSec}s` : 'In progress'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            ) : (
              <div className="no-history-state">
                <IconInfo size={20} />
                <p>Run history will appear here once monitoring runs are triggered.</p>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
