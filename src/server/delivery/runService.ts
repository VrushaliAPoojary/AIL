import 'server-only';
import { executeArtMonitoring } from './art';
import { createRunController } from './runController';
import { findRunByIdempotencyKey, listRuns, saveRun } from './store';
import { demoOrders } from './data';
import { getDeliverySettings } from './config';
import { localBusinessDate } from './date';
import type { RunRecord } from './types';

async function executeRun(run: RunRecord) {
  if (run.source === 'demo') {
    const settings = await getDeliverySettings();
    const today = localBusinessDate(settings.timezone);
    return { purchaseOrders: demoOrders(today), simulated: true };
  }
  return await executeArtMonitoring(run);
}

const controller = createRunController({
  findByIdempotencyKey: findRunByIdempotencyKey,
  list: listRuns,
  save: saveRun,
  execute: executeRun,
});

export const startMonitoringRun = controller.start;
export const getRunHistory = controller.getHistory;
