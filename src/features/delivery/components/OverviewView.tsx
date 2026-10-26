import React from 'react';
import {
  IconOrders,
  IconAlertTriangle,
  IconClock,
  IconArrowRight,
  IconCheckCircle,
  IconPartial,
  IconHelpCircle,
  IconShieldCheck,
  IconRuns,
  IconInfo,
} from './Icons';
import { DeliveryStatusBadge, SeverityBadge, RunStatusBadge } from './StatusBadges';
import { OnboardingBanner } from './OnboardingBanner';
import { PoDelayAnalyzer } from './PoDelayAnalyzer';

interface OverviewViewProps {
  data: any;
  setView: (view: string) => void;
  setFilter: (filter: string) => void;
  setSelectedOrder: (orderId: string) => void;
  selectedOrder?: string | null;
  onRun?: () => void;
  isRunBusy?: boolean;
}

const fmtTime = (value?: string | null) =>
  value
    ? new Date(value).toLocaleString('en-IN', {
        dateStyle: 'medium',
        timeStyle: 'short',
      })
    : 'No execution recorded';

const pretty = (val?: string) =>
  val
    ? val
        .replaceAll('_', ' ')
        .toLowerCase()
        .replace(/\b\w/g, (c) => c.toUpperCase())
    : 'Unknown';

