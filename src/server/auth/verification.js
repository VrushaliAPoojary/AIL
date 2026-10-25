import { randomInt } from 'node:crypto';
import { createEmailKey, maskEmail, normalizeEmail } from './identity.js';
import { createSignedSession, readSignedSession, SESSION_COOKIE_NAME, setSessionCookie } from './session.js';

export const EMAIL_VERIFICATION_COOKIE_NAME = 'ail_email_verification';
const VERIFICATION_TTL_SECONDS = 15 * 60;

function encode(value) {
  return Buffer.from(JSON.stringify(value), 'utf8').toString('base64url');
}

function decode(value) {
  return JSON.parse(Buffer.from(value, 'base64url').toString('utf8'));
}

function sign(value, secret) {
  return createSignedSession({ value }, secret).split('.', 2)[1];
}

function hashCode({ challengeId, emailKey, code }, secret) {
  return sign(`${challengeId}:${emailKey}:${code}`, secret);
}

export function createVerificationChallenge({ email, secret, ttlSeconds = VERIFICATION_TTL_SECONDS }) {
  const normalizedEmail = normalizeEmail(email);
  const emailKey = createEmailKey(normalizedEmail, secret);
  const challengeId = `ver_${Date.now().toString(36)}_${randomInt(0, 1_000_000).toString().padStart(6, '0')}`;
  const verificationCode = randomInt(0, 1_000_000).toString().padStart(6, '0');
  const issuedAt = new Date().toISOString();
  const expiresAt = new Date(Date.now() + ttlSeconds * 1000).toISOString();
  const payload = {
    challenge_id: challengeId,
    email_normalized: normalizedEmail,
    email_key: emailKey,
    email_label: maskEmail(normalizedEmail),
    code_hash: hashCode({ challengeId, emailKey, code: verificationCode }, secret),
    issued_at: issuedAt,
    expires_at: expiresAt,
  };

  return {
    verificationCode,
    payload,
  };
}

export function encodeVerificationChallenge(payload, secret) {
  const body = encode(payload);
  const signature = sign(body, secret);
  return `${body}.${signature}`;
}

export function setVerificationCookie(response, payload, secret) {
  response.cookies.set({
    name: EMAIL_VERIFICATION_COOKIE_NAME,
    value: encodeVerificationChallenge(payload, secret),
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: VERIFICATION_TTL_SECONDS,
  });
}

export function clearVerificationCookie(response) {
  response.cookies.set({
    name: EMAIL_VERIFICATION_COOKIE_NAME,
    value: '',
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: 0,
  });
}

export function readVerificationChallengeFromRequest(request, secret) {
  const rawCookie = request.headers.get('cookie') || '';
  const cookie = rawCookie
    .split(';')
    .map((segment) => segment.trim())
    .find((segment) => segment.startsWith(`${EMAIL_VERIFICATION_COOKIE_NAME}=`));

  if (!cookie) {
    return null;
  }

  const token = cookie.slice(EMAIL_VERIFICATION_COOKIE_NAME.length + 1);
  const session = readSignedSession(token, secret);
  if (!session || !session.value) {
    return null;
  }

  const payload = session.value;
  if (!payload || typeof payload !== 'object') {
    return null;
  }

  const expiresAt = Date.parse(payload.expires_at || '');
  if (!Number.isFinite(expiresAt) || expiresAt < Date.now()) {
    return null;
  }

  return payload;
}

export function verifyChallengeCode(payload, code, secret) {
  if (!payload || !code) {
    return false;
  }

  const expected = hashCode({
    challengeId: payload.challenge_id,
    emailKey: payload.email_key,
    code,
  }, secret);

  return expected === payload.code_hash;
}

export function buildSessionPayload(contributor, emailKey) {
  return {
    contributor_id: contributor.id,
    contributor_email_key: emailKey,
    contributor_name: contributor.name,
    issued_at: new Date().toISOString(),
  };
}
