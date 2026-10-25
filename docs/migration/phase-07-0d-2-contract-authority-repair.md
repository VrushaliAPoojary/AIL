# Phase 07-0D-2 Contract Authority Repair

## Scope
Repair the AIL contract authority so the canonical JSON Schema, TypeScript model, runtime validator, and compiler validation model agree on the same Investigation Brief structure. No UI, loader, or presentation architecture changes were made.

## Files Updated
- `contracts/AIL-INVESTIGATION-BRIEF-JSON-SCHEMA-V1.json`
- `src/types/investigationBrief.ts`
- `src/data/investigationBriefValidator.ts`
- `compiler/validation/models.py`
- `compiler/validation/validator.py`
- `compiler/core/mapper.py`
- `contracts/AIL-INVESTIGATION-BRIEF-CONTRACT-V1.md`

## Contract Authority Decision
AIL contract authority now rests on the structured `InvestigationBrief` JSON schema and matching runtime/compiler models. Markdown remains a supported input/resource format, but it is not the transport contract between compiler and UI.

## Compatibility Notes
- `Decision.reusable_intelligence` is modeled as a structured array.
- Checkpoints no longer require the legacy `evidence` and `result` pair from the outdated schema wording.
- Optional workflow, section, relationship, and falsification structures are preserved for future compiler output.
- Provenance now supports optional URL context.

## Validation Summary
The repaired schema/model surface was smoke-tested with compiler imports and structural validation. A representative mapped investigation was validated against the repaired schema after the model updates.

## Deferred Work
Run 5 should focus on migrating the mature AOI compiler capability into the receiving `compiler/` structure and proving end-to-end contract compatibility with real research content.
