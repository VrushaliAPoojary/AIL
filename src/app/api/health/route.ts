import { NextResponse } from 'next/server';
import { getServerEnvironment } from '../../../lib/server/serverEnvironment';

export const dynamic = 'force-dynamic';

export async function GET() {
  getServerEnvironment();

  return NextResponse.json({
    status: 'ok',
    service: 'ail',
  });
}
