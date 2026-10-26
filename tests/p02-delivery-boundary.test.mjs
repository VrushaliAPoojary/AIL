import assert from 'node:assert/strict';
import test from 'node:test';
import { createAdminSessionToken, verifyAdminCredentials, verifyAdminSessionToken } from '../src/server/delivery/authCore.ts';
import { waitForAdkConnection, awaitAdkRun, executeAgentRun } from '../src/server/delivery/adkExecution.ts';
import { normalizeAgentReport } from '../src/server/delivery/artContract.ts';
import { localBusinessDate } from '../src/server/delivery/date.ts';
import { createRunController } from '../src/server/delivery/runController.ts';
import { validateSettings } from '../src/server/delivery/settingsValidation.ts';
import { getIntegrationReadiness, setIntegrationReadiness } from '../src/server/delivery/readiness.ts';
import { publicRunRecord } from '../src/server/delivery/types.ts';

test('admin credentials require exact configured username and password and reject oversized values', () => {
  assert.equal(verifyAdminCredentials('buyer', 'correct-horse', 'buyer', 'correct-horse'), true);
  assert.equal(verifyAdminCredentials('buyer', 'wrong', 'buyer', 'correct-horse'), false);
  assert.equal(verifyAdminCredentials('buyer', 'correct-horse ', 'buyer', 'correct-horse'), false);
  assert.equal(verifyAdminCredentials('x'.repeat(121), 'correct-horse', 'buyer', 'correct-horse'), false);
});

test('administrator session tokens are signed, expire, and reject tampering', () => {
  const token = createAdminSessionToken('buyer', 'a-secret-for-tests', 1_000, 60);
  assert.deepEqual(verifyAdminSessionToken(token, 'a-secret-for-tests', 2_000), { username: 'buyer', role: 'admin', exp: 61_000 });
  assert.equal(verifyAdminSessionToken(token, 'a-secret-for-tests', 61_000), null);
  assert.equal(verifyAdminSessionToken(`${token}x`, 'a-secret-for-tests', 2_000), null);
  assert.equal(verifyAdminSessionToken(token, 'another-secret', 2_000), null);
});

test('integration readiness distinguishes demo, configured, connected, validated, and failed states', () => {
  assert.deepEqual(getIntegrationReadiness(false), { status: 'DEMO', failure: null });
  assert.deepEqual(getIntegrationReadiness(true), { status: 'CONFIGURED', failure: null });
  setIntegrationReadiness('CONNECTING');
  assert.equal(getIntegrationReadiness(true).status, 'CONNECTING');
  setIntegrationReadiness('CONNECTED');
  assert.equal(getIntegrationReadiness(true).status, 'CONNECTED');
  setIntegrationReadiness('VALIDATED');
  assert.equal(getIntegrationReadiness(true).status, 'VALIDATED');
  setIntegrationReadiness('FAILED', 'CONNECTION_FAILED');
  assert.deepEqual(getIntegrationReadiness(true), { status: 'FAILED', failure: 'CONNECTION_FAILED' });
});

test('public run records never expose raw failed-run errors', () => {
  const publicRun = publicRunRecord({ id: 'run-1', idempotencyKey: 'key-1', status: 'FAILED', startedAt: 'now', finishedAt: 'now', source: 'art', result: null, error: 'secret=must-not-leak' });
  assert.equal(publicRun.error, 'Run failed. Check server-side logs for details.');
  assert.equal(JSON.stringify(publicRun).includes('must-not-leak'), false);
});

test('ADK connection wait tolerates stopped and retrying states until connected', async () => {
  const states = ['stopped', 'retrying', 'connected'];
  const adk = { getState: () => states.shift() || 'connected' };
  await waitForAdkConnection(adk, 100, 1);
});

test('ADK connection failure returns unavailable after its deadline', async () => {
  await assert.rejects(() => waitForAdkConnection({ getState: () => 'retrying' }, 2, 1), /did not become ready/);
});

test('ADK run resolves only its final result and enforces a timeout', async () => {
  assert.deepEqual(await awaitAdkRun({ done: async () => ({ report: 'final' }) }, 100), { report: 'final' });
  await assert.rejects(() => awaitAdkRun({ done: () => new Promise(() => {}) }, 2), /timed out/);
});

test('ADK invocation awaits the promise returned by thread.run before calling done', async () => {
  const calls = [];
  const expectedRun = { done: async () => { calls.push('done'); return { result: 'final' }; } };
  const adk = {
    getState: () => 'connected',
    agent: (id) => ({ connect: () => ({ thread: () => ({ run: async (prompt) => {
      calls.push(`run:${id}:${prompt}`);
      await Promise.resolve();
      return expectedRun;
    } }) }) }),
  };
  assert.deepEqual(await executeAgentRun(adk, 'agent-1', 'read only', 100), { result: 'final' });
  assert.deepEqual(calls, ['run:agent-1:read only', 'done']);
});

