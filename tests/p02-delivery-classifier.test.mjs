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
      receiptRetrieval: { scope: { purchaseOrderId: id, purchaseOrderItemId: itemId }, complete: true, pagesRetrieved: 1, hasMore: false },
      receipts: [], ...overrides.item }],
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

test('requires exact scope and exhausted pagination before claiming receipt quantities', () => {
  const cases = [
    { complete: false, pagesRetrieved: 1, hasMore: false },
    { complete: true, pagesRetrieved: null, hasMore: null },
    { complete: true, pagesRetrieved: 1, hasMore: true },
    { complete: true, pagesRetrieved: 1, hasMore: false, scope: { purchaseOrderId: 'OTHER', purchaseOrderItemId: 'PO-TEST-1-ITEM-1' } },
    null,
  ];
  for (const receiptRetrieval of cases) {
    const result = assess(order({ item: { receiptRetrieval, receipts: [] } }));
    assert.equal(result.deliveryStatus, 'NEEDS_VERIFICATION');
    assert.equal(result.receivedQuantity, null);
    assert.equal(result.outstandingQuantity, null);
  }
});

test('accepts only a completely scoped exhausted receipt retrieval', () => {
  const result = assess();
  assert.equal(result.receivedQuantity, 0);
  assert.equal(result.outstandingQuantity, 10);
  assert.equal(result.deliveryStatus, 'DUE_TODAY');
});

