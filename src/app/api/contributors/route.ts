import { NextResponse } from 'next/server';
import { AppError } from '../../../server/storage/index.js';
import { createContributorRecord } from '../../../server/contributionService.js';
import { getServerSecurityConfigFromEnv, createInvestigationStore } from '../../../server/storage/index.js';
import { REGISTRATION_CEREMONY_COOKIE_NAME, clearCeremonyCookie, readCeremonyCookieFromRequest, buildSessionPayload } from '../../../server/auth/webauthn.js';
import { setSessionCookie } from '../../../server/auth/session.js';
import { errorResponse, readJsonBody } from '../../../server/http.js';

export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  try {
    const security = getServerSecurityConfigFromEnv();
    const challenge = readCeremonyCookieFromRequest(request, REGISTRATION_CEREMONY_COOKIE_NAME, security.sessionSecret || security.identityPepper);
    if (!challenge) {
      throw new AppError('Passkey registration ceremony is required.', 401, 'UNAUTHORIZED');
    }

    const body = await readJsonBody(request);
    const store = createInvestigationStore();
    const result = await createContributorRecord(store, {
      name: body.name,
      role: body.role,
    }, challenge, body.registration_response || body);

    const response = NextResponse.json(result.contributor, { status: 201 });
    setSessionCookie(response, buildSessionPayload(result.contributor, result.credential), security.sessionSecret || security.identityPepper);
    clearCeremonyCookie(response, REGISTRATION_CEREMONY_COOKIE_NAME);
    return response;
  } catch (error) {
    return errorResponse(error, 'Unable to save contributor.');
  }
}
