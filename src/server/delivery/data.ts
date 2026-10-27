import 'server-only';
import { classifyPurchaseOrders } from './classifier';
import { getDeliverySettings, getIntegrationStatus, getLocalBusinessDate } from './config';
import { listAuditEvents, listStagedChasers, listSupplierPromises } from './store';
import { getRunHistory } from './runService';
import { publicRunRecord, type PurchaseOrder } from './types';

function shiftDate(date: string, days: number) {
  const value = new Date(`${date}T00:00:00Z`);
  value.setUTCDate(value.getUTCDate() + days);
  return value.toISOString().slice(0, 10);
}

export function erpnextPurchaseOrders(today: string): PurchaseOrder[] {
  const createOrder = (
    id: string,
    itemId: string,
    supplier: string,
    itemCode: string,
    description: string,
    orderedQty: number,
    scheduleOffset: number,
    receivedQty: number,
    retrievalComplete = true,
    expectedOffset: number | null = null,
    receiptId: string | null = null,
    receiptItemId: string | null = null,
    confirmationNo: string | null = null,
    confirmationOffset: number | null = null,
    txOffset = -14
  ): PurchaseOrder => {
    const receipts = receivedQty > 0 ? [{
      receiptId: receiptId || `MAT-PRE-${id.slice(-4)}-01`,
      receiptItemId: receiptItemId || `${itemId}-REC-01`,
      purchaseOrderId: id,
      purchaseOrderItemId: itemId,
      quantity: receivedQty,
      docstatus: 1,
    }] : [];
    return {
      id,
      supplier,
      transactionDate: shiftDate(today, txOffset),
      docstatus: 1,
      status: receivedQty === orderedQty ? 'Completed' : 'To Receive and Bill',
      orderConfirmationNo: confirmationNo,
      orderConfirmationDate: confirmationOffset !== null ? shiftDate(today, confirmationOffset) : null,
      items: [{
        id: itemId,
        itemCode,
        description,
        orderedQuantity: orderedQty,
        scheduleDate: id.endsWith('0006') ? null : shiftDate(today, scheduleOffset),
        expectedDeliveryDate: expectedOffset === null ? null : shiftDate(today, expectedOffset),
        receiptRetrieval: {
          scope: { purchaseOrderId: id, purchaseOrderItemId: itemId },
          complete: retrievalComplete,
          pagesRetrieved: 1,
          hasMore: false,
        },
        receipts,
      }],
    };
  };

  return [
    createOrder('PUR-ORD-2026-0001', 'POI-2026-0001-01', 'Bharat Precision Bearings', 'IND-BEAR-6205-01', 'Deep Groove Ball Bearing 6205-2RS', 100, -2, 0, true, 1, null, null, 'CONF-BPB-9921', -12),
    createOrder('PUR-ORD-2026-0002', 'POI-2026-0002-01', 'Apex Industrial Supplies', 'RAW-MTL-STEEL-01', 'Cold Rolled Steel Coil 1.2mm Grade A', 500, 0, 0, true, null, null, null, 'CONF-AIS-4421', -10),
    createOrder('PUR-ORD-2026-0003', 'POI-2026-0003-01', 'Kirloskar Electric Ltd', 'ELEC-MOT-415V-02', '3-Phase Induction Motor 415V 5HP 1440RPM', 50, 3, 20, true, null, null, null, 'CONF-KEL-2091', -11),
    // Order 0004 issued 5 days ago with NO confirmation number/date -> Triggers Acknowledgment Overdue (>48h SLA)
    createOrder('PUR-ORD-2026-0004', 'POI-2026-0004-01', 'Tata Steel Distributors', 'STEEL-ROD-EN8-01', 'EN8 Carbon Steel Round Rod Dia 25mm', 200, 12, 0, true, null, null, null, null, null, -5),
    createOrder('PUR-ORD-2026-0005', 'POI-2026-0005-01', 'Schneider Electric India', 'ELEC-SW-MCB-32A', 'Miniature Circuit Breaker 32A 3-Pole C-Curve', 100, -10, 100, true, null, null, null, 'CONF-SEI-1020', -13),
    createOrder('PUR-ORD-2026-0006', 'POI-2026-0006-01', 'Festo Pneumatics India', 'PNEU-VALV-SOL-01', '5/2 Solenoid Air Valve 24V DC G1/4', 75, 4, 0, false, null, null, null, 'CONF-FPI-5501', -10),
    {
      id: 'PUR-ORD-2026-0007',
      supplier: 'Larsen Precision Machining',
      transactionDate: shiftDate(today, -3),
      docstatus: 2,
      status: 'Cancelled',
      items: [{
        id: 'POI-2026-0007-01',
        itemCode: 'MACH-FLG-SS304',
        description: 'CNC Machined Flange SS304 Class 150',
        orderedQuantity: 50,
        scheduleDate: shiftDate(today, -1),
        expectedDeliveryDate: null,
        receiptRetrieval: {
          scope: { purchaseOrderId: 'PUR-ORD-2026-0007', purchaseOrderItemId: 'POI-2026-0007-01' },
          complete: true,
          pagesRetrieved: 1,
          hasMore: false,
        },
        receipts: [],
      }],
    },
    {
      id: 'PUR-ORD-2026-0008',
      supplier: 'Hydraulics India Tech',
      transactionDate: shiftDate(today, -20),
      docstatus: 1,
      status: 'Closed',
      orderConfirmationNo: 'CONF-HIT-0081',
      orderConfirmationDate: shiftDate(today, -18),
      items: [{
        id: 'POI-2026-0008-01',
        itemCode: 'HYDR-HOSE-HIGH-01',
        description: 'High Pressure Hydraulic Hose Assembly 1/2 inch',
        orderedQuantity: 100,
        scheduleDate: shiftDate(today, -15),
        expectedDeliveryDate: null,
        receiptRetrieval: {
          scope: { purchaseOrderId: 'PUR-ORD-2026-0008', purchaseOrderItemId: 'POI-2026-0008-01' },
          complete: true,
          pagesRetrieved: 1,
          hasMore: false,
        },
        receipts: [],
      }],
    },
  ];
}

