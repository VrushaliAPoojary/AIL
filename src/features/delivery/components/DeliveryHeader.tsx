import React from 'react';
import { ModeBadge } from './StatusBadges';
import { IconRefresh, IconUser, IconLock } from './Icons';

interface DeliveryHeaderProps {
  currentViewLabel: string;
  source?: string;
  mode?: string;
  readiness?: string;
  monitoringDate?: string | null;
  timezone?: string;
  authenticated: boolean;
  authConfigured: boolean;
  loading: boolean;
  onRefresh: () => void;
  onSignOut: () => void;
  onSignInClick: () => void;
  onToggleSidebar?: () => void;
}

export function DeliveryHeader({
  currentViewLabel,
  source,
  mode,
  readiness,
  monitoringDate,
  timezone = 'Asia/Kolkata',
  authenticated,
  authConfigured,
  loading,
  onRefresh,
  onSignOut,
  onSignInClick,
  onToggleSidebar,
}: DeliveryHeaderProps) {
  const formattedDate = monitoringDate
    ? new Date(`${monitoringDate.slice(0, 10)}T00:00:00`).toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    : 'Pending';

  return (
    <header className="delivery-header">
      <div className="header-left">
        {onToggleSidebar && (
          <button
            type="button"
            className="mobile-nav-toggle"
            onClick={onToggleSidebar}
            aria-label="Toggle navigation menu"
          >
            <span className="hamburger-bar" />
            <span className="hamburger-bar" />
            <span className="hamburger-bar" />
          </button>
        )}
        <div className="header-breadcrumbs">
          <span className="breadcrumb-sub">Procurement Workspace</span>
          <span className="breadcrumb-sep">/</span>
          <span className="breadcrumb-process">P02 Supplier Delivery</span>
          <span className="breadcrumb-sep">/</span>
          <h1 className="breadcrumb-current">{currentViewLabel}</h1>
        </div>
      </div>

      <div className="header-right">
        {/* Monitoring business date context */}
        <div className="monitoring-date-chip" title={`Current business monitoring date in ${timezone}`}>
          <span className="date-icon-dot" />
          <span className="date-label">Business Date:</span>
          <strong>{formattedDate}</strong>
          <span className="tz-label">({timezone.replace('Asia/', '')})</span>
        </div>

        {/* Mode pill (Demo vs Live) */}
        <ModeBadge mode={mode} source={source} readiness={readiness} />

        {/* Admin session button */}
        {authenticated ? (
          <div className="admin-session-pill">
            <span className="admin-avatar">
              <IconUser size={13} />
            </span>
            <span className="admin-name">Admin Session</span>
            <button
              type="button"
              className="sign-out-btn"
              onClick={onSignOut}
              title="End administrator session"
            >
              Sign out
            </button>
          </div>
        ) : (
          <button
            type="button"
            className="admin-login-btn"
            onClick={onSignInClick}
            title={authConfigured ? 'Sign in to access admin controls' : 'Admin credentials not configured in environment'}
          >
            <IconLock size={13} />
            <span>{authConfigured ? 'Admin Sign In' : 'Admin (Unset)'}</span>
          </button>
        )}

        {/* Refresh button */}
        <button
          type="button"
          className={`refresh-btn ${loading ? 'is-loading' : ''}`}
          onClick={onRefresh}
          disabled={loading}
          aria-label="Refresh delivery workspace"
          title="Refresh delivery workspace"
        >
          <IconRefresh size={16} />
        </button>
      </div>
    </header>
  );
}
