export type IntegrationReadiness = 'DEMO' | 'CONFIGURED' | 'CONNECTING' | 'CONNECTED' | 'VALIDATED' | 'FAILED';
export type IntegrationFailureCode = 'CONNECTION_FAILED' | 'RUN_FAILED' | 'REPORT_INVALID';

let runtimeReadiness: IntegrationReadiness | null = null;
let runtimeFailure: IntegrationFailureCode | null = null;

export function setIntegrationReadiness(status: IntegrationReadiness, failure: IntegrationFailureCode | null = null) {
  runtimeReadiness = status;
  runtimeFailure = status === 'FAILED' ? failure || 'RUN_FAILED' : null;
}

export function getIntegrationReadiness(configured: boolean) {
  if (!configured) return { status: 'DEMO' as const, failure: null };
  return {
    status: runtimeReadiness || 'CONFIGURED',
    failure: runtimeFailure,
  };
}
