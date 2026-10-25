# ART-GOV-002 — Human Review Displays Unresolved Runtime Variables

- **Severity:** HIGH
- **Status:** OPEN

## Bug

The Human Review notification displays unresolved template variables instead of the actual runtime values generated during implant reconciliation agent.

Examples displayed in the notification include:

- `${IMPLANT_CASE_ID}`
- `${RECONCILIATION_CLASSIFICATION}`
- `${RECONCILIATION_MATCH_STATUS}`
- `${RECONCILIATION_REASON}`
- `${RECOMMENDED_NEXT_OWNER}`

The agent result and serverless-function result contain the correct values, but those values are not resolved inside the Human Review notification.

## Expected

The Human Review notification should display the actual case ID, classification, match status, reconciliation reason and recommended owner produced during the current execution.

## Actual

The notification displays the template expressions as literal text, making the review information unreadable and preventing the reviewer from making an informed decision.

## Evidence

- [ART-GOV-002__unresolved-template-values__2026-09-24__01.png](ART-GOV-002__unresolved-template-values__2026-09-24__01.png)

## Production-Grade Fix Proposal

Human Review must receive resolved runtime facts, not unresolved template expressions.

### Required implementation

1. Store Human Review mappings as typed references to registered facts, not as plain text containing `${...}`.
2. Validate every mapped fact when the policy is saved.
3. Validate every mapped fact again during Build and Publish.
4. Resolve all fact references from the current action-execution context before creating the review request.
5. Preserve the resolved values as an immutable approval snapshot.
6. If a required fact is missing or unresolved:
   - Do not create the Human Review request.
   - Stop execution with `HUMAN_REVIEW_FACT_RESOLUTION_FAILED`.
   - Identify the exact missing fact and its source action.
7. Never display unresolved expressions such as `${IMPLANT_CASE_ID}` to reviewers.
8. Provide a mapping preview containing representative typed values before publishing.
9. Display human-readable labels in the reviewer interface while retaining technical keys in the audit view.
10. Support structured fields such as arrays and objects with readable tables instead of raw serialized text.
11. Record the source action, fact key, resolved value, data type, execution ID, and resolution timestamp in the audit log.

### Acceptance criteria

- Every configured field displays its resolved runtime value.
- No `${...}` expression appears in a Human Review notification.
- Missing required facts block request creation.
- The reviewer sees readable labels and formatted values.
- Arrays and objects render as structured content.
- The approval snapshot cannot change after the request is created.
- The audit log identifies the source of every resolved fact.

## Developer Update

## Retest

## Azure DevOps

- **Work Item ID:** 68832
- **URL:** https://dev.azure.com/BixBytesSolutions/f3253417-808e-457f-a7f2-5699b2f38aa6/_apis/wit/workItems/68832
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
- **Last Azure Sync:** 2026-10-12T06:45:06.653684+00:00


## Resolution History

### 2026-10-12 — Azure Lifecycle Update

Azure Work Item: #68832
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
