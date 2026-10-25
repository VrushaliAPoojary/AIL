import { createHmac, timingSafeEqual } from 'node:crypto';

export const SESSION_COOKIE_NAME = 'ail_session';

function encodeSegment(value) {
  return Buffer.from(JSON.stringify(value), 'utf8').toString('base64url');
}

function decodeSegment(value) {
  return JSON.parse(Buffer.from(value, 'base64url').toString('utf8'));
}

function sign(value, secret) {
  return createHmac('sha256', secret).update(value, 'utf8').digest('base64url');
}

function safeEqual(left, right) {
  const leftBuffer = Buffer.from(left, 'utf8');
  const rightBuffer = Buffer.from(right, 'utf8');
  if (leftBuffer.length !== rightBuffer.length) {
    return false;
  }
  return timingSafeEqual(leftBuffer, rightBuffer);
}

export function createSignedSession(payload, secret) {
  const body = encodeSegment(payload);
  const signature = sign(body, secret);
  return `${body}.${signature}`;
}

export function readSignedSession(token, secret) {
  if (typeof token !== 'string' || !token.includes('.')) {
    return null;
  }

  const [body, signature] = token.split('.', 2);
  if (!body || !signature) {
    return null;
  }

  const expected = sign(body, secret);
  if (!safeEqual(signature, expected)) {
    return null;
  }

  try {
    return decodeSegment(body);
  } catch {
    return null;
  }
}

export function parseCookieHeader(cookieHeader) {
  const cookies = new Map();
  const segments = String(cookieHeader || '').split(';');
  for (const segment of segments) {
    const index = segment.indexOf('=');
    if (index === -1) {
      continue;
    }
    const key = segment.slice(0, index).trim();
    const value = segment.slice(index + 1).trim();
    if (key) {
      cookies.set(key, value);
    }
  }
  return cookies;
}

export function readSessionTokenFromRequest(request) {
  return parseCookieHeader(request.headers.get('cookie')).get(SESSION_COOKIE_NAME) || '';
}

export function readSessionFromRequest(request, secret) {
  return readSignedSession(readSessionTokenFromRequest(request), secret);
}

export function setSessionCookie(response, payload, secret, options = {}) {
  response.cookies.set({
    name: SESSION_COOKIE_NAME,
    value: createSignedSession(payload, secret),
    httpOnly: true,
    sameSite: 'lax',
    secure: options.secure ?? process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: options.maxAge ?? 60 * 60 * 24 * 30,
  });
}

export function clearSessionCookie(response) {
  response.cookies.set({
    name: SESSION_COOKIE_NAME,
    value: '',
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: 0,
  });
}
