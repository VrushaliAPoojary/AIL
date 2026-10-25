import { ConflictError, ResourceFileNotFoundError } from './errors.js';
import { createResourceFileDescriptor, cloneResourceFileBytes, cloneResourceFileDescriptor, verifyResourceFileIntegrity, ResourceFileAlreadyExistsError } from './resourceFiles.js';

function clone(value) {
  return value === null || value === undefined ? value : structuredClone(value);
}

export class MemoryInvestigationStore {
  constructor(seed = {}) {
    this.contributors = new Map((seed.contributors || []).map((item) => [item.id, item]));
    this.contributorsByEmail = new Map((seed.contributorsByEmail || []).map((item) => [item.email_key, item]));
    this.contributorIdempotency = new Map((seed.contributorIdempotency || []).map((item) => [item.idempotency_key, item]));
    this.credentials = new Map((seed.credentials || []).map((item) => [item.id, item]));
    this.credentialsByHash = new Map((seed.credentialsByHash || []).map((item) => [item.credential_hash, item]));
    this.resources = new Map((seed.resources || []).map((item) => [item.id, item]));
    this.resourcesByFingerprint = new Map((seed.resourcesByFingerprint || []).map((item) => [item.fingerprint, item]));
    this.resourceFiles = new Map((seed.resourceFiles || []).map((item) => [item.resource_id, item]));
    this.contributions = new Map((seed.contributions || []).map((item) => [item.id, item]));
    this.activities = new Map((seed.activities || []).map((item) => [item.id, item]));
  }

  async createContributor(contributor) {
    if (this.contributors.has(contributor.id)) {
      throw new ConflictError(`Contributor already exists: ${contributor.id}`);
    }
    this.contributors.set(contributor.id, clone(contributor));
    return clone(contributor);
  }

  async getContributor(id) {
    return this.contributors.has(id) ? clone(this.contributors.get(id)) : null;
  }

  async createContributorEmailIndex(emailKey, index) {
    if (this.contributorsByEmail.has(emailKey)) {
      throw new ConflictError(`Contributor email already exists: ${emailKey}`);
    }
    this.contributorsByEmail.set(emailKey, clone(index));
    return clone(index);
  }

  async getContributorEmailIndex(emailKey) {
    return this.contributorsByEmail.has(emailKey) ? clone(this.contributorsByEmail.get(emailKey)) : null;
  }

  async getContributorByEmailKey(emailKey) {
    const index = await this.getContributorEmailIndex(emailKey);
    if (!index) {
      return null;
    }
    if (index.contributor) {
      return clone(index.contributor);
    }
    return index.contributor_id ? this.getContributor(index.contributor_id) : null;
  }

  async createContributorIdempotencyIndex(idempotencyKey, index) {
    if (this.contributorIdempotency.has(idempotencyKey)) {
      throw new ConflictError(`Contributor idempotency already exists: ${idempotencyKey}`);
    }
    this.contributorIdempotency.set(idempotencyKey, clone(index));
    return clone(index);
  }

  async getContributorIdempotencyIndex(idempotencyKey) {
    return this.contributorIdempotency.has(idempotencyKey) ? clone(this.contributorIdempotency.get(idempotencyKey)) : null;
  }

  async createCredential(credential) {
    if (this.credentials.has(credential.id)) {
      throw new ConflictError(`Credential already exists: ${credential.id}`);
    }
    this.credentials.set(credential.id, clone(credential));
    return clone(credential);
  }

  async getCredential(id) {
    return this.credentials.has(id) ? clone(this.credentials.get(id)) : null;
  }

  async createCredentialIndex(credentialHash, index) {
    if (this.credentialsByHash.has(credentialHash)) {
      throw new ConflictError(`Credential already exists: ${credentialHash}`);
    }
    this.credentialsByHash.set(credentialHash, clone(index));
    return clone(index);
  }