test('marks item retrieval scope mismatch for verification even with exact receipt rows', () => {
  const result = assess(order({ item: { receiptRetrieval: {
    scope: { purchaseOrderId: 'OTHER', purchaseOrderItemId: 'PO-TEST-1-ITEM-1' }, complete: true, pagesRetrieved: 1, hasMore: false,
  } } }));
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

test('classifies fully received delivery when verified receipts match ordered quantity', () => {
  const po = order({ item: {
    orderedQuantity: 10,
    receipts: [
      { receiptId: 'PR-FULL-1', receiptItemId: 'PRI-1', purchaseOrderId: 'PO-TEST-1', purchaseOrderItemId: 'PO-TEST-1-ITEM-1', itemCode: 'TEST-ITEM', quantity: 6, docstatus: 1 },
      { receiptId: 'PR-FULL-2', receiptItemId: 'PRI-2', purchaseOrderId: 'PO-TEST-1', purchaseOrderItemId: 'PO-TEST-1-ITEM-1', itemCode: 'TEST-ITEM', quantity: 4, docstatus: 1 },
    ],
  } });
  const result = assess(po);
  assert.equal(result.receivedQuantity, 10);
  assert.equal(result.outstandingQuantity, 0);
  assert.equal(result.partialReceipt, false);
  assert.equal(result.deliveryStatus, 'RECEIVED');
});

test('classifies partially received overdue delivery when quantity remains outstanding past due date', () => {
  const po = order({ item: {
    orderedQuantity: 10,
    scheduleDate: '2026-10-20',
    receipts: [
      { receiptId: 'PR-PARTIAL-1', receiptItemId: 'PRI-1', purchaseOrderId: 'PO-TEST-1', purchaseOrderItemId: 'PO-TEST-1-ITEM-1', itemCode: 'TEST-ITEM', quantity: 4, docstatus: 1 },
    ],
  } });
  const result = assess(po);
  assert.equal(result.receivedQuantity, 4);
  assert.equal(result.outstandingQuantity, 6);
  assert.equal(result.partialReceipt, true);
  assert.equal(result.deliveryStatus, 'OVERDUE');
});

test('requires exact purchase order ID and purchase order item ID for classification', () => {
  const missingItemId = assess(order({ item: { id: '' } }));
  assert.equal(missingItemId.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.match(missingItemId.verificationReasons.join(' '), /item identifier is missing/i);

  const missingOrderId = assess(order({ order: { id: '' } }));
  assert.equal(missingOrderId.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.match(missingOrderId.verificationReasons.join(' '), /purchase order identifier or supplier is missing/i);
});

test('marks receipt item code mismatch for verification', () => {
  const po = order({ item: {
    itemCode: 'TEST-ITEM',
    receipts: [
      { receiptId: 'PR-MISMATCH', receiptItemId: 'PRI-1', purchaseOrderId: 'PO-TEST-1', purchaseOrderItemId: 'PO-TEST-1-ITEM-1', itemCode: 'OTHER-CODE', quantity: 5, docstatus: 1 },
    ],
  } });
  const result = assess(po);
  assert.equal(result.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.equal(result.receivedQuantity, null);
  assert.match(result.verificationReasons.join(' '), /does not match purchase order item code/i);
});

test('marks receipt linked to wrong purchase order item on same PO for verification', () => {
  const po = order({ item: {
    receipts: [
      { receiptId: 'PR-WRONG-ITEM', receiptItemId: 'PRI-WRONG', purchaseOrderId: 'PO-TEST-1', purchaseOrderItemId: 'PO-TEST-1-ITEM-DIFFERENT', quantity: 10, docstatus: 1 },
    ],
  } });
  const result = assess(po);
  assert.equal(result.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.equal(result.receivedQuantity, null);
  assert.match(result.verificationReasons.join(' '), /exact purchase-order item linkage/i);
});

test('marks receipt with missing receiptId or receiptItemId for verification', () => {
  const po = order({ item: {
    receipts: [
      { receiptId: '', receiptItemId: 'PRI-1', purchaseOrderId: 'PO-TEST-1', purchaseOrderItemId: 'PO-TEST-1-ITEM-1', quantity: 10, docstatus: 1 },
    ],
  } });
  const result = assess(po);
  assert.equal(result.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.equal(result.receivedQuantity, null);
  assert.match(result.verificationReasons.join(' '), /exact purchase-order item linkage/i);
});

test('marks unexhausted pagination (hasMore: true or pagesRetrieved: 0) for verification', () => {
  const poHasMore = order({ item: {
    receiptRetrieval: { scope: { purchaseOrderId: 'PO-TEST-1', purchaseOrderItemId: 'PO-TEST-1-ITEM-1' }, complete: true, pagesRetrieved: 1, hasMore: true },
    receipts: [{ receiptId: 'PR-1', receiptItemId: 'PRI-1', purchaseOrderId: 'PO-TEST-1', purchaseOrderItemId: 'PO-TEST-1-ITEM-1', quantity: 10, docstatus: 1 }],
  } });
  const resHasMore = assess(poHasMore);
  assert.equal(resHasMore.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.equal(resHasMore.receivedQuantity, null);

  const poZeroPages = order({ item: {
    receiptRetrieval: { scope: { purchaseOrderId: 'PO-TEST-1', purchaseOrderItemId: 'PO-TEST-1-ITEM-1' }, complete: true, pagesRetrieved: 0, hasMore: false },
    receipts: [],
  } });
  const resZeroPages = assess(poZeroPages);
  assert.equal(resZeroPages.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.equal(resZeroPages.receivedQuantity, null);
});

test('preserves NEEDS_VERIFICATION when dateConflict is true under supplier_promise mode', () => {
  const po = order({ item: {
    dateConflict: true,
    expectedDeliveryDate: '2026-10-30',
    scheduleDate: '2026-10-25',
  } });
  const result = assess(po, { ...settings, dueDateBasis: 'supplier_promise' });
  assert.equal(result.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.match(result.verificationReasons.join(' '), /dates conflict/i);
});

test('does not classify partial delivery as confirmed or received', () => {
  const po = order({ item: {
    orderedQuantity: 10,
    scheduleDate: '2026-10-28',
    receipts: [
      { receiptId: 'PR-PART-1', receiptItemId: 'PRI-1', purchaseOrderId: 'PO-TEST-1', purchaseOrderItemId: 'PO-TEST-1-ITEM-1', quantity: 7, docstatus: 1 },
    ],
  } });
  const result = assess(po);
  assert.notEqual(result.deliveryStatus, 'RECEIVED');
  assert.equal(result.partialReceipt, true);
  assert.equal(result.receivedQuantity, 7);
  assert.equal(result.outstandingQuantity, 3);
  assert.equal(result.deliveryStatus, 'UPCOMING');
});

test('excludes Closed purchase orders from active delivery obligations', () => {
  const po = order({
    order: { status: 'Closed' },
    item: { scheduleDate: '2026-10-20' }, // date in the past
  });
  const result = assess(po);
  assert.equal(result.excluded, true);
  assert.match(result.exclusionReason || '', /Closed/i);
});

test('correctly evaluates 48-hour supplier acknowledgment SLA', () => {
  // 1. Order confirmed with confirmation reference and date
  const poConfirmed = order({
    order: {
      transactionDate: '2026-10-20',
      orderConfirmationNo: 'ACK-999',
      orderConfirmationDate: '2026-10-21',
    },
  });
  const resConfirmed = assess(poConfirmed);
  assert.equal(resConfirmed.isAcknowledged, true);
  assert.equal(resConfirmed.acknowledgmentOverdue, false);

  // 2. Order unconfirmed, placed 5 days ago (> 48h)
  const poOverdue = order({
    order: {
      transactionDate: '2026-10-20',
      orderConfirmationNo: null,
      orderConfirmationDate: null,
    },
  });
  const resOverdue = assess(poOverdue, settings, '2026-10-25');
  assert.equal(resOverdue.isAcknowledged, false);
  assert.equal(resOverdue.acknowledgmentOverdue, true);
  assert.ok(resOverdue.acknowledgmentDueHours && resOverdue.acknowledgmentDueHours > 48);

  // 3. Order unconfirmed, placed today (< 48h)
  const poRecent = order({
    order: {
      transactionDate: '2026-10-25',
      orderConfirmationNo: null,
      orderConfirmationDate: null,
    },
  });
  const resRecent = assess(poRecent, settings, '2026-10-25');
  assert.equal(resRecent.isAcknowledged, false);
  assert.equal(resRecent.acknowledgmentOverdue, false);
});

test('provides transparent UNAVAILABLE fallback for inventory buffer risk without hallucinating scores', () => {
  const po = order();
  const result = assess(po);
  assert.equal(result.bufferRisk, 'UNAVAILABLE');
  assert.equal(result.bufferMarginDays, null);
  assert.match(result.bufferDetails || '', /not present in current query scope/i);
});

test('flags discrepancy between PO line received quantity and receipt evidence (Defect 6)', () => {
  // PO line claims 15 received, but receipt evidence only accounts for 10
  const po = order({
    item: {
      orderedQuantity: 20,
      receivedQuantity: 15, // Claimed on PO row
      receipts: [
        {
          receiptId: 'PR-1',
          receiptItemId: 'PRI-1',
          purchaseOrderId: 'PO-TEST-1',
          purchaseOrderItemId: 'PO-TEST-1-ITEM-1',
          quantity: 10,
          docstatus: 1,
        },
      ],
    },
  });

  const result = assess(po);
  assert.equal(result.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.equal(result.receivedQuantity, null);
  assert.equal(result.outstandingQuantity, null);
  assert.ok(result.verificationReasons.some((r) => r.includes('does not match verified receipt evidence')));
});

test('does not infer receipt match from supplier, item code, or total quantity alone (Defect 2 & 3)', () => {
  // Receipt has same supplier and item code, but purchaseOrderId or purchaseOrderItemId are missing/wrong
  const po = order({
    item: {
      orderedQuantity: 10,
      receipts: [
        {
          receiptId: 'PR-UNLINKED',
          receiptItemId: 'PRI-UNLINKED',
          purchaseOrderId: 'OTHER-PO-999', // Mismatched PO link
          purchaseOrderItemId: 'OTHER-ITEM-999',
          itemCode: 'TEST-ITEM', // Same item code!
          quantity: 10,
          docstatus: 1,
        },
      ],
    },
  });

  const result = assess(po);
  // Must NOT infer match, must mark NEEDS_VERIFICATION
  assert.equal(result.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.equal(result.receivedQuantity, null);
  assert.ok(result.verificationReasons.some((r) => r.includes('lacks exact purchase-order item linkage')));
});

test('preserves uom and warehouse on item assessment', () => {
  const po = order({
    item: {
      uom: 'Nos',
      warehouse: 'Stores - Main Plant',
    },
  });

  const result = assess(po);
  assert.equal(result.uom, 'Nos');
  assert.equal(result.warehouse, 'Stores - Main Plant');
});


