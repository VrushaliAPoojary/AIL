# Phase 07-0C Compiler Migration

This document records the compiler implementation migration from AOI into AIL.

## Copied compiler implementation

Copied from AOI into the matching AIL paths:

- `compiler/main.py`
- `compiler/core/change_detection.py`
- `compiler/core/compiler_main.py`
- `compiler/core/firewall.py`
- `compiler/core/ir.py`
- `compiler/core/mapper.py`
- `compiler/core/normalizer.py`
- `compiler/core/parser.py`
- `compiler/core/resolver.py`
- `compiler/core/validator.py`
- `compiler/input/loader.py`
- `compiler/output/writer.py`
- `compiler/validation/models.py`
- `compiler/validation/validator.py`
- `compiler/extraction/interface.py`
- `compiler/extraction/registry.py`
- `compiler/extraction/gemini.py`
- `compiler/extraction/prompts/investigation_brief_v1.txt`

## Preserved AIL structure

The existing AIL application structure was not modified:

- `src/`
- `public/`
- `contracts/`
- `docs/repository-current-state.md`
- `docs/ai-development-protocol.md`
- `docs/migration/aoi-to-ail-migration-map.md`
- `docs/migration/phase-07-0b-structure.md`

The Markdown UI and presentation components remain operational and untouched in this run.

## Contract authority

The existing AIL contract targets remain authoritative:

- `contracts/AIL-INVESTIGATION-BRIEF-JSON-SCHEMA-V1.json`
- `contracts/AIL-INVESTIGATION-BRIEF-CONTRACT-V1.md`

No contract reconciliation was attempted in this run.

## Direct runtime dependency notes

The copied compiler implementation keeps the AOI package semantics intact.

Observed direct local dependencies stayed within the compiler package:

- `compiler/main.py` depends on the compiler input, extraction, validation, and output packages.
- `compiler/core/*.py` depend on `compiler.core.ir` and the local parser/normalizer/resolver/validator stages.
- `compiler/input/loader.py` depends on `compiler.extraction.interface`.
- `compiler/extraction/*.py` depend on `compiler.extraction.interface` and `compiler.validation.models`.
- `compiler/output/writer.py` is standalone apart from the Python standard library.
- `compiler/validation/*.py` depend on `compiler.validation.models` and Pydantic.

No AOI corpus, AOI UI, or AOI contract files were copied.

## Expected next step

Run 4 should reconcile the migrated compiler output with the authoritative AIL contract without altering the preserved UI paths.