export const demoOrders = erpnextPurchaseOrders;

function summarize(orders: PurchaseOrder[], assessments: ReturnType<typeof classifyPurchaseOrders>) {
  const activeOrders = orders.filter((order) => order.docstatus === 1 && order.status !== 'Closed');
  const active = assessments.filter((item) => !item.excluded);
  const statuses = (status: typeof active[number]['deliveryStatus']) => active.filter((item) => item.deliveryStatus === status);
  const byOrder = (status: typeof active[number]['deliveryStatus']) => new Set(statuses(status).map((item) => item.orderId)).size;
  return {
    totalOrders: activeOrders.length,
    overdue: byOrder('OVERDUE'),
    dueToday: byOrder('DUE_TODAY'),
    upcoming: byOrder('UPCOMING'),
    received: activeOrders.filter((order) => {
      const items = active.filter((item) => item.orderId === order.id);
      return items.length > 0 && items.every((item) => item.deliveryStatus === 'RECEIVED');
    }).length,
    partialReceipts: new Set(active.filter((item) => item.partialReceipt || item.deliveryStatus === 'PARTIALLY_RECEIVED').map((item) => item.orderId)).size,
    needsVerification: byOrder('NEEDS_VERIFICATION'),
    ackOverdue: active.filter((item) => item.acknowledgmentOverdue).length,
  };
}