test('ADK invocation propagates a rejected thread.run promise', async () => {
  const adk = {
    getState: () => 'connected',
    agent: () => ({ connect: () => ({ thread: () => ({ run: async () => { throw new Error('agent run rejected'); } }) }) }),
  };
  await assert.rejects(() => executeAgentRun(adk, 'agent-1', 'read only', 100), /agent run rejected/);
});

test('P02 report normalizer accepts only the expected report and preserves source linkage', () => {
  const report = normalizeAgentReport({ purchaseOrders: [{ id: 'PO-1', supplier: 'Vendor', docstatus: 1, items: [{
    id: 'POI-1', itemCode: 'SKU-1', orderedQuantity: 4, scheduleDate: '2026-10-25', expectedDeliveryDate: null,
    receiptRetrieval: { scope: { purchaseOrderId: 'PO-1', purchaseOrderItemId: 'POI-1' }, complete: true, pagesRetrieved: 2, hasMore: false, sourceToolId: 'tool-source-1', sourceResponseId: 'response-1' },
    receipts: [{ receiptId: 'PR-1', receiptItemId: 'PRI-1', purchaseOrderId: 'PO-1', purchaseOrderItemId: 'POI-1', quantity: 2, docstatus: 1 }],
  }] }] });
  assert.equal(report.purchaseOrders[0].items[0].receipts[0].purchaseOrderItemId, 'POI-1');
  assert.equal(report.purchaseOrders[0].items[0].receiptRetrieval.pagesRetrieved, 2);
  assert.equal(report.purchaseOrders[0].items[0].receiptRetrieval.sourceResponseId, 'response-1');
});

test('P02 report normalizer rejects malformed or missing evidence contracts', () => {
  assert.throws(() => normalizeAgentReport({ text: 'finished' }), /did not match/);
  assert.throws(() => normalizeAgentReport({ purchaseOrders: [{ supplier: 'Vendor', items: [] }] }), /source id/);
  const report = normalizeAgentReport({ purchaseOrders: [{ id: 'PO-1', supplier: 'Vendor', items: [{ id: 'POI-1', receipts: [] }] }] });
  assert.equal(report.purchaseOrders[0].items[0].receiptRetrieval, null);
});

test('configuration validation constrains the upcoming window, due-date basis, and timezone', () => {
  assert.deepEqual(validateSettings({ upcomingDays: 14, dueDateBasis: 'supplier_promise', timezone: 'Asia/Kolkata' }), {
    upcomingDays: 14, dueDateBasis: 'supplier_promise', timezone: 'Asia/Kolkata',
  });
  assert.throws(() => validateSettings({ upcomingDays: 0, dueDateBasis: 'contractual', timezone: 'UTC' }), /1 to 90/);
  assert.throws(() => validateSettings({ upcomingDays: 7, dueDateBasis: 'invented', timezone: 'UTC' }), /supported due-date/);
  assert.throws(() => validateSettings({ upcomingDays: 7, dueDateBasis: 'contractual', timezone: 'Mars/Olympus' }), /IANA timezone/);
});

test('monitoring date is computed in the configured timezone, including midnight rollover', () => {
  assert.equal(localBusinessDate('Asia/Kolkata', new Date('2026-10-24T20:00:00.000Z')), '2026-10-25');
  assert.equal(localBusinessDate('America/Chicago', new Date('2026-10-25T04:00:00.000Z')), '2026-10-24');
});

test('run controller reuses idempotent requests and prevents overlapping runs', async () => {
  const runs = [];
  const events = [];
  let executeCount = 0;
  let nextId = 0;
  let finishRun;
  const finalResult = new Promise((resolve) => { finishRun = resolve; });
  const controller = createRunController({
    findByIdempotencyKey: async (key) => runs.find((run) => run.idempotencyKey === key) || null,
    list: async () => [...runs],
    save: async (record, actor, action) => {
      const index = runs.findIndex((run) => run.id === record.id);
      if (index < 0) runs.unshift(record); else runs[index] = record;
      events.push({ actor, action });
    },
    execute: async () => { executeCount += 1; return finalResult; },
    createId: () => `run-${++nextId}`,
    now: () => '2026-10-25T00:00:00.000Z',
  });
  const first = await controller.start('manual-click-0001');
  const duplicate = await controller.start('manual-click-0001');
  assert.equal(duplicate.reused, true);
  assert.equal(duplicate.run.id, first.run.id);
  assert.equal(executeCount, 1);
  await assert.rejects(() => controller.start('manual-click-0002'), (error) => error.status === 409);
  finishRun({ purchaseOrders: [] });
  for (let i = 0; i < 20 && runs[0]?.status !== 'SUCCEEDED'; i += 1) await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(runs[0].status, 'SUCCEEDED');
  assert.deepEqual(events.map((event) => event.action), ['run.queued', 'run.started', 'run.succeeded']);
  assert.equal((await controller.start('manual-click-0002')).reused, false);
});

