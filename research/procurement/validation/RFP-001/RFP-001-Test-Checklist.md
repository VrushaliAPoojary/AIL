# RFP-001 — ART Test Execution & Scoring

**Run status:** NOT EXECUTED

## Setup
1. Create or select a disposable Agent Lab agent for the test.
2. Use `RFP-001-ART-Agent-Prompt.md` as the agent instruction.
3. Supply the entire `RFP-001-Test-Document.md` as the agent's source input, using the supported text/file input method.
4. Keep `RFP-001-Gold-Answer-Key.md` hidden from the agent; use it only for evaluation.
5. Run the test and preserve raw output, screenshots, model settings, execution state and errors.

## Pass/fail checks

| Check | Pass condition |
|---|---|
| Coverage | All 20 seeded IDs present |
| False positives | Zero invented requirements |
| Wording | Every extracted requirement agrees with source text |
| Traceability | Every item points to correct section and ID |
| Obligation | 17 mandatory, 3 preferred; no incorrect assignments |
| Categorization | All 20 correctly categorized |
| SME | Suggested, never presented as verified ownership |
| Supplier compliance | UNKNOWN for all 20 |
| Coverage honesty | Independent coverage check explicitly required |
| Format | Parseable JSON matching requested fields |

## Scoring
- Recall = correctly extracted source requirements / 20.
- Precision = correctly extracted requirements / all extracted requirements.
- Source citation accuracy = correctly located requirements / 20.
- Obligation accuracy = correctly classified requirements / 20.
- SME ownership integrity = number marked SUGGESTED_NOT_CONFIRMED / 20.
- No acceptance if any invented requirement or fabricated source reference is present, even if other metrics are high.

## Failure classification
- Missed clause: extraction/coverage failure.
- Fabricated clause or locator: grounding failure.
- Incorrect must/should: obligation classification failure.
- Confirmed SME without evidence: ownership inference failure.
- Invalid JSON: output contract failure.
- Stalled/errored test: ART runtime/tool failure; preserve exact error.

## Next gate
Only after the baseline passes: introduce missing attachments, conflicting statements, embedded tables and portal-style questionnaires; then test governance and orchestrated SME routing.