function buildExceptions(assessments: ReturnType<typeof classifyPurchaseOrders>) {
  return assessments.filter((item) => !item.excluded && (
    item.deliveryStatus === 'OVERDUE' || item.deliveryStatus === 'DUE_TODAY' ||
    item.deliveryStatus === 'NEEDS_VERIFICATION' || item.partialReceipt || item.deliveryStatus === 'PARTIALLY_RECEIVED' ||
    item.acknowledgmentOverdue
  )).map((item) => {
    const isAckOnly = item.acknowledgmentOverdue && item.deliveryStatus !== 'OVERDUE' && item.deliveryStatus !== 'NEEDS_VERIFICATION';
    const detected = isAckOnly
      ? `Supplier acknowledgment overdue: Order issued >48h ago without formal order confirmation number or date.`
      : item.deliveryStatus === 'OVERDUE'
        ? `Overdue commitment: ${item.outstandingQuantity ?? 'unverified'} units outstanding past ${item.applicableDueDate || 'scheduled date'}${item.partialReceipt ? ' (partially received)' : ''}.`
        : item.deliveryStatus === 'DUE_TODAY'
          ? `Due today: ${item.outstandingQuantity ?? 'unverified'} units scheduled for arrival today (${item.applicableDueDate}).`
          : item.deliveryStatus === 'NEEDS_VERIFICATION'
            ? `Evidence uncertainty: ${item.verificationReasons[0] || 'Required evidence is incomplete or unverified'}.`
            : `Partial delivery: ${item.receivedQuantity ?? 0}/${item.orderedQuantity ?? '?'} units confirmed received, ${item.outstandingQuantity ?? '?'} units outstanding.`;

    const supportingRecords = [
      `Purchase Order: ${item.orderId} (Row: ${item.orderItemId || 'missing'})`,
      ...(item.isAcknowledged ? [`Supplier Confirmation: ${item.orderId} acknowledged`] : ['Supplier Confirmation: None recorded (overdue >48h)']),
      ...item.receiptEvidence.map((r) => `Purchase Receipt: ${r.receiptId} (Row: ${r.receiptItemId}, Qty: ${r.quantity}${r.isReturn ? ', Return' : ''})`),
    ];

    const missingEvidence = item.verificationReasons.length > 0
      ? item.verificationReasons
      : item.acknowledgmentOverdue && !item.isAcknowledged
        ? ['Supplier order confirmation reference (order_confirmation_no/date) is missing (>48h SLA elapsed).']
        : item.partialReceipt
          ? ['Subsequent receipt evidence for the remaining quantity is not yet recorded in ERPNext.']
          : ['No missing evidence; verified against retrieved source records.'];

    const manualVerificationNeeded = item.deliveryStatus === 'NEEDS_VERIFICATION'
      ? 'Inspect ERPNext Purchase Order and Purchase Receipt items directly to verify row links, docstatus, and pagination completeness before classifying.'
      : isAckOnly
        ? `Review with purchasing agent and stage a 48h acknowledgment chaser email for ${item.supplier}.`
        : item.deliveryStatus === 'OVERDUE'
          ? `Review open commitment with procurement buyer and determine whether to stage an expedite chaser for ${item.supplier}.`
          : item.partialReceipt
            ? `Confirm supplier dispatch status and estimated arrival date for the remaining ${item.outstandingQuantity ?? 'open'} units.`
            : 'Confirm delivery arrival and receiving inspection with warehouse dock team.';

    return {
      id: `${item.orderId}:${item.orderItemId}`,
      orderId: item.orderId,
      orderItemId: item.orderItemId,
      supplier: item.supplier,
      itemCode: item.itemCode,
      status: isAckOnly ? 'ACK_OVERDUE' : item.deliveryStatus,
      severity: item.deliveryStatus === 'OVERDUE' ? 'High' : isAckOnly ? 'High' : item.deliveryStatus === 'NEEDS_VERIFICATION' ? 'Review' : item.partialReceipt ? 'Medium' : 'Low',
      reason: isAckOnly ? 'Order acknowledgment SLA exceeded (>48 hours without confirmation).' : item.verificationReasons[0] || (item.partialReceipt ? 'Submitted receipt evidence confirms only a partial quantity.' : item.deliveryStatus === 'OVERDUE' ? 'Verified open quantity remains after the applicable due date.' : `${item.deliveryStatus.replaceAll('_', ' ').toLowerCase()} delivery needs buyer attention.`),
      suggestedNextStep: isAckOnly ? 'Stage a 48h supplier chaser draft to request formal acknowledgment.' : item.deliveryStatus === 'NEEDS_VERIFICATION' ? 'Review ERPNext PO and receipt item references before classifying.' : item.deliveryStatus === 'OVERDUE' ? 'Review the supplier status and stage an expedite chaser.' : item.partialReceipt ? 'Review remaining quantity and the next confirmed delivery date.' : 'Review the delivery schedule with the buyer.',
      dueDate: item.applicableDueDate,
      isAcknowledged: item.isAcknowledged,
      acknowledgmentOverdue: item.acknowledgmentOverdue,
      detected,
      supportingRecords,
      missingEvidence,
      manualVerificationNeeded,
    };
  }).sort((left, right) => {
    const severity = { High: 0, Review: 1, Medium: 2, Low: 3 };
    return severity[left.severity as keyof typeof severity] - severity[right.severity as keyof typeof severity] ||
      String(left.dueDate || '9999-12-31').localeCompare(String(right.dueDate || '9999-12-31'));
  });
}

