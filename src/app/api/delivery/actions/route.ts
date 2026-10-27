import { NextResponse } from 'next/server';
import { requireP02Admin } from '../../../../server/delivery/auth';
import { sameOrigin } from '../../../../server/delivery/http';
import { getControlCenterData } from '../../../../server/delivery/data';
import { generateChaserDraft } from '../../../../server/delivery/chaserService';
import {
  saveStagedChaser,
  updateChaserStatus,
  saveSupplierPromise,
  listStagedChasers,
  listSupplierPromises,
} from '../../../../server/delivery/store';
import { randomUUID } from 'node:crypto';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET() {
  const chasers = await listStagedChasers();
  const promises = await listSupplierPromises();
  return NextResponse.json({ chasers, promises }, { headers: { 'Cache-Control': 'private, no-store' } });
}

export async function POST(request: Request) {
  if (!sameOrigin(request)) {
    return NextResponse.json({ error: 'Cross-origin request rejected.' }, { status: 403 });
  }

  const isAuthed = await requireP02Admin();
  if (!isAuthed && process.env.NODE_ENV === 'production') {
    return NextResponse.json({ error: 'Administrator authentication required.' }, { status: 401 });
  }

  let body: any;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON request body.' }, { status: 400 });
  }

  const { action, payload } = body;
  const actor = 'buyer';

  if (action === 'stage-chaser') {
    const { orderId, orderItemId, notes } = payload || {};
    if (!orderId || typeof orderId !== 'string') {
      return NextResponse.json({ error: 'Missing required orderId.' }, { status: 400 });
    }

    const data = await getControlCenterData();
    const order = data.purchaseOrders.find((o: any) => o.id === orderId);
    if (!order) {
      return NextResponse.json({ error: `Order ${orderId} not found.` }, { status: 404 });
    }

    const targetItem = order.items.find((it: any) => (orderItemId ? it.id === orderItemId : true)) || order.items[0];
    const assessment = order.assessments?.find((a: any) => a.orderItemId === targetItem.id) || {
      orderId: order.id,
      orderItemId: targetItem.id,
      supplier: order.supplier,
      itemCode: targetItem.itemCode,
      description: targetItem.description,
      orderedQuantity: targetItem.orderedQuantity,
      receivedQuantity: 0,
      outstandingQuantity: targetItem.orderedQuantity,
      baselineDate: targetItem.scheduleDate,
      promisedDate: targetItem.expectedDeliveryDate,
      applicableDueDate: targetItem.expectedDeliveryDate || targetItem.scheduleDate,
      deliveryStatus: 'OVERDUE',
      partialReceipt: false,
      excluded: false,
      isAcknowledged: Boolean(order.orderConfirmationNo),
      acknowledgmentOverdue: !order.orderConfirmationNo,
      orderStatus: order.status,
      isClosedOrCompleted: false,
      bufferRisk: 'UNAVAILABLE',
      bufferMarginDays: null,
      verificationReasons: [],
      receiptEvidence: [],
    };

    const chaser = generateChaserDraft(order, assessment, notes);
    await saveStagedChaser(chaser, actor);
    return NextResponse.json({ success: true, chaser }, { status: 201 });
  }

  if (action === 'approve-chaser' || action === 'dismiss-chaser') {
    const { chaserId } = payload || {};
    if (!chaserId || typeof chaserId !== 'string') {
      return NextResponse.json({ error: 'Missing required chaserId.' }, { status: 400 });
    }

    const status = action === 'approve-chaser' ? 'APPROVED' : 'DISMISSED';
    const updated = await updateChaserStatus(chaserId, status, actor);
    if (!updated) {
      return NextResponse.json({ error: `Chaser ${chaserId} not found.` }, { status: 404 });
    }

    return NextResponse.json({ success: true, chaser: updated });
  }

  if (action === 'record-promise') {
    const { orderId, orderItemId, promisedDate, promisedQuantity, sourceReference, notes } = payload || {};
    if (!orderId || !promisedDate || !sourceReference) {
      return NextResponse.json({ error: 'Missing orderId, promisedDate, or sourceReference.' }, { status: 400 });
    }

    if (!/^\d{4}-\d{2}-\d{2}$/.test(promisedDate)) {
      return NextResponse.json({ error: 'Promised date must be an ISO date (YYYY-MM-DD).' }, { status: 400 });
    }

    const data = await getControlCenterData();
    const order = data.purchaseOrders.find((o: any) => o.id === orderId);
    const targetItem = order?.items?.find((it: any) => (orderItemId ? it.id === orderItemId : true)) || order?.items?.[0];

    const promise = {
      id: `PROM-${orderId}-${randomUUID().slice(0, 8)}`,
      orderId,
      orderItemId: targetItem?.id || orderItemId || 'row-1',
      originalRequestedDate: targetItem?.scheduleDate || null,
      promisedDate,
      promisedQuantity: Number.isFinite(promisedQuantity) ? Number(promisedQuantity) : null,
      state: 'CONFIRMED' as const,
      sourceReference: String(sourceReference).trim(),
      recordedAt: new Date().toISOString(),
      recordedBy: actor,
      notes: notes ? String(notes).trim() : undefined,
    };

    await saveSupplierPromise(promise, actor);
    return NextResponse.json({ success: true, promise }, { status: 201 });
  }

  return NextResponse.json({ error: `Unknown action: ${action}` }, { status: 400 });
}
