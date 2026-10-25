# AOI → AIL Migration Map

Run 1 inventory only. Read-only analysis, with this document as the only write.

## Scope

This map covers the consolidation path from the AOI repository into AIL for Phase 07-0.

It separates:

- compiler capability
- contract/schema support
- research corpus
- current AIL presentation stack
- legacy Markdown handoff material

It does not migrate code in this run.

## Current AOI Architecture

### Top-level shape

Relevant AOI roots:

- `compiler/`
- `contracts/`
- `docs/`
- `opportunities/`
- `JSON Data/`
- `outreach/`
- `src/`
- `tests/`
- `WALKTHROUGH.md`
- `REGISTRY.md`
- `prompt.md`

### What lives where

- `compiler/` contains the mature Python compiler pipeline.
- `compiler/core/` contains parser, IR, normalizer, resolver, firewall, change detection, validator, and compiler mapping logic.
- `compiler/input/` contains the package loader.
- `compiler/extraction/` contains the provider abstraction, Gemini provider, registry, and prompt.
- `compiler/output/` contains JSON and failure writers.
- `compiler/validation/` contains the Pydantic contract model and validator.
- `contracts/` contains AOI contract and schema artifacts.
- `opportunities/`, `JSON Data/`, `WALKTHROUGH.md`, `REGISTRY.md`, and `outreach/` are the research corpus and registry/history surface.
- `src/` contains the older AOI semantic/runtime support layer, including ingestion, semantic models, runner, providers, capabilities, and demos.
- `tests/` contains compiler regression, schema, stress, and product regression tests.

### AOI compiler intent

AOI already has the full pipeline boundary the migration wants:

`Markdown corpus -> loader -> parser -> IR -> normalizer -> resolver/firewall/change detection -> validator -> schema mapping -> JSON output`

The extraction provider is downstream of that pipeline and is a dependency, not the semantic source.

## Current AIL Architecture

### Top-level shape

Relevant AIL roots:

- `src/`
- `contracts/`
- `scripts/`
- `docs/`
- `public/`
- `deployment/`

### What lives where

- `src/data/investigationBriefLoader.ts` loads JSON briefs from `src/data/investigations/**/*.json`.
- `src/data/investigationBriefValidator.ts` validates the current InvestigationBrief payload shape.
- `src/types/investigationBrief.ts` defines the current InvestigationBrief TypeScript model.
- `src/types/markdownContract.ts` and `src/features/core/walkthrough/MarkdownRenderer.tsx` represent the current Markdown-based presentation pipeline.
- `src/features/core/walkthrough/` renders walkthrough/presentation content.
- `src/features/core/workflow/` renders workflow presentation.
- `src/features/aoi/` renders the AOI explorer surface.
- `contracts/` already contains AIL-specific contract/schema documents.
- `scripts/` contains validation and packaging helpers.

### Current AIL dependency posture

AIL is already a UI application that consumes normalized brief JSON and renders presentation surfaces.

It still contains a Markdown parsing/presentation stack that is legacy relative to the Phase 07 consolidation target.

## Dependency Graph

```text
AOI research corpus
  -> compiler/input/loader.py
  -> compiler/core/parser.py
  -> compiler/core/ir.py
  -> compiler/core/normalizer.py
  -> compiler/core/resolver.py
  -> compiler/core/firewall.py
  -> compiler/core/change_detection.py
  -> compiler/core/validator.py
  -> compiler/core/mapper.py
  -> compiler/validation/models.py
  -> compiler/validation/validator.py
  -> compiler/output/writer.py
  -> compiled InvestigationBrief JSON
  -> AIL loader / validator / types
  -> AIL UI presentation
```

```text
AOI extraction prompt + provider registry
  -> compiler/extraction/interface.py
  -> compiler/extraction/registry.py
  -> compiler/extraction/gemini.py
  -> compiler/extraction/prompts/investigation_brief_v1.txt
```

```text
AIL legacy Markdown path
  -> src/types/markdownContract.ts
  -> src/data/README.md
  -> src/features/core/walkthrough/MarkdownRenderer.tsx
  -> src/features/core/walkthrough/Presentation.tsx
  -> src/features/core/walkthrough/Walkthrough.tsx
  -> src/features/aoi/AOIExplorer.tsx
```

## Exact File Migration Table

