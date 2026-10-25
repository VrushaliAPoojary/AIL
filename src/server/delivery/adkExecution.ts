export async function waitForAdkConnection(adk: any, timeoutMs = 20_000, intervalMs = 250) {
  const deadline = Date.now() + timeoutMs;
  while (adk.getState() !== 'connected' && Date.now() < deadline) {
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  if (adk.getState() !== 'connected') throw new Error('ART connection did not become ready before timeout.');
}

export async function awaitAdkRun(run: { done(): Promise<unknown> }, timeoutMs = 120_000) {
  let timeout: ReturnType<typeof setTimeout> | undefined;
  const timeoutMessage = timeoutMs < 1_000 ? 'ART agent run timed out.' : `ART agent run timed out after ${Math.round(timeoutMs / 1000)} seconds.`;
  return Promise.race([
    run.done(),
    new Promise<never>((_, reject) => { timeout = setTimeout(() => reject(new Error(timeoutMessage)), timeoutMs); }),
  ]).finally(() => { if (timeout) clearTimeout(timeout); });
}

export async function executeAgentRun(adk: any, agentId: string, prompt: string, timeoutMs = 120_000, onConnected?: () => void) {
  await waitForAdkConnection(adk);
  onConnected?.();
  const agent = adk.agent(agentId).connect();
  const execution = await agent.thread().run(prompt);
  return await awaitAdkRun(execution, timeoutMs);
}
