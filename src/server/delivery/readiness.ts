export type IntegrationReadiness =
  | 'DEMO'
  | 'NOT_CONFIGURED'
  | 'CONFIGURED'
  | 'CONFIGURED_UNVERIFIED'
  | 'CONNECTING'
  | 'CONNECTED'
  | 'VALIDATED'
  | 'AUTHENTICATION_FAILED'
  | 'CONNECTION_FAILED'
  | 'FAILED';

export type IntegrationFailureCode =
  | 'AUTHENTICATION_FAILED'
  | 'CONNECTION_FAILED'
  | 'RUN_FAILED'
  | 'REPORT_INVALID';

let runtimeReadiness: IntegrationReadiness | null = null;
let runtimeFailure: IntegrationFailureCode | null = null;

export function setIntegrationReadiness(status: IntegrationReadiness, failure: IntegrationFailureCode | null = null) {
  runtimeReadiness = status;
  runtimeFailure = (status === 'FAILED' || status === 'AUTHENTICATION_FAILED' || status === 'CONNECTION_FAILED')
    ? failure || (status === 'AUTHENTICATION_FAILED' ? 'AUTHENTICATION_FAILED' : status === 'CONNECTION_FAILED' ? 'CONNECTION_FAILED' : 'RUN_FAILED')
    : null;
}

export function getIntegrationReadiness(
  configured: boolean,
  latestRun?: { status?: string; error?: string | null } | null
) {
  if (!configured) return { status: 'DEMO' as const, failure: null };
  if (runtimeReadiness) {
    return {
      status: runtimeReadiness,
      failure: runtimeFailure,
    };
  }
  if (latestRun?.status === 'SUCCEEDED') {
    return { status: 'VALIDATED' as const, failure: null };
  }
  if (latestRun?.status === 'FAILED') {
    const err = (latestRun.error || '').toLowerCase();
    const isAuth = err.includes('401') || err.includes('unauthorized') || err.includes('authentication') || err.includes('project not found') || err.includes('failed to get project');
    return {
      status: 'FAILED' as const,
      failure: (isAuth ? 'AUTHENTICATION_FAILED' : 'CONNECTION_FAILED') as IntegrationFailureCode,
    };
  }
  return {
    status: 'CONFIGURED' as const,
    failure: null,
  };
}