| Source | Destination | Classification | Dependencies | Risk | Reason |
|---|---|---|---|---|---|
| `compiler/main.py` | `compiler/main.py` in AIL | MIGRATE | `compiler/input/loader.py`, `compiler/extraction/registry.py`, `compiler/validation/validator.py`, `compiler/output/writer.py` | Medium | Main compiler entrypoint for the mature AOI pipeline. |
| `compiler/core/parser.py` | `compiler/core/parser.py` in AIL | MIGRATE | Markdown corpus, provenance handling | High | Core semantic parser required by the compiler. |
| `compiler/core/ir.py` | `compiler/core/ir.py` in AIL | MIGRATE | parser, normalizer, resolver, validator | High | IR is the structural bridge between raw research and frozen output. |
| `compiler/core/normalizer.py` | `compiler/core/normalizer.py` in AIL | MIGRATE | parser, IR | High | Converts parsed Markdown structures into semantic IR. |
| `compiler/core/resolver.py` | `compiler/core/resolver.py` in AIL | MIGRATE | IR, provenance, ID graph | High | Resolves references and relationships. |
| `compiler/core/firewall.py` | `compiler/core/firewall.py` in AIL | MIGRATE | IR, extraction tokens | Medium | Removes temporary tool references and keeps provenance clean. |
| `compiler/core/change_detection.py` | `compiler/core/change_detection.py` in AIL | MIGRATE | IR stable IDs, previous compilation snapshots | Medium | Needed for deterministic recompile/change tracking. |
| `compiler/core/validator.py` | `compiler/core/validator.py` in AIL | MIGRATE | IR, schema rules, epistemic rules | High | Validates semantic and structural integrity before output. |
| `compiler/core/mapper.py` | `compiler/core/mapper.py` in AIL | MIGRATE | IR, contract model, validation model | High | Maps compiler IR to the frozen InvestigationBrief output. |
| `compiler/core/compiler_main.py` | `compiler/core/compiler_main.py` in AIL | MIGRATE | parser, normalizer, resolver, firewall, change detection, validator, mapper | High | Orchestrates the compiler stages end to end. |
| `compiler/input/loader.py` | `compiler/input/loader.py` in AIL | MIGRATE | filesystem, corpus layout, package hashing | High | Discovers and normalizes the input package. |
| `compiler/validation/models.py` | `compiler/validation/models.py` in AIL | MIGRATE | JSON schema contract, pydantic | High | Defines the structured output model used by validation. |
| `compiler/validation/validator.py` | `compiler/validation/validator.py` in AIL | MIGRATE | validation models, reference graph | High | Enforces schema and cross-reference integrity. |
| `compiler/output/writer.py` | `compiler/output/writer.py` in AIL | MIGRATE | output directories, atomic writes | Medium | Persists valid output and failure records. |
| `compiler/extraction/interface.py` | `compiler/extraction/interface.py` in AIL | MIGRATE | compiler entrypoint, provider abstraction | Medium | Defines the provider contract used by the compiler. |
| `compiler/extraction/registry.py` | `compiler/extraction/registry.py` in AIL | MIGRATE | provider implementations | Medium | Selects extraction provider implementations. |
| `compiler/extraction/gemini.py` | `compiler/extraction/gemini.py` in AIL | MIGRATE | provider API, environment keys, extraction prompt | Medium | AOI extraction provider implementation. |
| `compiler/extraction/prompts/investigation_brief_v1.txt` | `compiler/extraction/prompts/investigation_brief_v1.txt` in AIL | MIGRATE | AOI compiler prompt | Medium | Prompt is part of the compiler semantics, not UI behavior. |
| `compiler/core/tests/test_compiler_core.py` | `compiler/core/tests/test_compiler_core.py` in AIL | MIGRATE | compiler core | Medium | Core stage coverage must move with the compiler. |
| `compiler/core/tests/test_integration.py` | `compiler/core/tests/test_integration.py` in AIL | MIGRATE | compiler core, fixtures | Medium | End-to-end compiler verification. |
| `compiler/core/tests/test_real_corpus_stress.py` | `compiler/core/tests/test_real_corpus_stress.py` in AIL | MIGRATE | real corpus fixtures | High | Stress test for real Markdown corpus behavior. |
| `compiler/core/tests/test_v1_2_schema.py` | `compiler/core/tests/test_v1_2_schema.py` in AIL | MIGRATE | schema contract, mapper | High | Verifies schema mapping and contract fidelity. |
| `compiler/tests/test_compiler.py` | `compiler/tests/test_compiler.py` in AIL | MIGRATE | compiler package, extraction path | Medium | Compiler regression coverage. |
| `compiler/tests/test_extraction_spec.py` | `compiler/tests/test_extraction_spec.py` in AIL | MIGRATE | extraction provider boundary | Medium | Provider/extraction specification coverage. |
| `contracts/InvestigationBrief.schema.json` | `contracts/AIL-INVESTIGATION-BRIEF-JSON-SCHEMA-V1.json` already exists | REPLACE | AIL schema contract | High | AIL already has its locked schema; do not duplicate blindly. |
| `contracts/InvestigationBrief-contract-v1.md` | `contracts/AIL-INVESTIGATION-BRIEF-CONTRACT-V1.md` already exists | REPLACE | AIL contract doc | High | Equivalent contract documentation already exists in AIL. |
| `contracts/INVESTIGATION-BRIEF-COMPILER-CONTRACT-V1.md` | `contracts/INVESTIGATION-BRIEF-COMPILER-CONTRACT-V1.md` in AIL history only | LEGACY/HANDOFF ONLY | historical compiler boundary | Medium | Useful history, but not the runtime transport contract. |
| `contracts/AOI-AIC-REQUEST-TEMPLATE.md` | none | LEGACY/HANDOFF ONLY | AOI intake flow | Low | Only used for AOI handoff/request generation. |
| `contracts/AOI-AIL-INVESTIGATION-INTAKE-TEMPLATE.md` | none | LEGACY/HANDOFF ONLY | AOI intake flow | Low | Only used for AOI to AIL Markdown intake handoff. |
| `src/aoi_semantic_model.py` | none | KEEP IN AOI HISTORY | AOI legacy semantic runtime | Medium | Historical AOI semantic model, not part of the compiler migration. |
| `src/aoi_ingestion.py` | none | KEEP IN AOI HISTORY | legacy ingestion model | Medium | Older AOI ingestion path; not the compiler core. |
| `src/models.py` | none | KEEP IN AOI HISTORY | AOI runtime support | Medium | Legacy runtime contracts for AOI-specific execution. |
| `src/interfaces.py` | none | KEEP IN AOI HISTORY | AOI runtime support | Medium | Runtime interfaces for AOI tooling. |
| `src/providers.py` | none | KEEP IN AOI HISTORY | AOI runtime support | Medium | Mock provider/runtime support, not the compiler core. |
| `src/capabilities.py` | none | KEEP IN AOI HISTORY | AOI runtime support | Medium | Capability simulation layer, not the compiler core. |
| `src/runner.py` | none | KEEP IN AOI HISTORY | AOI runtime support | Medium | Workflow runner runtime support. |
| `src/demo/demo.py` | none | KEEP IN AOI HISTORY | demo runtime support | Low | Demo helper, not migration target. |
| `src/demo/demo_capability.py` | none | KEEP IN AOI HISTORY | demo runtime support | Low | Demo helper, not migration target. |
| `src/capabilities/*.md` | none | KEEP IN AOI HISTORY | AOI capability registry docs | Low | Historical capability notes only. |
| `opportunities/**/OPP-*.md` | none | KEEP IN AOI HISTORY | research corpus | High | Research source corpus stays in AOI. |
| `JSON Data/industries/**/OPP-*.json` | none | KEEP IN AOI HISTORY | research corpus | High | Normalized corpus artifacts stay in AOI. |
| `WALKTHROUGH.md` | none | KEEP IN AOI HISTORY | presentation corpus | High | Canonical research walkthrough content stays in AOI. |
| `REGISTRY.md` | none | KEEP IN AOI HISTORY | opportunity registry | High | Historical registry remains in AOI. |
| `outreach/TARGETED-DIRECT-OUTREACH-QUEUE.md` | none | KEEP IN AOI HISTORY | outreach corpus | Low | Operational history only. |
| `tests/test_aoi_ingestion.py` | none | KEEP IN AOI HISTORY | AOI ingestion runtime | Medium | Tests the AOI ingestion path, not the compiler migration. |
| `tests/test_phase_06_traceability.py` | none | KEEP IN AOI HISTORY | phase 06 presentation contract | Medium | Retain as history unless a later phase explicitly migrates it. |
| `tests/test_foundation.py` | none | KEEP IN AOI HISTORY | repo foundation | Low | Repository process test, not compiler capability. |
| `tests/test_pilot_readiness.py` | none | KEEP IN AOI HISTORY | product/regression surface | Low | Product regression, not compiler capability. |

