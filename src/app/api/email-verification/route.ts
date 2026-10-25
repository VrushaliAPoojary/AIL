import { NextResponse } from 'next/server';
import { AppError, validateEmail } from '../../../server/storage/index.js';
import { createVerificationChallenge, setVerificationCookie } from '../../../server/auth/verification.js';
import { getServerSecurityConfigFromEnv } from '../../../server/storage/index.js';
import { errorResponse, readJsonBody } from '../../../server/http.js';

export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  try {
    const body = await readJsonBody(request);
    const email = validateEmail(body.email);
    const security = getServerSecurityConfigFromEnv();
    const challenge = createVerificationChallenge({ email, secret: security.identityPepper });
    const response = NextResponse.json(
      {
        status: 'ok',
        email_label: challenge.payload.email_label,
        ...(process.env.NODE_ENV !== 'production'
          ? { verification_code: challenge.verificationCode }
          : {}),
      },
      { status: 200 },
    );
    setVerificationCookie(response, challenge.payload, security.identityPepper);
    return response;
  } catch (error) {
    if (error instanceof AppError) {
      return errorResponse(error, 'Unable to start email verification.');
    }
    return errorResponse(error, 'Unable to start email verification.');
  }
}
