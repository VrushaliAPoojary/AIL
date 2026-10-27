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
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  const candidate = value as Record<string, unknown>;
  if (Array.isArray(candidate.purchaseOrders)) return candidate;
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
  if (!payload || !Array.isArray(payload.purchaseOrders)) throw new Error('ART agent completed, but its result did not match the required P02 purchase-order evidence contract.');
  if (Buffer.byteLength(JSON.stringify(payload)) > 2_000_000) throw new Error('ART agent response exceeded the 2 MB report limit.');
  const purchaseOrders = payload.purchaseOrders.map((rawOrder: any): PurchaseOrder => {
    if (!rawOrder || typeof rawOrder !== 'object' || Array.isArray(rawOrder)) throw new Error('ART returned a malformed purchase order.');
    if (typeof rawOrder.id !== 'string' || typeof rawOrder.supplier !== 'string' || !Array.isArray(rawOrder.items)) throw new Error('ART purchase order is missing its source id, supplier, or items array.');
    const items = rawOrder.items.map((rawItem: any) => {
      if (!rawItem || typeof rawItem !== 'object' || Array.isArray(rawItem)) throw new Error('ART returned a malformed purchase-order item.');
      if (!Array.isArray(rawItem.receipts)) throw new Error('ART item result is missing its receipt rows.');
      return {
        id: typeof rawItem.id === 'string' ? rawItem.id : '',
        itemCode: typeof rawItem.itemCode === 'string' ? rawItem.itemCode : '',
        description: typeof rawItem.description === 'string' ? rawItem.description : undefined,
        orderedQuantity: typeof rawItem.orderedQuantity === 'number' && Number.isFinite(rawItem.orderedQuantity) ? rawItem.orderedQuantity : null,
        scheduleDate: typeof rawItem.scheduleDate === 'string' ? rawItem.scheduleDate : null,
        expectedDeliveryDate: typeof rawItem.expectedDeliveryDate === 'string' ? rawItem.expectedDeliveryDate : null,
        receiptRetrieval: normalizeReceiptRetrieval(rawItem.receiptRetrieval, rawOrder.id, rawItem.id),
        dateConflict: rawItem.dateConflict === true,
        receipts: rawItem.receipts.map((receipt: any) => ({
          receiptId: typeof receipt?.receiptId === 'string' ? receipt.receiptId : '',
          receiptItemId: typeof receipt?.receiptItemId === 'string' ? receipt.receiptItemId : '',
          purchaseOrderId: typeof receipt?.purchaseOrderId === 'string' ? receipt.purchaseOrderId : '',
          purchaseOrderItemId: typeof receipt?.purchaseOrderItemId === 'string' ? receipt.purchaseOrderItemId : '',
          itemCode: typeof receipt?.itemCode === 'string' ? receipt.itemCode : undefined,
          quantity: typeof receipt?.quantity === 'number' && Number.isFinite(receipt.quantity) ? receipt.quantity : Number.NaN,
          docstatus: Number.isInteger(receipt?.docstatus) ? receipt.docstatus : -1,
          isReturn: receipt?.isReturn === true,
        })),
      };
    });
    return {
      id: rawOrder.id,
      supplier: rawOrder.supplier,
      transactionDate: typeof rawOrder.transactionDate === 'string' ? rawOrder.transactionDate : null,
      docstatus: Number.isInteger(rawOrder.docstatus) ? rawOrder.docstatus : -1,
      status: typeof rawOrder.status === 'string' ? rawOrder.status : 'Unknown',
      orderConfirmationNo: typeof rawOrder.orderConfirmationNo === 'string' ? rawOrder.orderConfirmationNo : null,
      orderConfirmationDate: typeof rawOrder.orderConfirmationDate === 'string' ? rawOrder.orderConfirmationDate : null,
      items,
    };
  });
  return { purchaseOrders };
}
