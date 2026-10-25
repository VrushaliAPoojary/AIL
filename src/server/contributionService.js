import { createActivityId, createContributionId, createContributorId, createCredentialHash, createResourceId, createResourceFingerprint, normalizeEmail, normalizeResourcePayloadForStorage } from './auth/identity.js';
import { buildSessionPayload, consumeCeremony, deserializeCredentialRecord, generatePasskeyAuthenticationOptions, generatePasskeyRegistrationOptions, getWebAuthnRequestContext, serializeCredentialIndex, serializeCredentialRecord, verifyPasskeyAuthenticationResponse, verifyPasskeyRegistrationResponse, createCeremonyPayload } from './auth/webauthn.js';
import { NotFoundError, PersistenceError, ValidationError, AppError, ResourceFileSizeMismatchError, ResourceFileTypeUnsupportedError } from './storage/errors.js';
import { normalizeContext, normalizeIdempotencyKey, validateContributorId, validateContributorProfileInput, validateContributionId, validateContributionInput, validateContributionListOptions } from './storage/validation.js';

function nowIso() {
  return new Date().toISOString();
}

function hydrateResourceRecord(resource) {
  if (!resource) {
    return null;
  }
  const payload = resource.payload?.resource || resource.resource || null;
  const readiness = determineResourceReadiness(resource.type);
  if (payload) {
    return {
      ...resource,
      ...payload,
      content_availability: resource.content_availability || readiness.content_availability,
      handoff_status: resource.handoff_status || readiness.handoff_status,
    };
  }
  return {
    ...resource,
    content_availability: resource.content_availability || readiness.content_availability,
    handoff_status: resource.handoff_status || readiness.handoff_status,
  };
}

function determineResourceReadiness(type) {
  const normalized = String(type || '').toUpperCase();
  if (normalized === 'LINK') {
    return {
      content_availability: 'URL_REFERENCE',
      handoff_status: 'READY',
    };
  }
  if (normalized === 'TEXT' || normalized === 'INSIGHT') {
    return {
      content_availability: 'INLINE_CONTENT',
      handoff_status: 'READY',
    };
  }
  return {
    content_availability: 'METADATA_ONLY',
    handoff_status: 'CONTENT_REQUIRED',
  };
}

async function hydrateContributionRecord(store, contribution) {
  if (!contribution) {
    return null;
  }
  const resource = contribution.resource_id ? await store.getResource(contribution.resource_id) : null;
  return {
    ...contribution,
    ...(resource ? { resource: hydrateResourceRecord(resource) } : {}),
  };
}

async function getContributorBySession(store, session) {
  if (!session?.contributor_id) {
    throw new NotFoundError('Contributor not found.');
  }
  const contributor = await store.getContributor(session.contributor_id);
  if (contributor) {
    return contributor;
  }
  if (session.credential_hash) {
    const restored = await store.getContributorByCredentialHash(session.credential_hash);
    if (restored) {
      return restored;
    }
  }
  throw new NotFoundError('Contributor not found.');
}

async function resolveResourceRecord(store, type, resource) {
  const fingerprint = createResourceFingerprint(type, resource);
  const existing = await store.getResourceByFingerprint(fingerprint);
  if (existing) {
    return existing;
  }
  const timestamp = nowIso();
  const payload = normalizeResourcePayloadForStorage(type, resource);
  const readiness = determineResourceReadiness(type);
  const resourceRecord = {
    id: createResourceId(),
    type,
    fingerprint,
    payload,
    ...readiness,
    created_at: timestamp,
    updated_at: timestamp,
  };
  const indexRecord = {
    fingerprint,
    resource_id: resourceRecord.id,
    resource: resourceRecord,
    created_at: timestamp,
    updated_at: timestamp,
  };
  try {
    await store.createResource(resourceRecord);
  } catch (error) {
    const winner = await store.getResourceByFingerprint(fingerprint);
    if (winner) {
      return winner;
    }
    throw error;
  }
  try {
    await store.createResourceFingerprintIndex(fingerprint, indexRecord);
  } catch (error) {
    const winner = await store.getResourceByFingerprint(fingerprint);
    if (winner) {
      return winner;
    }
    throw error;
  }
  return resourceRecord;
}

