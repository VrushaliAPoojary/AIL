import React from 'react';
import {
  IconLogo,
  IconDashboard,
  IconOrders,
  IconExceptions,
  IconRuns,
  IconWorkflow,
  IconConfiguration,
  IconShieldCheck,
  IconClose,
} from './Icons';

export type ViewId = 'overview' | 'orders' | 'exceptions' | 'runs' | 'workflow' | 'configuration';

export interface NavItemConfig {
  id: ViewId;
  label: string;
  badge?: number | string | null;
  badgeTone?: 'red' | 'blue' | 'neutral';
}

interface DeliverySidebarProps {
  currentView: ViewId;
  onSelectView: (view: ViewId) => void;
  ordersCount?: number;
  exceptionsCount?: number;
  needsVerificationCount?: number;
  activeRun?: boolean;
  isOpenMobile?: boolean;
  onCloseMobile?: () => void;
}

export function DeliverySidebar({
  currentView,
  onSelectView,
  ordersCount = 0,
  exceptionsCount = 0,
  needsVerificationCount = 0,
  activeRun = false,
  isOpenMobile = false,
  onCloseMobile,
}: DeliverySidebarProps) {
  const navItems: NavItemConfig[] = [
    { id: 'overview', label: 'Mission Overview' },
    { id: 'orders', label: 'Purchase Orders', badge: ordersCount > 0 ? ordersCount : null },
    {
      id: 'exceptions',
      label: 'Exception Workbench',
      badge: exceptionsCount > 0 ? exceptionsCount : null,
      badgeTone: needsVerificationCount > 0 ? 'red' : 'neutral',
    },
    {
      id: 'runs',
      label: 'Monitoring Run Center',
      badge: activeRun ? 'Running' : null,
      badgeTone: 'blue',
    },
    { id: 'workflow', label: 'Workflow & Evidence' },
    { id: 'configuration', label: 'System Configuration' },
  ];

  const getNavIcon = (id: ViewId) => {
    switch (id) {
      case 'overview':
        return <IconDashboard size={18} />;
      case 'orders':
        return <IconOrders size={18} />;
      case 'exceptions':
        return <IconExceptions size={18} />;
      case 'runs':
        return <IconRuns size={18} />;
      case 'workflow':
        return <IconWorkflow size={18} />;
      case 'configuration':
        return <IconConfiguration size={18} />;
    }
  };

  return (
    <>
      {isOpenMobile && (
        <div
          className="sidebar-backdrop"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}
      <aside className={`delivery-sidebar ${isOpenMobile ? 'is-open-mobile' : ''}`}>
        {/* Brand identity */}
        <div className="sidebar-brand-wrapper">
          <div className="sidebar-brand">
            <IconLogo size={36} className="brand-logo-icon" />
            <div className="brand-text">
              <div className="brand-title-row">
                <span className="brand-code-badge">P02</span>
                <strong className="brand-name">DELIVERY</strong>
              </div>
              <span className="brand-sub">CONTROL CENTER</span>
            </div>
          </div>
          {onCloseMobile && (
            <button
              type="button"
              className="mobile-close-btn"
              onClick={onCloseMobile}
              aria-label="Close menu"
            >
              <IconClose size={20} />
            </button>
          )}
        </div>

        {/* Section label */}
        <div className="sidebar-section-label">OPERATIONS WORKSPACE</div>

        {/* Navigation list */}
        <nav className="sidebar-nav" aria-label="Main Navigation">
          {navItems.map((item) => {
            const isActive = currentView === item.id;
            return (
              <button
                key={item.id}
                type="button"
                className={`nav-btn ${isActive ? 'is-active' : ''}`}
                onClick={() => {
                  onSelectView(item.id);
                  if (onCloseMobile) onCloseMobile();
                }}
              >
                <span className="nav-btn-icon" aria-hidden="true">
                  {getNavIcon(item.id)}
                </span>
                <span className="nav-btn-label">{item.label}</span>
                {item.badge != null && (
                  <span className={`nav-badge badge-${item.badgeTone || 'neutral'}`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Safeguard badge */}
        <div className="sidebar-safeguard-card">
          <div className="safeguard-icon-row">
            <IconShieldCheck size={18} className="safeguard-shield" />
            <strong>Read-Only Guardrails</strong>
          </div>
          <p>
            Automated ERPNext write operations and external supplier messaging are strictly disabled in this control center.
          </p>
        </div>

        {/* Sidebar footer: Process & Owner */}
        <div className="sidebar-footer">
          <div className="process-info-row">
            <span className="process-status-dot" aria-hidden="true" />
            <span className="process-code">WF-P02</span>
            <span className="process-title">Delivery Reconciliation</span>
          </div>
          <div className="owner-profile-card">
            <div className="owner-avatar" aria-hidden="true">VP</div>
            <div className="owner-meta">
              <strong className="owner-name">Vrushali Poojary</strong>
              <span className="owner-role">Process Owner · AIL</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
