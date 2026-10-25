import { ConfigurationError } from './errors.js';
import { createGitHubInvestigationStore } from './githubInvestigationStore.js';
import { MemoryInvestigationStore } from './memoryInvestigationStore.js';

export { AppError, ValidationError, NotFoundError, ConflictError, ConfigurationError, PersistenceError, ResourceFileTooLargeError, ResourceFileTypeUnsupportedError, ResourceFileSizeMismatchError, ResourceFileAlreadyExistsError, ResourceFileIntegrityError, ResourceFileNotFoundError } from './errors.js';
export { createRecordId } from './ids.js';
export { createCredentialHash } from '../auth/identity.js';
export {
  validateEmail,
  validateContributorInput,
  validateContributorProfileInput,
  validateContributorCreationInput,
  validateContributorId,
  validateContributionId,
  validateResourceId,
  validateContributionInput,
  validateContributionListOptions,
  summarizeContributionResource,
  normalizeContext,
  normalizeIdempotencyKey,
} from './validation.js';
export { MemoryInvestigationStore } from './memoryInvestigationStore.js';
export { DEFAULT_MAX_RESOURCE_FILE_BYTES, getMaxResourceFileBytesFromEnv, getResourceFileExtension, createResourceFileStorageKey, createResourceFileDescriptor, createStoredResourceFileRecord, verifyResourceFileIntegrity, cloneResourceFileDescriptor, cloneResourceFileBytes } from './resourceFiles.js';
export { GitHubInvestigationStore, createGitHubInvestigationStore } from './githubInvestigationStore.js';

export function getGitHubPersistenceConfigFromEnv(env = process.env) {
  const token = env.GITHUB_TOKEN;
  const owner = env.GITHUB_OWNER;
  const repo = env.GITHUB_DATA_REPO;
  const branch = env.GITHUB_BRANCH || 'main';

  if (!token || !owner || !repo) {
    return null;
  }

  return { token, owner, repo, branch };
}

export function getServerSecurityConfigFromEnv(env = process.env) {
  const identityPepper = env.IDENTITY_PEPPER;
  const sessionSecret = env.SESSION_SECRET || identityPepper;

  if (!identityPepper) {
    throw new ConfigurationError('IDENTITY_PEPPER is not configured.');
  }

  return {
    identityPepper,
    sessionSecret,
  };
}

let memoryStoreSingleton = null;

export function resetMemoryStoreSingleton() {
  memoryStoreSingleton = null;
}

export function createInvestigationStore(env = process.env) {
  if (env.USE_MEMORY_STORE === 'true' || (env.NODE_ENV === 'test' && !getGitHubPersistenceConfigFromEnv(env))) {
    if (!memoryStoreSingleton) {
      memoryStoreSingleton = createMemoryInvestigationStore();
    }
    return memoryStoreSingleton;
  }
  const config = getGitHubPersistenceConfigFromEnv(env);
  if (!config) {
    throw new ConfigurationError('GitHub data repository is not configured.');
  }
  return createGitHubInvestigationStore(config);
}

export function createMemoryInvestigationStore(seed = {}) {
  return new MemoryInvestigationStore(seed);
}
