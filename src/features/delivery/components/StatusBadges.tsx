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
  const readyNorm = (readiness || '').toUpperCase();
  const isAuthFailed = readyNorm === 'AUTHENTICATION_FAILED';
  const isConnFailed = readyNorm === 'CONNECTION_FAILED' || readyNorm === 'FAILED';
  const isValidated = readyNorm === 'VALIDATED';
  const isConnecting = readyNorm === 'CONNECTING';
  const isConnected = readyNorm === 'CONNECTED';
  const isUnverified = readyNorm === 'CONFIGURED_UNVERIFIED' || readyNorm === 'CONFIGURED';
  const isDemo = mode === 'demo' || mode === 'NOT_CONFIGURED' || source === 'synthetic demonstration data';

  if (isAuthFailed) {
    return (
      <span
        className="env-badge env-failed"
        title="ART Authentication Failed (HTTP 401). Check credentials in ART dashboard and local environment. Displaying synthetic baseline data."
      >
        <span className="env-pulse failed-pulse" aria-hidden="true" />
        <span className="env-label">ART · AUTH FAILED</span>
      </span>
    );
  }

  if (isConnFailed) {
    return (
      <span
        className="env-badge env-failed"
        title="ART Connection Failed. Check server configuration. Displaying synthetic baseline data."
      >
        <span className="env-pulse failed-pulse" aria-hidden="true" />
        <span className="env-label">ART · CONNECTION FAILED</span>
      </span>
    );
  }

  if (isValidated) {
    return (
      <span
        className="env-badge env-live"
        title="Live ART Agent report verified from ERPNext"
      >
        <span className="env-pulse live-pulse" aria-hidden="true" />
        <span className="env-label">LIVE · VALIDATED</span>
      </span>
    );
  }

  if (isConnecting) {
    return (
      <span
        className="env-badge env-configured"
        title="Connecting to ART WebSocket…"
      >
        <span className="env-pulse unverified-pulse" aria-hidden="true" />
        <span className="env-label">ART · CONNECTING…</span>
      </span>
    );
  }

  if (isConnected) {
    return (
      <span
        className="env-badge env-live"
        title="Connected to ART Agent. Awaiting run completion."
      >
        <span className="env-pulse live-pulse" aria-hidden="true" />
        <span className="env-label">ART · CONNECTED</span>
      </span>
    );
  }

  if (isUnverified && mode === 'configured') {
    return (
      <span
        className="env-badge env-configured"
        title="ART configured on server, but live agent connection has not been verified. Displaying synthetic baseline."
      >
        <span className="env-pulse unverified-pulse" aria-hidden="true" />
        <span className="env-label">ART · UNVERIFIED</span>
      </span>
    );
  }

  return (
    <span className="env-badge env-demo" title="Synthetic demonstration data. No ERPNext changes or live ART connection.">
      <span className="env-pulse demo-pulse" aria-hidden="true" />
      <span className="env-label">SYNTHETIC DEMO</span>
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
