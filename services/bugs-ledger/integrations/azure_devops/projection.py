"""
integrations/azure_devops/projection.py

Dedicated Developer Ticket Projection and Azure Description Formatter.
Projects canonical ART investigations into concise, developer-ready structured values.
Strictly maps each canonical value 1:1 to its verified Azure DevOps field.
Microsoft.VSTS.TCM.ReproSteps contains the complete developer-facing structured ticket
formatted into clean, Azure-compatible HTML across 11 canonical sections:
1. Problem
2. Observed Behavior
3. Reproduction
4. Expected Behavior
5. Business Impact
6. User Experience
7. Investigation Guidance
8. Fix Requirement
9. Recommended Solution
10. Minimum Working Fix
11. Acceptance Criteria
"""

import re
import html
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass(frozen=True)
class DeveloperTicketProjection:
    """
    Concise developer action brief projected from canonical investigation / ticket.
    Kept separate from the lifecycle domain and repository persistence.
    """
    canonical_bug_id: str
    title: str
    problem: str
    what_is_failing: List[str] = field(default_factory=list)
    critical_behavior: Optional[str] = None
    repro_steps: Optional[str] = None
    reproduction: Optional[str] = None
    expected_result: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_result: Optional[str] = None
    observed_behavior: Optional[str] = None
    business_impact: Optional[str] = None
    user_experience: Optional[str] = None
    investigation_guidance: Optional[str] = None
    fix_requirement: Optional[str] = None
    recommended_solution: Optional[str] = None
    implementation_bullets: List[str] = field(default_factory=list)
    minimum_working_fix: Optional[str] = None
    acceptance_criteria: List[str] = field(default_factory=list)
    severity: Optional[str] = None
    priority: Optional[int] = None
    priority_rationale: Optional[str] = None
    tags: List[str] = field(default_factory=list)


