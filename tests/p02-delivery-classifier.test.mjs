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

// ============================================================================
// SYNTHETIC TEST FIXTURES: Isolated Classification Regression Test Suite
// Note: All fixtures below are deterministic synthetic records for unit testing.
// No live ERPNext tools, remote calls, or live database modifications are performed.
// ============================================================================

function createSyntheticPoFixture({
  id = 'SYNTHETIC-PO-001',
  supplier = 'Synthetic Components Corp',
  transactionDate = '2026-10-10',
  docstatus = 1,
  status = 'To Receive and Bill',
  itemId = 'SYNTHETIC-ITEM-001',
  itemCode = 'SYN-SKU-100',
  description = 'Synthetic Precision Component',
  orderedQuantity = 100,
  receivedQuantity = null,
  pendingQuantity = null,
  scheduleDate = '2026-10-25',
  expectedDeliveryDate = null,
  uom = 'Nos',
  warehouse = 'Stores - Synthetic Plant',
  receiptRetrieval,
  receipts = [],
  dateConflict = false,
  orderConfirmationNo = null,
  orderConfirmationDate = null,
} = {}) {
  const effectiveRetrieval = receiptRetrieval !== undefined
    ? receiptRetrieval
    : {
        scope: { purchaseOrderId: id, purchaseOrderItemId: itemId },
        complete: true,
        pagesRetrieved: 1,
        hasMore: false,
      };

  return {
    id,
    supplier,
    transactionDate,
    docstatus,
    status,
    orderConfirmationNo,
    orderConfirmationDate,
    items: [
      {
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
        receiptRetrieval: effectiveRetrieval,
        dateConflict,
        receipts,
      },
    ],
  };
}

test('Synthetic Fixture: scenario 1 — fully received item evaluates to RECEIVED', () => {
  const po = createSyntheticPoFixture({
    id: 'SYN-PO-REC-01',
    scheduleDate: '2026-10-20',
    orderedQuantity: 80,
    receipts: [
      { receiptId: 'SYN-PR-1', receiptItemId: 'SYN-PRI-1', purchaseOrderId: 'SYN-PO-REC-01', purchaseOrderItemId: 'SYNTHETIC-ITEM-001', itemCode: 'SYN-SKU-100', quantity: 50, docstatus: 1 },
      { receiptId: 'SYN-PR-2', receiptItemId: 'SYN-PRI-2', purchaseOrderId: 'SYN-PO-REC-01', purchaseOrderItemId: 'SYNTHETIC-ITEM-001', itemCode: 'SYN-SKU-100', quantity: 30, docstatus: 1 },
    ],
  });
  const res = assess(po);
  assert.equal(res.deliveryStatus, 'RECEIVED');
  assert.equal(res.receivedQuantity, 80);
  assert.equal(res.outstandingQuantity, 0);
  assert.equal(res.partialReceipt, false);
});

test('Synthetic Fixture: scenario 2 — overdue open delivery before monitoring date', () => {
  const po = createSyntheticPoFixture({
    scheduleDate: '2026-10-24', // yesterday relative to today 2026-10-25
    orderedQuantity: 50,
    receipts: [],
  });
  const res = assess(po);
  assert.equal(res.deliveryStatus, 'OVERDUE');
  assert.equal(res.receivedQuantity, 0);
  assert.equal(res.outstandingQuantity, 50);
  assert.equal(res.applicableDueDate, '2026-10-24');
  assert.equal(res.partialReceipt, false);
});

test('Synthetic Fixture: scenario 3 — due today on exact monitoring date', () => {
  const po = createSyntheticPoFixture({
    scheduleDate: '2026-10-25', // today
    orderedQuantity: 60,
    receipts: [],
  });
  const res = assess(po);
  assert.equal(res.deliveryStatus, 'DUE_TODAY');
  assert.equal(res.receivedQuantity, 0);
  assert.equal(res.outstandingQuantity, 60);
  assert.equal(res.applicableDueDate, '2026-10-25');
  assert.equal(res.partialReceipt, false);
});

