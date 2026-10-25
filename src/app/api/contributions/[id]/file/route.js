import { NextResponse } from 'next/server.js';
import { AppError, createInvestigationStore, getServerSecurityConfigFromEnv } from '../../../../../server/storage/index.js';
import { attachFileToContributionRecord } from '../../../../../server/contributionService.js';
import { readSessionFromRequest } from '../../../../../server/auth/session.js';
import { errorResponse } from '../../../../../server/http.js';

export const dynamic = 'force-dynamic';

export async function POST(request, context) {
  try {
    const security = getServerSecurityConfigFromEnv();
    const session = readSessionFromRequest(request, security.sessionSecret || security.identityPepper);
    if (!session) {
      throw new AppError('Not authenticated.', 401, 'UNAUTHORIZED');
    }

    const { id } = await context.params;

    let formData;
    try {
      formData = await request.formData();
    } catch {
      throw new AppError('Request body must be multipart/form-data.', 400, 'INVALID_MULTIPART');
    }

    const file = formData.get('file');
    if (!file || typeof file === 'string' || typeof file.arrayBuffer !== 'function') {
      throw new AppError('file field is required in multipart request.', 400, 'MISSING_FILE');
    }

    const arrayBuffer = await file.arrayBuffer();
    const bytes = Buffer.from(arrayBuffer);

    const store = createInvestigationStore();
    const result = await attachFileToContributionRecord(store, session, id, {
      bytes,
      original_name: file.name || '',
      mime_type: file.type || '',
      size: bytes.length,
    });

    return NextResponse.json(result, { status: 200 });
  } catch (error) {
    return errorResponse(error, 'Unable to upload resource file.');
  }
}
