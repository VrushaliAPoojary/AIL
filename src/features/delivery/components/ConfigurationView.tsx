import React, { FormEvent } from 'react';
import {
  IconConfiguration,
  IconShieldCheck,
  IconLock,
  IconInfo,
  IconCheckCircle,
} from './Icons';

interface ConfigurationViewProps {
  settings: {
    upcomingDays: number;
    dueDateBasis: string;
    timezone: string;
  };
  setSettings: (settings: any) => void;
  save: (event: FormEvent) => void;
  busy: boolean;
  authenticated: boolean;
  configured: boolean;
  message: string;
  onSignIn: () => void;
  integrations: {
    backend?: string;
    readiness?: string;
    erpnext?: string;
  };
}

const pretty = (val?: string) =>
  val
    ? val
        .replaceAll('_', ' ')
        .toLowerCase()
        .replace(/\b\w/g, (c) => c.toUpperCase())
    : 'Unknown';

export function ConfigurationView({
  settings,
  setSettings,
  save,
  busy,
  authenticated,
  configured,
  message,
  onSignIn,
  integrations,
}: ConfigurationViewProps) {
  return (
    <div className="config-container">
      <div className="config-grid-layout">
        {/* Left Column: Scope Settings */}
        <section className="config-panel scope-settings-panel" aria-labelledby="scope-heading">
          <div className="panel-top-bar">
            <div>
              <div className="eyebrow-tag">PREFERENCES &amp; BUSINESS LOGIC</div>
              <h2 id="scope-heading" className="panel-title">
                Delivery Monitoring Scope
              </h2>
              <p className="panel-subtitle">
                Configure time windows and scheduling basis for delivery classification
              </p>
            </div>
          </div>

          {!authenticated ? (
            <div className="config-locked-card">
              <div className="lock-icon-wrapper">
                <IconLock size={28} />
              </div>
              <h3 className="locked-title">Administrator Authentication Required</h3>
              <p className="locked-desc">
                Configuration controls are protected. Sign in with administrator credentials to modify delivery classification settings.
              </p>
              {configured ? (
                <button type="button" className="config-signin-btn" onClick={onSignIn}>
                  Sign in as Administrator →
                </button>
              ) : (
                <div className="config-unset-note">
                  <IconInfo size={16} />
                  <span>
                    Set <code>P02_ADMIN_USERNAME</code>, <code>P02_ADMIN_PASSWORD</code>, and <code>P02_SESSION_SECRET</code> in the server environment to enable administrator configuration.
                  </span>
                </div>
              )}
            </div>
          ) : (
            <form onSubmit={save} className="scope-config-form">
              <div className="form-group">
                <label htmlFor="upcoming-days-select" className="form-label">
                  Upcoming Delivery Horizon
                </label>
                <select
                  id="upcoming-days-select"
                  className="form-select"
                  value={settings.upcomingDays}
                  onChange={(e) =>
                    setSettings({ ...settings, upcomingDays: Number(e.target.value) })
                  }
                >
                  <option value={3}>Next 3 days (Tight window)</option>
                  <option value={7}>Next 7 days (Standard operational window)</option>
                  <option value={14}>Next 14 days (Extended lookahead)</option>
                  <option value={30}>Next 30 days (Monthly procurement planning)</option>
                </select>
                <span className="form-help-text">
                  Orders with applicable delivery dates falling within this number of days will be flagged as Upcoming.
                </span>
              </div>

              <div className="form-group">
                <label htmlFor="due-date-basis-select" className="form-label">
                  Applicable Due Date Basis
                </label>
                <select
                  id="due-date-basis-select"
                  className="form-select"
                  value={settings.dueDateBasis}
                  onChange={(e) =>
                    setSettings({ ...settings, dueDateBasis: e.target.value })
                  }
                >
                  <option value="contractual">Contractual Item Schedule Date</option>
                  <option value="supplier_promise">Supplier Promised Date</option>
                </select>
                <span className="form-help-text">
                  Controls which date determines Overdue status. Both contractual schedule and promised dates remain individually visible across all tables and audit drawers.
                </span>
              </div>

              <div className="form-group">
                <label htmlFor="timezone-input" className="form-label">
                  Operational Business Timezone
                </label>
                <input
                  id="timezone-input"
                  type="text"
                  className="form-input"
                  value={settings.timezone}
                  onChange={(e) =>
                    setSettings({ ...settings, timezone: e.target.value })
                  }
                  placeholder="Asia/Kolkata"
                  maxLength={100}
                />
                <span className="form-help-text">
                  Standard IANA timezone name (e.g., <code>Asia/Kolkata</code>, <code>UTC</code>, <code>America/New_York</code>). Used to calculate midnight date rollovers.
                </span>
              </div>

              <div className="form-submit-row">
                <button
                  type="submit"
                  className="save-settings-btn"
                  disabled={busy}
                >
                  {busy ? 'Saving Settings…' : 'Save Configuration'}
                </button>

                {message && (
                  <div
                    className={`form-message-banner ${
                      message.includes('saved') ? 'msg-success' : 'msg-error'
                    }`}
                  >
                    {message.includes('saved') ? (
                      <IconCheckCircle size={16} />
                    ) : (
                      <IconInfo size={16} />
                    )}
                    <span>{message}</span>
                  </div>
                )}
              </div>
            </form>
          )}
        </section>

        {/* Right Column: Security & Server Telemetry */}
        <section className="config-panel telemetry-panel" aria-labelledby="telemetry-heading">
          <div className="panel-top-bar">
            <div>
              <div className="eyebrow-tag">SERVER TELEMETRY</div>
              <h2 id="telemetry-heading" className="panel-title">
                Integration &amp; Security Health
              </h2>
              <p className="panel-subtitle">Environment readiness and safeguard enforcement</p>
            </div>
          </div>

          <div className="telemetry-status-list">
            <div className="status-row">
              <span className="status-label">Backend Persistence &amp; API</span>
              <strong className="status-value text-green">
                <span className="dot-green" />
                {pretty(integrations.backend)}
              </strong>
            </div>
            <div className="status-row">
              <span className="status-label">ART Agent Environment</span>
              <strong className="status-value">
                <span
                  className={
                    integrations.readiness === 'VALIDATED'
                      ? 'dot-green'
                      : integrations.readiness === 'AUTHENTICATION_FAILED' || integrations.readiness === 'CONNECTION_FAILED' || integrations.readiness === 'FAILED'
                      ? 'dot-red'
                      : 'dot-amber'
                  }
                />
                {pretty(integrations.readiness)}
              </strong>
            </div>
            <div className="status-row">
              <span className="status-label">ERPNext Data Report</span>
              <strong className="status-value">
                <span
                  className={
                    integrations.erpnext === 'VALIDATED' ? 'dot-green' : 'dot-neutral'
                  }
                />
                {pretty(integrations.erpnext)}
              </strong>
            </div>
          </div>

          <div className="security-callout-card">
            <div className="callout-header">
              <IconShieldCheck size={18} className="shield-icon" />
              <strong>Zero Credential Exposure</strong>
            </div>
            <p>
              ERPNext API tokens and ART Client Secrets are stored exclusively in secure server environment variables. Browser sessions never receive, store, or transmit integration credentials.
            </p>
          </div>

          <div className="security-callout-card">
            <div className="callout-header">
              <IconInfo size={18} className="info-icon" />
              <strong>Execution Policy: Manual Trigger Only</strong>
            </div>
            <p>
              Automated cron schedules are disabled by design. Every monitoring scan requires explicit operator initiation to prevent unbounded external queries.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