test('Synthetic Fixture: scenario 4 — upcoming delivery within configured reminder window', () => {
  // Test start of upcoming window (tomorrow: 2026-10-26)
  const poTomorrow = createSyntheticPoFixture({
    scheduleDate: '2026-10-26',
    orderedQuantity: 40,
    receipts: [],
  });
  const resTomorrow = assess(poTomorrow);
  assert.equal(resTomorrow.deliveryStatus, 'UPCOMING');
  assert.equal(resTomorrow.outstandingQuantity, 40);

  // Test exact outer boundary of upcoming window (today + 7 = 2026-11-01)
  const poWindowEnd = createSyntheticPoFixture({
    scheduleDate: '2026-11-01',
    orderedQuantity: 40,
    receipts: [],
  });
  const resWindowEnd = assess(poWindowEnd);
  assert.equal(resWindowEnd.deliveryStatus, 'UPCOMING');
  assert.equal(resWindowEnd.outstandingQuantity, 40);
});

test('Synthetic Fixture: scenario 5 — future open delivery beyond reminder window', () => {
  // Boundary + 1 day (today + 8 = 2026-11-02)
  const poBoundaryPlusOne = createSyntheticPoFixture({
    scheduleDate: '2026-11-02',
    orderedQuantity: 100,
    receipts: [],
  });
  const resBoundary = assess(poBoundaryPlusOne);
  assert.equal(resBoundary.deliveryStatus, 'FUTURE_OPEN_DELIVERY');
  assert.equal(resBoundary.outstandingQuantity, 100);

  // Far future date
  const poFarFuture = createSyntheticPoFixture({
    scheduleDate: '2026-12-15',
    orderedQuantity: 100,
    receipts: [],
  });
  const resFar = assess(poFarFuture);
  assert.equal(resFar.deliveryStatus, 'FUTURE_OPEN_DELIVERY');
});

test('Synthetic Fixture: scenario 6 — partially received item across all primary date classifications', () => {
  // Partial Overdue
  const poPartialOverdue = createSyntheticPoFixture({
    id: 'SYN-PO-PART-OD',
    scheduleDate: '2026-10-20',
    orderedQuantity: 100,
    receipts: [
      { receiptId: 'PR-OD-1', receiptItemId: 'PRI-OD-1', purchaseOrderId: 'SYN-PO-PART-OD', purchaseOrderItemId: 'SYNTHETIC-ITEM-001', itemCode: 'SYN-SKU-100', quantity: 40, docstatus: 1 },
    ],
  });
  const resOD = assess(poPartialOverdue);
  assert.equal(resOD.deliveryStatus, 'OVERDUE');
  assert.equal(resOD.partialReceipt, true);
  assert.equal(resOD.receivedQuantity, 40);
  assert.equal(resOD.outstandingQuantity, 60);

  // Partial Due Today
  const poPartialToday = createSyntheticPoFixture({
    id: 'SYN-PO-PART-TODAY',
    scheduleDate: '2026-10-25',
    orderedQuantity: 100,
    receipts: [
      { receiptId: 'PR-TOD-1', receiptItemId: 'PRI-TOD-1', purchaseOrderId: 'SYN-PO-PART-TODAY', purchaseOrderItemId: 'SYNTHETIC-ITEM-001', itemCode: 'SYN-SKU-100', quantity: 30, docstatus: 1 },
    ],
  });
  const resToday = assess(poPartialToday);
  assert.equal(resToday.deliveryStatus, 'DUE_TODAY');
  assert.equal(resToday.partialReceipt, true);
  assert.equal(resToday.receivedQuantity, 30);
  assert.equal(resToday.outstandingQuantity, 70);

  // Partial Upcoming
  const poPartialUpcoming = createSyntheticPoFixture({
    id: 'SYN-PO-PART-UP',
    scheduleDate: '2026-10-29',
    orderedQuantity: 100,
    receipts: [
      { receiptId: 'PR-UP-1', receiptItemId: 'PRI-UP-1', purchaseOrderId: 'SYN-PO-PART-UP', purchaseOrderItemId: 'SYNTHETIC-ITEM-001', itemCode: 'SYN-SKU-100', quantity: 25, docstatus: 1 },
    ],
  });
  const resUp = assess(poPartialUpcoming);
  assert.equal(resUp.deliveryStatus, 'UPCOMING');
  assert.equal(resUp.partialReceipt, true);
  assert.equal(resUp.receivedQuantity, 25);
  assert.equal(resUp.outstandingQuantity, 75);

  // Partial Future Open
  const poPartialFuture = createSyntheticPoFixture({
    id: 'SYN-PO-PART-FUT',
    scheduleDate: '2026-11-20',
    orderedQuantity: 100,
    receipts: [
      { receiptId: 'PR-FUT-1', receiptItemId: 'PRI-FUT-1', purchaseOrderId: 'SYN-PO-PART-FUT', purchaseOrderItemId: 'SYNTHETIC-ITEM-001', itemCode: 'SYN-SKU-100', quantity: 50, docstatus: 1 },
    ],
  });
  const resFut = assess(poPartialFuture);
  assert.equal(resFut.deliveryStatus, 'FUTURE_OPEN_DELIVERY');
  assert.equal(resFut.partialReceipt, true);
  assert.equal(resFut.receivedQuantity, 50);
  assert.equal(resFut.outstandingQuantity, 50);
});

