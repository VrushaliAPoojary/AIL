import { NextResponse } from 'next/server';
import { getContributorRecord } from '../../../../server/contributionService.js';
import { createInvestigationStore } from '../../../../server/storage/index.js';
import { errorResponse } from '../../../../server/http.js';

export const dynamic = 'force-dynamic';

export async function GET(_request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const store = createInvestigationStore();
    const { id } = await context.params;
    const contributor = await getContributorRecord(store, id);
    return NextResponse.json(contributor);
  } catch (error) {
    return errorResponse(error, 'Unable to load contributor.');
  }
}
