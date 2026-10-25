import 'server-only';

export type ServerEnvironment = {
  githubToken: string | undefined;
  githubOwner: string | undefined;
  githubDataRepo: string | undefined;
  githubBranch: string | undefined;
};

export function getServerEnvironment(): ServerEnvironment {
  return {
    githubToken: process.env.GITHUB_TOKEN,
    githubOwner: process.env.GITHUB_OWNER,
    githubDataRepo: process.env.GITHUB_DATA_REPO,
    githubBranch: process.env.GITHUB_BRANCH,
  };
}

export function isGitHubPersistenceConfigured(): boolean {
  const env = getServerEnvironment();
  return Boolean(env.githubToken && env.githubOwner && env.githubDataRepo);
}

export function getGitHubPersistenceConfig() {
  const env = getServerEnvironment();

  if (!env.githubToken || !env.githubOwner || !env.githubDataRepo) {
    return null;
  }

  return {
    token: env.githubToken,
    owner: env.githubOwner,
    repo: env.githubDataRepo,
    branch: env.githubBranch || 'main',
  };
}
