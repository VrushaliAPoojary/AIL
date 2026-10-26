import React, { useState, useMemo } from 'react';
import {
  IconSearch,
  IconAlertTriangle,
  IconClock,
  IconCheckCircle,
  IconArrowRight,
  IconHelpCircle,
  IconOrders,
  IconRuns,
  IconRefresh,
} from './Icons';
import { DeliveryStatusBadge } from './StatusBadges';

interface PoDelayAnalyzerProps {
  orders: any[];
  monitoringDate: string;
  timezone?: string;
  dueDateBasis?: string;
  selectedOrderId: string | null;
  onSelectOrder: (id: string | null) => void;
  onRunMonitoring?: () => void;
  isRunBusy?: boolean;
}

export function PoDelayAnalyzer({
  orders = [],
  monitoringDate,
  dueDateBasis = 'contractual',
  selectedOrderId,
  onSelectOrder,
  onRunMonitoring,
  isRunBusy = false,
}: PoDelayAnalyzerProps) {
  const [searchInput, setSearchInput] = useState('');

  // Find active orders and assessments
  const activeOrders = useMemo(() => orders.filter((o) => o.docstatus === 1), [orders]);

  // Determine which PO is currently active in the analyzer
  const activePo = useMemo(() => {
    if (searchInput.trim()) {
      const q = searchInput.trim().toLowerCase();
      const match = orders.find(
        (o) =>
          o.id.toLowerCase() === q ||
          o.id.toLowerCase().includes(q) ||
          o.supplier.toLowerCase().includes(q) ||
          o.items?.some((it: any) => it.itemCode?.toLowerCase().includes(q))
      );
      if (match) return match;
    }
    if (selectedOrderId) {
      const match = orders.find((o) => o.id === selectedOrderId);
      if (match) return match;
    }
    // Default to the first overdue or interesting PO
    return (
      orders.find((o) =>
        o.assessments?.some((a: any) => a.deliveryStatus === 'OVERDUE')
      ) ||
      orders[0] ||
      null
    );
  }, [orders, searchInput, selectedOrderId]);

  // Extract assessment and calculation metrics for the selected PO
  const analysis = useMemo(() => {
    if (!activePo) return null;
    const items = activePo.items || [];
    const assessments = activePo.assessments || [];
    const primaryItem = items[0] || {};
    const primaryAssessment = assessments[0] || {};

    const orderedQty = primaryAssessment.orderedQuantity ?? primaryItem.orderedQuantity ?? 0;
    const receivedQty = primaryAssessment.receivedQuantity ?? 0;
    const outstandingQty = primaryAssessment.outstandingQuantity ?? Math.max(0, orderedQty - receivedQty);
    const status = primaryAssessment.deliveryStatus || 'UPCOMING';
    const dueDate =
      dueDateBasis === 'supplier_promise' && primaryItem.expectedDeliveryDate
        ? primaryItem.expectedDeliveryDate
        : primaryItem.scheduleDate || primaryItem.expectedDeliveryDate;

    // Calculate delay in calendar days relative to monitoringDate
    let delayDays = 0;
    let isOverdue = false;
    let isDueToday = false;
    let isUpcoming = false;

    if (dueDate && monitoringDate) {
      const dueTime = new Date(dueDate).getTime();
      const todayTime = new Date(monitoringDate).getTime();
      const diffMs = todayTime - dueTime;
      const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));

      if (diffDays > 0) {
        delayDays = diffDays;
        isOverdue = true;
      } else if (diffDays === 0) {
        isDueToday = true;
      } else {
        delayDays = Math.abs(diffDays);
        isUpcoming = true;
      }
    }

    const percentFulfilled =
      orderedQty > 0 ? Math.min(100, Math.round((receivedQty / orderedQty) * 100)) : 0;

    // Build specific procurement solutions based on status & evidence
    const solutions: Array<{ step: string; title: string; action: string; urgency: 'Critical' | 'High' | 'Normal' }> = [];

    if (status === 'OVERDUE') {
      solutions.push({
        step: '1',
        title: 'Immediate Supplier Follow-up & Dispatch Tracking',
        action: `Contact ${activePo.supplier} immediately. Request the consignment dispatch note (e.g. AWB/tracking code) for the remaining ${outstandingQty} outstanding units of ${primaryItem.itemCode || 'item'}.`,
        urgency: 'Critical',
      });
      solutions.push({
        step: '2',
        title: 'Warehouse Inward Staging Inspection',
        action: `Check goods-receiving staging at the dock. Confirm whether a partial physical shipment arrived without an approved ERPNext Purchase Receipt docstatus.`,
        urgency: 'High',
      });
      solutions.push({
        step: '3',
        title: 'Production Line Impact Mitigation',
        action: `Verify stock buffer in ERPNext for ${primaryItem.itemCode}. If work order schedule is jeopardized, request emergency expedited freight at supplier expense.`,
        urgency: 'High',
      });
      solutions.push({
        step: '4',
        title: 'Update Supplier Promise Date in ERPNext',
        action: `Obtain a formal revised delivery commitment from ${activePo.supplier} and record it under expected_delivery_date to maintain procurement auditability.`,
        urgency: 'Normal',
      });
    } else if (status === 'PARTIALLY_RECEIVED' || primaryAssessment.partialReceipt) {
      solutions.push({
        step: '1',
        title: 'Reconcile Balance Delivery Schedule',
        action: `A partial receipt of ${receivedQty} units is verified. Contact ${activePo.supplier} to confirm the ship date and carrier details for the remaining ${outstandingQty} units.`,
        urgency: 'High',
      });
      solutions.push({
        step: '2',
        title: 'Inspect Quality of Received Batch',
        action: `Confirm with Quality Assurance that the ${receivedQty} received units passed incoming inspection before clearing billing release in ERPNext.`,
        urgency: 'Normal',
      });
      solutions.push({
        step: '3',
        title: 'Monitor Due Date for Balance',
        action: `Ensure the remaining balance is scheduled to arrive before ${dueDate || 'target date'} to prevent partial shipment escalation.`,
        urgency: 'Normal',
      });
    } else if (status === 'DUE_TODAY') {
      solutions.push({
        step: '1',
        title: 'Dock Intake Alert',
        action: `Alert warehouse receiving team that ${orderedQty} units from ${activePo.supplier} are scheduled for delivery today. Prepare unloading bay and goods receipt paperwork.`,
        urgency: 'High',
      });
      solutions.push({
        step: '2',
        title: 'Carrier Gate Verification',
        action: `Confirm truck arrival with carrier logistics coordinator before the daily receiving cut-off window.`,
        urgency: 'Normal',
      });
    } else if (status === 'NEEDS_VERIFICATION') {
      solutions.push({
        step: '1',
        title: 'Audit Source Receipt Row References',
        action: `Evidence discrepancy detected: ${primaryAssessment.verificationReasons?.[0] || 'Unverified row link or incomplete pagination'}. Open ERPNext and verify item code and row IDs match exact PO line.`,
        urgency: 'High',
      });
      solutions.push({
        step: '2',
        title: 'Verify Draft or Cancelled Receipts',
        action: `Check if any Purchase Receipt against ${activePo.id} is currently in draft (docstatus 0) or cancelled (docstatus 2). Submit draft receipts once goods are inspected.`,
        urgency: 'Normal',
      });
    } else if (status === 'RECEIVED') {
      solutions.push({
        step: '1',
        title: 'Delivery Complete — Ready for Purchase Invoice Matching',
        action: `All ${receivedQty} units have been verified against submitted receipts. The order is fulfilled and cleared for accounts payable matching.`,
        urgency: 'Normal',
      });
    } else {
      solutions.push({
        step: '1',
        title: 'On Track for Delivery',
        action: `Delivery is on schedule for ${dueDate} (${delayDays} days remaining). Review supplier status 48 hours prior to delivery date.`,
        urgency: 'Normal',
      });
    }

    return {
      primaryItem,
      primaryAssessment,
      orderedQty,
      receivedQty,
      outstandingQty,
      status,
      dueDate,
      delayDays,
      isOverdue,
      isDueToday,
      isUpcoming,
      percentFulfilled,
      solutions,
      receipts: primaryItem.receipts || [],
    };
  }, [activePo, monitoringDate, dueDateBasis]);

  return (
    <section className="po-delay-analyzer-card" aria-label="Purchase Order Delay and Solution Finder">
      {/* Hero Header */}
      <div className="analyzer-header">
        <div className="analyzer-title-group">
          <div className="analyzer-icon-badge">
            <IconSearch size={22} />
          </div>
          <div>
            <h2 className="analyzer-heading">Purchase Order Delay & Solution Finder</h2>
            <p className="analyzer-subheading">
              Enter any PO ID to immediately calculate delivery delays, inspect receipt evidence, and get step-by-step resolution actions.
            </p>
          </div>
        </div>

        {onRunMonitoring && (
          <button
            type="button"
            className="analyzer-run-btn"
            onClick={onRunMonitoring}
            disabled={isRunBusy}
            title="Execute automated monitoring run across all purchase orders"
          >
            {isRunBusy ? (
              <>
                <span className="btn-spinner" />
                <span>Scanning ERPNext…</span>
              </>
            ) : (
              <>
                <IconRuns size={16} />
                <span>Run Monitoring Scan</span>
              </>
            )}
          </button>
        )}
      </div>

      {/* Quick Search & Select Bar */}
      <div className="analyzer-search-row">
        <div className="analyzer-input-wrapper">
          <IconSearch size={18} className="analyzer-search-icon" />
          <input
            type="text"
            className="analyzer-search-input"
            placeholder="Type Purchase Order ID (e.g. SYN-PO-2601, PO-2602) or supplier..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          {searchInput && (
            <button
              type="button"
              className="analyzer-clear-btn"
              onClick={() => setSearchInput('')}
              aria-label="Clear search"
            >
              ×
            </button>
          )}
        </div>

        {/* Quick select chips for easy 1-click exploration */}
        <div className="analyzer-chips-container">
          <span className="chips-label">Quick select:</span>
          {activeOrders.slice(0, 6).map((order) => {
            const st = order.assessments?.[0]?.deliveryStatus || 'UPCOMING';
            const isSelected = activePo?.id === order.id;
            return (
              <button
                key={order.id}
                type="button"
                className={`po-chip ${isSelected ? 'active' : ''} chip-${st.toLowerCase()}`}
                onClick={() => {
                  setSearchInput(order.id);
                  onSelectOrder(order.id);
                }}
              >
                <strong>{order.id}</strong>
                <span className="chip-status-text">
                  {st === 'OVERDUE'
                    ? '⚠️ Overdue'
                    : st === 'DUE_TODAY'
                    ? '⏰ Due Today'
                    : st === 'PARTIALLY_RECEIVED'
                    ? '📦 Partial'
                    : st === 'RECEIVED'
                    ? '✅ Received'
                    : st === 'NEEDS_VERIFICATION'
                    ? '❓ Needs Audit'
                    : '📅 Upcoming'}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Analysis Display */}
      {activePo && analysis ? (
        <div className="analyzer-results-grid">
          {/* Top Status & Delay Metrics Banner */}
          <div className={`analyzer-status-banner banner-${analysis.status.toLowerCase()}`}>
            <div className="banner-badge-col">
              <span className="banner-po-id">{activePo.id}</span>
              <DeliveryStatusBadge status={analysis.status} size="lg" />
              <span className="banner-supplier-text">Supplier: <strong>{activePo.supplier}</strong></span>
            </div>

            <div className="banner-calc-col">
              <div className="delay-metric-box">
                <span className="delay-metric-title">Delay Calculation</span>
                {analysis.isOverdue ? (
                  <div className="delay-metric-value text-red">
                    <IconAlertTriangle size={20} />
                    <span><strong>{analysis.delayDays} Days Overdue</strong></span>
                  </div>
                ) : analysis.isDueToday ? (
                  <div className="delay-metric-value text-amber">
                    <IconClock size={20} />
                    <span><strong>Due Today ({analysis.dueDate})</strong></span>
                  </div>
                ) : analysis.status === 'RECEIVED' ? (
                  <div className="delay-metric-value text-green">
                    <IconCheckCircle size={20} />
                    <span><strong>100% Received in Full</strong></span>
                  </div>
                ) : (
                  <div className="delay-metric-value text-blue">
                    <IconArrowRight size={20} />
                    <span><strong>On Schedule ({analysis.delayDays} days left)</strong></span>
                  </div>
                )}
                <div className="delay-metric-sub">
                  Scheduled Delivery: <strong>{analysis.dueDate || 'Not set'}</strong> | Monitoring Date: <strong>{monitoringDate}</strong>
                </div>
              </div>
            </div>

            <div className="banner-qty-col">
              <div className="qty-progress-header">
                <span>Fulfillment Progress</span>
                <strong>{analysis.percentFulfilled}%</strong>
              </div>
              <div className="qty-progress-bar-bg">
                <div
                  className={`qty-progress-bar-fill fill-${analysis.status.toLowerCase()}`}
                  style={{ width: `${analysis.percentFulfilled}%` }}
                />
              </div>
              <div className="qty-stats-grid">
                <div>Ordered: <strong>{analysis.orderedQty}</strong></div>
                <div>Received: <strong>{analysis.receivedQty}</strong></div>
                <div>Pending: <strong className={analysis.outstandingQty > 0 ? 'text-orange' : ''}>{analysis.outstandingQty}</strong></div>
              </div>
            </div>
          </div>

          {/* Solutions & Action Plan Box (Requested by user) */}
          <div className="analyzer-solutions-section">
            <div className="solutions-header">
              <div className="solutions-header-icon">📋</div>
              <div>
                <h3 className="solutions-title">Recommended Procurement Solutions & Action Plan</h3>
                <p className="solutions-subtitle">
                  AI & rule-based operational steps to resolve this delivery status and mitigate production risk.
                </p>
              </div>
            </div>

            <div className="solutions-list">
              {analysis.solutions.map((item) => (
                <div key={item.step} className={`solution-item urgency-${item.urgency.toLowerCase()}`}>
                  <div className="solution-step-number">{item.step}</div>
                  <div className="solution-content">
                    <div className="solution-title-row">
                      <h4 className="solution-item-title">{item.title}</h4>
                      <span className={`urgency-pill pill-${item.urgency.toLowerCase()}`}>
                        {item.urgency} Action
                      </span>
                    </div>
                    <p className="solution-item-action">{item.action}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Supporting Evidence Breakdown */}
          <div className="analyzer-evidence-section">
            <h4 className="evidence-section-title">
              <span>Supporting Evidence Records</span>
              <span className="evidence-count">({analysis.receipts.length} Receipt Records Linked)</span>
            </h4>

            {analysis.receipts.length === 0 ? (
              <div className="empty-evidence-box">
                <IconHelpCircle size={18} />
                <span>No submitted Purchase Receipts found in ERPNext for this line. All {analysis.orderedQty} units remain outstanding.</span>
              </div>
            ) : (
              <div className="evidence-table-wrapper">
                <table className="evidence-table">
                  <thead>
                    <tr>
                      <th>Receipt ID</th>
                      <th>Linked PO Item</th>
                      <th>Receipt Item Row</th>
                      <th>Docstatus</th>
                      <th>Verified Quantity</th>
                      <th>Link Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analysis.receipts.map((r: any, idx: number) => (
                      <tr key={`${r.receiptId}-${idx}`}>
                        <td className="font-mono font-bold">{r.receiptId}</td>
                        <td className="font-mono text-xs">{r.purchaseOrderItemId || '—'}</td>
                        <td className="font-mono text-xs">{r.receiptItemId || '—'}</td>
                        <td>
                          <span className={`docstatus-badge docstatus-${r.docstatus}`}>
                            {r.docstatus === 1 ? 'Submitted (1)' : r.docstatus === 0 ? 'Draft (0)' : 'Cancelled (2)'}
                          </span>
                        </td>
                        <td>
                          <strong>{r.quantity}</strong> {r.isReturn ? ' (Return)' : ''}
                        </td>
                        <td>
                          {r.docstatus === 1 && !r.isReturn ? (
                            <span className="status-badge-inline text-green">
                              <IconCheckCircle size={14} /> Verified Exact Link
                            </span>
                          ) : (
                            <span className="status-badge-inline text-amber">
                              <IconAlertTriangle size={14} /> {r.isReturn ? 'Return deducted' : 'Unconfirmed'}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="analyzer-empty-state">
          <IconSearch size={32} />
          <p>No purchase order matching &ldquo;{searchInput}&rdquo; was found.</p>
          <button
            type="button"
            className="analyzer-reset-btn"
            onClick={() => setSearchInput('')}
          >
            Show All Purchase Orders
          </button>
        </div>
      )}
    </section>
  );
}
