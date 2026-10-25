import 'server-only';
import type { DeliverySettings } from './types';
import { getSavedSettings } from './store';
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
    process.env.ART_URI && process.env.ART_CLIENT_ID && process.env.ART_CLIENT_SECRET &&
    process.env.ART_ORG_TITLE && process.env.ART_ENVIRONMENT && process.env.ART_PROJECT_KEY &&
    process.env.ART_AGENT_ID,
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
  const readiness = getIntegrationReadiness(settings.mode === 'configured');
  return {
    mode: settings.mode,
    backend: 'available',
    readiness: readiness.status,
    failure: readiness.failure,
    art: readiness.status,
    erpnext: readiness.status === 'VALIDATED' ? 'report validated' : 'not validated',
    reasons: settings.mode === 'configured' ? [] : [
      'Configure the ART connection and target agent in the server environment.',
      'ERPNext is accessed through the configured ART agent tools; no direct ERPNext credentials are configured here.',
    ],
  } as const;
}

export function getLocalBusinessDate(timezone = process.env.P02_TIMEZONE || 'Asia/Kolkata', now = new Date()) {
  return localBusinessDate(timezone, now);
}

export function isAdminConfigured() {
  return Boolean(process.env.P02_ADMIN_USERNAME && process.env.P02_ADMIN_PASSWORD && process.env.P02_SESSION_SECRET);
}
