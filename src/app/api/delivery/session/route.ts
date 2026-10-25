import { NextResponse } from 'next/server';
import { adminCookieOptions, clearLoginFailures, createAdminToken, isLoginRateLimited, P02_ADMIN_COOKIE, recordLoginFailure, requireP02Admin, verifyAdminCredentials } from '../../../../server/delivery/auth';
import { isAdminConfigured } from '../../../../server/delivery/config';
import { sameOrigin } from '../../../../server/delivery/http';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET() {
  return NextResponse.json({ configured: isAdminConfigured(), authenticated: await requireP02Admin() });
}

export async function POST(request: Request) {
  if (!sameOrigin(request)) return NextResponse.json({ error: 'Cross-origin request rejected.' }, { status: 403 });
  const contentLength = Number(request.headers.get('content-length') || 0);
  if (contentLength > 4_096) return NextResponse.json({ error: 'Sign-in request is too large.' }, { status: 413 });
  const key = request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || 'local';
  if (isLoginRateLimited(key)) return NextResponse.json({ error: 'Too many sign-in attempts. Try again later.' }, { status: 429 });
  if (!isAdminConfigured()) return NextResponse.json({ error: 'Administrator sign-in is not configured on the server.' }, { status: 503 });
  let body: any;
  try { body = await request.json(); } catch { return NextResponse.json({ error: 'Request body must be valid JSON.' }, { status: 400 }); }
  if (!verifyAdminCredentials(body.username, body.password)) {
    recordLoginFailure(key);
    return NextResponse.json({ error: 'Username or password is incorrect.' }, { status: 401 });
  }
  clearLoginFailures(key);
  const response = NextResponse.json({ authenticated: true });
  response.cookies.set(P02_ADMIN_COOKIE, createAdminToken(body.username), adminCookieOptions());
  return response;
}

export async function DELETE(request: Request) {
  if (!sameOrigin(request)) return NextResponse.json({ error: 'Cross-origin request rejected.' }, { status: 403 });
  const response = NextResponse.json({ authenticated: false });
  response.cookies.set(P02_ADMIN_COOKIE, '', { ...adminCookieOptions(), maxAge: 0 });
  return response;
}