export function createPasskeyRegistrationCeremony(input, request) {
  const profile = validateContributorProfileInput(input);
  const { origin, rpID } = getWebAuthnRequestContext(request);
  const pendingContributorId = createContributorId();
  const challenge = createCeremonyPayload('registration', {
    origin,
    rp_id: rpID,
    profile,
    pending_contributor_id: pendingContributorId,
  });
  return generatePasskeyRegistrationOptions({
    name: profile.name,
    role: profile.role,
    rpID,
    challenge: Buffer.from(challenge.challenge, 'base64url'),
    contributorId: pendingContributorId,
  }).then((options) => ({ options, challenge, profile, pendingContributorId, origin, rpID }));
}

export function createPasskeyAuthenticationCeremony(request) {
  const { origin, rpID } = getWebAuthnRequestContext(request);
  const challenge = createCeremonyPayload('authentication', { origin, rp_id: rpID });
  return generatePasskeyAuthenticationOptions({ rpID, challenge: Buffer.from(challenge.challenge, 'base64url') }).then((options) => ({ options, challenge, origin, rpID }));
}

export async function createContributorRecord(store, input, challenge, registrationResponse, options = {}) {
  const profile = validateContributorProfileInput(input);
  if (!challenge || challenge.kind !== 'registration') {
    throw new ValidationError('Registration ceremony is required.');
  }
  if (!consumeCeremony(challenge.ceremony_id)) {
    throw new ValidationError('Registration challenge already used.');
  }
  const verifyRegistration = options.verifyRegistrationResponse || verifyPasskeyRegistrationResponse;
  let verified;
  try {
    verified = await verifyRegistration({
      response: registrationResponse,
      expectedChallenge: challenge.challenge,
      expectedOrigin: challenge.origin,
      expectedRPID: challenge.rp_id,
    });
  } catch (verifyError) {
    throw new ValidationError(verifyError instanceof Error ? verifyError.message : 'Passkey registration could not be verified.');
  }
  if (!verified.verified) {
    throw new ValidationError('Passkey registration could not be verified.');
  }
  const credentialHash = createCredentialHash(verified.registrationInfo.credential.id);
  const existingContributor = await store.getContributorByCredentialHash(credentialHash);
  if (existingContributor) {
    const existingCredential = await store.getCredentialByHash(credentialHash);
    return { contributor: existingContributor, credential: existingCredential, registrationInfo: verified.registrationInfo };
  }
  const timestamp = nowIso();
  const contributor = {
    id: challenge.pending_contributor_id || createContributorId(),
    name: profile.name,
    role: profile.role,
    created_at: timestamp,
    updated_at: timestamp,
  };
  const credentialRecord = serializeCredentialRecord({
    credential: {
      id: verified.registrationInfo.credential.id,
      publicKey: verified.registrationInfo.credential.publicKey,
      counter: verified.registrationInfo.credential.counter,
      transports: verified.registrationInfo.credential.transports,
    },
    registrationInfo: verified.registrationInfo,
    contributorId: contributor.id,
    challenge,
  });
  const credentialIndex = serializeCredentialIndex(credentialRecord);
  try {
    await store.createCredentialIndex(credentialHash, credentialIndex);
  } catch (error) {
    const winnerContributor = await store.getContributorByCredentialHash(credentialHash);
    const winnerCredential = await store.getCredentialByHash(credentialHash);
    if (winnerContributor) {
      return { contributor: winnerContributor, credential: winnerCredential, registrationInfo: verified.registrationInfo };
    }
    throw error;
  }
  try {
    await store.createContributor(contributor);
  } catch (error) {
    const winnerContributor = await store.getContributorByCredentialHash(credentialHash);
    const winnerCredential = await store.getCredentialByHash(credentialHash);
    if (winnerContributor) {
      return { contributor: winnerContributor, credential: winnerCredential, registrationInfo: verified.registrationInfo };
    }
    throw error;
  }
  try {
    await store.createCredential(credentialRecord);
  } catch (error) {
    const winnerContributor = await store.getContributorByCredentialHash(credentialHash);
    const winnerCredential = await store.getCredentialByHash(credentialHash);
    if (winnerContributor) {
      return { contributor: winnerContributor, credential: winnerCredential, registrationInfo: verified.registrationInfo };
    }
    throw error;
  }
  return { contributor, credential: credentialRecord, registrationInfo: verified.registrationInfo };
}

