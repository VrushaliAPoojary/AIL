# Phase 07-0F Corpus + Loader Proof

## Scope
Imported the minimum representative AOI research corpus needed for OPP-001, OPP-006, and OPP-008 into AIL-local `research/imported/` paths and proved the AIL-only pipeline from local Markdown to validated InvestigationBrief JSON.

## Corpus imported

- `research/imported/Healthcare_and_Pharmaceuticals/Baby_Memorial_Hospital_Kozhikode/opportunity - 01/`
- `research/imported/IT_and_Business_Services/servicenow/opportunity06/`
- `research/imported/IT_and_Business_Services/servicenow/opportunity08/`

## Compiled outputs

- `src/data/investigations/imported/Healthcare_and_Pharmaceuticals/Baby_Memorial_Hospital_Kozhikode/opportunity - 01/OPP-001.json`
- `src/data/investigations/imported/IT_and_Business_Services/servicenow/opportunity06/OPP-006.json`
- `src/data/investigations/imported/IT_and_Business_Services/servicenow/opportunity08/OPP-008.json`

## Migrated test

- `compiler/core/tests/test_real_corpus_stress.py`

### Test classification

| AOI Test | Classification | Reason |
| --- | --- | --- |
| `compiler/core/tests/test_real_corpus_stress.py` | MIGRATE_NOW | Runs against the AIL-local imported corpus without requiring the full AOI repository at runtime. |

## Test modifications

- `compiler/core/tests/test_real_corpus_stress.py`: updated corpus paths to `research/imported/` and kept semantic assertions intact.

## Loader proof

- Validated the compiled briefs with the AIL TypeScript validator path used by the loader.
- Confirmed the AIL production build still succeeds with the imported JSON briefs under the loader glob.

## Results

- `PASSED`: migrated real-corpus stress test, AIL validator check, production build.
- `FAILED`: none.
- `SKIPPED`: none.
- `DEFERRED`: corpus expansion beyond the representative source set was not attempted in this run.
