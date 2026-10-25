# RFP-001 — Synthetic Test Validation Kit

## Purpose and Status

This directory contains the synthetic benchmark validation kit for **RFP-001** (Enterprise Service Platform).

- **Nature of Data:** **SYNTHETIC TEST DATA**. This document and requirements set were generated for benchmarking purposes only and do not represent a real commercial tender or live client RFP.
- **Evidentiary Status:** **DOES NOT PROVE INDUSTRY PAIN OR ART CAPABILITY**. Performance on synthetic test data cannot be cited as empirical evidence of operational friction, real-world practitioner pain, or enterprise production readiness.
- **Execution Status:** **CURRENTLY NOT TESTED**. No live agent execution has been certified for this benchmark within this workspace.

---

## Benchmark Security & Protocol

1. **Answer Key Isolation:**
   The reference file [`RFP-001-Gold-Answer-Key.md`](./RFP-001-Gold-Answer-Key.md) must **NEVER** be supplied, uploaded, or exposed to the agent being evaluated. It is strictly reserved for independent post-execution scoring by the human evaluator.

2. **Separation from Research Evidence:**
   Test outcomes, agent extraction runs, and benchmark scores must be recorded separately from empirical research evidence. They must **never** be entered into [`../../EVIDENCE_REGISTER.md`](../../EVIDENCE_REGISTER.md) as E1, E2, E3, or E4 evidence.

3. **Input Protocol:**
   Only [`RFP-001-ART-Agent-Prompt.md`](./RFP-001-ART-Agent-Prompt.md) and [`RFP-001-Test-Document.md`](./RFP-001-Test-Document.md) may be provided to the candidate agent during test execution.

---

## File Inventory

| File | Purpose | Access Control |
|---|---|---|
| [`RFP-001-ART-Agent-Prompt.md`](./RFP-001-ART-Agent-Prompt.md) | Standard instructions and JSON output schema given to the candidate agent | Supplied to Agent |
| [`RFP-001-Test-Document.md`](./RFP-001-Test-Document.md) | Synthetic 8-section tender document containing 20 seeded requirements | Supplied to Agent |
| [`RFP-001-Gold-Answer-Key.md`](./RFP-001-Gold-Answer-Key.md) | Human-reviewed reference inventory of the 20 seeded requirements | Evaluator ONLY (Hidden from Agent) |
| [`RFP-001-Test-Checklist.md`](./RFP-001-Test-Checklist.md) | 10-point pass/fail criteria, recall/precision scoring, and failure taxonomy | Evaluator ONLY |

---

## Scoring and Evaluation Reference

Refer to [`RFP-001-Test-Checklist.md`](./RFP-001-Test-Checklist.md) for full evaluation guidelines:
- **Baseline Recall:** 20 / 20 explicit requirements.
- **Zero Hallucination Gate:** Immediate fail if any invented requirement or fabricated locator is returned.
- **Obligation Grounding:** Exactly 17 mandatory (`must`), 3 preferred (`should`).
- **Epistemic Honesty:** All vendor compliance answers must remain `UNKNOWN`; suggested SME assignments must be flagged as `SUGGESTED_NOT_CONFIRMED`.
