# Phase 07-0E Test Safety Net

## Test classification

| AOI Test | Classification | Reason |
| --- | --- | --- |
| `compiler/core/tests/test_compiler_core.py` | MIGRATE_NOW | Core compiler semantics, parser/normalizer, epistemic rules, and firewall assertions run without the full AOI corpus. |
| `compiler/core/tests/test_integration.py` | MIGRATE_NOW | End-to-end compiler integration can run from a self-contained temp fixture. |
| `compiler/core/tests/test_real_corpus_stress.py` | MIGRATE_LATER_WITH_CORPUS | Requires `AOI/opportunities/` real corpus coverage. |
| `compiler/core/tests/test_v1_2_schema.py` | MIGRATE_NOW | Contract/schema validation can run against the repaired AIL schema. |
| `compiler/tests/test_compiler.py` | MIGRATE_NOW | Loader, extraction-package, and validator coverage can run with temp fixtures and a known-good local JSON sample. |
| `compiler/tests/test_extraction_spec.py` | MIGRATE_NOW | Spec coverage can run with a local generated `artifacts/` fixture and the existing prompt. |

## Tests migrated

- `AOI/compiler/core/tests/test_compiler_core.py` -> `AIL/compiler/core/tests/test_compiler_core.py`
- `AOI/compiler/core/tests/test_integration.py` -> `AIL/compiler/core/tests/test_integration.py`
- `AOI/compiler/core/tests/test_v1_2_schema.py` -> `AIL/compiler/core/tests/test_v1_2_schema.py`
- `AOI/compiler/tests/test_compiler.py` -> `AIL/compiler/tests/test_compiler.py`
- `AOI/compiler/tests/test_extraction_spec.py` -> `AIL/compiler/tests/test_extraction_spec.py`
- New migration-specific contract test: `AIL/compiler/core/tests/test_contract_authority_repair.py`

## Test modifications

- `compiler/core/tests/test_compiler_core.py`: IMPORT PATH, CONTRACT-COMPATIBILITY
- `compiler/core/tests/test_integration.py`: IMPORT PATH, FIXTURE PATH, CONTRACT-COMPATIBILITY
- `compiler/core/tests/test_v1_2_schema.py`: IMPORT PATH, SCHEMA PATH, FIXTURE PATH, CONTRACT-COMPATIBILITY
- `compiler/tests/test_compiler.py`: IMPORT PATH, FIXTURE PATH, CONTRACT-COMPATIBILITY
- `compiler/tests/test_extraction_spec.py`: FIXTURE PATH, CONTRACT-COMPATIBILITY
- `compiler/core/tests/test_contract_authority_repair.py`: new focused contract proof using existing models/mapper

## Deferred tests

- `compiler/core/tests/test_real_corpus_stress.py` remained deferred because it depends on the AOI real corpus and should not be forced into AIL in this run.

## Results

- `PASSED`: 22 migrated tests executed successfully.
- `FAILED`: 0 migrated tests.
- `SKIPPED`: 0 migrated tests.
- `DEFERRED`: `compiler/core/tests/test_real_corpus_stress.py`.
