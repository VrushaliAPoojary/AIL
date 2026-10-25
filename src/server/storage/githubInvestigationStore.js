import { ConflictError, ConfigurationError, PersistenceError, ResourceFileAlreadyExistsError, ResourceFileIntegrityError, ResourceFileNotFoundError } from './errors.js';
import { createResourceFileDescriptor, cloneResourceFileBytes, cloneResourceFileDescriptor, verifyResourceFileIntegrity } from './resourceFiles.js';

const API_VERSION = '2022-11-28';
const BASE_URL = 'https://api.github.com';
const CONTRIBUTOR_DIR = 'data/contributors';
const CONTRIBUTION_DIR = 'data/contributions';
const RESOURCE_DIR = 'data/resources';
const AUTH_CREDENTIAL_DIR = 'data/auth/credentials';
const ACTIVITY_DIR = 'data/activity';
const CONTRIBUTOR_EMAIL_INDEX_DIR = 'data/indexes/contributors/by-email';
const CONTRIBUTOR_IDEMPOTENCY_INDEX_DIR = 'data/indexes/contributors/by-idempotency';
const CREDENTIAL_INDEX_DIR = 'data/indexes/credentials';
const RESOURCE_FINGERPRINT_INDEX_DIR = 'data/indexes/resources/by-fingerprint';
const RESOURCE_FILE_DIR = 'data/resource-files';

function encodeContent(value) {
  return Buffer.from(JSON.stringify(value, null, 2) + '\n', 'utf8').toString('base64');
}

function decodeContent(value) {
  const normalized = String(value || '').replace(/\n/g, '');
  return JSON.parse(Buffer.from(normalized, 'base64').toString('utf8'));
}

function assertConfigured(config) {
  const { token, owner, repo } = config || {};
  if (!token || !owner || !repo) {
    throw new ConfigurationError('GitHub data repository is not configured.');
  }
}

function normalizeBranch(branch) {
  return branch || 'main';
}

function ensureSafeId(id, prefix) {
  if (typeof id !== 'string' || !id.startsWith(prefix) || !/^[a-z]{3}_[a-z0-9_]+$/.test(id)) {
    throw new PersistenceError(`Unsafe record identifier: ${id}`, 400);
  }
  return id;
}

function ensureSafeHash(hash) {
  if (typeof hash !== 'string' || !/^[a-f0-9]{64}$/.test(hash)) {
    throw new PersistenceError(`Unsafe content hash: ${hash}`, 400);
  }
  return hash;
}

function safePath(directory, id) {
  return `${directory}/${id}.json`;
}

function hashPath(directory, hash) {
  return `${directory}/${ensureSafeHash(hash)}.json`;
}

function resourceFileDescriptorPath(resourceId) {
  return RESOURCE_FILE_DIR + '/' + ensureSafeId(resourceId, 'res_') + '/descriptor.json';
}

function clone(value) {
  return value === null || value === undefined ? value : structuredClone(value);
}

export class GitHubInvestigationStore {
  constructor(config) {
    assertConfigured(config);
    this.config = {
      token: config.token,
      owner: config.owner,
      repo: config.repo,
      branch: normalizeBranch(config.branch),
    };
  }

  _url(path) {
    return `${BASE_URL}/repos/${this.config.owner}/${this.config.repo}/contents/${path}`;
  }

  async _request(path, options = {}) {
    const response = await fetch(this._url(path), {
      ...options,
      headers: {
        Accept: 'application/vnd.github+json',
        Authorization: `Bearer ${this.config.token}`,
        'X-GitHub-Api-Version': API_VERSION,
        ...(options.headers || {}),
      },
    });

    if (response.ok) {
      if (response.status === 204) {
        return null;
      }
      const text = await response.text();
      return text ? JSON.parse(text) : null;
    }

    if (response.status === 404) {
      return null;
    }

    let details = null;
    try {
      details = await response.json();
    } catch {
      details = await response.text();
    }

    const message = details?.message || `GitHub API request failed with ${response.status}`;
    throw new PersistenceError(message, response.status, details);
  }

  async _readJson(path) {
    const data = await this._request(path, {
      method: 'GET',
      headers: {
        Accept: 'application/vnd.github.object+json',
      },
    });

    if (!data) {
      return null;
    }

    if (Array.isArray(data)) {
      return data;
    }

    if (typeof data.content === 'string') {
      return decodeContent(data.content);
    }

    return data;
  }

  async _readBinaryFile(path) {
    const data = await this._request(path, {
      method: 'GET',
      headers: {
        Accept: 'application/vnd.github.object+json',
      },
    });

    if (!data || Array.isArray(data) || typeof data.content !== 'string') {
      return null;
    }

    return {
      meta: data,
      bytes: Buffer.from(String(data.content || '').replace(/\n/g, ''), 'base64'),
    };
  }

  async _getFileMeta(path) {
    const data = await this._request(path, {
      method: 'GET',
      headers: {
        Accept: 'application/vnd.github.object+json',
      },
    });

    if (!data || Array.isArray(data)) {
      return null;
    }

    return data;
  }

