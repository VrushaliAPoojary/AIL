# ART-AGENT-003 — Agent Workflow Displays Default Robot Icon Instead of Configured Custom Icon

- **Canonical Bug ID:** ART-AGENT-003
- **Title:** Agent Workflow Displays Default Robot Icon Instead of Configured Custom Icon
- **Module:** AGENT
- **Status:** OPEN
- **Severity:** LOW
- **Priority:** P3
- **Assignee:** Unassigned
- **Environment:** Testing (Enterprise Plan)
- **Tags:** Agent-Lab, Agent-Builder, Agent-Node, Custom-Icon, UI-Branding, Workflow-Canvas

## Problem

A custom logo/icon was provided for the Agent, but the Agent workflow still displays the default ART robot icon instead of the configured custom logo.
In the attached evidence, the custom agent icon is provided separately, while the Agent Builder workflow for "attacking agent" continues to show the default robot icon on the Agent node.

## Bug

The Agent Builder workflow canvas fails to display a configured custom logo/icon on the Agent node, continuing to show the default ART robot icon instead.

## Observed Behavior

In the Agent Lab workflow for "attacking agent", the central Agent node renders the default ART robot icon. A custom agent icon was configured and provided separately, but the custom graphic is not displayed on the Agent node in the workflow canvas.

## Reproduction

Not provided.

## Expected Behavior

After a custom Agent logo/icon is configured, the Agent Builder should display that configured icon consistently on the Agent node instead of the default robot icon.

## Business Impact

Custom agent branding and visual differentiation are not reflected in the workflow canvas. Organizations and users cannot visually identify specialized agents (such as the "attacking agent" / AEGIS Attack Planner) by their custom logos, reducing clarity in multi-agent environments and degrading the white-label/branding experience.

## User Experience

Users who upload or assign a custom icon to an agent observe no visual change on the workflow canvas. The agent node continues to display the generic ART robot graphic, creating uncertainty as to whether the custom logo configuration was successfully saved or applied.

## Investigation Guidance

Inspect the Agent Lab frontend workflow canvas where Agent node components are rendered.
Trace the following:
1. Examine the Agent node view model and determine how the icon/avatar property is resolved from the agent configuration entity.
2. Investigate whether the Agent node component checks for a custom icon asset reference or URL before rendering the fallback default robot icon.
3. Verify if the agent configuration save and workflow load pipelines serialize, persist, and deserialize the custom icon URL or asset identifier.
4. Check if the image element or SVG wrapper in the node component handles custom image URLs and supports expected image dimensions and formats.

## Fix Requirement

The Agent node component on the Agent Builder workflow canvas must check for a configured custom icon or logo on the agent definition. If a custom icon is present, it must render that custom image in the agent node avatar area instead of displaying the default robot icon.

## Recommended Solution

1. In the Agent node canvas component, bind the node avatar image source to the agent's custom icon URL/property if defined.
2. Maintain the default ART robot icon as a fallback when no custom icon is configured or if the custom image fails to load.
3. Ensure the workflow loader and canvas state management preserve the custom icon metadata when loading the agent workflow.
4. Ensure appropriate CSS sizing (e.g. `object-fit: contain`) so custom icons scale neatly within the node avatar container.

## Minimum Working Fix

Update the Agent node canvas component to display the configured custom icon URL when present on the agent model, falling back to the default robot icon only when the custom icon property is empty or undefined.

## Acceptance Criteria

- When a custom icon/logo is configured for an Agent, the Agent node in the Agent Builder workflow canvas displays that custom icon.
- When no custom icon is configured, the Agent node continues to display the default ART robot icon.
- If a custom icon fails to load, the Agent node gracefully falls back to the default robot icon.
- The custom icon renders with correct aspect ratio and scaling within the Agent node header.

## Environment

Testing (Enterprise Plan)

## Severity

LOW

## Priority

P3

## Tags

- Agent-Lab
- Agent-Builder
- Agent-Node
- Custom-Icon
- UI-Branding
- Workflow-Canvas

## Assignee

Unassigned

## Evidence

- [ART-AGENT-003__custom-agent-icon-asset__2026-09-29__01.png](ART-AGENT-003__custom-agent-icon-asset__2026-09-29__01.png)
- [ART-AGENT-003__agent-workflow-canvas-default-robot-icon__2026-09-29__02.png](ART-AGENT-003__agent-workflow-canvas-default-robot-icon__2026-09-29__02.png)

## Discussion

Not provided

## Developer Update

Pending.

## Retest

Pending.

## Azure DevOps

- **Work Item ID:** 68852
- **URL:** https://dev.azure.com/BixBytesSolutions/f3253417-808e-457f-a7f2-5699b2f38aa6/_workitems/edit/68852
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
- **Last Azure Sync:** 2026-10-12T06:44:57.037127+00:00


## Resolution History

### 2026-10-12 — Azure Lifecycle Update

Azure Work Item: #68852
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
