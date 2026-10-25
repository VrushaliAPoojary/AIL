# ART-AGENT-002 — Agent Run Fails with Generic Error and No Diagnostics During Media Processing

- **Canonical Bug ID:** ART-AGENT-002
- **Title:** Agent Run Fails with Generic Error and No Diagnostics During Media Processing
- **Module:** AGENT
- **Status:** OPEN
- **Severity:** HIGH
- **Priority:** P1
- **Assignee:** Unassigned
- **Environment:** Testing / InvestigationLab
- **Tags:** Agent-Lab, Media-Processing, Observability, Error-Handling, OpenAI

## Problem

When testing the Ticket Resolution Agent with uploaded media (image or video) using the configured OpenAI GPT-5.1 Mini model, the run fails with a generic `AGENT_RUN_ERROR` ("The agent could not complete this request."). In Observability, storage tools (`storage list files`, `storage get file url`) execute successfully, but execution terminates at the Agent step with "No diagnostic message was recorded." Neither the Agent Test UI nor Observability provides actionable diagnostics, making it impossible to determine whether the failure stems from media retrieval, multimodal model invocation, output schema parsing, or another lifecycle phase.

## Bug

The Ticket Resolution Agent fails during media execution with `AGENT_RUN_ERROR` and displays only "The agent could not complete this request." Observability logs show media storage operations executing successfully before the run fails at the Agent level with "No diagnostic message was recorded." The system fails to process the media input into structured output and fails to provide diagnostic details regarding the point or reason of failure.

## Expected

The Agent should process the uploaded media (image or video), extract relevant information, create a summary, and return structured output based on the configured output schema. If processing fails at any stage, ART must capture and display a clear, descriptive diagnostic error message explaining the exact reason and failing step.

## Expected Result

The Agent should process the uploaded media (image or video), extract relevant information, create a summary, and return structured output based on the configured output schema. If processing fails at any stage, ART must capture and display a clear, descriptive diagnostic error message explaining the exact reason and failing step.

## Actual

The Agent run terminates with an error modal showing `type: agent_error_response`, `status: error`, `code: AGENT_RUN_ERROR`, and `message: The agent could not complete this request.` In Observability Conversation Explorer, the trace marks `Run failed` and `Agent error` with the description: "This activity could not be completed. No diagnostic message was recorded."

## Actual Result

The Agent run terminates with an error modal showing `type: agent_error_response`, `status: error`, `code: AGENT_RUN_ERROR`, and `message: The agent could not complete this request.` In Observability Conversation Explorer, the trace marks `Run failed` and `Agent error` with the description: "This activity could not be completed. No diagnostic message was recorded."

## Business Impact

Automated support ticket resolution workflows relying on image or video evidence cannot execute, blocking core multi-modal agent capabilities. Furthermore, developers and support engineers cannot diagnose root causes or troubleshoot runtime failures due to suppressed diagnostic messages, increasing mean time to repair and delaying production deployments.

## User Experience

When a user submits an image or video in the Agent Test interface, the agent fails with an unhelpful error badge and generic modal dialog ("The agent could not complete this request."). Navigating to Observability to inspect the failure provides no additional clarity, showing only "No diagnostic message was recorded," leaving the user blocked with no actionable path to resolution.

## Recommended Solution

Implement robust exception handling, diagnostic logging, and error propagation across the agent multimodal execution pipeline:

1. Ensure media payloads fetched by storage tools are properly validated and formatted for the selected model's multimodal API contract.
2. Capture upstream model errors, HTTP status codes, payload limit errors, and schema parsing exceptions at each lifecycle step.
3. Record granular diagnostic logs and error details in Observability trace spans rather than suppressing error strings.
4. Replace the generic `AGENT_RUN_ERROR` fallback with specific error codes (e.g., `MEDIA_PAYLOAD_UNSUPPORTED`, `MODEL_INVOCATION_TIMEOUT`, `SCHEMA_VALIDATION_FAILED`) and descriptive messages in the Agent Test interface.
5. Provide actionable remediation hints in both the UI error modal and the Observability Activity pane.

## Production-Grade Fix Proposal

Implement robust exception handling, diagnostic logging, and error propagation across the agent multimodal execution pipeline:

### Required implementation

1. Catch specific exceptions across media download/presign, multimodal payload serialization, LLM invocation, and output parsing.
2. Populate the Observability trace span `error` and `diagnostic_message` attributes with full exception details and stack traces.
3. Map internal failure states to standardized, human-readable error messages for the client interface.
4. Verify that the configured model (OpenAI GPT-5.1 Mini) supports the ingested media type and payload encoding.
5. In the UI error modal, display the failed execution phase and detailed reason alongside raw JSON details.

### Acceptance criteria

- Uploaded image or video media is successfully processed by the agent to generate structured output conforming to the configured schema.
- If media processing fails, the Agent Test modal displays a descriptive error message indicating the exact failure reason.
- Observability trace tree captures and displays meaningful diagnostic messages for failed agent activities instead of "No diagnostic message was recorded."
- Tool execution, LLM invocation, and output validation phases record distinct, traceable status spans.

## Minimum Working Fix

Catch unhandled exceptions in the agent runner during media processing and schema parsing, record the exception message into the Observability trace span's diagnostic field, and return the descriptive error string to the user interface instead of suppressing it with a generic fallback.

## Acceptance Criteria

- Uploaded image or video media is successfully processed by the agent to generate structured output conforming to the configured schema.
- If media processing fails, the Agent Test modal displays a descriptive error message indicating the exact failure reason.
- Observability trace tree captures and displays meaningful diagnostic messages for failed agent activities instead of "No diagnostic message was recorded."
- Tool execution, LLM invocation, and output validation phases record distinct, traceable status spans.

## Evidence

- [ART-AGENT-002__agent-test-run-error__2026-09-29__01.png](ART-AGENT-002__agent-test-run-error__2026-09-29__01.png)
- [ART-AGENT-002__observability-no-diagnostic-message__2026-09-29__02.png](ART-AGENT-002__observability-no-diagnostic-message__2026-09-29__02.png)

## Discussion

Not provided

## Developer Update

Pending.

## Retest

Pending.

## Azure DevOps

- **Work Item ID:** 68842
- **URL:** https://dev.azure.com/BixBytesSolutions/f3253417-808e-457f-a7f2-5699b2f38aa6/_workitems/edit/68842
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
- **Last Azure Sync:** 2026-10-12T06:44:56.366372+00:00


## Resolution History

### 2026-10-12 — Azure Lifecycle Update

Azure Work Item: #68842
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
