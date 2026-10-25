import 'server-only';
import { executeArtMonitoring } from './art';
import { createRunController } from './runController';
import { findRunByIdempotencyKey, listRuns, saveRun } from './store';

const controller = createRunController({
  findByIdempotencyKey: findRunByIdempotencyKey,
  list: listRuns,
  save: saveRun,
  execute: executeArtMonitoring,
});

export const startMonitoringRun = controller.start;
export const getRunHistory = controller.getHistory;
