# ART-GOV-003 — Duplicate Human Approval Request After Decision

- **Severity:** HIGH
- **Status:** OPEN

## Bug

After a reviewer approves or rejects an Implant Usage Evidence Review request, the agent can invoke the same governed action again and create another approval notification for the same case.

The previous approval request is resolved, but the workflow does not reliably continue to a final outcome.

## Expected

Each case should create only one Human Review request.

After the reviewer selects Approve or Reject, the agent should resume from that decision, return the final outcome and must not invoke the same governed action again for the same case.

## Actual

A new approval notification can be generated after the previous human decision, resulting in a repeated approval loop.

## Evidence

- [ART-GOV-003__duplicate-approval-notification__2026-09-24__01.png](ART-GOV-003__duplicate-approval-notification__2026-09-24__01.png)
- [ART-GOV-003__approval-loop-decision__2026-09-24__02.png](ART-GOV-003__approval-loop-decision__2026-09-24__02.png)

## Production-Grade Fix Proposal

A Human Review decision must resume the suspended execution exactly once and must never create another approval request for the same action execution.

### Required implementation

1. Assign a unique `action_execution_id` to every governed action invocation.
2. Create an approval request using an idempotency key derived from:
   - Agent execution ID
   - Action execution ID
   - Policy ID
3. Enforce a unique database constraint on the approval idempotency key.
4. When Human Review is required:
   - Persist the execution state.
   - Mark it `WAITING_FOR_HUMAN`.
   - Stop further agent reasoning and action invocation.
5. When the reviewer approves or rejects:
   - Persist the decision atomically.
   - Mark the approval request resolved.
   - Resume the original suspended execution from its saved continuation point.
6. Do not restart the agent from the original user prompt after the decision.
7. Pass the approval decision as a trusted system event, not as a new conversational user message.
8. Before creating any approval request, check whether the action execution already has:
   - A pending request
   - An approved decision
   - A rejected decision
9. If a decision already exists, return the stored decision instead of invoking Human Review again.
10. Ignore duplicate button clicks, retry deliveries, and repeated decision events using the same idempotency key.
11. Record request creation, decision, resumption, and completion in one audit trail.

### Acceptance criteria

- One governed action execution creates no more than one approval request.
- Approving does not generate another notification.
- Rejecting does not generate another notification.
- The original execution resumes rather than restarting.
- Duplicate clicks do not create duplicate decisions.
- Event retries do not create duplicate requests.
- The final Agent Result references the original approval decision.
- The audit trail shows one request, one decision, and one continuation.

## Developer Update

## Retest

## Azure DevOps

- **Work Item ID:** 68833
- **URL:** https://dev.azure.com/BixBytesSolutions/f3253417-808e-457f-a7f2-5699b2f38aa6/_apis/wit/workItems/68833
- **Parent Feature:** Governance
- **Parent Feature ID:** 68812
- **Assigned To:** Unassigned
- **Sync Status:** SYNCED

## Resolution Status

- **ART Disposition:** OPEN
- **Azure State:** New
- **Azure Reason:** New
- **Retest Required:** NO
- **Action Required:** AWAIT_DEVELOPER
- **Last Azure Sync:** 2026-10-12T06:45:07.318685+00:00


## Resolution History

### 2026-10-12 — Azure Lifecycle Update

Azure Work Item: #68833
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
