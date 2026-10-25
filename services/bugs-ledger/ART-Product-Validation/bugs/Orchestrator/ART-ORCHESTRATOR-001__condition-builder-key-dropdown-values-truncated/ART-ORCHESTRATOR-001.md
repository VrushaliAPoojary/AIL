# ART-ORCHESTRATOR-001 — Condition Builder Key Dropdown Values Are Truncated and Unreadable

- **Canonical Bug ID:** ART-ORCHESTRATOR-001
- **Title:** Condition Builder Key Dropdown Values Are Truncated and Unreadable
- **Module:** ORCHESTRATOR
- **Status:** OPEN
- **Severity:** MEDIUM
- **Priority:** P2
- **Assignee:** Unassigned
- **Environment:** Not provided
- **Tags:** Orchestrator, Workflow-Routing, UX-Clarity, UI-Defect

## Problem

The values displayed in the Condition Builder Key field dropdown are severely truncated due to restricted dropdown width and overflow clipping, showing only `agentOrchestrator_1.c...` for all options. This prevents users from identifying, distinguishing, and selecting the correct runtime variables and path attributes.

## Bug

The values displayed in the Condition Builder Key field dropdown are severely truncated due to restricted dropdown width and overflow clipping, showing only `agentOrchestrator_1.c...` for all options. This prevents users from identifying, distinguishing, and selecting the correct runtime variables and path attributes.

## Expected

Dropdown options in the Condition Builder Key field should display full variable and path names clearly, adjusting dropdown container width to fit content (or providing text wrapping / tooltips on hover) so users can distinguish and select the appropriate key.

## Expected Result

Dropdown options in the Condition Builder Key field should display full variable and path names clearly, adjusting dropdown container width to fit content (or providing text wrapping / tooltips on hover) so users can distinguish and select the appropriate key.

## Actual

Values in the Condition Builder Key dropdown are truncated to `agentOrchestrator_1.c...` due to narrow dropdown width. Multiple distinct attributes appear visually identical, making it difficult or impossible to identify and select the intended value.

## Actual Result

Values in the Condition Builder Key dropdown are truncated to `agentOrchestrator_1.c...` due to narrow dropdown width. Multiple distinct attributes appear visually identical, making it difficult or impossible to identify and select the intended value.

## Business Impact

Users cannot reliably configure routing conditions in workflow orchestrations when multiple variables share a common prefix, leading to configuration errors, misrouted workflow execution paths, and decreased developer productivity.

## User Experience

When configuring routing conditions in the Condition Builder, users open the Key dropdown and see a column of identical truncated strings (`agentOrchestrator_1.c...`), forcing guesswork or trial-and-error to select the right field.

## Recommended Solution

Update the Condition Builder Key dropdown UI styling and component behavior to ensure full readability:

1. Set dropdown menu width to fit content (`min-width: max-content` or expanded fixed width) with a sensible maximum width and horizontal scrolling or auto-expansion.
2. Implement text truncation with ellipsis only when exceeding maximum container bounds, and provide native `title` or tooltip attributes showing the full variable path on hover.
3. Ensure selected token pills and dropdown items preserve clear font sizing, padding, and high-contrast styling.
4. Optionally support variable path shortening with smart middle-truncation or hierarchy grouping (e.g. grouping by node `agentOrchestrator_1` -> sub-properties).

## Production-Grade Fix Proposal

Update the Condition Builder Key dropdown UI styling and component behavior to ensure full readability:

### Required implementation

1. Set dropdown menu width to fit content (`min-width: max-content` or expanded fixed width) with a sensible maximum width and horizontal scrolling or auto-expansion.
2. Implement text truncation with ellipsis only when exceeding maximum container bounds, and provide native `title` or tooltip attributes showing the full variable path on hover.
3. Ensure selected token pills and dropdown items preserve clear font sizing, padding, and high-contrast styling.
4. Optionally support variable path shortening with smart middle-truncation or hierarchy grouping (e.g. grouping by node `agentOrchestrator_1` -> sub-properties).

### Acceptance criteria

- Dropdown options display the complete variable path without premature truncation.
- Dropdown container dynamically adjusts or provides sufficient width for long variable names.
- Full variable names are accessible via tooltip on hover if text exceeds container bounds.
- Users can clearly identify and select distinct variables originating from the same workflow node.

## Minimum Working Fix

Expand the Condition Builder Key dropdown menu width (e.g., `min-width: 320px` or `width: max-content`) and add tooltip/title attributes so variable paths are fully visible and readable.

## Acceptance Criteria

- Dropdown options display the complete variable path without premature truncation.
- Dropdown container dynamically adjusts or provides sufficient width for long variable names.
- Full variable names are accessible via tooltip on hover if text exceeds container bounds.
- Users can clearly identify and select distinct variables originating from the same workflow node.

## Evidence

- [ART-ORCHESTRATOR-001__condition-builder-key-dropdown-truncated__2026-09-29__01.png](ART-ORCHESTRATOR-001__condition-builder-key-dropdown-truncated__2026-09-29__01.png)

## Discussion

Not provided

## Developer Update

Pending.

## Retest

Pending.

## Azure DevOps

- **Work Item ID:** 68839
- **URL:** https://dev.azure.com/BixBytesSolutions/f3253417-808e-457f-a7f2-5699b2f38aa6/_workitems/edit/68839
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
- **Last Azure Sync:** 2026-10-12T06:45:12.653603+00:00


## Resolution History

### 2026-10-12 — Azure Lifecycle Update

Azure Work Item: #68839
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
