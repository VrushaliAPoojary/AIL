import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';
import { createSignedSession, readSignedSession, clearSessionCookie } from '../src/server/auth/session.js';
import { normalizeEmail } from '../src/server/auth/identity.js';
import { createContributorRecord, createContributionRecord, getContributionRecord, getCurrentContributorRecord, listContributionRecords, resolveContributorFromPasskey, attachFileToContributionRecord } from '../src/server/contributionService.js';
import { createGitHubInvestigationStore, createMemoryInvestigationStore, createInvestigationStore, getServerSecurityConfigFromEnv } from '../src/server/storage/index.js';
import { POST as fileUploadRoute } from '../src/app/api/contributions/[id]/file/route.js';

function nowIso() {
  return new Date().toISOString();
}

function makeRegistrationChallenge(id, overrides = {}) {
  return {
    ceremony_id: id,
    kind: 'registration',
    challenge: 'challenge-' + id,
    issued_at: nowIso(),
    expires_at: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
    origin: 'http://localhost:3000',
    rp_id: 'localhost',
    profile: { name: 'Test Contributor', role: 'Researcher' },
    pending_contributor_id: 'ctr_' + id.replace(/[^a-z0-9_]/gi, '_'),
    ...overrides,
  };
}

function makeAuthenticationChallenge(id, overrides = {}) {
  return {
    ceremony_id: id,
    kind: 'authentication',
    challenge: 'challenge-' + id,
    issued_at: nowIso(),
    expires_at: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
    origin: 'http://localhost:3000',
    rp_id: 'localhost',
    ...overrides,
  };
}

