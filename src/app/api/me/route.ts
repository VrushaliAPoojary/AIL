import { NextResponse } from 'next/server';
import { AppError } from '../../../server/storage/index.js';
import { createInvestigationStore, getServerSecurityConfigFromEnv } from '../../../server/storage/index.js';
import { getCurrentContributorRecord } from '../../../server/contributionService.js';
import { readSessionFromRequest } from '../../../server/auth/session.js';
import { errorResponse } from '../../../server/http.js';

export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
  try {
    const security = getServerSecurityConfigFromEnv();
    const session = readSessionFromRequest(request, security.sessionSecret || security.identityPepper);
    if (!session) {
      throw new AppError('Not authenticated.', 401, 'UNAUTHORIZED');
    }

    const store = createInvestigationStore();
    const contributor = await getCurrentContributorRecord(store, session);
    return NextResponse.json(contributor);
  } catch (error) {
    return errorResponse(error, 'Unable to load current contributor.');
  }
}
