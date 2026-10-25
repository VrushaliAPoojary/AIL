# Markdown → UI Data Contract

The application is a renderer and experimentation system. Research content belongs in Markdown; presentation code consumes normalized data.

## Pipeline

```text
walkthrough.md ─┐
                ├─> document parser ─> normalizer ─> canonical investigation model ─> UI
workflow.md ────┘
```

The current repository paths are `src/data/investigations/AIL-SERVICENOW-01.md` for the walkthrough/investigation record and `src/data/workflow.md` for the workflow. There is currently no root-level `walkthrough.md`; a future source can use that conventional name without changing the model.

## Separate input contracts

### Walkthrough Markdown

The walkthrough is an investigation/reasoning record. It may contain an identity table, narrative sections, progression headings, evidence registers, claims, inferences, hypotheses, experiments, results, decisions, unknowns, contradictions, and source registers. The parser preserves headings and raw section content, then derives variable-count walkthrough nodes from meaningful sections. It does not assume a fixed number or order of stages.

### Workflow Markdown

The workflow is an executable/experimental specification. Each `## NODE` block may provide `node_id`, `node_type`, `title`, `purpose`, `input`, `operation`, `ai_capability`, `automation_capability`, `human_involvement`, `decision_logic`, `output` or `expected_output`, `failure_condition`, `research_basis`, `next`, `status`, and `demo_behavior` or `demo_interaction`. Fields are optional in the source; absent values normalize to `null` and are reported as unknown rather than invented.

## Canonical model

`src/types/markdownContract.ts` defines the normalized model. It keeps walkthrough and workflow nodes distinct while sharing `ResearchStatus`, `Provenance`, fragments, and graph relationships. Every research-bearing object has document/path, section, source identifier where available, excerpt, and line-range provenance.

Statuses are controlled by `CONTROLLED_RESEARCH_STATUSES`: `UNKNOWN`, `UNVERIFIED`, `PENDING`, `ACTIVE`, `PASSED`, `FAILED`, `BLOCKED`, `SURVIVED`, and `KILLED`. Source values outside that vocabulary are normalized conservatively and retained as `sourceStatus`; for example, `DRAFT` becomes `UNKNOWN`, `VERIFIED` becomes `PASSED`, and `KILL` becomes `KILLED`.

Relationships are an explicit variable-length collection. Workflow `next` values become `NEXT` relationships, while progression sections become `SEQUENCE` relationships. Unknown relationship targets remain visible to validation and are never silently removed.

## Parser API

`src/data/markdownContract.ts` exposes:

- `parseWalkthroughMarkdown(input)`
- `parseWorkflowMarkdown(input)`
- `normalizeInvestigation(walkthrough, workflow)`
- `validateCanonicalInvestigation(model)`

The UI should consume the result of these functions and should not read raw Markdown or encode investigation-specific fields in components.
