import { randomUUID } from 'node:crypto';
import type { ItemAssessment, PurchaseOrder, StagedChaserDraft } from './types';

export function generateChaserDraft(
  order: PurchaseOrder,
  first: any,
  second?: any,
  third?: string
): StagedChaserDraft {
  const assessment: ItemAssessment = second && typeof second === 'object' && 'deliveryStatus' in second
    ? second
    : first;
  const noteStr = typeof third === 'string'
    ? third
    : (typeof second === 'string' ? second : '');

  const itemCode = assessment.itemCode || first?.itemCode || 'N/A';
  const orderItemId = assessment.orderItemId || first?.id || 'N/A';
  const orderedQty = assessment.orderedQuantity ?? first?.orderedQuantity ?? null;
  const baselineDate = assessment.baselineDate || first?.scheduleDate || null;

  const isAckOverdue = assessment.acknowledgmentOverdue || (!assessment.isAcknowledged && (assessment.acknowledgmentDueHours ?? 0) > 48);
  const isDelayOverdue = assessment.deliveryStatus === 'OVERDUE';
  const isDueToday = assessment.deliveryStatus === 'DUE_TODAY';

  let urgency: StagedChaserDraft['urgency'] = 'Routine';
  let subject = `DELIVERY STATUS: Purchase Order ${order.id} — ${itemCode}`;
  let specificQuestion = '';

  if (isAckOverdue) {
    urgency = 'Urgent';
    subject = `URGENT: Purchase Order Acknowledgment Overdue — ${order.id} (${order.supplier})`;
    specificQuestion = `We note that an order confirmation reference has not been received within the contractual 48-hour SLA following order issue on ${order.transactionDate || 'issuance'}. Please provide your formal order confirmation number and confirmed dispatch schedule.`;
  } else if (isDelayOverdue) {
    urgency = 'Critical';
    subject = `CRITICAL: Overdue Delivery Expedite Notice — ${order.id} (${order.supplier})`;
    specificQuestion = `The delivery for ${assessment.outstandingQuantity ?? 'the outstanding'} units of ${itemCode} was due on ${assessment.applicableDueDate || 'scheduled date'} and is now overdue. Production schedules require immediate status. Please provide the carrier Air Waybill (AWB) / consignment tracking code and confirmed dock arrival date.`;
  } else if (isDueToday) {
    urgency = 'Urgent';
    subject = `DOCK ADVICE: Delivery Due Today — ${order.id} (${itemCode})`;
    specificQuestion = `Our records indicate ${assessment.outstandingQuantity ?? 'the order'} is scheduled to arrive at our receiving dock today (${assessment.applicableDueDate}). Please confirm if the consignment has been dispatched and provide vehicle / delivery docket details.`;
  } else if (assessment.partialReceipt) {
    urgency = 'Urgent';
    subject = `PARTIAL RECEIPT RECONCILIATION: Balance Delivery Schedule — ${order.id}`;
    specificQuestion = `Our dock has verified receipt of ${assessment.receivedQuantity} units. An outstanding balance of ${assessment.outstandingQuantity} units remains open against ${itemCode}. Please confirm the target ship date for the balance.`;
  } else {
    subject = `DELIVERY SCHEDULE CHECK: Purchase Order ${order.id} — ${itemCode}`;
    specificQuestion = `Please confirm that the upcoming delivery of ${orderedQty ?? 'the scheduled'} units of ${itemCode} remains on track for arrival on ${assessment.applicableDueDate || 'scheduled date'}.`;
  }

  const bodyLines = [
    `Dear ${order.supplier} Order Desk,`,
    '',
    `Regarding Purchase Order: ${order.id}`,
    `Line Item Code: ${itemCode} ${assessment.description ? `(${assessment.description})` : ''}`,
    `PO Item Row Reference: ${orderItemId}`,
    '',
    `Commitment Breakdown:`,
    `- Ordered Quantity: ${orderedQty ?? 'N/A'} units`,
    `- Confirmed Received Quantity: ${assessment.receivedQuantity ?? 0} units`,
    `- Outstanding Open Quantity: ${assessment.outstandingQuantity ?? 'N/A'} units`,
    `- Original Requested Delivery Date (Baseline RDD): ${baselineDate || 'Not specified'}`,
    assessment.promisedDate ? `- Current Supplier Promised Date: ${assessment.promisedDate}` : null,
    `- Active Due Date: ${assessment.applicableDueDate || 'Pending confirmation'}`,
    '',
    `Action Requested:`,
    specificQuestion,
    noteStr?.trim() ? `\nBuyer Note: ${noteStr.trim()}` : null,
    '',
    'Please reply directly to this communication with your formal dispatch or revised commitment details.',
    '',
    'Regards,',
    'Purchasing & Inbound Materials Team',
    'Vanguard Precision Manufacturing',
  ].filter(Boolean);

  return {
    id: `CHASER-${order.id}-${randomUUID().slice(0, 8)}`,
    orderId: order.id,
    orderItemId,
    supplier: order.supplier,
    itemCode,
    recipientEmail: null,
    subject,
    body: bodyLines.join('\n'),
    urgency,
    autoSend: false,
    status: 'DRAFT',
    createdAt: new Date().toISOString(),
    approvedAt: null,
    approvedBy: null,
  };
}
