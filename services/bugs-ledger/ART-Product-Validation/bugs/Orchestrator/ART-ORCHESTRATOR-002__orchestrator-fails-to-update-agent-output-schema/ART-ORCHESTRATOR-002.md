# ART-ORCHESTRATOR-002 — Orchestrator Downstream Nodes Display Stale Agent Output Schema After Update

- **Canonical Bug ID:** ART-ORCHESTRATOR-002
- **Title:** Orchestrator Downstream Nodes Display Stale Agent Output Schema After Update
- **Module:** ORCHESTRATOR
- **Status:** OPEN
- **Severity:** HIGH
- **Priority:** P1
- **Assignee:** Unassigned
- **Environment:** Testing / InvestigationLab
- **Tags:** Orchestrator, Agent-Lab, Schema-Validation, Workflow-Routing, State-Consistency

## Problem

When an Agent's output message schema is updated and saved with new fields (such as `media_status`, `media_summary`, `observed_facts`, and `reported_facts`), downstream nodes in the Orchestration (including Condition Builder, Data Mapper, and Serverless Function mapping) do not reflect the new fields. Even after saving the agent, rebuilding/publishing the orchestration, and performing a hard refresh, the orchestrator continues displaying outdated schema fields (such as `classification`, `inferences`, `missing_information`, `ready_for_ticket`, `ticket.*`, and stale `facts`). This prevents updated agent output data from being mapped or utilized across workflow steps.

## Bug

In the Ticket Resolution Agent, updated and saved output schema fields such as `media_status`, `media_summary`, `observed_facts`, and `reported_facts` fail to propagate to the Ticket Resolution Orchestration. Even after saving the agent, rebuilding/publishing the orchestration, and hard refreshing, downstream nodes such as the Condition Builder, Data Mapper, and Serverless Function mapping only display stale, legacy fields (`classification`, `inferences`, `missing_information`, `ready_for_ticket`, `ticket.*`, and stale `facts`). As a result, latest Agent output values cannot be mapped or used downstream.

## Expected

The Orchestrator should use the Agent's latest saved/published output schema and expose all updated fields correctly to downstream nodes upon save, rebuild/publish, or schema refresh.

## Expected Result

The Orchestrator should use the Agent's latest saved/published output schema and expose all updated fields correctly to downstream nodes upon save, rebuild/publish, or schema refresh.

## Actual

Downstream nodes in the Orchestration retain stale, cached schema definitions and do not expose newly configured fields (`media_status`, `media_summary`, `observed_facts`, `reported_facts`), continuing to display legacy fields (`classification`, `inferences`, `missing_information`, `ready_for_ticket`, `ticket.*`, and stale `facts`).

## Actual Result

Downstream nodes in the Orchestration retain stale, cached schema definitions and do not expose newly configured fields (`media_status`, `media_summary`, `observed_facts`, `reported_facts`), continuing to display legacy fields (`classification`, `inferences`, `missing_information`, `ready_for_ticket`, `ticket.*`, and stale `facts`).

## Business Impact

Workflows relying on updated agent capabilities cannot access new output data, preventing automated ticket processing, multi-modal media status handling, and fact-based routing. This blocks feature rollout and breaks end-to-end orchestration pipelines.

## User Experience

Users configure new output fields in Agent Lab expecting them to be available in the workflow Orchestration. However, dropdowns in Data Mapper and Condition Builder omit the new fields and display obsolete structures, causing confusion and blocking workflow completion despite rebuilding and refreshing.

## Recommended Solution

Implement reactive schema synchronization and cache invalidation between Agent Lab and Workflow Orchestrator:

1. Invalidate Orchestrator node schema caches whenever an underlying Agent definition or output schema is saved or published.
2. Implement schema version tracking on Agent nodes so Orchestration workflows detect when an agent node schema is out of date.
3. Ensure Build and Publish re-fetches canonical output schemas for all referenced workflow agent nodes before compiling downstream port definitions.
4. Provide an explicit "Refresh Node Schema" or "Sync Agent Schema" action in the Orchestrator node configuration drawer.
5. Update Data Mapper and Condition Builder source field resolvers to pull schema definitions directly from the active agent version rather than stale session state.

## Production-Grade Fix Proposal

Implement reactive schema synchronization and cache invalidation between Agent Lab and Workflow Orchestrator:

### Required implementation

1. Invalidate Orchestrator node schema caches whenever an underlying Agent definition or output schema is saved or published.
2. Implement schema version tracking on Agent nodes so Orchestration workflows detect when an agent node schema is out of date.
3. Ensure Build and Publish re-fetches canonical output schemas for all referenced workflow agent nodes before compiling downstream port definitions.
4. Provide an explicit "Refresh Node Schema" or "Sync Agent Schema" action in the Orchestrator node configuration drawer.
5. Update Data Mapper and Condition Builder source field resolvers to pull schema definitions directly from the active agent version rather than stale session state.

### Acceptance criteria

- Saving changes to an Agent's output schema propagates updated fields to the Orchestration workflow.
- Newly added agent output fields appear immediately in downstream Data Mapper source field pickers.
- Newly added agent output fields are selectable in Condition Builder routing rules.
- Rebuilding and publishing the Orchestration persists and enforces the updated schema contract.
- Deprecated or removed schema fields are flagged or removed from downstream mappings.

## Minimum Working Fix

Invalidate the workflow node schema cache and re-fetch the latest Agent output schema during workflow load and rebuild/publish so downstream node field pickers receive updated schema definitions.

## Acceptance Criteria

- Saving changes to an Agent's output schema propagates updated fields to the Orchestration workflow.
- Newly added agent output fields appear immediately in downstream Data Mapper source field pickers.
- Newly added agent output fields are selectable in Condition Builder routing rules.
- Rebuilding and publishing the Orchestration persists and enforces the updated schema contract.
- Deprecated or removed schema fields are flagged or removed from downstream mappings.

## Evidence

- [ART-ORCHESTRATOR-002__agent-output-schema-configured__2026-09-29__01.png](ART-ORCHESTRATOR-002__agent-output-schema-configured__2026-09-29__01.png)
- [ART-ORCHESTRATOR-002__orchestrator-data-mapper-stale-schema__2026-09-29__02.png](ART-ORCHESTRATOR-002__orchestrator-data-mapper-stale-schema__2026-09-29__02.png)

## Discussion

Not provided

## Developer Update

Pending.

## Retest

Pending.

## Azure DevOps

- **Work Item ID:** 68840
- **URL:** https://dev.azure.com/BixBytesSolutions/f3253417-808e-457f-a7f2-5699b2f38aa6/_workitems/edit/68840
- **Parent Feature:** Orchestrator
- **Parent Feature ID:** 68806
- **Assigned To:** Unassigned
- **Sync Status:** SYNCED

## Resolution Status

- **ART Disposition:** OPEN
- **Azure State:** New
- **Azure Reason:** New
- **Retest Required:** NO
- **Action Required:** AWAIT_DEVELOPER
- **Last Azure Sync:** 2026-10-12T06:45:13.368950+00:00


## Resolution History

### 2026-10-12 — Azure Lifecycle Update

Azure Work Item: #68840
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