test('Synthetic Fixture: scenario 7 — missing scheduled date or invalid quantities evaluate to NEEDS_VERIFICATION', () => {
  // Null scheduleDate
  const nullDate = assess(createSyntheticPoFixture({ scheduleDate: null }));
  assert.equal(nullDate.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.ok(nullDate.verificationReasons.some((r) => r.includes('schedule date is missing')));

  // Empty string scheduleDate
  const emptyDate = assess(createSyntheticPoFixture({ scheduleDate: '' }));
  assert.equal(emptyDate.deliveryStatus, 'NEEDS_VERIFICATION');

  // Null orderedQuantity
  const nullQty = assess(createSyntheticPoFixture({ orderedQuantity: null }));
  assert.equal(nullQty.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.ok(nullQty.verificationReasons.some((r) => r.includes('Ordered quantity is missing or invalid')));

  // Negative orderedQuantity
  const negQty = assess(createSyntheticPoFixture({ orderedQuantity: -10 }));
  assert.equal(negQty.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.ok(negQty.verificationReasons.some((r) => r.includes('Ordered quantity is missing or invalid')));

  // NaN orderedQuantity
  const nanQty = assess(createSyntheticPoFixture({ orderedQuantity: Number.NaN }));
  assert.equal(nanQty.deliveryStatus, 'NEEDS_VERIFICATION');

  // Infinity orderedQuantity
  const infQty = assess(createSyntheticPoFixture({ orderedQuantity: Number.POSITIVE_INFINITY }));
  assert.equal(infQty.deliveryStatus, 'NEEDS_VERIFICATION');
});

test('Synthetic Fixture: scenario 8 — missing or incorrect receipt linkage evaluates to NEEDS_VERIFICATION', () => {
  // Wrong purchaseOrderId on receipt
  const wrongPo = assess(createSyntheticPoFixture({
    id: 'SYN-PO-CORRECT',
    receipts: [
      { receiptId: 'PR-1', receiptItemId: 'PRI-1', purchaseOrderId: 'SYN-PO-WRONG', purchaseOrderItemId: 'SYNTHETIC-ITEM-001', quantity: 10, docstatus: 1 },
    ],
  }));
  assert.equal(wrongPo.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.ok(wrongPo.verificationReasons.some((r) => r.includes('exact purchase-order item linkage')));

  // Wrong purchaseOrderItemId on receipt
  const wrongItem = assess(createSyntheticPoFixture({
    id: 'SYN-PO-CORRECT',
    itemId: 'SYNTHETIC-ITEM-001',
    receipts: [
      { receiptId: 'PR-1', receiptItemId: 'PRI-1', purchaseOrderId: 'SYN-PO-CORRECT', purchaseOrderItemId: 'SYNTHETIC-ITEM-WRONG', quantity: 10, docstatus: 1 },
    ],
  }));
  assert.equal(wrongItem.deliveryStatus, 'NEEDS_VERIFICATION');

  // Missing receiptId on receipt row
  const missingReceiptId = assess(createSyntheticPoFixture({
    id: 'SYN-PO-CORRECT',
    receipts: [
      { receiptId: '', receiptItemId: 'PRI-1', purchaseOrderId: 'SYN-PO-CORRECT', purchaseOrderItemId: 'SYNTHETIC-ITEM-001', quantity: 10, docstatus: 1 },
    ],
  }));
  assert.equal(missingReceiptId.deliveryStatus, 'NEEDS_VERIFICATION');

  // Missing receiptRetrieval metadata
  const missingRetrieval = assess(createSyntheticPoFixture({ receiptRetrieval: null }));
  assert.equal(missingRetrieval.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.ok(missingRetrieval.verificationReasons.some((r) => r.includes('receipt retrieval with exhausted pagination is not evidenced')));
});

test('Synthetic Fixture: scenario 9 — draft and cancelled receipts are excluded from verified totals', () => {
  const po = createSyntheticPoFixture({
    id: 'SYN-PO-DOCSTATUS',
    orderedQuantity: 100,
    receipts: [
      { receiptId: 'PR-DRAFT', receiptItemId: 'PRI-DRAFT', purchaseOrderId: 'SYN-PO-DOCSTATUS', purchaseOrderItemId: 'SYNTHETIC-ITEM-001', quantity: 50, docstatus: 0 },
      { receiptId: 'PR-CANCELLED', receiptItemId: 'PRI-CANCELLED', purchaseOrderId: 'SYN-PO-DOCSTATUS', purchaseOrderItemId: 'SYNTHETIC-ITEM-001', quantity: 50, docstatus: 2 },
      { receiptId: 'PR-SUBMITTED', receiptItemId: 'PRI-SUBMITTED', purchaseOrderId: 'SYN-PO-DOCSTATUS', purchaseOrderItemId: 'SYNTHETIC-ITEM-001', quantity: 30, docstatus: 1 },
    ],
  });
  const res = assess(po);
  // Only submitted receipt (qty: 30) is counted
  assert.equal(res.receivedQuantity, 30);
  assert.equal(res.outstandingQuantity, 70);
  assert.equal(res.partialReceipt, true);
  assert.equal(res.receiptEvidence.length, 1);
  assert.equal(res.receiptEvidence[0].receiptId, 'PR-SUBMITTED');

  // Invalid docstatus (e.g. docstatus: 3) triggers invalid document status reason
  const poInvalidDocstatus = createSyntheticPoFixture({
    id: 'SYN-PO-INVALID-DOCSTATUS',
    receipts: [
      { receiptId: 'PR-INV', receiptItemId: 'PRI-INV', purchaseOrderId: 'SYN-PO-INVALID-DOCSTATUS', purchaseOrderItemId: 'SYNTHETIC-ITEM-001', quantity: 10, docstatus: 3 },
    ],
  });
  const resInv = assess(poInvalidDocstatus);
  assert.equal(resInv.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.ok(resInv.verificationReasons.some((r) => r.includes('invalid document status')));
});

test('Synthetic Fixture: scenario 10 — duplicate receipt item rows are detected without double-counting', () => {
  const duplicateReceiptRow = {
    receiptId: 'PR-DUP-01',
    receiptItemId: 'PRI-DUP-ROW-99', // identical receipt item identifier
    purchaseOrderId: 'SYN-PO-DUP',
    purchaseOrderItemId: 'SYNTHETIC-ITEM-001',
    itemCode: 'SYN-SKU-100',
    quantity: 40,
    docstatus: 1,
  };
  const po = createSyntheticPoFixture({
    id: 'SYN-PO-DUP',
    orderedQuantity: 100,
    receipts: [duplicateReceiptRow, duplicateReceiptRow],
  });
  const res = assess(po);
  assert.equal(res.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.equal(res.receivedQuantity, null);
  assert.equal(res.outstandingQuantity, null);
  assert.ok(res.verificationReasons.some((r) => r.includes('appears more than once in the evidence set')));
});

test('Synthetic Fixture: scenario 11 — PO line received quantity inconsistent with receipts triggers NEEDS_VERIFICATION', () => {
  // Consistent case: PO line claims 30, verified receipts sum to 30
  const poConsistent = createSyntheticPoFixture({
    id: 'SYN-PO-CONSISTENT',
    orderedQuantity: 100,
    receivedQuantity: 30,
    receipts: [
      { receiptId: 'PR-OK', receiptItemId: 'PRI-OK', purchaseOrderId: 'SYN-PO-CONSISTENT', purchaseOrderItemId: 'SYNTHETIC-ITEM-001', itemCode: 'SYN-SKU-100', quantity: 30, docstatus: 1 },
    ],
  });
  const resConsistent = assess(poConsistent);
  assert.equal(resConsistent.receivedQuantity, 30);
  assert.equal(resConsistent.outstandingQuantity, 70);
  assert.equal(resConsistent.verificationReasons.length, 0);

  // Inconsistent case: PO line claims 50, but verified receipts only total 30
  const poInconsistent = createSyntheticPoFixture({
    id: 'SYN-PO-INCONSISTENT',
    orderedQuantity: 100,
    receivedQuantity: 50, // Claims 50
    receipts: [
      { receiptId: 'PR-INCON-1', receiptItemId: 'PRI-INCON-1', purchaseOrderId: 'SYN-PO-INCONSISTENT', purchaseOrderItemId: 'SYNTHETIC-ITEM-001', itemCode: 'SYN-SKU-100', quantity: 30, docstatus: 1 },
    ],
  });
  const resInconsistent = assess(poInconsistent);
  assert.equal(resInconsistent.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.equal(resInconsistent.receivedQuantity, null);
  assert.equal(resInconsistent.outstandingQuantity, null);
  assert.ok(resInconsistent.verificationReasons.some((r) => r.includes('does not match verified receipt evidence')));
});

test('Synthetic Fixture: scenario 12 — fully received future-dated item evaluates to RECEIVED not future open', () => {
  const poFutureFull = createSyntheticPoFixture({
    id: 'SYN-PO-FUT-FULL',
    scheduleDate: '2026-12-25', // 2 months in the future
    orderedQuantity: 50,
    receipts: [
      { receiptId: 'PR-FUT-FULL', receiptItemId: 'PRI-FUT-FULL', purchaseOrderId: 'SYN-PO-FUT-FULL', purchaseOrderItemId: 'SYNTHETIC-ITEM-001', itemCode: 'SYN-SKU-100', quantity: 50, docstatus: 1 },
    ],
  });
  const res = assess(poFutureFull);
  assert.equal(res.deliveryStatus, 'RECEIVED');
  assert.equal(res.receivedQuantity, 50);
  assert.equal(res.outstandingQuantity, 0);
  assert.equal(res.partialReceipt, false);
});

test('Synthetic Fixture: scenario 13 — boundary dates, zero quantities, and invalid values', () => {
  // Boundary dates around today (2026-10-25) with upcoming window = 7
  assert.equal(assess(createSyntheticPoFixture({ scheduleDate: '2026-10-24' })).deliveryStatus, 'OVERDUE');
  assert.equal(assess(createSyntheticPoFixture({ scheduleDate: '2026-10-25' })).deliveryStatus, 'DUE_TODAY');
  assert.equal(assess(createSyntheticPoFixture({ scheduleDate: '2026-10-26' })).deliveryStatus, 'UPCOMING');
  assert.equal(assess(createSyntheticPoFixture({ scheduleDate: '2026-11-01' })).deliveryStatus, 'UPCOMING');
  assert.equal(assess(createSyntheticPoFixture({ scheduleDate: '2026-11-02' })).deliveryStatus, 'FUTURE_OPEN_DELIVERY');

  // Zero quantity ordered: 0 ordered and 0 received -> 0 outstanding -> RECEIVED
  const zeroOrdered = assess(createSyntheticPoFixture({ orderedQuantity: 0, receipts: [] }));
  assert.equal(zeroOrdered.deliveryStatus, 'RECEIVED');
  assert.equal(zeroOrdered.outstandingQuantity, 0);

  // Over-receipt: receipt quantity exceeds ordered quantity
  const overReceipt = assess(createSyntheticPoFixture({
    id: 'SYN-PO-OVER',
    orderedQuantity: 10,
    receipts: [
      { receiptId: 'PR-OVER', receiptItemId: 'PRI-OVER', purchaseOrderId: 'SYN-PO-OVER', purchaseOrderItemId: 'SYNTHETIC-ITEM-001', quantity: 15, docstatus: 1 },
    ],
  }));
  assert.equal(overReceipt.deliveryStatus, 'NEEDS_VERIFICATION');
  assert.ok(overReceipt.verificationReasons.some((r) => r.includes('exceeds ordered quantity')));

  // Negative receipt return without prior receipt -> contradictory negative received
  const negReturn = assess(createSyntheticPoFixture({
    id: 'SYN-PO-RET',
    orderedQuantity: 10,
    receipts: [
      { receiptId: 'PR-RET', receiptItemId: 'PRI-RET', purchaseOrderId: 'SYN-PO-RET', purchaseOrderItemId: 'SYNTHETIC-ITEM-001', quantity: 5, isReturn: true, docstatus: 1 },
    ],
  }));
  assert.equal(negReturn.deliveryStatus, 'NEEDS_VERIFICATION');

  // Invalid calendar dates
  assert.equal(assess(createSyntheticPoFixture({ scheduleDate: '2026-02-29' })).deliveryStatus, 'NEEDS_VERIFICATION'); // Non-leap year
  assert.equal(assess(createSyntheticPoFixture({ scheduleDate: '2026-04-31' })).deliveryStatus, 'NEEDS_VERIFICATION'); // April has 30 days
  assert.equal(assess(createSyntheticPoFixture({ scheduleDate: '25-10-2026' })).deliveryStatus, 'NEEDS_VERIFICATION'); // Wrong format

  // Missing identifier fields (empty, null, undefined)
  assert.equal(assess(createSyntheticPoFixture({ id: '' })).deliveryStatus, 'NEEDS_VERIFICATION');
  assert.equal(assess({ ...createSyntheticPoFixture(), id: null }).deliveryStatus, 'NEEDS_VERIFICATION');
  assert.equal(assess({ ...createSyntheticPoFixture(), id: undefined }).deliveryStatus, 'NEEDS_VERIFICATION');
  assert.equal(assess(createSyntheticPoFixture({ supplier: '' })).deliveryStatus, 'NEEDS_VERIFICATION');
  assert.equal(assess({ ...createSyntheticPoFixture(), supplier: null }).deliveryStatus, 'NEEDS_VERIFICATION');
  assert.equal(assess({ ...createSyntheticPoFixture(), supplier: undefined }).deliveryStatus, 'NEEDS_VERIFICATION');
  assert.equal(assess(createSyntheticPoFixture({ itemId: '' })).deliveryStatus, 'NEEDS_VERIFICATION');
  const poNullItem = createSyntheticPoFixture();
  poNullItem.items[0].id = null;
  assert.equal(assess(poNullItem).deliveryStatus, 'NEEDS_VERIFICATION');
  assert.equal(assess(createSyntheticPoFixture({ itemCode: '' })).deliveryStatus, 'NEEDS_VERIFICATION');
  const poNullCode = createSyntheticPoFixture();
  poNullCode.items[0].itemCode = null;
  assert.equal(assess(poNullCode).deliveryStatus, 'NEEDS_VERIFICATION');

  // Zero quantity receipt: submitted receipt with quantity 0 does not alter outstanding quantity
  const zeroReceipt = assess(createSyntheticPoFixture({
    id: 'SYN-PO-ZERO-PR',
    scheduleDate: '2026-10-25',
    orderedQuantity: 20,
    receipts: [
      { receiptId: 'PR-ZERO', receiptItemId: 'PRI-ZERO', purchaseOrderId: 'SYN-PO-ZERO-PR', purchaseOrderItemId: 'SYNTHETIC-ITEM-001', itemCode: 'SYN-SKU-100', quantity: 0, docstatus: 1 },
    ],
  }));
  assert.equal(zeroReceipt.deliveryStatus, 'DUE_TODAY');
  assert.equal(zeroReceipt.receivedQuantity, 0);
  assert.equal(zeroReceipt.outstandingQuantity, 20);
  assert.equal(zeroReceipt.partialReceipt, false);

  // Month-end rollover boundary: monitoring date at month end (Feb 28, non-leap year)
  const febSettings = { ...settings, upcomingDays: 7 };
  const febToday = '2026-02-28';
  // 2026-02-28 + 7 days = 2026-03-07 (UPCOMING)
  const poMonthEndUpcoming = createSyntheticPoFixture({ scheduleDate: '2026-03-07', orderedQuantity: 10 });
  assert.equal(assess(poMonthEndUpcoming, febSettings, febToday).deliveryStatus, 'UPCOMING');
  // 2026-02-28 + 8 days = 2026-03-08 (FUTURE_OPEN_DELIVERY)
  const poMonthEndFuture = createSyntheticPoFixture({ scheduleDate: '2026-03-08', orderedQuantity: 10 });
  assert.equal(assess(poMonthEndFuture, febSettings, febToday).deliveryStatus, 'FUTURE_OPEN_DELIVERY');

  // Supplier promise due-date basis (dueDateBasis: 'supplier_promise')
  const promiseSettings = { ...settings, dueDateBasis: 'supplier_promise' };
  const poPromisedOverdue = createSyntheticPoFixture({ scheduleDate: '2026-10-30', expectedDeliveryDate: '2026-10-24', orderedQuantity: 10 });
  assert.equal(assess(poPromisedOverdue, promiseSettings).deliveryStatus, 'OVERDUE');
  const poPromisedToday = createSyntheticPoFixture({ scheduleDate: '2026-10-30', expectedDeliveryDate: '2026-10-25', orderedQuantity: 10 });
  assert.equal(assess(poPromisedToday, promiseSettings).deliveryStatus, 'DUE_TODAY');
  const poPromisedUpcoming = createSyntheticPoFixture({ scheduleDate: '2026-10-20', expectedDeliveryDate: '2026-10-28', orderedQuantity: 10 });
  assert.equal(assess(poPromisedUpcoming, promiseSettings).deliveryStatus, 'UPCOMING');
  const poPromisedFuture = createSyntheticPoFixture({ scheduleDate: '2026-10-20', expectedDeliveryDate: '2026-11-15', orderedQuantity: 10 });
  assert.equal(assess(poPromisedFuture, promiseSettings).deliveryStatus, 'FUTURE_OPEN_DELIVERY');
  const poPromisedMissing = createSyntheticPoFixture({ scheduleDate: '2026-10-25', expectedDeliveryDate: null, orderedQuantity: 10 });
  assert.equal(assess(poPromisedMissing, promiseSettings).deliveryStatus, 'NEEDS_VERIFICATION');
  assert.ok(assess(poPromisedMissing, promiseSettings).verificationReasons.some((r) => r.includes('Supplier promised date is missing')));
});

test('Synthetic Fixture: scenario 14 — inventory buffer risk is transparently UNAVAILABLE across all delivery states', () => {
  // Test across multiple delivery states: open, overdue, received, partial, and needs verification
  const states = [
    createSyntheticPoFixture({ scheduleDate: '2026-10-24' }), // Overdue
    createSyntheticPoFixture({ scheduleDate: '2026-10-25' }), // Due Today
    createSyntheticPoFixture({ scheduleDate: '2026-10-28' }), // Upcoming
    createSyntheticPoFixture({ scheduleDate: '2026-11-20' }), // Future Open
    createSyntheticPoFixture({ scheduleDate: '2026-10-20', orderedQuantity: 10, receipts: [{ receiptId: 'PR-1', receiptItemId: 'PRI-1', purchaseOrderId: 'SYNTHETIC-PO-001', purchaseOrderItemId: 'SYNTHETIC-ITEM-001', itemCode: 'SYN-SKU-100', quantity: 10, docstatus: 1 }] }), // Received
    createSyntheticPoFixture({ scheduleDate: '2026-10-20', orderedQuantity: 10, receipts: [{ receiptId: 'PR-1', receiptItemId: 'PRI-1', purchaseOrderId: 'SYNTHETIC-PO-001', purchaseOrderItemId: 'SYNTHETIC-ITEM-001', itemCode: 'SYN-SKU-100', quantity: 4, docstatus: 1 }] }), // Partial
    createSyntheticPoFixture({ scheduleDate: null }), // Needs verification
  ];

  for (const po of states) {
    const res = assess(po);
    // Mandatory requirement 6: do not infer zero stock from missing Bin records or hallucinate risk tiers
    assert.equal(res.bufferRisk, 'UNAVAILABLE');
    assert.equal(res.bufferMarginDays, null);
    assert.equal(res.bufferDetails, 'Stock on-hand and production work-order demand evidence are not present in current query scope.');
  }
});

