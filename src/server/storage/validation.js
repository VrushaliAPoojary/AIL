import { ValidationError } from './errors.js';

const CONTRIBUTION_TYPES = new Set(['LINK', 'TEXT', 'FILE', 'INSIGHT']);
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const SAFE_TEXT_PATTERN = /\S/;

function isPlainObject(value) {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function normalizeString(value) {
  return typeof value === 'string' ? value.trim() : '';
}

function requireString(value, fieldName, maxLength) {
  const normalized = normalizeString(value);
  if (!normalized) {
    throw new ValidationError(`${fieldName} is required.`);
  }
  if (normalized.length > maxLength) {
    throw new ValidationError(`${fieldName} is too long.`);
  }
  return normalized;
}

function optionalString(value, fieldName, maxLength) {
  if (value === undefined || value === null || value === '') {
    return undefined;
  }
  return requireString(value, fieldName, maxLength);
}

export function validateEmail(email) {
  const normalized = requireString(email, 'email', 254);
  if (!EMAIL_PATTERN.test(normalized)) {
    throw new ValidationError('email must be a valid email address.');
  }
  return normalized;
}

function validateUrl(url) {
  const normalized = requireString(url, 'resource.url', 2048);
  let parsed;
  try {
    parsed = new URL(normalized);
  } catch {
    throw new ValidationError('resource.url must be a valid URL.');
  }
  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
    throw new ValidationError('resource.url must use http or https.');
  }
  return parsed.toString();
}

function validatePositiveInteger(value, fieldName, max = Number.MAX_SAFE_INTEGER) {
  if (value === undefined || value === null || value === '') {
    throw new ValidationError(`${fieldName} is required.`);
  }
  const numeric = typeof value === 'string' ? Number(value) : value;
  if (!Number.isInteger(numeric) || numeric < 0 || numeric > max) {
    throw new ValidationError(`${fieldName} must be a valid non-negative integer.`);
  }
  return numeric;
}

function validateRecordId(id, prefix, fieldName) {
  const normalized = requireString(id, fieldName, 80);
  if (!normalized.startsWith(prefix)) {
    throw new ValidationError(`${fieldName} must start with ${prefix}.`);
  }
  return normalized;
}

export function validateContributorInput(input) {
  if (!isPlainObject(input)) {
    throw new ValidationError('Request body must be a JSON object.');
  }

  const name = requireString(input.name, 'name', 120);
  const email = validateEmail(input.email);
  const role = requireString(input.role, 'role', 80);

  return { name, email, role };
}

export function validateContributorProfileInput(input) {
  if (!isPlainObject(input)) {
    throw new ValidationError('Request body must be a JSON object.');
  }

  const name = requireString(input.name, 'name', 120);
  const role = requireString(input.role, 'role', 80);

  return { name, role };
}

export function validateContributorCreationInput(input) {
  if (!isPlainObject(input)) {
    throw new ValidationError('Request body must be a JSON object.');
  }

  const profile = validateContributorProfileInput(input);
  const verification_code = requireString(input.verification_code, 'verification_code', 6);
  if (!/^\d{6}$/.test(verification_code)) {
    throw new ValidationError('verification_code must be a 6 digit code.');
  }

  return { ...profile, verification_code };
}

export function validateContributorId(id) {
  return validateRecordId(id, 'ctr_', 'contributor id');
}

export function validateContributionId(id) {
  return validateRecordId(id, 'con_', 'contribution id');
}

export function validateResourceId(id) {
  return validateRecordId(id, 'res_', 'resource id');
}

export function validateContributionInput(input) {
  if (!isPlainObject(input)) {
    throw new ValidationError('Request body must be a JSON object.');
  }

  const type = requireString(input.type, 'type', 20).toUpperCase();
  if (!CONTRIBUTION_TYPES.has(type)) {
    throw new ValidationError('type must be LINK, TEXT, FILE, or INSIGHT.');
  }

  const context = optionalString(input.context, 'context', 2000);
  const resource = input.resource;
  if (!isPlainObject(resource)) {
    throw new ValidationError('resource is required.');
  }

  if (type === 'LINK') {
    return {
      type,
      context,
      resource: {
        url: validateUrl(resource.url),
      },
    };
  }

  if (type === 'TEXT' || type === 'INSIGHT') {
    const text = requireString(resource.text, 'resource.text', 8000);
    if (!SAFE_TEXT_PATTERN.test(text)) {
      throw new ValidationError('resource.text must contain visible text.');
    }
    return {
      type,
      context,
      resource: {
        text,
      },
    };
  }

  const file = resource.file;
  if (!isPlainObject(file)) {
    throw new ValidationError('resource.file is required for FILE contributions.');
  }

  const name = requireString(file.name, 'resource.file.name', 255);
  const mime_type = optionalString(file.mime_type, 'resource.file.mime_type', 255);
  const size = validatePositiveInteger(file.size, 'resource.file.size', 100 * 1024 * 1024);

  return {
    type,
    context,
    resource: {
      file: {
        name,
        ...(mime_type ? { mime_type } : {}),
        size,
      },
    },
  };
}

export function validateContributionListOptions(options) {
  const limit = options?.limit === undefined ? 20 : validatePositiveInteger(options.limit, 'limit', 50);
  return { limit: limit === 0 ? 20 : limit };
}

export function summarizeContributionResource(contribution) {
  const resource = contribution.resource || {};
  if (contribution.type === 'LINK') {
    try {
      const url = new URL(resource.url);
      return url.hostname.replace(/^www\./, '') + url.pathname;
    } catch {
      return resource.url || 'Link';
    }
  }
  if (contribution.type === 'TEXT' || contribution.type === 'INSIGHT') {
    const text = normalizeString(resource.text);
    return text.length > 120 ? `${text.slice(0, 117)}...` : text || 'Text';
  }
  if (resource.file?.name) {
    return resource.file.name;
  }
  return 'File';
}

export function normalizeContext(context) {
  return optionalString(context, 'context', 2000);
}

export function normalizeIdempotencyKey(value) {
  if (value === undefined || value === null || value === '') {
    return '';
  }
  return requireString(value, 'Idempotency-Key', 255);
}
