import 'server-only';
import { classifyPurchaseOrders } from './classifier';
import { getDeliverySettings, getIntegrationStatus, getLocalBusinessDate } from './config';
import { listAuditEvents } from './store';
import { getRunHistory } from './runService';
import type { PurchaseOrder } from './types';

function shiftDate(date: string, days: number) {
  const value = new Date(`${date}T00:00:00Z`);
  value.setUTCDate(value.getUTCDate() + days);
  return value.toISOString().slice(0, 10);
}

function demoOrders(today: string): PurchaseOrder[] {
  const createOrder = (id: string, itemId: string, scheduleOffset: number, receivedQty: number, receiptEvidenceComplete = true, expectedOffset: number | null = null): PurchaseOrder => {
    const receipts = receivedQty > 0 ? [{
      receiptId: `${id}-PR-01`, receiptItemId: `${id}-PRI-01`, purchaseOrderId: id,
      purchaseOrderItemId: itemId, quantity: receivedQty, docstatus: 1,
    }] : [];
    return {
      id,
      supplier: `Synthetic Supplier ${id.slice(-2)}`,
      transactionDate: shiftDate(today, -14),
      docstatus: 1,
      status: receivedQty === 100 ? 'Completed' : 'To Receive and Bill',
      items: [{
        id: itemId,
        itemCode: `SYN-ITEM-${id.slice(-2)}`,
        description: 'Synthetic demonstration component',
        orderedQuantity: 100,
        scheduleDate: id.endsWith('06') ? null : shiftDate(today, scheduleOffset),
        expectedDeliveryDate: expectedOffset === null ? null : shiftDate(today, expectedOffset),
        receiptEvidenceComplete,
        receipts,
      }],
    };
  };

  return [
    createOrder('SYN-PO-2601', 'SYN-PO-2601-ITEM-01', -2, 0, true, 1),
    createOrder('SYN-PO-2602', 'SYN-PO-2602-ITEM-01', 0, 0),
    createOrder('SYN-PO-2603', 'SYN-PO-2603-ITEM-01', 3, 40),
    createOrder('SYN-PO-2604', 'SYN-PO-2604-ITEM-01', 12, 0),
    createOrder('SYN-PO-2605', 'SYN-PO-2605-ITEM-01', -10, 100),
    createOrder('SYN-PO-2606', 'SYN-PO-2606-ITEM-01', 4, 0, false),
    {
      id: 'SYN-PO-2607', supplier: 'Synthetic Supplier 07', transactionDate: shiftDate(today, -3), docstatus: 2, status: 'Cancelled',
      items: [{ id: 'SYN-PO-2607-ITEM-01', itemCode: 'SYN-ITEM-07', description: 'Cancelled demonstration commitment', orderedQuantity: 100,
        scheduleDate: shiftDate(today, -1), expectedDeliveryDate: null, receiptEvidenceComplete: true, receipts: [] }],
    },
  ];
}

function summarize(orders: PurchaseOrder[], assessments: ReturnType<typeof classifyPurchaseOrders>) {
  const activeOrders = orders.filter((order) => order.docstatus === 1);
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
    partialReceipts: new Set(active.filter((item) => item.partialReceipt).map((item) => item.orderId)).size,
    needsVerification: byOrder('NEEDS_VERIFICATION'),
  };
}

