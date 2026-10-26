import React from 'react';
import {
  IconCheckCircle,
  IconAlertTriangle,
  IconClock,
  IconArrowRight,
  IconPartial,
  IconHelpCircle,
  IconBox,
} from './Icons';

export interface DeliveryStatusBadgeProps {
  status?: string | null;
  partialReceipt?: boolean;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

export function DeliveryStatusBadge({
  status,
  partialReceipt = false,
  size = 'md',
  showIcon = true,
}: DeliveryStatusBadgeProps) {
  const norm = (status || 'NEEDS_VERIFICATION').toUpperCase();

  let label = 'Needs Verification';
  let themeClass = 'status-badge-verification';
  let Icon = IconHelpCircle;

  switch (norm) {
    case 'RECEIVED':
      label = 'Verified Completed';
      themeClass = 'status-badge-received';
      Icon = IconCheckCircle;
      break;
    case 'PARTIALLY_RECEIVED':
      label = 'Partially Received';
      themeClass = 'status-badge-partial';
      Icon = IconPartial;
      break;
    case 'OVERDUE':
      label = 'Overdue Delivery';
      themeClass = 'status-badge-overdue';
      Icon = IconAlertTriangle;
      break;
    case 'DUE_TODAY':
      label = 'Due Today';
      themeClass = 'status-badge-duetoday';
      Icon = IconClock;
      break;
    case 'UPCOMING':
      label = 'Upcoming';
      themeClass = 'status-badge-upcoming';
      Icon = IconArrowRight;
      break;
    case 'FUTURE_OPEN_DELIVERY':
      label = 'Future Open';
      themeClass = 'status-badge-future';
      Icon = IconBox;
      break;
    case 'NEEDS_VERIFICATION':
    default:
      label = 'Needs Verification';
      themeClass = 'status-badge-verification';
      Icon = IconHelpCircle;
      break;
  }

  return (
    <div className={`status-badge-wrapper ${size}`}>
      <span className={`status-badge ${themeClass} ${size}`} title={`Delivery status: ${label}`}>
        {showIcon && <Icon size={size === 'sm' ? 12 : size === 'lg' ? 16 : 14} className="status-badge-icon" />}
        <span className="status-badge-text">{label}</span>
      </span>
      {partialReceipt && norm !== 'PARTIALLY_RECEIVED' && (
        <span className="partial-receipt-pill" title="Partial receipt records confirmed in ERPNext">
          Partial Qty
        </span>
      )}
    </div>
  );
}

export function SeverityBadge({ severity }: { severity?: string }) {
  const norm = (severity || 'Low').toLowerCase();
  let tone = 'low';
  let label = 'Low';

  if (norm === 'high') {
    tone = 'high';
    label = 'Critical Action';
  } else if (norm === 'review') {
    tone = 'review';
    label = 'Audit Review';
  } else if (norm === 'medium') {
    tone = 'medium';
    label = 'Medium Risk';
  }

  return (
    <span className={`severity-tag severity-${tone}`}>
      <span className="severity-dot" aria-hidden="true" />
      <span>{label}</span>
    </span>
  );
}

export function ModeBadge({
  mode,
  source,
  readiness,
}: {
  mode?: string;
  source?: string;
  readiness?: string;
}) {
  const isDemo = mode === 'demo' || source === 'synthetic demonstration data';

  if (isDemo) {
    return (
      <span className="env-badge env-demo" title="Synthetic demonstration data. No ERPNext changes or live ART connection.">
        <span className="env-pulse demo-pulse" aria-hidden="true" />
        <span className="env-label">SYNTHETIC DEMO</span>
      </span>
    );
  }

  const isConfigured = mode === 'configured';
  const readyNorm = (readiness || '').toUpperCase();
  const isValidated = readyNorm === 'VALIDATED';

  return (
    <span
      className={`env-badge ${isValidated ? 'env-live' : 'env-configured'}`}
      title={isValidated ? 'Live ART Agent report verified' : 'ART configured on server'}
    >
      <span className="env-pulse live-pulse" aria-hidden="true" />
      <span className="env-label">
        {isValidated ? 'LIVE · VALIDATED' : `ART · ${readiness || 'CONFIGURED'}`}
      </span>
    </span>
  );
}

export function RunStatusBadge({ status }: { status?: string | null }) {
  const norm = (status || 'IDLE').toUpperCase();

  switch (norm) {
    case 'SUCCEEDED':
      return (
        <span className="run-pill run-pill-success">
          <IconCheckCircle size={13} />
          <span>Succeeded</span>
        </span>
      );
    case 'FAILED':
      return (
        <span className="run-pill run-pill-failed">
          <IconAlertTriangle size={13} />
          <span>Failed</span>
        </span>
      );
    case 'RUNNING':
      return (
        <span className="run-pill run-pill-running">
          <span className="spinning-dot" />
          <span>Running…</span>
        </span>
      );
    case 'QUEUED':
      return (
        <span className="run-pill run-pill-queued">
          <IconClock size={13} />
          <span>Queued</span>
        </span>
      );
    default:
      return (
        <span className="run-pill run-pill-idle">
          <span>Idle</span>
        </span>
      );
  }
}
