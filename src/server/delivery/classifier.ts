import type { DeliverySettings, ItemAssessment, PurchaseOrder } from './types';

function validDate(value: string | null | undefined): value is string {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(`${value}T00:00:00Z`);
  return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
}

function addDays(date: string, count: number) {
  const result = new Date(`${date}T00:00:00Z`);
  result.setUTCDate(result.getUTCDate() + count);
  return result.toISOString().slice(0, 10);
}

function assessItem(order: PurchaseOrder, item: PurchaseOrder['items'][number], settings: DeliverySettings, today: string): ItemAssessment {
  const reasons: string[] = [];
  const ordered = item.orderedQuantity;

  const normalizedStatus = (order.status || '').trim().toLowerCase();
  const isClosed = normalizedStatus === 'closed';
  const isCompleted = normalizedStatus === 'completed' || normalizedStatus === 'delivered';
  const isClosedOrCompleted = isClosed || isCompleted;

  let excluded = order.docstatus !== 1;
  let exclusionReason: string | null = null;
  if (order.docstatus === 2) {
    exclusionReason = 'Purchase order is cancelled and excluded.';
    reasons.push(exclusionReason);
  } else if (order.docstatus === 0) {
    exclusionReason = 'Purchase order is not submitted and excluded.';
    reasons.push(exclusionReason);
  } else if (order.docstatus !== 1) {
    exclusionReason = `Purchase order has invalid document status (${order.docstatus}) and is excluded.`;
    reasons.push(exclusionReason);
  } else if (isClosed) {
    excluded = true;
    exclusionReason = 'Purchase order status is Closed and excluded from open delivery obligations.';
    reasons.push(exclusionReason);
  }

  if (!order.id || !order.id.trim() || !order.supplier.trim()) reasons.push('Purchase order identifier or supplier is missing.');
  if (!item.id || !item.id.trim()) reasons.push('Purchase order item identifier is missing.');
  if (!item.itemCode || !item.itemCode.trim()) reasons.push('Purchase order item code is missing.');
  if (ordered === null || !Number.isFinite(ordered) || ordered < 0) reasons.push('Ordered quantity is missing or invalid.');

  // Acknowledgment 48h SLA Tracking
  const hasConfNo = Boolean(order.orderConfirmationNo && order.orderConfirmationNo.trim());
  const hasConfDate = validDate(order.orderConfirmationDate);
  const isAcknowledged = hasConfNo || hasConfDate;
  let acknowledgmentOverdue = false;
  let acknowledgmentDueHours: number | null = null;
  if (!isAcknowledged && validDate(order.transactionDate)) {
    const txMs = new Date(`${order.transactionDate}T00:00:00Z`).getTime();
    const todayMs = new Date(`${today}T00:00:00Z`).getTime();
    const elapsedHours = Math.round((todayMs - txMs) / (1000 * 60 * 60));
    acknowledgmentDueHours = elapsedHours;
    if (elapsedHours > 48) {
      acknowledgmentOverdue = true;
    }
  }

  const seenReceiptItems = new Set<string>();
  const validReceipts = item.receipts.filter((receipt) => {
    if (receipt.receiptItemId && seenReceiptItems.has(receipt.receiptItemId)) {
      reasons.push('A receipt item appears more than once in the evidence set.');
      return false;
    }
    if (receipt.receiptItemId) seenReceiptItems.add(receipt.receiptItemId);
    const valid = receipt.docstatus === 1 && receipt.purchaseOrderId === order.id &&
      receipt.purchaseOrderItemId === item.id && Number.isFinite(receipt.quantity) &&
      Boolean(receipt.receiptId && receipt.receiptItemId);
    if (receipt.docstatus === 2 || receipt.docstatus === 0) return false;
    if (receipt.docstatus !== 1) {
      reasons.push('Receipt evidence has an invalid document status.');
      return false;
    }
    if (receipt.itemCode && item.itemCode && receipt.itemCode.trim() !== item.itemCode.trim()) {
      reasons.push('Receipt item code does not match purchase order item code.');
      return false;
    }
    if (!valid) reasons.push('A submitted receipt lacks exact purchase-order item linkage or valid quantity.');
    return valid;
  });
  const retrieval = item.receiptRetrieval;
  const retrievalScopeMatches = retrieval?.scope?.purchaseOrderId === order.id &&
    retrieval.scope.purchaseOrderItemId === item.id;
  const paginationComplete = Number.isInteger(retrieval?.pagesRetrieved) &&
    (retrieval?.pagesRetrieved || 0) > 0 && retrieval?.hasMore === false;
  if (!retrieval || retrieval.complete !== true || !retrievalScopeMatches || !paginationComplete) {
    reasons.push('Complete, exactly scoped receipt retrieval with exhausted pagination is not evidenced.');
  }

  const received = reasons.length === 0 && ordered !== null
    ? validReceipts.reduce((sum, receipt) => sum + (receipt.isReturn ? -Math.abs(receipt.quantity) : receipt.quantity), 0)
    : null;
  const outstanding = received === null || ordered === null ? null : ordered - received;
  if (outstanding !== null && (outstanding < 0 || received! < 0)) reasons.push('Receipt quantity exceeds ordered quantity or is contradictory.');
  if (item.dateConflict) reasons.push('Supplier delivery dates conflict across available source evidence.');

  const baselineDate = validDate(item.scheduleDate) ? item.scheduleDate : null;
  const promisedDate = validDate(item.expectedDeliveryDate) ? item.expectedDeliveryDate : null;
  const dueDate = settings.dueDateBasis === 'contractual' ? baselineDate : promisedDate;
  if (outstanding !== null && outstanding > 0 && settings.dueDateBasis === 'contractual' && !baselineDate) reasons.push('Contractual item schedule date is missing or invalid.');
  if (outstanding !== null && outstanding > 0 && settings.dueDateBasis === 'supplier_promise' && !promisedDate) reasons.push('Supplier promised date is missing or invalid.');

  let status: ItemAssessment['deliveryStatus'] = 'NEEDS_VERIFICATION';
  if (reasons.length === 0 && outstanding !== null && outstanding >= 0 && outstanding === 0) {
    status = 'RECEIVED';
  } else if (reasons.length === 0 && outstanding !== null && outstanding > 0 && dueDate) {
    if (dueDate < today) status = 'OVERDUE';
    else if (dueDate === today) status = 'DUE_TODAY';
    else if (dueDate <= addDays(today, settings.upcomingDays)) status = 'UPCOMING';
    else status = 'FUTURE_OPEN_DELIVERY';
  }

  // Buffer and runway risk analysis
  const bufferRisk: ItemAssessment['bufferRisk'] = 'UNAVAILABLE';
  const bufferMarginDays: number | null = null;
  const bufferDetails = 'Stock on-hand and production work-order demand evidence are not present in current query scope.';

  return {
    orderId: order.id,
    orderItemId: item.id,
    supplier: order.supplier,
    itemCode: item.itemCode,
    description: item.description,
    orderedQuantity: ordered,
    receivedQuantity: received,
    outstandingQuantity: outstanding,
    baselineDate,
    promisedDate,
    applicableDueDate: dueDate,
    deliveryStatus: status,
    partialReceipt: received !== null && received > 0 && outstanding !== null && outstanding > 0,
    excluded,
    exclusionReason,
    isAcknowledged,
    acknowledgmentOverdue,
    acknowledgmentDueHours,
    orderStatus: order.status,
    isClosedOrCompleted,
    bufferRisk,
    bufferMarginDays,
    bufferDetails,
    verificationReasons: [...new Set(reasons)],
    receiptEvidence: validReceipts,
  };
}

export function classifyPurchaseOrders(orders: PurchaseOrder[], settings: DeliverySettings, today: string): ItemAssessment[] {
  if (!validDate(today)) throw new Error('Monitoring date must be an ISO local business date.');
  return orders.flatMap((order) => order.items.map((item) => assessItem(order, item, settings, today)));
}
