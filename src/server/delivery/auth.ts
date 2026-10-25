import 'server-only';
import { cookies } from 'next/headers';
import { createAdminSessionToken, verifyAdminCredentials, verifyAdminSessionToken } from './authCore';

const COOKIE = 'p02_admin_session';
const SESSION_SECONDS = 8 * 60 * 60;
const loginAttempts = new Map<string, { count: number; windowStartedAt: number; blockedUntil: number }>();

export function isLoginRateLimited(key: string) {
  const entry = loginAttempts.get(key);
  if (!entry) return false;
  if (Date.now() - entry.windowStartedAt >= 15 * 60_000) {
    loginAttempts.delete(key);
    return false;
  }
  return entry.blockedUntil > Date.now();
}

export function recordLoginFailure(key: string) {
  const now = Date.now();
  const old = loginAttempts.get(key);
  const sameWindow = Boolean(old && now - old.windowStartedAt < 15 * 60_000);
  const count = (sameWindow ? old!.count : 0) + 1;
  const windowStartedAt = sameWindow ? old!.windowStartedAt : now;
  loginAttempts.set(key, { count, windowStartedAt, blockedUntil: count >= 5 ? now + 15 * 60_000 : 0 });
}

export function clearLoginFailures(key: string) {
  loginAttempts.delete(key);
}

export function adminCookieOptions() {
  return { httpOnly: true, secure: process.env.NODE_ENV === 'production', sameSite: 'strict' as const, path: '/', maxAge: SESSION_SECONDS };
}

export function createAdminToken(username: string) {
  const secret = process.env.P02_SESSION_SECRET;
  if (!secret) throw new Error('P02 admin sessions are not configured.');
  return createAdminSessionToken(username, secret, Date.now(), SESSION_SECONDS);
}

export async function requireP02Admin() {
  const secret = process.env.P02_SESSION_SECRET;
  if (!secret) return false;
  const cookieStore = await cookies();
  const token = cookieStore.get(COOKIE)?.value || '';
  return Boolean(verifyAdminSessionToken(token, secret));
}

export const P02_ADMIN_COOKIE = COOKIE;
export { verifyAdminCredentials };
