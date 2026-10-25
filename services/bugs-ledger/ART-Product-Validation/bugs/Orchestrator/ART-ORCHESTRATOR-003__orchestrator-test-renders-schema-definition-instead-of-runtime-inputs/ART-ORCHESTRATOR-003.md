# ART-ORCHESTRATOR-003 — Orchestrator Test Exposes Schema Definition Structure Instead of Runtime Input Fields

- **Canonical Bug ID:** ART-ORCHESTRATOR-003
- **Title:** Orchestrator Test Exposes Schema Definition Structure Instead of Runtime Input Fields
- **Module:** ORCHESTRATOR
- **Status:** OPEN
- **Severity:** HIGH
- **Priority:** P1
- **Assignee:** Unassigned
- **Environment:** Testing / InvestigationLab
- **Tags:** Orchestrator, Start-Node, JSON-Schema, Test-Input, Workflow-Execution, Form-Generation

## Problem

In the Daily Work Coordinator Orchestrator, the Start node input schema is configured with one required runtime field named `message` of type `string`.
The saved Start schema is:
```json
{
  "additionalProperties": false,
  "properties": {
    "message": {
      "type": "string"
    }
  },
  "required": [
    "message"
  ],
  "type": "object"
}
```

When opening Orchestrator Test, ART does not provide an input field where the user can enter the runtime value for `message`.
Instead, the Test Input UI displays the JSON Schema definition itself as editable/form fields, including:
- `additionalProperties`
- `properties`
- `message`
- `type`
- `required`
- `required[0]`
- root `type`

Because of this, users cannot provide the actual runtime payload expected by the Start node, such as:
```json
{
  "message": "Today I need to finish the Agent Lab storyboard, review the provider sheet, and prepare the blog calendar."
}
```

## Bug

The Orchestrator Test panel exposes the JSON Schema definition structure itself as form fields instead of generating runtime input controls for the configured schema properties. In the Daily Work Coordinator Orchestrator with a Start node configured to require a `message` string, the Test Input panel renders raw schema keywords (`additionalProperties`, `properties`, `message`, `type`, `required`, `required[0]`, root `type`) as inputs, preventing users from supplying the runtime input payload expected by the workflow.

## Observed Behavior

When opening the Orchestrator Test side panel for a workflow configured with a Start node input schema, the Test Input section exposes input controls corresponding to the internal JSON Schema meta-schema keys rather than the target data fields. Specifically, the form displays:
- An `additionalProperties` checkbox
- A `properties` container with a nested `message` -> `type: string` input
- A `required` list control with `required[0]: message`
- A root `type: object` field

Users cannot enter a direct runtime string value for `message`, making it difficult or impossible to pass the expected runtime payload (`start.message`) to the workflow through the Test panel.

## Reproduction

1. Open the Daily Work Coordinator Orchestrator in the workflow canvas.
2. Open Configure Start -> Basic Config and define the Start input schema as:
   ```json
   {
     "additionalProperties": false,
     "properties": {
       "message": {
         "type": "string"
       }
     },
     "required": [
       "message"
     ],
     "type": "object"
   }
   ```
3. Save the Start node configuration.
4. Click Orchestrator Test to open the test execution side panel.
5. Inspect the generated fields under TEST INPUT.

## Expected

Orchestrator Test should interpret the configured Start input schema and generate runtime input controls from it. For this schema, it should show a user-editable `message` field. When Run is clicked, the workflow should receive the entered value as `start.message`.

## Expected Behavior

Orchestrator Test should interpret the configured Start input schema and generate runtime input controls from it. For this schema, it should show a user-editable `message` field. When Run is clicked, the workflow should receive the entered value as `start.message`.

## Actual

Orchestrator Test exposes the schema-definition structure itself instead of a runtime message input. This makes it difficult or impossible to provide the Start node's expected test payload through the Test UI.

## Actual Result

Orchestrator Test exposes the schema-definition structure itself instead of a runtime message input. This makes it difficult or impossible to provide the Start node's expected test payload through the Test UI.

## Business Impact

Workflow developers and QA engineers cannot execute, test, or validate reactive orchestrations through the Orchestrator Test interface when Start nodes have structured input schemas. This blocks rapid iteration, testing of multi-step automations, and end-to-end verification of workflows that depend on initial message payloads.

## User Experience

When a user opens Orchestrator Test expecting to test-run their workflow with sample input text, they are confronted with a confusing form exposing raw JSON Schema keywords (`additionalProperties`, `properties`, `type`, `required[0]`). Attempting to fill in these fields fails to produce the expected runtime object, creating confusion and blocking test execution.

## Investigation Guidance

Inspect the Orchestrator Test panel component and form generation pipeline where the Start node's input schema is loaded to construct the Test Input UI:
- Trace where the Start node's `input_schema` is received and parsed by the Orchestrator Test runner.
- Investigate why the form renderer binds to the schema definition object itself rather than compiling its `properties` dictionary into input field definitions.
- Contrast with form generation in other ART test runners (such as the Agent test runner or result inspector) to align on the standard schema-to-form contract.
- Do not assume an unverified root cause or invent speculative repository paths; trace execution from the Orchestrator Test drawer component toward the schema form resolver.

