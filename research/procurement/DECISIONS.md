# Central Decisions Register: Procurement Research

> **Coordinator:** Chiranjeevi  
> **Repository:** `ART-Automation-Lab/art-investigation-lab`  
> **Last Updated:** 2026-10-08

---

## Decision Index

- [`DEC-PROC-001`](#dec-proc-001-isolation-of-procurement-research-from-application-runtime-and-schemas) — Isolation of Procurement Research from Application Runtime and Schemas
- [`DEC-PROC-002`](#dec-proc-002-four-person-single-process-ownership-model) — Four-Person Single-Process Ownership Model
- [`DEC-PROC-003`](#dec-proc-003-strict-epistemic-evidence-and-ambiguity-classification) — Strict Epistemic Evidence and Ambiguity Classification
- [`DEC-PROC-004`](#dec-proc-004-strict-isolation-of-synthetic-rfp-001-benchmark-kit) — Strict Isolation of Synthetic RFP-001 Benchmark Kit

---

## DEC-PROC-001: Isolation of Procurement Research from Application Runtime and Schemas

- **Decision ID:** `DEC-PROC-001`
- **Date:** 2026-10-08
- **Decider:** Chiranjeevi (Coordinator)
- **Status:** APPROVED & LOCKED
- **Context:**  
  The ART Investigation Lab repository hosts a production Next.js application, locked JSON schemas (`contracts/AIL-INVESTIGATION-BRIEF-JSON-SCHEMA-V1.json`), and compiler contracts (`contracts/INVESTIGATION-BRIEF-COMPILER-CONTRACT-V1.md`). A four-person procurement research initiative is commencing.
- **Decision:**  
  All procurement research artifacts, workflows, evidence registers, and investigation notes must be housed strictly under `research/procurement/`. Under no circumstances shall procurement research directly alter, modify, or extend application contracts or runtime components.
- **Consequences:**  
  - Complete decoupling of research velocity from application stability.
  - Zero risk of regression in existing Next.js build or persistence tests.
  - Future compilation of procurement intelligence into AIL view models will occur via an explicit compiler pipeline rather than runtime file coupling.

---

## DEC-PROC-002: Four-Person Single-Process Ownership Model

- **Decision ID:** `DEC-PROC-002`
- **Date:** 2026-10-08
- **Decider:** Chiranjeevi (Coordinator)
- **Status:** APPROVED & LOCKED
- **Context:**  
  Procurement covers a vast surface area. Without crisp ownership boundaries, team members risk overlapping research, conflicting edits, and merge friction.
- **Decision:**  
  Assign exactly one process owner per process:
  - `P01-RFP`: Chiranjeevi
  - `P02-SUPPLIER-DELIVERY`: Vrushali
  - `P03-REPLENISHMENT`: Bhushan
  - `P04-INVOICE-EXCEPTIONS`: Ashwin  
  Cross-process handoffs must be documented via traceable links rather than duplicating research across directories.
- **Consequences:**  
  - Eliminates merge conflicts in Git.
  - Fixes accountability for evidence grounding and ambiguity resolution.
  - Prevents superficial breadth across multiple topics in favor of deep forensic rigor.

---

## DEC-PROC-003: Strict Epistemic Evidence and Ambiguity Classification

- **Decision ID:** `DEC-PROC-003`
- **Date:** 2026-10-08
- **Decider:** Chiranjeevi (Coordinator)
- **Status:** APPROVED & LOCKED
- **Context:**  
  Unverified AI generation tends to conflate marketing claims, software feature lists, and live operational feasibility.
- **Decision:**  
  Enforce a strict 5-tier evidence taxonomy (`E0`–`E4`) and 4-tier ambiguity taxonomy (`A1`–`A4`) across all research deliverables, governed by [`RESEARCH_STANDARD.md`](./RESEARCH_STANDARD.md) and [`MASTER_PROMPT.md`](./MASTER_PROMPT.md).
- **Consequences:**  
  - Automatic promotion of evidence levels is forbidden.
  - Claims lacking primary documentation remain at `E0`.
  - Ambiguities must be logged explicitly with required evidence paths.

---

## DEC-PROC-004: Strict Isolation of Synthetic RFP-001 Benchmark Kit

- **Decision ID:** `DEC-PROC-004`
- **Date:** 2026-10-08
- **Decider:** Chiranjeevi (Coordinator)
- **Status:** APPROVED & LOCKED
- **Context:**  
  A validation kit `RFP-001` containing synthetic test documents, prompts, checklists, and a gold answer key was imported from `/home/chiranjeevi/Downloads/RFP-001-ART-Validation-Kit`.
- **Decision:**  
  - The kit is placed in [`validation/RFP-001/`](./validation/RFP-001/).
  - It is classified as synthetic benchmarking test data, NOT operational research evidence.
  - The gold answer key must never be provided to candidate agents.
  - Test execution status remains marked as `CURRENTLY NOT TESTED` until live execution is formally conducted and audited.
- **Consequences:**  
  - Preserves integrity of benchmark scoring.
  - Prevents synthetic data from polluting real-world empirical findings.
