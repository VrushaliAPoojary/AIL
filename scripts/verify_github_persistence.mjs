import { createContributorRecord, createContributionRecord, getContributorRecord, getContributionRecord, listContributionRecords } from '../src/server/contributionService.js';
import { createGitHubInvestigationStore } from '../src/server/storage/githubInvestigationStore.js';
import { getGitHubPersistenceConfigFromEnv, getServerSecurityConfigFromEnv } from '../src/server/storage/index.js';

function safeTimestamp() {
  return new Date().toISOString().replace(/[:.]/g, '-');
}

function fakeRegistrationVerifier(credentialId) {
  return async ({ expectedOrigin, expectedRPID }) => ({
    verified: true,
    registrationInfo: {
      credential: {
        id: credentialId,
        publicKey: new Uint8Array([1, 2, 3, 4]),
        counter: 0,
        transports: ['internal'],
      },
      credentialType: 'public-key',
      credentialDeviceType: 'singleDevice',
      credentialBackedUp: false,
      userVerified: true,
      origin: expectedOrigin,
      rpID: expectedRPID,
    },
  });
}

const config = getGitHubPersistenceConfigFromEnv();
if (!config) {
  console.error('BLOCKED: GITHUB_DATA_REPOSITORY_NOT_CONFIGURED');
  process.exit(2);
}

const security = (() => {
  try {
    return getServerSecurityConfigFromEnv();
  } catch {
    return {
      identityPepper: 'local-identity-pepper',
      sessionSecret: 'local-session-secret',
    };
  }
})();

const store = createGitHubInvestigationStore(config);
const suffix = safeTimestamp();
const contributorId = 'ctr_' + suffix.replace(/[^a-z0-9]/gi, '').slice(0, 16);
const credentialId = 'cred-' + suffix;
const contributorInput = {
  name: 'AIL Persistence Test ' + suffix,
  role: 'Persistence Validation',
};
const challenge = {
  ceremony_id: 'reg_' + suffix.replace(/[^a-z0-9]/gi, '').slice(0, 16),
  kind: 'registration',
  challenge: 'challenge-' + suffix,
  issued_at: new Date().toISOString(),
  expires_at: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
  origin: 'http://localhost:3000',
  rp_id: 'localhost',
  profile: contributorInput,
  pending_contributor_id: contributorId,
};

const contributorResult = await createContributorRecord(
  store,
  contributorInput,
  challenge,
  { id: 'response-' + suffix },
  { verifyRegistrationResponse: fakeRegistrationVerifier(credentialId) },
);
const contributor = contributorResult.contributor;
const credential = contributorResult.credential;
const loadedContributor = await getContributorRecord(store, contributor.id);
const contribution = await createContributionRecord(store, {
  contributor_id: contributor.id,
  credential_hash: credential.credential_hash,
}, {
  type: 'TEXT',
  resource: {
    text: '07B-01B persistence validation',
  },
  context: 'Controlled persistence verification',
});
const loadedContribution = await getContributionRecord(store, contribution.id);
const recentContributions = await listContributionRecords(store, { limit: 5 });

const paths = {
  contributor: 'data/contributors/' + contributor.id + '.json',
  credential: 'data/auth/credentials/' + credential.credential_hash + '.json',
  credentialIndex: 'data/indexes/credentials/' + credential.credential_hash + '.json',
  resource: 'data/resources/' + contribution.resource_id + '.json',
  resourceFingerprintIndex: 'data/indexes/resources/by-fingerprint/<hash>.json',
  contribution: 'data/contributions/' + contribution.id + '.json',
  activity: 'data/activity/<event-id>.json',
};

console.log(JSON.stringify({
  status: 'verified',
  paths,
  contributor_id: contributor.id,
  credential_hash: credential.credential_hash,
  contribution_id: contribution.id,
  loaded_contributor_matches: loadedContributor.id === contributor.id,
  loaded_contribution_matches: loadedContribution.id === contribution.id,
  recent_count: recentContributions.length,
}, null, 2));
