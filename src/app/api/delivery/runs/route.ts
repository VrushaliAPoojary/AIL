import { NextResponse } from 'next/server';
import { requireAdminResponse, sameOrigin } from '../../../../server/delivery/http';
import { getDeliverySettings } from '../../../../server/delivery/config';
import { getRunHistory, startMonitoringRun } from '../../../../server/delivery/runService';
import { publicRunRecord } from '../../../../server/delivery/types';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET() {
  const runs = await getRunHistory();
  return NextResponse.json({ runs: runs.map(({ result: _result, ...run }) => publicRunRecord({ ...run, result: null })) }, { headers: { 'Cache-Control': 'private, no-store' } });
}

export async function POST(request: Request) {
  if (!sameOrigin(request)) return NextResponse.json({ error: 'Cross-origin request rejected.' }, { status: 403 });
  const settings = await getDeliverySettings();
  const url = new URL(request.url);
  const headerMode = request.headers.get('x-delivery-mode');
  const queryMode = url.searchParams.get('mode');
  const isDemo = queryMode === 'demo' || headerMode === 'demo' || settings.mode === 'demo';

  // If in configured live mode and not executing a demo run, administrator authentication is required
  if (!isDemo && settings.mode === 'configured') {
    const denied = await requireAdminResponse();
    if (denied) return denied;
  }

  const idempotencyKey = request.headers.get('idempotency-key') || '';
  if (!/^[A-Za-z0-9._:-]{8,120}$/.test(idempotencyKey)) return NextResponse.json({ error: 'A valid Idempotency-Key header is required.' }, { status: 400 });
  try {
    const source: 'art' | 'demo' = isDemo ? 'demo' : 'art';
    const started = await startMonitoringRun(idempotencyKey, source);
    return NextResponse.json(started, { status: started.reused ? 200 : 202 });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : 'Unable to start run.' }, { status: Number((error as { status?: number }).status) || 503 });
  }
}