CANONICAL_BUG_DATA: Dict[str, Dict[str, Any]] = {
    "ART-AGENT-001": {
        "problem": (
            "The Agent Output Parser does not consistently enforce configured field names, "
            "nested structures, data types, or required collection defaults before accepting an Agent Result."
        ),
        "observed_behavior": (
            "The same workflow has produced:\n\n"
            "- `compared_fields` as arrays instead of objects\n"
            "- `field_name` instead of the configured `field`\n"
            "- numeric values as strings\n"
            "- `mismatches: null` instead of `mismatches: []`\n\n"
            "These results are displayed as successful Agent Results without contract-validation errors."
        ),
        "actual_result": (
            "The same workflow has produced:\n\n"
            "- `compared_fields` as arrays instead of objects\n"
            "- `field_name` instead of the configured `field`\n"
            "- numeric values as strings\n"
            "- `mismatches: null` instead of `mismatches: []`\n\n"
            "These results are displayed as successful Agent Results without contract-validation errors."
        ),
        "reproduction": "Not provided",
        "repro_steps": "Not provided",
        "expected_behavior": (
            "ART must validate every agent result against the configured output contract before "
            "displaying or sending it to governance.\n\n"
            "Invalid output must be rejected or automatically repaired. The UI must clearly identify "
            "the affected field, expected type, and received type.\n\n"
            "Empty collection fields such as `mismatches` must return `[]`, never `null`."
        ),
        "expected_result": (
            "ART must validate every agent result against the configured output contract before "
            "displaying or sending it to governance.\n\n"
            "Invalid output must be rejected or automatically repaired. The UI must clearly identify "
            "the affected field, expected type, and received type.\n\n"
            "Empty collection fields such as `mismatches` must return `[]`, never `null`."
        ),
        "business_impact": (
            "Structured Agent output can no longer be treated as a reliable contract, "
            "which can cause downstream workflows or governance steps to process unexpected data."
        ),
        "user_experience": (
            "The user configures an explicit output contract expecting ART to preserve the configured "
            "fields and types. ART currently presents contract-violating output as successful, making "
            "it difficult for the user to know whether downstream automation can safely use the result."
        ),
        "investigation_guidance": (
            "Inspect the Agent Output Parser and validation pipeline where the model response is received "
            "and evaluated against the configured schema contract. Verify schema validation logic, type coercion, "
            "and why contract-violating output is accepted and passed to governance."
        ),
        "fix_requirement": (
            "Enforce server-side schema validation against the configured agent output contract prior to "
            "accepting an Agent Result. Reject or fail execution with OUTPUT_VALIDATION_FAILED if the output "
            "violates property names, types, or structure."
        ),
        "recommended_solution": (
            "ART must enforce structured output as a platform contract instead of depending only on prompt instructions.\n\n"
            "1. Generate and store one canonical JSON Schema from the Output Parser configuration.\n"
            "2. The schema must define: required properties, exact property names, data types, enum values, nested object structures, array item structures, nullable rules, default values, and additionalProperties: false.\n"
            "3. Use provider-native strict structured output whenever the selected model supports it.\n"
            "4. Use schema-bound tool calling when native structured output is unavailable.\n"
            "5. Validate the final model response server-side before displaying it or sending it to governance.\n"
            "6. Automatically apply only safe normalization (missing optional arrays to [], missing optional objects to {}, whitespace trimming, known enum casing).\n"
            "7. Do not automatically modify business decisions, evidence, mismatch findings, ownership, or approval requirements.\n"
            "8. If validation fails, return the exact validation errors to the model and perform one repair attempt.\n"
            "9. The repair attempt must not repeat tool calls, actions, notifications, or governance execution.\n"
            "10. If validation still fails, stop execution with OUTPUT_VALIDATION_FAILED.\n"
            "11. Invalid output must never be displayed as a successful Agent Result or passed to governance.\n"
            "12. Provide a visual schema builder for non-technical users.\n"
            "13. Before publishing, automatically test exact match, single mismatch, multiple mismatches, missing evidence, null values, invalid types, and unexpected properties."
        ),
        "minimum_working_fix": (
            "Validate the final Agent response against the configured schema immediately before ART accepts the result. "
            "On validation failure: Return OUTPUT_VALIDATION_FAILED and stop execution before governance."
        ),
        "acceptance_criteria": [
            "Property names remain unchanged between executions.",
            "`compared_fields` is always an array of objects.",
            "`mismatches` is always an array and never `null`.",
            "Numeric values remain numeric.",
            "Invalid enum values are rejected.",
            "Additional properties are rejected.",
            "Invalid results never reach governance.",
            "Repair attempts do not repeat business actions.",
            "Validation errors are readable by non-technical users.",
            "Build and Publish is blocked when contract tests fail."
        ]
    },
    "ART-GOV-002": {
        "problem": (
            "The Human Review notification displays unresolved template variables instead of the actual runtime "
            "values generated during implant reconciliation agent.\n\n"
            "Examples displayed in the notification include:\n\n"
            "- `${IMPLANT_CASE_ID}`\n"
            "- `${RECONCILIATION_CLASSIFICATION}`\n"
            "- `${RECONCILIATION_MATCH_STATUS}`\n"
            "- `${RECONCILIATION_REASON}`\n"
            "- `${RECOMMENDED_NEXT_OWNER}`\n\n"
            "The agent result and serverless-function result contain the correct values, but those values are not "
            "resolved inside the Human Review notification."
        ),
        "observed_behavior": (
            "The notification displays template expressions as literal text, making the review information "
            "unreadable and preventing the reviewer from making an informed decision."
        ),
        "actual_result": (
            "The notification displays template expressions as literal text, making the review information "
            "unreadable and preventing the reviewer from making an informed decision."
        ),
        "reproduction": "Not provided",
        "repro_steps": "Not provided",
        "expected_behavior": (
            "The Human Review notification should display the actual case ID, classification, match status, "
            "reconciliation reason and recommended owner produced during the current execution."
        ),
        "expected_result": (
            "The Human Review notification should display the actual case ID, classification, match status, "
            "reconciliation reason and recommended owner produced during the current execution."
        ),
        "business_impact": (
            "Human reviewers cannot verify runtime case facts during approval, risking incorrect approval or "
            "rejection of critical reconciliation actions."
        ),
        "user_experience": (
            "The reviewer sees unresolved raw template variables like `${IMPLANT_CASE_ID}` instead of real clinical case "
            "data, creating confusion and blocking informed human decision-making."
        ),
        "investigation_guidance": (
            "Inspect the Human Review notification construction and templating pipeline. Trace where fact references "
            "from prior action execution contexts are bound to the review request payload and verify variable interpolation."
        ),
        "fix_requirement": (
            "Resolve all mapped fact references from the current execution context before creating the Human Review request. "
            "Ensure no unresolved template expressions reach the reviewer interface."
        ),
        "recommended_solution": (
            "Human Review must receive resolved runtime facts, not unresolved template expressions.\n\n"
            "1. Store Human Review mappings as typed references to registered facts, not as plain text containing `${...}`.\n"
            "2. Validate every mapped fact when the policy is saved.\n"
            "3. Validate every mapped fact again during Build and Publish.\n"
            "4. Resolve all fact references from the current action-execution context before creating the review request.\n"
            "5. Preserve the resolved values as an immutable approval snapshot.\n"
            "6. If a required fact is missing or unresolved: do not create the Human Review request, stop execution with HUMAN_REVIEW_FACT_RESOLUTION_FAILED, and identify the exact missing fact and its source action.\n"
            "7. Never display unresolved expressions such as `${IMPLANT_CASE_ID}` to reviewers.\n"
            "8. Provide a mapping preview containing representative typed values before publishing.\n"
            "9. Display human-readable labels in the reviewer interface while retaining technical keys in the audit view.\n"
            "10. Support structured fields such as arrays and objects with readable tables instead of raw serialized text.\n"
            "11. Record the source action, fact key, resolved value, data type, execution ID, and resolution timestamp in the audit log."
        ),
        "minimum_working_fix": (
            "Resolve all fact references from the current action-execution context before creating the review request. "
            "If a required fact is missing or unresolved, do not create the Human Review request and stop execution with HUMAN_REVIEW_FACT_RESOLUTION_FAILED."
        ),
        "acceptance_criteria": [
            "Every configured field displays its resolved runtime value.",
            "No `${...}` expression appears in a Human Review notification.",
            "Missing required facts block request creation.",
            "The reviewer sees readable labels and formatted values.",
            "Arrays and objects render as structured content.",
            "The approval snapshot cannot change after the request is created.",
            "The audit log identifies the source of every resolved fact."
        ]
    },
    "ART-GOV-003": {
        "problem": (
            "After a reviewer approves or rejects an Implant Usage Evidence Review request, the agent can invoke the "
            "same governed action again and create another approval notification for the same case.\n\n"
            "The previous approval request is resolved, but the workflow does not reliably continue to a final outcome."
        ),
        "observed_behavior": (
            "A new approval notification can be generated after the previous human decision, resulting in a repeated approval loop."
        ),
        "actual_result": (
            "A new approval notification can be generated after the previous human decision, resulting in a repeated approval loop."
        ),
        "reproduction": "Not provided",
        "repro_steps": "Not provided",
        "expected_behavior": (
            "Each case should create only one Human Review request.\n\n"
            "After the reviewer selects Approve or Reject, the agent should resume from that decision, return the "
            "final outcome and must not invoke the same governed action again for the same case."
        ),
        "expected_result": (
            "Each case should create only one Human Review request.\n\n"
            "After the reviewer selects Approve or Reject, the agent should resume from that decision, return the "
            "final outcome and must not invoke the same governed action again for the same case."
        ),
        "business_impact": (
            "Duplicate approval notifications spam human reviewers, disrupt hospital workflows, and risk repeated executions "
            "of irreversible business actions."
        ),
        "user_experience": (
            "Reviewers receive repeated approval requests for cases they already decided on, leading to alert fatigue and "
            "uncertainty about whether their decision was recorded."
        ),
        "investigation_guidance": (
            "Inspect the post-decision resumption logic in the governance engine and action execution state machine. "
            "Check how execution resumes after human review resolution, whether idempotency keys are enforced, and why the governed action is re-entered."
        ),
        "fix_requirement": (
            "A Human Review decision must resume the suspended execution exactly once and must never create another approval "
            "request for the same action execution."
        ),
        "recommended_solution": (
            "A Human Review decision must resume the suspended execution exactly once and must never create another approval "
            "request for the same action execution.\n\n"
            "1. Assign a unique `action_execution_id` to every governed action invocation.\n"
            "2. Create an approval request using an idempotency key derived from: Agent execution ID, Action execution ID, and Policy ID.\n"
            "3. Enforce a unique database constraint on the approval idempotency key.\n"
            "4. When Human Review is required: persist execution state, mark it WAITING_FOR_HUMAN, and stop further agent reasoning and action invocation.\n"
            "5. When the reviewer approves or rejects: persist decision atomically, mark request resolved, and resume the original suspended execution from saved continuation point.\n"
            "6. Do not restart the agent from the original user prompt after the decision.\n"
            "7. Pass the approval decision as a trusted system event, not as a new conversational user message.\n"
            "8. Before creating any approval request, check whether the action execution already has a pending request, approved decision, or rejected decision.\n"
            "9. If a decision already exists, return the stored decision instead of invoking Human Review again.\n"
            "10. Ignore duplicate button clicks, retry deliveries, and repeated decision events using the same idempotency key.\n"
            "11. Record request creation, decision, resumption, and completion in one audit trail."
        ),
        "minimum_working_fix": (
            "A Human Review decision must resume the suspended execution exactly once and must never create another approval "
            "request for the same action execution."
        ),
        "acceptance_criteria": [
            "One governed action execution creates no more than one approval request.",
            "Approving does not generate another notification.",
            "Rejecting does not generate another notification.",
            "The original execution resumes rather than restarting.",
            "Duplicate clicks do not create duplicate decisions.",
            "Event retries do not create duplicate requests.",
            "The final Agent Result references the original approval decision.",
            "The audit trail shows one request, one decision, and one continuation."
        ]
    },
    "ART-SFN-001": {
        "problem": (
            "A serverless function connected to the agent through Tool Connector does not appear in Governance → Action Registry "
            "when the action capability is changed to Tool Action.\n\n"
            "The workflow was built and published successfully, but the Tool selector still displays “No matches.”"
        ),
        "observed_behavior": (
            "The serverless function executes successfully from the workflow, but it is unavailable in the Action Registry Tool selector.\n\n"
            "This prevents the function from being directly bound to the governed action."
        ),
        "actual_result": (
            "The serverless function executes successfully from the workflow, but it is unavailable in the Action Registry Tool selector.\n\n"
            "This prevents the function from being directly bound to the governed action."
        ),
        "reproduction": "Not provided",
        "repro_steps": "Not provided",
        "expected_behavior": (
            "A connected and published serverless function should be selectable as the Tool Action target so its deterministic "
            "output can be governed by policy rules and Human Review."
        ),
        "expected_result": (
            "A connected and published serverless function should be selectable as the Tool Action target so its deterministic "
            "output can be governed by policy rules and Human Review."
        ),
        "business_impact": (
            "Published serverless functions cannot be governed by policy rules or Human Review, blocking compliant deployment "
            "of medical device integration workflows."
        ),
        "user_experience": (
            "Users configure and publish serverless functions successfully, but when configuring governed Tool Actions, the "
            "dropdown displays “No matches”, forcing manual workarounds."
        ),
        "investigation_guidance": (
            "Inspect the capability registry and catalog lookup queried by the Action Registry Tool selector. "
            "Verify query filters, status checks, and synchronization between Tool Connector published assets and Action Registry."
        ),
        "fix_requirement": (
            "Published serverless functions connected to an agent workflow must be discoverable and selectable as governed Tool Actions."
        ),
        "recommended_solution": (
            "Published serverless functions connected to an agent workflow must be discoverable and selectable as governed Tool Actions.\n\n"
            "1. Register every successfully published serverless function in a central capability registry.\n"
            "2. Store function ID, published version, name, provider, entrypoint, input/output schemas, workspace, environment, publication status, agent bindings, and governance eligibility.\n"
            "3. Tool Connector and Action Registry must query the same capability registry.\n"
            "4. Only published and active function versions should appear in Tool Action selection.\n"
            "5. Filter available functions by workspace, environment, permissions, and agent binding.\n"
            "6. When no function is available, replace generic 'No matches' with a specific diagnostic reason.\n"
            "7. When Build and Publish completes, update registry atomically and invalidate caches.\n"
            "8. Provide manual registry refresh option for administrators.\n"
            "9. Preserve selected function version in governed action definition.\n"
            "10. Prevent silent version switching after deployment.\n"
            "11. Validate function input and output schemas before allowing action to be saved.\n"
            "12. Show serverless function as a first-class Tool Action without requiring users to recreate it as another tool."
        ),
        "minimum_working_fix": (
            "Published serverless functions connected to an agent workflow must be discoverable and selectable as governed Tool Actions."
        ),
        "acceptance_criteria": [
            "A published and connected serverless function appears in Tool Action selection.",
            "Search finds the function by name and function ID.",
            "Unavailable functions display a specific diagnostic reason.",
            "Registry refresh does not require recreating the function.",
            "The selected version remains locked after publishing.",
            "Input and output schemas are available for policy facts and mappings.",
            "Workspace and environment isolation are enforced.",
            "The governed action successfully invokes the selected serverless function."
        ]
    },
    "ART-ORCHESTRATOR-001": {
        "problem": (
            "The values displayed in the Condition Builder Key field dropdown are severely truncated due to "
            "restricted dropdown width and overflow clipping, showing only `agentOrchestrator_1.c...` for all options. "
            "This prevents users from identifying, distinguishing, and selecting the correct runtime variables and path attributes."
        ),
        "observed_behavior": (
            "Values in the Condition Builder Key dropdown are truncated to `agentOrchestrator_1.c...` due to narrow dropdown width. "
            "Multiple distinct attributes appear visually identical, making it difficult or impossible to identify and select the intended value."
        ),
        "actual_result": (
            "Values in the Condition Builder Key dropdown are truncated to `agentOrchestrator_1.c...` due to narrow dropdown width. "
            "Multiple distinct attributes appear visually identical, making it difficult or impossible to identify and select the intended value."
        ),
        "reproduction": (
            "1. Open the workflow Orchestrator and select a Condition Builder node.\n"
            "2. Click the Key field to open the variable dropdown.\n"
            "3. Observe that options are truncated to 'agentOrchestrator_1.c...'."
        ),
        "repro_steps": (
            "1. Open the workflow Orchestrator and select a Condition Builder node.\n"
            "2. Click the Key field to open the variable dropdown.\n"
            "3. Observe that options are truncated to 'agentOrchestrator_1.c...'."
        ),
        "expected_behavior": (
            "Dropdown options in the Condition Builder Key field should display full variable and path names clearly, "
            "adjusting dropdown container width to fit content (or providing text wrapping / tooltips on hover) so users "
            "can distinguish and select the appropriate key."
        ),
        "expected_result": (
            "Dropdown options in the Condition Builder Key field should display full variable and path names clearly, "
            "adjusting dropdown container width to fit content (or providing text wrapping / tooltips on hover) so users "
            "can distinguish and select the appropriate key."
        ),
        "business_impact": (
            "Users cannot reliably configure routing conditions in workflow orchestrations when multiple variables share a common prefix, "
            "leading to configuration errors, misrouted workflow execution paths, and decreased developer productivity."
        ),
        "user_experience": (
            "When configuring routing conditions in the Condition Builder, users open the Key dropdown and see a column of identical "
            "truncated strings (`agentOrchestrator_1.c...`), forcing guesswork or trial-and-error to select the right field."
        ),
        "investigation_guidance": (
            "Inspect the Condition Builder Key dropdown component and styling. Check CSS width constraints, text-overflow rules, "
            "and tooltip support for dropdown items."
        ),
        "fix_requirement": (
            "Expand the Condition Builder Key dropdown menu width and ensure variable paths are fully readable or viewable on hover."
        ),
        "recommended_solution": (
            "Update the Condition Builder Key dropdown UI styling and component behavior to ensure full readability:\n\n"
            "1. Set dropdown menu width to fit content (`min-width: max-content` or expanded fixed width) with a sensible maximum width and horizontal scrolling or auto-expansion.\n"
            "2. Implement text truncation with ellipsis only when exceeding maximum container bounds, and provide native `title` or tooltip attributes showing the full variable path on hover.\n"
            "3. Ensure selected token pills and dropdown items preserve clear font sizing, padding, and high-contrast styling.\n"
            "4. Optionally support variable path shortening with smart middle-truncation or hierarchy grouping (e.g. grouping by node `agentOrchestrator_1` -> sub-properties)."
        ),
        "minimum_working_fix": (
            "Expand the Condition Builder Key dropdown menu width (e.g., `min-width: 320px` or `width: max-content`) and add tooltip/title attributes so variable paths are fully visible and readable."
        ),
        "acceptance_criteria": [
            "Dropdown options display the complete variable path without premature truncation.",
            "Dropdown container dynamically adjusts or provides sufficient width for long variable names.",
            "Full variable names are accessible via tooltip on hover if text exceeds container bounds.",
            "Users can clearly identify and select distinct variables originating from the same workflow node."
        ]
    },
    "ART-ORCHESTRATOR-002": {
        "problem": (
            "When an Agent's output message schema is updated and saved with new fields (such as `media_status`, `media_summary`, `observed_facts`, and `reported_facts`), "
            "downstream nodes in the Orchestration (including Condition Builder, Data Mapper, and Serverless Function mapping) do not reflect the new fields. "
            "Even after saving the agent, rebuilding/publishing the orchestration, and performing a hard refresh, the orchestrator continues displaying outdated schema fields "
            "(such as `classification`, `inferences`, `missing_information`, `ready_for_ticket`, `ticket.*`, and stale `facts`). "
            "This prevents updated agent output data from being mapped or utilized across workflow steps."
        ),
        "observed_behavior": (
            "Downstream nodes in the Orchestration retain stale, cached schema definitions and do not expose newly configured fields "
            "(`media_status`, `media_summary`, `observed_facts`, `reported_facts`), continuing to display legacy fields "
            "(`classification`, `inferences`, `missing_information`, `ready_for_ticket`, `ticket.*`, and stale `facts`)."
        ),
        "actual_result": (
            "Downstream nodes in the Orchestration retain stale, cached schema definitions and do not expose newly configured fields "
            "(`media_status`, `media_summary`, `observed_facts`, `reported_facts`), continuing to display legacy fields "
            "(`classification`, `inferences`, `missing_information`, `ready_for_ticket`, `ticket.*`, and stale `facts`)."
        ),
        "reproduction": (
            "1. In Agent Lab, update and save an agent's output schema with new fields.\n"
            "2. Open the Orchestration workflow using this agent, rebuild/publish, and refresh.\n"
            "3. Open downstream nodes (Condition Builder, Data Mapper) and inspect available input fields."
        ),
        "repro_steps": (
            "1. In Agent Lab, update and save an agent's output schema with new fields.\n"
            "2. Open the Orchestration workflow using this agent, rebuild/publish, and refresh.\n"
            "3. Open downstream nodes (Condition Builder, Data Mapper) and inspect available input fields."
        ),
        "expected_behavior": (
            "The Orchestrator should use the Agent's latest saved/published output schema and expose all updated fields correctly to downstream nodes "
            "upon save, rebuild/publish, or schema refresh."
        ),
        "expected_result": (
            "The Orchestrator should use the Agent's latest saved/published output schema and expose all updated fields correctly to downstream nodes "
            "upon save, rebuild/publish, or schema refresh."
        ),
        "business_impact": (
            "Workflows relying on updated agent capabilities cannot access new output data, preventing automated ticket processing, multi-modal media status handling, "
            "and fact-based routing. This blocks feature rollout and breaks end-to-end orchestration pipelines."
        ),
        "user_experience": (
            "Users configure new output fields in Agent Lab expecting them to be available in the workflow Orchestration. "
            "However, dropdowns in Data Mapper and Condition Builder omit the new fields and display obsolete structures, "
            "causing confusion and blocking workflow completion despite rebuilding and refreshing."
        ),
        "investigation_guidance": (
            "Inspect schema propagation and caching between Agent definitions and the Orchestration graph. "
            "Check the schema fetch lifecycle during workflow load, build, and publish, as well as port metadata resolution in downstream nodes."
        ),
        "fix_requirement": (
            "Invalidate cached node schemas and fetch the current agent output schema during workflow load and rebuild/publish "
            "so downstream nodes receive updated fields."
        ),
        "recommended_solution": (
            "Implement reactive schema synchronization and cache invalidation between Agent Lab and Workflow Orchestrator:\n\n"
            "1. Invalidate Orchestrator node schema caches whenever an underlying Agent definition or output schema is saved or published.\n"
            "2. Implement schema version tracking on Agent nodes so Orchestration workflows detect when an agent node schema is out of date.\n"
            "3. Ensure Build and Publish re-fetches canonical output schemas for all referenced workflow agent nodes before compiling downstream port definitions.\n"
            "4. Provide an explicit 'Refresh Node Schema' or 'Sync Agent Schema' action in the Orchestrator node configuration drawer.\n"
            "5. Update Data Mapper and Condition Builder source field resolvers to pull schema definitions directly from the active agent version rather than stale session state."
        ),
        "minimum_working_fix": (
            "Invalidate the workflow node schema cache and re-fetch the latest Agent output schema during workflow load and rebuild/publish "
            "so downstream node field pickers receive updated schema definitions."
        ),
        "acceptance_criteria": [
            "Saving changes to an Agent's output schema propagates updated fields to the Orchestration workflow.",
            "Newly added agent output fields appear immediately in downstream Data Mapper source field pickers.",
            "Newly added agent output fields are selectable in Condition Builder routing rules.",
            "Rebuilding and publishing the Orchestration persists and enforces the updated schema contract.",
            "Deprecated or removed schema fields are flagged or removed from downstream mappings."
        ]
    },
    "ART-AGENT-002": {
        "problem": (
            "When testing the Ticket Resolution Agent with uploaded media (image or video) using the configured OpenAI GPT-5.1 Mini model, "
            "the run fails with a generic `AGENT_RUN_ERROR` (\"The agent could not complete this request.\"). "
            "In Observability, storage tools (`storage list files`, `storage get file url`) execute successfully, "
            "but execution terminates at the Agent step with \"No diagnostic message was recorded.\" "
            "Neither the Agent Test UI nor Observability provides actionable diagnostics, making it impossible to determine whether "
            "the failure stems from media retrieval, multimodal model invocation, output schema parsing, or another lifecycle phase."
        ),
        "observed_behavior": (
            "The Agent run terminates with an error modal showing `type: agent_error_response`, `status: error`, "
            "`code: AGENT_RUN_ERROR`, and `message: The agent could not complete this request.` In Observability Conversation Explorer, "
            "the trace marks `Run failed` and `Agent error` with the description: \"This activity could not be completed. No diagnostic message was recorded.\""
        ),
        "actual_result": (
            "The Agent run terminates with an error modal showing `type: agent_error_response`, `status: error`, "
            "`code: AGENT_RUN_ERROR`, and `message: The agent could not complete this request.` In Observability Conversation Explorer, "
            "the trace marks `Run failed` and `Agent error` with the description: \"This activity could not be completed. No diagnostic message was recorded.\""
        ),
        "reproduction": (
            "1. Open the Ticket Resolution Agent test interface.\n"
            "2. Upload an image or video file and submit.\n"
            "3. Observe the error modal in the test UI and the corresponding trace in Observability."
        ),
        "repro_steps": (
            "1. Open the Ticket Resolution Agent test interface.\n"
            "2. Upload an image or video file and submit.\n"
            "3. Observe the error modal in the test UI and the corresponding trace in Observability."
        ),
        "expected_behavior": (
            "The Agent should process the uploaded media (image or video), extract relevant information, create a summary, "
            "and return structured output based on the configured output schema. If processing fails at any stage, ART must capture "
            "and display a clear, descriptive diagnostic error message explaining the exact reason and failing step."
        ),
        "expected_result": (
            "The Agent should process the uploaded media (image or video), extract relevant information, create a summary, "
            "and return structured output based on the configured output schema. If processing fails at any stage, ART must capture "
            "and display a clear, descriptive diagnostic error message explaining the exact reason and failing step."
        ),
        "business_impact": (
            "Automated support ticket resolution workflows relying on image or video evidence cannot execute, blocking core multi-modal "
            "agent capabilities. Furthermore, developers and support engineers cannot diagnose root causes or troubleshoot runtime failures "
            "due to suppressed diagnostic messages, increasing mean time to repair and delaying production deployments."
        ),
        "user_experience": (
            "When a user submits an image or video in the Agent Test interface, the agent fails with an unhelpful error badge and generic "
            "modal dialog (\"The agent could not complete this request.\"). Navigating to Observability to inspect the failure provides "
            "no additional clarity, showing only \"No diagnostic message was recorded,\" leaving the user blocked with no actionable path to resolution."
        ),
        "investigation_guidance": (
            "Inspect the multimodal execution path in the agent runner where media assets are passed to the model. "
            "Check exception handling and diagnostic message propagation to Observability trace spans and client responses."
        ),
        "fix_requirement": (
            "Catch unhandled exceptions in the agent runner during media processing and schema parsing, record the exception message "
            "into the Observability trace span's diagnostic field, and return the descriptive error string to the user interface instead "
            "of suppressing it with a generic fallback."
        ),
        "recommended_solution": (
            "Implement robust exception handling, diagnostic logging, and error propagation across the agent multimodal execution pipeline:\n\n"
            "1. Ensure media payloads fetched by storage tools are properly validated and formatted for the selected model's multimodal API contract.\n"
            "2. Capture upstream model errors, HTTP status codes, payload limit errors, and schema parsing exceptions at each lifecycle step.\n"
            "3. Record granular diagnostic logs and error details in Observability trace spans rather than suppressing error strings.\n"
            "4. Replace the generic AGENT_RUN_ERROR fallback with specific error codes (e.g., MEDIA_PAYLOAD_UNSUPPORTED, MODEL_INVOCATION_TIMEOUT, SCHEMA_VALIDATION_FAILED) and descriptive messages in the Agent Test interface.\n"
            "5. Provide actionable remediation hints in both the UI error modal and the Observability Activity pane."
        ),
        "minimum_working_fix": (
            "Catch unhandled exceptions in the agent runner during media processing and schema parsing, record the exception message "
            "into the Observability trace span's diagnostic field, and return the descriptive error string to the user interface instead "
            "of suppressing it with a generic fallback."
        ),
        "acceptance_criteria": [
            "Uploaded image or video media is successfully processed by the agent to generate structured output conforming to the configured schema.",
            "If media processing fails, the Agent Test modal displays a descriptive error message indicating the exact failure reason.",
            "Observability trace tree captures and displays meaningful diagnostic messages for failed agent activities instead of 'No diagnostic message was recorded.'",
            "Tool execution, LLM invocation, and output validation phases record distinct, traceable status spans."
        ]
    },
    "ART-ORCHESTRATOR-003": {
        "problem": (
            "In the Daily Work Coordinator Orchestrator, the Start node input schema is configured with one required runtime field named message of type string. "
            "When opening Orchestrator Test, ART does not provide an input field where the user can enter the runtime value for message. "
            "Instead, the Test Input UI displays the JSON Schema definition itself as editable/form fields (additionalProperties, properties, message, type, required, required[0], root type), "
            "preventing users from providing the actual runtime payload expected by the Start node."
        ),
        "observed_behavior": (
            "When opening the Orchestrator Test side panel for a workflow configured with a Start node input schema, the Test Input section exposes input controls corresponding to the internal JSON Schema meta-schema keys rather than the target data fields. "
            "Specifically, the form displays: an additionalProperties checkbox, a properties container with nested message -> type: string input, a required list control with required[0]: message, and a root type: object field. "
            "Users cannot enter a direct runtime string value for message, making it difficult or impossible to pass the expected runtime payload (start.message) to the workflow through the Test panel."
        ),
        "actual_result": (
            "Orchestrator Test exposes the schema-definition structure itself instead of a runtime message input. "
            "This makes it difficult or impossible to provide the Start node's expected test payload through the Test UI."
        ),
        "reproduction": (
            "1. Open the Daily Work Coordinator Orchestrator in the workflow canvas.\n"
            "2. Open Configure Start -> Basic Config and define the Start input schema with properties.message (type string) and required: [message].\n"
            "3. Save the Start node configuration.\n"
            "4. Click Orchestrator Test to open the test execution side panel.\n"
            "5. Inspect the generated fields under TEST INPUT."
        ),
        "repro_steps": (
            "1. Open the Daily Work Coordinator Orchestrator in the workflow canvas.\n"
            "2. Open Configure Start -> Basic Config and define the Start input schema with properties.message (type string) and required: [message].\n"
            "3. Save the Start node configuration.\n"
            "4. Click Orchestrator Test to open the test execution side panel.\n"
            "5. Inspect the generated fields under TEST INPUT."
        ),
        "expected_behavior": (
            "Orchestrator Test should interpret the configured Start input schema and generate runtime input controls from it. "
            "For this schema, it should show a user-editable message field. When Run is clicked, the workflow should receive the entered value as start.message."
        ),
        "expected_result": (
            "Orchestrator Test should interpret the configured Start input schema and generate runtime input controls from it. "
            "For this schema, it should show a user-editable message field. When Run is clicked, the workflow should receive the entered value as start.message."
        ),
        "business_impact": (
            "Workflow developers and QA engineers cannot execute, test, or validate reactive orchestrations through the Orchestrator Test interface when Start nodes have structured input schemas. "
            "This blocks rapid iteration, testing of multi-step automations, and end-to-end verification of workflows that depend on initial message payloads."
        ),
        "user_experience": (
            "When a user opens Orchestrator Test expecting to test-run their workflow with sample input text, they are confronted with a confusing form exposing raw JSON Schema keywords (additionalProperties, properties, type, required[0]). "
            "Attempting to fill in these fields fails to produce the expected runtime object, creating confusion and blocking test execution."
        ),
        "investigation_guidance": (
            "Inspect the Orchestrator Test panel component and form generation pipeline where the Start node's input schema is loaded to construct the Test Input UI. "
            "Trace where the Start node's input_schema is received and parsed by the Orchestrator Test runner. "
            "Investigate why the form renderer binds to the schema definition object itself rather than compiling its properties dictionary into input field definitions. "
            "Contrast with form generation in other ART test runners to align on the standard schema-to-form contract."
        ),
        "fix_requirement": (
            "Orchestrator Test must interpret the Start node's configured input JSON Schema and render form input controls for the defined runtime properties (e.g., an editable message string input) instead of displaying the JSON Schema specification keywords as form inputs. "
            "The submitted form data must produce a runtime payload matching the configured schema structure."
        ),
        "recommended_solution": (
            "Implement schema-aware runtime form generation for Orchestrator Test:\n\n"
            "1. Pass the Start node's input schema to a dedicated schema form compiler that extracts defined properties (properties.*) and their types.\n"
            "2. Render appropriate input widgets based on property definitions (e.g. text inputs for string, number inputs for number, toggles for boolean, item lists for array).\n"
            "3. Enforce validation rules defined in the schema (required properties, enums, format constraints) on the client side before triggering workflow runs.\n"
            "4. Construct the runtime execution payload from the user-entered property values under the root object structure (e.g., {\"message\": \"<entered_value>\"}) and pass it as the Start node execution payload.\n"
            "5. Provide a raw JSON input toggle for developers who prefer directly pasting a JSON payload."
        ),
        "minimum_working_fix": (
            "Update the Orchestrator Test panel to parse the properties map of the Start node's input schema and render runtime input controls for each declared property (e.g., message) instead of binding form controls directly to the top-level schema definition object."
        ),
        "acceptance_criteria": [
            "Orchestrator Test renders an editable input control for message when the Start node schema defines properties.message.",
            "JSON Schema meta-keywords (additionalProperties, properties, required, root type) are not displayed as editable form fields in the Test Input UI.",
            "Required fields defined in the schema's required array are marked as mandatory in the Test UI.",
            "Submitting the test form sends the user-entered value as the runtime payload ({ \"message\": \"<value>\" }) to the Start node.",
            "Workflow execution successfully receives and processes start.message."
        ]
    },
    "ART-AGENT-003": {
        "title": "Agent Workflow Displays Default Robot Icon Instead of Configured Custom Icon",
        "module": "AGENT",
        "severity": "LOW",
        "priority": 3,
        "environment": "Testing (Enterprise Plan)",
        "tags": [
            "Agent-Lab",
            "Agent-Builder",
            "Agent-Node",
            "Custom-Icon",
            "UI-Branding",
            "Workflow-Canvas"
        ],
        "problem": (
            "A custom logo/icon was provided for the Agent, but the Agent workflow still displays the default ART robot icon instead of the configured custom logo. "
            "In the attached evidence, the custom agent icon is provided separately, while the Agent Builder workflow for 'attacking agent' continues to show the default robot icon on the Agent node."
        ),
        "observed_behavior": (
            "In the Agent Lab workflow for 'attacking agent', the central Agent node renders the default ART robot icon. "
            "A custom agent icon was configured and provided separately, but the custom graphic is not displayed on the Agent node in the workflow canvas."
        ),
        "actual_result": (
            "The default robot icon continues to appear on the Agent node, and the configured custom logo/icon is not reflected in the Agent workflow canvas."
        ),
        "reproduction": "Not provided.",
        "repro_steps": "Not provided.",
        "expected_behavior": (
            "After a custom Agent logo/icon is configured, the Agent Builder should display that configured icon consistently on the Agent node instead of the default robot icon."
        ),
        "expected_result": (
            "After a custom Agent logo/icon is configured, the Agent Builder should display that configured icon consistently on the Agent node instead of the default robot icon."
        ),
        "business_impact": (
            "Custom agent branding and visual differentiation are not reflected in the workflow canvas. "
            "Organizations and users cannot visually identify specialized agents by their custom logos, reducing clarity in multi-agent environments and degrading the white-label/branding experience."
        ),
        "user_experience": (
            "Users who upload or assign a custom icon to an agent observe no visual change on the workflow canvas. "
            "The agent node continues to display the generic ART robot graphic, creating uncertainty as to whether the custom logo configuration was successfully saved or applied."
        ),
        "investigation_guidance": (
            "Inspect the Agent Lab frontend workflow canvas where Agent node components are rendered. "
            "Trace how the Agent node view model resolves the icon/avatar property from the agent configuration entity. "
            "Investigate whether the Agent node component checks for a custom icon asset reference or URL before rendering the fallback default robot icon. "
            "Verify if the agent configuration save and workflow load pipelines serialize, persist, and deserialize the custom icon URL or asset identifier."
        ),
        "fix_requirement": (
            "The Agent node component on the Agent Builder workflow canvas must check for a configured custom icon or logo on the agent definition. "
            "If a custom icon is present, it must render that custom image in the agent node avatar area instead of displaying the default robot icon."
        ),
        "recommended_solution": (
            "1. In the Agent node canvas component, bind the node avatar image source to the agent's custom icon URL/property if defined.\n"
            "2. Maintain the default ART robot icon as a fallback when no custom icon is configured or if the custom image fails to load.\n"
            "3. Ensure the workflow loader and canvas state management preserve the custom icon metadata when loading the agent workflow.\n"
            "4. Ensure appropriate CSS sizing (e.g. object-fit: contain) so custom icons scale neatly within the node avatar container."
        ),
        "minimum_working_fix": (
            "Update the Agent node canvas component to display the configured custom icon URL when present on the agent model, falling back to the default robot icon only when the custom icon property is empty or undefined."
        ),
        "acceptance_criteria": [
            "When a custom icon/logo is configured for an Agent, the Agent node in the Agent Builder workflow canvas displays that custom icon.",
            "When no custom icon is configured, the Agent node continues to display the default ART robot icon.",
            "If a custom icon fails to load, the Agent node gracefully falls back to the default robot icon.",
            "The custom icon renders with correct aspect ratio and scaling within the Agent node header."
        ]
    },
    "ART-AGENT-004": {
        "title": "Agent Description Does Not Sync Both Ways Between Agent Dashboard and Workflow",
        "module": "AGENT",
        "severity": "MEDIUM",
        "priority": 3,
        "environment": "Testing (Enterprise Plan)",
        "tags": [
            "Agent-Lab",
            "Agent-Dashboard",
            "Agent-Workflow",
            "Description-Sync",
            "Data-Consistency"
        ],
        "problem": (
            "The Agent description is not synchronized correctly between the Agent Dashboard and the Agent Workflow. "
            "When an agent description is added or updated from the Agent Dashboard/Homepage (Agent Studio), the updated description is visible on the dashboard card (e.g. for 'Daily Work Coordinator V2' showing 'Daily Work Coordinator V2 is a personal ...'), but inside the Agent Workflow canvas the central agent node still displays 'No Description added.' "
            "However, when the description is updated from inside the Agent Workflow, the change is reflected correctly on the Agent Dashboard. "
            "This creates inconsistent bidirectional synchronization behavior where the same Agent has two places to view and manage its description, but only Workflow-to-Dashboard synchronization functions properly."
        ),
        "observed_behavior": (
            "- Direction 1 (Dashboard → Workflow) [FAILED]:\n"
            "  When an Agent description is added or modified from the Agent Studio Dashboard (e.g., setting the description for 'Daily Work Coordinator V2' to 'Daily Work Coordinator V2 is a personal ...'), the dashboard card reflects the description. However, opening the Agent Workflow reveals that the central Agent node on the canvas displays 'No Description added.'\n"
            "- Direction 2 (Workflow → Dashboard) [PASSED]:\n"
            "  When the description is updated directly within the Agent Workflow editor, saving and returning to the Agent Dashboard correctly displays the updated description on the Agent card."
        ),
        "actual_result": (
            "- Dashboard → Workflow: Description does not update. The Agent Workflow canvas displays 'No Description added.'\n"
            "- Workflow → Dashboard: Description does update correctly."
        ),
        "reproduction": (
            "1. Navigate to the Agent Studio homepage / Agent Dashboard (Your agents section).\n"
            "2. Locate or create an agent (e.g., 'Daily Work Coordinator V2').\n"
            "3. Add or update the description from the Dashboard view (e.g. 'Daily Work Coordinator V2 is a personal ...').\n"
            "4. Verify that the updated description appears on the Agent card under Your agents on the Dashboard.\n"
            "5. Open the Agent Workflow editor by clicking on the agent card.\n"
            "6. Inspect the central Agent node on the workflow canvas.\n"
            "7. Observe that the node subtitle reads 'No Description added' instead of the description configured on the dashboard.\n"
            "8. In the Workflow editor, edit the agent description and return to the Dashboard; observe that the description does update on the dashboard card."
        ),
        "repro_steps": (
            "1. Navigate to the Agent Studio homepage / Agent Dashboard (Your agents section).\n"
            "2. Locate or create an agent (e.g., 'Daily Work Coordinator V2').\n"
            "3. Add or update the description from the Dashboard view (e.g. 'Daily Work Coordinator V2 is a personal ...').\n"
            "4. Verify that the updated description appears on the Agent card under Your agents on the Dashboard.\n"
            "5. Open the Agent Workflow editor by clicking on the agent card.\n"
            "6. Inspect the central Agent node on the workflow canvas.\n"
            "7. Observe that the node subtitle reads 'No Description added' instead of the description configured on the dashboard.\n"
            "8. In the Workflow editor, edit the agent description and return to the Dashboard; observe that the description does update on the dashboard card."
        ),
        "expected_behavior": (
            "The Agent should have a single description value. Updating the description from either the Agent Dashboard or Agent Workflow should automatically update the same description everywhere. "
            "Opening the Agent Workflow after setting a description on the Dashboard must display that description on the Agent node instead of 'No Description added.'"
        ),
        "expected_result": (
            "The Agent should have a single description value. Updating the description from either the Agent Dashboard or Agent Workflow should automatically update the same description everywhere. "
            "Opening the Agent Workflow after setting a description on the Dashboard must display that description on the Agent node instead of 'No Description added.'"
        ),
        "business_impact": (
            "Users must enter the same Agent description multiple times and are exposed to conflicting agent metadata across different screens. "
            "This creates confusion, increases friction during agent authoring and maintenance, and risks deploying agents with missing or mismatched documentation."
        ),
        "user_experience": (
            "When a user provides a clear description on the Agent Dashboard to document an agent's purpose, entering the workflow canvas displays 'No Description added.' "
            "Users assume their previous input was lost or unsaved, prompting unnecessary rework or mistrust in the platform's state persistence."
        ),
        "investigation_guidance": (
            "Inspect how the Agent entity description is retrieved and persisted across the Agent Dashboard and the Agent Workflow editor:\n"
            "1. Examine the API endpoints and payload schemas used by the Agent Dashboard update action versus the Agent Workflow settings drawer to check if they write to distinct fields (e.g. top-level agent entity description vs. workflow graph definition workflow.description or node metadata).\n"
            "2. Trace the workflow editor initialization and fetch routines to determine where it sources the displayed description string, and why it does not read the updated agent entity description.\n"
            "3. Verify if state caching in the workflow canvas prevents newly updated dashboard metadata from being fetched."
        ),
        "fix_requirement": (
            "Establish a single source of truth for the Agent description across both views. Updates made in either the Agent Dashboard or the Agent Workflow must persist to the same canonical property, "
            "and opening the Workflow editor must populate the Agent node with the current description rather than falling back to 'No Description added.'"
        ),
        "recommended_solution": (
            "1. Use the same persisted Agent description field/source for both the Agent Dashboard and Agent Workflow views.\n"
            "2. Ensure the Agent Workflow initialization query fetches and populates the description from the canonical Agent entity record.\n"
            "3. If the workflow canvas maintains a separate node description property, ensure it is bidirectionally synchronized with the root agent entity description during load and save operations.\n"
            "4. Invalidate or refresh cached agent metadata in the client store whenever navigation occurs between the dashboard and workflow canvas."
        ),
        "minimum_working_fix": (
            "Update the Agent Workflow editor's canvas loader to read and display the Agent record's top-level description property upon opening, rather than falling back to 'No Description added' when workflow-specific node description metadata is empty."
        ),
        "acceptance_criteria": [
            "Updating an Agent description from the Agent Dashboard immediately reflects in the Agent Workflow editor upon opening.",
            "Updating an Agent description from the Agent Workflow immediately reflects on the Agent Dashboard card.",
            "When an Agent has a description configured on the Dashboard (e.g. 'Daily Work Coordinator V2 is a personal ...'), opening the Agent Workflow displays that text on the central node instead of 'No Description added.'",
            "Both interfaces display the identical description value after edits in either location."
        ]
    },
    "ART-AGENT-005": {
        "title": "Conversation State Inconsistency: Multi-Turn Task Reconciliation Omits Cumulative Tasks",
        "module": "AGENT",
        "severity": "HIGH",
        "priority": 2,
        "environment": "Testing",
        "tags": [
            "Agent-Lab",
            "Multi-Turn",
            "State-Management",
            "Conversation-History",
            "Task-Reconciliation",
            "Structured-Output"
        ],
        "problem": (
            "Daily Work Coordinator V2 exhibits a conversation state consistency defect during multi-turn interactions. "
            "When testing the Agent in a continuous conversation thread with multiple sequential task operations (creating tasks, changing status, blocking tasks, setting dependencies, resuming work, completing work, and adding more tasks), individual responses process the immediate turn, but the Agent does not reliably maintain, reconcile, and reconstruct the complete cumulative task state across the conversation. "
            "When querying for remaining or open work after multiple task updates, the returned structured output can omit tasks or return an incomplete representation of active work that should exist based on earlier turns in the same thread."
        ),
        "observed_behavior": (
            "Across a multi-turn conversation thread in Agent Test (Thread: 8bc4a601-d959-481e-8f46-97def160a025):\n"
            "- The Agent responds to individual prompts with structured JSON payloads matching its schema definition (e.g. Finish the Agent X banner as planned/in progress, Update the provider sheet as planned/blocked).\n"
            "- However, as the conversation progresses through multiple sequential task additions, status updates, blocking dependencies, and completions, later structured outputs do not consistently maintain the full set of established tasks.\n"
            "- When asked for remaining or open work, the returned structured output (e.g. open_tasks) can omit previously established tasks or fail to reflect the true cumulative state established across earlier messages in the same thread."
        ),
        "actual_result": (
            "After multiple task additions and status changes in the same thread, later structured responses do not consistently represent all task state established by previous messages, omitting valid unfinished tasks from the cumulative result."
        ),
        "reproduction": (
            "1. Open Daily Work Coordinator V2 in Agent Lab and open Agent Test (Thread: 8bc4a601-d959-481e-8f46-97def160a025).\n"
            "2. Turn 1 (09:05 AM): Send 'I have started working on the Agent X screenshots.' (Agent records task in progress, high priority, deadline 4 PM).\n"
            "3. Turn 2 (09:05 AM): Send '...waiting for Ashwin to send the final assets.' (Agent updates task to blocked, waiting on Ashwin).\n"
            "4. Turn 3 (09:06 AM): Send 'Ashwin sent the assets. I have resumed working on the screenshots.' (Agent transitions task to in progress).\n"
            "5. Turn 4 (09:06 AM): Send 'The Agent X screenshots are completed.' (Agent marks task completed).\n"
            "6. Turn 5 (09:06 AM): Send 'What work do I still need to do?' (Agent returns empty open_tasks list).\n"
            "7. Turn 6 (09:14 AM): Send 'I need to finish the Agent X banner by 2 PM. This is high priority.' (Agent creates task as planned).\n"
            "8. Turn 7 (09:14 AM): Send 'I also need to update the provider sheet today. This is medium priority.' (Agent creates task as planned).\n"
            "9. Turn 8 (09:14 AM): Send 'I started working on the Agent X banner.' (Agent updates banner task to in progress).\n"
            "10. Turn 9 (09:14 AM): Send 'The provider sheet is blocked because I am waiting for Karthik to confirm the providers.' (Agent updates task to blocked, waiting on Karthik).\n"
            "11. Turn 10 (09:14 AM): Send '1. What work do I still need to do?' and observe the returned structured open_tasks.\n"
            "12. Notice across extended multi-turn conversations that earlier tasks or accumulated task state can be dropped or omitted from subsequent reconciliation queries."
        ),
        "repro_steps": (
            "1. Open Daily Work Coordinator V2 in Agent Lab and open Agent Test (Thread: 8bc4a601-d959-481e-8f46-97def160a025).\n"
            "2. Turn 1 (09:05 AM): Send 'I have started working on the Agent X screenshots.' (Agent records task in progress, high priority, deadline 4 PM).\n"
            "3. Turn 2 (09:05 AM): Send '...waiting for Ashwin to send the final assets.' (Agent updates task to blocked, waiting on Ashwin).\n"
            "4. Turn 3 (09:06 AM): Send 'Ashwin sent the assets. I have resumed working on the screenshots.' (Agent transitions task to in progress).\n"
            "5. Turn 4 (09:06 AM): Send 'The Agent X screenshots are completed.' (Agent marks task completed).\n"
            "6. Turn 5 (09:06 AM): Send 'What work do I still need to do?' (Agent returns empty open_tasks list).\n"
            "7. Turn 6 (09:14 AM): Send 'I need to finish the Agent X banner by 2 PM. This is high priority.' (Agent creates task as planned).\n"
            "8. Turn 7 (09:14 AM): Send 'I also need to update the provider sheet today. This is medium priority.' (Agent creates task as planned).\n"
            "9. Turn 8 (09:14 AM): Send 'I started working on the Agent X banner.' (Agent updates banner task to in progress).\n"
            "10. Turn 9 (09:14 AM): Send 'The provider sheet is blocked because I am waiting for Karthik to confirm the providers.' (Agent updates task to blocked, waiting on Karthik).\n"
            "11. Turn 10 (09:14 AM): Send '1. What work do I still need to do?' and observe the returned structured open_tasks.\n"
            "12. Notice across extended multi-turn conversations that earlier tasks or accumulated task state can be dropped or omitted from subsequent reconciliation queries."
        ),
        "expected_behavior": (
            "The Agent execution engine should reliably track and accumulate task state throughout a multi-turn thread:\n"
            "- Completed tasks should no longer appear as open.\n"
            "- Blocked tasks should remain blocked until explicitly updated.\n"
            "- In-progress tasks should remain in progress.\n"
            "- Newly added tasks should remain available alongside previously created tasks.\n"
            "- Updating one task must not cause unrelated tasks to disappear.\n"
            "- Asking for open/remaining work should return all currently unfinished tasks established throughout the thread."
        ),
        "expected_result": (
            "The Agent should use the complete relevant conversation state and return the latest state of every applicable task across multi-turn conversations without omitting previously established tasks."
        ),
        "business_impact": (
            "Users cannot rely on the Daily Work Coordinator Agent to track complex multi-task workflows or hold persistent operational state across conversations. "
            "Missing or dropped tasks directly undermine the core value proposition of an automated work coordinator, risking missed deadlines, duplicate work, and critical operational oversights."
        ),
        "user_experience": (
            "In multi-turn planning sessions, users see tasks they previously created vanish from subsequent summary or status responses. "
            "Users are forced to re-prompt and re-enter task details, leading to severe frustration and loss of confidence in the Agent's conversational memory and tracking accuracy."
        ),
        "investigation_guidance": (
            "Investigate the Agent execution flow responsible for: conversation history/context → task extraction → existing task reconciliation → state update → structured output generation.\n"
            "- Do not assume an unverified root cause (such as the model, prompt, conversation memory, persistence layer, output parser, or schema handling) until the implementation is inspected.\n"
            "- Inspect how thread conversation history is assembled and injected into the prompt context for multi-turn runs.\n"
            "- Check whether the prompt or model context window truncates earlier assistant structured messages, losing previous task state.\n"
            "- Inspect the task extraction and reconciliation pipeline: verify if there is an explicit state entity/memory store that merges current-turn deltas with previous-turn state, or if the agent relies entirely on raw context re-generation.\n"
            "- Check if the output parser or structured schema generator restricts output array items or drops entities during schema serialization."
        ),
        "fix_requirement": (
            "The Agent execution pipeline must reliably reconcile and preserve cumulative task state across multi-turn threads. "
            "Updating one task or adding a new task must maintain all existing active tasks, and querying for remaining work must return the complete, accurate set of open tasks."
        ),
        "recommended_solution": (
            "1. Implement or repair the state reconciliation layer in the Agent execution pipeline so that each turn extracts task delta events and reconciles them against a persistent session state model (or complete accumulated thread state) before generating structured outputs.\n"
            "2. Ensure conversation history passed to the agent preserves all previous structured output states without lossy truncation.\n"
            "3. Add regression tests validating multi-turn task workflows (creation, status update, blocker addition, completion, query remaining work) to verify that unrelated tasks are never dropped."
        ),
        "minimum_working_fix": (
            "Ensure the Agent's multi-turn prompt instructions or state reconciliation logic explicitly carries over previously established open tasks into subsequent structured response payloads unless they have been explicitly marked as completed or removed."
        ),
        "acceptance_criteria": [
            "In a multi-turn conversation thread, adding a new task does not remove or overwrite previously existing tasks.",
            "Updating the status or blocker information of one task preserves all other tasks unchanged.",
            "Querying for open/remaining work returns all currently active, in-progress, and blocked tasks created across all turns of the thread.",
            "Tasks explicitly marked as completed no longer appear in open task lists.",
            "Structured outputs generated across 5+ consecutive turns maintain 100% task state fidelity."
        ]
    },
    "ART-AGENT-006": {
        "title": "Agent Output Schema Allowed Values Are Not Strictly Enforced for Text Fields",
        "module": "AGENT",
        "severity": "HIGH",
        "priority": 2,
        "environment": "Testing (Daily Work Coordinator V2)",
        "tags": [
            "Agent-Lab",
            "Output-Schema",
            "Output-Validation",
            "Enum-Validation",
            "Allowed-Values",
            "Structured-Output"
        ],
        "problem": (
            "In Daily Work Coordinator V2 (Agent Lab), the Agent Output Schema is configured with Text fields and restricted allowed values for structured properties such as intent, status, and priority. "
            "During testing, when the Agent is prompted to create or update structured items with values outside the configured allowed-value contract (e.g. setting status to STARTED and priority to URGENT), the validation layer does not enforce the restricted allowed-value contract for Text fields. "
            "The Agent execution completes successfully and outputs the invalid text values as a valid structured result (custom_6abb997e92bd477cd1a327b8). "
            "In contrast, primitive type validation is actively enforced: when incompatible types (such as numeric priority or boolean status) are provided, ART detects the type mismatch and halts execution with an error (code: invalid_task_fields). "
            "This demonstrates that while type checking operates, the configured allowed-value restrictions for Text fields are bypassed, allowing schema-violating strings to be treated as successful results and propagated downstream."
        ),
        "observed_behavior": (
            "- Allowed-Value Violation (Passed / Unenforced): Prompting the agent with \"Add a task called Prepare ART demo. Set the status to STARTED and priority to URGENT.\" results in a successful structured response where status is 'started' and priority is 'urgent', despite both values violating the schema's allowed enum values.\n"
            "- Type Incompatibility (Caught / Enforced): Providing incompatible primitive types (e.g. numeric priority or boolean status) causes ART to halt and reject the request with code: invalid_task_fields and message: \"Task priority and status values are invalid.\"\n"
            "- Summary of Discrepancy: Runtime validation verifies that values are strings, but fails to check whether string values belong to the configured allowed-value set defined in the schema contract."
        ),
        "actual_result": (
            "String values outside configured allowed-value sets (e.g. status='started', priority='urgent') are accepted as valid output and returned successfully. "
            "Type validation is enforced for non-string types, but allowed-value / enum restrictions on Text fields are bypassed."
        ),
        "reproduction": (
            "1. In Agent Lab, open Daily Work Coordinator V2 (Agent ID: 6abb98f892bd477cd1a327b3).\n"
            "2. Verify the Agent Output Schema configures Text fields with restricted allowed values for status (e.g. planned, in progress, completed, blocked) and priority (e.g. high, medium, low).\n"
            "3. Open Agent Test and submit a task creation prompt containing values outside the allowed set: \"Add a task called Prepare ART demo. Set the status to STARTED and priority to URGENT.\"\n"
            "4. Open the Agent result modal upon completion.\n"
            "5. Observe that the agent returned a successful structured response (custom_6abb997e92bd477cd1a327b8) with status: 'started' and priority: 'urgent' without validation error or repair.\n"
            "6. In contrast, submit a prompt with incompatible primitive types (e.g. numeric priority or boolean status) and observe that ART rejects the request with code: invalid_task_fields."
        ),
        "repro_steps": (
            "1. In Agent Lab, open Daily Work Coordinator V2 (Agent ID: 6abb98f892bd477cd1a327b3).\n"
            "2. Verify the Agent Output Schema configures Text fields with restricted allowed values for status (e.g. planned, in progress, completed, blocked) and priority (e.g. high, medium, low).\n"
            "3. Open Agent Test and submit a task creation prompt containing values outside the allowed set: \"Add a task called Prepare ART demo. Set the status to STARTED and priority to URGENT.\"\n"
            "4. Open the Agent result modal upon completion.\n"
            "5. Observe that the agent returned a successful structured response (custom_6abb997e92bd477cd1a327b8) with status: 'started' and priority: 'urgent' without validation error or repair.\n"
            "6. In contrast, submit a prompt with incompatible primitive types (e.g. numeric priority or boolean status) and observe that ART rejects the request with code: invalid_task_fields."
        ),
        "expected_behavior": (
            "ART should validate the final Agent output against the complete configured Output Schema before accepting the result:\n"
            "- Text fields with configured allowed values must only accept values within the allowed set.\n"
            "- Text values outside the allowed set must not be accepted as valid output.\n"
            "- Invalid values should either be safely repaired to a contract-valid value or execution should halt with a clear output-validation error.\n"
            "- The validation error must identify the affected field and invalid value.\n"
            "- Invalid structured output must not be exposed as a successful Agent result or propagated downstream."
        ),
        "expected_result": (
            "ART should validate the final Agent output against the complete configured Output Schema before accepting the result, rejecting or repairing text values that violate the configured allowed values set."
        ),
        "business_impact": (
            "Downstream Orchestrator flows, switch conditions, and integrations expecting strict enum values receive unhandled strings, leading to workflow routing failures, silent errors, and data corruption in task persistence."
        ),
        "user_experience": (
            "Builders define explicit allowed values expecting the platform to enforce them, but find that end-user inputs can inject arbitrary values directly into the final agent output. Downstream debugging is frustrating because the upstream Agent reports success despite violating the explicit contract."
        ),
        "investigation_guidance": (
            "Investigate the post-execution Agent output validation pipeline:\n"
            "- Identify where post-model execution output validation takes place (between LLM response parsing and the creation of custom_... structured result).\n"
            "- Check how the Agent Output Schema is compiled into a JSON Schema validator. Determine whether enum or oneOf constraints configured for Text fields in the UI builder are included in the compiled schema or dropped during compilation.\n"
            "- Contrast the implementation of invalid_task_fields (which detects non-string primitive types) with the general schema validation routine. Determine whether allowed-value checks were omitted from the custom field validation logic or if schema validation only checks primitive types.\n"
            "- Check whether an auto-repair or normalization step exists and why unallowed values bypass it without triggering a fallback error."
        ),
        "fix_requirement": (
            "The Agent output validation engine must enforce configured allowed-value (enum) constraints on all Text fields. Any output value not belonging to the allowed-value set must not be accepted as a successful result; it must either be coerced/repaired to a valid allowed value or rejected with an informative output-validation error."
        ),
        "recommended_solution": (
            "1. Ensure the schema generator always populates the enum array for Text fields with configured allowed values.\n"
            "2. Enforce strict JSON Schema validation against the complete compiled schema after agent execution.\n"
            "3. If an output field contains an unallowed string value, return an error payload (e.g., code: invalid_field_allowed_value with details specifying the field, received value, and allowed choices) rather than emitting a successful custom_... response.\n"
            "4. Add unit and integration tests verifying that outputs with unallowed text values are rejected or repaired."
        ),
        "minimum_working_fix": (
            "In the agent output validation routine, add an explicit check for all Text fields with defined allowed values verifying value in field_spec['allowed_values']. If the value is outside the allowed list, emit an invalid_task_fields error response instead of proceeding to emit the successful result payload."
        ),
        "acceptance_criteria": [
            "Text fields configured with allowed values reject any output value outside the allowed set with a clear validation error.",
            "The validation error identifies the invalid field name and the offending value.",
            "Valid enum values within the allowed set continue to be accepted and processed normally.",
            "Incompatible primitive types (e.g. numeric, boolean) continue to be rejected.",
            "Invalid structured outputs are never emitted as successful custom_... results or passed to downstream nodes."
        ]
    },
    "ART-ORCHESTRATOR-004": {
        "title": "Daily Work Coordinator V2 Works Differently When Executed Through Orchestrator Agent Node",
        "module": "ORCHESTRATOR",
        "severity": "HIGH",
        "priority": 2,
        "environment": "Testing (Daily Work Coordinator Orchestrator V2 / Daily Work Coordinator V2)",
        "tags": [
            "Orchestrator",
            "Agent-Node",
            "Input-Mapping",
            "Workflow-Execution",
            "Data-Handoff",
            "ConflictingUpdateOperators"
        ],
        "problem": (
            "In Daily Work Coordinator Orchestrator V2, when the Daily Work Coordinator V2 agent is executed through an Orchestrator Agent node using mapped input (message = ${start.message}), the linked Agent fails to extract or recognize task information from the mapped message string. "
            "While direct execution of Daily Work Coordinator V2 in Agent Test accurately parses task entities from natural language inputs and returns populated structured data, executing the exact same agent through the Orchestrator results in the Agent returning an empty task array (tasks: []) accompanied by a clarification message ('No task information was provided in the message.' or 'No task updates were provided.'). "
            "Furthermore, Orchestrator test executions intermittently fail completely with a workflow execution error: (ConflictingUpdateOperators) Updating the path 'version' would create a conflict at 'version'."
        ),
        "observed_behavior": (
            "- Direct Agent Test (Working): Testing Daily Work Coordinator V2 directly in Agent Lab successfully extracts task name, status, priority, and deadline from natural-language prompts.\n"
            "- Orchestrator Execution (Failing to Extract Tasks): Submitting task creation messages (e.g. \"Add a task called ORCHESTRATOR-MAPPING-TEST-947. Set priority to HIGH and deadline to 6 PM.\" or \"Add a task called Prepare customer presentation.\") in Orchestrator Test results in the Agent node returning empty tasks (tasks: []) and stating no task information was provided.\n"
            "- Workflow Execution Failure: In Thread 6b17226c-aa6e-4a34-a470-856bc7b27aa1, Orchestrator Test halts with error WORKFLOW_EXECUTION_FAILED: (ConflictingUpdateOperators) Updating the path 'version' would create a conflict at 'version' (agent_id: 6ab2063392bd477cd1a3139c, ref_id: 6abce73b73ba24ec923cd225_orch_com_6ab119ae92bd477cd1a312a1_1)."
        ),
        "actual_result": (
            "When Daily Work Coordinator V2 is executed via an Orchestrator Agent node using mapped ${start.message}, it fails to identify task information and returns empty tasks ([]), whereas direct Agent execution successfully extracts tasks from the same input. Furthermore, workflow execution can fail with a ConflictingUpdateOperators error on the 'version' field."
        ),
        "reproduction": (
            "1. Open Daily Work Coordinator Orchestrator V2 in Orchestrator Builder.\n"
            "2. Configure the Start node input schema with required property message of type string (additionalProperties: false).\n"
            "3. Add an Agent node linked to Daily Work Coordinator V2 and configure message mapping: message = ${start.message}.\n"
            "4. Open Orchestrator Test.\n"
            "5. Submit task input message: \"Add a task called ORCHESTRATOR-MAPPING-TEST-947. Set priority to HIGH and deadline to 6 PM.\"\n"
            "6. Click Run and observe the output: Agent returns tasks: [] and response: 'No task information was provided in the message.'\n"
            "7. Submit alternative task input: \"I need to finish the Agent X Play Store screenshots by 4 PM. This is high priority.\"\n"
            "8. Observe identical empty result (tasks: []).\n"
            "9. Notice that certain workflow runs fail completely with WORKFLOW_EXECUTION_FAILED: (ConflictingUpdateOperators) Updating the path 'version' would create a conflict at 'version'."
        ),
        "repro_steps": (
            "1. Open Daily Work Coordinator Orchestrator V2 in Orchestrator Builder.\n"
            "2. Configure the Start node input schema with required property message of type string (additionalProperties: false).\n"
            "3. Add an Agent node linked to Daily Work Coordinator V2 and configure message mapping: message = ${start.message}.\n"
            "4. Open Orchestrator Test.\n"
            "5. Submit task input message: \"Add a task called ORCHESTRATOR-MAPPING-TEST-947. Set priority to HIGH and deadline to 6 PM.\"\n"
            "6. Click Run and observe the output: Agent returns tasks: [] and response: 'No task information was provided in the message.'\n"
            "7. Submit alternative task input: \"I need to finish the Agent X Play Store screenshots by 4 PM. This is high priority.\"\n"
            "8. Observe identical empty result (tasks: []).\n"
            "9. Notice that certain workflow runs fail completely with WORKFLOW_EXECUTION_FAILED: (ConflictingUpdateOperators) Updating the path 'version' would create a conflict at 'version'."
        ),
        "expected_behavior": (
            "- The Orchestrator Agent node must evaluate the ${start.message} mapping and pass the exact runtime string to the linked Agent.\n"
            "- Given equivalent input, the linked Agent's execution behavior, intent classification, and structured task extraction must be identical whether executed directly in Agent Lab or via an Orchestrator Agent node.\n"
            "- If input mapping or handoff fails, ART should surface an explicit mapping error rather than silently invoking the Agent with an empty or unresolved payload.\n"
            "- Workflow execution state persistence must execute cleanly without database update operator conflicts on version."
        ),
        "expected_result": (
            "The Agent node in the Orchestrator should evaluate ${start.message} and pass the input string to the linked Agent runtime. Given equivalent input, the Agent's extraction behavior and structured output must be consistent with direct Agent execution, and the workflow execution engine must not fail with version update conflicts."
        ),
        "business_impact": (
            "Orchestrator workflows cannot reliably delegate task processing to Agent nodes. Workflows fail to extract task information, and execution engine crashes interrupt workflow runs abruptly."
        ),
        "user_experience": (
            "Builders who successfully build and test an Agent in Agent Lab experience unexpected failures when connecting the Agent to an Orchestrator workflow. The UI displays successful runs even though task extraction failed completely."
        ),
        "investigation_guidance": (
            "Investigate the Orchestrator-to-Agent execution and data handoff pipeline:\n"
            "- Expression Evaluation & Handoff: Trace how ${start.message} is resolved during node execution. Verify the actual payload delivered to the linked agent runtime service. Check if the string is passed under the expected parameter name or if an empty string/null is received by the agent prompt.\n"
            "- Agent Identity & Version Resolution: Check which agent definition is loaded by agent_id: 6ab2063392bd477cd1a3139c. Verify whether the Orchestrator Agent node points to the latest configured version of Daily Work Coordinator V2 or a stale/unconfigured draft.\n"
            "- Database Update Operator Conflict: Investigate the persistence routine saving workflow execution state: Error: (ConflictingUpdateOperators) Updating the path 'version' would create a conflict at 'version'. Check the update query for conflicting operators on the 'version' field."
        ),
        "fix_requirement": (
            "The Orchestrator Agent node execution pipeline must correctly resolve input mappings from upstream nodes, provide the complete runtime input to the linked agent, and ensure workflow execution records are persisted without document update conflicts."
        ),
        "recommended_solution": (
            "1. Fix Parameter Mapping: Ensure the Orchestrator runtime expression evaluator properly substitutes ${start.message} with the runtime input string and formats the Agent execution request payload matching the Agent's expected input schema.\n"
            "2. Align Agent Runtime Configuration: Verify that the linked Agent node loads the active, configured Agent graph and system prompts rather than an incomplete stub.\n"
            "3. Resolve Database Update Conflict: Refactor the workflow execution state update query to use a single update operator on the 'version' field."
        ),
        "minimum_working_fix": (
            "Ensure the mapped ${start.message} string is correctly passed to the Agent's prompt execution payload, and remove the redundant or conflicting version operator in the workflow execution update query."
        ),
        "acceptance_criteria": [
            "Mapped input strings (${start.message}) passed to an Agent node in Orchestrator extract task information consistently with direct Agent execution.",
            "When valid task instructions are submitted in Orchestrator Test, the Agent node returns a populated tasks array.",
            "Orchestrator workflow executions complete without ConflictingUpdateOperators errors on the version path.",
            "If mapping resolution fails, an explicit execution/mapping error is raised rather than returning a silent empty extraction."
        ]
    },
    "ART-TOOL-001": {
        "title": "Tool Builder: Added HTTPS Schema Fields Cannot Be Deleted",
        "module": "TOOL",
        "severity": "MEDIUM",
        "priority": 3,
        "environment": "Testing (Tool Builder / HTTPS Tool Configuration)",
        "tags": [
            "Tool-Builder",
            "HTTPS-Tool",
            "Schema-Builder",
            "Schema-Tree",
            "Field-Settings",
            "JSON-Preview",
            "UX-Clarity"
        ],
        "problem": (
            "In Tool Builder, while configuring an HTTPS tool contract via Schema Builder, users can manually add fields to the Schema tree. "
            "However, once a field is added, there is no option or control to delete or remove that field from the schema. "
            "If a field is added accidentally, misnamed, or becomes obsolete during configuration, the schema cannot be modified to prune the unwanted field. "
            "The configuration becomes effectively permanent after a field is created, forcing the user to discard the entire schema draft or recreate the tool configuration from scratch just to eliminate an errant field."
        ),
        "observed_behavior": (
            "- In the Schema Builder modal for HTTPS tools, the interface provides controls to add fields (+ FIELD, + ADD FIELD), import schemas (IMPORT), and configure field properties within the Field settings panel.\n"
            "- After a field is added to the Schema tree, the UI displays no delete button, trash icon, context menu, or keyboard shortcut to remove the field from the schema tree.\n"
            "- The Field settings panel does not expose any 'Delete Field' or 'Remove' action.\n"
            "- The JSON preview reflects the added field, but there is no mechanism to prune or revert added fields prior to clicking SAVE SCHEMA.\n"
            "- The only way to remove an unwanted field is to cancel the modal entirely (CANCEL or X), discarding all other configured fields and starting over."
        ),
        "actual_result": (
            "After adding a field manually to the HTTPS Schema Builder, there is no available option, button, or control to delete or remove that field. The configuration becomes permanent unless the entire modal is cancelled, discarding all entered fields."
        ),
        "reproduction": (
            "1. Navigate to Tool Builder in the ART platform.\n"
            "2. Select or create an HTTPS tool configuration.\n"
            "3. Open the Schema Builder modal (for request payload or response schema).\n"
            "4. Observe the initial 3-panel layout: Schema tree (0 top-level fields), Field settings, and JSON preview.\n"
            "5. Click '+ FIELD' or '+ ADD FIELD' to manually add a new field to the schema tree.\n"
            "6. Attempt to remove or delete the newly created field from the Schema tree or Field settings panel.\n"
            "7. Observe that no delete/remove button, context option, or removal action is available anywhere in the UI."
        ),
        "repro_steps": (
            "1. Navigate to Tool Builder in the ART platform.\n"
            "2. Select or create an HTTPS tool configuration.\n"
            "3. Open the Schema Builder modal (for request payload or response schema).\n"
            "4. Observe the initial 3-panel layout: Schema tree (0 top-level fields), Field settings, and JSON preview.\n"
            "5. Click '+ FIELD' or '+ ADD FIELD' to manually add a new field to the schema tree.\n"
            "6. Attempt to remove or delete the newly created field from the Schema tree or Field settings panel.\n"
            "7. Observe that no delete/remove button, context option, or removal action is available anywhere in the UI."
        ),
        "expected_behavior": (
            "- Every manually added schema field in the Schema Builder (both top-level and nested fields) should provide an accessible and prominent delete/remove action (e.g., a trash can icon in the Schema tree item row and a 'Delete Field' button in the Field settings panel).\n"
            "- Triggering the delete action should immediately remove the selected field (and its children, if an object or array) from the Schema tree and update the JSON preview accordingly.\n"
            "- Unrelated schema fields, types, and configurations must remain untouched.\n"
            "- If all fields are deleted, the Schema Builder should cleanly return to its empty state and display the validation requirement ('Add at least one field before saving.')."
        ),
        "expected_result": (
            "Every manually added schema field in the Schema Builder (both top-level and nested fields) should provide an accessible delete/remove control. Deleting a field should immediately remove it from the schema tree and JSON preview, while preserving all other unrelated fields."
        ),
        "business_impact": (
            "A small configuration mistake cannot be corrected easily, making Tool Builder configuration unnecessarily difficult and error-prone. Users must scrap and recreate entire complex schema configurations to correct a single mistaken field entry."
        ),
        "user_experience": (
            "The builder experiences a 'trap' dynamic where additive operations are supported, but reductive operations are impossible without abandoning all progress. Lack of delete actions violates standard form and schema editor UX conventions, causing confusion and perceived platform fragility."
        ),
        "investigation_guidance": (
            "Investigate the Schema Builder frontend component tree in the Tool Builder module:\n"
            "- Component Hierarchy: Locate the Schema Builder dialog/modal component that renders the three-column layout (Schema tree, Field settings, JSON preview).\n"
            "- Schema Tree Item Renderer: Inspect the list/tree item rendering logic for schema fields. Check whether actions are limited to selection/expansion and why an action menu or delete button is absent.\n"
            "- Field Settings Component: Inspect the Field settings pane. Determine if a removal handler (e.g. onDeleteField(fieldId) or removeFieldAtPath(path)) exists in the schema state reducer/hook but lacks UI wiring.\n"
            "- State Management: Verify how the schema state (AST or JSON Schema object) is maintained. Ensure the deletion handler properly prunes nested keys, cleans up selection state if the deleted field was currently selected, and triggers re-rendering of the JSON preview."
        ),
        "fix_requirement": (
            "The Schema Builder in Tool Builder must provide a delete/remove control for every user-created field (top-level and nested). Removing a field must immediately excise it from the schema tree state and update the JSON preview in real time, while preserving all other fields."
        ),
        "recommended_solution": (
            "1. Tree Item Action: Add a delete icon button (e.g. trash icon) on hover/focus for each item in the Schema tree.\n"
            "2. Field Settings Action: Add a secondary 'Delete Field' button with confirmation or instant undo at the bottom of the Field settings panel for the active field.\n"
            "3. State Pruning Handler: Implement a recursive field deletion handler in the Schema Builder state manager that removes the targeted node by key/ID, removes it from any parent object properties or array item definitions, and adjusts selection state to null or a sibling node.\n"
            "4. Validation Synchronisation: Re-evaluate schema validity upon deletion (e.g. restoring 'Add at least one field before saving' when field count reaches 0)."
        ),
        "minimum_working_fix": (
            "Add a 'Delete Field' button in the Field settings pane that removes the currently selected field from the schema state dictionary and deselects the field, triggering an immediate update of the Schema tree and JSON preview."
        ),
        "acceptance_criteria": [
            "Every user-added field in the Schema Builder displays an accessible delete/remove action in the UI.",
            "Deleting a top-level field removes it from the Schema tree and JSON preview without affecting other fields.",
            "Deleting a nested field removes only that child field and leaves parent and sibling fields intact.",
            "When the active/selected field is deleted, the Field settings pane cleanly resets to the unselected state ('Select a field').",
            "Deleting the last remaining field returns the Schema Builder to the initial empty state and prevents saving."
        ]
    },
    "ART-ORCHESTRATOR-005": {
        "title": "Observability Does Not Display Runtime Input and Output Details for Orchestrator Agent Execution",
        "module": "ORCHESTRATOR",
        "severity": "MEDIUM",
        "priority": 3,
        "environment": "Testing (Daily Work Coordinator Orchestrator V2 / Observability Conversation Explorer)",
        "tags": [
            "Orchestrator",
            "Observability",
            "Trace-Tree",
            "Conversation-Explorer",
            "Agent-Execution",
            "Details-Panel",
            "Runtime-Diagnostics",
            "UX-Clarity"
        ],
        "problem": (
            "In Orchestrator Observability (Conversation Explorer), the Trace Tree records individual workflow execution steps for Agent nodes—such as Completed agentOrchestrator_1, Request received, Preparing the response, Output finalized, and Response ready. "
            "However, when these activities are selected, the Details panel is completely blank and fails to display runtime payloads. "
            "Specifically, selecting Request received does not reveal the input payload passed from the Orchestrator Start node to the Agent. Similarly, selecting output-related trace events (Output finalized, Response ready) provides no output inspection. "
            "The parent activity Completed agentOrchestrator_1 only outputs a generic placeholder string (agentOrchestrator_1 completed in ms). Consequently, builders and testers cannot determine what data actually entered or exited the Agent, disabling workflow diagnostics."
        ),
        "observed_behavior": (
            "- Parent Activity Placeholder: Selecting Completed agentOrchestrator_1 in the Trace Tree displays a Details panel containing only 'agentOrchestrator_1 completed in ms' with no input mapping data, runtime arguments, or return values.\n"
            "- Blank Child Activity Details: Selecting 'INPUT agent Request received' (timestamp 6:05:29 PM) results in a completely blank Details panel below the activity header. Selecting subsequent 'Request received' activities (timestamp 6:06:08 PM) similarly renders an empty Details pane with no request payload. Output stages (Output finalized, Response ready) fail to expose the structured task output or agent response text.\n"
            "- Omission of Runtime Diagnostics: The Trace Tree visualizes step durations (e.g. 2.20s, 2.18s, 3.69s), but payload inspection is unavailable across all sub-steps."
        ),
        "actual_result": (
            "The execution trace and individual stages are recorded, but the Details panel for Agent execution events is blank or contains only generic completion text ('agentOrchestrator_1 completed in ms'). The actual runtime request payload and structured response cannot be inspected."
        ),
        "reproduction": (
            "1. Open an Orchestrator workflow containing an Agent node (e.g. Daily Work Coordinator Orchestrator V2).\n"
            "2. Execute a test run in Orchestrator Test.\n"
            "3. Open Observability and select the execution run from Conversation Explorer (e.g. execution thread bf0644a4...82f2).\n"
            "4. Ensure the Trace Tree tab is active.\n"
            "5. In the Spans & Steps tree, select the parent Agent activity Completed agentOrchestrator_1.\n"
            "6. Inspect the Details panel: observe that it only shows generic text 'agentOrchestrator_1 completed in ms' with zero payload details.\n"
            "7. Select the child activity 'INPUT agent Request received' (or subsequent Request received steps).\n"
            "8. Inspect the Details panel: observe that the panel is completely empty."
        ),
        "repro_steps": (
            "1. Open an Orchestrator workflow containing an Agent node (e.g. Daily Work Coordinator Orchestrator V2).\n"
            "2. Execute a test run in Orchestrator Test.\n"
            "3. Open Observability and select the execution run from Conversation Explorer (e.g. execution thread bf0644a4...82f2).\n"
            "4. Ensure the Trace Tree tab is active.\n"
            "5. In the Spans & Steps tree, select the parent Agent activity Completed agentOrchestrator_1.\n"
            "6. Inspect the Details panel: observe that it only shows generic text 'agentOrchestrator_1 completed in ms' with zero payload details.\n"
            "7. Select the child activity 'INPUT agent Request received' (or subsequent Request received steps).\n"
            "8. Inspect the Details panel: observe that the panel is completely empty."
        ),
        "expected_behavior": (
            "- When an execution activity is selected in the Trace Tree, the Details panel must render meaningful structured runtime data:\n"
            "- Request received: Must display the resolved input payload passed from the Orchestrator to the Agent (e.g., mapped ${start.message} parameter and values).\n"
            "- Output finalized / Response ready: Must display the finalized structured Agent output payload (e.g., intent, extracted tasks, clarification response).\n"
            "- Parent Agent node activity: Should display execution summary metrics, input/output summary, and execution status.\n"
            "- Error/failure states: Must expose the specific failure reason, error codes, and the execution stage where failure occurred.\n"
            "- Sensitive fields should be masked or redacted according to platform privacy rules, without omitting the entire diagnostic payload."
        ),
        "expected_result": (
            "Observability should expose structured runtime data for each execution step in the Details panel: resolved Agent input for 'Request received', finalized structured result for 'Output finalized' / 'Response ready', execution status, duration, and error diagnostics when execution fails. Sensitive values should be masked rather than omitting the complete payload."
        ),
        "business_impact": (
            "Developers and QA engineers cannot use Observability to inspect what payload entered an Agent node, what structured output the Agent emitted, or where data handoff broke. Workflow debugging requires blind trial-and-error testing."
        ),
        "user_experience": (
            "Users click into individual trace activities expecting to inspect payloads, only to be presented with an empty white pane. The UI indicates that steps were executed and recorded, but provides no visibility into why an Agent produced a specific output or failed to parse an input."
        ),
        "investigation_guidance": (
            "Investigate the Orchestrator execution event emission and Observability trace storage pipeline:\n"
            "- Span Event Payload Capture: Inspect where the Orchestrator agent runner emits trace events (Request received, Preparing the response, Output finalized). Check whether runtime input/output arguments are serialized into the event span attributes or dropped prior to emission.\n"
            "- Trace Ingestion & Persistence: Verify whether the Observability ingestion service stores event attributes in the backend trace database or if attributes are stripped for size/performance.\n"
            "- Conversation Explorer Frontend Details Component: Inspect the component rendering the DETAILS tab in Conversation Explorer. Check whether it handles event attribute payloads or if it expects a specific schema/format that the backend is currently not supplying.\n"
            "- Timing String Placeholder Bug: In Completed agentOrchestrator_1, the string 'agentOrchestrator_1 completed in ms' is missing the numeric duration value (e.g. completed in <duration> ms), indicating a template formatting bug in the span result serializer."
        ),
        "fix_requirement": (
            "Observability must capture, persist, and render structured runtime input payloads for Request received events and structured output payloads for Output finalized / Response ready events within the Conversation Explorer Details panel, while formatting execution duration correctly in parent completion summaries."
        ),
        "recommended_solution": (
            "1. Payload Attachment at Bridge: Ensure the Orchestrator-to-Agent execution bridge attaches the resolved request object to the Request received span event.\n"
            "2. Output Attachment: Attach the model's finalized response and structured JSON payload to the Output finalized span event.\n"
            "3. Frontend Details Renderer: Update the Conversation Explorer Details pane to render formatted JSON code blocks for events containing payload attributes.\n"
            "4. Fix Duration Placeholder: Correct the template string in the agent completion handler so that numeric duration is properly interpolated (e.g. completed in 3690 ms).\n"
            "5. Sensitive Data Masking: Integrate existing redaction helpers to mask sensitive properties while preserving payload keys and structure."
        ),
        "minimum_working_fix": (
            "Serialize and attach the raw input dictionary to the Request received span event and the output dictionary to the Output finalized span event, and update the Details panel component to render JSON.stringify(event.payload, null, 2) when a payload exists."
        ),
        "acceptance_criteria": [
            "Selecting Request received in the Trace Tree displays the resolved input payload supplied to the Agent in the Details panel.",
            "Selecting Output finalized or Response ready displays the actual structured Agent output in the Details panel.",
            "Parent completion activity displays properly formatted duration (e.g., completed in <X> ms).",
            "Execution error events display the error code, reason, and failing step.",
            "Sensitive field values are masked without hiding the surrounding diagnostic structure.",
            "The displayed trace data matches the selected execution run."
        ]
    },
    "ART-GOV-004": {
        "title": "Governance Action Creation Fails Even When Required Tool Is Connected to Agent Workflow",
        "module": "GOV",
        "severity": "HIGH",
        "priority": 2,
        "environment": "Testing (Healthcare P2P Exception Agent / Governance Action Registry)",
        "tags": [
            "Governance",
            "Action-Registry",
            "Tool-Action",
            "Tool-Binding",
            "Agent-Workflow",
            "ERPNext-Tool",
            "Policy-Inputs"
        ],
        "problem": (
            "In Agent → Governance → Action Registry, an action cannot be created for a Tool that is already connected and available in the Agent workflow (e.g. Healthcare P2P Exception Agent with erpnext_art__erpnext_get_purchase_invoice). "
            "While creating the action through the New Action wizard, ART correctly detects the selected Tool capability and inherits its required input property ('invoice_name · string · required') in Step 4 (Policy inputs). "
            "However, when the user clicks CREATE ACTION, the platform halts action creation with a blocking validation error: 'action binding not connected to this agent\\'s workflow: tool \\'erpnext_art__erpnext_get_purchase_invoice\\' is not connected to this agent\\'s workflow'. "
            "Because the ERPNext Tool is already connected to the Agent workflow, ART falsely identifies the Tool binding as disconnected, preventing builders from registering governed Tool Actions."
        ),
        "observed_behavior": (
            "- Input Property Inheritance (Working): In the New Action modal under Step 4 of 4 (Policy inputs), ART correctly populates Inherited inputs with 'invoice_name · string · required', demonstrating that the wizard successfully inspected the Tool schema and identified its input contract.\n"
            "- Action Creation Rejection (Failing): Clicking CREATE ACTION triggers an error toast banner at the top of the viewport and an inline alert above Inherited inputs: 'action binding not connected to this agent’s workflow: tool \\'erpnext_art__erpnext_get_purchase_invoice\\' is not connected to this agent’s workflow'. Action registration is aborted, and the modal remains open in an un-saveable state.\n"
            "- UI Contradiction: The Governance wizard simultaneously recognizes the tool's input contract while declaring that the tool is not connected to the agent."
        ),
        "actual_result": (
            "Governance fails to create an Action Registry entry for a connected Tool, reporting that the tool is not connected to the agent's workflow ('action binding not connected to this agent’s workflow: tool \\'erpnext_art__erpnext_get_purchase_invoice\\' is not connected to this agent’s workflow'), despite correctly detecting the tool and inheriting its required inputs in the wizard."
        ),
        "reproduction": (
            "1. Open an Agent configured with an active connected Tool (e.g. Healthcare P2P Exception Agent with ERPNext Tool erpnext_art__erpnext_get_purchase_invoice).\n"
            "2. Navigate to the GOVERNANCE tab and open Action Registry.\n"
            "3. Click New Action to launch the action creation wizard.\n"
            "4. Complete Step 1 (Basics), Step 2 (Capability) by selecting the connected Tool, and Step 3 (Limits).\n"
            "5. In Step 4 of 4 (Policy inputs), verify that 'invoice_name · string · required' is visible under Inherited inputs.\n"
            "6. Click CREATE ACTION.\n"
            "7. Observe that action creation is rejected with error: 'action binding not connected to this agent’s workflow: tool \\'erpnext_art__erpnext_get_purchase_invoice\\' is not connected to this agent’s workflow'."
        ),
        "repro_steps": (
            "1. Open an Agent configured with an active connected Tool (e.g. Healthcare P2P Exception Agent with ERPNext Tool erpnext_art__erpnext_get_purchase_invoice).\n"
            "2. Navigate to the GOVERNANCE tab and open Action Registry.\n"
            "3. Click New Action to launch the action creation wizard.\n"
            "4. Complete Step 1 (Basics), Step 2 (Capability) by selecting the connected Tool, and Step 3 (Limits).\n"
            "5. In Step 4 of 4 (Policy inputs), verify that 'invoice_name · string · required' is visible under Inherited inputs.\n"
            "6. Click CREATE ACTION.\n"
            "7. Observe that action creation is rejected with error: 'action binding not connected to this agent’s workflow: tool \\'erpnext_art__erpnext_get_purchase_invoice\\' is not connected to this agent’s workflow'."
        ),
        "expected_behavior": (
            "- When a Tool is connected to an Agent workflow, Governance Action Registry must validate that Tool as an active capability and successfully create the Action record.\n"
            "- Required inputs defined on the Tool schema must be bound to the Governance Action without false disconnection rejections.\n"
            "- If a Tool is genuinely missing from an Agent's configuration, validation should fail with an actionable description of which specific configuration or binding is missing."
        ),
        "expected_result": (
            "If a Tool is connected and available to an Agent workflow, Governance should recognize the Tool binding as valid and allow the Action Registry entry to be created without false disconnection errors."
        ),
        "business_impact": (
            "Governance cannot be configured for valid Agent Tool actions. This blocks policy enforcement, approval workflows, and human review rules for tools that are already operational in the agent workflow."
        ),
        "user_experience": (
            "Builders experience a confusing contradiction where the UI successfully retrieves and renders the tool's input schema in the form, but then rejects saving on the claim that the tool is not connected. No explanation or resolution path is provided to clarify how to resolve the alleged disconnection."
        ),
        "investigation_guidance": (
            "Inspect the Governance Action Registry creation endpoint and Tool binding validation logic:\n"
            "- Identifier Matching: Compare the tool identifier format in the Agent capability store (e.g. fully qualified erpnext_art__erpnext_get_purchase_invoice vs. provider-prefixed vs. unscoped name) with the identifier passed in the Action creation request payload.\n"
            "- Node vs. Capability Resolution: Check whether Governance action validation checks the Agent's capability list or if it erroneously expects a specific canvas node type (e.g. requiring a literal Tool Connector node in the visual graph when tools may be bound via agent configuration/capabilities).\n"
            "- Workspace/Environment Scoping: Verify whether the validation routine filters tools by workspace ID, agent ID, or environment, and if an ID mismatch causes valid tools to be excluded from the lookup set."
        ),
        "fix_requirement": (
            "The Governance Action creation validation service must accurately resolve connected Agent tools against the Agent's active capability registry, allowing Action Registry entries to be saved for any tool available to the Agent."
        ),
        "recommended_solution": (
            "1. Normalize Tool Identifiers: Ensure the tool identifier format used in Governance matches the canonical identifier stored in the Agent's capability registry.\n"
            "2. Capability-Based Validation: Validate tool bindings against the Agent's configured capabilities rather than relying on strict visual canvas node presence.\n"
            "3. Consistent Scope Check: Ensure workspace and agent scoping during action validation correctly reflects the active agent's runtime environment.\n"
            "4. Actionable Diagnostics: If a tool binding fails validation, log and display both the requested tool identifier and the list of available agent capabilities."
        ),
        "minimum_working_fix": (
            "Update the Governance Action creation backend validator to check tool_id in agent.get_connected_tools(), ensuring consistent string normalization so that erpnext_art__erpnext_get_purchase_invoice resolves successfully."
        ),
        "acceptance_criteria": [
            "A Tool connected and available to an Agent workflow is recognized by Governance as a valid action capability.",
            "An Action Registry entry can be successfully created and saved for the connected Tool.",
            "Required Tool inputs (e.g. invoice_name) continue to be inherited into the action contract.",
            "Action creation does not falsely require a specific canvas node when the tool is already configured in the agent.",
            "Genuinely disconnected tools continue to be rejected with appropriate diagnostic errors.",
            "Unrelated Governance action types (Serverless Functions, Agent actions) remain unaffected."
        ]
    },
    "ART-ORCHESTRATOR-006": {
        "title": "Media Node File Upload does not support PDF/non-image files and provides no clear response",
        "module": "ORCHESTRATOR",
        "severity": "MEDIUM",
        "priority": 3,
        "environment": "Testing (InvoiceFlow Orchestrator / Invoclear Runtime / Media Node)",
        "tags": [
            "Orchestrator",
            "Media-Node",
            "File-Upload",
            "Document-Processing",
            "PDF-Support",
            "Validation-Error",
            "UX-Feedback"
        ],
        "problem": (
            "In the Orchestrator Media Node, the file upload component does not properly handle non-image document formats such as PDF. "
            "When a PDF or other unsupported/non-image file is selected for upload, the file is neither accepted nor processed as expected. "
            "Furthermore, the UI provides no clear validation response, error banner, or explanatory message indicating whether the file format is unsupported, the upload failed, or a validation issue occurred. "
            "This defect prevents workflows intended for document intake (such as InvoiceFlow, configured to accept invoice attachments and pass them to the Invoclear runtime) from reliably receiving standard business documents like PDF invoices, while leaving users with an unresponsive upload control."
        ),
        "observed_behavior": (
            "- Non-Image/PDF Upload Failure: When a PDF or non-image document format is selected in the Media Node file upload control, the file is not accepted or processed into the workflow.\n"
            "- Silent Rejection and Missing Feedback: The UI does not display any validation error, toast banner, or inline message explaining why the file was rejected or which file formats are supported.\n"
            "- Unresponsive Interface: The upload component remains unresponsive following file selection, leaving builders unable to determine whether the issue is caused by format restrictions, upload network failures, or node execution errors.\n"
            "- Workflow Build Context: In the InvoiceFlow Orchestrator deployment (invoiceflowv1), the workflow is explicitly defined to 'accept a message and any invoice attachment supported by the invoicing runtime, pass the message to Invoclear, and return the 50-field structured invoice result', yet non-image invoice formats like PDF cannot be processed through the Media Node."
        ),
        "actual_result": (
            "PDF/non-image files are not accepted by the Media Node, and the user receives no useful response or validation feedback explaining why the upload was rejected or failed. The UI remains unresponsive with no indication of allowed formats."
        ),
        "reproduction": (
            "1. Open an Orchestrator workflow containing a Media Node (e.g. InvoiceFlow at demo.arealtimetech.com/agent-builder/orchestrators/invoiceflow).\n"
            "2. Access the Media Node configuration or test execution file upload interface.\n"
            "3. Select a PDF document (e.g., a standard invoice PDF) or another non-image file format in the file selection dialog.\n"
            "4. Attempt to upload the selected file.\n"
            "5. Observe that the file is not accepted or processed into the node.\n"
            "6. Observe that the UI displays no error, validation message, or indication of supported file types, leaving the upload control unresponsive."
        ),
        "repro_steps": (
            "1. Open an Orchestrator workflow containing a Media Node (e.g. InvoiceFlow at demo.arealtimetech.com/agent-builder/orchestrators/invoiceflow).\n"
            "2. Access the Media Node configuration or test execution file upload interface.\n"
            "3. Select a PDF document (e.g., a standard invoice PDF) or another non-image file format in the file selection dialog.\n"
            "4. Attempt to upload the selected file.\n"
            "5. Observe that the file is not accepted or processed into the node.\n"
            "6. Observe that the UI displays no error, validation message, or indication of supported file types, leaving the upload control unresponsive."
        ),
        "expected_behavior": (
            "- The Media Node should handle file selection deterministically: if document formats including PDF are intended for the workflow, PDF files must upload and process successfully.\n"
            "- If a selected file format is unsupported, the UI must immediately display a clear and visible validation message explaining that the file format is unsupported and listing permitted file types.\n"
            "- The UI must never silently fail or remain unresponsive after a file is selected.\n"
            "- Existing image and media file upload functionality must continue working without regression."
        ),
        "expected_result": (
            "The Media Node should either support configured document formats, including PDF where applicable, or immediately display a clear validation message explaining which file formats are supported. Supported files should upload successfully, while unsupported files should be rejected with an explicit validation response."
        ),
        "business_impact": (
            "Workflows that need document inputs (such as InvoiceFlow passing invoice attachments to Invoclear) cannot reliably use the Media Node. Users cannot determine whether failures are caused by format restrictions, upload errors, or node execution problems."
        ),
        "user_experience": (
            "The file upload control appears broken or frozen when non-image files are chosen. Users receive no guidance regarding which file formats are supported or why their selected document was rejected."
        ),
        "investigation_guidance": (
            "Inspect the Media Node's file-picker restrictions, frontend validation, upload API validation, supported MIME types, and error-response handling:\n"
            "- File Input Restrictions: Inspect the <input type=\"file\"> accept attribute in the Media Node frontend component to verify whether it restricts selection to image MIME types (e.g., image/*) or omits application/pdf / .pdf.\n"
            "- Frontend Validation Logic: Check file selection event handlers for client-side MIME type or extension filtering. Identify unhandled rejection paths that fail silently without setting error state or displaying a user notification.\n"
            "- Upload API Endpoint & Supported MIME Types: Inspect the backend upload route handling Media Node file uploads. Verify whether the server rejects non-image MIME types with 4xx/415 status codes and whether the frontend client swallows or ignores these HTTP errors.\n"
            "- Architectural Intent: Confirm whether the Media Node is architecturally intended to support document formats (such as PDF) for document-processing pipelines or if a separate document ingestion node is planned. If PDF is intended for Media Node, ensure upload and storage handlers accommodate PDF MIME types."
        ),
        "fix_requirement": (
            "The Media Node must handle file selection deterministically. Supported file formats must upload and bind successfully; unsupported formats must be rejected immediately with an explicit, visible validation message indicating that the file type is unsupported and listing allowed formats. If PDF is an intended supported format, the upload and validation pipeline must accept PDF files."
        ),
        "recommended_solution": (
            "1. Frontend Validation & Feedback: Add explicit client-side validation in the Media Node file selection handler. If an unsupported file is chosen, display an immediate inline validation banner or toast.\n"
            "2. File Picker Filtering: Update the accept attribute on the file input element to match intended allowed file formats.\n"
            "3. PDF Ingestion Support: If PDF documents are intended for downstream document workflows (e.g., Invoclear invoice extraction), update the Media Node upload endpoint and validator to permit application/pdf.\n"
            "4. Error Handling: Ensure API error responses (400 Bad Request, 415 Unsupported Media Type, 413 Payload Too Large) are captured and displayed to the user with clear diagnostic messages."
        ),
        "minimum_working_fix": (
            "Display an immediate and visible validation error in the Media Node UI when an unsupported file type is selected, specifying the supported file formats. If PDF is intended to be supported, add application/pdf and .pdf to the allowed formats list and file picker accept filter."
        ),
        "acceptance_criteria": [
            "Supported file formats upload successfully through the Media Node.",
            "PDF files upload and process successfully if PDF is an intended supported format.",
            "Selecting an unsupported file type immediately displays a visible validation message.",
            "The validation message identifies that the file type is unsupported and indicates the allowed formats.",
            "The UI does not silently fail or remain unresponsive after file selection.",
            "Existing image and media file uploads continue working without regression."
        ]
    },
    "ART-ORCHESTRATOR-007": {
        "title": "Orchestrator Test UI does not allow PDF upload while Agent Lab Test UI supports PDF",
        "module": "ORCHESTRATOR",
        "severity": "MEDIUM",
        "priority": 3,
        "environment": "Testing (Agent Lab Test vs Orchestrator Test / File Upload)",
        "tags": [
            "Orchestrator",
            "Agent-Lab",
            "Test-UI",
            "File-Upload",
            "PDF-Support",
            "File-Picker",
            "Consistency",
            "UX-Inconsistency"
        ],
        "problem": (
            "There is inconsistent file-upload support between Agent Lab Test and Orchestrator Test. "
            "In Agent Lab Test, the file picker allows PDF files to be selected and uploaded from a folder. "
            "However, when testing an Orchestrator workflow with file/media input, the same folder containing PDF files appears as 'Folder is Empty' because the Orchestrator Test file picker filters out PDF files. "
            "Both testing interfaces navigate to the same local folder (/Projects/Immospice/tex...v2/data/invoice) containing multiple PDF invoice documents. "
            "Agent Lab Test correctly displays and allows selection of these PDF files, while Orchestrator Test excludes them entirely without any indication or explanation. "
            "This prevents end-to-end testing of document-processing Orchestrator workflows even when the underlying Agent supports PDF input."
        ),
        "observed_behavior": (
            "- Agent Lab Test (Working): The file picker displays PDF files in the /Projects/Immospice/tex...v2/data/invoice folder. Multiple PDF invoice files (EKZ-Rechnung invoices) are visible with file sizes and modification dates. The Custom Files filter is active, and the Open button is available for selection.\n"
            "- Orchestrator Test (Failing): The file picker navigated to the identical folder path displays 'Folder is Empty'. The PDF files present in the folder are completely filtered out by the Orchestrator file picker, making it impossible to select any PDF file.\n"
            "- No Feedback: The Orchestrator Test file picker provides no indication that files exist but are being filtered. The user sees an empty folder with no explanation."
        ),
        "actual_result": (
            "Agent Lab Test file picker shows PDF files and allows selection. "
            "Orchestrator Test file picker filters out PDF files from the same folder, displaying 'Folder is Empty'. "
            "The user cannot test an Orchestrator with a PDF document that is selectable through Agent Lab."
        ),
        "reproduction": (
            "1. Open an Agent that supports PDF/document input in Agent Lab (e.g. Immospice text extraction Agent V2).\n"
            "2. In Agent Lab Test, click the file attachment/upload control.\n"
            "3. Navigate to a folder containing PDF files (e.g. /Projects/Immospice/tex...v2/data/invoice).\n"
            "4. Observe that PDF files (e.g. EKZ-Rechnung invoices) are visible and selectable in the file picker.\n"
            "5. Now open the Orchestrator that connects to the same Agent.\n"
            "6. In Orchestrator Test, click the file attachment/upload control.\n"
            "7. Navigate to the same folder containing the PDF files.\n"
            "8. Observe that the folder displays 'Folder is Empty' — PDF files are filtered out by the Orchestrator file picker."
        ),
        "repro_steps": (
            "1. Open an Agent that supports PDF/document input in Agent Lab (e.g. Immospice text extraction Agent V2).\n"
            "2. In Agent Lab Test, click the file attachment/upload control.\n"
            "3. Navigate to a folder containing PDF files (e.g. /Projects/Immospice/tex...v2/data/invoice).\n"
            "4. Observe that PDF files (e.g. EKZ-Rechnung invoices) are visible and selectable in the file picker.\n"
            "5. Now open the Orchestrator that connects to the same Agent.\n"
            "6. In Orchestrator Test, click the file attachment/upload control.\n"
            "7. Navigate to the same folder containing the PDF files.\n"
            "8. Observe that the folder displays 'Folder is Empty' — PDF files are filtered out by the Orchestrator file picker."
        ),
        "expected_behavior": (
            "- If PDF is a supported input type in Agent Lab, Orchestrator Test should also allow PDF input when the connected workflow/Agent supports document input.\n"
            "- The supported file types should remain consistent across both testing interfaces.\n"
            "- If the Orchestrator file picker restricts file types, a clear message should explain which formats are supported."
        ),
        "expected_result": (
            "If PDF is a supported input type in Agent Lab, Orchestrator Test should also allow PDF input when the connected workflow/Agent supports document input. "
            "The supported file types should remain consistent across both testing interfaces."
        ),
        "business_impact": (
            "Document-processing workflows cannot be tested end-to-end through Orchestrator Test even though the underlying Agent supports the same PDF input. "
            "This blocks validation of invoice extraction, document processing, and similar workflows at the orchestration level."
        ),
        "user_experience": (
            "The behavior is inconsistent and misleading. A PDF works as an Agent input but the Orchestrator file picker makes the same file unavailable without explaining why. "
            "Users see 'Folder is Empty' in a folder they know contains files, creating confusion about whether the folder path is wrong or the system is broken."
        ),
        "investigation_guidance": (
            "Compare the accepted file types and MIME-type configurations used by the Agent Lab Test file picker with the Orchestrator Test file picker:\n"
            "- Accept Attribute: Check whether the Orchestrator Test file input element uses a restrictive accept attribute (e.g. image/*) that excludes application/pdf / .pdf, while Agent Lab Test uses a broader or unrestricted accept value.\n"
            "- Frontend File Filtering: Inspect whether Orchestrator Test applies additional client-side filtering (e.g. extension-based or MIME-based filtering in the file selection handler) that Agent Lab Test does not apply.\n"
            "- Shared Configuration: Determine whether both test interfaces read from a shared accepted-file-types configuration or if they have independent, hardcoded filter lists.\n"
            "- Runtime Propagation: Before enabling PDF selection in Orchestrator Test, verify that the Orchestrator runtime input handler can correctly propagate uploaded PDF files to the connected Agent node."
        ),
        "fix_requirement": (
            "Orchestrator Test must allow supported document formats, including PDF, when those formats are valid for the workflow's input path. "
            "File-type validation must be consistent with the actual runtime capabilities and with Agent Lab Test behavior."
        ),
        "recommended_solution": (
            "1. Align File Picker Filters: Update the Orchestrator Test file picker accept/MIME-type configuration to include application/pdf and .pdf when the workflow supports document input, matching the Agent Lab Test behavior.\n"
            "2. Remove Hardcoded Restriction: Remove or update any hardcoded image-only accept attribute in the Orchestrator Test file upload component.\n"
            "3. Runtime Propagation: Ensure the Orchestrator runtime correctly propagates PDF files to the connected Agent node.\n"
            "4. Shared Configuration: Maintain a shared/common accepted-file-types configuration so that Agent Lab Test and Orchestrator Test remain consistent."
        ),
        "minimum_working_fix": (
            "Enable PDF (application/pdf / .pdf) selection in the Orchestrator Test file picker when PDF is a supported workflow input, and ensure the selected file reaches the downstream Agent correctly."
        ),
        "acceptance_criteria": [
            "PDF files visible in Agent Lab Test are also selectable from Orchestrator Test when the workflow supports document input.",
            ".pdf / application/pdf is not incorrectly filtered from the Orchestrator file picker.",
            "Uploaded PDF reaches the connected Agent through the Orchestrator runtime.",
            "Existing supported image/media uploads continue working without regression.",
            "Unsupported file types remain blocked with a clear validation message.",
            "Agent Lab and Orchestrator Test expose consistent supported-file behavior for equivalent workflows."
        ]
    },
    "ART-ORCHESTRATOR-008": {
        "title": "Orchestrator Test Shows Blank Response After Successful Workflow Execution",
        "module": "ORCHESTRATOR",
        "severity": "HIGH",
        "priority": 2,
        "environment": "Testing (Daily Work Coordinator Orchestrator V2 / Orchestrator Test / Professional Plan / InvestigationLab)",
        "tags": [
            "Orchestrator",
            "Test-UI",
            "Response-Rendering",
            "Blank-Response",
            "Workflow-Output",
            "Agent-Output",
            "UX-Critical",
            "Response-Resolver"
        ],
        "problem": (
            "When testing an Orchestrator workflow, the workflow completes successfully (thread header shows Completed) but the Orchestrator's response in the Test conversation panel is completely blank. "
            "The user input is received and displayed correctly, but the Orchestrator response bubbles contain no text, structured data, or any visible content. "
            "This creates a critical UX contradiction: 'Completed' communicates success while giving the user no usable result. "
            "The Orchestrator Test should always resolve a completed execution into a displayable response. "
            "Workflows such as Start → Agent or Start → Agent → Condition should expose the result of the completed execution path rather than silently returning blank. "
            "An empty assistant bubble must never be rendered for a completed execution."
        ),
        "observed_behavior": (
            "- Execution Status: The Orchestrator Test thread af1821e... is marked Completed, indicating the workflow finished without error.\n"
            "- User Input Displayed Correctly: Two user messages are rendered in the conversation panel as structured schema tables showing additionalProperties, properties, required, and type fields with the user's input text.\n"
            "- Blank Orchestrator Responses: Two Orchestrator response bubbles appear (green icon, timestamp 03:33 PM) but contain no visible content — the response area is completely empty white space.\n"
            "- No Error Indication: There is no error banner, warning toast, or diagnostic message indicating that the response could not be resolved.\n"
            "- Workflow Canvas Context: The workflow consists of Start → Daily Work Coordinator (Agent node, 23 runs, 100%) → Condition Builder (14 runs, 100%). Both nodes show successful execution statistics."
        ),
        "actual_result": (
            "The workflow is marked Completed, but the Orchestrator displays blank response bubbles. "
            "The user input is shown correctly with structured schema rendering, but the Orchestrator's replies contain no visible content. "
            "Two blank response bubbles appear (green Orchestrator icon, 03:33 PM timestamp) with empty white space where the response content should be."
        ),
        "reproduction": (
            "1. Open the Daily Work Coordinator Orchestrator (or any Orchestrator with a Start → Agent → Condition workflow and no explicit Sender/response node).\n"
            "2. Open Orchestrator Test (Draft mode).\n"
            "3. Submit a test input such as 'Add a task called Prepare customer presentation. Set priority to HIGH and deadline to 4 PM.' or 'I need to update one of my tasks.'\n"
            "4. Wait for the workflow to complete — observe the thread header shows Completed.\n"
            "5. Inspect the Orchestrator response bubbles in the Test conversation panel.\n"
            "6. Observe that the Orchestrator response bubbles (green icon, timestamped 03:33 PM) are completely blank with no text, structured data, or any content displayed."
        ),
        "repro_steps": (
            "1. Open the Daily Work Coordinator Orchestrator (or any Orchestrator with a Start → Agent → Condition workflow and no explicit Sender/response node).\n"
            "2. Open Orchestrator Test (Draft mode).\n"
            "3. Submit a test input such as 'Add a task called Prepare customer presentation. Set priority to HIGH and deadline to 4 PM.' or 'I need to update one of my tasks.'\n"
            "4. Wait for the workflow to complete — observe the thread header shows Completed.\n"
            "5. Inspect the Orchestrator response bubbles in the Test conversation panel.\n"
            "6. Observe that the Orchestrator response bubbles (green icon, timestamped 03:33 PM) are completely blank with no text, structured data, or any content displayed."
        ),
        "expected_behavior": (
            "- A successfully completed Orchestrator execution must always provide a visible response or an explicit no-output state.\n"
            "- The Orchestrator Test should resolve the workflow result using a deterministic fallback chain: "
            "1) Explicit workflow response/output, "
            "2) Output of the final successful user-facing node, "
            "3) Latest successful Agent output, "
            "4) Structured workflow result rendered as JSON, "
            "5) Explicit 'No response was produced by this workflow' message.\n"
            "- An empty assistant bubble must never be rendered for a completed execution.\n"
            "- Workflows without a Sender node (e.g. Start → Agent) must still display the Agent's result in Test."
        ),
        "expected_result": (
            "A successfully completed Orchestrator execution always provides a visible response or an explicit no-output state. "
            "Empty assistant bubbles are never rendered for completed executions."
        ),
        "business_impact": (
            "Users cannot determine whether the workflow produced the expected result, making Orchestrator testing unreliable. "
            "A 'Completed' status with a blank response creates the false impression that successful workflows are broken. "
            "Combined with ART-ORCHESTRATOR-005 (Observability not showing runtime input/output), users have zero visibility into what the workflow produced."
        ),
        "user_experience": (
            "The user sees their input rendered correctly but receives blank responses from the Orchestrator, creating confusion about whether the workflow is functioning. "
            "The 'Completed' badge communicates success while providing no evidence of success, undermining user trust in the testing interface. "
            "Users are forced to add Sender nodes solely to make Test usable, which is a workflow design burden that should not exist."
        ),
        "investigation_guidance": (
            "Investigate the Orchestrator Test response rendering pipeline and the workflow output resolution mechanism:\n"
            "- Response Resolution Logic: Inspect how the Orchestrator Test conversation component resolves the displayable response after workflow completion. Check whether it only renders output from explicit Sender/response nodes or if it can resolve output from the final executed node in the workflow graph.\n"
            "- Agent Output Availability: The Agent node (Daily Work Coordinator) executed successfully (23 runs, 100%). Check whether the Agent's structured output is available in the execution context but not being resolved by the Test response renderer.\n"
            "- Condition Node Output: The Condition Builder node also executed successfully. Check whether the output of the selected condition branch is available but not propagated to the Test conversation.\n"
            "- Empty Bubble Rendering: Identify the frontend component that renders the Orchestrator response bubble. Check whether it renders regardless of content availability or if it should have a guard to prevent rendering when no content is resolved.\n"
            "- Relationship to ART-ORCHESTRATOR-005: The blank response in Test and the blank Details panel in Observability may share a common root cause — the execution pipeline may not be storing or propagating node outputs to downstream consumers."
        ),
        "fix_requirement": (
            "The Orchestrator Test must never display a blank response bubble for a completed execution. "
            "The Test conversation renderer must resolve the workflow result through a deterministic fallback chain and always display either the resolved output or an explicit no-output message. "
            "Sender nodes must not be required for Test to display results."
        ),
        "recommended_solution": (
            "1. Orchestrator Response Resolver: Add a deterministic response resolution pipeline that resolves the final displayable result from a completed workflow execution.\n"
            "2. Resolution Priority Chain: Explicit workflow response/output → final successful user-facing node output → latest successful Agent output → structured workflow result rendered as JSON → explicit 'No response was produced' state.\n"
            "3. Structured Output Rendering: When the resolved result is structured JSON, render the human-facing field intelligently or display the full structured object in a formatted code block.\n"
            "4. Never Empty: The Test conversation must never render an empty assistant bubble for a completed execution.\n"
            "5. Sender Independence: The response resolver must not require a Sender node. A workflow consisting of Start → Agent should still display the Agent's result in Test."
        ),
        "minimum_working_fix": (
            "Resolve the latest successful Agent output from the completed workflow execution context and render it in the Orchestrator Test response bubble. "
            "If the output is structured JSON, render it as a formatted code block. "
            "If no output is available, display 'No response was produced by this workflow' instead of an empty bubble."
        ),
        "acceptance_criteria": [
            "A completed Orchestrator workflow execution always displays a visible response or an explicit no-output message in the Test conversation.",
            "The Orchestrator Test response resolver follows a deterministic fallback chain (explicit output → final node output → Agent output → structured result → no-output message).",
            "Empty assistant bubbles are never rendered for completed executions.",
            "Workflows without a Sender node (e.g. Start → Agent) still display the Agent's result in Test.",
            "Structured Agent output (e.g. JSON with needs_clarification, clarification_question) is rendered in a readable format.",
            "Existing workflows with explicit Sender/response nodes continue working without regression."
        ]
    },
    "ART-AGENT-007": {
        "title": "Output Schema Fields Should Be Required by Default",
        "module": "AGENT",
        "severity": "MEDIUM",
        "priority": 2,
        "environment": "Testing (Procurement Exception Agent / Agent Lab / Professional Plan / InvestigationLab)",
        "tags": [
            "Agent-Lab",
            "Output-Schema",
            "Schema-Builder",
            "Required-By-Default",
            "Structured-Output",
            "Contract-Enforcement",
            "UX-Improvement",
            "Governance-Reliability"
        ],
        "problem": (
            "When creating an Agent output schema in Agent Lab / Schema Builder, newly added fields and nested subfields are not marked as Required by default. "
            "Users must manually toggle Required ON for every individual field and nested property. "
            "During testing, outputs were noticeably more complete and structurally consistent after Required was enabled across the schema. "
            "Under the current optional-by-default behavior, the model frequently omits fields from structured outputs, making downstream Orchestrator mappings, "
            "Condition Builder branch logic, and Governance rules unreliable. "
            "For structured Agent outputs, schema-first workflows should default toward strict contracts (Required = ON by default) with explicit opt-out for genuinely optional fields. "
            "Additionally, importing a schema where required is not specified should clearly indicate optional fields rather than silently allowing a loose contract."
        ),
        "observed_behavior": (
            "- Default Optional State: When a new field is added in the Output Schema builder, the Required toggle defaults to OFF (required: false).\n"
            "- Subfield Configuration Overhead: When structured objects or arrays of objects are added, all nested properties also default to Required: false, requiring repetitive manual toggling for every subfield.\n"
            "- Model Field Omission: When fields are left optional, the model omits properties from structured output payloads, causing missing keys in downstream nodes.\n"
            "- Complete Output When Required Is Enforced: In procurement-exception-agent (thread b2fcb32b, @arttest_2 and thread 28f25547, @arttest_1), configuring all properties (including nested facts and array fields) as required produces 100% complete and structurally consistent results without field dropping.\n"
            "- Silent Loose Contract on Import: Importing an external schema lacking an explicit required array silently allows a loose contract without visual indication or confirmation."
        ),
        "actual_result": (
            "When creating an Agent output schema, newly added fields and nested subfields are not marked as Required by default. "
            "Users must manually toggle Required ON for every individual field and nested property. "
            "When fields are left optional, the model frequently omits them from structured responses, causing ambiguous states and evaluation failures in downstream Orchestrators, Condition Builders, and Governance rules."
        ),
        "reproduction": (
            "1. Open Agent Lab and create or edit an Agent workflow (e.g. Procurement Exception Agent).\n"
            "2. Navigate to the Output Schema / Schema Builder section.\n"
            "3. Click 'Add Field' to create a new output schema field (e.g. exception_type, human_review_required, or facts).\n"
            "4. Observe that the newly created field has Required disabled by default.\n"
            "5. Add nested fields inside an object or an array of structured objects (e.g. facts.amount, facts.supplier).\n"
            "6. Observe that all nested subfields also default to Required = OFF, requiring manual activation for every property.\n"
            "7. Import an external JSON schema where the required array is not specified and observe that ART silently imports the loose contract without warning."
        ),
        "repro_steps": (
            "1. Open Agent Lab and create or edit an Agent workflow (e.g. Procurement Exception Agent).\n"
            "2. Navigate to the Output Schema / Schema Builder section.\n"
            "3. Click 'Add Field' to create a new output schema field (e.g. exception_type, human_review_required, or facts).\n"
            "4. Observe that the newly created field has Required disabled by default.\n"
            "5. Add nested fields inside an object or an array of structured objects (e.g. facts.amount, facts.supplier).\n"
            "6. Observe that all nested subfields also default to Required = OFF, requiring manual activation for every property.\n"
            "7. Import an external JSON schema where the required array is not specified and observe that ART silently imports the loose contract without warning."
        ),
        "expected_behavior": (
            "- When a user adds a new output-schema field, Required should be enabled by default (required: true).\n"
            "- The same Required = true default must apply recursively to fields created inside nested objects and arrays of structured objects.\n"
            "- Users must retain the ability to manually toggle Required OFF for genuinely optional fields.\n"
            "- When importing a schema where required is not specified, ART should clearly indicate which fields are optional instead of silently allowing a loose contract.\n"
            "- Downstream Orchestrators, Condition Builders, and Governance rules receive predictable, complete payloads conforming to strict contracts."
        ),
        "expected_result": (
            "When a user adds a new output-schema field or nested subfield, Required is enabled by default. "
            "Users can explicitly toggle Required OFF for optional fields. "
            "Importing schemas without explicit required specifications clearly highlights optional fields."
        ),
        "business_impact": (
            "Governance rules (e.g. human_review_required == true, facts.amount evaluation) and downstream Orchestrator branch conditions become unpredictable when models omit optional fields. "
            "Missing fields produce ambiguous three-state outcomes (true / false / missing) that halt workflows or bypass required reviews. "
            "Manual per-field configuration introduces high cognitive overhead and configuration mistakes that surface as runtime failures in production workflows."
        ),
        "user_experience": (
            "Schema authoring is cumbersome and error-prone because users must remember to toggle Required for every field and nested property. "
            "When importing schemas, authors receive no visual feedback regarding contract strictness, leading to unexpected runtime omissions. "
            "Defaulting to Required = ON establishes a strict contract by default, aligning with enterprise developer expectations while allowing deliberate opt-out when needed."
        ),
        "investigation_guidance": (
            "Investigate the Agent Output Schema Builder UI and schema compilation components:\n"
            "- Schema Builder Field Factory: Inspect the component or state handler that initializes new fields in the Schema Builder (e.g. addField, addNestedProperty, or equivalent field definition factory). Check where default property attributes (type, name, required, description) are initialized.\n"
            "- Nested Schema Handlers: Ensure default required: true is applied consistently across all container types: top-level object properties, nested object properties, and array items of type object.\n"
            "- JSON Schema Compilation: Verify how the Schema Builder state compiles into the final JSON Schema required array (properties vs required: [...]). Ensure setting required: true properly adds the field name into the parent object's required list.\n"
            "- Schema Import Parser: Inspect the schema import handler. Identify where imported JSON Schemas are converted into builder state, and verify how missing required arrays are surfaced to the user.\n"
            "- Regression Protection: Ensure existing schemas with explicitly optional fields (required: false) are preserved and not mutated upon loading or editing."
        ),
        "fix_requirement": (
            "The Agent Output Schema Builder must initialize all newly created fields and nested subfields with Required enabled by default. "
            "Users must remain able to toggle Required off. The schema import mechanism must clearly surface optional fields when required is not specified. "
            "Existing saved schemas must retain their configured required/optional settings without modification."
        ),
        "recommended_solution": (
            "1. Default Required = True for New Fields: In the Schema Builder field factory, set the default required flag to true for all newly created fields.\n"
            "2. Recursive Application: Ensure that adding subfields to nested objects or structured array items also defaults required to true.\n"
            "3. Opt-Out Control: Maintain the existing UI toggle allowing authors to switch Required from ON to OFF for fields intended to be optional.\n"
            "4. Schema Import Inspection: In the schema importer, detect when an object schema does not define a required list or defines optional fields. Display an informational notice/badge indicating optional fields, with a quick action to 'Mark All as Required' or 'Keep As Optional'.\n"
            "5. Preserve Existing Saved Schemas: Ensure schema serialization and deserialization does not alter existing agent schemas that have optional fields already configured."
        ),
        "minimum_working_fix": (
            "In the Schema Builder's field creation action handler, change the default state of required from false to true for newly instantiated fields and nested object properties. "
            "Ensure the UI toggle reflects this checked state and includes the field in the parent object's required array upon generation."
        ),
        "acceptance_criteria": [
            "Newly added top-level output schema fields have Required enabled by default.",
            "Newly added fields inside nested objects and structured array items have Required enabled by default.",
            "Users can manually toggle Required OFF for any field or subfield without restriction.",
            "Saving an Agent output schema with default settings generates a JSON Schema containing all created properties in the required array.",
            "Importing a schema without specified required properties clearly identifies optional fields in the UI.",
            "Existing Agent output schemas with optional fields remain unchanged upon loading and editing."
        ]
    },
    "ART-GOV-005": {
        "title": "Policy Inputs Dropdown Cannot Scroll Through Available Facts",
        "module": "GOV",
        "severity": "HIGH",
        "priority": 2,
        "environment": "Testing (Procurement Exception Agent / Governance / Action Registry / Professional Plan / InvestigationLab)",
        "tags": [
            "Governance",
            "Action-Registry",
            "Policy-Inputs",
            "Dropdown-Scroll",
            "Modal-Clipping",
            "Schema-Facts",
            "UI-Blocking",
            "P2"
        ],
        "problem": (
            "In Governance → Action Registry, while configuring a new action in Step 4 — Policy Inputs, the Required facts and Optional facts dropdown selectors "
            "do not allow the user to scroll through all available fact options. "
            "When expanded, the dropdown menu renders initial schema properties but is visually clipped by the bottom boundary of the modal dialog and does not scroll vertically. "
            "Because facts outside the visible portion cannot be reached or selected, workflow authors are blocked from selecting necessary policy inputs for actions governed by policy rules."
        ),
        "observed_behavior": (
            "- Dropdown List Rendered but Cut Off: When clicking 'Select required facts' in Step 4 of the New Action modal, the dropdown options list expands downwards.\n"
            "- Visual Clipping: The options container extends past the bottom boundary of the modal (New Action) and is visually truncated at properties / can_proceed / type.\n"
            "- No Scroll Functionality: Attempting to scroll using the mouse wheel, trackpad, or scrollbar does not scroll the list content; options beyond the initial five items remain inaccessible.\n"
            "- Modal Step Context: The issue occurs in Step 4 of 4: Policy inputs after completing Action basics (Step 1), Action capability (Step 2), and Execution limits (Step 3).\n"
            "- Selection Blocking: Since required facts outside the visible area cannot be selected, the user cannot complete action creation with the desired policy input bindings."
        ),
        "actual_result": (
            "In Governance → Action Registry, the Required facts / Optional facts dropdown in Step 4 — Policy Inputs opens and displays initial schema paths, "
            "but the options list is visually clipped by the modal boundary and does not allow vertical scrolling. "
            "Fields outside the initial visible area cannot be reached or selected, blocking the user from selecting necessary policy inputs."
        ),
        "reproduction": (
            "1. Open an Agent (e.g. Procurement Exception Agent).\n"
            "2. Go to Governance → Action Registry.\n"
            "3. Click + Create action (or Create Action).\n"
            "4. In Step 1 (Action basics), provide an action name, set status to ACTIVE, and click Continue.\n"
            "5. In Step 2 (Action capability), select a capability type (e.g. Custom) and click Continue.\n"
            "6. In Step 3 (Execution limits), set execution timeout and click Continue.\n"
            "7. In Step 4 (Policy inputs), click the Required facts (or Optional facts) dropdown input.\n"
            "8. Attempt to scroll through the list of available output-schema facts.\n"
            "9. Observe that the dropdown list cannot be scrolled and options beyond the initial visible list are cut off and inaccessible."
        ),
        "repro_steps": (
            "1. Open an Agent (e.g. Procurement Exception Agent).\n"
            "2. Go to Governance → Action Registry.\n"
            "3. Click + Create action (or Create Action).\n"
            "4. In Step 1 (Action basics), provide an action name, set status to ACTIVE, and click Continue.\n"
            "5. In Step 2 (Action capability), select a capability type (e.g. Custom) and click Continue.\n"
            "6. In Step 3 (Execution limits), set execution timeout and click Continue.\n"
            "7. In Step 4 (Policy inputs), click the Required facts (or Optional facts) dropdown input.\n"
            "8. Attempt to scroll through the list of available output-schema facts.\n"
            "9. Observe that the dropdown list cannot be scrolled and options beyond the initial visible list are cut off and inaccessible."
        ),
        "expected_behavior": (
            "- The Required facts and Optional facts dropdowns must have a bounded visible height with functional vertical scrolling.\n"
            "- Users must be able to scroll through and select every available policy-input field, regardless of schema size or depth.\n"
            "- Mouse wheel, trackpad, and keyboard arrow keys should smoothly navigate through all available options.\n"
            "- Long schema paths (e.g. deeply nested objects) should remain readable within the dropdown items.\n"
            "- Selecting an item must not unexpectedly dismiss or reset the modal dialog."
        ),
        "expected_result": (
            "The Policy Inputs dropdown panel has a bounded visible height with functional vertical scrolling so every available schema field can be viewed and selected. "
            "Keyboard navigation and search operate reliably, and selections do not dismiss or reset the modal."
        ),
        "business_impact": (
            "Users configuring governed actions for Agents with structured or multi-field output schemas cannot select required policy inputs located beyond the visible dropdown area. "
            "This completely blocks Action Registry configuration and halts downstream testing and execution of Policy Rules, human review triggers, and governed actions."
        ),
        "user_experience": (
            "The user sees a dropdown that opens but is visibly clipped at the modal border, giving the impression that the UI is frozen or broken. "
            "Scrolling attempts fail silently with no visual feedback. "
            "Completing steps 1 through 3 is wasted because step 4 cannot be completed."
        ),
        "investigation_guidance": (
            "Inspect the Policy Inputs dropdown/popover component and its scroll/overflow container hierarchy:\n"
            "- Max-Height and Overflow: Check if the dropdown menu container (e.g. ul or div holding options) has max-height set without overflow-y: auto, or if overflow: hidden on a parent modal wrapper (New Action dialog) is clipping the popover.\n"
            "- Portal Rendering: Determine whether the dropdown is rendered inside the modal DOM hierarchy or via a React portal attached to document.body. If inside the modal, check overflow on modal body containers.\n"
            "- Wheel Event Trapping: Check if wheel/touch scroll event listeners on the modal backdrop or content container prevent the dropdown from receiving native scroll events.\n"
            "- Keyboard Accessibility: Verify whether KeyDown events (ArrowDown / ArrowUp) change the highlighted option and trigger scrollIntoView().\n"
            "- Search Filtering: Investigate adding a filter/search input inside the dropdown to allow quick typing for large schema lists."
        ),
        "fix_requirement": (
            "The Required facts and Optional facts selectors in the Action Registry Policy Inputs step must support full vertical scrolling of all available schema options with bounded height. "
            "All options must be reachable and selectable via mouse, trackpad, and keyboard navigation."
        ),
        "recommended_solution": (
            "1. Bounded Dropdown Height & Auto Scroll: Apply explicit max-height: 240px (or max-h-60) and overflow-y: auto to the options container.\n"
            "2. Prevent Modal Clipping: If the dropdown is rendered inline, either render it via a portal to break out of the modal overflow boundary or adjust parent modal container padding/overflow.\n"
            "3. Keyboard Navigation Support: Enable arrow key navigation with automatic scroll-into-view for focused options.\n"
            "4. Searchable Selection: Add search/filter input at the top of the dropdown list for schemas with many fields.\n"
            "5. Consistency: Ensure both Required facts and Optional facts selectors utilize the same fixed component behavior."
        ),
        "minimum_working_fix": (
            "Add max-height: 250px; overflow-y: auto; to the CSS / style definition of the dropdown menu list container in the Policy Inputs step, "
            "ensuring the container permits scrolling and does not overflow outside the modal viewport without scrollbars."
        ),
        "acceptance_criteria": [
            "The Policy Inputs Required facts dropdown has a bounded visible height and displays a working vertical scrollbar when options exceed the container height.",
            "Users can scroll to and select the last available schema property in the list using mouse wheel, trackpad, and scrollbar.",
            "Keyboard navigation (ArrowDown / ArrowUp) scrolls through all options and allows selection with Enter.",
            "The Optional facts dropdown behaves identically with working vertical scrolling.",
            "Long and nested schema property paths remain readable and properly formatted.",
            "Short schemas with few properties continue to render correctly without unnecessary empty scroll space."
        ]
    },
    "ART-AGENT-008": {
        "title": "Output Parser Intermittently Fails Valid Agent Structured Responses with Trailing Characters",
        "module": "AGENT",
        "severity": "HIGH",
        "priority": 1,
        "environment": "Testing (Procurement Exception Agent / Agent Test Draft / Professional Plan / InvestigationLab)",
        "tags": [
            "Agent-Lab",
            "Output-Parser",
            "Structured-Output",
            "OutputParseError",
            "JSON-Validation",
            "Pydantic-Error",
            "Flaky-Execution",
            "P1"
        ],
        "problem": (
            "The Agent Output Parser intermittently fails valid structured responses emitted by the model when the completion text contains extraneous trailing characters "
            "(such as an extra closing brace at the end of the JSON string). Instead of isolating or extracting the root valid JSON object, the parser passes the raw "
            "unnormalized string directly to Pydantic/JSON validation. When Pydantic encounters trailing characters after the closing bracket, it raises a json_invalid error. "
            "The system performs 4 repetitive retry attempts without repairing or isolating the candidate JSON, and ultimately crashes, dumping a raw Python OutputParseError "
            "with full Pydantic exception details directly into the user-facing chat conversation bubble."
        ),
        "observed_behavior": (
            "- Parsing Crash on Trailing Characters: During an evaluation in Agent Test (Draft mode, thread ba53441e...) for a ₹7,50,000 procurement exception request, execution failed with an unhandled exception.\n"
            "- Complete Payload Emitted by Model: The model generated a complete and valid structured response containing all required properties.\n"
            "- Trailing Characters Error: The candidate string contained an extra trailing brace at line 1 column 1082, causing Pydantic to fail with: Invalid JSON: trailing characters at line 1 column 1082 [type=json_invalid].\n"
            "- Unproductive Retries: The parser repeated the operation 4 times (attempts=4) without stripping trailing characters or isolating the JSON boundary.\n"
            "- Raw Exception Dumped in UI: The full raw exception was rendered verbatim in red inside the assistant message bubble: OutputParseError(raw_text='...', error='1 validation error... Invalid JSON: trailing characters... attempts=4).\n"
            "- Intermittent Success on Re-run: Re-running the identical user input subsequently returned a valid structured Agent result without error when trailing characters were absent."
        ),
        "actual_result": (
            "The Agent Output Parser intermittently fails valid structured outputs when the candidate JSON text contains trailing characters "
            "(such as an extra closing brace at line 1 column 1082). The parser retries 4 times without isolating or repairing the root JSON payload, "
            "and ultimately renders an unhandled raw OutputParseError with full Pydantic exception details directly into the user-facing chat bubble."
        ),
        "reproduction": (
            "1. Open Agent Lab and open the Procurement Exception Agent (or any Agent configured with structured output).\n"
            "2. Open Agent Test in Draft mode.\n"
            "3. Submit a complex evaluation prompt (e.g. Purchase request for ₹7,50,000 from Apex Network Solutions (non-preferred supplier). User states all procurement approvals are available).\n"
            "4. Observe that the model produces structured JSON with an extra trailing brace or trailing whitespace/character.\n"
            "5. Observe that the parser retries 4 times and halts with OutputParseError (json_invalid: Invalid JSON: trailing characters at line 1 column 1082, attempts=4).\n"
            "6. Observe that the raw Python traceback, Pydantic discriminator information, and Pydantic doc URL are displayed in the chat message bubble.\n"
            "7. Re-run the identical input; observe that execution succeeds when no trailing character is emitted."
        ),
        "repro_steps": (
            "1. Open Agent Lab and open the Procurement Exception Agent (or any Agent configured with structured output).\n"
            "2. Open Agent Test in Draft mode.\n"
            "3. Submit a complex evaluation prompt (e.g. Purchase request for ₹7,50,000 from Apex Network Solutions (non-preferred supplier). User states all procurement approvals are available).\n"
            "4. Observe that the model produces structured JSON with an extra trailing brace or trailing whitespace/character.\n"
            "5. Observe that the parser retries 4 times and halts with OutputParseError (json_invalid: Invalid JSON: trailing characters at line 1 column 1082, attempts=4).\n"
            "6. Observe that the raw Python traceback, Pydantic discriminator information, and Pydantic doc URL are displayed in the chat message bubble.\n"
            "7. Re-run the identical input; observe that execution succeeds when no trailing character is emitted."
        ),
        "expected_behavior": (
            "- The Output Parser must normalize and isolate the candidate JSON payload before schema validation, ignoring trailing characters outside the root JSON object.\n"
            "- Valid structured responses must not intermittently fail due to superficial wrapper or trailing characters.\n"
            "- Repair attempts should be bounded, deterministic, and observable.\n"
            "- If parsing genuinely fails after bounded repair, a controlled user-facing error message must be displayed instead of raw internal Python exceptions.\n"
            "- Malformed outputs must never reach downstream execution, and complete diagnostic details must be preserved in Observability traces."
        ),
        "expected_result": (
            "Valid structured outputs are successfully parsed and validated even when trailing characters are present in the raw model completion. "
            "Internal Pydantic/Python exceptions are never leaked to the conversation UI."
        ),
        "business_impact": (
            "Valid business workflows fail intermittently due to benign trailing characters in LLM responses. "
            "End users and testers are exposed to raw Python and Pydantic exception traces in the conversation UI. "
            "Repeated blind retry attempts (attempts=4) cause unnecessary latency and token consumption without resolving the parsing error."
        ),
        "user_experience": (
            "The user is presented with a large red error bubble filled with code, escaped JSON, and Pydantic documentation URLs rather than a clean response. "
            "Re-running the same query works, creating confusion about whether the issue was in their input prompt, the agent configuration, or the platform."
        ),
        "investigation_guidance": (
            "Inspect the Agent Output Parser and response validation pipeline:\n"
            "- Candidate JSON Extraction: Inspect the parsing routine that processes raw LLM completion text before schema validation. Check whether it uses naive json.loads(text) or a boundary-aware extractor like json.JSONDecoder().raw_decode(text.lstrip()).\n"
            "- Pydantic Validation Layer: Locate the AgentOutput[Annotated[Union[AgentErrorResponse, custom_...]]] model and examine how attempts=4 is executed. Verify whether retry logic applies any sanitization between attempts.\n"
            "- Error Formatting Handler: Inspect the frontend and backend error serialization that formats parser exceptions for the conversation stream. Ensure internal exceptions are mapped to clean error responses."
        ),
        "fix_requirement": (
            "The Output Parser must extract and validate only the candidate JSON object from model completions, safely discarding extraneous trailing characters. "
            "Repair attempts must be bounded and unrecoverable errors must be surfaced cleanly in the UI while preserving trace logs."
        ),
        "recommended_solution": (
            "1. Boundary-Aware JSON Parsing: Use json.JSONDecoder().raw_decode() to parse only the valid JSON object from the start of the string, ignoring trailing characters.\n"
            "2. Pre-Validation Normalization: Strip markdown code fences, leading/trailing whitespace, and trailing brackets before validating against the Pydantic schema.\n"
            "3. Controlled Error Response: Replace the raw OutputParseError dump with a standardized AgentErrorResponse in the UI.\n"
            "4. Preserve Observability Diagnostics: Log the raw completion, error code, and attempts to the Observability trace store."
        ),
        "minimum_working_fix": (
            "In the Output Parser, replace json.loads(raw_text) with json.JSONDecoder().raw_decode(raw_text.strip())[0] "
            "to extract the primary JSON object while discarding trailing characters before passing the dictionary to Pydantic validation."
        ),
        "acceptance_criteria": [
            "Valid structured responses do not fail validation when extraneous trailing characters or braces follow the JSON object.",
            "The primary JSON object is isolated and validated against the output schema.",
            "Repair attempts are bounded and logged in execution traces.",
            "Raw internal Python/Pydantic validation errors (OutputParseError, https://errors.pydantic.dev) are never rendered in the chat bubble.",
            "Identical requests execute deterministically without intermittent parser crashes."
        ]
    },
    "ART-GOV-006": {
        "title": "Fact Library Runtime Usage is Non-Deterministic and Cannot Be Verified",
        "module": "GOV",
        "severity": "HIGH",
        "priority": 1,
        "environment": "Testing (Procurement Exception Agent / Governance / Fact Library / Professional Plan / InvestigationLab)",
        "tags": [
            "Governance",
            "Fact-Library",
            "Runtime-State",
            "Non-Deterministic",
            "Cache-Invalidation",
            "Observability",
            "Auditability",
            "P1"
        ],
        "problem": (
            "In Governance → Fact Library, an active Fact value does not produce deterministic runtime behavior across activation/deactivation cycles, "
            "and ART provides no visible evidence showing whether the fact was loaded or consumed during Agent execution. "
            "During testing with SENIOR_PROCUREMENT_REVIEW_THRESHOLD = 500000, an initial request for ₹7,50,000 returned APPROVAL_REQUIRED. "
            "When the fact was toggled to INACTIVE, the same scenario returned NO_EXCEPTION. "
            "When the fact was toggled back to ACTIVE, the same scenario unexpectedly continued returning NO_EXCEPTION. "
            "Because ART lacks runtime provenance and observability into fact resolution, users cannot verify whether a business fact was loaded, stale, "
            "cached, or never consumed by an active rule, creating an unpredictable governance execution environment."
        ),
        "observed_behavior": (
            "- Non-Deterministic Runtime Effect: With SENIOR_PROCUREMENT_REVIEW_THRESHOLD set to 500000, evaluation initially resulted in APPROVAL_REQUIRED. "
            "After toggling to INACTIVE, the identical request returned NO_EXCEPTION. After toggling back to ACTIVE, the request still returned NO_EXCEPTION.\n"
            "- Zero Runtime Observability: Neither Agent Test nor Observability traces display whether SENIOR_PROCUREMENT_REVIEW_THRESHOLD was loaded into the execution context, which version was evaluated, or which policy rule consumed it.\n"
            "- Ambiguous Policy Binding: The UI does not indicate whether a Fact Library entry requires an explicit Policy Rule or Action binding to influence model behavior.\n"
            "- UI State vs. Runtime Desynchronization: Toggling fact status in the Fact Library (ACTIVE vs INACTIVE) does not reliably propagate to the agent's active execution snapshot."
        ),
        "actual_result": (
            "Active Fact Library values produce non-deterministic runtime outcomes across activation/deactivation cycles. "
            "With SENIOR_PROCUREMENT_REVIEW_THRESHOLD set to 500000, a ₹7,50,000 purchase request initially evaluated as APPROVAL_REQUIRED. "
            "After setting the fact to INACTIVE, the scenario returned NO_EXCEPTION. "
            "After toggling the fact back to ACTIVE, the scenario unexpectedly continued returning NO_EXCEPTION, with zero telemetry in Observability."
        ),
        "reproduction": (
            "1. Open an Agent with Governance enabled (e.g. Procurement Exception Agent).\n"
            "2. Go to Governance → Fact Library.\n"
            "3. Create or edit a fact: name 'Senior Procurement Review Threshold', key 'SENIOR_PROCUREMENT_REVIEW_THRESHOLD', type 'Number', default value 500000, status ACTIVE.\n"
            "4. In Agent Test, submit an evaluation request exceeding the threshold (e.g. purchase request for ₹7,50,000) and observe APPROVAL_REQUIRED.\n"
            "5. Return to Fact Library, toggle fact status to INACTIVE, and save.\n"
            "6. Re-run identical request in Agent Test; observe NO_EXCEPTION.\n"
            "7. Return to Fact Library, toggle fact status back to ACTIVE, and save.\n"
            "8. Re-run identical request in Agent Test.\n"
            "9. Observe that execution continues returning NO_EXCEPTION, failing to honor the reactivated fact."
        ),
        "repro_steps": (
            "1. Open an Agent with Governance enabled (e.g. Procurement Exception Agent).\n"
            "2. Go to Governance → Fact Library.\n"
            "3. Create or edit a fact: name 'Senior Procurement Review Threshold', key 'SENIOR_PROCUREMENT_REVIEW_THRESHOLD', type 'Number', default value 500000, status ACTIVE.\n"
            "4. In Agent Test, submit an evaluation request exceeding the threshold (e.g. purchase request for ₹7,50,000) and observe APPROVAL_REQUIRED.\n"
            "5. Return to Fact Library, toggle fact status to INACTIVE, and save.\n"
            "6. Re-run identical request in Agent Test; observe NO_EXCEPTION.\n"
            "7. Return to Fact Library, toggle fact status back to ACTIVE, and save.\n"
            "8. Re-run identical request in Agent Test.\n"
            "9. Observe that execution continues returning NO_EXCEPTION, failing to honor the reactivated fact."
        ),
        "expected_behavior": (
            "- Fact activation state and runtime availability must be deterministic across executions.\n"
            "- When an active fact is configured, ART must consistently expose its resolved value to the governance runtime context.\n"
            "- Toggling a fact between ACTIVE and INACTIVE must predictably invalidate cached runtime snapshots and update subsequent runs.\n"
            "- If a fact requires an associated Policy Rule or Action to participate in decisions, ART should make that dependency explicit in the UI.\n"
            "- Observability traces must identify which facts were loaded, their source version, and whether they were evaluated."
        ),
        "expected_result": (
            "Fact activation state and runtime availability are deterministic across executions. "
            "Observability traces clearly display loaded facts, resolved values, versions, and consumption details."
        ),
        "business_impact": (
            "Enterprise organizations cannot verify whether financial limits, compliance rules, or vendor thresholds defined in the Fact Library are enforced at runtime. "
            "Non-deterministic execution undermines auditability, compliance guarantees, and confidence in the Governance layer. "
            "Without runtime telemetry, developers cannot diagnose whether policy anomalies stem from prompt variations, missing rules, or stale cached fact state."
        ),
        "user_experience": (
            "Toggling a fact from Active to Inactive and back to Active produces inconsistent behavior, making the Governance settings feel unresponsive and broken. "
            "No visibility into runtime fact resolution leaves users guessing about how Fact Library entries interact with agent decisions."
        ),
        "investigation_guidance": (
            "Trace the complete lifecycle of Fact Library entries from definition to runtime execution:\n"
            "- Persistence & Versioning: Check how facts are stored in the database and whether updates bump an entity version or revision hash.\n"
            "- Cache Invalidation: Inspect whether active agent workflows cache runtime snapshots or governance configuration. Verify if saving a fact triggers cache invalidation.\n"
            "- Context Injection Pipeline: Trace where Fact Library entries are compiled into the LLM system prompt or governance evaluation context.\n"
            "- Policy Rule Dependency: Determine whether facts are directly injected into prompt context or if they are only evaluated when referenced by an active Policy Rule or Action condition.\n"
            "- Observability Telemetry: Check what execution metadata is emitted to the trace store; verify if loaded facts and resolved values are logged."
        ),
        "fix_requirement": (
            "Ensure Fact Library state transitions (ACTIVE / INACTIVE) deterministically update the execution runtime snapshot, "
            "and expose runtime provenance in Observability to identify loaded and consumed facts."
        ),
        "recommended_solution": (
            "1. Deterministic Snapshot Invalidation: Invalidate and recompile the runtime configuration snapshot whenever Fact Library definitions or activation states are updated.\n"
            "2. Context Injection Pipeline: Ensure active facts are deterministically loaded into the agent/governance execution context on every invocation.\n"
            "3. Runtime Fact Provenance in Observability: Record detailed telemetry for each execution: list of loaded facts, resolved values, version/hash, source, and whether consumed by any policy rule or condition.\n"
            "4. UI Consumer Relationship Indicator: In the Fact Library, display badges or tooltips showing where a fact is consumed."
        ),
        "minimum_working_fix": (
            "Ensure that saving an update to a Fact Library entry immediately invalidates the agent's cached runtime configuration, "
            "and include a governance_facts array in the execution trace recording loaded fact keys and resolved values."
        ),
        "acceptance_criteria": [
            "Repeated execution against the same published configuration produces consistent fact availability.",
            "Toggling a fact between ACTIVE and INACTIVE is deterministically reflected in subsequent test executions.",
            "Observability traces identify the fact key, resolved value, version/source, and whether it was loaded and consumed.",
            "The UI clearly indicates when a Fact requires an associated Policy Rule or consumer before it can affect decisions.",
            "Identical inputs against identical published configurations execute deterministically without stale fact state."
        ]
    },
    "ART-GOV-007": {
        "title": "Human Review Execution Fails After Agent Identifies Review Requirement",
        "module": "GOV",
        "severity": "HIGH",
        "priority": 1,
        "environment": "Testing (Procurement Exception Agent / Governance / Human Review / Professional Plan / InvestigationLab)",
        "tags": [
            "Governance",
            "Human-Review",
            "Human-in-the-Loop",
            "HIL-Execution",
            "Participant-Resolution",
            "Approval-Request",
            "Policy-Rule-Dependency",
            "P1"
        ],
        "problem": (
            "In Governance → Human Review, an active Human-in-the-Loop (HIL) approval configuration exists for high-risk procurement exceptions with a specific user configured as approver. "
            "When an Agent processes a high-risk procurement request and correctly determines that human review is required, the Agent Test execution fails with the generic error: 'The agent could not complete this request.' "
            "Instead of initiating the configured Human Review, creating a pending approval request for the designated participant, and pausing or routing execution, the runtime terminates abruptly. "
            "No approval notification is generated, no review modal/banner appears, and the Human Review configuration card continues to display 'Not used yet', with zero diagnostic feedback explaining why the review could not be invoked."
        ),
        "observed_behavior": (
            "- Correct Agent Output: The Agent generates a structured result containing exception_type: 'NON_PREFERRED_SUPPLIER', human_review_required: true, risk_assessment: 'High risk...', and recommended_next_action: 'Escalate for human review...' (verified in Observability trace 9833e3e1).\n"
            "- Immediate Execution Failure: Agent Test (thread fbf28fac...) halts with the error banner 'The agent could not complete this request.'\n"
            "- No Approval Created: No approval request or Human Review execution is created for the configured USER participant (chiranjeevi.pk@bixbytessolutions.com).\n"
            "- Summary Card Unused: The Human Review configuration card displays 'Not used yet'.\n"
            "- Masked Diagnostics: Zero diagnostics, error codes, or trace logs explain whether participant resolution failed or an explicit Policy Rule binding was missing."
        ),
        "actual_result": (
            "When an Agent evaluates a scenario that triggers human review (human_review_required: true, high risk), Agent Test ends with the generic error 'The agent could not complete this request.' "
            "No approval request is created for the configured USER participant, no review task is spawned, and no diagnostic explains why the Human Review configuration failed to execute or connect."
        ),
        "reproduction": (
            "1. Open an Agent with Governance enabled (e.g. Procurement Exception Agent).\n"
            "2. Navigate to Governance → Human Review.\n"
            "3. Configure a Human-in-Loop approval review for high-risk procurement exceptions: set Approver type to USER, specify an approver email (e.g. chiranjeevi.pk@bixbytessolutions.com), and select Approval mode ANY ONE.\n"
            "4. Save and ensure the Human Review configuration is active.\n"
            "5. Open Agent Test in Draft mode.\n"
            "6. Submit a procurement prompt with significant risk factors (e.g. 'Requires human approval before proceeding with a high-risk procurement exception involving a non-preferred supplier...').\n"
            "7. Observe that the Agent determines human review is required, but execution halts with the error 'The agent could not complete this request.'\n"
            "8. Observe that no approval request is created, no Human Review execution is presented, and the background summary card indicates 'Not used yet'."
        ),
        "repro_steps": (
            "1. Open an Agent with Governance enabled (e.g. Procurement Exception Agent).\n"
            "2. Navigate to Governance → Human Review.\n"
            "3. Configure a Human-in-Loop approval review for high-risk procurement exceptions: set Approver type to USER, specify an approver email (e.g. chiranjeevi.pk@bixbytessolutions.com), and select Approval mode ANY ONE.\n"
            "4. Save and ensure the Human Review configuration is active.\n"
            "5. Open Agent Test in Draft mode.\n"
            "6. Submit a procurement prompt with significant risk factors (e.g. 'Requires human approval before proceeding with a high-risk procurement exception involving a non-preferred supplier...').\n"
            "7. Observe that the Agent determines human review is required, but execution halts with the error 'The agent could not complete this request.'\n"
            "8. Observe that no approval request is created, no Human Review execution is presented, and the background summary card indicates 'Not used yet'."
        ),
        "expected_behavior": (
            "- If the active Human Review configuration is applicable, ART should create the approval request for the configured participant and pause/route execution according to the Human Review configuration.\n"
            "- If Human Review is not connected to the current execution path (e.g. requires an explicit 'Ask Human' Policy Rule), ART should clearly indicate that dependency in both the UI and runtime diagnostics instead of returning a generic Agent failure.\n"
            "- If participant resolution fails for a configured USER approver, ART must return a specific diagnostic identifying the lookup or resolution error.\n"
            "- Agent Test should render the pending approval state and allow the tester to view or act upon the review."
        ),
        "expected_result": (
            "If the active Human Review configuration is applicable, ART creates the approval request for the configured participant and pauses or routes execution according to the Human Review configuration. "
            "If Human Review is not connected or participant resolution fails, ART returns an informative diagnostic rather than a generic agent failure."
        ),
        "business_impact": (
            "Human-in-the-loop governance cannot be validated or deployed in production. "
            "Enterprise workflows requiring compliance sign-off or executive approval fail completely when review thresholds are reached. "
            "Collapsing HIL routing failures into generic agent execution errors prevents developers and administrators from identifying configuration gaps."
        ),
        "user_experience": (
            "The user configures a Human Review flow and triggers it with an appropriate prompt, only to receive a cryptic red error: 'The agent could not complete this request.' "
            "The configuration card continues showing 'Not used yet', giving no indication of how to connect or activate the review flow properly."
        ),
        "investigation_guidance": (
            "Trace the Human Review invocation path:\n"
            "- Execution Path: Trace Agent structured output → governance evaluation → Human Review configuration lookup → participant resolution → approval-request creation → execution pause/resume → Agent Test response.\n"
            "- USER Participant Resolution: Specifically inspect the USER participant resolution path, because this occurred after selecting a specific user (email) as the Human Review participant. Verify whether email strings are mapped to user IDs or if missing identity mapping throws an unhandled error.\n"
            "- Policy Rule Dependency: Inspect whether the Human Review configuration must be explicitly referenced by an Ask Human Policy Rule. If it does, the runtime and UI should make that dependency clear.\n"
            "- Error Handling: Inspect the exception handler in the test runner that collapses governance errors into 'The agent could not complete this request.'"
        ),
        "fix_requirement": (
            "Human Review invocation must either successfully create a pending approval for the configured user or return a specific diagnostic identifying why the review could not be invoked. "
            "Do not collapse governance/HIL failures into the generic 'agent could not complete' response."
        ),
        "recommended_solution": (
            "1. Robust Participant Resolution: Inspect the USER participant resolver in the Human Review engine to ensure configured user identities resolve to valid active account IDs without throwing unhandled exceptions.\n"
            "2. Explicit HIL Binding Architecture: If Human Review flows require an 'Ask Human' Policy Rule to trigger, enforce and display this dependency in the UI (e.g. warning 'Review is inactive until linked to a Policy Rule').\n"
            "3. Controlled Error Diagnostics: Never collapse governance/HIL orchestration exceptions into generic 'agent could not complete' messages. Return structured error codes (e.g. HIL_PARTICIPANT_UNRESOLVED or HIL_UNBOUND_RULE).\n"
            "4. Graceful Execution Pause: In Agent Test, render a pending approval banner when Human Review is triggered, allowing testers to review data and simulate/submit the human decision."
        ),
        "minimum_working_fix": (
            "Human Review invocation must either successfully create a pending approval for the configured user or return a specific diagnostic identifying why the review could not be invoked. "
            "Do not collapse governance/HIL failures into the generic 'agent could not complete' response."
        ),
        "acceptance_criteria": [
            "Submitting a prompt that triggers human review successfully initiates the configured Human Review flow or reports an explicit, actionable diagnostic.",
            "Configured USER participants (by email address) are resolved without unhandled exceptions.",
            "If Human Review requires an associated Policy Rule, the requirement is clearly indicated in both the Governance UI and execution diagnostics.",
            "The generic error 'The agent could not complete this request' is not used to mask governance/HIL execution failures.",
            "Agent Test displays the pending approval state or human review prompt when HIL is triggered."
        ]
    },
    "ART-GOV-008": {
        "title": "HIL Participant Group User Selection is Incomplete",
        "module": "GOV",
        "severity": "HIGH",
        "priority": 1,
        "environment": "Testing (Procurement Exception Agent / Governance / Human Review / App Management / Professional Plan / InvestigationLab)",
        "tags": [
            "Governance",
            "Human-Review",
            "Human-in-the-Loop",
            "HIL-Participant",
            "App-Management",
            "Groups",
            "User-Selector",
            "Pagination",
            "Directory-Search",
            "P1"
        ],
        "problem": (
            "In App Management → Groups and Governance → Human Review (Participants configuration), the user/group selector "
            "does not expose the full organization user directory, and users cannot be entered manually when they are missing from the dropdown list.\n\n"
            "When setting up Human-in-the-Loop (HIL) approval groups or assigning group participants to human review flows, "
            "the selector only displays a hardcoded or capped initial subset of accounts. Searching within the selector only filters "
            "against this preloaded list on the client side, rather than querying the backend user directory. As a result, valid active "
            "employees cannot be located or added to approval groups."
        ),
        "observed_behavior": (
            "- Incomplete Directory Expose: The user selector dropdown loads only a limited subset of accounts (e.g. showing only 'ART group test user').\n"
            "- Client-Only Filtering: Typing into the Search... field filters only within the already rendered dropdown items; it does not issue a remote query to search against the full directory.\n"
            "- No Manual Entry Fallback: Users cannot manually enter an email address or username to select an account that is not present in the preloaded set.\n"
            "- Approval Groups Blocked: Because the desired approvers cannot be selected, administrators are blocked from establishing correct group memberships for human review policies."
        ),
        "actual_result": (
            "In App Management → Groups and HIL participant configuration, the user selector dropdown only displays a capped subset of accounts. "
            "Typing in the search input only filters the client-side preloaded list without querying the backend user directory. "
            "Users absent from the initial list cannot be discovered or manually entered, preventing reliable creation and assignment of approval groups."
        ),
        "reproduction": (
            "1. Navigate to App Management → Groups (or Governance → Human Review → Edit Human-in-Loop → Step 3: Participants).\n"
            "2. Choose Approver type: GROUP (or create/edit a user group in App Management).\n"
            "3. Open the Approvers search input/dropdown.\n"
            "4. Attempt to find an active organization account that is not included in the initially loaded dropdown list.\n"
            "5. Enter the username or email in the Search... input.\n"
            "6. Observe that no results are found because search does not perform a backend query.\n"
            "7. Attempt to enter or paste the valid user identifier manually; observe that manual input is not accepted."
        ),
        "repro_steps": (
            "1. Navigate to App Management → Groups (or Governance → Human Review → Edit Human-in-Loop → Step 3: Participants).\n"
            "2. Choose Approver type: GROUP (or create/edit a user group in App Management).\n"
            "3. Open the Approvers search input/dropdown.\n"
            "4. Attempt to find an active organization account that is not included in the initially loaded dropdown list.\n"
            "5. Enter the username or email in the Search... input.\n"
            "6. Observe that no results are found because search does not perform a backend query.\n"
            "7. Attempt to enter or paste the valid user identifier manually; observe that manual input is not accepted."
        ),
        "expected_behavior": (
            "- The participant selector should perform debounced server-side queries against the complete eligible user directory.\n"
            "- Valid users should be discoverable by username, display name, or email address.\n"
            "- The dropdown should support pagination or virtualized scrolling for large directories.\n"
            "- If manual entry is restricted, the UI should provide clear contextual feedback explaining the eligibility criteria and directory source."
        ),
        "expected_result": (
            "Search queries the complete eligible user directory via server-side search and pagination. "
            "Valid active users are discoverable by username or email and can be added to approval groups."
        ),
        "business_impact": (
            "Enterprise administrators cannot configure Human-in-the-Loop approval groups with required business stakeholders. "
            "Governance review policies cannot be routed to designated approval groups, blocking compliant deployment of high-risk agent workflows."
        ),
        "user_experience": (
            "The administrator types a known colleague's name into the search box, but the interface displays no matches. "
            "There is no error message, no pagination indicator, and no way to enter the email manually, giving the impression that the user management system is broken or out of sync."
        ),
        "investigation_guidance": (
            "Inspect the user/group selector component and user directory queries:\n"
            "- Frontend Component: Inspect the user/group selector component used in App Management → Groups and the Human Review modal (Step 3: Participants).\n"
            "- Data Fetching: Check whether the component issues a single unpaginated GET request (e.g. limit=20 or page=1) on mount without a dynamic query parameter.\n"
            "- Search Query Pipeline: Trace Group UI → user search/query → pagination/filtering → eligible-user API → selected IDs → group persistence.\n"
            "- API Capabilities: Verify if the user directory endpoint supports search filtering (e.g. GET /api/v1/users?search=...) and pagination parameters (limit, offset, cursor)."
        ),
        "fix_requirement": (
            "The user selector must allow discovering and selecting any eligible organization user through server-backed search and pagination, reliably resolving selected users to canonical user IDs."
        ),
        "recommended_solution": (
            "1. Server-Side Debounced Search: Connect the search input to a backend directory search endpoint with debouncing (e.g. 300ms) to query all active accounts matching the search term.\n"
            "2. Paginated/Infinite Scroll: Implement pagination in the dropdown menu so users can browse beyond the initial page of results.\n"
            "3. Canonical ID Binding: Persist canonical user UUIDs upon selection rather than fragile display strings.\n"
            "4. Descriptive Empty State: When a search returns no results, display helpful guidance (e.g. 'No users found in directory matching <query>')."
        ),
        "minimum_working_fix": (
            "Implement server-backed searchable and paginated participant lookup in the user selector component, ensuring that typing a query searches the entire user directory and resolves the selection to a valid canonical user ID."
        ),
        "acceptance_criteria": [
            "Searching in the user selector queries the complete eligible user directory via backend API.",
            "Valid users not in the initial dropdown list can be found by username or email.",
            "Dropdown supports pagination or scrolling through the full set of eligible accounts.",
            "Selected users reliably resolve to their canonical user IDs upon group save.",
            "If arbitrary manual entry is prohibited, the interface clearly indicates eligibility and directory requirements."
        ]
    },
    "ART-GOV-009": {
        "title": "HIL Runtime Fails After Valid Human Review Configuration",
        "module": "GOV",
        "severity": "HIGH",
        "priority": 1,
        "environment": "Testing (Procurement Exception Agent / Governance / Human Review / Professional Plan / InvestigationLab)",
        "tags": [
            "Governance",
            "Human-Review",
            "Human-in-the-Loop",
            "HIL-Runtime",
            "HIL-Execution",
            "Group-Approval",
            "Agent-Runtime-Error",
            "Execution-Suspension",
            "Observability",
            "P1"
        ],
        "problem": (
            "After configuring an active Human Review approval flow with a valid GROUP participant (and ART successfully accepts "
            "the group, with the Human Review card reflecting '1 group'), submitting a high-risk procurement request that triggers "
            "human review fails at runtime with AGENT_RUNTIME_ERROR: 'The agent could not complete this request.'\n\n"
            "Because this failure occurs consistently across both USER (ART-GOV-007) and GROUP approver configurations, the root defect "
            "is within the core Human-in-the-Loop (HIL) runtime execution pipeline itself: ART fails to resolve the participant/group, "
            "create the approval request, dispatch notifications, or suspend execution, and then masks the internal failure by "
            "collapsing it into a generic AGENT_RUNTIME_ERROR."
        ),
        "observed_behavior": (
            "- Agent Model Evaluates Correctly: The LLM produces a complete structured output with human_review_required: true, risk_assessment: 'High risk...', exception_type: 'NON_PREFERRED_SUPPLIER', and recommended_next_action: 'Escalate for human review...' (Observability trace 9833e3e1).\n"
            "- Valid GROUP Configuration Accepted: In Governance → Human Review, High-Risk Procurement Exception is configured with Approver type GROUP, showing '1 group' on the summary card.\n"
            "- Generic Runtime Error: In Agent Test (thread 382d3da9...), execution halts and the Agent result preview modal reveals type: agent_error_response, status: error, code: AGENT_RUNTIME_ERROR, message: 'The agent could not complete this request.'\n"
            "- No Review Created or Suspended: No pending approval request is created, no notification is sent, and execution does not pause into an interactive approval state.\n"
            "- Zero Boundary Telemetry: Observability traces lack telemetry for review resolution, participant lookup, or approval creation, giving no insight into which stage failed."
        ),
        "actual_result": (
            "Even when an applicable Human Review configuration is configured with a valid GROUP approver and shows '1 group', "
            "submitting a high-risk request that requires human review triggers AGENT_RUNTIME_ERROR ('The agent could not complete this request.'). "
            "ART fails to resolve the group, create a pending approval request, notify group participants, or pause execution, "
            "and collapses the internal governance failure into an opaque generic runtime error."
        ),
        "reproduction": (
            "1. Open an Agent with Governance enabled (e.g. Procurement Exception Agent).\n"
            "2. Navigate to Governance → Human Review.\n"
            "3. Configure an active Human Review approval flow (e.g. High-Risk Procurement Exception) with Approver type: GROUP and assign a valid group (e.g. 'ART group test user').\n"
            "4. Save configuration and verify the Human Review summary card reflects '1 group'.\n"
            "5. Open Agent Test in Draft mode.\n"
            "6. Submit a procurement prompt with significant risk factors requiring human approval (e.g. purchase request for ₹18,75,000 for 25 laptops from a non-preferred supplier without contract or comparison).\n"
            "7. Observe that the Agent generates structured output with human_review_required: true, but execution halts.\n"
            "8. Open the Agent result preview modal.\n"
            "9. Observe that execution fails with code: AGENT_RUNTIME_ERROR and message: 'The agent could not complete this request.', with no pending approval created and no specific HIL diagnostic."
        ),
        "repro_steps": (
            "1. Open an Agent with Governance enabled (e.g. Procurement Exception Agent).\n"
            "2. Navigate to Governance → Human Review.\n"
            "3. Configure an active Human Review approval flow (e.g. High-Risk Procurement Exception) with Approver type: GROUP and assign a valid group (e.g. 'ART group test user').\n"
            "4. Save configuration and verify the Human Review summary card reflects '1 group'.\n"
            "5. Open Agent Test in Draft mode.\n"
            "6. Submit a procurement prompt with significant risk factors requiring human approval (e.g. purchase request for ₹18,75,000 for 25 laptops from a non-preferred supplier without contract or comparison).\n"
            "7. Observe that the Agent generates structured output with human_review_required: true, but execution halts.\n"
            "8. Open the Agent result preview modal.\n"
            "9. Observe that execution fails with code: AGENT_RUNTIME_ERROR and message: 'The agent could not complete this request.', with no pending approval created and no specific HIL diagnostic."
        ),
        "expected_behavior": (
            "- For an applicable Human Review, ART must evaluate governance rules, resolve the configured Human Review policy, resolve GROUP members, create and persist a pending approval request, dispatch notifications, and suspend execution into an interactive pending review state.\n"
            "- If any stage fails, ART must emit a typed diagnostic (e.g. HIL_PARTICIPANT_RESOLUTION_FAILED, HIL_GROUP_EMPTY, HIL_REVIEW_CREATION_FAILED) identifying the failed stage and root reason, rather than collapsing into AGENT_RUNTIME_ERROR."
        ),
        "expected_result": (
            "For an applicable Human Review, ART resolves the configured group, creates a pending approval, notifies participants, and pauses execution. "
            "If any stage fails, ART returns a specific HIL/governance diagnostic with the failed stage."
        ),
        "business_impact": (
            "Human-in-the-Loop runtime execution is completely blocked across both individual USER and GROUP configurations. "
            "Enterprise workflows requiring compliance sign-off or group quorum cannot be deployed or tested. "
            "Collapsing internal HIL failures into AGENT_RUNTIME_ERROR prevents operators and developers from diagnosing why review invocation fails."
        ),
        "user_experience": (
            "The user configures an approval group, confirms it displays '1 group' in Governance, and runs a test scenario, only to receive a cryptic AGENT_RUNTIME_ERROR: 'The agent could not complete this request.' "
            "The preview modal provides zero actionable details, leaving the builder unable to determine how to fix the workflow."
        ),
        "investigation_guidance": (
            "Trace the complete Human-in-the-Loop runtime invocation path:\n"
            "- Trace Path: Agent result → governance evaluation → applicable policy/review resolution → Human Review config → GROUP participant resolution → group members → approval request persistence → notification dispatch → execution suspension → response.\n"
            "- Group Resolution: Check how the group ID/name ('ART group test user') is resolved to member user IDs. Verify whether group membership resolution fails or returns an empty list.\n"
            "- Approval Request Creation: Check the database transaction or service call that persists the approval request entity. Verify if a foreign key constraint or schema mismatch triggers an unhandled exception.\n"
            "- Execution State Machine: Check how the execution engine suspends the agent run when awaiting human input. Verify whether the orchestrator fails to handle the suspended state and throws AGENT_RUNTIME_ERROR.\n"
            "- Boundary Logging: Add structured logging across all HIL boundaries: review_config_id, review_type, participant_type, participant/group ID, resolved_participant_count, approval_mode, review_request_id, notification result, execution state, and actual failure code/message."
        ),
        "fix_requirement": (
            "Never convert an internal Human-in-the-Loop execution failure into only AGENT_RUNTIME_ERROR. "
            "The runtime must either successfully create the pending approval request and pause execution or return a specific diagnostic indicating the exact failed stage."
        ),
        "recommended_solution": (
            "1. Multi-Stage HIL Execution Pipeline: Implement robust stage-by-stage handling for HIL invocation:\n"
            "   Agent result → governance evaluation → applicable policy/review resolution → Human Review config → GROUP participant resolution → group members → approval request persistence → notification dispatch → execution suspension → response.\n"
            "2. Structured Boundary Telemetry: Log and emit structured telemetry at each boundary:\n"
            "   review_config_id, review_type, participant_type, participant/group ID, resolved_participant_count, approval_mode, review_request_id, notification result, execution state, and actual failure code/message.\n"
            "3. Specific Error Codes: Replace generic AGENT_RUNTIME_ERROR with typed governance error codes: HIL_PARTICIPANT_RESOLUTION_FAILED, HIL_GROUP_EMPTY, HIL_REVIEW_CREATION_FAILED, HIL_POLICY_NOT_MATCHED, HIL_DISPATCH_FAILED.\n"
            "4. Graceful Execution Suspension: In Agent Test, render the pending approval banner allowing the tester to inspect the pending review and simulate/submit an approval decision."
        ),
        "minimum_working_fix": (
            "Catch internal exceptions within the Human Review execution pipeline specifically and return an informative diagnostic identifying the failed stage (e.g. HIL_PARTICIPANT_RESOLUTION_FAILED or HIL_REVIEW_CREATION_FAILED) instead of letting the exception bubble up to the global catch block that emits generic AGENT_RUNTIME_ERROR."
        ),
        "acceptance_criteria": [
            "High-risk requests triggering Human Review do not produce generic AGENT_RUNTIME_ERROR.",
            "Active GROUP review configurations successfully resolve group members and create a pending approval request.",
            "Agent Test displays the pending review state and execution suspension.",
            "Any failure in the HIL pipeline returns a structured diagnostic with the specific failure code and failed stage.",
            "Observability traces record review_config_id, participant_type, resolved_participant_count, and execution_state."
        ]
    },
    "ART-SFN-002": {
        "title": "Serverless Function Input Mapper Cannot Access Agent Output Fields",
        "module": "SFN",
        "severity": "HIGH",
        "priority": 1,
        "environment": "Testing (Procurement Exception Agent / Agent Capabilities / Serverless Functions / Professional Plan / InvestigationLab)",
        "tags": [
            "Serverless-Functions",
            "Data-Mapper",
            "Input-Mapping",
            "Agent-Lab",
            "Workflow-Node",
            "Capabilities",
            "Schema-Registry",
            "Output-Parser",
            "P1"
        ],
        "problem": (
            "A Serverless Function assigned through Agent Capabilities (e.g. prepare_investigation_row) is available on the Agent workflow canvas, "
            "but its Input Mapping via the Data Mapper interface cannot access the Agent's runtime or structured output data.\n\n"
            "When configuring the function's input contract, the only selectable Source node in the Data Mapper dropdown is Meta. "
            "Meta only provides system-level execution attributes (configuration_id, environment_name, tenant, task_id). "
            "Neither the parent Agent node nor the Output Parser node is available as a selectable source. As a result, "
            "the business fields required by the Serverless Function contract cannot be mapped from the Agent's output."
        ),
        "observed_behavior": (
            "- Successful Capability Assignment: The Serverless Function prepare_investigation_row is successfully attached via Capabilities and appears connected under the Tool Connector node in the Agent workflow canvas.\n"
            "- Contract Expects Business Fields: The function contract expects structured investigation fields: actual_result, business_impact, classification, discussion, expected_result, media_status, media_summary, module, priority, ready_for_ticket, recommended_solution, severity, thread_id, and title.\n"
            "- Source Node Restricted to Meta: In the Data Mapper modal, opening the Source node dropdown only displays Meta.\n"
            "- Source Field Restricted to Metadata: Selecting Meta exposes only configuration_id, environment_name, tenant, and task_id.\n"
            "- Agent and Parser Missing: Neither Procurement Exception Agent nor Output Parser is discoverable as a mapping source, making it impossible to pass agent output into the Serverless Function."
        ),
        "actual_result": (
            "In Data Mapper for a Serverless Function assigned through Agent Capabilities, the only selectable Source node is 'Meta'. "
            "Neither the Agent node nor the Output Parser node is exposed as a mapping source. "
            "Because Meta only provides execution metadata (configuration_id, environment_name, tenant, task_id), "
            "none of the Agent's structured business outputs or parsed fields can be mapped into the function contract, leaving the input mapping unusable."
        ),
        "reproduction": (
            "1. Open an Agent in Agent Lab (e.g. Procurement Exception Agent).\n"
            "2. Go to Capabilities and assign a Serverless Function (e.g. prepare_investigation_row).\n"
            "3. Return to the Workflow tab and verify the function node is present under Tool Connector.\n"
            "4. Click the gear icon on the Serverless Function node to open Configure serverless function.\n"
            "5. Under Basic Config → Input mapping, click to open the Data Mapper.\n"
            "6. Select any target contract field (e.g. actual_result or business_impact).\n"
            "7. Open the Source node dropdown and observe that only Meta is listed.\n"
            "8. Open the Source field dropdown under Meta and observe that only metadata attributes appear.\n"
            "9. Attempt to select or map any field from the Agent or Output Parser; observe that no agent data is accessible."
        ),
        "repro_steps": (
            "1. Open an Agent in Agent Lab (e.g. Procurement Exception Agent).\n"
            "2. Go to Capabilities and assign a Serverless Function (e.g. prepare_investigation_row).\n"
            "3. Return to the Workflow tab and verify the function node is present under Tool Connector.\n"
            "4. Click the gear icon on the Serverless Function node to open Configure serverless function.\n"
            "5. Under Basic Config → Input mapping, click to open the Data Mapper.\n"
            "6. Select any target contract field (e.g. actual_result or business_impact).\n"
            "7. Open the Source node dropdown and observe that only Meta is listed.\n"
            "8. Open the Source field dropdown under Meta and observe that only metadata attributes appear.\n"
            "9. Attempt to select or map any field from the Agent or Output Parser; observe that no agent data is accessible."
        ),
        "expected_behavior": (
            "- The Data Mapper must expose all valid upstream data-producing sources in the Agent context.\n"
            "- The Agent structured output and Output Parser output must be selectable as Source nodes.\n"
            "- Selecting the Agent or Output Parser as the source node should populate the Source field dropdown with its declared schema fields.\n"
            "- Mapped fields must be persisted upon saving and resolved to runtime values when the function executes."
        ),
        "expected_result": (
            "Data Mapper exposes the Agent and Output Parser as selectable Source nodes with their active schema fields, "
            "allowing builders to map runtime business data into the Serverless Function contract."
        ),
        "business_impact": (
            "Serverless Functions attached to Agents via Capabilities cannot consume agent reasoning or structured output. "
            "Post-processing functions (e.g. database insertion, ticket row preparation, external notifications) cannot operate on agent data. "
            "This defect blocks end-to-end automation pipelines that rely on Serverless Functions within Agent workflows."
        ),
        "user_experience": (
            "The user attaches a Serverless Function to automate post-processing, sees it appear in the workflow, and opens the Data Mapper expecting to wire the agent's output fields into the function inputs. "
            "Instead, the user finds only a bare Meta node with four system strings, with no way to access the business data generated by the agent."
        ),
        "investigation_guidance": (
            "Trace the schema discovery and node registry pipeline:\n"
            "- Trace Path: Capability assignment → function node creation → function input contract → Data Mapper source discovery → upstream node/schema registry → Agent/Output Parser schema exposure → persisted mapping → runtime function payload.\n"
            "- Mapper Discovery Logic: Inspect the Data Mapper source discovery service. Determine whether it assumes an Orchestrator DAG with explicit incoming data edges, failing to recognize capability-owned functions attached directly to an Agent.\n"
            "- Agent Context Registration: Verify how the Agent and Output Parser schemas are published to the node registry so that embedded capability nodes can access them.\n"
            "- Payload Compiler: Inspect the runtime execution engine where function payloads are constructed before invocation. Verify that mapped agent paths resolve correctly against the active execution context."
        ),
        "fix_requirement": (
            "Populate Data Mapper source nodes with every valid data-producing source accessible to the Serverless Function. "
            "Agent structured output and Output Parser fields must be selectable, persistable, and resolved at runtime."
        ),
        "recommended_solution": (
            "1. Context-Aware Source Discovery: Update the Data Mapper source provider to detect when a Serverless Function is hosted within an Agent workflow and inject the parent Agent and Output Parser nodes as available source nodes.\n"
            "2. Schema Introspection: Dynamically load the current Output Parser schema fields into the Source field dropdown when the Output Parser or Agent source node is selected.\n"
            "3. Robust Mapping Persistence: Serialize mapped paths (e.g. agent.output.facts or output_parser.risk_assessment) into the function node configuration.\n"
            "4. Runtime Argument Binding: At runtime before function execution, resolve the mapped expressions against the completed agent output and pass the resolved dictionary as the function input arguments."
        ),
        "minimum_working_fix": (
            "In the Data Mapper source discovery handler, include the Agent's Output Parser as a selectable Source node alongside Meta, "
            "expose its top-level schema fields under Source field, and pass the mapped values to the function during workflow execution."
        ),
        "acceptance_criteria": [
            "Data Mapper displays the Agent and/or Output Parser as selectable Source nodes alongside Meta.",
            "Schema fields defined in the Output Parser appear in the Source field dropdown.",
            "Target function contract fields can be mapped to corresponding agent output fields.",
            "Saved mappings persist across workflow reload, build, and publish.",
            "At runtime, the Serverless Function receives the resolved agent output values.",
            "Meta properties remain available for mapping."
        ]
    },
    "ART-TOOL-002": {
        "title": "Add Built-in Row Filtering Support to Supabase Database Tools",
        "module": "TOOL",
        "severity": "HIGH",
        "priority": 1,
        "environment": "Testing (Procurement Exception Agent / Tool Builder / Supabase Tools / Professional Plan / InvestigationLab)",
        "tags": [
            "Tool-Builder",
            "Supabase",
            "Database-Tools",
            "Select-Rows",
            "Update-Rows",
            "Delete-Rows",
            "Row-Filtering",
            "PostgREST",
            "Safety-Validation",
            "P1"
        ],
        "problem": (
            "The Supabase database tools (Select Rows, Update Rows, and Delete Rows) fail with HTTP status 400 "
            "whenever a filter is supplied to narrow the scope of the operation.\n\n"
            "While unfiltered Select Rows and single Insert Row operations execute successfully, any attempt to filter "
            "records using standard PostgREST syntax (e.g. test_key=eq.ART-SUPABASE-DB-001 or id=eq.1) causes the tool "
            "to fail with 'failed to parse filter (...)'. The tools lack built-in, native structured row filtering support. "
            "Instead of providing structured filter inputs in the tool schema that automatically translate to valid backend "
            "queries, the tools expect raw filter strings that the runtime fails to parse and transmit correctly to Supabase."
        ),
        "observed_behavior": (
            "- Select Rows with Filter Fails: Executing Select Rows on table art_connector_test with test_key=eq.ART-SUPABASE-DB-001 returns status 400: 'failed to parse filter (test_key=eq.ART-SUPABASE-DB-001)'.\n"
            "- Select Rows with ID Filter Fails: Executing Select Rows with id=eq.1 returns status 400: 'failed to parse filter (id=eq.1)'.\n"
            "- Update Rows with Filter Fails: Executing Update Rows (supabase_art__update_rows) with id=eq.1 returns status 400: 'failed to parse filter (id=eq.1)'.\n"
            "- Delete Rows with Filter Fails: Executing Delete Rows (supabase_art__delete_rows) with id=eq.1 returns status 400: 'failed to parse filter (id=eq.1)'.\n"
            "- Baseline Operations Pass: Unfiltered Select Rows and Insert Row operations succeed."
        ),
        "actual_result": (
            "When any filter is supplied to the Supabase Select Rows, Update Rows, or Delete Rows tools, "
            "the tool execution fails with HTTP status 400 and error: 'failed to parse filter (...)'. "
            "The tools currently do not provide built-in structured filtering or correctly format filter expressions for the PostgREST backend. "
            "Unfiltered Select Rows and Insert Row succeed, but any filtered query, update, or deletion fails."
        ),
        "reproduction": (
            "1. Open an Agent with Supabase database tools enabled (e.g. Procurement Exception Agent).\n"
            "2. Ensure Select Rows, Update Rows, and Delete Rows tools (from Supabase Data REST API) are connected under Tool Connector.\n"
            "3. In Agent Test, submit a query requesting to select a row with a filter (e.g. 'Use the Supabase Select Rows tool on table art_connector_test. Filter the rows using: test_key=eq.ART-SUPABASE-DB-001' or 'id=eq.1').\n"
            "4. Observe that the tool fails with HTTP status 400: 'failed to parse filter (id=eq.1)'.\n"
            "5. Submit a query requesting to update a specific row with a filter (e.g. update row where id=1 on table art_connector_test).\n"
            "6. Observe that Update Rows fails with HTTP status 400: 'failed to parse filter (id=eq.1)'.\n"
            "7. Submit a query requesting to delete a specific row with a filter (e.g. delete row where id=1 on table art_connector_test).\n"
            "8. Observe that Delete Rows fails with HTTP status 400: 'failed to parse filter (id=eq.1)'."
        ),
        "repro_steps": (
            "1. Open an Agent with Supabase database tools enabled (e.g. Procurement Exception Agent).\n"
            "2. Ensure Select Rows, Update Rows, and Delete Rows tools (from Supabase Data REST API) are connected under Tool Connector.\n"
            "3. In Agent Test, submit a query requesting to select a row with a filter (e.g. 'Use the Supabase Select Rows tool on table art_connector_test. Filter the rows using: test_key=eq.ART-SUPABASE-DB-001' or 'id=eq.1').\n"
            "4. Observe that the tool fails with HTTP status 400: 'failed to parse filter (id=eq.1)'.\n"
            "5. Submit a query requesting to update a specific row with a filter (e.g. update row where id=1 on table art_connector_test).\n"
            "6. Observe that Update Rows fails with HTTP status 400: 'failed to parse filter (id=eq.1)'.\n"
            "7. Submit a query requesting to delete a specific row with a filter (e.g. delete row where id=1 on table art_connector_test).\n"
            "8. Observe that Delete Rows fails with HTTP status 400: 'failed to parse filter (id=eq.1)'."
        ),
        "expected_behavior": (
            "- Supabase database tools (Select Rows, Update Rows, Delete Rows) should natively support row filtering via structured parameters.\n"
            "- The tool implementation must convert structured filters into the correct PostgREST query parameters internally (e.g. id=eq.1).\n"
            "- Common comparison operators must be supported: eq, neq, gt, gte, lt, lte, like, ilike, is, in.\n"
            "- Select Rows must return only matching records. Update Rows must modify only matching records. Delete Rows must remove only matching records.\n"
            "- For Update Rows and Delete Rows, filters must be strictly validated before execution; if a filter is invalid or absent without explicit bulk override, the operation must abort safely without mutating data."
        ),
        "expected_result": (
            "Supabase database tools support row filtering as a built-in capability, translating structured filters into valid PostgREST queries. "
            "Select, Update, and Delete operations target only matching rows, and invalid filters fail safely without modifying data."
        ),
        "business_impact": (
            "Agents cannot query specific records, update individual rows, or delete targeted items in Supabase databases. "
            "All real-world database workflows requiring record lookup, status updating, or specific record deletion are completely broken. "
            "Furthermore, if a faulty filter handling fallback were to execute without constraints, mutating operations could accidentally modify or delete all rows in a database table."
        ),
        "user_experience": (
            "The agent attempts to follow user instructions to query or update a specific record, but the tool immediately crashes with an unhelpful status 400: 'failed to parse filter (...)' error. "
            "Users and agents are left guessing how filter syntax should be formatted, with no built-in schema guidance."
        ),
        "investigation_guidance": (
            "Trace the tool invocation and query construction pipeline:\n"
            "- Trace Path: Agent tool call → tool parameter validation → filter parser/translator → Supabase/PostgREST HTTP request builder → API execution → response parsing.\n"
            "- Query Parameter Construction: Inspect how the filter parameter is serialized into the HTTP request URL. Check whether filter strings are being passed as raw body parameters, headers, or improperly URL-encoded query parameters.\n"
            "- PostgREST Specification: PostgREST expects filters as URL query parameters in the format ?column=operator.value (e.g. ?id=eq.1). Verify whether the tool currently sends filters in the request body or wraps them incorrectly.\n"
            "- Tool Schema Definition: Inspect the OpenAPI / JSON schema definition for supabase_art__select_rows, supabase_art__update_rows, and supabase_art__delete_rows. Verify how the filter parameter is typed and whether it exposes structured filter fields."
        ),
        "fix_requirement": (
            "Implement built-in structured row filtering in the Supabase Select Rows, Update Rows, and Delete Rows tools. "
            "The tools must accept structured filter objects, translate them internally into valid PostgREST query parameters, and enforce strict safety validation before executing mutating operations."
        ),
        "recommended_solution": (
            "1. Structured Filter Input Schema: Update tool schemas to accept a filters array of objects containing column (string), operator (enum of supported PostgREST operators), and value (primitive or list).\n"
            "2. Internal PostgREST Query Builder: Translate the structured filters into standard URL query strings (e.g. filter[0] -> ?column=eq.value).\n"
            "3. Operator Coverage: Support standard operators: eq, neq, gt, gte, lt, lte, like, ilike, is, in.\n"
            "4. Safety Guardrail on Mutations: In Update Rows and Delete Rows, require non-empty valid filters by default. If no valid filter is present, reject the request with UNFILTERED_MUTATION_REJECTED unless an explicit allow_all_rows: true flag is provided.\n"
            "5. Accurate Error Messaging: When an unparseable filter or invalid column is supplied, return a clear, structured validation error before making any network call."
        ),
        "minimum_working_fix": (
            "Update the tool execution handler for Supabase database tools to properly format PostgREST query parameters on the outgoing HTTP request (e.g. converting id=eq.1 to the URL query string ?id=eq.1), safely validating that mutating operations (update, delete) never run without a verified filter expression."
        ),
        "acceptance_criteria": [
            "Select Rows returns only rows matching the specified filter criteria.",
            "Update Rows modifies only rows matching the specified filter criteria.",
            "Delete Rows removes only rows matching the specified filter criteria.",
            "Common operators (eq, neq, gt, gte, lt, lte, like, ilike, is, in) execute correctly.",
            "Invalid or unparseable filter inputs return a clear HTTP 400 validation error without executing mutations.",
            "Unfiltered updates and deletions are blocked by default for data safety.",
            "Unfiltered Select Rows and Insert Row continue to function without regressions."
        ]
    },
    "ART-AGENTX-001": {
        "title": "Agent X authorization error message has incorrect padding and clipped close button on mobile",
        "module": "AGENTX",
        "severity": "LOW",
        "priority": 3,
        "environment": "Mobile (Android, Agent X Mobile Web/App, Select Workspace screen)",
        "tags": [
            "Agent-X",
            "Select-Workspace",
            "Mobile",
            "UI-Alignment",
            "Alert-Banner",
            "Padding",
            "Dismiss-Button",
            "P3"
        ],
        "problem": (
            "In Agent X, the authorization error banner displayed on the mobile Select Workspace screen suffers from layout containment and padding defects. "
            "The alert container has insufficient right-side padding, causing the dismissible error badge to be visually clipped along the right border "
            "and rendering the close ('x') icon partially obscured and difficult to interact with on mobile interfaces."
        ),
        "observed_behavior": (
            "- On the Agent X mobile Select Workspace screen, an authorization failure renders the alert banner: 'Authorization failed: Invalid expiry'.\n"
            "- The alert banner exhibits insufficient padding and margins along the right boundary.\n"
            "- The right-side rounded corner of the alert container is visually truncated / clipped.\n"
            "- The circular close button containing the white x glyph is clipped against the right perimeter of the banner and partially obscured.\n"
            "- The alert content and dismiss button do not appear properly balanced within the alert box."
        ),
        "actual_result": (
            "On the Agent X mobile Select Workspace screen, an authorization failure renders the alert banner: Authorization failed: Invalid expiry. "
            "The alert banner exhibits insufficient padding and margins along the right boundary. The right-side rounded corner of the alert container is visually truncated / clipped. "
            "The circular close button containing the white x glyph is clipped against the right perimeter of the banner and partially obscured."
        ),
        "reproduction": (
            "1. Open the Agent X mobile application or web client on a mobile device or responsive viewport.\n"
            "2. Navigate to the Select Workspace screen.\n"
            "3. Trigger an authorization error (e.g. attempt authentication with an expired session or invalid token yielding Authorization failed: Invalid expiry).\n"
            "4. Observe the rendered error alert banner container and dismiss button."
        ),
        "repro_steps": (
            "1. Open the Agent X mobile application or web client on a mobile device or responsive viewport.\n"
            "2. Navigate to the Select Workspace screen.\n"
            "3. Trigger an authorization error (e.g. attempt authentication with an expired session or invalid token yielding Authorization failed: Invalid expiry).\n"
            "4. Observe the rendered error alert banner container and dismiss button."
        ),
        "expected_behavior": (
            "The error alert container should maintain consistent internal padding and margins on all sides across mobile viewports. "
            "The complete alert container, including its rounded corners, should remain visible within the screen, and the close (x) button should be fully visible, properly aligned, and easily tappable."
        ),
        "expected_result": (
            "The error alert container maintains consistent internal padding on all sides, the complete container and rounded corners remain fully visible, "
            "and the close button is completely visible, properly positioned, and easily tappable on mobile viewports."
        ),
        "business_impact": (
            "Degrades user experience and visual polish on mobile devices. A clipped dismiss action hinders mobile users from easily closing the error banner, "
            "making the interface appear broken and reducing user confidence during workspace selection and onboarding."
        ),
        "user_experience": (
            "Users encountering an authorization error on mobile see an unbalanced, trimmed alert box where the close button is partially cut off at the right edge, "
            "making it difficult to dismiss the error message cleanly."
        ),
        "investigation_guidance": (
            "Inspect the styling and layout definitions for the authorization error alert container in the Agent X Select Workspace view. "
            "Check the CSS/layout rules governing container padding, margins, overflow properties, flex/grid alignment, and responsive constraints on mobile viewports. "
            "Compare the right-side padding with the left-side padding and verify that the close button container has adequate right margin/padding without overflowing or being clipped by parent overflow boundaries."
        ),
        "fix_requirement": (
            "The alert component on mobile viewports must enforce uniform padding, ensure child elements (including the close button) remain within the visible container bounds without clipping, "
            "and preserve accessibility and tap target dimensions."
        ),
        "recommended_solution": (
            "Adjust the container's responsive stylesheet to ensure proper horizontal padding (e.g. symmetric padding on left and right) and ensure box-sizing: border-box "
            "or appropriate flexbox spacing (justify-content: space-between, align-items: center) is applied. Ensure parent containers on mobile do not impose clipping "
            "(overflow: hidden) that cuts off the alert border radius."
        ),
        "minimum_working_fix": (
            "Apply proper right padding or margin to the error alert container and ensure the close button container is spaced safely away from the right edge so that the button and rounded border remain intact and unclipped."
        ),
        "acceptance_criteria": [
            "The error alert banner displays with consistent horizontal and vertical padding on mobile screens.",
            "The right-side boundary and rounded corners of the alert container are fully visible and unclipped.",
            "The close (x) button is completely visible and positioned with adequate clearance from the container border.",
            "The close button remains easily tappable with an adequate touch target.",
            "The alert message text remains clearly readable and balanced."
        ]
    },
    "ART-AGENTX-002": {
        "title": "Agent X mobile UI is trimmed at screen edges and corners",
        "module": "AGENTX",
        "severity": "LOW",
        "priority": 3,
        "environment": "Mobile (Android, Agent X Mobile Web/App, Select Workspace screen)",
        "tags": [
            "Agent-X",
            "Mobile-UI",
            "Select-Workspace",
            "Responsive-Design",
            "Viewport-Padding",
            "Layout-Clipping",
            "P3"
        ],
        "problem": (
            "In Agent X, the Select Workspace screen suffers from inadequate horizontal viewport margins and responsive layout containment on mobile devices. "
            "The screen content container, including header text, authorization alert banner, dropdown picker, input field, and action buttons, is positioned "
            "too close to the mobile screen boundaries, causing components to appear visually clipped or trimmed at the left and right edges and corners."
        ),
        "observed_behavior": (
            "- On the Agent X mobile Select Workspace screen, main content extends excessively close to the mobile screen boundaries.\n"
            "- Left and right display areas appear visually trimmed and clipped.\n"
            "- UI elements lack consistent responsive horizontal padding across the mobile viewport.\n"
            "- The error alert banner and workspace selection container appear compressed within the available screen width.\n"
            "- Spacing around corners and edges is inconsistent on the mobile layout."
        ),
        "actual_result": (
            "On the Agent X mobile Select Workspace screen, main content extends excessively close to the mobile screen boundaries. "
            "Left and right display areas appear visually trimmed and clipped. UI elements lack consistent responsive horizontal padding across the mobile viewport. "
            "The error alert banner and workspace selection container appear compressed within the available screen width. "
            "Spacing around corners and edges is inconsistent on the mobile layout."
        ),
        "reproduction": (
            "1. Open the Agent X mobile application or web client on a mobile device or responsive viewport.\n"
            "2. Navigate to the Select Workspace screen.\n"
            "3. Observe the layout spacing, horizontal margins, and edge containment of the card container, alert banner, and workspace selection controls."
        ),
        "repro_steps": (
            "1. Open the Agent X mobile application or web client on a mobile device or responsive viewport.\n"
            "2. Navigate to the Select Workspace screen.\n"
            "3. Observe the layout spacing, horizontal margins, and edge containment of the card container, alert banner, and workspace selection controls."
        ),
        "expected_behavior": (
            "The Agent X mobile interface should maintain consistent responsive padding and safe margins from all screen edges. "
            "No content, borders, rounded corners, alert banners, form controls, or action buttons should appear clipped, trimmed, or compressed on supported mobile screen sizes."
        ),
        "expected_result": (
            "The Agent X mobile interface maintains consistent responsive padding and safe margins from all screen edges. "
            "No content, borders, rounded corners, alert banners, form controls, or action buttons appear clipped, trimmed, or compressed on supported mobile screen sizes."
        ),
        "business_impact": (
            "Degrades visual polish and user confidence during initial workspace selection. Clipping and lack of safe horizontal margins make the mobile interface appear broken and risk obstructing touch targets located near viewport boundaries."
        ),
        "user_experience": (
            "Mobile users see a cramped screen layout where form elements, alert boxes, and headers push directly against the device display edges, making the UI appear cut off and poorly optimized for mobile screens."
        ),
        "investigation_guidance": (
            "Inspect the responsive CSS stylesheet rules, layout grid/flexbox containers, and padding configurations for the Select Workspace screen in Agent X. "
            "Check the outermost content wrapper for missing or insufficient horizontal padding (e.g. padding: 0 16px or safe-area-inset) on mobile viewport breakpoints (< 640px). "
            "Verify that container max-width constraints and overflow properties do not truncate rounded corners or push elements flush against screen perimeters."
        ),
        "fix_requirement": (
            "The Select Workspace view on mobile viewports must enforce uniform container padding and safe horizontal margins, ensuring all child cards, alert banners, form controls, and action buttons remain fully visible, properly padded, and unclipped."
        ),
        "recommended_solution": (
            "Add or adjust responsive horizontal padding (e.g. padding-left: 16px; padding-right: 16px; or utility class px-4) on the top-level page or card wrapper for mobile viewports. "
            "Ensure box-sizing: border-box is set and integrate CSS safe-area insets (env(safe-area-inset-left), env(safe-area-inset-right)) so that edge boundaries and border radii are preserved cleanly."
        ),
        "minimum_working_fix": (
            "Apply adequate horizontal padding (e.g. minimum 16px safe margin) to the main container wrapper on mobile viewports so that elements are not positioned directly against or clipped by screen edges."
        ),
        "acceptance_criteria": [
            "The Select Workspace screen displays with consistent horizontal and vertical safe padding on mobile viewports.",
            "Form containers, alert banners, and action buttons remain fully visible with unclipped borders and rounded corners.",
            "No UI elements extend flush against or beyond display perimeters on supported mobile screen dimensions.",
            "Touch targets and dismiss buttons maintain adequate clearance from viewport edges.",
            "Desktop and tablet viewports remain unaffected and properly centered."
        ]
    }
}


