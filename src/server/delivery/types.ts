export type DeliveryStatus =
  | 'RECEIVED'
  | 'PARTIALLY_RECEIVED'
  | 'OVERDUE'
  | 'DUE_TODAY'
  | 'UPCOMING'
  | 'FUTURE_OPEN_DELIVERY'
  | 'NEEDS_VERIFICATION';

export type DueDateBasis = 'contractual' | 'supplier_promise';

export type ReceiptEvidence = {
  receiptId: string;
  receiptItemId: string;
  purchaseOrderId: string;
  purchaseOrderItemId: string;
  itemCode?: string;
  quantity: number;
  docstatus: number;
  isReturn?: boolean;
};

export type ReceiptRetrievalEvidence = {
  scope: {
    purchaseOrderId: string;
    purchaseOrderItemId: string;
  };
  complete: boolean;
  pagesRetrieved: number | null;
  hasMore: boolean | null;
  sourceToolId?: string | null;
  sourceResponseId?: string | null;
};

export type PurchaseOrderItem = {
  id: string;
  itemCode: string;
  description?: string;
  orderedQuantity: number | null;
  scheduleDate: string | null;
  expectedDeliveryDate: string | null;
  receiptRetrieval: ReceiptRetrievalEvidence | null;
  dateConflict?: boolean;
  receipts: ReceiptEvidence[];
};

export type PurchaseOrder = {
  id: string;
  supplier: string;
  transactionDate: string | null;
  docstatus: number;
  status: string;
  items: PurchaseOrderItem[];
};

export type ItemAssessment = {
  orderId: string;
  orderItemId: string;
  supplier: string;
  itemCode: string;
  description?: string;
  orderedQuantity: number | null;
  receivedQuantity: number | null;
  outstandingQuantity: number | null;
  baselineDate: string | null;
  promisedDate: string | null;
  applicableDueDate: string | null;
  deliveryStatus: DeliveryStatus;
  partialReceipt: boolean;
  excluded: boolean;
  verificationReasons: string[];
  receiptEvidence: ReceiptEvidence[];
};

export type DeliverySettings = {
  upcomingDays: number;
  dueDateBasis: DueDateBasis;
  timezone: string;
  mode: 'demo' | 'configured';
};

export type RunRecord = {
  id: string;
  idempotencyKey: string;
  status: 'QUEUED' | 'RUNNING' | 'SUCCEEDED' | 'FAILED';
  startedAt: string;
  finishedAt: string | null;
  source: 'art';
  result: unknown | null;
  error: string | null;
};

export function publicRunRecord(run: RunRecord): RunRecord {
  return {
    ...run,
    error: run.status === 'FAILED' ? 'Run failed. Check server-side logs for details.' : null,
  };
}
