# ART-SFN-001 — Serverless Function Not Available as Tool Action

- **Severity:** HIGH
- **Status:** OPEN

## Bug

A serverless function connected to the agent through Tool Connector does not appear in Governance → Action Registry when the action capability is changed to Tool Action.

The workflow was built and published successfully, but the Tool selector still displays “No matches.”

## Expected

A connected and published serverless function should be selectable as the Tool Action target so its deterministic output can be governed by policy rules and Human Review.

## Actual

The serverless function executes successfully from the workflow, but it is unavailable in the Action Registry Tool selector.

This prevents the function from being directly bound to the governed action.

## Evidence

- [ART-SFN-001__workflow-tool-connector__2026-09-24__01.png](ART-SFN-001__workflow-tool-connector__2026-09-24__01.png)
- [ART-SFN-001__action-registry-no-matches__2026-09-24__02.png](ART-SFN-001__action-registry-no-matches__2026-09-24__02.png)

## Production-Grade Fix Proposal

Published serverless functions connected to an agent workflow must be discoverable and selectable as governed Tool Actions.

### Required implementation

1. Register every successfully published serverless function in a central capability registry.
2. Store:
   - Function ID
   - Published version
   - Function name
   - Provider
   - Entrypoint
   - Input schema
   - Output schema
   - Owning workspace
   - Environment
   - Publication status
   - Agent bindings
   - Governance eligibility
3. Tool Connector and Action Registry must query the same capability registry.
4. Only published and active function versions should appear in Tool Action selection.
5. Filter available functions by workspace, environment, permissions, and agent binding.
6. When no function is available, replace the generic `No matches` message with a diagnostic reason:
   - Function not published
   - Wrong environment
   - Not connected to this agent
   - Missing permission
   - Unsupported capability type
   - Registry synchronization failure
7. When Build and Publish completes, update the registry atomically and invalidate relevant caches.
8. Provide a manual registry refresh option for administrators.
9. Preserve the selected function version in the governed action definition.
10. Prevent silent version switching after deployment.
11. Validate function input and output schemas before allowing the action to be saved.
12. Show the serverless function as a first-class Tool Action without requiring users to recreate it as another tool.

### Acceptance criteria

- A published and connected serverless function appears in Tool Action selection.
- Search finds the function by name and function ID.
- Unavailable functions display a specific diagnostic reason.
- Registry refresh does not require recreating the function.
- The selected version remains locked after publishing.
- Input and output schemas are available for policy facts and mappings.
- Workspace and environment isolation are enforced.
- The governed action successfully invokes the selected serverless function.

## Developer Update

## Retest

## Azure DevOps

- **Work Item ID:** 68834
- **URL:** https://dev.azure.com/BixBytesSolutions/f3253417-808e-457f-a7f2-5699b2f38aa6/_apis/wit/workItems/68834
- **Parent Feature:** Serverless Functions
- **Parent Feature ID:** 68811
- **Assigned To:** Unassigned
- **Sync Status:** SYNCED

## Resolution Status

- **ART Disposition:** OPEN
- **Azure State:** New
- **Azure Reason:** New
- **Retest Required:** NO
- **Action Required:** AWAIT_DEVELOPER
- **Last Azure Sync:** 2026-10-12T06:45:18.031880+00:00


## Resolution History

### 2026-10-12 — Azure Lifecycle Update

Azure Work Item: #68834
Azure State: New
Azure Reason: New
Changed By: Chiranjeevi P.K

Developer Feedback:

Not provided

ART Assessment:

OPEN

Retest Required:

NO

Action Required:

AWAIT_DEVELOPER

Assessment Reason:

Issue remains open in Azure with no implementation or resolution claim established.
