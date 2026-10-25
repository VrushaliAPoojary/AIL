import type { DeliverySettings } from './types';

export function validateSettings(input: unknown): Pick<DeliverySettings, 'upcomingDays' | 'dueDateBasis' | 'timezone'> {
  if (!input || typeof input !== 'object' || Array.isArray(input)) throw new Error('Settings must be a JSON object.');
  const value = input as Record<string, unknown>;
  if (!Number.isInteger(value.upcomingDays) || Number(value.upcomingDays) < 1 || Number(value.upcomingDays) > 90) throw new Error('Upcoming window must be from 1 to 90 days.');
  if (value.dueDateBasis !== 'contractual' && value.dueDateBasis !== 'supplier_promise') throw new Error('Choose a supported due-date basis.');
  if (typeof value.timezone !== 'string' || value.timezone.length > 100) throw new Error('Timezone is required.');
  try { new Intl.DateTimeFormat('en-US', { timeZone: value.timezone }); } catch { throw new Error('Timezone must be a valid IANA timezone.'); }
  return { upcomingDays: Number(value.upcomingDays), dueDateBasis: value.dueDateBasis, timezone: value.timezone };
}
