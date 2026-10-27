import React, { useEffect } from 'react';
import {
  IconClose,
  IconShieldCheck,
  IconCheckCircle,
  IconAlertTriangle,
  IconInfo,
  IconBox,
} from './Icons';
import { DeliveryStatusBadge } from './StatusBadges';

interface OrderDrawerProps {
  order: any;
  onClose: () => void;
  stagedChasers?: any[];
  onApproveChaser?: (id: string) => void;
}

const fmtDate = (value?: string | null) =>
  value
    ? new Date(`${value.slice(0, 10)}T00:00:00`).toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    : 'Not specified';

const pretty = (val?: string) =>
  val
    ? val
        .replaceAll('_', ' ')
        .toLowerCase()
        .replace(/\b\w/g, (c) => c.toUpperCase())
    : 'Unknown';

export function OrderDrawer({ order, onClose, stagedChasers = [], onApproveChaser }: OrderDrawerProps) {
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <div
      className="drawer-backdrop"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="order-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="drawer-order-title"
      >
        {/* Drawer Header */}
        <div className="drawer-header">
          <div className="drawer-header-info">
            <span className="drawer-eyebrow">PURCHASE ORDER AUDIT DOSSIER</span>
            <div className="drawer-title-row">
              <h2 id="drawer-order-title" className="drawer-title monospace">
                {order.id}
              </h2>
              <span className="drawer-docstatus-pill">{pretty(order.status)}</span>
            </div>
            <div className="drawer-meta-line">
              <span className="meta-supplier">Supplier: <strong>{order.supplier}</strong></span>
              <span className="meta-sep">·</span>
              <span className="meta-date">Date: {fmtDate(order.transactionDate)}</span>
            </div>
          </div>
          <button
            type="button"
            className="drawer-close-btn"
            onClick={onClose}
            aria-label="Close order dossier"
          >
            <IconClose size={20} />
          </button>
        </div>

        {/* Drawer Content Body */}
        <div className="drawer-body">
          {order.items.map((item: any) => {
            const assessment = order.assessments?.find(
              (entry: any) => entry.orderItemId === item.id
            );
            const retrieval = item.receiptRetrieval;
            const orderedQty = assessment?.orderedQuantity ?? 0;
            const receivedQty = assessment?.receivedQuantity ?? 0;
            const outstandingQty = assessment?.outstandingQuantity ?? 0;
            const percent =
              orderedQty > 0
                ? Math.min(100, Math.round((receivedQty / orderedQty) * 100))
                : 0;

            return (
              <div key={item.id} className="item-audit-card">
                {/* Item Top Header */}
                <div className="item-card-header">
                  <div>
                    <h3 className="item-code-title">{item.itemCode || 'Unknown item code'}</h3>
                    <span className="item-id-badge monospace">
                      PO Line Item Row ID: {item.id || 'Missing'}
                    </span>
                  </div>
                  <DeliveryStatusBadge
                    status={assessment?.deliveryStatus}
                    partialReceipt={assessment?.partialReceipt}
                    size="md"
                  />
                </div>

                {item.description && (
                  <p className="item-description-text">{item.description}</p>
                )}

                {/* Progress / Fulfillment Bar */}
                <div className="fulfillment-meter-box">
                  <div className="meter-label-row">
                    <span>Receipt Fulfillment</span>
                    <strong>
                      {assessment?.receivedQuantity == null
                        ? 'Evidence Unverified'
                        : `${percent}% Received`}
                    </strong>
                  </div>
                  <div className="meter-track">
                    <div
                      className={`meter-fill ${
                        percent >= 100
                          ? 'meter-full'
                          : percent > 0
                          ? 'meter-partial'
                          : 'meter-empty'
                      }`}
                      style={{ width: `${percent}%` }}
                    />
                  </div>
                </div>

                {/* Quantity Tally Grid */}
                <div className="quantity-tally-grid">
                  <div className="tally-box">
                    <span className="tally-label">Ordered Qty</span>
                    <strong className="tally-value">{assessment?.orderedQuantity ?? '—'}</strong>
                  </div>
                  <div className="tally-box">
                    <span className="tally-label">Verified Received</span>
                    <strong className="tally-value text-green">
                      {assessment?.receivedQuantity == null
                        ? 'Unverified'
                        : assessment.receivedQuantity}
                    </strong>
                  </div>
                  <div className="tally-box">
                    <span className="tally-label">Outstanding Qty</span>
                    <strong
                      className={`tally-value ${
                        outstandingQty > 0 ? 'text-amber' : 'text-slate'
                      }`}
                    >
                      {assessment?.outstandingQuantity == null
                        ? 'Unverified'
                        : assessment.outstandingQuantity}
                    </strong>
                  </div>
                </div>

                {/* Delivery Dates Comparison Grid */}
                <div className="dates-comparison-section">
                  <div className="section-mini-heading">Delivery Schedule Comparison</div>
                  <div className="dates-grid">
                    <div className="date-tile">
                      <span className="date-tile-label">Contractual Item Date</span>
                      <strong className="date-tile-value">
                        {fmtDate(assessment?.baselineDate)}
                      </strong>
                    </div>
                    <div className="date-tile">
                      <span className="date-tile-label">Supplier Promised Date</span>
                      <strong className="date-tile-value">
                        {fmtDate(assessment?.promisedDate)}
                      </strong>
                    </div>
                    <div className="date-tile date-tile-active">
                      <div className="active-basis-tag">Active Schedule Basis</div>
                      <span className="date-tile-label">Applicable Due Date</span>
                      <strong className="date-tile-value text-blue">
                        {fmtDate(assessment?.applicableDueDate)}
                      </strong>
                    </div>
                  </div>
                </div>

                {/* Receipt Evidence Sub-section */}
                <div className="receipt-evidence-section">
                  <div className="section-mini-heading">
                    Submitted Purchase Receipt Evidence ({assessment?.receiptEvidence?.length || 0})
                  </div>
                  {assessment?.receiptEvidence?.length ? (
                    <div className="receipt-records-stack">
                      {assessment.receiptEvidence.map((receipt: any) => (
                        <div key={receipt.receiptItemId} className="receipt-evidence-card">
                          <div className="receipt-card-top">
                            <div className="receipt-id-group">
                              <IconCheckCircle size={15} className="receipt-check" />
                              <strong className="receipt-number monospace">
                                {receipt.receiptId}
                              </strong>
                              <span className="receipt-item-row monospace">
                                Row: {receipt.receiptItemId}
                              </span>
                            </div>
                            <span className="exact-match-tag">Exact Link Verified</span>
                          </div>

                          <div className="receipt-card-details">
                            <div className="detail-row">
                              <span>Linked PO:</span>
                              <strong className="monospace">{receipt.purchaseOrderId}</strong>
                              <span>Linked Row:</span>
                              <strong className="monospace">{receipt.purchaseOrderItemId}</strong>
                            </div>
                            <div className="detail-row">
                              <span>Quantity Credited:</span>
                              <strong>
                                {receipt.quantity} {receipt.isReturn ? '(Return Deduction)' : 'units'}
                              </strong>
                              <span>Document Status:</span>
                              <strong className="docstatus-submitted">
                                Submitted (docstatus: {receipt.docstatus})
                              </strong>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="no-receipts-notice">
                      <IconInfo size={16} />
                      <span>
                        No submitted Purchase Receipts matching this PO and item row ID have been recorded in ERPNext.
                      </span>
                    </div>
                  )}
                </div>

                {/* Supplier Order Acknowledgment (48h SLA) */}
                <div className="retrieval-audit-section">
                  <div className="section-mini-heading">Supplier Order Acknowledgment (48h SLA)</div>
                  <div className="audit-specs-grid">
                    <div className="spec-item">
                      <span className="spec-label">Confirmation Reference</span>
                      <strong className="spec-value monospace">
                        {order.orderConfirmationNo || 'None recorded'}
                      </strong>
                    </div>
                    <div className="spec-item">
                      <span className="spec-label">Confirmation Date</span>
                      <strong className="spec-value">
                        {fmtDate(order.orderConfirmationDate)}
                      </strong>
                    </div>
                    <div className="spec-item">
                      <span className="spec-label">Acknowledgment SLA</span>
                      <strong
                        className={`spec-value ${
                          assessment?.isAcknowledged
                            ? 'text-green'
                            : assessment?.acknowledgmentOverdue
                            ? 'text-red font-bold'
                            : 'text-amber'
                        }`}
                      >
                        {assessment?.isAcknowledged
                          ? '✓ Acknowledged'
                          : assessment?.acknowledgmentOverdue
                          ? '⚠️ Overdue (>48h SLA Breached)'
                          : '⏳ Pending (<48h)'}
                      </strong>
                    </div>
                  </div>
                </div>

                {/* Receipt Retrieval Audit Trail */}
                <div className="retrieval-audit-section">
                  <div className="section-mini-heading">Receipt Retrieval Audit Trail</div>
                  <div className="audit-specs-grid">
                    <div className="spec-item">
                      <span className="spec-label">Target Retrieval Scope</span>
                      <strong className="spec-value monospace">
                        {retrieval?.scope?.purchaseOrderId
                          ? `PO: ${retrieval.scope.purchaseOrderId} / Row: ${retrieval.scope.purchaseOrderItemId}`
                          : 'No scope evidenced'}
                      </strong>
                    </div>
                    <div className="spec-item">
                      <span className="spec-label">Pagination Exhaustion</span>
                      <strong className="spec-value">
                        {retrieval?.pagesRetrieved != null
                          ? `${retrieval.pagesRetrieved} page(s) · ${
                              retrieval.hasMore === false ? 'Exhausted (Complete)' : 'Has more pages'
                            }`
                          : 'Unevidenced'}
                      </strong>
                    </div>
                    <div className="spec-item">
                      <span className="spec-label">Completeness Claimed</span>
                      <strong
                        className={`spec-value ${
                          retrieval?.complete ? 'text-green' : 'text-amber'
                        }`}
                      >
                        {retrieval?.complete ? 'Verified Complete' : 'Incomplete / Missing'}
                      </strong>
                    </div>
                    <div className="spec-item">
                      <span className="spec-label">Connector Tool / Response</span>
                      <strong className="spec-value monospace">
                        {retrieval?.sourceToolId || 'N/A'} / {retrieval?.sourceResponseId || 'N/A'}
                      </strong>
                    </div>
                  </div>
                </div>

                {/* Human Verification Notice (if any verification reasons) */}
                {assessment?.verificationReasons?.length > 0 && (
                  <div className="verification-alert-box">
                    <div className="verification-alert-header">
                      <IconAlertTriangle size={16} />
                      <strong>Manual Verification Required</strong>
                    </div>
                    <ul className="verification-reasons-list">
                      {assessment.verificationReasons.map((reason: string, idx: number) => (
                        <li key={idx}>{reason}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            );
          })}

          {/* Staged Chasers Dossier Section */}
          {stagedChasers && stagedChasers.length > 0 && (
            <div className="receipt-evidence-section" style={{ marginTop: '24px' }}>
              <div className="section-mini-heading">
                Staged Supplier Chaser Follow-ups ({stagedChasers.length}) · auto_send: false
              </div>
              <div className="receipt-records-stack">
                {stagedChasers.map((chaser: any) => (
                  <div key={chaser.id} className="receipt-evidence-card">
                    <div className="receipt-card-top">
                      <div className="receipt-id-group">
                        <strong className="receipt-number monospace">{chaser.id}</strong>
                        <span className="receipt-item-row monospace">
                          Status: {chaser.status}
                        </span>
                      </div>
                      <span className="exact-match-tag">Urgency: {chaser.urgency}</span>
                    </div>
                    <div style={{ marginTop: '8px', fontSize: '13px' }}>
                      <p><strong>Subject:</strong> {chaser.subject}</p>
                      <pre style={{ whiteSpace: 'pre-wrap', background: '#f8fafc', padding: '10px', borderRadius: '6px', fontSize: '12px', marginTop: '6px', border: '1px solid #e2e8f0', color: '#1e293b' }}>
                        {chaser.body}
                      </pre>
                    </div>
                    {chaser.status === 'DRAFT' && onApproveChaser && (
                      <div style={{ marginTop: '10px' }}>
                        <button
                          type="button"
                          className="drawer-action-close"
                          style={{ background: '#059669', borderColor: '#059669', color: '#ffffff', padding: '6px 14px', fontSize: '12px', borderRadius: '4px' }}
                          onClick={() => onApproveChaser(chaser.id)}
                        >
                          ✓ Approve Chaser &amp; Authorize Dispatch
                        </button>
                      </div>
                    )}
                    {chaser.status === 'APPROVED' && (
                      <div style={{ marginTop: '8px', fontSize: '12px', color: '#059669', fontWeight: 600 }}>
                        ✓ Approved by {chaser.approvedBy || 'Buyer'} on {new Date(chaser.approvedAt).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Drawer Footer */}
        <div className="drawer-footer">
          <div className="drawer-footer-guard">
            <IconShieldCheck size={16} />
            <span>Read-Only Audit Trail · No records modified</span>
          </div>
          <button type="button" className="drawer-action-close" onClick={onClose}>
            Close Dossier
          </button>
        </div>
      </div>
    </div>
  );
}
