import type { PurchaseOrder } from './types';

function normalizeReceiptRetrieval(value: unknown, purchaseOrderId: string, purchaseOrderItemId: string) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  const evidence = value as Record<string, any>;
  const scope = evidence.scope;
  if (!scope || typeof scope !== 'object' || Array.isArray(scope) || typeof evidence.complete !== 'boolean') return null;
  const pagesRetrieved = evidence.pagesRetrieved === null ? null : evidence.pagesRetrieved;
  const hasMore = evidence.hasMore === null ? null : evidence.hasMore;
  if (pagesRetrieved !== null && (!Number.isInteger(pagesRetrieved) || pagesRetrieved < 0)) return null;
  if (hasMore !== null && typeof hasMore !== 'boolean') return null;
  const optionalId = (id: unknown) => id === null || id === undefined || typeof id === 'string' ? id ?? null : undefined;
  const sourceToolId = optionalId(evidence.sourceToolId);
  const sourceResponseId = optionalId(evidence.sourceResponseId);
  if (sourceToolId === undefined || sourceResponseId === undefined) return null;
  return {
    scope: {
      purchaseOrderId: typeof scope.purchaseOrderId === 'string' ? scope.purchaseOrderId : '',
      purchaseOrderItemId: typeof scope.purchaseOrderItemId === 'string' ? scope.purchaseOrderItemId : '',
    },
    complete: evidence.complete,
    pagesRetrieved,
    hasMore,
    sourceToolId,
    sourceResponseId,
  };
}

function extractJsonString(str: string): string {
  const trimmed = str.trim();
  const fenceMatch = trimmed.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
  if (fenceMatch) return fenceMatch[1].trim();
  const firstBrace = trimmed.indexOf('{');
  const lastBrace = trimmed.lastIndexOf('}');
  if (firstBrace !== -1 && lastBrace !== -1 && lastBrace > firstBrace) {
    return trimmed.slice(firstBrace, lastBrace + 1);
  }
  return trimmed;
}

function extractReceiptEvidence(receipt: any, parentDoc?: any) {
  const receiptId = typeof receipt?.receiptId === 'string' && receipt.receiptId
    ? receipt.receiptId
    : (typeof receipt?.parent === 'string' && receipt.parent
      ? receipt.parent
      : (parentDoc && typeof parentDoc.name === 'string' && parentDoc.name
        ? parentDoc.name
        : (typeof receipt?.name === 'string' ? receipt.name : '')));

  const receiptItemId = typeof receipt?.receiptItemId === 'string' && receipt.receiptItemId
    ? receipt.receiptItemId
    : (typeof receipt?.name === 'string' && receipt.name ? receipt.name : '');

  const purchaseOrderId = typeof receipt?.purchaseOrderId === 'string' && receipt.purchaseOrderId
    ? receipt.purchaseOrderId
    : (typeof receipt?.purchase_order === 'string' && receipt.purchase_order ? receipt.purchase_order : '');

  const purchaseOrderItemId = typeof receipt?.purchaseOrderItemId === 'string' && receipt.purchaseOrderItemId
    ? receipt.purchaseOrderItemId
    : (typeof receipt?.purchase_order_item === 'string' && receipt.purchase_order_item
      ? receipt.purchase_order_item
      : (typeof receipt?.po_detail === 'string' && receipt.po_detail ? receipt.po_detail : ''));

  const itemCode = typeof receipt?.itemCode === 'string' && receipt.itemCode
    ? receipt.itemCode
    : (typeof receipt?.item_code === 'string' && receipt.item_code ? receipt.item_code : undefined);

  const rawQty = receipt?.quantity ?? receipt?.qty ?? receipt?.received_qty;
  const quantity = typeof rawQty === 'number' && Number.isFinite(rawQty) ? rawQty : Number.NaN;

  const docstatus = Number.isInteger(receipt?.docstatus)
    ? receipt.docstatus
    : (parentDoc && Number.isInteger(parentDoc.docstatus) ? parentDoc.docstatus : -1);

  const isReturn = receipt?.isReturn === true
    || receipt?.is_return === 1
    || receipt?.is_return === true
    || parentDoc?.isReturn === true
    || parentDoc?.is_return === 1
    || parentDoc?.is_return === true;

  const uom = typeof receipt?.uom === 'string' && receipt.uom
    ? receipt.uom
    : (typeof receipt?.stock_uom === 'string' && receipt.stock_uom ? receipt.stock_uom : null);

  const warehouse = typeof receipt?.warehouse === 'string' && receipt.warehouse
    ? receipt.warehouse
    : null;

  return {
    receiptId,
    receiptItemId,
    purchaseOrderId,
    purchaseOrderItemId,
    itemCode,
    quantity,
    docstatus,
    isReturn,
    uom,
    warehouse,
  };
}

