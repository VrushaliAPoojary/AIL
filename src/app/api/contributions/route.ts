import { NextResponse } from 'next/server';
import { AppError } from '../../../server/storage/index.js';
import { createContributionRecord, listContributionRecords } from '../../../server/contributionService.js';
import { createInvestigationStore, getServerSecurityConfigFromEnv } from '../../../server/storage/index.js';
import { readSessionFromRequest } from '../../../server/auth/session.js';
import { errorResponse, readJsonBody } from '../../../server/http.js';

export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
  try {
    const store = createInvestigationStore();
    const url = new URL(request.url);
    const limit = Number(url.searchParams.get('limit') || '20');
    const contributions = await listContributionRecords(store, { limit });
    return NextResponse.json({ contributions });
  } catch (error) {
    return errorResponse(error, 'Unable to load contributions.');
  }
}

export async function POST(request: Request) {
  try {
    const security = getServerSecurityConfigFromEnv();
    const session = readSessionFromRequest(request, security.sessionSecret || security.identityPepper);
    if (!session) {
      throw new AppError('Not authenticated.', 401, 'UNAUTHORIZED');
    }

    const store = createInvestigationStore();
    const body = await readJsonBody(request);
    const contribution = await createContributionRecord(store, session, body);
    return NextResponse.json(contribution, { status: 201 });
  } catch (error) {
    return errorResponse(error, 'Unable to save contribution.');
  }
}
