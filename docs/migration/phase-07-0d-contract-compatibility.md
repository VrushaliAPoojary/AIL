# Phase 07-0D Contract Compatibility

Compatibility run for the migrated AOI compiler against AIL's authoritative InvestigationBrief contract.

## Compatibility matrix

| Area | Compiler Model | Mapper Output | AIL Schema | TS Model | Result |
| --- | --- | --- | --- | --- | --- |
| Root identity | Partial native support in `Investigation` (`id`, `title`); other identity fields are synthesized by the mapper | Serializes `investigation_id`, `company`, `opportunity`, `investigation_type`, `research_status`, `primary_question`, and `industry` | Requires root identity fields but does not define `industry` | Requires `investigation_id`, `company`, `industry`, `opportunity`, `investigation_type`, `research_status`, `presentation`, `decision`, `primary_question` | GAP |
| Checkpoints | Native `Checkpoint` objects exist | Serializes checkpoint objects, but uses `tested`, `found`, `what_changed`, `resulting_state`, `evidence_refs`, `source_refs` | Requires `id`, `what_changed`, `evidence`, `result`, `provenance` | Requires `id`, `title`, `status`, `investigation_question`, `tested`, `found`, `what_changed`, `resulting_state`, `evidence_refs`, `source_refs`, `provenance` | GAP |
| Sections | Native `Section` objects exist | Serializes `sections` array | Not present | Not present | LEGACY FIELD |
| Evidence | Native `Evidence` objects exist | Serializes `evidence` with `id`, `statement`, `classification`, `source`, `provenance` | Requires `id`, `statement`, `classification`, `source`, `provenance` | Matches the same shape | COMPATIBLE |
| Workflows | Native `WorkflowModel` objects exist | Serializes `workflows` with `workflow_type`, `steps`, and provenance | Not present | Not present | LEGACY FIELD |
| Workflow steps | Native `WorkflowStep` objects exist | Serializes step-level evidence and provenance | Not present | Not present | LEGACY FIELD |
| Relationships | Native `Relationship` objects exist | Serializes `relationships` with `source_id`, `target_id`, `relationship_type` | Not present | Not present | GAP |
| Decisions | Native `Decision` objects exist | Serializes `decision`, `reason`, `reusable_intelligence`, `provenance` | Requires `decision`, `reason`, `reusable_intelligence`, `provenance` but models `reusable_intelligence` as `string` | Requires `reusable_intelligence` as `IntelligenceObject[]` | GAP |
| Provenance | Native provenance stores file + section + position | Mapper converts to `source_file`, `section`, `line_start`, `line_end` | Requires `source_file`, `section`, `line_start`, `line_end` | Requires `source_file`, `section`, `line_start`, `line_end` | COMPATIBLE |
| Epistemic state | Preserves distinct AOI states: `VERIFIED`, `DIRECT`, `OBSERVED`, `TRIANGULATED`, `RECONSTRUCTED`, `INFERRED`, `HYPOTHESIS`, `PROPOSED`, `UNKNOWN`, `UNVERIFIED` | Serializes the raw compiler status into `classification` for evidence and keeps workflow types separate in the IR | Evidence classification is unconstrained string; other epistemic values are not modeled as dedicated enums | TS model keeps controlled research statuses, but not the full AOI epistemic enum set | GAP |
| Workflow type | Preserves `OBSERVED_EXISTING`, `RECONSTRUCTED`, `PROPOSED_ART` | Mapper emits `OBSERVED`, `RECONSTRUCTED`, `PROPOSED_ART` | Workflows are not represented | Not represented | LEGACY FIELD |

## Validation executed

Targeted checks completed:

- `python3 -m compileall compiler`
- import smoke for `compiler`, `compiler.core.*`, `compiler.input.loader`, `compiler.output.writer`, `compiler.validation.*`
- representative mapped brief generation with `ContractMapper`
- Draft-07 schema validation against `contracts/AIL-INVESTIGATION-BRIEF-JSON-SCHEMA-V1.json`

## Representative mapped object validation

Validation was run on a synthetic `Investigation` object with a checkpoint, evidence, source, and workflow.

Schema validation errors:

- `$.checkpoints[0]: 'evidence' is a required property`
- `$.checkpoints[0]: 'result' is a required property`
- `$.decision.reusable_intelligence: [] is not of type 'string'`

## Contract mismatches found

1. `decision.reusable_intelligence` is a semantic conflict between the authoritative AIL JSON Schema and the authoritative TypeScript/runtime validator shape.
2. The migrated compiler preserves richer checkpoint semantics than the AIL JSON Schema can represent.
3. `workflows`, `sections`, and `relationships` are preserved by the compiler, but they are not represented in the authoritative AIL schema or TypeScript model.
4. Workflow type distinctions are preserved in the compiler, but the authoritative AIL schema does not model workflows at all.

## Result

PHASE 07-0D BLOCKED - CONTRACT GAP IDENTIFIED.

The migrated compiler can be imported and compiled, but the representative mapped output does not validate against the authoritative AIL JSON Schema without dropping or rewriting preserved semantics.

## Deferred issues

- Reconcile the authoritative AIL schema with the runtime validator/TypeScript model before any semantic adapter changes.
- Decide whether AIL should adopt workflow/relationship containers at the contract level or keep them compiler-only.
- Resolve the `decision.reusable_intelligence` shape conflict without collapsing reusable intelligence semantics.

## Recommended Run 5 inputs

- `docs/migration/phase-07-0d-contract-compatibility.md`
- `contracts/AIL-INVESTIGATION-BRIEF-JSON-SCHEMA-V1.json`
- `contracts/AIL-INVESTIGATION-BRIEF-CONTRACT-V1.md`
- `src/types/investigationBrief.ts`
- `src/data/investigationBriefValidator.ts`
- `compiler/core/mapper.py`
- `compiler/validation/models.py`