_ALLOWED_TAG_PATTERN = re.compile(
    r"(</?(?:strong|code|em|br|ul|ol|li)(?:\s*/?>|\s*>))",
    re.IGNORECASE
)


def _sanitize_text(text: str) -> str:
    """
    Escapes HTML entities in text while preserving whitelisted semantic tags
    and markdown code backticks.
    """
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    parts = _ALLOWED_TAG_PATTERN.split(text)
    out = []
    for part in parts:
        if _ALLOWED_TAG_PATTERN.match(part):
            out.append(part)
        else:
            out.append(html.escape(part, quote=True))
    return "".join(out)


def _format_section_content_to_html(content: Any) -> str:
    """
    Renders structured section content into clean, semantic Azure DevOps compatible HTML.
    Preserves lists (unordered and ordered), line breaks, and code tokens cleanly.
    """
    if not content or content == "Not provided":
        return "<p>Not provided</p>"

    if isinstance(content, list):
        if not content:
            return "<p>Not provided</p>"
        items_html = "".join(f"<li>{_sanitize_text(str(item))}</li>" for item in content)
        return f"<ul>{items_html}</ul>"

    text = str(content).strip()
    if not text or text == "Not provided":
        return "<p>Not provided</p>"

    lines = text.splitlines()
    html_parts = []
    in_ul = False
    in_ol = False
    current_p = []

    def flush_p():
        nonlocal current_p
        if current_p:
            p_text = " ".join(current_p).strip()
            if p_text:
                sanitized_p = _sanitize_text(p_text)
                html_parts.append(f"<p>{sanitized_p}</p>")
            current_p = []

    def flush_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            html_parts.append("</ul>")
            in_ul = False
        if in_ol:
            html_parts.append("</ol>")
            in_ol = False

    for line in lines:
        sline = line.strip()
        if not sline:
            flush_p()
            flush_lists()
            continue

        m_ul = re.match(r"^[-*]\s+(.+)$", sline)
        m_ol = re.match(r"^\d+\.\s+(.+)$", sline)

        if m_ul:
            flush_p()
            if in_ol:
                html_parts.append("</ol>")
                in_ol = False
            if not in_ul:
                html_parts.append("<ul>")
                in_ul = True
            item_text = _sanitize_text(m_ul.group(1))
            html_parts.append(f"<li>{item_text}</li>")
        elif m_ol:
            flush_p()
            if in_ul:
                html_parts.append("</ul>")
                in_ul = False
            if not in_ol:
                html_parts.append("<ol>")
                in_ol = True
            item_text = _sanitize_text(m_ol.group(1))
            html_parts.append(f"<li>{item_text}</li>")
        else:
            if in_ul or in_ol:
                if not (line.startswith("   ") or line.startswith("\t")):
                    flush_lists()
            current_p.append(sline)

    flush_p()
    flush_lists()
    return "".join(html_parts)


