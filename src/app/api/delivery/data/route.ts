import { NextResponse } from 'next/server';
import { requireP02Admin } from '../../../../server/delivery/auth';
import { getDeliverySettings } from '../../../../server/delivery/config';
import { getControlCenterData } from '../../../../server/delivery/data';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET() {
  const settings = await getDeliverySettings();
  if (settings.mode === 'configured' && !(await requireP02Admin())) {
    return NextResponse.json({ error: 'Administrator authentication is required to view live procurement data.' }, { status: 401 });
  }
  try { return NextResponse.json(await getControlCenterData(), { headers: { 'Cache-Control': 'private, no-store' } }); }
  catch { return NextResponse.json({ error: 'Delivery data is unavailable because its source report could not be validated.' }, { status: 503 }); }
}