## Fix Requirement

Orchestrator Test must interpret the Start node's configured input JSON Schema and render form input controls for the defined runtime properties (e.g., an editable `message` string input) instead of displaying the JSON Schema specification keywords as form inputs. The submitted form data must produce a runtime payload matching the configured schema structure.

## Recommended Solution

Implement schema-aware runtime form generation for Orchestrator Test:
1. Pass the Start node's input schema to a dedicated schema form compiler that extracts defined properties (`properties.*`) and their types.
2. Render appropriate input widgets based on property definitions (e.g. text inputs for `string`, number inputs for `number`, toggles for `boolean`, item lists for `array`).
3. Enforce validation rules defined in the schema (required properties, enums, format constraints) on the client side before triggering workflow runs.
4. Construct the runtime execution payload from the user-entered property values under the root object structure (e.g., `{ "message": "<entered_value>" }`) and pass it as the Start node execution payload.
5. Provide a raw JSON input toggle for developers who prefer directly pasting a JSON payload.

## Production-Grade Fix Proposal

Implement schema-aware runtime form generation for Orchestrator Test:

### Required implementation

1. Pass the Start node's input schema to a dedicated schema form compiler that extracts defined properties (`properties.*`) and their types.
2. Render appropriate input widgets based on property definitions (e.g. text inputs for `string`, number inputs for `number`, toggles for `boolean`, item lists for `array`).
3. Enforce validation rules defined in the schema (required properties, enums, format constraints) on the client side before triggering workflow runs.
4. Construct the runtime execution payload from the user-entered property values under the root object structure (e.g., `{ "message": "<entered_value>" }`) and pass it as the Start node execution payload.
5. Provide a raw JSON input toggle for developers who prefer directly pasting a JSON payload.

### Acceptance criteria

- Orchestrator Test renders an editable input control for `message` when the Start node schema defines `properties.message`.
- JSON Schema meta-keywords (`additionalProperties`, `properties`, `required`, root `type`) are not displayed as editable form fields in the Test Input UI.
- Required fields defined in the schema's `required` array are marked as mandatory in the Test UI.
- Submitting the test form sends the user-entered value as the runtime payload (`{ "message": "<value>" }`) to the Start node.
- Workflow execution successfully receives and processes `start.message`.

## Minimum Working Fix

Update the Orchestrator Test panel to parse the `properties` map of the Start node's input schema and render runtime input controls for each declared property (e.g., `message`) instead of binding form controls directly to the top-level schema definition object.

## Acceptance Criteria

- Orchestrator Test renders an editable input control for `message` when the Start node schema defines `properties.message`.
- JSON Schema meta-keywords (`additionalProperties`, `properties`, `required`, root `type`) are not displayed as editable form fields in the Test Input UI.
- Required fields defined in the schema's `required` array are marked as mandatory in the Test UI.
- Submitting the test form sends the user-entered value as the runtime payload (`{ "message": "<value>" }`) to the Start node.
- Workflow execution successfully receives and processes `start.message`.

## Environment

Testing / InvestigationLab

## Severity

HIGH

## Priority

P1

## Tags

- Orchestrator
- Start-Node
- JSON-Schema
- Test-Input
- Workflow-Execution
- Form-Generation

## Assignee

Unassigned

## Evidence

- [ART-ORCHESTRATOR-003__start-node-input-schema-configured__2026-09-29__01.png](ART-ORCHESTRATOR-003__start-node-input-schema-configured__2026-09-29__01.png)
- [ART-ORCHESTRATOR-003__orchestrator-test-schema-definition-fields-top__2026-09-29__02.png](ART-ORCHESTRATOR-003__orchestrator-test-schema-definition-fields-top__2026-09-29__02.png)
- [ART-ORCHESTRATOR-003__orchestrator-test-schema-definition-fields-bottom__2026-09-29__03.png](ART-ORCHESTRATOR-003__orchestrator-test-schema-definition-fields-bottom__2026-09-29__03.png)
- [ART-ORCHESTRATOR-003__agent-result-comparison-schema-representation__2026-09-29__04.png](ART-ORCHESTRATOR-003__agent-result-comparison-schema-representation__2026-09-29__04.png)

## Discussion

Not provided

## Developer Update

Pending.

## Retest

Pending.

## Azure DevOps

- **Work Item ID:** 68849
- **URL:** https://dev.azure.com/BixBytesSolutions/f3253417-808e-457f-a7f2-5699b2f38aa6/_workitems/edit/68849
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
- **Last Azure Sync:** 2026-10-12T06:45:14.181004+00:00


## Resolution History

### 2026-10-12 — Azure Lifecycle Update

Azure Work Item: #68849
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