export async function resolveContributorFromPasskey(store, challenge, authenticationResponse, options = {}) {
  if (!challenge || challenge.kind !== 'authentication') {
    throw new ValidationError('Authentication ceremony is required.');
  }
  if (!consumeCeremony(challenge.ceremony_id)) {
    throw new ValidationError('Authentication challenge already used.');
  }
  const credentialHash = createCredentialHash(authenticationResponse.id);
  const storedCredential = await store.getCredentialByHash(credentialHash);
  if (!storedCredential) {
    throw new NotFoundError('Unknown credential.');
  }
  const credential = deserializeCredentialRecord(storedCredential);
  const verifyAuthentication = options.verifyAuthenticationResponse || verifyPasskeyAuthenticationResponse;
  let verified;
  try {
    verified = await verifyAuthentication({
      response: authenticationResponse,
      expectedChallenge: challenge.challenge,
      expectedOrigin: challenge.origin,
      expectedRPID: challenge.rp_id,
      credential: {
        id: credential.credential_id,
        publicKey: credential.publicKey,
        counter: credential.counter,
        transports: credential.transports,
      },
    });
  } catch (verifyError) {
    throw new ValidationError(verifyError instanceof Error ? verifyError.message : 'Passkey authentication could not be verified.');
  }
  if (!verified.verified) {
    throw new ValidationError('Passkey authentication could not be verified.');
  }
  const contributor = await store.getContributor(storedCredential.contributor_id);
  if (!contributor) {
    throw new NotFoundError('Contributor not found.');
  }
  return { contributor, credential: storedCredential, authenticationInfo: verified.authenticationInfo };
}

export async function getContributorRecord(store, id) {
  const contributorId = validateContributorId(id);
  const contributor = await store.getContributor(contributorId);
  if (contributor) {
    return contributor;
  }
  throw new NotFoundError('Contributor not found.');
}

export async function getCurrentContributorRecord(store, session) {
  return getContributorBySession(store, session);
}

export async function createContributionRecord(store, contributor, input) {
  const payload = validateContributionInput(input);
  const owner = await getContributorBySession(store, contributor);
  const resource = await resolveResourceRecord(store, payload.type, payload.resource);
  const timestamp = nowIso();
  const context = normalizeContext(payload.context);
  const contribution = {
    id: createContributionId(),
    contributor_id: owner.id,
    contributor_name: owner.name,
    resource_id: resource.id,
    type: payload.type,
    ...(context ? { context } : {}),
    status: 'RECEIVED',
    created_at: timestamp,
    updated_at: timestamp,
  };
  const saved = await store.createContribution(contribution);
  const activity = {
    id: createActivityId(),
    type: 'CONTRIBUTION_CREATED',
    contributor_id: owner.id,
    contributor_name: owner.name,
    contribution_id: saved.id,
    resource_id: resource.id,
    created_at: timestamp,
  };
  try {
    await store.createActivity(activity);
  } catch (error) {
    if (typeof store.deleteContribution === 'function') {
      try {
        await store.deleteContribution(saved.id);
      } catch {
        // Leave the contribution in place if rollback fails; the browser still gets a safe error.
      }
    }
    if (error instanceof ValidationError) {
      throw error;
    }
    throw new PersistenceError('Unable to save activity event.', 500);
  }
  return hydrateContributionRecord(store, saved);
}

