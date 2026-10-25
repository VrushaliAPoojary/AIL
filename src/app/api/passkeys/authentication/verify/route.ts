import { NextResponse } from 'next/server';
import { AppError } from '../../../../../server/storage/index.js';
import { resolveContributorFromPasskey } from '../../../../../server/contributionService.js';
import { getServerSecurityConfigFromEnv, createInvestigationStore } from '../../../../../server/storage/index.js';
import { AUTHENTICATION_CEREMONY_COOKIE_NAME, clearCeremonyCookie, readCeremonyCookieFromRequest, buildSessionPayload } from '../../../../../server/auth/webauthn.js';
import { setSessionCookie } from '../../../../../server/auth/session.js';
import { errorResponse, readJsonBody } from '../../../../../server/http.js';

export const dynamic = 'force-dynamic';

export async function POST(request) {
  try {
    const security = getServerSecurityConfigFromEnv();
    const challenge = readCeremonyCookieFromRequest(request, AUTHENTICATION_CEREMONY_COOKIE_NAME, security.sessionSecret || security.identityPepper);
    if (!challenge) {
      throw new AppError('Authentication ceremony is required.', 401, 'UNAUTHORIZED');
    }
    const body = await readJsonBody(request);
    const store = createInvestigationStore();
    const result = await resolveContributorFromPasskey(store, challenge, body.authentication_response || body);
    const response = NextResponse.json(result.contributor);
    setSessionCookie(response, buildSessionPayload(result.contributor, result.credential), security.sessionSecret || security.identityPepper);
    clearCeremonyCookie(response, AUTHENTICATION_CEREMONY_COOKIE_NAME);
    return response;
  } catch (error) {
    return errorResponse(error, 'Unable to complete passkey authentication.');
  }
}
