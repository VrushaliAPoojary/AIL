import React, { useState, useMemo } from 'react';
import {
  IconExceptions,
  IconShieldCheck,
  IconAlertTriangle,
  IconInfo,
  IconChevronRight,
  IconSearch,
} from './Icons';
import { DeliveryStatusBadge, SeverityBadge } from './StatusBadges';

interface ExceptionsViewProps {
  exceptions: any[];
  onSelect: (orderId: string) => void;
}

const fmtDate = (value?: string | null) =>
  value
    ? new Date(`${value.slice(0, 10)}T00:00:00`).toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    : 'Not specified';

export function ExceptionsView({ exceptions, onSelect }: ExceptionsViewProps) {
  const [severityFilter, setSeverityFilter] = useState('all');
  const [search, setSearch] = useState('');

  const filteredExceptions = useMemo(() => {
    return exceptions.filter((item) => {
      const matchSeverity =
        severityFilter === 'all' || item.severity?.toLowerCase() === severityFilter.toLowerCase();
      const matchText =
        `${item.orderId} ${item.supplier} ${item.itemCode} ${item.detected || ''} ${item.reason || ''}`
          .toLowerCase()
          .includes(search.trim().toLowerCase());
      return matchSeverity && matchText;
    });
  }, [exceptions, severityFilter, search]);

  const highCount = exceptions.filter((e) => e.severity === 'High').length;
  const reviewCount = exceptions.filter((e) => e.severity === 'Review').length;

  return (
    <section className="exceptions-workbench" aria-labelledby="exceptions-heading">
      <div className="workbench-top-bar">
        <div>
          <div className="eyebrow-tag">HUMAN OVERSIGHT QUEUE</div>
          <h2 id="exceptions-heading" className="workbench-heading">
            Delivery Exceptions Workbench
          </h2>
          <p className="workbench-subheading">
            Prioritized human review for delivery delays, incomplete evidence, and quantity reconciliation. Automated action is strictly prohibited.
          </p>
        </div>
        <div className="exceptions-summary-pills">
          <span className="summary-pill total-pill">
            <strong>{exceptions.length}</strong> Open Exceptions
          </span>
          {highCount > 0 && (
            <span className="summary-pill critical-pill">
              <strong>{highCount}</strong> Critical
            </span>
          )}
          {reviewCount > 0 && (
            <span className="summary-pill review-pill">
              <strong>{reviewCount}</strong> Verification
            </span>
          )}
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="exceptions-controls-bar">
        <div className="severity-tabs-row" role="tablist" aria-label="Filter exceptions by severity">
          <button
            type="button"
            className={`severity-tab-btn ${severityFilter === 'all' ? 'is-active' : ''}`}
            onClick={() => setSeverityFilter('all')}
          >
            All Exceptions ({exceptions.length})
          </button>
          <button
            type="button"
            className={`severity-tab-btn ${severityFilter === 'high' ? 'is-active' : ''}`}
            onClick={() => setSeverityFilter('high')}
          >
            Critical Overdue ({highCount})
          </button>
          <button
            type="button"
            className={`severity-tab-btn ${severityFilter === 'review' ? 'is-active' : ''}`}
            onClick={() => setSeverityFilter('review')}
          >
            Needs Verification ({reviewCount})
          </button>
          <button
            type="button"
            className={`severity-tab-btn ${severityFilter === 'medium' ? 'is-active' : ''}`}
            onClick={() => setSeverityFilter('medium')}
          >
            Partial Delivery ({exceptions.filter((e) => e.severity === 'Medium').length})
          </button>
        </div>

        <div className="exception-search-box">
          <IconSearch size={15} className="search-icon" />
          <input
            type="text"
            placeholder="Search exceptions by PO, supplier, or reason…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Search exceptions"
          />
          {search && (
            <button
              type="button"
              className="clear-search-btn"
              onClick={() => setSearch('')}
            >
              ×
            </button>
          )}
        </div>
      </div>

      {/* Exception Cards Stack */}
      <div className="exceptions-grid">
        {filteredExceptions.map((item) => {
          return (
            <article
              key={item.id}
              className={`exception-card priority-border-${item.severity?.toLowerCase()}`}
            >
              {/* Card Header */}
              <div className="exception-card-header">
                <div className="header-left-col">
                  <div className="po-supplier-line">
                    <strong className="order-id-badge monospace">{item.orderId}</strong>
                    <span className="supplier-name-bold">{item.supplier}</span>
                  </div>
                  <div className="item-schedule-line">
                    <span className="item-tag">Item: <strong>{item.itemCode}</strong></span>
                    <span className="row-tag monospace">Row ID: {item.orderItemId || 'Missing'}</span>
                    {item.dueDate && (
                      <span className="due-date-tag">Due Date: <strong>{fmtDate(item.dueDate)}</strong></span>
                    )}
                  </div>
                </div>

                <div className="header-right-col">
                  <SeverityBadge severity={item.severity} />
                  <DeliveryStatusBadge
                    status={item.status}
                    partialReceipt={item.status === 'PARTIALLY_RECEIVED'}
                    size="sm"
                  />
                </div>
              </div>

              {/* Structured Audit Matrix */}
              <div className="structured-audit-matrix">
                {/* 1. What Happened / Detected */}
                <div className="audit-cell cell-detected">
                  <div className="cell-label">
                    <span className="cell-num">1</span>
                    <strong>What Happened (Detected Anomaly)</strong>
                  </div>
                  <p className="cell-content-text">
                    {item.detected || item.reason}
                  </p>
                </div>

                {/* 2. Supporting Records */}
                <div className="audit-cell cell-records">
                  <div className="cell-label">
                    <span className="cell-num">2</span>
                    <strong>Supporting Evidenced Records</strong>
                  </div>
                  <ul className="cell-records-list">
                    {(item.supportingRecords || [`Purchase Order: ${item.orderId}`]).map(
                      (rec: string, index: number) => (
                        <li key={index} className="record-item monospace">
                          {rec}
                        </li>
                      )
                    )}
                  </ul>
                </div>

                {/* 3. Missing Evidence */}
                <div className="audit-cell cell-missing">
                  <div className="cell-label">
                    <span className="cell-num">3</span>
                    <strong>Missing or Conflicting Evidence</strong>
                  </div>
                  <ul className="cell-missing-list">
                    {(item.missingEvidence || [item.reason]).map((ev: string, index: number) => (
                      <li key={index}>{ev}</li>
                    ))}
                  </ul>
                </div>

                {/* 4. Actionable Next Step for Buyer */}
                <div className="audit-cell cell-action">
                  <div className="cell-label">
                    <span className="cell-num">4</span>
                    <strong>Required Human Buyer Action</strong>
                  </div>
                  <p className="cell-action-text">
                    {item.manualVerificationNeeded || item.suggestedNextStep}
                  </p>
                </div>
              </div>

              {/* Card Footer / Action */}
              <div className="exception-card-footer">
                <span className="safety-note">
                  Review ERPNext records directly. Never trigger automated supplier messages.
                </span>
                <button
                  type="button"
                  className="review-order-btn"
                  onClick={() => onSelect(item.orderId)}
                >
                  <span>Inspect Order &amp; Evidence</span>
                  <IconChevronRight size={15} />
                </button>
              </div>
            </article>
          );
        })}

        {filteredExceptions.length === 0 && (
          <div className="exceptions-empty-state">
            <IconShieldCheck size={36} className="empty-shield-icon" />
            <h3>No delivery exceptions found</h3>
            <p>
              {search
                ? `No exceptions matching "${search}".`
                : 'No delivery commitments require human buyer review under the current filter.'}
            </p>
          </div>
        )}
      </div>

      <div className="workbench-footer-note">
        <IconInfo size={15} className="note-icon" />
        <span>
          <strong>Human Oversight Rule:</strong> Automated supplier email dispatch, Purchase Order amendments, and inventory writebacks are prohibited. Exceptions must be reconciled manually with suppliers or dock receivers.
        </span>
      </div>
    </section>
  );
}
