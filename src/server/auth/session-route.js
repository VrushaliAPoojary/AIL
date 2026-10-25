import { cookies } from 'next/headers';
import { readSignedSession, SESSION_COOKIE_NAME } from './session.js';

export async function readSessionFromCookies(secret) {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value || '';
  return readSignedSession(token, secret);
}
