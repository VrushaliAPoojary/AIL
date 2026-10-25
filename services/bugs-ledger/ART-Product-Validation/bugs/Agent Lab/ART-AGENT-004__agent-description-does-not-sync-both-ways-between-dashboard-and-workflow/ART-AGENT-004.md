# ART-AGENT-004 — Agent Description Does Not Sync Both Ways Between Agent Dashboard and Workflow

- **Canonical Bug ID:** ART-AGENT-004
- **Title:** Agent Description Does Not Sync Both Ways Between Agent Dashboard and Workflow
- **Module:** AGENT
- **Status:** OPEN
- **Severity:** MEDIUM
- **Priority:** P2
- **Assignee:** Unassigned
- **Environment:** Testing (Enterprise Plan)
- **Tags:** Agent-Lab, Agent-Dashboard, Agent-Workflow, Description-Sync, Data-Consistency

## Problem

The Agent description is not synchronized correctly between the Agent Dashboard and the Agent Workflow.

When an agent description is added or updated from the Agent Dashboard/Homepage (Agent Studio), the updated description is visible on the dashboard card (e.g. for "Daily Work Coordinator V2" showing "Daily Work Coordinator V2 is a personal ..."), but inside the Agent Workflow canvas the central agent node still displays "No Description added."

However, when the description is updated from inside the Agent Workflow, the change is reflected correctly on the Agent Dashboard.

This creates inconsistent bidirectional synchronization behavior where the same Agent has two places to view and manage its description, but only Workflow-to-Dashboard synchronization functions properly.

## Bug

The Agent description fails to synchronize from the Agent Dashboard to the Agent Workflow canvas. While description updates performed within the Workflow editor propagate back to the Dashboard card, descriptions added or modified on the Agent Dashboard/Homepage do not propagate into the Workflow view, causing the Agent node on the canvas to display "No Description added."

## Observed Behavior

- **Direction 1 (Dashboard → Workflow) [FAILED]:**
  When an Agent description is added or modified from the Agent Studio Dashboard (e.g., setting the description for "Daily Work Coordinator V2" to "Daily Work Coordinator V2 is a personal ..."), the dashboard card reflects the description. However, opening the Agent Workflow reveals that the central Agent node on the canvas displays "No Description added."
- **Direction 2 (Workflow → Dashboard) [PASSED]:**
  When the description is updated directly within the Agent Workflow editor, saving and returning to the Agent Dashboard correctly displays the updated description on the Agent card.

## Reproduction

1. Navigate to the Agent Studio homepage / Agent Dashboard (`Your agents` section).
2. Locate or create an agent (e.g., "Daily Work Coordinator V2").
3. Add or update the description from the Dashboard view (e.g. "Daily Work Coordinator V2 is a personal ...").
4. Verify that the updated description appears on the Agent card under `Your agents` on the Dashboard.
5. Open the Agent Workflow editor by clicking on the agent card.
6. Inspect the central Agent node on the workflow canvas.
7. Observe that the node subtitle reads "No Description added" instead of the description configured on the dashboard.
8. In the Workflow editor, edit the agent description and return to the Dashboard; observe that the description does update on the dashboard card.

## Expected

The Agent should maintain a single authoritative description across all views. Updating the description from either the Agent Dashboard or the Agent Workflow should automatically and immediately reflect the identical description in both interfaces.

## Expected Behavior

The Agent should have a single description value. Updating the description from either the Agent Dashboard or Agent Workflow should automatically update the same description everywhere. Opening the Agent Workflow after setting a description on the Dashboard must display that description on the Agent node instead of "No Description added."

## Actual

- Dashboard → Workflow: Description does not update. The Agent Workflow canvas displays "No Description added."
- Workflow → Dashboard: Description does update correctly.

## Actual Result

- Dashboard → Workflow: Description does not update. The Agent Workflow canvas displays "No Description added."
- Workflow → Dashboard: Description does update correctly.

## Business Impact

Users must enter the same Agent description multiple times and are exposed to conflicting agent metadata across different screens. This creates confusion, increases friction during agent authoring and maintenance, and risks deploying agents with missing or mismatched documentation.

## User Experience

When a user provides a clear description on the Agent Dashboard to document an agent's purpose, entering the workflow canvas displays "No Description added." Users assume their previous input was lost or unsaved, prompting unnecessary rework or mistrust in the platform's state persistence.

