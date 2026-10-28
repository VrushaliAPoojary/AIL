import 'server-only';
import type { DeliverySettings } from './types';
import { getSavedSettings, listRuns } from './store';
import { localBusinessDate } from './date';
import { getIntegrationReadiness } from './readiness';

const DEFAULTS: DeliverySettings = {
  upcomingDays: 7,
  dueDateBasis: 'contractual',
  timezone: process.env.P02_TIMEZONE || 'Asia/Kolkata',
  mode: 'demo',
};

export async function getDeliverySettings(): Promise<DeliverySettings> {
  const configuredDays = Number(process.env.P02_UPCOMING_DAYS);
  const configuredBasis = process.env.P02_DUE_DATE_BASIS;
  const liveConfigured = Boolean(
    process.env.ART_URI?.trim() && process.env.ART_CLIENT_ID?.trim() && process.env.ART_CLIENT_SECRET?.trim() &&
    process.env.ART_ORG_TITLE?.trim() && process.env.ART_ENVIRONMENT?.trim() && process.env.ART_PROJECT_KEY?.trim() &&
    process.env.ART_AGENT_ID?.trim(),
  );

  const saved = await getSavedSettings();
  return {
    ...DEFAULTS,
    upcomingDays: Number.isInteger(configuredDays) && configuredDays >= 1 && configuredDays <= 90
      ? configuredDays : DEFAULTS.upcomingDays,
    dueDateBasis: configuredBasis === 'supplier_promise' ? 'supplier_promise' : DEFAULTS.dueDateBasis,
    ...saved,
    mode: liveConfigured ? 'configured' : 'demo',
  };
}

export async function getIntegrationStatus() {
  const settings = await getDeliverySettings();
  const runs = await listRuns();
  const latestRun = runs[0] || null;
  const readiness = getIntegrationReadiness(settings.mode === 'configured', latestRun);

  let effectiveStatus: string = readiness.status;
  if (settings.mode !== 'configured') {
    effectiveStatus = 'NOT_CONFIGURED';
  } else if (readiness.status === 'FAILED') {
    effectiveStatus = readiness.failure === 'AUTHENTICATION_FAILED' ? 'AUTHENTICATION_FAILED' : 'CONNECTION_FAILED';
  } else if (readiness.status === 'CONFIGURED' && !latestRun) {
    effectiveStatus = 'CONFIGURED_UNVERIFIED';
  }

  const failure = readiness.failure || (effectiveStatus === 'AUTHENTICATION_FAILED' ? 'AUTHENTICATION_FAILED' : effectiveStatus === 'CONNECTION_FAILED' ? 'CONNECTION_FAILED' : null);

  const reasons = settings.mode !== 'configured'
    ? [
        'Configure the ART connection and target agent in the server environment.',
        'ERPNext is accessed through the configured ART agent tools; no direct ERPNext credentials are configured here.',
      ]
    : effectiveStatus === 'AUTHENTICATION_FAILED'
      ? [
          'ART server rejected authentication (HTTP 401). Verify ART_PROJECT_KEY, ART_CLIENT_ID, and ART_CLIENT_SECRET in the local environment.',
          'ERPNext is accessed through the configured ART agent tools; live connection requires valid ART authentication.',
        ]
      : effectiveStatus === 'CONNECTION_FAILED'
        ? [
            'ART connection could not be established. Check ART_URI and network reachability.',
            'ERPNext is accessed through the configured ART agent tools; no direct ERPNext credentials are configured here.',
          ]
        : effectiveStatus === 'CONFIGURED_UNVERIFIED'
          ? [
              'ART credentials are configured on the server, but live agent connection has not yet been verified.',
              'Execute a live monitoring run to establish and validate the ART ↔ ERPNext connection.',
            ]
          : [];

  return {
    mode: settings.mode,
    backend: 'available',
    readiness: effectiveStatus,
    failure,
    art: effectiveStatus,
    erpnext: effectiveStatus === 'VALIDATED' ? 'report validated' : 'not validated',
    latestRunStatus: latestRun?.status || null,
    reasons,
  } as const;
}

export function getLocalBusinessDate(timezone = process.env.P02_TIMEZONE || 'Asia/Kolkata', now = new Date()) {
  return localBusinessDate(timezone, now);
}

export function isAdminConfigured() {
  return Boolean(
    (process.env.P02_ADMIN_USERNAME || process.env.ADMIN_USERNAME) &&
    (process.env.P02_ADMIN_PASSWORD || process.env.ADMIN_PASSWORD) &&
    (process.env.P02_SESSION_SECRET || process.env.SESSION_SECRET)
  );
}