  async _writeJson(path, payload, message) {
    const existing = await this._getFileMeta(path);
    if (existing) {
      throw new ConflictError(`Record already exists at ${path}`);
    }

    return this._request(path, {
      method: 'PUT',
      body: JSON.stringify({
        message,
        branch: this.config.branch,
        content: encodeContent(payload),
      }),
    });
  }

  async _writeBinaryFile(path, bytes, message) {
    const existing = await this._getFileMeta(path);
    if (existing) {
      throw new ConflictError(`Record already exists at ${path}`);
    }

    return this._request(path, {
      method: 'PUT',
      body: JSON.stringify({
        message,
        branch: this.config.branch,
        content: Buffer.from(bytes).toString('base64'),
      }),
    });
  }

  async _deleteJson(path, sha, message) {
    return this._request(path, {
      method: 'DELETE',
      body: JSON.stringify({
        message,
        branch: this.config.branch,
        sha,
      }),
    });
  }

  async _listDirectory(path) {
    const data = await this._request(path, {
      method: 'GET',
      headers: {
        Accept: 'application/vnd.github.object+json',
      },
    });

    if (!data) {
      return [];
    }

    if (Array.isArray(data)) {
      return data;
    }

    if (Array.isArray(data.entries)) {
      return data.entries;
    }

    if (Array.isArray(data.items)) {
      return data.items;
    }

    return [data];
  }

  async createContributor(contributor) {
    ensureSafeId(contributor.id, 'ctr_');
    await this._writeJson(safePath(CONTRIBUTOR_DIR, contributor.id), contributor, `Create contributor ${contributor.id}`);
    return clone(contributor);
  }

  async getContributor(id) {
    ensureSafeId(id, 'ctr_');
    return this._readJson(safePath(CONTRIBUTOR_DIR, id));
  }

  async createContributorEmailIndex(emailKey, index) {
    ensureSafeHash(emailKey);
    await this._writeJson(hashPath(CONTRIBUTOR_EMAIL_INDEX_DIR, emailKey), index, `Index contributor by email ${emailKey}`);
    return clone(index);
  }

  async getContributorEmailIndex(emailKey) {
    ensureSafeHash(emailKey);
    return this._readJson(hashPath(CONTRIBUTOR_EMAIL_INDEX_DIR, emailKey));
  }

  async getContributorByEmailKey(emailKey) {
    const index = await this.getContributorEmailIndex(emailKey);
    if (!index) {
      return null;
    }

    if (index.contributor) {
      return index.contributor;
    }

    if (index.contributor_id) {
      const contributor = await this.getContributor(index.contributor_id);
      if (contributor) {
        return contributor;
      }
    }

    return null;
  }

  async createContributorIdempotencyIndex(idempotencyKey, index) {
    ensureSafeHash(idempotencyKey);
    await this._writeJson(hashPath(CONTRIBUTOR_IDEMPOTENCY_INDEX_DIR, idempotencyKey), index, `Index contributor idempotency ${idempotencyKey}`);
    return clone(index);
  }

  async getContributorIdempotencyIndex(idempotencyKey) {
    ensureSafeHash(idempotencyKey);
    return this._readJson(hashPath(CONTRIBUTOR_IDEMPOTENCY_INDEX_DIR, idempotencyKey));
  }

  async createCredential(credential) {
    ensureSafeHash(credential.id);
    await this._writeJson(hashPath(AUTH_CREDENTIAL_DIR, credential.id), credential, `Create credential ${credential.id}`);
    return clone(credential);
  }

  async getCredential(id) {
    ensureSafeHash(id);
    return this._readJson(hashPath(AUTH_CREDENTIAL_DIR, id));
  }

  async createCredentialIndex(credentialHash, index) {
    ensureSafeHash(credentialHash);
    await this._writeJson(hashPath(CREDENTIAL_INDEX_DIR, credentialHash), index, `Index credential ${credentialHash}`);
    return clone(index);
  }

  async getCredentialIndex(credentialHash) {
    ensureSafeHash(credentialHash);
    return this._readJson(hashPath(CREDENTIAL_INDEX_DIR, credentialHash));
  }

  async getCredentialByHash(credentialHash) {
    const index = await this.getCredentialIndex(credentialHash);
    if (!index) {
      return null;
    }
    if (index.credential) {
      return clone(index.credential);
    }
    return this.getCredential(credentialHash);
  }

  async getContributorByCredentialHash(credentialHash) {
    const index = await this.getCredentialIndex(credentialHash);
    if (!index) {
      return null;
    }
    if (index.contributor) {
      return clone(index.contributor);
    }
    return index.contributor_id ? this.getContributor(index.contributor_id) : null;
  }

  async createResource(resource) {
    ensureSafeId(resource.id, 'res_');
    await this._writeJson(safePath(RESOURCE_DIR, resource.id), resource, `Create resource ${resource.id}`);
    return clone(resource);
  }

  async getResource(id) {
    ensureSafeId(id, 'res_');
    return this._readJson(safePath(RESOURCE_DIR, id));
  }

