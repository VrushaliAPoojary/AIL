import { NextResponse } from 'next/server';
import { requireP02Admin } from './auth';

export function sameOrigin(request: Request) {
  const origin = request.headers.get('origin');
  if (!origin) return true;
  try {
    const originUrl = new URL(origin);
    const requestUrl = new URL(request.url);
    if (originUrl.origin === requestUrl.origin) return true;
    const host = request.headers.get('host');
    if (host && (originUrl.host === host || originUrl.host === host.split(':')[0])) return true;
    const isLocalOrigin = originUrl.hostname === 'localhost' || originUrl.hostname === '127.0.0.1';
    const isLocalReq = requestUrl.hostname === 'localhost' || requestUrl.hostname === '127.0.0.1';
    if (isLocalOrigin && isLocalReq) return true;
    return false;
  } catch {
    return false;
  }
}

export async function requireAdminResponse() {
  if (await requireP02Admin()) return null;
  return NextResponse.json({ error: 'Administrator authentication is required.' }, { status: 401 });
}

export function safeError(error: unknown) {
  const message = error instanceof Error ? error.message : 'Request could not be completed.';
  return NextResponse.json({ error: message }, { status: Number((error as { status?: number })?.status) || 400 });
}