## Research Corpus Inventory

### AOI research corpus

This corpus stays in AOI and feeds the compiler:

- `opportunities/`
- `JSON Data/`
- `WALKTHROUGH.md`
- `REGISTRY.md`
- `outreach/`
- `prompt.md`

### Corpus characteristics

- Markdown files under `opportunities/` are the primary raw research input.
- `JSON Data/` holds normalized or precompiled JSON artifacts for historical/reference use.
- `WALKTHROUGH.md` and `REGISTRY.md` are legacy presentation/history surfaces and should not be confused with the AIL transport contract.
- Corpus files remain the source material; they are not UI-ready transport.

## Tests That Must Migrate

Compiler tests that should move with the compiler capability:

- `compiler/core/tests/test_compiler_core.py`
- `compiler/core/tests/test_integration.py`
- `compiler/core/tests/test_real_corpus_stress.py`
- `compiler/core/tests/test_v1_2_schema.py`
- `compiler/tests/test_compiler.py`
- `compiler/tests/test_extraction_spec.py`

Tests that should remain in AOI history:

- `tests/test_aoi_ingestion.py`
- `tests/test_phase_06_traceability.py`
- `tests/test_pilot_readiness.py`
- `tests/test_foundation.py`
- opportunity-specific product regression tests under `tests/test_*.py`

