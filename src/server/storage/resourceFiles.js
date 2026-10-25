import { createHash } from 'node:crypto';
import { ConfigurationError, ConflictError, NotFoundError, ValidationError } from './errors.js';
import { validateResourceId } from './validation.js';

export const DEFAULT_MAX_RESOURCE_FILE_BYTES = 5 * 1024 * 1024;

const RESOURCE_FILE_EXTENSION_BY_MIME = {
  'image/jpeg': '.jpg',
  'image/png': '.png',
  'image/gif': '.gif',
  'image/webp': '.webp',
  'application/pdf': '.pdf',
  'text/plain': '.txt',
  'text/markdown': '.md',
};

function normalizeText(value) {
  return typeof value === 'string' ? value.trim() : '';
}

function normalizeMimeType(value) {
  return normalizeText(value).toLowerCase().split(';', 1)[0];
}

function toBuffer(bytes) {
  if (Buffer.isBuffer(bytes)) {
    return Buffer.from(bytes);
  }
  if (bytes instanceof Uint8Array) {
    return Buffer.from(bytes);
  }
  throw new ValidationError('bytes must be a Buffer or Uint8Array.');
}

function createSha256Hex(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function ensureStorageProvider(value) {
  const normalized = normalizeText(value).toUpperCase();
  if (normalized !== 'GITHUB' && normalized !== 'MEMORY') {
    throw new ValidationError('storage_provider must be GITHUB or MEMORY.');
  }
  return normalized;
}

export class ResourceFileTooLargeError extends ValidationError {
  constructor(message = 'Resource file is too large.', details = undefined) {
    super(message, details);
    this.name = 'ResourceFileTooLargeError';
    this.status = 413;
    this.code = 'RESOURCE_FILE_TOO_LARGE';
  }
}

export class ResourceFileTypeUnsupportedError extends ValidationError {
  constructor(message = 'Resource file type is unsupported.', details = undefined) {
    super(message, details);
    this.name = 'ResourceFileTypeUnsupportedError';
    this.status = 415;
    this.code = 'RESOURCE_FILE_TYPE_UNSUPPORTED';
  }
}

export class ResourceFileSizeMismatchError extends ValidationError {
  constructor(message = 'Resource file size does not match the received bytes.', details = undefined) {
    super(message, details);
    this.name = 'ResourceFileSizeMismatchError';
    this.code = 'RESOURCE_FILE_SIZE_MISMATCH';
  }
}

export class ResourceFileAlreadyExistsError extends ConflictError {
  constructor(message = 'Resource file already exists.', details = undefined) {
    super(message, details);
    this.name = 'ResourceFileAlreadyExistsError';
    this.code = 'RESOURCE_FILE_ALREADY_EXISTS';
  }
}

export class ResourceFileIntegrityError extends ValidationError {
  constructor(message = 'Resource file integrity check failed.', details = undefined) {
    super(message, details);
    this.name = 'ResourceFileIntegrityError';
    this.status = 500;
    this.code = 'RESOURCE_FILE_INTEGRITY_FAILURE';
  }
}

export class ResourceFileNotFoundError extends NotFoundError {
  constructor(message = 'Resource file not found.', details = undefined) {
    super(message, details);
    this.name = 'ResourceFileNotFoundError';
    this.code = 'RESOURCE_FILE_NOT_FOUND';
  }
}

export function getMaxResourceFileBytesFromEnv(env = process.env) {
  const raw = env.MAX_RESOURCE_FILE_BYTES;
  if (raw === undefined || raw === null || raw === '') {
    return DEFAULT_MAX_RESOURCE_FILE_BYTES;
  }
  const parsed = Number(raw);
  if (!Number.isInteger(parsed) || parsed <= 0) {
    throw new ConfigurationError('MAX_RESOURCE_FILE_BYTES is invalid.');
  }
  return parsed;
}

export function getResourceFileExtension(mimeType) {
  const normalized = normalizeMimeType(mimeType);
  const extension = RESOURCE_FILE_EXTENSION_BY_MIME[normalized];
  if (!extension) {
    throw new ResourceFileTypeUnsupportedError('Resource file MIME type is unsupported.', {
      mime_type: normalized,
    });
  }
  return extension;
}

export function createResourceFileStorageKey(resourceId, mimeType) {
  const validatedResourceId = validateResourceId(resourceId);
  return `data/resource-files/${validatedResourceId}/payload${getResourceFileExtension(mimeType)}`;
}

export function createResourceFileDescriptor(input, options = {}) {
  const storageProvider = ensureStorageProvider(options.storageProvider);
  const storedAt = options.storedAt || new Date().toISOString();
  const maxBytes = options.maxResourceFileBytes || getMaxResourceFileBytesFromEnv(options.env);

  if (!input || typeof input !== 'object') {
    throw new ValidationError('Resource file input must be a JSON object.');
  }

  const bytes = toBuffer(input.bytes);
  const size = bytes.length;
  if (size > maxBytes) {
    throw new ResourceFileTooLargeError('Resource file is too large.', {
      max_bytes: maxBytes,
      actual_size: size,
    });
  }

  const originalName = normalizeText(input.original_name);
  if (!originalName) {
    throw new ValidationError('original_name is required.');
  }

  const mimeType = normalizeMimeType(input.mime_type);
  const extension = getResourceFileExtension(mimeType);
  const resourceId = validateResourceId(input.resource_id);

  if (input.size !== undefined && input.size !== null && input.size !== '') {
    const declaredSize = typeof input.size === 'string' ? Number(input.size) : input.size;
    if (!Number.isInteger(declaredSize) || declaredSize < 0 || declaredSize !== size) {
      throw new ResourceFileSizeMismatchError('Resource file size does not match the received bytes.', {
        declared_size: declaredSize,
        actual_size: size,
      });
    }
  }

  const contentSha256 = createSha256Hex(bytes);
  const storageKey = createResourceFileStorageKey(resourceId, mimeType);

  return {
    descriptor: {
      resource_id: resourceId,
      storage_provider: storageProvider,
      storage_key: storageKey,
      original_name: originalName,
      mime_type: mimeType,
      size,
      content_sha256: contentSha256,
      stored_at: storedAt,
    },
    bytes,
    storageKey,
    contentSha256,
    extension,
    resourceId,
    mimeType,
    size,
  };
}

export function createStoredResourceFileRecord(input, options = {}) {
  return createResourceFileDescriptor(input, options).descriptor;
}

export function verifyResourceFileIntegrity(descriptor, bytes) {
  const actualHash = createSha256Hex(bytes);
  if (descriptor.content_sha256 !== actualHash) {
    throw new ResourceFileIntegrityError('Resource file integrity check failed.', {
      resource_id: descriptor.resource_id,
      expected_sha256: descriptor.content_sha256,
      actual_sha256: actualHash,
    });
  }
}

export function cloneResourceFileDescriptor(descriptor) {
  return structuredClone(descriptor);
}

export function cloneResourceFileBytes(bytes) {
  return Buffer.from(bytes);
}
