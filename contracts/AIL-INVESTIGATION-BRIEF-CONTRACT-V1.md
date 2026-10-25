# AIL Investigation Brief Contract v1

## 1. Authority
This document defines the canonical AIL Investigation Brief contract. The authoritative transport format is structured `InvestigationBrief` JSON, validated against `contracts/AIL-INVESTIGATION-BRIEF-JSON-SCHEMA-V1.json` and the matching TypeScript and runtime validators. Markdown remains a supported input/resource format, but it is not the system-to-system contract.

## 2. Purpose
The contract preserves research semantics, provenance, and traceability while allowing AIL to normalize AOI research into the presentation-ready view model. The UI must not infer facts, upgrade epistemic status, or weaken provenance.

## 3. Contract Boundaries
AIL validates and presents structured research. AOI or the compiler layer provides the research semantics. The UI consumes the normalized object and must not parse Markdown as transport.

## 4. Canonical Object Set
The canonical brief contains these object families:
- identity and decision metadata
- sources and provenance
- checkpoints
- evidence, claims, inferences, hypotheses, results
- workflows, sections, and relationships
- optional falsification and reusable intelligence
- traceability

## 5. Required Structural Rules
- `investigation_id`, `company`, `opportunity`, `investigation_type`, `research_status`, `primary_question`, `presentation`, `decision`, `sources`, `checkpoints`, `evidence`, `claims`, `inferences`, `hypotheses`, `results`, and `traceability` are required at the root.
- `decision.reusable_intelligence` is a structured array of intelligence objects.
- `workflows`, `sections`, `relationships`, and `falsification` are supported optional structures.
- Checkpoints require `id`, `title`, `what_changed`, and `provenance`; other checkpoint fields may be present as optional supporting detail.

## 6. Provenance
Every semantic object carries provenance. Provenance records source file, section, line span, and optional URL context so the compiler and validator can preserve evidence references without inventing new facts.

## 7. Controlled Vocabulary
The contract uses controlled enums for workflow and relationship types and preserves UNKNOWN where the source is unresolved. AIL must not convert UNKNOWN into FALSE, NO, VERIFIED, or FACT.

## 8. Validation Rules
Validation is schema-first and semantics-aware. The schema, TypeScript types, runtime validator, and compiler validation models must agree on the same contract authority. Divergence is treated as a migration defect, not normalized away in the UI.

## 9. Legacy Preservation
Existing AIL presentation components, loaders, and contract files remain in place until the compiled JSON path fully covers their behavior. This document does not deprecate those paths.