function getReportPayload(value: unknown): Record<string, unknown> | null {
  if (typeof value === 'string') {
    try {
      return getReportPayload(JSON.parse(value));
    } catch {
      try {
        const cleaned = extractJsonString(value);
        return getReportPayload(JSON.parse(cleaned));
      } catch {
        return null;
      }
    }
  }
  if (!value || typeof value !== 'object') return null;
  if (Array.isArray(value)) {
    return { purchaseOrders: value };
  }
  const candidate = value as Record<string, unknown>;
  if (Array.isArray(candidate.purchaseOrders)) return candidate;
  // If candidate is a single PO document (e.g. from Get Purchase Order)
  if (Array.isArray(candidate.items) && (candidate.id || candidate.name)) {
    return { purchaseOrders: [candidate] };
  }
  // Check candidate.data (standard Frappe response envelope)
  if (candidate.data !== undefined && candidate.data !== null) {
    if (Array.isArray(candidate.data)) {
      return { purchaseOrders: candidate.data };
    }
    if (typeof candidate.data === 'object') {
      const dataObj = candidate.data as Record<string, unknown>;
      if (Array.isArray(dataObj.purchaseOrders)) return dataObj;
      if (Array.isArray(dataObj.items) && (dataObj.id || dataObj.name)) {
        return { purchaseOrders: [dataObj] };
      }
    }
  }
  // Check candidate.message (alternative Frappe RPC envelope)
  if (candidate.message !== undefined && candidate.message !== null) {
    if (Array.isArray(candidate.message)) {
      return { purchaseOrders: candidate.message };
    }
    if (typeof candidate.message === 'object') {
      const msgObj = candidate.message as Record<string, unknown>;
      if (Array.isArray(msgObj.purchaseOrders)) return msgObj;
      if (Array.isArray(msgObj.items) && (msgObj.id || msgObj.name)) {
        return { purchaseOrders: [msgObj] };
      }
    }
  }
  for (const key of ['report', 'output', 'text', 'content', 'result', 'data', 'response', 'message']) {
    if (candidate[key] !== undefined && candidate[key] !== null) {
      const nested = getReportPayload(candidate[key]);
      if (nested) return nested;
    }
  }
  return null;
}

