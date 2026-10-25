import { NextResponse } from 'next/server';
import { getContributionRecord } from '../../../../server/contributionService.js';
import { createInvestigationStore } from '../../../../server/storage/index.js';
import { errorResponse } from '../../../../server/http.js';

export const dynamic = 'force-dynamic';

export async function GET(_request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const store = createInvestigationStore();
    const { id } = await context.params;
    const contribution = await getContributionRecord(store, id);
    return NextResponse.json(contribution);
  } catch (error) {
    return errorResponse(error, 'Unable to load contribution.');
  }
}
