import assert from 'node:assert/strict';
import test from 'node:test';
import { classifyPurchaseOrders } from '../src/server/delivery/classifier.ts';

const settings = { upcomingDays: 7, dueDateBasis: 'contractual', timezone: 'Asia/Kolkata', mode: 'demo' };
const today = '2026-10-25';

function order(overrides = {}) {
  const id = 'PO-TEST-1';
  const itemId = 'PO-TEST-1-ITEM-1';
  return {
    id, supplier: 'Test supplier', transactionDate: '2026-10-01', docstatus: 1, status: 'To Receive and Bill',
    items: [{ id: itemId, itemCode: 'TEST-ITEM', orderedQuantity: 10, scheduleDate: '2026-10-25', expectedDeliveryDate: null,
      receiptEvidenceComplete: true, receipts: [], ...overrides.item }],
    ...overrides.order,
  };
}

function assess(po = order(), config = settings, date = today) {
  return classifyPurchaseOrders([po], config, date)[0];
}

test('classifies date boundaries as overdue, due today, upcoming, and future open', () => {
  assert.equal(assess(order({ item: { scheduleDate: '2026-10-24' } })).deliveryStatus, 'OVERDUE');
  assert.equal(assess(order({ item: { scheduleDate: today } })).deliveryStatus, 'DUE_TODAY');
  assert.equal(assess(order({ item: { scheduleDate: '2026-11-01' } })).deliveryStatus, 'UPCOMING');
  assert.equal(assess(order({ item: { scheduleDate: '2026-11-02' } })).deliveryStatus, 'FUTURE_OPEN_DELIVERY');
});

test('calculates received and outstanding quantities from multiple exact linked submitted receipt rows', () => {
  const po = order({ item: { receipts: [
    { receiptId: 'PR-1', receiptItemId: 'PRI-1', purchaseOrderId: 'PO-TEST-1', purchaseOrderItemId: 'PO-TEST-1-ITEM-1', quantity: 3, docstatus: 1 },
    { receiptId: 'PR-2', receiptItemId: 'PRI-2', purchaseOrderId: 'PO-TEST-1', purchaseOrderItemId: 'PO-TEST-1-ITEM-1', quantity: 2, docstatus: 1 },
  ] } });
  const result = assess(po);
  assert.equal(result.receivedQuantity, 5);
  assert.equal(result.outstandingQuantity, 5);
  assert.equal(result.partialReceipt, true);
});

test('ignores cancelled and draft receipts when receipt enumeration is complete', () => {
  const po = order({ item: { receipts: [
    { receiptId: 'PR-CANCELLED', receiptItemId: 'PRI-CANCELLED', purchaseOrderId: 'PO-TEST-1', purchaseOrderItemId: 'PO-TEST-1-ITEM-1', quantity: 10, docstatus: 2 },
    { receiptId: 'PR-DRAFT', receiptItemId: 'PRI-DRAFT', purchaseOrderId: 'PO-TEST-1', purchaseOrderItemId: 'PO-TEST-1-ITEM-1', quantity: 10, docstatus: 0 },
  ] } });
  const result = assess(po);
  assert.equal(result.receivedQuantity, 0);
  assert.equal(result.outstandingQuantity, 10);
});

test('requires complete receipt evidence before claiming open or fully received quantities', () => {
  const result = assess(order({ item: { receiptEvidenceComplete: false, receipts: [] } }));
  assert.equal(result.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.equal(result.receivedQuantity, null);
  assert.equal(result.outstandingQuantity, null);
});

test('requires exact PO and PO item linkage for submitted receipt evidence', () => {
  const po = order({ item: { receipts: [{ receiptId: 'PR-1', receiptItemId: 'PRI-1', purchaseOrderId: 'OTHER-PO', purchaseOrderItemId: 'OTHER-ITEM', quantity: 10, docstatus: 1 }] } });
  const result = assess(po);
  assert.equal(result.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.equal(result.receivedQuantity, null);
  assert.match(result.verificationReasons.join(' '), /exact purchase-order item linkage/);
});

test('does not double-count duplicate receipt item evidence', () => {
  const row = { receiptId: 'PR-1', receiptItemId: 'PRI-1', purchaseOrderId: 'PO-TEST-1', purchaseOrderItemId: 'PO-TEST-1-ITEM-1', quantity: 6, docstatus: 1 };
  const result = assess(order({ item: { receipts: [row, row] } }));
  assert.equal(result.receivedQuantity, null);
  assert.equal(result.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.match(result.verificationReasons.join(' '), /appears more than once/);
});

test('marks negative and over-received quantities for verification', () => {
  const po = order({ item: { receipts: [{ receiptId: 'PR-1', receiptItemId: 'PRI-1', purchaseOrderId: 'PO-TEST-1', purchaseOrderItemId: 'PO-TEST-1-ITEM-1', quantity: 12, docstatus: 1 }] } });
  const result = assess(po);
  assert.equal(result.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.match(result.verificationReasons.join(' '), /exceeds ordered quantity/);
});

test('uses returns as negative received quantity and flags contradictions', () => {
  const po = order({ item: { receipts: [{ receiptId: 'PR-RETURN', receiptItemId: 'PRI-RETURN', purchaseOrderId: 'PO-TEST-1', purchaseOrderItemId: 'PO-TEST-1-ITEM-1', quantity: 2, docstatus: 1, isReturn: true }] } });
  assert.equal(assess(po).deliveryStatus, 'NEEDS_VERIFICATION');
});

test('does not classify cancelled or draft purchase orders as active deliveries', () => {
  assert.equal(assess(order({ order: { docstatus: 2, status: 'Cancelled' } })).excluded, true);
  assert.equal(assess(order({ order: { docstatus: 0, status: 'Draft' } })).excluded, true);
});

test('reports conflicting supplier date evidence as needs verification', () => {
  const result = assess(order({ item: { dateConflict: true, expectedDeliveryDate: '2026-10-31' } }));
  assert.equal(result.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.match(result.verificationReasons.join(' '), /dates conflict/);
});

test('keeps contractual and promised dates separate and applies the configured basis', () => {
  const po = order({ item: { scheduleDate: '2026-10-24', expectedDeliveryDate: '2026-10-30' } });
  assert.equal(assess(po).deliveryStatus, 'OVERDUE');
  assert.equal(assess(po, { ...settings, dueDateBasis: 'supplier_promise' }).deliveryStatus, 'UPCOMING');
  assert.equal(assess(po).baselineDate, '2026-10-24');
  assert.equal(assess(po).promisedDate, '2026-10-30');
});

test('requires a date for open items and validates the monitoring business date', () => {
  assert.equal(assess(order({ item: { scheduleDate: null } })).deliveryStatus, 'NEEDS_VERIFICATION');
  assert.equal(assess(order({ item: { scheduleDate: '2026-02-30' } })).deliveryStatus, 'NEEDS_VERIFICATION');
  assert.throws(() => classifyPurchaseOrders([order()], settings, 'not-a-date'));
});
