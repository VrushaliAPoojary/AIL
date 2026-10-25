import { createHmac, timingSafeEqual } from 'node:crypto';

function equalSecret(left: string, right: string) {
  const a = Buffer.from(left);
  const b = Buffer.from(right);
  return a.length === b.length && timingSafeEqual(a, b);
}

export function verifyAdminCredentials(username: unknown, password: unknown, expectedUser = process.env.P02_ADMIN_USERNAME, expectedPassword = process.env.P02_ADMIN_PASSWORD) {
  if (!expectedUser || !expectedPassword || typeof username !== 'string' || typeof password !== 'string' || username.length > 120 || password.length > 256) return false;
  return equalSecret(username, expectedUser) && equalSecret(password, expectedPassword);
}

export function createAdminSessionToken(username: string, secret: string, now = Date.now(), ttlSeconds = 8 * 60 * 60) {
  const body = Buffer.from(JSON.stringify({ username, role: 'admin', exp: now + ttlSeconds * 1000 })).toString('base64url');
  const signature = createHmac('sha256', secret).update(body).digest('base64url');
  return `${body}.${signature}`;
}

export function verifyAdminSessionToken(token: string, secret: string, now = Date.now()) {
  const [body, supplied] = token.split('.', 2);
  if (!body || !supplied) return null;
  const expected = createHmac('sha256', secret).update(body).digest('base64url');
  if (!equalSecret(supplied, expected)) return null;
  try {
    const payload = JSON.parse(Buffer.from(body, 'base64url').toString('utf8'));
    if (payload.role !== 'admin' || typeof payload.username !== 'string' || !Number.isFinite(payload.exp) || payload.exp <= now) return null;
    return { username: payload.username as string, role: 'admin' as const, exp: payload.exp as number };
  } catch { return null; }
}