function fakeRegistrationVerifier(credentialId, origin = 'http://localhost:3000', rpID = 'localhost') {
  return async ({ expectedOrigin, expectedRPID }) => ({
    verified: expectedOrigin === origin && expectedRPID === rpID,
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

function fakeAuthenticationVerifier(origin = 'http://localhost:3000', rpID = 'localhost') {
  return async ({ expectedOrigin, expectedRPID, credential }) => ({
    verified: expectedOrigin === origin && expectedRPID === rpID && Boolean(credential.id),
    authenticationInfo: {
      credentialID: credential.id,
      newCounter: credential.counter + 1,
      userVerified: true,
      credentialDeviceType: 'singleDevice',
      credentialBackedUp: false,
      origin: expectedOrigin,
      rpID: expectedRPID,
    },
  });
}

async function registerContributor(store, challengeId, credentialId, overrides = {}) {
  const challenge = makeRegistrationChallenge(challengeId, overrides.challenge || {});
  const result = await createContributorRecord(
    store,
    {
      name: challenge.profile.name,
      role: challenge.profile.role,
    },
    challenge,
    { id: 'response-' + credentialId },
    { verifyRegistrationResponse: fakeRegistrationVerifier(credentialId, challenge.origin, challenge.rp_id) },
  );
  return { challenge, result };
}

async function authenticateContributor(store, challengeId, credentialId, contributor, credential, overrides = {}) {
  const challenge = makeAuthenticationChallenge(challengeId, overrides.challenge || {});
  const result = await resolveContributorFromPasskey(
    store,
    challenge,
    { id: credentialId },
    { verifyAuthenticationResponse: fakeAuthenticationVerifier(challenge.origin, challenge.rp_id) },
  );
  const session = {
    contributor_id: contributor.id,
    credential_hash: credential.credential_hash,
    credential_id: credential.credential_id,
  };
  return { challenge, result, session };
}

test('email normalization preserves plus addressing and dots', () => {
  const normalized = normalizeEmail('  Alice.Plus+tag@Example.COM  ');
  assert.equal(normalized, 'alice.plus+tag@example.com');
});

test('successful new registration persists contributor and credential', async () => {
  const store = createMemoryInvestigationStore();
  const { result } = await registerContributor(store, 'reg-1', 'cred-reg-1');
  assert.match(result.contributor.id, /^ctr_/);
  assert.equal(store.contributors.size, 1);
  assert.equal(store.credentials.size, 1);
  assert.equal(store.credentialsByHash.size, 1);
  assert.equal(result.contributor.name, 'Test Contributor');
});

test('registration challenge replay rejected', async () => {
  const store = createMemoryInvestigationStore();
  const challenge = makeRegistrationChallenge('reg-replay');
  await createContributorRecord(
    store,
    { name: challenge.profile.name, role: challenge.profile.role },
    challenge,
    { id: 'response-replay' },
    { verifyRegistrationResponse: fakeRegistrationVerifier('cred-replay') },
  );
  await assert.rejects(
    () => createContributorRecord(
      store,
      { name: challenge.profile.name, role: challenge.profile.role },
      challenge,
      { id: 'response-replay' },
      { verifyRegistrationResponse: fakeRegistrationVerifier('cred-replay') },
    ),
    (error) => error.status === 400,
  );
});

test('invalid origin rejected', async () => {
  const store = createMemoryInvestigationStore();
  const challenge = makeRegistrationChallenge('reg-origin', { origin: 'https://bad.example' });
  await assert.rejects(
    () => createContributorRecord(
      store,
      { name: challenge.profile.name, role: challenge.profile.role },
      challenge,
      { id: 'response-origin' },
      { verifyRegistrationResponse: async () => ({ verified: false }) },
    ),
    (error) => error.status === 400,
  );
});

test('invalid challenge rejected', async () => {
  const store = createMemoryInvestigationStore();
  const challenge = makeRegistrationChallenge('reg-invalid-kind', { kind: 'authentication' });
  await assert.rejects(
    () => createContributorRecord(
      store,
      { name: challenge.profile.name, role: challenge.profile.role },
      challenge,
      { id: 'response-invalid-kind' },
      { verifyRegistrationResponse: fakeRegistrationVerifier('cred-invalid-kind') },
    ),
    (error) => error.status === 400,
  );
});

test('successful returning sign-in resolves the existing contributor', async () => {
  const store = createMemoryInvestigationStore();
  const registration = await registerContributor(store, 'reg-returning', 'cred-returning');
  const credential = Array.from(store.credentialsByHash.values())[0];
  const auth = await authenticateContributor(store, 'aut-returning', 'cred-returning', registration.result.contributor, credential);
  assert.equal(auth.result.contributor.id, registration.result.contributor.id);
  const restored = await getCurrentContributorRecord(store, auth.session);
  assert.equal(restored.id, registration.result.contributor.id);
});

test('unknown credential rejected', async () => {
  const store = createMemoryInvestigationStore();
  const challenge = makeAuthenticationChallenge('aut-unknown');
  await assert.rejects(
    () => resolveContributorFromPasskey(
      store,
      challenge,
      { id: 'unknown-credential' },
      { verifyAuthenticationResponse: fakeAuthenticationVerifier() },
    ),
    (error) => error.status === 404,
  );
});

test('same credential resolves the same contributor and does not create duplicates', async () => {
  const store = createMemoryInvestigationStore();
  const first = await registerContributor(store, 'reg-dupe-1', 'cred-dupe');
  const secondChallenge = makeRegistrationChallenge('reg-dupe-2', {
    pending_contributor_id: 'ctr_reg-dupe-2',
    profile: { name: 'Second Name', role: 'Second Role' },
  });
  const second = await createContributorRecord(
    store,
    { name: secondChallenge.profile.name, role: secondChallenge.profile.role },
    secondChallenge,
    { id: 'response-dupe' },
    { verifyRegistrationResponse: fakeRegistrationVerifier('cred-dupe') },
  );
  assert.equal(second.contributor.id, first.result.contributor.id);
  assert.equal(store.contributors.size, 1);
});

test('authentication cannot create duplicate contributor', async () => {
  const store = createMemoryInvestigationStore();
  const registration = await registerContributor(store, 'reg-auth-dupe', 'cred-auth-dupe');
  const credential = Array.from(store.credentialsByHash.values())[0];
  const first = await authenticateContributor(store, 'aut-auth-dupe-1', 'cred-auth-dupe', registration.result.contributor, credential);
  const second = await authenticateContributor(store, 'aut-auth-dupe-2', 'cred-auth-dupe', registration.result.contributor, credential);
  assert.equal(first.result.contributor.id, second.result.contributor.id);
  assert.equal(store.contributors.size, 1);
});

test('tampered session rejected', () => {
  const token = createSignedSession({ contributor_id: 'ctr_01abc', credential_hash: 'a'.repeat(64) }, 'session-secret');
  const tampered = token.slice(0, -1) + (token.endsWith('a') ? 'b' : 'a');
  assert.equal(readSignedSession(tampered, 'session-secret'), null);
});

test('logout invalidates session', () => {
  const response = {
    cookies: {
      value: null,
      set(cookie) {
        this.value = cookie;
      },
    },
  };
  clearSessionCookie(response);
  assert.equal(response.cookies.value.name, 'ail_session');
  assert.equal(response.cookies.value.maxAge, 0);
});

test('returning contributor restores profile through the session payload', async () => {
  const store = createMemoryInvestigationStore();
  const registration = await registerContributor(store, 'reg-restore', 'cred-restore');
  const credential = Array.from(store.credentialsByHash.values())[0];
  const session = {
    contributor_id: registration.result.contributor.id,
    credential_hash: credential.credential_hash,
    credential_id: credential.credential_id,
  };
  const restored = await getCurrentContributorRecord(store, session);
  assert.equal(restored.id, registration.result.contributor.id);
});

test('resource availability and handoff readiness are derived from contribution type', async () => {
  const store = createMemoryInvestigationStore();
  const registration = await registerContributor(store, 'reg-readiness', 'cred-readiness');
  const credential = Array.from(store.credentialsByHash.values())[0];
  const session = {
    contributor_id: registration.result.contributor.id,
    credential_hash: credential.credential_hash,
  };

  const linkContribution = await createContributionRecord(store, session, {
    type: 'LINK',
    resource: { url: 'https://example.com/brief' },
    context: 'Link context',
  });
  const linkResource = await store.getResource(linkContribution.resource_id);
  assert.equal(linkResource.content_availability, 'URL_REFERENCE');
  assert.equal(linkResource.handoff_status, 'READY');

  const textContribution = await createContributionRecord(store, session, {
    type: 'TEXT',
    resource: { text: 'Inline text content' },
    context: 'Text context',
  });
  const textResource = await store.getResource(textContribution.resource_id);
  assert.equal(textResource.content_availability, 'INLINE_CONTENT');
  assert.equal(textResource.handoff_status, 'READY');

  const fileContribution = await createContributionRecord(store, session, {
    type: 'FILE',
    resource: { file: { name: 'evidence.pdf', mime_type: 'application/pdf', size: 1024 } },
    context: 'File context',
  });
  const fileResource = await store.getResource(fileContribution.resource_id);
  assert.equal(fileResource.content_availability, 'METADATA_ONLY');
  assert.equal(fileResource.handoff_status, 'CONTENT_REQUIRED');
  assert.equal(fileResource.payload.resource.file.name, 'evidence.pdf');
  assert.equal(fileResource.payload.resource.file.mime_type, 'application/pdf');
  assert.equal(fileResource.payload.resource.file.size, 1024);
});

test('same resource from two contributors deduplicates the resource record', async () => {
  const store = createMemoryInvestigationStore();
  const first = await registerContributor(store, 'reg-resource-1', 'cred-resource-1');
  await registerContributor(store, 'reg-resource-2', 'cred-resource-2');
  const credentials = Array.from(store.credentialsByHash.values());
  const firstSession = {
    contributor_id: first.result.contributor.id,
    credential_hash: credentials[0].credential_hash,
  };
  const secondSession = {
    contributor_id: credentials[1].contributor_id ? credentials[1].contributor_id : Array.from(store.contributors.keys())[1],
    credential_hash: credentials[1].credential_hash,
  };
  const firstContribution = await createContributionRecord(store, firstSession, {
    type: 'LINK',
    resource: { url: 'https://example.com/research' },
    context: 'One',
  });
  const secondContribution = await createContributionRecord(store, secondSession, {
    type: 'LINK',
    resource: { url: 'https://example.com/research' },
    context: 'Two',
  });
  assert.equal(firstContribution.resource_id, secondContribution.resource_id);
  assert.equal(store.resources.size, 1);
  assert.equal(store.contributions.size, 2);
  assert.equal((await getContributionRecord(store, firstContribution.id)).resource.url, 'https://example.com/research');
  assert.equal((await listContributionRecords(store, { limit: 5 })).length, 2);
});

test('resource file save and retrieve works in memory', async () => {
  const store = createMemoryInvestigationStore();
  const bytes = Buffer.from('%PDF-1.7\nresource-file');
  const descriptor = await store.saveResourceFile({
    resource_id: 'res_file_01',
    bytes,
    original_name: 'evidence.pdf',
    mime_type: 'application/pdf',
    size: bytes.length,
  });

  assert.equal(descriptor.resource_id, 'res_file_01');
  assert.equal(descriptor.storage_provider, 'MEMORY');
  assert.equal(descriptor.storage_key, 'data/resource-files/res_file_01/payload.pdf');
  assert.equal(descriptor.original_name, 'evidence.pdf');
  assert.equal(descriptor.mime_type, 'application/pdf');
  assert.equal(descriptor.size, bytes.length);

  const stored = await store.getResourceFile('res_file_01');
  assert.equal(stored.descriptor.content_sha256, descriptor.content_sha256);
  assert.equal(Buffer.compare(stored.bytes, bytes), 0);
});

test('resource file save rejects size mismatch', async () => {
  const store = createMemoryInvestigationStore();
  await assert.rejects(
    () => store.saveResourceFile({
      resource_id: 'res_file_02',
      bytes: Buffer.from('bytes'),
      original_name: 'note.txt',
      mime_type: 'text/plain',
      size: 999,
    }),
    (error) => error.code === 'RESOURCE_FILE_SIZE_MISMATCH',
  );
});

test('resource file save rejects unsupported mime types', async () => {
  const store = createMemoryInvestigationStore();
  await assert.rejects(
    () => store.saveResourceFile({
      resource_id: 'res_file_03',
      bytes: Buffer.from('hello'),
      original_name: 'archive.zip',
      mime_type: 'application/zip',
      size: 5,
    }),
    (error) => error.code === 'RESOURCE_FILE_TYPE_UNSUPPORTED',
  );
});

test('resource file save is idempotent for matching bytes and conflicts on different bytes', async () => {
  const store = createMemoryInvestigationStore();
  const firstBytes = Buffer.from('same file');
  const first = await store.saveResourceFile({
    resource_id: 'res_file_04',
    bytes: firstBytes,
    original_name: 'same.md',
    mime_type: 'text/markdown',
    size: firstBytes.length,
  });
  const second = await store.saveResourceFile({
    resource_id: 'res_file_04',
    bytes: Buffer.from('same file'),
    original_name: 'same.md',
    mime_type: 'text/markdown',
    size: firstBytes.length,
  });
  assert.equal(first.content_sha256, second.content_sha256);
  assert.equal(store.resourceFiles.size, 1);

  await assert.rejects(
    () => store.saveResourceFile({
      resource_id: 'res_file_04',
      bytes: Buffer.from('different file'),
      original_name: 'same.md',
      mime_type: 'text/markdown',
      size: 'different file'.length,
    }),
    (error) => error.code === 'RESOURCE_FILE_ALREADY_EXISTS',
  );
});

test('resource file retrieval detects tampering and missing records', async () => {
  const store = createMemoryInvestigationStore();
  const bytes = Buffer.from('tamper test');
  await store.saveResourceFile({
    resource_id: 'res_file_05',
    bytes,
    original_name: 'tamper.txt',
    mime_type: 'text/plain',
    size: bytes.length,
  });
  store.resourceFiles.get('res_file_05').bytes = Buffer.from('mutated');

  await assert.rejects(
    () => store.getResourceFile('res_file_05'),
    (error) => error.code === 'RESOURCE_FILE_INTEGRITY_FAILURE',
  );
  await assert.rejects(
    () => store.getResourceFile('res_file_missing'),
    (error) => error.code === 'RESOURCE_FILE_NOT_FOUND',
  );
});

test('github store saves and restores resource files with deterministic paths', async () => {
  const store = createGitHubInvestigationStore({ token: 'token', owner: 'owner', repo: 'repo', branch: 'main' });
  const files = new Map();
  const originalFetch = global.fetch;

  function makeResponse(status, body) {
    return {
      ok: status >= 200 && status < 300,
      status,
      text: async () => body,
      json: async () => JSON.parse(body),
    };
  }

  global.fetch = async (url, options = {}) => {
    const path = String(url).split('/contents/')[1];
    const method = options.method || 'GET';

    if (method === 'GET') {
      const entry = files.get(path);
      if (!entry) {
        return { ok: false, status: 404, text: async () => '', json: async () => ({}) };
      }

      if (entry.kind === 'json') {
        const content = Buffer.from(JSON.stringify(entry.value, null, 2) + '\n', 'utf8').toString('base64');
        return makeResponse(200, JSON.stringify({ content }));
      }

      return makeResponse(200, JSON.stringify({ content: entry.value.toString('base64') }));
    }

    if (method === 'PUT') {
      const payload = JSON.parse(options.body);
      const raw = Buffer.from(payload.content, 'base64');
      if (path.endsWith('/descriptor.json')) {
        files.set(path, { kind: 'json', value: JSON.parse(raw.toString('utf8')) });
      } else {
        files.set(path, { kind: 'bytes', value: raw });
      }
      return makeResponse(200, '{}');
    }

    return { ok: false, status: 405, text: async () => '', json: async () => ({}) };
  };

  try {
    const bytes = Buffer.from('github file payload');
    const descriptor = await store.saveResourceFile({
      resource_id: 'res_file_06',
      bytes,
      original_name: 'evidence.txt',
      mime_type: 'text/plain',
      size: bytes.length,
    });

    assert.equal(descriptor.storage_key, 'data/resource-files/res_file_06/payload.txt');
    assert.equal(files.has('data/resource-files/res_file_06/payload.txt'), true);
    assert.equal(files.has('data/resource-files/res_file_06/descriptor.json'), true);

    const retrieved = await store.getResourceFile('res_file_06');
    assert.equal(retrieved.descriptor.content_sha256, descriptor.content_sha256);
    assert.equal(Buffer.compare(retrieved.bytes, bytes), 0);
  } finally {
    global.fetch = originalFetch;
  }
});

test('browser-authentication tokens are not stored in localStorage', () => {
  const onboarding = fs.readFileSync(new URL('../src/features/onboarding/OnboardingFlow.tsx', import.meta.url), 'utf8');
  const contribute = fs.readFileSync(new URL('../src/features/contribute/ContributeFlow.tsx', import.meta.url), 'utf8');
  assert.equal(onboarding.includes('localStorage'), false);
  assert.equal(contribute.includes('localStorage'), false);
});

test('attachFileToContributionRecord attaches bytes to FILE contribution and leaves readiness unchanged', async () => {
  const store = createMemoryInvestigationStore();
  const registration = await registerContributor(store, 'reg-file-attach', 'cred-file-attach');
  const credentials = Array.from(store.credentialsByHash.values());
  const session = { contributor_id: registration.result.contributor.id, credential_hash: credentials[0].credential_hash };

  const bytes = Buffer.from('%PDF-1.7\nvalid payload content');
  const fileContribution = await createContributionRecord(store, session, {
    type: 'FILE',
    resource: { file: { name: 'report.pdf', mime_type: 'application/pdf', size: bytes.length } },
    context: 'Evidence report',
  });

  const uploadResult = await attachFileToContributionRecord(store, session, fileContribution.id, {
    bytes,
    original_name: 'report.pdf',
    mime_type: 'application/pdf',
    size: bytes.length,
  });

  assert.equal(uploadResult.resource_id, fileContribution.resource_id);
  assert.equal(uploadResult.stored, true);
  assert.equal(uploadResult.file.name, 'report.pdf');
  assert.equal(uploadResult.file.mime_type, 'application/pdf');
  assert.equal(uploadResult.file.size, bytes.length);
  assert.ok(uploadResult.file.content_sha256);
  assert.equal(uploadResult.github_token, undefined);
  assert.equal(uploadResult.storage_key, undefined);

  // Exact bytes retrievable
  const storedFile = await store.getResourceFile(fileContribution.resource_id);
  assert.equal(Buffer.compare(storedFile.bytes, bytes), 0);

  // Verification: FILE remains CONTENT_REQUIRED / METADATA_ONLY in Phase 07C-00C2A (Requirement 17)
  const resource = await store.getResource(fileContribution.resource_id);
  assert.equal(resource.content_availability, 'METADATA_ONLY');
  assert.equal(resource.handoff_status, 'CONTENT_REQUIRED');
});

test('attachFileToContributionRecord rejects unauthorized contributor', async () => {
  const store = createMemoryInvestigationStore();
  const ownerReg = await registerContributor(store, 'reg-owner', 'cred-owner');
  const attackerReg = await registerContributor(store, 'reg-attacker', 'cred-attacker');
  const credentials = Array.from(store.credentialsByHash.values());

  const ownerSession = { contributor_id: ownerReg.result.contributor.id, credential_hash: credentials[0].credential_hash };
  const attackerSession = { contributor_id: attackerReg.result.contributor.id, credential_hash: credentials[1].credential_hash };

  const bytes = Buffer.from('confidential file');
  const contribution = await createContributionRecord(store, ownerSession, {
    type: 'FILE',
    resource: { file: { name: 'secret.pdf', mime_type: 'application/pdf', size: bytes.length } },
  });

  await assert.rejects(
    () => attachFileToContributionRecord(store, attackerSession, contribution.id, {
      bytes,
      original_name: 'secret.pdf',
      mime_type: 'application/pdf',
      size: bytes.length,
    }),
    (error) => error.status === 403,
  );
});

test('attachFileToContributionRecord rejects non-FILE contributions', async () => {
  const store = createMemoryInvestigationStore();
  const registration = await registerContributor(store, 'reg-non-file', 'cred-non-file');
  const credentials = Array.from(store.credentialsByHash.values());
  const session = { contributor_id: registration.result.contributor.id, credential_hash: credentials[0].credential_hash };

  const linkContribution = await createContributionRecord(store, session, {
    type: 'LINK',
    resource: { url: 'https://example.com' },
  });

  const bytes = Buffer.from('some text bytes');
  await assert.rejects(
    () => attachFileToContributionRecord(store, session, linkContribution.id, {
      bytes,
      original_name: 'link.txt',
      mime_type: 'text/plain',
      size: bytes.length,
    }),
    (error) => error.status === 400 && error.code === 'CONTRIBUTION_NOT_FILE',
  );
});

test('attachFileToContributionRecord validates metadata size, MIME, and filename', async () => {
  const store = createMemoryInvestigationStore();
  const registration = await registerContributor(store, 'reg-meta-val', 'cred-meta-val');
  const credentials = Array.from(store.credentialsByHash.values());
  const session = { contributor_id: registration.result.contributor.id, credential_hash: credentials[0].credential_hash };

  const bytes = Buffer.from('hello world');
  const contribution = await createContributionRecord(store, session, {
    type: 'FILE',
    resource: { file: { name: 'hello.txt', mime_type: 'text/plain', size: 11 } },
  });

  // Size mismatch
  await assert.rejects(
    () => attachFileToContributionRecord(store, session, contribution.id, {
      bytes: Buffer.from('hello'), // length 5 != 11
      original_name: 'hello.txt',
      mime_type: 'text/plain',
      size: 5,
    }),
    (error) => error.code === 'RESOURCE_FILE_SIZE_MISMATCH',
  );

  // MIME mismatch
  await assert.rejects(
    () => attachFileToContributionRecord(store, session, contribution.id, {
      bytes,
      original_name: 'hello.txt',
      mime_type: 'image/png',
      size: 11,
    }),
    (error) => error.status === 415 && error.code === 'RESOURCE_FILE_TYPE_UNSUPPORTED',
  );

  // Filename mismatch
  await assert.rejects(
    () => attachFileToContributionRecord(store, session, contribution.id, {
      bytes,
      original_name: 'different.txt',
      mime_type: 'text/plain',
      size: 11,
    }),
    (error) => error.status === 400,
  );
});

test('attachFileToContributionRecord supports same-byte retry and rejects different-byte overwrite', async () => {
  const store = createMemoryInvestigationStore();
  const registration = await registerContributor(store, 'reg-idempotent', 'cred-idempotent');
  const credentials = Array.from(store.credentialsByHash.values());
  const session = { contributor_id: registration.result.contributor.id, credential_hash: credentials[0].credential_hash };

  const bytes = Buffer.from('idempotent content');
  const contribution = await createContributionRecord(store, session, {
    type: 'FILE',
    resource: { file: { name: 'test.txt', mime_type: 'text/plain', size: bytes.length } },
  });

  // First upload
  const res1 = await attachFileToContributionRecord(store, session, contribution.id, {
    bytes,
    original_name: 'test.txt',
    mime_type: 'text/plain',
    size: bytes.length,
  });
  assert.equal(res1.stored, true);

  // Retry with same bytes -> success
  const res2 = await attachFileToContributionRecord(store, session, contribution.id, {
    bytes: Buffer.from('idempotent content'),
    original_name: 'test.txt',
    mime_type: 'text/plain',
    size: bytes.length,
  });
  assert.equal(res2.stored, true);

  // Upload different bytes -> Conflict 409
  await assert.rejects(
    () => attachFileToContributionRecord(store, session, contribution.id, {
      bytes: Buffer.from('different content!'),
      original_name: 'test.txt',
      mime_type: 'text/plain',
      size: 'different content!'.length,
    }),
    (error) => error.status === 409 && error.code === 'RESOURCE_FILE_ALREADY_EXISTS',
  );
});

test('POST /api/contributions/[id]/file route behavior and error mapping', async () => {
  process.env.USE_MEMORY_STORE = 'true';
  process.env.IDENTITY_PEPPER = 'test-pepper';

  const store = createInvestigationStore();
  const registration = await registerContributor(store, 'reg-route-test', 'cred-route-test');
  const credentials = Array.from(store.credentialsByHash.values());
  const session = { contributor_id: registration.result.contributor.id, credential_hash: credentials[0].credential_hash };

  const bytes = Buffer.from('route test pdf payload');
  const fileContribution = await createContributionRecord(store, session, {
    type: 'FILE',
    resource: { file: { name: 'route.pdf', mime_type: 'application/pdf', size: bytes.length } },
  });

  // 1. Unauthenticated request -> 401
  const unauthRequest = new Request(`http://localhost:3000/api/contributions/${fileContribution.id}/file`, {
    method: 'POST',
  });
  const unauthRes = await fileUploadRoute(unauthRequest, { params: Promise.resolve({ id: fileContribution.id }) });
  assert.equal(unauthRes.status, 401);

  // 2. Authenticated request with valid session token
  const sessionToken = createSignedSession(session, 'test-pepper');

  // Missing file field -> 400
  const emptyForm = new FormData();
  emptyForm.append('other', 'value');
  const noFileReq = new Request(`http://localhost:3000/api/contributions/${fileContribution.id}/file`, {
    method: 'POST',
    headers: { cookie: `ail_session=${sessionToken}` },
    body: emptyForm,
  });
  const noFileRes = await fileUploadRoute(noFileReq, { params: Promise.resolve({ id: fileContribution.id }) });
  assert.equal(noFileRes.status, 400);

  // Successful multipart file upload
  const validForm = new FormData();
  const webFile = new File([bytes], 'route.pdf', { type: 'application/pdf' });
  validForm.append('file', webFile);

  const validReq = new Request(`http://localhost:3000/api/contributions/${fileContribution.id}/file`, {
    method: 'POST',
    headers: { cookie: `ail_session=${sessionToken}` },
    body: validForm,
  });

  const validRes = await fileUploadRoute(validReq, { params: Promise.resolve({ id: fileContribution.id }) });
  assert.equal(validRes.status, 200);

  const json = await validRes.json();
  assert.equal(json.resource_id, fileContribution.resource_id);
  assert.equal(json.stored, true);
  assert.equal(json.file.name, 'route.pdf');
  assert.equal(json.file.mime_type, 'application/pdf');
  assert.equal(json.file.size, bytes.length);
  assert.ok(json.file.content_sha256);
  assert.equal(json.github_token, undefined);
  assert.equal(json.storage_key, undefined);
});

