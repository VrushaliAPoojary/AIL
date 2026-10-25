import { NextResponse } from 'next/server';
import { requireAdminResponse, safeError, sameOrigin } from '../../../../server/delivery/http';
import { getDeliverySettings } from '../../../../server/delivery/config';
import { validateSettings } from '../../../../server/delivery/settingsValidation';
import { saveSettings } from '../../../../server/delivery/store';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET() {
  const denied = await requireAdminResponse();
  if (denied) return denied;
  return NextResponse.json(await getDeliverySettings(), { headers: { 'Cache-Control': 'private, no-store' } });
}

export async function PUT(request: Request) {
  const denied = await requireAdminResponse();
  if (denied) return denied;
  if (!sameOrigin(request)) return NextResponse.json({ error: 'Cross-origin request rejected.' }, { status: 403 });
  try {
    const value = validateSettings(await request.json());
    return NextResponse.json(await saveSettings(value));
  } catch (error) { return safeError(error); }
}
