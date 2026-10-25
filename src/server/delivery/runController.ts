import { randomUUID } from 'node:crypto';
import type { RunRecord } from './types';

type Dependencies = {
  findByIdempotencyKey: (key: string) => Promise<RunRecord | null>;
  list: () => Promise<RunRecord[]>;
  save: (run: RunRecord, actor: string, action: string) => Promise<void>;
  execute: (run: RunRecord) => Promise<unknown>;
  createId?: () => string;
  now?: () => string;
};

export function createRunController(deps: Dependencies) {
  let activeRunId: string | null = null;
  let startLock = Promise.resolve();
  const createId = deps.createId || randomUUID;
  const now = deps.now || (() => new Date().toISOString());

  async function getHistory() {
    const current = await deps.list();
    if (activeRunId) return current;
    const stale = current.filter((run) => run.status === 'QUEUED' || run.status === 'RUNNING');
    for (const run of stale) {
      await deps.save({ ...run, status: 'FAILED', finishedAt: now(), error: 'The server restarted before a final ART response was recorded.' }, 'system', 'run.interrupted');
    }
    return stale.length ? deps.list() : current;
  }

  async function start(idempotencyKey: string) {
    let release!: () => void;
    const previous = startLock;
    startLock = new Promise((resolve) => { release = resolve; });
    await previous;
    let run: RunRecord;
    try {
      const existing = await deps.findByIdempotencyKey(idempotencyKey);
      if (existing) return { run: existing, reused: true };
      if (activeRunId) throw Object.assign(new Error('A monitoring run is already in progress.'), { status: 409 });
      const allRuns = await getHistory();
      if (allRuns.some((item) => item.status === 'QUEUED' || item.status === 'RUNNING')) {
        throw Object.assign(new Error('A monitoring run is already queued or running.'), { status: 409 });
      }
      run = { id: createId(), idempotencyKey, status: 'QUEUED', startedAt: now(), finishedAt: null, source: 'art', result: null, error: null };
      activeRunId = run.id;
      try { await deps.save(run, 'admin', 'run.queued'); }
      catch (error) { activeRunId = null; throw error; }
    } finally {
      release();
    }
    void executeAndPersist(run!);
    return { run: run!, reused: false };
  }

  async function executeAndPersist(initial: RunRecord) {
    let run: RunRecord = { ...initial, status: 'RUNNING' };
    try {
      await deps.save(run, 'admin', 'run.started');
      const result = await deps.execute(run);
      run = { ...run, status: 'SUCCEEDED', finishedAt: now(), result };
      await deps.save(run, 'admin', 'run.succeeded');
    } catch (error) {
      run = { ...run, status: 'FAILED', finishedAt: now(), error: error instanceof Error ? error.message : 'ART execution failed.' };
      try { await deps.save(run, 'admin', 'run.failed'); } catch { /* A failed local store cannot safely turn this into success. */ }
    } finally {
      activeRunId = null;
    }
  }

  return { start, getHistory };
}