  async getCredentialIndex(credentialHash) {
    return this.credentialsByHash.has(credentialHash) ? clone(this.credentialsByHash.get(credentialHash)) : null;
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
    if (this.resources.has(resource.id)) {
      throw new ConflictError(`Resource already exists: ${resource.id}`);
    }
    this.resources.set(resource.id, clone(resource));
    return clone(resource);
  }

  async getResource(id) {
    return this.resources.has(id) ? clone(this.resources.get(id)) : null;
  }

  async createResourceFingerprintIndex(fingerprint, index) {
    if (this.resourcesByFingerprint.has(fingerprint)) {
      throw new ConflictError(`Resource fingerprint already exists: ${fingerprint}`);
    }
    this.resourcesByFingerprint.set(fingerprint, clone(index));
    return clone(index);
  }

  async getResourceFingerprintIndex(fingerprint) {
    return this.resourcesByFingerprint.has(fingerprint) ? clone(this.resourcesByFingerprint.get(fingerprint)) : null;
  }

  async getResourceByFingerprint(fingerprint) {
    const index = await this.getResourceFingerprintIndex(fingerprint);
    if (!index) {
      return null;
    }
    if (index.resource) {
      return clone(index.resource);
    }
    return index.resource_id ? this.getResource(index.resource_id) : null;
  }

  async saveResourceFile(input) {
    const normalized = createResourceFileDescriptor(input, { storageProvider: 'MEMORY' });
    const existing = this.resourceFiles.get(normalized.descriptor.resource_id);

    if (existing) {
      verifyResourceFileIntegrity(existing.descriptor, existing.bytes);
      if (existing.descriptor.content_sha256 !== normalized.descriptor.content_sha256) {
        throw new ResourceFileAlreadyExistsError('Resource file already exists.', {
          resource_id: normalized.descriptor.resource_id,
          storage_key: normalized.descriptor.storage_key,
        });
      }
      return cloneResourceFileDescriptor(existing.descriptor);
    }

    const stored = {
      descriptor: cloneResourceFileDescriptor(normalized.descriptor),
      bytes: cloneResourceFileBytes(normalized.bytes),
    };
    this.resourceFiles.set(normalized.descriptor.resource_id, stored);
    return cloneResourceFileDescriptor(stored.descriptor);
  }

  async getResourceFile(resourceId) {
    const entry = this.resourceFiles.get(resourceId);
    if (!entry) {
      throw new ResourceFileNotFoundError('Resource file not found.', { resource_id: resourceId });
    }

    verifyResourceFileIntegrity(entry.descriptor, entry.bytes);
    return {
      descriptor: cloneResourceFileDescriptor(entry.descriptor),
      bytes: cloneResourceFileBytes(entry.bytes),
    };
  }

  async createContribution(contribution) {
    if (this.contributions.has(contribution.id)) {
      throw new ConflictError(`Contribution already exists: ${contribution.id}`);
    }
    this.contributions.set(contribution.id, clone(contribution));
    return clone(contribution);
  }

  async getContribution(id) {
    return this.contributions.has(id) ? clone(this.contributions.get(id)) : null;
  }

  async listContributions(options = {}) {
    const limit = options.limit ?? 20;
    return Array.from(this.contributions.values())
      .sort((left, right) => {
        const byTime = String(right.created_at).localeCompare(String(left.created_at));
        return byTime !== 0 ? byTime : String(right.id).localeCompare(String(left.id));
      })
      .slice(0, limit)
      .map((item) => clone(item));
  }

  async createActivity(activity) {
    if (this.activities.has(activity.id)) {
      throw new ConflictError(`Activity already exists: ${activity.id}`);
    }
    this.activities.set(activity.id, clone(activity));
    return clone(activity);
  }

  async deleteContribution(id) {
    this.contributions.delete(id);
  }

  async getActivity(id) {
    return this.activities.has(id) ? clone(this.activities.get(id)) : null;
  }
}