import React, { useState } from 'react';
import { IconInfo, IconChevronRight, IconCheckCircle, IconBox, IconAlertTriangle } from './Icons';

interface OnboardingBannerProps {
  mode?: string;
  source?: string;
  dueDateBasis?: string;
}

export function OnboardingBanner({ mode, source, dueDateBasis = 'contractual' }: OnboardingBannerProps) {
  const [collapsed, setCollapsed] = useState(false);
  const isDemo = mode === 'demo';

  return (
    <section className="onboarding-banner" aria-labelledby="onboarding-title">
      <div className="onboarding-header">
        <div className="onboarding-intro">
          <div className="onboarding-badge-row">
            <span className="onboarding-label">SYSTEM CAPABILITY BRIEF</span>
            {isDemo ? (
              <span className="demo-indicator-pill">
                ERPNEXT TEST ENVIRONMENT
              </span>
            ) : (
              <span className="demo-indicator-pill live-pill" style={{ background: '#059669', color: '#ffffff' }}>
                ERPNEXT LIVE PROCUREMENT
              </span>
            )}
          </div>
          <h2 id="onboarding-title" className="onboarding-heading">
            Supplier Delivery Confirmation &amp; Delay Escalation
          </h2>
          <p className="onboarding-subheading">
            Monitor supplier purchase orders, delivery commitments, receipt evidence, and delivery risks from one unified workspace with strict read-only audit controls.
          </p>
        </div>
        <button
          type="button"
          className="onboarding-toggle-btn"
          onClick={() => setCollapsed(!collapsed)}
          aria-expanded={!collapsed}
        >
          {collapsed ? 'How This Works ▼' : 'Hide Guide ▲'}
        </button>
      </div>

      {!collapsed && (
        <div className="onboarding-body">
          <div className="workflow-steps-grid">
            <div className="step-card">
              <div className="step-num-badge">01</div>
              <div className="step-content">
                <strong>Read-Only Scan</strong>
                <p>
                  The ART agent executes read-only tool calls against ERPNext to retrieve live Purchase Orders and submitted receipts.
                </p>
              </div>
            </div>

            <div className="step-card">
              <div className="step-num-badge">02</div>
              <div className="step-content">
                <strong>Evidence Audit</strong>
                <p>
                  Receipts are verified only with exact PO item row linkages, submitted document status, and exhausted pagination.
                </p>
              </div>
            </div>

            <div className="step-card">
              <div className="step-num-badge">03</div>
              <div className="step-content">
                <strong>Risk Classification</strong>
                <p>
                  Evaluates arrival dates against the active <b>{dueDateBasis}</b> due-date schedule to flag Overdue, Due Today, and Upcoming deliveries.
                </p>
              </div>
            </div>

            <div className="step-card">
              <div className="step-num-badge">04</div>
              <div className="step-content">
                <strong>Human Exception Review</strong>
                <p>
                  Discrepancies, missing pagination, and delays are escalated to buyers for manual verification. Automated writes are prohibited.
                </p>
              </div>
            </div>
          </div>

          <div className="onboarding-context-chips">
            <div className="context-chip">
              <IconInfo size={14} className="chip-icon" />
              <span>
                <strong>Needs Verification:</strong> Evidence is incomplete or unevidenced. The system will never assume receipt without proof.
              </span>
            </div>
            <div className="context-chip">
              <IconCheckCircle size={14} className="chip-icon" />
              <span>
                <strong>Verified Completed:</strong> Full quantity confirmed through submitted exact-linked Purchase Receipts.
              </span>
            </div>
            <div className="context-chip">
              <IconAlertTriangle size={14} className="chip-icon" />
              <span>
                <strong>Zero Mutation:</strong> No PO edits, receipt creations, or supplier emails are performed by this system.
              </span>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
