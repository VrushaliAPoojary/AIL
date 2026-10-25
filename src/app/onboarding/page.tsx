import { redirect } from 'next/navigation';
import { OnboardingFlow } from '../../features/onboarding/OnboardingFlow';
import { getServerSecurityConfigFromEnv } from '../../server/storage/index.js';
import { readSessionFromCookies } from '../../server/auth/session-route.js';

export const dynamic = 'force-dynamic';

export default async function OnboardingPage() {
  const security = getServerSecurityConfigFromEnv();
  const session = await readSessionFromCookies(security.sessionSecret || security.identityPepper);
  if (session?.contributor_id) {
    redirect('/contribute');
  }

  return <OnboardingFlow />;
}