export function OverviewView({
  data,
  setView,
  setFilter,
  setSelectedOrder,
  selectedOrder,
  onRun,
  isRunBusy = false,
}: OverviewViewProps) {
  const metric = data.metrics || {
    totalOrders: 0,
    overdue: 0,
    dueToday: 0,
    upcoming: 0,
    received: 0,
    partialReceipts: 0,
    needsVerification: 0,
  };

  const latest = data.latestRun;
  const isDemo = data.settings?.mode === 'demo' || data.source === 'synthetic demonstration data';

  const cards = [
    {
      key: 'all',
      filterKey: 'all',
      title: 'Active Purchase Orders',
      value: metric.totalOrders,
      icon: IconOrders,
      tone: 'navy',
      description: 'Submitted procurement commitments in active scope',
      statLabel: 'Active Scope',
    },
    {
      key: 'overdue',
      filterKey: 'overdue',
      title: 'Overdue Deliveries',
      value: metric.overdue,
      icon: IconAlertTriangle,
      tone: 'red',
      description: 'Outstanding lines past contractual/promise schedule',
      statLabel: 'Immediate Action',
    },
    {
      key: 'due_today',
      filterKey: 'due_today',
      title: 'Due Today',
      value: metric.dueToday,
      icon: IconClock,
      tone: 'amber',
      description: 'Expected arrival scheduled for the current business date',
      statLabel: 'Urgent Arrival',
    },
    {
      key: 'upcoming',
      filterKey: 'upcoming',
      title: `Upcoming (${data.settings?.upcomingDays || 7} Days)`,
      value: metric.upcoming,
      icon: IconArrowRight,
      tone: 'blue',
      description: `Deliveries scheduled within the ${data.settings?.upcomingDays || 7}-day window`,
      statLabel: 'In Transit / Queued',
    },
    {
      key: 'received',
      filterKey: 'received',
      title: 'Verified Completed',
      value: metric.received,
      icon: IconCheckCircle,
      tone: 'green',
      description: 'Exact linked submitted receipts match 100% of ordered qty',
      statLabel: 'Fully Received',
    },
    {
      key: 'partial',
      filterKey: 'partial',
      title: 'Partially Received',
      value: metric.partialReceipts,
      icon: IconPartial,
      tone: 'purple',
      description: 'Split shipments with confirmed receipt and open remainder',
      statLabel: 'Partial Balance',
    },
    {
      key: 'needs_verification',
      filterKey: 'needs_verification',
      title: 'Needs Verification',
      value: metric.needsVerification,
      icon: IconHelpCircle,
      tone: 'slate',
      description: 'Incomplete evidence, unexhausted pages, or date conflict',
      statLabel: 'Audit Required',
    },
  ];

  return (
    <div className="overview-container">
      {/* Onboarding Guide banner */}
      <OnboardingBanner
        mode={data.settings?.mode}
        source={data.source}
        dueDateBasis={data.settings?.dueDateBasis}
      />

      {/* Primary PO Delay Analyzer & Solution Finder */}
      <PoDelayAnalyzer
        orders={data.purchaseOrders || []}
        monitoringDate={data.monitoringDate || ''}
        timezone={data.settings?.timezone}
        dueDateBasis={data.settings?.dueDateBasis}
        selectedOrderId={selectedOrder || null}
        onSelectOrder={(id) => {
          setSelectedOrder(id || '');
        }}
        onRunMonitoring={onRun}
        isRunBusy={isRunBusy}
      />

      {/* Integration Readiness Bar */}
      <section className="integration-readiness-panel" aria-label="Integration Readiness Status">
        <div className="integration-panel-info">
          <div className="integration-title-group">
            <IconShieldCheck size={20} className="integration-icon-main" />
            <div>
              <strong className="integration-heading">Integration Readiness Telemetry</strong>
              <span className="integration-subheading">
                {isDemo
                  ? 'Active Mode: Synthetic demonstration data. Live ART execution is not engaged.'
                  : 'Active Mode: Server-configured ART agent. Execution requires valid tool responses.'}
              </span>
            </div>
          </div>
        </div>

        <div className="readiness-indicators">
          <div className="readiness-item" title="Backend API status">
            <span
              className={`indicator-dot ${
                data.integrations?.backend === 'available' ? 'is-good' : 'is-warning'
              }`}
            />
            <span className="indicator-label">Backend API:</span>
            <strong className="indicator-value">{pretty(data.integrations?.backend)}</strong>
          </div>

          <div className="readiness-item" title="ART Agent readiness status">
            <span
              className={`indicator-dot ${
                data.integrations?.readiness === 'VALIDATED'
                  ? 'is-good'
                  : data.integrations?.readiness === 'CONFIGURED'
                  ? 'is-info'
                  : 'is-neutral'
              }`}
            />
            <span className="indicator-label">ART Agent:</span>
            <strong className="indicator-value">{pretty(data.integrations?.readiness)}</strong>
          </div>

          <div className="readiness-item" title="ERPNext report status">
            <span
              className={`indicator-dot ${
                data.integrations?.erpnext === 'VALIDATED' ? 'is-good' : 'is-neutral'
              }`}
            />
            <span className="indicator-label">ERPNext Data:</span>
            <strong className="indicator-value">{pretty(data.integrations?.erpnext)}</strong>
          </div>
        </div>
      </section>

      {/* Audit Warning Notice if any orders need verification */}
      {metric.needsVerification > 0 && (
        <div className="audit-alert-banner">
          <div className="audit-alert-icon">
            <IconHelpCircle size={22} />
          </div>
          <div className="audit-alert-text">
            <strong>Audit Warning: {metric.needsVerification} purchase order commitment(s) require verification</strong>
            <p>
              To maintain audit integrity and prevent false claims of receipt, records lacking complete, exactly scoped receipt retrieval or exhausted pagination are excluded from verified delivery totals.
            </p>
          </div>
          <button
            type="button"
            className="audit-alert-btn"
            onClick={() => {
              setFilter('needs_verification');
              setView('orders');
            }}
          >
            Inspect Unverified Records →
          </button>
        </div>
      )}

      {/* Large KPI Cards Grid */}
      <div className="kpi-cards-grid">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <button
              key={card.key}
              type="button"
              className={`kpi-card tone-${card.tone}`}
              onClick={() => {
                setFilter(card.filterKey);
                setView('orders');
              }}
              title={`View ${card.title}`}
            >
              <div className="kpi-top-row">
                <span className="kpi-title">{card.title}</span>
                <span className="kpi-icon-bubble" aria-hidden="true">
                  <Icon size={20} />
                </span>
              </div>
              <div className="kpi-value-row">
                <span className="kpi-number">{card.value}</span>
                <span className="kpi-stat-tag">{card.statLabel}</span>
              </div>
              <p className="kpi-description">{card.description}</p>
            </button>
          );
        })}
      </div>

      {/* Two-Column Priority Operations Section */}
      <div className="overview-dual-columns">
        {/* Left Column: Priority Delivery Queue */}
        <section className="operations-panel queue-panel" aria-labelledby="queue-heading">
          <div className="panel-top-bar">
            <div>
              <h2 id="queue-heading" className="panel-title">Priority Delivery Queue</h2>
              <p className="panel-subtitle">Items requiring immediate buyer or dock coordinator attention</p>
            </div>
            <button
              type="button"
              className="panel-link-btn"
              onClick={() => setView('exceptions')}
            >
              View all exceptions ({data.exceptions?.length || 0}) →
            </button>
          </div>

          <div className="queue-list">
            {data.exceptions?.length ? (
              data.exceptions.slice(0, 5).map((item: any) => (
                <button
                  key={item.id}
                  type="button"
                  className="queue-row"
                  onClick={() => setSelectedOrder(item.orderId)}
                  title={`Inspect ${item.orderId}`}
                >
                  <div className="queue-row-left">
                    <SeverityBadge severity={item.severity} />
                    <div className="queue-row-order-info">
                      <strong className="queue-order-id">{item.orderId}</strong>
                      <span className="queue-supplier-meta">
                        {item.supplier} · {item.itemCode}
                      </span>
                    </div>
                  </div>
                  <div className="queue-row-right">
                    <DeliveryStatusBadge
                      status={item.status}
                      partialReceipt={item.status === 'PARTIALLY_RECEIVED' || item.severity === 'Medium'}
                      size="sm"
                    />
                    <span className="row-action-arrow">→</span>
                  </div>
                </button>
              ))
            ) : (
              <div className="empty-queue-box">
                <IconCheckCircle size={28} className="empty-check-icon" />
                <p>No active delivery exceptions require attention in this scope.</p>
              </div>
            )}
          </div>
        </section>

        {/* Right Column: Monitoring Activity */}
        <section className="operations-panel run-summary-panel" aria-labelledby="run-summary-heading">
          <div className="panel-top-bar">
            <div>
              <h2 id="run-summary-heading" className="panel-title">Monitoring Execution</h2>
              <p className="panel-subtitle">Latest confirmed ART scan status</p>
            </div>
            <RunStatusBadge status={latest?.status} />
          </div>

          <div className="run-summary-body">
            <div className="run-timestamp-box">
              <span className="run-timestamp-label">Latest Execution Run:</span>
              <strong className="run-timestamp-value">
                {fmtTime(latest?.finishedAt || latest?.startedAt)}
              </strong>
            </div>

            <div className="run-meta-grid">
              <div className="run-meta-cell">
                <span className="meta-label">Run Reference</span>
                <strong className="meta-value monospace">{latest?.id || 'No run yet'}</strong>
              </div>
              <div className="run-meta-cell">
                <span className="meta-label">Source Mode</span>
                <strong className="meta-value">
                  {latest?.source === 'art' && data.settings?.mode === 'configured'
                    ? 'Live ART Agent'
                    : 'Synthetic Demo'}
                </strong>
              </div>
            </div>

            <div className="run-integrity-callout">
              <IconInfo size={16} className="callout-icon" />
              <p>
                A queued request is not marked successful until the complete ART agent response satisfies the schema and evidence validation contract.
              </p>
            </div>

            {onRun && (
              <button
                type="button"
                className="primary-run-btn overview-primary-run-btn"
                disabled={isRunBusy}
                onClick={onRun}
                title="Execute supplier delivery monitoring run"
              >
                <IconRuns size={18} />
                <span>{isRunBusy ? 'Monitoring In Progress…' : 'Execute Monitoring Scan Now'}</span>
              </button>
            )}

            <button
              type="button"
              className="open-run-center-btn"
              onClick={() => setView('runs')}
            >
              <IconRuns size={18} />
              <span>Open Automation Run Center</span>
            </button>
          </div>
        </section>
      </div>

      {/* Operational Policy Footnote */}
      <div className="operations-policy-footnote">
        <IconInfo size={15} className="policy-icon" />
        <span>
          Delivery classification evaluates dates using <b>{pretty(data.settings?.dueDateBasis)}</b> as the active due-date basis. Contractual schedules and supplier promised dates are evaluated distinctly. No arrival date or receipt quantity is ever inferred from missing evidence.
        </span>
      </div>
    </div>
  );
}