function buildExceptions(assessments: ReturnType<typeof classifyPurchaseOrders>) {
  return assessments.filter((item) => !item.excluded && (
    item.deliveryStatus === 'OVERDUE' || item.deliveryStatus === 'DUE_TODAY' ||
    item.deliveryStatus === 'NEEDS_VERIFICATION' || item.partialReceipt
  )).map((item) => ({
    id: `${item.orderId}:${item.orderItemId}`,
    orderId: item.orderId,
    supplier: item.supplier,
    itemCode: item.itemCode,
    status: item.deliveryStatus,
    severity: item.deliveryStatus === 'OVERDUE' ? 'High' : item.deliveryStatus === 'NEEDS_VERIFICATION' ? 'Review' : item.partialReceipt ? 'Medium' : 'Low',
    reason: item.verificationReasons[0] || (item.partialReceipt ? 'Submitted receipt evidence confirms only a partial quantity.' : item.deliveryStatus === 'OVERDUE' ? 'Verified open quantity remains after the applicable due date.' : `${item.deliveryStatus.replaceAll('_', ' ').toLowerCase()} delivery needs buyer attention.`),
    suggestedNextStep: item.deliveryStatus === 'NEEDS_VERIFICATION' ? 'Review ERPNext PO and receipt item references before classifying.' : item.deliveryStatus === 'OVERDUE' ? 'Review the supplier status and decide whether a staged follow-up is needed.' : item.partialReceipt ? 'Review remaining quantity and the next confirmed delivery date.' : 'Review the delivery schedule with the buyer.',
    dueDate: item.applicableDueDate,
  })).sort((left, right) => {
    const severity = { High: 0, Review: 1, Medium: 2, Low: 3 };
    return severity[left.severity as keyof typeof severity] - severity[right.severity as keyof typeof severity] ||
      String(left.dueDate || '9999-12-31').localeCompare(String(right.dueDate || '9999-12-31'));
  });
}

export async function getControlCenterData() {
  const settings = await getDeliverySettings();
  const today = getLocalBusinessDate(settings.timezone);
  const runs = settings.mode === 'configured' ? await getRunHistory() : [];
  const latestRun = runs[0] || null;
  let orders: PurchaseOrder[] = [];
  let source: 'synthetic demonstration data' | 'validated ART result' | 'no validated data' = 'no validated data';

  if (settings.mode === 'demo') {
    orders = demoOrders(today);
    source = 'synthetic demonstration data';
  } else if (latestRun?.status === 'SUCCEEDED' && latestRun.result && typeof latestRun.result === 'object') {
    const rawOrders = (latestRun.result as { purchaseOrders?: unknown }).purchaseOrders;
    if (Array.isArray(rawOrders)) orders = rawOrders as PurchaseOrder[];
    source = orders.length ? 'validated ART result' : 'no validated data';
  }

  const assessments = classifyPurchaseOrders(orders, settings, today);
  const integrations = await getIntegrationStatus();
  return {
    generatedAt: new Date().toISOString(),
    monitoringDate: today,
    source,
    settings,
    integrations,
    metrics: summarize(orders, assessments),
    purchaseOrders: orders.filter((order) => order.docstatus === 1).map((order) => ({
      ...order,
      assessments: assessments.filter((item) => item.orderId === order.id),
    })),
    assessments: assessments.filter((item) => !item.excluded),
    exceptions: buildExceptions(assessments),
    latestRun,
    runs: runs.map(({ result: _result, ...run }) => run),
    auditEvents: settings.mode === 'configured' ? await listAuditEvents() : [],
    workflowStages: [
      { id: 'ack', name: 'PO acknowledgment monitoring', state: 'SPECIFIED', detail: 'P02 workflow WF-P02-001; no verified scheduler or acknowledgment event source is configured.' },
      { id: 'chaser', name: 'Staged supplier follow-up', state: 'SPECIFIED', detail: 'Human approval and auto_send: false are required; supplier messaging is not implemented.' },
      { id: 'reconcile', name: 'Promise and quantity reconciliation', state: settings.mode === 'configured' && source === 'validated ART result' ? 'PARTIALLY VALIDATED' : 'SPECIFIED', detail: 'Read-only PO and receipt evidence is normalized; exact item links are required.' },
      { id: 'buffer', name: 'Buffer and downstream impact', state: 'SPECIFIED', detail: 'Stock, safety-stock, and work-order evidence is not part of the verified live report contract yet.' },
      { id: 'escalate', name: 'Tiered escalation preparation', state: 'SPECIFIED', detail: 'Exception guidance is review-only; no alternate sourcing or freight action is executed.' },
      { id: 'asn', name: 'ASN intake and dock pre-receipt', state: 'SPECIFIED', detail: 'No ASN ingestion or Purchase Receipt creation is implemented.' },
    ],
  };
}