## Investigation Guidance

Inspect how the Agent entity description is retrieved and persisted across the Agent Dashboard and the Agent Workflow editor:
- Examine the API endpoints and payload schemas used by the Agent Dashboard update action versus the Agent Workflow settings drawer:
  - Check whether the Dashboard writes to an entity-level field (e.g., `agent.description`), while the Workflow canvas reads from a graph-level definition field (e.g., `workflow.nodes[agent].description` or `workflow.metadata.description`).
- Trace the workflow editor initialization and fetch routines:
  - Verify where the canvas node component resolves the description string displayed under the agent name header.
  - Check why it falls back to the default string "No Description added" when a valid description exists on the parent Agent record.
- Check client-side caching and state synchronization:
  - Verify whether navigation from the dashboard to the workflow canvas utilizes a stale cache that lacks the recently saved dashboard description.
- Do not invent speculative file paths or unverified root causes; trace data flow between the dashboard agent store, the backend persistence layer, and the canvas node renderer.

## Fix Requirement

Establish a single source of truth for the Agent description across both views. Updates made in either the Agent Dashboard or the Agent Workflow must persist to the same canonical property, and opening the Workflow editor must populate the Agent node with the current description rather than falling back to "No Description added."

## Recommended Solution

1. Use the same persisted Agent description field/source for both the Agent Dashboard and Agent Workflow views.
2. Ensure the Agent Workflow initialization query fetches and populates the description from the canonical Agent entity record.
3. If the workflow canvas maintains a separate node description property, ensure it is bidirectionally synchronized with the root agent entity description during load and save operations.
4. Invalidate or refresh cached agent metadata in the client store whenever navigation occurs between the dashboard and workflow canvas.

## Production-Grade Fix Proposal

1. Unify the data contract for agent descriptions so that both the Agent Studio Dashboard and the Workflow Editor interact with the identical field on the Agent record.
2. In the Workflow canvas loader, map the root `agent.description` to the central Agent node's display model upon initialization.
3. In the Dashboard agent updater, ensure any mutation updates the shared backend record and dispatches a cache invalidation event for the workflow store.
4. Provide fallback handling so that if a node-level description is missing, the canvas automatically displays the parent entity description before resorting to "No Description added."

## Minimum Working Fix

Update the Agent Workflow editor's canvas loader to read and display the Agent record's top-level description property upon opening, rather than falling back to "No Description added" when workflow-specific node description metadata is empty.

## Acceptance Criteria

- Updating an Agent description from the Agent Dashboard immediately reflects in the Agent Workflow editor upon opening.
- Updating an Agent description from the Agent Workflow immediately reflects on the Agent Dashboard card.
- When an Agent has a description configured on the Dashboard (e.g. "Daily Work Coordinator V2 is a personal ..."), opening the Agent Workflow displays that text on the central node instead of "No Description added."
- Both interfaces display the identical description value after edits in either location.

## Environment

Testing (Enterprise Plan)

## Severity

MEDIUM

## Priority

P2

## Tags

- Agent-Lab
- Agent-Dashboard
- Agent-Workflow
- Description-Sync
- Data-Consistency

## Assignee

Unassigned

## Evidence

- [ART-AGENT-004__agent-dashboard-description-present__2026-09-30__01.png](ART-AGENT-004__agent-dashboard-description-present__2026-09-30__01.png)
- [ART-AGENT-004__agent-workflow-no-description-added__2026-09-30__02.png](ART-AGENT-004__agent-workflow-no-description-added__2026-09-30__02.png)

## Discussion

Not provided

## Developer Update

Pending.

## Retest

Pending.

## Azure DevOps

- **Work Item ID:** 68863
- **URL:** https://dev.azure.com/BixBytesSolutions/f3253417-808e-457f-a7f2-5699b2f38aa6/_workitems/edit/68863
- **Parent Feature:** Agent Lab
- **Parent Feature ID:** 68783
- **Assigned To:** Unassigned
- **Sync Status:** SYNCED

## Resolution Status

- **ART Disposition:** OPEN
- **Azure State:** New
- **Azure Reason:** New
- **Retest Required:** NO
- **Action Required:** AWAIT_DEVELOPER
- **Last Azure Sync:** 2026-10-12T06:44:57.796581+00:00


## Resolution History

### 2026-10-12 — Azure Lifecycle Update

Azure Work Item: #68863
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