  async createResourceFingerprintIndex(fingerprint, index) {
    ensureSafeHash(fingerprint);
    await this._writeJson(hashPath(RESOURCE_FINGERPRINT_INDEX_DIR, fingerprint), index, `Index resource by fingerprint ${fingerprint}`);
    return clone(index);
  }

  async getResourceFingerprintIndex(fingerprint) {
    ensureSafeHash(fingerprint);
    return this._readJson(hashPath(RESOURCE_FINGERPRINT_INDEX_DIR, fingerprint));
  }

  async getResourceByFingerprint(fingerprint) {
    const index = await this.getResourceFingerprintIndex(fingerprint);
    if (!index) {
      return null;
    }

    if (index.resource) {
      return index.resource;
    }

    if (index.resource_id) {
      const resource = await this.getResource(index.resource_id);
      if (resource) {
        return resource;
      }
    }

    return null;
  }

  async saveResourceFile(input) {
    const normalized = createResourceFileDescriptor(input, { storageProvider: 'GITHUB' });
    const descriptorPath = resourceFileDescriptorPath(normalized.descriptor.resource_id);
    const payloadPath = normalized.descriptor.storage_key;
    const existingDescriptor = await this._readJson(descriptorPath);
    const existingPayload = await this._readBinaryFile(payloadPath);

    if (existingDescriptor) {
      if (existingPayload) {
        verifyResourceFileIntegrity(existingDescriptor, existingPayload.bytes);
      }
      if (existingDescriptor.content_sha256 !== normalized.descriptor.content_sha256) {
        throw new ResourceFileAlreadyExistsError('Resource file already exists.', { resource_id: normalized.descriptor.resource_id, storage_key: payloadPath });
      }
      if (!existingPayload) {
        await this._writeBinaryFile(payloadPath, normalized.bytes, 'Store resource file ' + normalized.descriptor.resource_id);
      }
      return cloneResourceFileDescriptor(existingDescriptor);
    }

    if (existingPayload) {
      verifyResourceFileIntegrity({ resource_id: normalized.descriptor.resource_id, content_sha256: normalized.descriptor.content_sha256 }, existingPayload.bytes);
      await this._writeJson(descriptorPath, normalized.descriptor, 'Store resource file descriptor ' + normalized.descriptor.resource_id);
      return cloneResourceFileDescriptor(normalized.descriptor);
    }

    await this._writeBinaryFile(payloadPath, normalized.bytes, 'Store resource file ' + normalized.descriptor.resource_id);
    await this._writeJson(descriptorPath, normalized.descriptor, 'Store resource file descriptor ' + normalized.descriptor.resource_id);
    return cloneResourceFileDescriptor(normalized.descriptor);
  }

  async getResourceFile(resourceId) {
    const descriptorPath = resourceFileDescriptorPath(resourceId);
    const descriptor = await this._readJson(descriptorPath);
    if (!descriptor) {
      throw new ResourceFileNotFoundError('Resource file not found.', { resource_id: resourceId });
    }

    const payload = await this._readBinaryFile(descriptor.storage_key);
    if (!payload) {
      throw new ResourceFileNotFoundError('Resource file not found.', { resource_id: resourceId });
    }

    verifyResourceFileIntegrity(descriptor, payload.bytes);
    return {
      descriptor: cloneResourceFileDescriptor(descriptor),
      bytes: cloneResourceFileBytes(payload.bytes),
    };
  }
  async createContribution(contribution) {
    ensureSafeId(contribution.id, 'con_');
    await this._writeJson(safePath(CONTRIBUTION_DIR, contribution.id), contribution, `Create contribution ${contribution.id}`);
    return clone(contribution);
  }

  async getContribution(id) {
    ensureSafeId(id, 'con_');
    return this._readJson(safePath(CONTRIBUTION_DIR, id));
  }

  async listContributions(options = {}) {
    const limit = options.limit ?? 20;
    const entries = await this._listDirectory(CONTRIBUTION_DIR);
    const files = entries
      .filter((entry) => entry && entry.type === 'file' && entry.name.endsWith('.json'))
      .sort((left, right) => String(right.name).localeCompare(String(left.name)))
      .slice(0, Math.min(limit, 50));

    const records = [];
    for (const entry of files) {
      const record = await this._readJson(entry.path);
      if (record) {
        records.push(record);
      }
    }

    return records
      .sort((left, right) => String(right.created_at).localeCompare(String(left.created_at)))
      .slice(0, limit);
  }

  async createActivity(activity) {
    ensureSafeId(activity.id, 'evt_');
    await this._writeJson(safePath(ACTIVITY_DIR, activity.id), activity, `Create activity ${activity.id}`);
    return clone(activity);
  }

  async deleteContribution(id) {
    ensureSafeId(id, 'con_');
    const meta = await this._getFileMeta(safePath(CONTRIBUTION_DIR, id));
    if (!meta) {
      return;
    }
    await this._deleteJson(safePath(CONTRIBUTION_DIR, id), meta.sha, `Delete contribution ${id}`);
  }
}

export function createGitHubInvestigationStore(config) {
  return new GitHubInvestigationStore(config);
}