import { randomBytes } from 'node:crypto';
import { generateAuthenticationOptions, generateRegistrationOptions, verifyAuthenticationResponse, verifyRegistrationResponse } from '@simplewebauthn/server';
import { createCredentialHash, createRecordId } from '../storage/index.js';
import { createSignedSession, readSignedSession } from './session.js';

export const REGISTRATION_CEREMONY_COOKIE_NAME = 'ail_passkey_registration';
export const AUTHENTICATION_CEREMONY_COOKIE_NAME = 'ail_passkey_authentication';
export const PASSKEY_RP_NAME = 'ART Investigation Lab';
export const PASSKEY_CEREMONY_TTL_SECONDS = 5 * 60;

const consumedCeremonyIds = new Set();

function nowIso() {
  return new Date().toISOString();
}

function encodePath(value) {
  return Buffer.from(value).toString('base64url');
}

function decodePath(value) {
  return Buffer.from(value, 'base64url');
}

export function getWebAuthnRequestContext(request) {
  const url = new URL(request.url);
  return {
    origin: url.origin,
    rpID: url.hostname,
  };
}

export function createCeremonyChallenge() {
  return randomBytes(32).toString('base64url');
}

export function createCeremonyPayload(kind, extras = {}, ttlSeconds = PASSKEY_CEREMONY_TTL_SECONDS) {
  const issuedAt = nowIso();
  return {
    ceremony_id: createRecordId(kind === 'registration' ? 'reg' : 'aut'),
    kind,
    challenge: createCeremonyChallenge(),
    issued_at: issuedAt,
    expires_at: new Date(Date.now() + ttlSeconds * 1000).toISOString(),
    ...extras,
  };
}

export function setCeremonyCookie(response, cookieName, payload, secret, options = {}) {
  response.cookies.set({
    name: cookieName,
    value: createSignedSession(payload, secret),
    httpOnly: true,
    sameSite: 'lax',
    secure: options.secure ?? process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: options.maxAge ?? PASSKEY_CEREMONY_TTL_SECONDS,
  });
}

export function clearCeremonyCookie(response, cookieName) {
  response.cookies.set({
    name: cookieName,
    value: '',
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: 0,
  });
}

function readCookieValue(request, cookieName) {
  const cookieHeader = request.headers.get('cookie') || '';
  const match = cookieHeader
    .split(';')
    .map((segment) => segment.trim())
    .find((segment) => segment.startsWith(cookieName + '='));

  return match ? match.slice(cookieName.length + 1) : '';
}

export function readCeremonyCookieFromRequest(request, cookieName, secret) {
  const token = readCookieValue(request, cookieName);
  if (!token) {
    return null;
  }

  const payload = readSignedSession(token, secret);
  if (!payload || typeof payload !== 'object') {
    return null;
  }

  const expiresAt = Date.parse(payload.expires_at || '');
  if (!Number.isFinite(expiresAt) || expiresAt < Date.now()) {
    return null;
  }

  return payload;
}

export function isCeremonyConsumed(ceremonyId) {
  return consumedCeremonyIds.has(ceremonyId);
}

export function consumeCeremony(ceremonyId) {
  if (consumedCeremonyIds.has(ceremonyId)) {
    return false;
  }
  consumedCeremonyIds.add(ceremonyId);
  return true;
}

export function serializeCredentialRecord({ credential, registrationInfo, contributorId, challenge }) {
  return {
    id: createCredentialHash(credential.id),
    credential_hash: createCredentialHash(credential.id),
    credential_id: credential.id,
    contributor_id: contributorId,
    public_key: encodePath(Buffer.from(credential.publicKey)),
    counter: credential.counter,
    transports: credential.transports || [],
    credential_device_type: registrationInfo?.credentialDeviceType,
    credential_backed_up: registrationInfo?.credentialBackedUp,
    user_verified: registrationInfo?.userVerified,
    origin: registrationInfo?.origin || challenge.origin,
    rp_id: registrationInfo?.rpID || challenge.rp_id,
    created_at: challenge.issued_at,
    updated_at: challenge.issued_at,
    last_used_at: challenge.issued_at,
  };
}

export function serializeCredentialIndex(credentialRecord) {
  return {
    credential_hash: credentialRecord.credential_hash,
    credential_id: credentialRecord.credential_id,
    contributor_id: credentialRecord.contributor_id,
    created_at: credentialRecord.created_at,
    updated_at: credentialRecord.updated_at,
  };
}

export function deserializeCredentialRecord(record) {
  if (!record) {
    return null;
  }

  return {
    ...record,
    publicKey: record.public_key ? decodePath(record.public_key) : undefined,
  };
}

export function buildSessionPayload(contributor, credentialRecord) {
  return {
    contributor_id: contributor.id,
    credential_hash: credentialRecord.credential_hash,
    credential_id: credentialRecord.credential_id,
    issued_at: nowIso(),
  };
}

export async function generatePasskeyRegistrationOptions({ name, role, rpID, challenge, contributorId }) {
  return generateRegistrationOptions({
    rpName: PASSKEY_RP_NAME,
    rpID,
    userName: name,
    userDisplayName: name + ' · ' + role,
    userID: Buffer.from(contributorId, 'utf8'),
    challenge,
    attestationType: 'none',
    authenticatorSelection: {
      residentKey: 'preferred',
      userVerification: 'preferred',
    },
  });
}

export async function generatePasskeyAuthenticationOptions({ rpID, challenge }) {
  return generateAuthenticationOptions({
    rpID,
    challenge,
    userVerification: 'preferred',
  });
}

export async function verifyPasskeyRegistrationResponse({ response, expectedChallenge, expectedOrigin, expectedRPID }) {
  return verifyRegistrationResponse({
    response,
    expectedChallenge,
    expectedOrigin,
    expectedRPID,
    expectedType: 'webauthn.create',
    requireUserPresence: true,
    requireUserVerification: false,
  });
}

export async function verifyPasskeyAuthenticationResponse({ response, expectedChallenge, expectedOrigin, expectedRPID, credential }) {
  return verifyAuthenticationResponse({
    response,
    expectedChallenge,
    expectedOrigin,
    expectedRPID,
    credential,
    expectedType: 'webauthn.get',
    requireUserVerification: false,
  });
}