test('run controller marks an unfinished record failed after process restart', async () => {
  const stale = { id: 'old-run', idempotencyKey: 'old-key', status: 'RUNNING', startedAt: '2026-10-24T00:00:00.000Z', finishedAt: null, source: 'art', result: null, error: null };
  const runs = [stale];
  const controller = createRunController({
    findByIdempotencyKey: async (key) => runs.find((run) => run.idempotencyKey === key) || null,
    list: async () => [...runs],
    save: async (record) => { runs[0] = record; },
    execute: async () => null,
    now: () => '2026-10-25T00:00:00.000Z',
  });
  const recovered = await controller.getHistory();
  assert.equal(recovered[0].status, 'FAILED');
  assert.match(recovered[0].error, /server restarted/);
});

test('run controller records ART failures and never marks them successful', async () => {
  const runs = [];
  const controller = createRunController({
    findByIdempotencyKey: async (key) => runs.find((run) => run.idempotencyKey === key) || null,
    list: async () => [...runs],
    save: async (record) => { const index = runs.findIndex((run) => run.id === record.id); if (index < 0) runs.unshift(record); else runs[index] = record; },
    execute: async () => { throw new Error('ART unavailable'); },
    createId: () => 'failed-run',
  });
  await controller.start('manual-failure-01');
  for (let i = 0; i < 20 && runs[0]?.status !== 'FAILED'; i += 1) await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(runs[0].status, 'FAILED');
  assert.equal(runs[0].error, 'ART unavailable');
  assert.equal(runs[0].result, null);
});

test('sanitizeArtUri strips scheme prefixes and trailing slashes', async () => {
  const { sanitizeArtUri } = await import('../src/server/delivery/adkExecution.ts');
  assert.equal(sanitizeArtUri('https://api.art.ai/'), 'api.art.ai');
  assert.equal(sanitizeArtUri('wss://gateway.art.ai///'), 'gateway.art.ai');
  assert.equal(sanitizeArtUri('http://localhost:8080'), 'localhost:8080');
  assert.equal(sanitizeArtUri('ws://127.0.0.1:9000/'), '127.0.0.1:9000');
  assert.equal(sanitizeArtUri('  art.example.com  '), 'art.example.com');
});

test('executeAgentRun rejects invalid adk instance, empty agent ID, or invalid run', async () => {
  await assert.rejects(() => executeAgentRun(null, 'agent-1', 'prompt', 100), /invalid adk instance/i);
  await assert.rejects(() => executeAgentRun({ getState: () => 'connected' }, '', 'prompt', 100), /agent id is missing/i);
  await assert.rejects(() => executeAgentRun({ getState: () => 'connected' }, '   ', 'prompt', 100), /agent id is missing/i);

  const adkWithBadRun = {
    getState: () => 'connected',
    agent: () => ({ connect: () => ({ thread: () => ({ run: async () => ({}) }) }) }),
  };
  await assert.rejects(() => executeAgentRun(adkWithBadRun, 'agent-1', 'prompt', 100), /did not return an active run instance/i);
});

test('run controller executes simulated demo run with source: demo and distinct demo audit actions', async () => {
  const runs = [];
  const events = [];
  const controller = createRunController({
    findByIdempotencyKey: async (key) => runs.find((r) => r.idempotencyKey === key) || null,
    list: async () => [...runs],
    save: async (record, actor, action) => {
      const idx = runs.findIndex((r) => r.id === record.id);
      if (idx < 0) runs.unshift(record); else runs[idx] = record;
      events.push({ actor, action, source: record.source });
    },
    execute: async (r) => ({ purchaseOrders: [], simulated: true }),
    createId: () => 'demo-run-001',
    now: () => '2026-10-26T00:00:00.000Z',
  });

  const started = await controller.start('demo-key-1', 'demo');
  assert.equal(started.reused, false);
  assert.equal(started.run.source, 'demo');
  for (let i = 0; i < 20 && runs[0]?.status !== 'SUCCEEDED'; i += 1) await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(runs[0].status, 'SUCCEEDED');
  assert.equal(runs[0].source, 'demo');
  assert.deepEqual(events.map((e) => e.action), ['run.demo_queued', 'run.demo_started', 'run.demo_succeeded']);
  assert.equal(events.every((e) => e.actor === 'demo-user'), true);
});

test('delivery classification in demo mode preserves explicit demo and synthetic labeling', () => {
  const readiness = getIntegrationReadiness(false);
  assert.equal(readiness.status, 'DEMO');
  assert.equal(readiness.failure, null);
});
