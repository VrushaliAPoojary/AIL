import { createHash, createHmac } from 'node:crypto';
import { createRecordId } from '../storage/ids.js';

function normalizeText(value) {
  return typeof value === 'string' ? value.trim() : '';
}

function sortValue(value) {
  if (Array.isArray(value)) {
    return value.map(sortValue);
  }

  if (!value || typeof value !== 'object') {
    return value;
  }

  const sorted = {};
  for (const key of Object.keys(value).sort()) {
    sorted[key] = sortValue(value[key]);
  }
  return sorted;
}

export function normalizeEmail(email) {
  return normalizeText(email).toLowerCase();
}

export function createEmailKey(normalizedEmail, pepper) {
  return createHmac('sha256', pepper).update(normalizedEmail, 'utf8').digest('hex');
}

export function createContributorId() {
  return createRecordId('ctr');
}

export function createResourceId() {
  return createRecordId('res');
}

export function createContributionId() {
  return createRecordId('con');
}

export function createActivityId() {
  return createRecordId('evt');
}

export function createFingerprint(value) {
  return createHash('sha256').update(value, 'utf8').digest('hex');
}

export function createCredentialHash(credentialId) {
  return createFingerprint(String(credentialId || ''));
}

function normalizeResourcePayload(type, resource) {
  if (type === 'LINK') {
    const url = normalizeText(resource?.url);
    if (!url) {
      return { type, resource: { url: '' } };
    }
    return { type, resource: { url: new URL(url).toString() } };
  }

  if (type === 'TEXT' || type === 'INSIGHT') {
    return { type, resource: { text: normalizeText(resource?.text) } };
  }

  if (type === 'FILE') {
    const file = resource?.file || {};
    const payload = {
      name: normalizeText(file.name),
      ...(file.mime_type ? { mime_type: normalizeText(file.mime_type).toLowerCase() } : {}),
      ...(file.size === undefined || file.size === null ? {} : { size: Number(file.size) }),
    };
    return { type, resource: { file: payload } };
  }

  return { type, resource: sortValue(resource || {}) };
}

export function createResourceFingerprint(type, resource) {
  const payload = normalizeResourcePayload(String(type || '').toUpperCase(), resource);
  return createFingerprint(JSON.stringify(sortValue(payload)));
}

export function normalizeResourcePayloadForStorage(type, resource) {
  return normalizeResourcePayload(String(type || '').toUpperCase(), resource);
}

export function maskEmail(normalizedEmail) {
  const email = normalizeText(normalizedEmail);
  const atIndex = email.indexOf('@');
  if (atIndex <= 0) {
    return email;
  }

  const local = email.slice(0, atIndex);
  const domain = email.slice(atIndex + 1);
  const prefix = local.slice(0, Math.min(2, local.length));
  const suffix = local.length > 2 ? '***' : '*';
  return `${prefix}${suffix}@${domain}`;
}
