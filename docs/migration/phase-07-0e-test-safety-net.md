# Phase 07-0E Test Safety Net

## Scope
Migrate the mature compiler regression tests that can run inside AIL without the full AOI research corpus. The compiler implementation itself was not re-migrated in this run.

## Classification
### MIGRATE_NOW
- `compiler/core/tests/test_compiler_core.py`
- `compiler/core/tests/test_integration.py`
- `compiler/core/tests/test_v1_2_schema.py`
- `compiler/tests/test_compiler.py`
- `compiler/tests/test_extraction_spec.py`
- `compiler/core/tests/test_contract_authority_repair.py` (new migration-specific contract test)

### MIGRATE_LATER_WITH_CORPUS
- `compiler/core/tests/test_real_corpus_stress.py`

### Deferred / not copied
- Corpus-backed stress coverage that depends on `AOI/opportunities/`

## Files Created
- `compiler/core/tests/__init__.py`
- `compiler/core/tests/test_compiler_core.py`
- `compiler/core/tests/test_integration.py`
- `compiler/core/tests/test_v1_2_schema.py`
- `compiler/core/tests/test_contract_authority_repair.py`
- `compiler/tests/__init__.py`
- `compiler/tests/test_compiler.py`
- `compiler/tests/test_extraction_spec.py`
- `artifacts/investigation-brief-extraction-spec-v1.md`

## Preserved Boundaries
- AIL UI architecture remains untouched.
- No AOI corpus was copied.
- No realtime, collaboration, or backend work was introduced.
- The repaired contract authority remains unchanged.

## Expected Outcome
The migrated compiler safety net should validate the preserved semantics of the receiving compiler package without requiring the full AOI corpus.