class DeveloperTicketProjector:
    """
    Projects a canonical ticket dictionary and optional enrichment data into
    a DeveloperTicketProjection.
    """

    @classmethod
    def project_ticket(
        cls,
        ticket: Dict[str, Any],
        canonical_bug_id: str,
        enrichments: Optional[Dict[str, Any]] = None
    ) -> DeveloperTicketProjection:
        enrichments = enrichments or {}
        canon_defaults = CANONICAL_BUG_DATA.get(canonical_bug_id, {})

        # 1. Canonical inputs
        title = ticket.get("title", f"Bug {canonical_bug_id}")
        repro = ticket.get("reproduction") or ticket.get("repro_steps") or ticket.get("reproSteps")
        expected = (
            ticket.get("expected_behavior")
            or ticket.get("expected_result")
            or ticket.get("expectedResult")
            or ticket.get("expected")
        )
        actual = (
            ticket.get("observed_behavior")
            or ticket.get("actual_result")
            or ticket.get("actualResult")
            or ticket.get("actual")
        )
        solution = ticket.get("recommended_solution") or ticket.get("recommendedSolution") or ticket.get("fix_proposal")
        impact = ticket.get("business_impact") or ticket.get("businessImpact")
        ux = ticket.get("user_experience") or ticket.get("userExperience")
        inv_guidance = ticket.get("investigation_guidance") or ticket.get("investigationGuidance")
        fix_req = ticket.get("fix_requirement") or ticket.get("fixRequirement")
        mwf_input = ticket.get("minimum_working_fix") or ticket.get("minimumWorkingFix")
        ac_input = ticket.get("acceptance_criteria") or ticket.get("acceptanceCriteria")

        # 2. Problem
        problem = enrichments.get("problem")
        if not problem:
            if canonical_bug_id == "ART-AGENT-001":
                problem = (
                    "The Agent Output Parser is <strong>not enforcing the configured output contract</strong> "
                    "before accepting an Agent Result."
                )
            elif canon_defaults.get("problem"):
                problem = canon_defaults["problem"]
            elif ticket.get("problem"):
                problem = ticket["problem"]
            else:
                problem = title

        # 3. What is failing / Observed Behavior / Actual Result
        what_is_failing = enrichments.get("what_is_failing")
        critical_behavior = enrichments.get("critical_behavior")
        actual_result_clean = enrichments.get("observed_behavior") or enrichments.get("actual_result")
        if what_is_failing is None:
            if canonical_bug_id == "ART-AGENT-001":
                what_is_failing = [
                    "<strong>Wrong property names</strong> — <code>field_name</code> instead of <code>field</code>",
                    "<strong>Wrong data types</strong> — numeric values returned as strings",
                    "<strong>Invalid collection values</strong> — <code>mismatches: null</code> instead of <code>mismatches: []</code>"
                ]
                critical_behavior = (
                    "ART still displays these responses as <strong>successful Agent Results</strong>."
                )
            elif actual and actual != "Not provided":
                what_is_failing = [actual]
            elif canon_defaults.get("observed_behavior"):
                what_is_failing = [canon_defaults["observed_behavior"]]
            elif canon_defaults.get("actual_result"):
                what_is_failing = [canon_defaults["actual_result"]]
            else:
                what_is_failing = []

        if not actual_result_clean:
            if actual and actual != "Not provided":
                actual_result_clean = actual
            elif canon_defaults.get("observed_behavior"):
                actual_result_clean = canon_defaults["observed_behavior"]
            elif canon_defaults.get("actual_result"):
                actual_result_clean = canon_defaults["actual_result"]

        observed_behavior_clean = actual_result_clean

        # 4. Reproduction / Repro Steps rule: never manufacture. If missing or "Not provided" -> "Not provided"
        if repro and repro.strip() and repro.strip() != "Not provided":
            repro_clean = repro.strip()
        elif canon_defaults.get("reproduction") and canon_defaults.get("reproduction") != "Not provided":
            repro_clean = canon_defaults["reproduction"]
        elif canon_defaults.get("repro_steps") and canon_defaults.get("repro_steps") != "Not provided":
            repro_clean = canon_defaults["repro_steps"]
        else:
            repro_clean = "Not provided"

        # 5. Expected Behavior / Expected Result
        expected_clean = enrichments.get("expected_behavior") or enrichments.get("expected_result")
        if not expected_clean:
            if canonical_bug_id == "ART-AGENT-001":
                expected_clean = (
                    "ART should <strong>validate the Agent Result against the configured output schema "
                    "before accepting it</strong>.<br/>"
                    "If validation fails, the result should <strong>not continue as successful output "
                    "or reach governance</strong>."
                )
            elif expected and expected.strip() != "Not provided":
                expected_clean = expected.strip()
            elif canon_defaults.get("expected_behavior"):
                expected_clean = canon_defaults["expected_behavior"]
            elif canon_defaults.get("expected_result"):
                expected_clean = canon_defaults["expected_result"]

        # 6. Business Impact
        impact_clean = enrichments.get("business_impact")
        if not impact_clean:
            if impact and impact.strip() != "Not provided":
                impact_clean = impact.strip()
            elif canonical_bug_id == "ART-AGENT-001":
                impact_clean = (
                    "Structured Agent output can no longer be treated as a reliable contract, "
                    "which can cause downstream workflows or governance steps to process unexpected data."
                )
            elif canon_defaults.get("business_impact"):
                impact_clean = canon_defaults["business_impact"]

        # 7. User Experience
        ux_clean = enrichments.get("user_experience")
        if not ux_clean:
            if ux and ux.strip() != "Not provided":
                ux_clean = ux.strip()
            elif canonical_bug_id == "ART-AGENT-001":
                ux_clean = (
                    "The user configures an explicit output contract expecting ART to preserve "
                    "the configured fields and types. ART currently presents contract-violating "
                    "output as successful, making it difficult for the user to know whether "
                    "downstream automation can safely use the result."
                )
            elif canon_defaults.get("user_experience"):
                ux_clean = canon_defaults["user_experience"]

        # 8. Investigation Guidance
        inv_clean = enrichments.get("investigation_guidance")
        if not inv_clean:
            if inv_guidance and inv_guidance.strip() != "Not provided":
                inv_clean = inv_guidance.strip()
            elif canon_defaults.get("investigation_guidance"):
                inv_clean = canon_defaults["investigation_guidance"]
            else:
                inv_clean = "Not provided"

        # 9. Fix Requirement
        fix_req_clean = enrichments.get("fix_requirement")
        if not fix_req_clean:
            if fix_req and fix_req.strip() != "Not provided":
                fix_req_clean = fix_req.strip()
            elif canon_defaults.get("fix_requirement"):
                fix_req_clean = canon_defaults["fix_requirement"]
            else:
                fix_req_clean = "Not provided"

        # 10. Recommended Solution & Bullets
        rec_sol = enrichments.get("recommended_solution")
        rec_bullets = enrichments.get("implementation_bullets", [])
        if not rec_sol:
            if canonical_bug_id == "ART-AGENT-001":
                rec_sol = (
                    "Enforce structured output as a <strong>server-side schema contract</strong> "
                    "before accepting model responses."
                )
                rec_bullets = []
            elif solution and solution.strip() != "Not provided":
                rec_sol = solution.strip()
            elif canon_defaults.get("recommended_solution"):
                rec_sol = canon_defaults["recommended_solution"]

        # 11. Minimum Working Fix
        mwf = enrichments.get("minimum_working_fix")
        if not mwf:
            if canonical_bug_id == "ART-AGENT-001":
                mwf = (
                    "<strong>Validate the final Agent response against the configured schema "
                    "immediately before ART accepts the result.</strong><br/>"
                    "On validation failure: <strong>Return <code>OUTPUT_VALIDATION_FAILED</code> "
                    "and stop execution before governance.</strong>"
                )
            elif mwf_input and mwf_input.strip() != "Not provided":
                mwf = mwf_input.strip()
            elif canon_defaults.get("minimum_working_fix"):
                mwf = canon_defaults["minimum_working_fix"]
            elif solution and solution.strip() != "Not provided":
                mwf = f"<strong>Apply minimal fix addressing:</strong> {solution}"
            else:
                mwf = f"<strong>Apply minimum working fix for {canonical_bug_id}.</strong>"

        # 12. Acceptance Criteria
        ac = enrichments.get("acceptance_criteria")
        if not ac:
            if ac_input and isinstance(ac_input, list) and ac_input:
                ac = list(ac_input)
            elif canonical_bug_id == "ART-AGENT-001":
                ac = [
                    "Configured property names are preserved.",
                    "Incorrect field types are rejected.",
                    "Collection fields defined as arrays do not pass validation as null.",
                    "Validation failure prevents the Agent Result from reaching governance.",
                    "Validation errors identify the affected field and mismatch reason."
                ]
            elif canon_defaults.get("acceptance_criteria"):
                ac = list(canon_defaults["acceptance_criteria"])

        # 13. Severity & Priority derivation
        existing_sev = ticket.get("severity")
        if existing_sev and existing_sev != "Not provided":
            severity = existing_sev
        else:
            severity = enrichments.get("severity", "HIGH")

        existing_pri = ticket.get("priority")
        if existing_pri and existing_pri != "Not provided":
            pri_str = str(existing_pri).upper()
            if pri_str == "P0":
                priority = 1
            elif pri_str == "P1":
                priority = 2
            elif pri_str == "P2":
                priority = 3
            elif pri_str == "P3":
                priority = 4
            else:
                try:
                    priority = int(existing_pri)
                except (ValueError, TypeError):
                    priority = 2
            pri_rationale = "Preserved from canonical priority."
        else:
            priority = enrichments.get("priority", 2)
            pri_rationale = enrichments.get(
                "priority_rationale",
                "High-priority defect: silent contract violation directly corrupts downstream."
            )

        # 14. Controlled ART Tags
        tags = enrichments.get("tags")
        if not tags:
            if canonical_bug_id == "ART-AGENT-001":
                tags = [
                    "ART",
                    "Agent-Lab",
                    "Structured-Output",
                    "Output-Parser",
                    "Schema-Validation",
                    "Contract-Enforcement",
                    "Governance-Safety"
                ]
            else:
                tags = ["ART"]
                mod = ticket.get("module")
                if mod and mod != "Not provided":
                    tags.append(str(mod).lower())
                for t in ticket.get("tags") or []:
                    t_str = str(t).strip()
                    if t_str and t_str not in tags:
                        tags.append(t_str)

        return DeveloperTicketProjection(
            canonical_bug_id=canonical_bug_id,
            title=title,
            problem=problem,
            what_is_failing=what_is_failing,
            critical_behavior=critical_behavior,
            repro_steps=repro_clean,
            reproduction=repro_clean,
            expected_result=expected_clean,
            expected_behavior=expected_clean,
            actual_result=actual_result_clean,
            observed_behavior=observed_behavior_clean,
            business_impact=impact_clean,
            user_experience=ux_clean,
            investigation_guidance=inv_clean,
            fix_requirement=fix_req_clean,
            recommended_solution=rec_sol,
            implementation_bullets=rec_bullets,
            minimum_working_fix=mwf,
            acceptance_criteria=ac or [],
            severity=severity,
            priority=priority,
            priority_rationale=pri_rationale,
            tags=tags
        )