## Dependencies Required by the Compiler

Required runtime and structural dependencies:

- filesystem package loading from `compiler/input/loader.py`
- parser / IR / normalizer / resolver / firewall / change detection pipeline
- Pydantic validation models in `compiler/validation/models.py`
- schema/reference validation in `compiler/validation/validator.py`
- extraction provider abstraction and registry
- Gemini provider implementation and the extraction prompt
- atomic output writing
- source corpus directory layout under `opportunities/`

External or environment dependencies:

- Python runtime
- Google Gemini API access for live extraction
- local corpus file access

## Handoff-Only Components To Retire

These components exist primarily for the retired Markdown handoff path and should not become the new transport contract:

- `contracts/AOI-AIC-REQUEST-TEMPLATE.md`
- `contracts/AOI-AIL-INVESTIGATION-INTAKE-TEMPLATE.md`
- `src/types/markdownContract.ts`
- `src/data/README.md`
- `src/features/core/walkthrough/MarkdownRenderer.tsx`
- `src/features/core/walkthrough/Presentation.tsx`
- `src/features/core/walkthrough/Walkthrough.tsx`
- `src/features/aoi/AOIExplorer.tsx`
- any runtime path that parses Markdown directly inside the UI as transport

## Recommended AIL Destination Structure

Keep AIL's existing UI structure intact and add the minimum receiving surface needed for the migrated compiler capability.

Recommended structure:

- `compiler/` for the migrated Python compiler package
- `compiler/core/` for parser, IR, normalizer, resolver, firewall, change detection, validator, and mapper
- `compiler/input/` for package loading
- `compiler/extraction/` for provider abstraction and prompt
- `compiler/output/` for persisted compiler output
- `compiler/validation/` for the structured output model and validator
- `contracts/` for the locked AIL contract/schema docs
- `src/data/investigations/` for compiled InvestigationBrief JSON inputs to the UI
- `docs/migration/` for migration notes and phase tracking
- `tests/` or `compiler/tests/` for compiler and contract regression coverage

## Exact Sequence For Runs 2-7

1. Run 2: prepare the minimum AIL receiving structure only.
2. Run 3: migrate the investigation compiler implementation and internal dependencies.
3. Run 4: migrate or wire the InvestigationBrief contract/schema boundary.
4. Run 5: migrate research corpus wiring and compiled brief ingestion paths.
5. Run 6: migrate UI/view-model consumption of the compiled briefs and remove direct Markdown transport dependence.
6. Run 7: execute the full regression suite and stabilize remaining gaps.

## Notes

- AIL already has its own locked contract and JSON loader/validator stack.
- The current AIL Markdown pipeline is legacy relative to the Phase 07 transport target.
- AOI corpus and history should be preserved until AIL is independently functional.
