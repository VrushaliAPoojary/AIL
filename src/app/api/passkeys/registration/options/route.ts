import { NextResponse } from 'next/server';
import { AppError } from '../../../../../server/storage/index.js';
import { createPasskeyRegistrationCeremony } from '../../../../../server/contributionService.js';
import { getServerSecurityConfigFromEnv } from '../../../../../server/storage/index.js';
import { REGISTRATION_CEREMONY_COOKIE_NAME, setCeremonyCookie } from '../../../../../server/auth/webauthn.js';
import { errorResponse, readJsonBody } from '../../../../../server/http.js';

export const dynamic = 'force-dynamic';

const attempts = new Map();
const WINDOW_MS = 10 * 60 * 1000;
const LIMIT = 5;

function requestKey(request) {
  return request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || 'unknown';
}

function allowAttempt(key) {
  const now = Date.now();
  const entry = attempts.get(key) || [];
  const active = entry.filter((value) => now - value < WINDOW_MS);
  if (active.length >= LIMIT) {
    return false;
  }
  active.push(now);
  attempts.set(key, active);
  return true;
}

export async function POST(request) {
  try {
    const key = requestKey(request);
    if (!allowAttempt(key)) {
      throw new AppError('Too many registration attempts. Please wait and try again.', 429, 'RATE_LIMITED');
    }

    const body = await readJsonBody(request);
    const security = getServerSecurityConfigFromEnv();
    const ceremony = await createPasskeyRegistrationCeremony(body, request);
    const response = NextResponse.json({ options: ceremony.options });
    setCeremonyCookie(response, REGISTRATION_CEREMONY_COOKIE_NAME, ceremony.challenge, security.sessionSecret || security.identityPepper);
    return response;
  } catch (error) {
    return errorResponse(error, 'Unable to start passkey registration.');
  }
}