class ReproStepsFormatter:
    """
    Renders the complete developer-facing structured ticket into clean,
    Azure-compatible HTML across 11 canonical sections for Microsoft.VSTS.TCM.ReproSteps:
    1. Problem
    2. Observed Behavior
    3. Reproduction
    4. Expected Behavior
    5. Business Impact
    6. User Experience
    7. Investigation Guidance
    8. Fix Requirement
    9. Recommended Solution
    10. Minimum Working Fix
    11. Acceptance Criteria
    """

    @classmethod
    def format_html(cls, proj: DeveloperTicketProjection) -> str:
        # Build Observed Behavior representation
        if proj.observed_behavior and proj.observed_behavior.strip() != "Not provided":
            observed_content = proj.observed_behavior.strip()
        elif proj.what_is_failing:
            items_html = "".join(f"<li>{item}</li>" for item in proj.what_is_failing)
            crit_html = f"<p>{proj.critical_behavior}</p>" if proj.critical_behavior else ""
            observed_content = f"<ul>{items_html}</ul>{crit_html}"
        elif proj.actual_result and proj.actual_result.strip() != "Not provided":
            observed_content = proj.actual_result.strip()
        else:
            observed_content = "Not provided"

        # Build Reproduction representation
        repro_content = proj.reproduction or proj.repro_steps or "Not provided"

        # Build Expected Behavior representation
        expected_content = proj.expected_behavior or proj.expected_result or "Not provided"

        # Build Recommended Solution representation
        rec_sol_content = proj.recommended_solution or "Not provided"
        if proj.implementation_bullets:
            bullets_text = "\n".join(f"- {b}" for b in proj.implementation_bullets)
            rec_sol_content = f"{rec_sol_content}\n\n{bullets_text}"

        sections = [
            ("Problem", proj.problem),
            ("Observed Behavior", observed_content),
            ("Reproduction", repro_content),
            ("Expected Behavior", expected_content),
            ("Business Impact", proj.business_impact or "Not provided"),
            ("User Experience", proj.user_experience or "Not provided"),
            ("Investigation Guidance", proj.investigation_guidance or "Not provided"),
            ("Fix Requirement", proj.fix_requirement or "Not provided"),
            ("Recommended Solution", rec_sol_content),
            ("Minimum Working Fix", proj.minimum_working_fix or "Not provided"),
            ("Acceptance Criteria", proj.acceptance_criteria if proj.acceptance_criteria else "Not provided"),
        ]

        html_blocks: List[str] = []
        for header, content in sections:
            html_blocks.append(f"<p><strong>{header}</strong></p>")
            if isinstance(content, str) and (content.startswith("<ul>") or content.startswith("<ol>")):
                html_blocks.append(content)
            else:
                html_blocks.append(_format_section_content_to_html(content))

        return "".join(html_blocks)


class AzureDescriptionFormatter(ReproStepsFormatter):
    """
    Alias for ReproStepsFormatter to ensure seamless backward compatibility.
    """
    pass


class ARTResolutionBriefFormatter:
    """
    Internal projection formatter maintained for offline / repository documentation.
    """

    @classmethod
    def format_html(cls, proj: DeveloperTicketProjection) -> str:
        return AzureDescriptionFormatter.format_html(proj)
