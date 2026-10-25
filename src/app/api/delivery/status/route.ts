import { NextResponse } from 'next/server';
import { getIntegrationStatus } from '../../../../server/delivery/config';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET() {
  return NextResponse.json(await getIntegrationStatus());
}
