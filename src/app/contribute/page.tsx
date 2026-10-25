import { redirect } from 'next/navigation';
import { ContributeFlow } from '../../features/contribute/ContributeFlow';
import { getServerSecurityConfigFromEnv, createInvestigationStore } from '../../server/storage/index.js';
import { getCurrentContributorRecord } from '../../server/contributionService.js';
import { readSessionFromCookies } from '../../server/auth/session-route.js';

export const dynamic = 'force-dynamic';

export default async function ContributePage() {
  const security = getServerSecurityConfigFromEnv();
  const session = await readSessionFromCookies(security.sessionSecret || security.identityPepper);
  if (!session?.contributor_id) {
    redirect('/onboarding');
  }

  const store = createInvestigationStore();
  const contributor = await getCurrentContributorRecord(store, session);
  return <ContributeFlow contributor={contributor} />;
}
