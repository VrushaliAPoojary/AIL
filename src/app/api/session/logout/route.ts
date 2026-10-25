import { NextResponse } from 'next/server';
import { clearSessionCookie } from '../../../../server/auth/session.js';
import { clearCeremonyCookie, REGISTRATION_CEREMONY_COOKIE_NAME, AUTHENTICATION_CEREMONY_COOKIE_NAME } from '../../../../server/auth/webauthn.js';

export const dynamic = 'force-dynamic';

export async function POST() {
  const response = NextResponse.json({ status: 'ok' });
  clearSessionCookie(response);
  clearCeremonyCookie(response, REGISTRATION_CEREMONY_COOKIE_NAME);
  clearCeremonyCookie(response, AUTHENTICATION_CEREMONY_COOKIE_NAME);
  return response;
}
