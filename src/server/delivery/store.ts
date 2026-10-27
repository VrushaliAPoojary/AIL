import 'server-only';
import { mkdir, readFile, rename, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import type { DeliverySettings, RunRecord } from './types';

type StoreData = {
  runs: RunRecord[];
  audit: Array<{ id: string; action: string; actor: string; at: string; runId?: string }>;
  settings: Partial<DeliverySettings> | null;
  chasers: import('./types').StagedChaserDraft[];
  promises: import('./types').SupplierPromise[];
};
const EMPTY: StoreData = { runs: [], audit: [], settings: null, chasers: [], promises: [] };
let writeChain = Promise.resolve();

function storePath() {
  return path.resolve(/*turbopackIgnore: true*/ process.env.P02_DATA_DIR || path.join(process.cwd(), '.data', 'p02-delivery'));
}

async function readDisk(): Promise<StoreData> {
  try {
    const parsed = JSON.parse(await readFile(path.join(storePath(), 'history.json'), 'utf8'));
    return {
      runs: Array.isArray(parsed.runs) ? parsed.runs : [],
      audit: Array.isArray(parsed.audit) ? parsed.audit : [],
      settings: parsed.settings && typeof parsed.settings === 'object' ? parsed.settings : null,
      chasers: Array.isArray(parsed.chasers) ? parsed.chasers : [],
      promises: Array.isArray(parsed.promises) ? parsed.promises : [],
    };
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') return structuredClone(EMPTY);
    throw new Error('Run history could not be read.');
  }
}

async function readStore(): Promise<StoreData> {
  await writeChain;
  return readDisk();
}

async function persist(data: StoreData) {
  const dir = storePath();
  await mkdir(dir, { recursive: true });
  const target = path.join(dir, 'history.json');
  const temp = `${target}.${randomUUID()}.tmp`;
  await writeFile(temp, JSON.stringify(data, null, 2), { encoding: 'utf8', mode: 0o600 });
  await rename(temp, target);
}

function transact<T>(update: (data: StoreData) => T | Promise<T>) {
  const operation = writeChain.then(async () => {
    const data = await readDisk();
    const result = await update(data);
    await persist(data);
    return result;
  });
  writeChain = operation.then(() => undefined, () => undefined);
  return operation;
}

export async function listRuns() {
  return (await readStore()).runs;
}

export async function getRun(id: string) {
  return (await readStore()).runs.find((run) => run.id === id) || null;
}

export async function findRunByIdempotencyKey(key: string) {
  return (await readStore()).runs.find((run) => run.idempotencyKey === key) || null;
}

export async function saveRun(record: RunRecord, actor = 'system', action = 'run.updated') {
  await transact((data) => {
    const index = data.runs.findIndex((run) => run.id === record.id);
    if (index >= 0) data.runs[index] = record;
    else data.runs.unshift(record);
    data.runs = data.runs.slice(0, 100);
    data.audit.unshift({ id: randomUUID(), action, actor, at: new Date().toISOString(), runId: record.id });
    data.audit = data.audit.slice(0, 500);
  });
}

export async function listAuditEvents() {
  return (await readStore()).audit;
}

export async function getSavedSettings() {
  return (await readStore()).settings;
}

export async function saveSettings(settings: Partial<DeliverySettings>, actor = 'admin') {
  return transact((data) => {
    data.settings = { ...data.settings, ...settings };
    data.audit.unshift({ id: randomUUID(), action: 'configuration.updated', actor, at: new Date().toISOString() });
    data.audit = data.audit.slice(0, 500);
    return data.settings;
  });
}

export async function listStagedChasers() {
  return (await readStore()).chasers;
}

export async function saveStagedChaser(chaser: import('./types').StagedChaserDraft, actor = 'buyer') {
  await transact((data) => {
    const index = data.chasers.findIndex((c) => c.id === chaser.id);
    if (index >= 0) data.chasers[index] = chaser;
    else data.chasers.unshift(chaser);
    data.chasers = data.chasers.slice(0, 200);
    data.audit.unshift({
      id: randomUUID(),
      action: 'chaser.staged',
      actor,
      at: new Date().toISOString(),
      runId: chaser.orderId,
    });
    data.audit = data.audit.slice(0, 500);
  });
}

export async function updateChaserStatus(id: string, status: 'APPROVED' | 'DISMISSED', actor = 'buyer') {
  return transact((data) => {
    const chaser = data.chasers.find((c) => c.id === id);
    if (!chaser) return null;
    chaser.status = status;
    if (status === 'APPROVED') {
      chaser.approvedAt = new Date().toISOString();
      chaser.approvedBy = actor;
    }
    data.audit.unshift({
      id: randomUUID(),
      action: status === 'APPROVED' ? 'chaser.approved' : 'chaser.dismissed',
      actor,
      at: new Date().toISOString(),
      runId: chaser.orderId,
    });
    data.audit = data.audit.slice(0, 500);
    return chaser;
  });
}

export async function listSupplierPromises() {
  return (await readStore()).promises;
}

export async function saveSupplierPromise(promise: import('./types').SupplierPromise, actor = 'buyer') {
  await transact((data) => {
    const index = data.promises.findIndex((p) => p.id === promise.id);
    if (index >= 0) data.promises[index] = promise;
    else data.promises.unshift(promise);
    data.promises = data.promises.slice(0, 200);
    data.audit.unshift({
      id: randomUUID(),
      action: 'promise.recorded',
      actor,
      at: new Date().toISOString(),
      runId: promise.orderId,
    });
    data.audit = data.audit.slice(0, 500);
  });
}