export async function getControlCenterData(forceDemo = false) {
  const settings = await getDeliverySettings();
  const effectiveMode = forceDemo ? 'demo' : settings.mode;
  const today = getLocalBusinessDate(settings.timezone);
  const runs = await getRunHistory();
  const latestRun = runs[0] || null;
  let orders: PurchaseOrder[] = [];
  let source: string;
  let isSynthetic: boolean;

  if (latestRun?.status === 'SUCCEEDED' && latestRun.source === 'art' && latestRun.result && typeof latestRun.result === 'object') {
    const rawOrders = (latestRun.result as { purchaseOrders?: unknown }).purchaseOrders;
    if (Array.isArray(rawOrders) && rawOrders.length > 0) {
      orders = rawOrders as PurchaseOrder[];
      source = 'Live ERPNext (via validated ART Agent execution)';
      isSynthetic = false;
    } else {
      orders = demoOrders(today);
      source = 'Synthetic Demo Baseline (Live ART run returned empty order set)';
      isSynthetic = true;
    }
  } else if (effectiveMode === 'demo') {
    orders = demoOrders(today);
    source = 'ERPNext Demo Environment (Synthetic Fixtures)';
    isSynthetic = true;
  } else {
    // Configured mode without a validated live run
    orders = demoOrders(today);
    source = latestRun?.status === 'FAILED'
      ? 'Synthetic Baseline (Live ART run failed; showing local fallback)'
      : 'Synthetic Baseline (No live ART run executed)';
    isSynthetic = true;
  }

  const assessments = classifyPurchaseOrders(orders, { ...settings, mode: effectiveMode }, today);
  const integrations = await getIntegrationStatus();
  const stagedChasers = await listStagedChasers();
  const supplierPromises = await listSupplierPromises();

  return {
    generatedAt: new Date().toISOString(),
    monitoringDate: today,
    source,
    isSynthetic,
    settings: { ...settings, mode: effectiveMode },
    integrations: { ...integrations, mode: effectiveMode },
    metrics: summarize(orders, assessments),
    purchaseOrders: orders.filter((order) => order.docstatus === 1 && order.status !== 'Closed').map((order) => ({
      ...order,
      assessments: assessments.filter((item) => item.orderId === order.id),
    })),
    assessments: assessments.filter((item) => !item.excluded),
    exceptions: buildExceptions(assessments),
    stagedChasers,
    supplierPromises,
    latestRun: latestRun ? publicRunRecord(latestRun) : null,
    runs: runs.map(({ result: _result, ...run }) => publicRunRecord({ ...run, result: null })),
    auditEvents: settings.mode === 'configured' ? await listAuditEvents() : [],
    workflowStages: [
      { id: 'ack', name: 'PO acknowledgment monitoring', state: 'IMPLEMENTED', detail: 'WF-P02-001: 48h acknowledgment SLA tracking active; overdue orders surfaced in exception queue.' },
      { id: 'chaser', name: 'Staged supplier follow-up', state: 'IMPLEMENTED', detail: 'WF-P02-002: Context-aware supplier chaser staging with strict auto_send: false and human approval.' },
      { id: 'reconcile', name: 'Promise and quantity reconciliation', state: 'IMPLEMENTED', detail: 'WF-P02-003: Deterministic line-item reconciliation, baseline date preservation, and promise tracking.' },
      { id: 'buffer', name: 'Buffer and downstream impact', state: 'SPECIFIED', detail: 'WF-P02-004: Stock on-hand and production schedule evidence is specified; awaiting ERPNext inventory connector scope.' },
      { id: 'escalate', name: 'Tiered escalation preparation', state: 'SPECIFIED', detail: 'WF-P02-005: Multi-tier escalation guidance active; consequential actions require human buyer approval.' },
      { id: 'asn', name: 'ASN intake and dock pre-receipt', state: 'SPECIFIED', detail: 'WF-P02-006: Inbound ASN parsing and draft receipt preparation specified; dock submission guarded.' },
    ],
  };
}



