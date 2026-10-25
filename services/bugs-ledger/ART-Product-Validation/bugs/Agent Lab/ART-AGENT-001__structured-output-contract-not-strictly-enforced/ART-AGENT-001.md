# ART-AGENT-001 — Structured output contract is not strictly enforced

- **Severity:** HIGH
- **Status:** OPEN

## Bug

The Agent Output Parser does not consistently enforce configured field names, nested structures, data types, or required collection defaults.

## Expected

ART must validate every agent result against the configured output contract before displaying or sending it to governance.

Invalid output must be rejected or automatically repaired. The UI must clearly identify the affected field, expected type, and received type.

Empty collection fields such as `mismatches` must return `[]`, never `null`.

## Actual

The same workflow has produced:

- `compared_fields` as arrays instead of objects
- `field_name` instead of the configured `field`
- numeric values as strings
- `mismatches: null` instead of `mismatches: []`

These results are displayed as successful Agent Results without contract-validation errors.

## Evidence

- [ART-AGENT-001__agent-result-contract-violation__2026-09-24__01.png](ART-AGENT-001__agent-result-contract-violation__2026-09-24__01.png)
- [ART-AGENT-001__schema-builder-contract__2026-09-24__02.png](ART-AGENT-001__schema-builder-contract__2026-09-24__02.png)

## Production-Grade Fix Proposal

ART must enforce structured output as a platform contract instead of depending only on prompt instructions.

### Required implementation

1. Generate and store one canonical JSON Schema from the Output Parser configuration.
2. The schema must define:
   - Required properties
   - Exact property names
   - Data types
   - Enum values
   - Nested object structures
   - Array item structures
   - Nullable rules
   - Default values
   - `additionalProperties: false`
3. Use provider-native strict structured output whenever the selected model supports it.
4. Use schema-bound tool calling when native structured output is unavailable.
5. Validate the final model response server-side before displaying it or sending it to governance.
6. Automatically apply only safe normalization:
   - Missing optional arrays to `[]`
   - Missing optional objects to `{}`
   - Whitespace trimming
   - Known enum casing normalization
7. Do not automatically modify business decisions, evidence, mismatch findings, ownership, or approval requirements.
8. If validation fails, return the exact validation errors to the model and perform one repair attempt.
9. The repair attempt must not repeat tool calls, actions, notifications, or governance execution.
10. If validation still fails, stop execution with `OUTPUT_VALIDATION_FAILED`.
11. Invalid output must never be displayed as a successful Agent Result or passed to governance.
12. Provide a visual schema builder for non-technical users with:
    - Display label
    - Property key
    - Type
    - Required or optional
    - Allow null
    - Default value
    - Allowed values
    - Array item structure
13. Before publishing, automatically test exact match, single mismatch, multiple mismatches, missing evidence, null values, invalid types, and unexpected properties.

### Acceptance criteria

- Property names remain unchanged between executions.
- `compared_fields` is always an array of objects.
- `mismatches` is always an array and never `null`.
- Numeric values remain numeric.
- Invalid enum values are rejected.
- Additional properties are rejected.
- Invalid results never reach governance.
- Repair attempts do not repeat business actions.
- Validation errors are readable by non-technical users.
- Build and Publish is blocked when contract tests fail.

## Developer Update

Pending.

## Retest

Pending.

## Azure DevOps

- **Work Item ID:** 68831
- **URL:** https://dev.azure.com/BixBytesSolutions/f3253417-808e-457f-a7f2-5699b2f38aa6/_apis/wit/workItems/68831
- **Parent Feature:** Agent Lab
- **Parent Feature ID:** 68783
- **Assigned To:** Unassigned
- **Sync Status:** SYNCED

## Resolution Status

- **ART Disposition:** OPEN
- **Current Azure Assignee:** Anusha Ganesh Hegde
- **Azure State:** New
- **Azure Reason:** New
- **Retest Required:** NO
- **Action Required:** AWAIT_DEVELOPER
- **Latest Lifecycle Update:** 2026-09-29T13:01:19.327Z
- **Last Azure Sync:** 2026-10-13T03:33:46.185845+00:00


## Resolution History

### 2026-10-12 — Azure Lifecycle Update

Azure Work Item: #68831
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

### 2026-10-13 — Azure Lifecycle Update

Azure Work Item: #68831
Azure State: New
Azure Reason: New
Current Azure Assignee: Anusha Ganesh Hegde
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
