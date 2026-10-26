export async function waitForAdkConnection(adk: any, timeoutMs = 20_000, intervalMs = 250) {
  if (!adk || typeof adk.getState !== 'function') throw new Error('Invalid ADK instance: missing getState method.');
  const deadline = Date.now() + timeoutMs;
  while (adk.getState() !== 'connected' && Date.now() < deadline) {
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  if (adk.getState() !== 'connected') throw new Error('ART connection did not become ready before timeout.');
}

export async function awaitAdkRun(run: { done?: () => Promise<unknown> } | null | undefined, timeoutMs = 120_000) {
  if (!run || typeof run.done !== 'function') {
    throw new Error('ART agent execution failed: thread.run() did not return an active run instance with done().');
  }
  let timeout: ReturnType<typeof setTimeout> | undefined;
  const timeoutMessage = timeoutMs < 1_000 ? 'ART agent run timed out.' : `ART agent run timed out after ${Math.round(timeoutMs / 1000)} seconds.`;
  return Promise.race([
    run.done(),
    new Promise<never>((_, reject) => { timeout = setTimeout(() => reject(new Error(timeoutMessage)), timeoutMs); }),
  ]).finally(() => { if (timeout) clearTimeout(timeout); });
}

export async function executeAgentRun(adk: any, agentId: string, prompt: string, timeoutMs = 120_000, onConnected?: () => void) {
  if (!agentId || typeof agentId !== 'string' || !agentId.trim()) {
    throw new Error('ART agent ID is missing or invalid.');
  }
  await waitForAdkConnection(adk);
  onConnected?.();
  const agent = adk.agent(agentId.trim()).connect();
  const execution = await agent.thread().run(prompt);
  return await awaitAdkRun(execution, timeoutMs);
}

export function sanitizeArtUri(uri: string): string {
  return uri.trim().replace(/^(https?|wss?):\/\//i, '').replace(/\/+$/, '');
}
