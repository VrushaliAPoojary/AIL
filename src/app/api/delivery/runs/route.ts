import { NextResponse } from 'next/server';
import { requireAdminResponse, sameOrigin } from '../../../../server/delivery/http';
import { getDeliverySettings } from '../../../../server/delivery/config';
import { getRunHistory, startMonitoringRun } from '../../../../server/delivery/runService';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET() {
  const denied = await requireAdminResponse();
  if (denied) return denied;
  const runs = await getRunHistory();
  return NextResponse.json({ runs: runs.map(({ result: _result, ...run }) => run) }, { headers: { 'Cache-Control': 'private, no-store' } });
}

export async function POST(request: Request) {
  const denied = await requireAdminResponse();
  if (denied) return denied;
  if (!sameOrigin(request)) return NextResponse.json({ error: 'Cross-origin request rejected.' }, { status: 403 });
  if ((await getDeliverySettings()).mode !== 'configured') return NextResponse.json({ error: 'ART execution is unavailable until server-side ART connection and agent settings are configured.' }, { status: 503 });
  const idempotencyKey = request.headers.get('idempotency-key') || '';
  if (!/^[A-Za-z0-9._:-]{8,120}$/.test(idempotencyKey)) return NextResponse.json({ error: 'A valid Idempotency-Key header is required.' }, { status: 400 });
  try {
    const started = await startMonitoringRun(idempotencyKey);
    return NextResponse.json(started, { status: started.reused ? 200 : 202 });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : 'Unable to start run.' }, { status: Number((error as { status?: number }).status) || 503 });
  }
}