export function normalizeAgentReport(value: unknown): { purchaseOrders: PurchaseOrder[] } {
  const payload = getReportPayload(value);
  if (!payload || !Array.isArray(payload.purchaseOrders)) {
    throw new Error('ART agent completed, but its result did not match the required P02 purchase-order evidence contract.');
  }
  if (Buffer.byteLength(JSON.stringify(payload)) > 2_000_000) {
    throw new Error('ART agent response exceeded the 2 MB report limit.');
  }

  // Extract top-level receipts if provided
  const globalReceipts: ReturnType<typeof extractReceiptEvidence>[] = [];
  const rawGlobalReceipts = Array.isArray(payload.purchaseReceipts)
    ? payload.purchaseReceipts
    : (Array.isArray(payload.receipts) ? payload.receipts : null);
  if (rawGlobalReceipts) {
    for (const item of rawGlobalReceipts) {
      if (item && typeof item === 'object') {
        if (Array.isArray(item.items)) {
          for (const child of item.items) {
            globalReceipts.push(extractReceiptEvidence(child, item));
          }
        } else {
          globalReceipts.push(extractReceiptEvidence(item));
        }
      }
    }
  }

  const purchaseOrders = payload.purchaseOrders.map((rawOrder: any): PurchaseOrder => {
    if (!rawOrder || typeof rawOrder !== 'object' || Array.isArray(rawOrder)) {
      throw new Error('ART returned a malformed purchase order.');
    }
    const id = typeof rawOrder.id === 'string' && rawOrder.id
      ? rawOrder.id
      : (typeof rawOrder.name === 'string' && rawOrder.name ? rawOrder.name : '');
    const supplier = typeof rawOrder.supplier === 'string' ? rawOrder.supplier : '';
    if (!id || !supplier || !Array.isArray(rawOrder.items)) {
      throw new Error('ART purchase order is missing its source id, supplier, or items array.');
    }

    const items = rawOrder.items.map((rawItem: any) => {
      if (!rawItem || typeof rawItem !== 'object' || Array.isArray(rawItem)) {
        throw new Error('ART returned a malformed purchase-order item.');
      }
      const itemId = typeof rawItem.id === 'string' && rawItem.id
        ? rawItem.id
        : (typeof rawItem.name === 'string' && rawItem.name ? rawItem.name : '');

      const itemCode = typeof rawItem.itemCode === 'string' && rawItem.itemCode
        ? rawItem.itemCode
        : (typeof rawItem.item_code === 'string' && rawItem.item_code ? rawItem.item_code : '');

      const description = typeof rawItem.description === 'string'
        ? rawItem.description
        : (typeof rawItem.item_name === 'string' ? rawItem.item_name : undefined);

      const rawOrdQty = rawItem.orderedQuantity ?? rawItem.qty ?? rawItem.ordered_quantity;
      const orderedQuantity = typeof rawOrdQty === 'number' && Number.isFinite(rawOrdQty) ? rawOrdQty : null;

      const rawRecQty = rawItem.receivedQuantity ?? rawItem.received_qty;
      const receivedQuantity = typeof rawRecQty === 'number' && Number.isFinite(rawRecQty) ? rawRecQty : null;

      const rawPendQty = rawItem.pendingQuantity ?? rawItem.pending_qty;
      const pendingQuantity = typeof rawPendQty === 'number' && Number.isFinite(rawPendQty)
        ? rawPendQty
        : (orderedQuantity !== null && receivedQuantity !== null ? Math.max(0, orderedQuantity - receivedQuantity) : null);

      const scheduleDate = typeof rawItem.scheduleDate === 'string' && rawItem.scheduleDate
        ? rawItem.scheduleDate
        : (typeof rawItem.schedule_date === 'string' && rawItem.schedule_date ? rawItem.schedule_date : null);

      const expectedDeliveryDate = typeof rawItem.expectedDeliveryDate === 'string' && rawItem.expectedDeliveryDate
        ? rawItem.expectedDeliveryDate
        : (typeof rawItem.expected_delivery_date === 'string' && rawItem.expected_delivery_date ? rawItem.expected_delivery_date : null);

      const uom = typeof rawItem.uom === 'string' && rawItem.uom
        ? rawItem.uom
        : (typeof rawItem.stock_uom === 'string' && rawItem.stock_uom ? rawItem.stock_uom : null);

      const warehouse = typeof rawItem.warehouse === 'string' && rawItem.warehouse
        ? rawItem.warehouse
        : null;

      // Receipts mapping: prioritize item-level receipts, then match from top-level receipts
      let receipts: ReturnType<typeof extractReceiptEvidence>[];
      if (Array.isArray(rawItem.receipts)) {
        receipts = rawItem.receipts.map((r: any) => extractReceiptEvidence(r));
      } else if (globalReceipts.length > 0) {
        receipts = globalReceipts.filter((r) => r.purchaseOrderId === id && r.purchaseOrderItemId === itemId);
      } else {
        receipts = [];
      }

      return {
        id: itemId,
        itemCode,
        description,
        orderedQuantity,
        receivedQuantity,
        pendingQuantity,
        scheduleDate,
        expectedDeliveryDate,
        uom,
        warehouse,
        receiptRetrieval: normalizeReceiptRetrieval(rawItem.receiptRetrieval, id, itemId),
        dateConflict: rawItem.dateConflict === true,
        receipts,
      };
    });

    return {
      id,
      supplier,
      transactionDate: typeof rawOrder.transactionDate === 'string'
        ? rawOrder.transactionDate
        : (typeof rawOrder.transaction_date === 'string' ? rawOrder.transaction_date : null),
      docstatus: Number.isInteger(rawOrder.docstatus) ? rawOrder.docstatus : -1,
      status: typeof rawOrder.status === 'string' ? rawOrder.status : 'Unknown',
      orderConfirmationNo: typeof rawOrder.orderConfirmationNo === 'string'
        ? rawOrder.orderConfirmationNo
        : (typeof rawOrder.order_confirmation_no === 'string' ? rawOrder.order_confirmation_no : null),
      orderConfirmationDate: typeof rawOrder.orderConfirmationDate === 'string'
        ? rawOrder.orderConfirmationDate
        : (typeof rawOrder.order_confirmation_date === 'string' ? rawOrder.order_confirmation_date : null),
      items,
    };
  });

  return { purchaseOrders };
}
