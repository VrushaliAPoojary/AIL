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
  uom?: string | null;
  warehouse?: string | null;
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
  receivedQuantity?: number | null;
  pendingQuantity?: number | null;
  scheduleDate: string | null;
  expectedDeliveryDate: string | null;
  uom?: string | null;
  warehouse?: string | null;
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
  orderConfirmationNo?: string | null;
  orderConfirmationDate?: string | null;
  items: PurchaseOrderItem[];
};

export type ItemAssessment = {
  orderId: string;
  orderItemId: string;
  supplier: string;
  itemCode: string;
  description?: string;
  uom?: string | null;
  warehouse?: string | null;
  orderedQuantity: number | null;
  receivedQuantity: number | null;
  outstandingQuantity: number | null;
  baselineDate: string | null;
  promisedDate: string | null;
  applicableDueDate: string | null;
  deliveryStatus: DeliveryStatus;
  partialReceipt: boolean;
  excluded: boolean;
  exclusionReason?: string | null;
  isAcknowledged: boolean;
  acknowledgmentOverdue: boolean;
  acknowledgmentDueHours?: number | null;
  orderStatus: string;
  isClosedOrCompleted: boolean;
  bufferRisk: 'TIER_1_ROUTINE' | 'TIER_2_EXPEDITE' | 'TIER_3_CRITICAL' | 'UNAVAILABLE';
  bufferMarginDays: number | null;
  bufferDetails?: string;
  verificationReasons: string[];
  receiptEvidence: ReceiptEvidence[];
};

export type StagedChaserDraft = {
  id: string;
  orderId: string;
  orderItemId: string;
  supplier: string;
  itemCode: string;
  recipientEmail?: string | null;
  subject: string;
  body: string;
  urgency: 'Routine' | 'Urgent' | 'Critical';
  autoSend: false;
  status: 'DRAFT' | 'APPROVED' | 'DISMISSED';
  createdAt: string;
  approvedAt: string | null;
  approvedBy: string | null;
};

export type SupplierPromise = {
  id: string;
  orderId: string;
  orderItemId: string;
  originalRequestedDate: string | null;
  promisedDate: string;
  promisedQuantity?: number | null;
  state: 'PROPOSED' | 'AWAITING_APPROVAL' | 'CONFIRMED' | 'REJECTED';
  sourceReference: string;
  recordedAt: string;
  recordedBy: string;
  notes?: string;
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
  source: 'art' | 'demo';
  result: unknown | null;
  error: string | null;
};

export function publicRunRecord(run: RunRecord): RunRecord {
  return {
    ...run,
    error: run.status === 'FAILED' ? 'Run failed. Check server-side logs for details.' : null,
  };
}

