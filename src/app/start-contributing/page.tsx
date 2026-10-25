import { redirect } from 'next/navigation';
import { getServerSecurityConfigFromEnv } from '../../server/storage/index.js';
import { readSessionFromCookies } from '../../server/auth/session-route.js';

export const dynamic = 'force-dynamic';

export default async function StartContributingPage() {
  const security = getServerSecurityConfigFromEnv();
  const session = await readSessionFromCookies(security.sessionSecret || security.identityPepper);
  redirect(session?.contributor_id ? '/contribute' : '/onboarding');
}
