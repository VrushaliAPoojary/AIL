import { NextResponse } from 'next/server';
import { requireP02Admin } from '../../../../server/delivery/auth';
import { getDeliverySettings } from '../../../../server/delivery/config';
import { getControlCenterData } from '../../../../server/delivery/data';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
  const settings = await getDeliverySettings();
  const url = new URL(request.url);
  const requestedDemo = url.searchParams.get('mode') === 'demo';
  const isAuthed = await requireP02Admin();
  const forceDemo = requestedDemo;

  try {
    const data = await getControlCenterData(forceDemo);
    return NextResponse.json({
      ...data,
      authNeeded: false,
      authenticated: isAuthed || process.env.NODE_ENV !== 'production',
    }, { headers: { 'Cache-Control': 'private, no-store' } });
  } catch {
    return NextResponse.json({ error: 'Delivery data is unavailable because its source report could not be validated.' }, { status: 503 });
  }
}