export async function getContributionRecord(store, id) {
  const contributionId = validateContributionId(id);
  const contribution = await store.getContribution(contributionId);
  if (!contribution) {
    throw new NotFoundError('Contribution not found.');
  }
  return hydrateContributionRecord(store, contribution);
}

export async function listContributionRecords(store, options = {}) {
  const { limit } = validateContributionListOptions(options);
  const contributions = await store.listContributions({ limit });
  return Promise.all(contributions.map((entry) => hydrateContributionRecord(store, entry)));
}

export async function attachFileToContributionRecord(store, session, contributionId, uploadedFile) {
  if (!session) {
    throw new AppError('Not authenticated.', 401, 'UNAUTHORIZED');
  }
  const owner = await getContributorBySession(store, session);
  const validatedId = validateContributionId(contributionId);
  const contribution = await store.getContribution(validatedId);
  if (!contribution) {
    throw new NotFoundError('Contribution not found.');
  }

  if (contribution.contributor_id !== owner.id) {
    throw new AppError('Contribution belongs to another contributor.', 403, 'FORBIDDEN');
  }

  if (contribution.type !== 'FILE') {
    throw new AppError('Contribution type is not FILE.', 400, 'CONTRIBUTION_NOT_FILE');
  }

  if (!contribution.resource_id) {
    throw new NotFoundError('Resource not found.');
  }

  const resourceRecord = await store.getResource(contribution.resource_id);
  if (!resourceRecord) {
    throw new NotFoundError('Resource not found.');
  }

  const fileMeta = resourceRecord.payload?.resource?.file || resourceRecord.resource?.file || null;
  if (!fileMeta) {
    throw new ValidationError('Resource metadata for FILE is missing.');
  }

  if (!uploadedFile || typeof uploadedFile !== 'object') {
    throw new ValidationError('Uploaded file is required.');
  }

  const bytes = uploadedFile.bytes;
  if (!Buffer.isBuffer(bytes) && !(bytes instanceof Uint8Array)) {
    throw new ValidationError('File bytes must be provided.');
  }

  const originalName = String(uploadedFile.original_name || uploadedFile.name || '').trim();
  if (!originalName) {
    throw new ValidationError('original_name is required.');
  }

  const mimeType = String(uploadedFile.mime_type || uploadedFile.type || '').trim().toLowerCase();
  if (!mimeType) {
    throw new ValidationError('mime_type is required.');
  }

  const actualSize = bytes.length;

  if (fileMeta.size !== undefined && fileMeta.size !== null && fileMeta.size !== '') {
    const expectedSize = Number(fileMeta.size);
    if (actualSize !== expectedSize) {
      throw new ResourceFileSizeMismatchError('Uploaded file size does not match stored resource metadata.', {
        expected_size: expectedSize,
        actual_size: actualSize,
      });
    }
  }

  if (fileMeta.mime_type) {
    const expectedMime = String(fileMeta.mime_type).trim().toLowerCase();
    const normalizedActualMime = mimeType.split(';')[0];
    const normalizedExpectedMime = expectedMime.split(';')[0];
    if (normalizedActualMime !== normalizedExpectedMime) {
      throw new ResourceFileTypeUnsupportedError('Uploaded file MIME type does not match stored resource metadata.', {
        expected_mime_type: expectedMime,
        actual_mime_type: mimeType,
      });
    }
  }

  if (fileMeta.name) {
    const expectedName = String(fileMeta.name).trim();
    if (originalName !== expectedName) {
      throw new ValidationError('Uploaded filename does not match stored resource metadata.', {
        expected_name: expectedName,
        actual_name: originalName,
      });
    }
  }

  const descriptor = await store.saveResourceFile({
    resource_id: resourceRecord.id,
    bytes,
    original_name: originalName,
    mime_type: mimeType,
    size: actualSize,
  });

  return {
    resource_id: resourceRecord.id,
    stored: true,
    file: {
      name: descriptor.original_name,
      mime_type: descriptor.mime_type,
      size: descriptor.size,
      content_sha256: descriptor.content_sha256,
    },
  };
}

export { buildSessionPayload };