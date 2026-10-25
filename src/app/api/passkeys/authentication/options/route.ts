import { NextResponse } from 'next/server';
import { AppError } from '../../../../../server/storage/index.js';
import { createPasskeyAuthenticationCeremony } from '../../../../../server/contributionService.js';
import { getServerSecurityConfigFromEnv } from '../../../../../server/storage/index.js';
import { AUTHENTICATION_CEREMONY_COOKIE_NAME, setCeremonyCookie } from '../../../../../server/auth/webauthn.js';
import { errorResponse } from '../../../../../server/http.js';

export const dynamic = 'force-dynamic';

export async function POST(request) {
  try {
    const security = getServerSecurityConfigFromEnv();
    const ceremony = await createPasskeyAuthenticationCeremony(request);
    const response = NextResponse.json({ options: ceremony.options });
    setCeremonyCookie(response, AUTHENTICATION_CEREMONY_COOKIE_NAME, ceremony.challenge, security.sessionSecret || security.identityPepper);
    return response;
  } catch (error) {
    return errorResponse(error, 'Unable to start passkey authentication.');
  }
}
