import { NextResponse } from 'next/server';
import { requireP02Admin } from './auth';

export function sameOrigin(request: Request) {
  const origin = request.headers.get('origin');
  if (!origin) return true;
  try { return new URL(origin).origin === new URL(request.url).origin; } catch { return false; }
}

export async function requireAdminResponse() {
  if (await requireP02Admin()) return null;
  return NextResponse.json({ error: 'Administrator authentication is required.' }, { status: 401 });
}

export function safeError(error: unknown) {
  const message = error instanceof Error ? error.message : 'Request could not be completed.';
  return NextResponse.json({ error: message }, { status: Number((error as { status?: number })?.status) || 400 });
}
