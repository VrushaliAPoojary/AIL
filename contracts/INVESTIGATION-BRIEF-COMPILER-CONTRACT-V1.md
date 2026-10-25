# INVESTIGATION BRIEF COMPILER CONTRACT (PHASE 01)

## 1. PURPOSE
This document establishes the strict architectural boundary, contract definition, and data ownership rules for the automated ART Intelligence Core Investigation Brief Compiler. It defines what constitutes a valid research input package and how that input is mapped to the final JSON artifact, explicitly separating raw research content from compiler metadata and ensuring verifiable traceability.

**WHY:** To ensure the compilation process is deterministic, repeatable, and prevents the LLM extraction engine from hallucinating or inventing unsupported research findings.
**WHAT:** A formal input-to-output contract boundary.
**WHERE:** Bound between the `art-opportunities-intelligence` repository (input) and the `art-investigation-lab` repository (output).
**HOW:** The compiler must follow these rules before initiating any LLM compilation phase.
**PROOF:** The existing AIL types and validators require precise adherence to expected JSON structures.
**IMPACT:** Establishes a predictable, safe pipeline for migrating textual Markdown intelligence into a structured epistemic graph.

## 2. SOURCE OF TRUTH
**WHY:** AIL must render state without attempting to parse unstructured Markdown at runtime.
**WHAT:** The raw Markdown files within the `art-opportunities-intelligence` repository are the immutable **source of truth** for research content. The compiled `InvestigationBrief` JSON is the **authoritative structured representation** for the AIL application. 
**WHERE:** `art-opportunities-intelligence` (Markdown) -> Compiler -> `art-investigation-lab` (JSON).
**HOW:** The compiler translates, but never modifies, the source research. AIL relies only on the validated JSON.
**PROOF:** The removal of runtime markdown ingestion in previous architectural shifts confirms AIL's strict dependency on JSON.
**IMPACT:** Complete decoupling of the runtime UI from the research generation process.

## 3. INPUT PACKAGE
**WHY:** The compiler needs a bounded context to extract relevant causal relationships and provenance.
**WHAT:** The input package is defined as a specific investigation directory (e.g., `opportunity02`) containing:
- `walkthrough.md` (mandatory)
- Zero or more checkpoint/research `.md` files (e.g., `OPP-002-01.md`)
- `opportunity.md` (mandatory)
- `workflow.md` (optional, but permitted if present)
**WHERE:** Sourced from `art-opportunities-intelligence/reseach for AIL/servicenow/*`.
**HOW:** The compiler will mount the entire directory as a single compilation context.
**PROOF:** Existing opportunity folders consistently follow this structural pattern.
**IMPACT:** Ensures that the compiler has access to the full evidentiary chain.

## 4. FILE DISCOVERY RULES
**WHY:** To ensure compilation is deterministic and no evidence is silently ignored or overwritten.
**WHAT:** 
1. **Locating directory:** The input directory path must be provided explicitly.
2. **Identifying walkthrough.md:** The file named exactly `walkthrough.md` must be present.
3. **Discovering checkpoints:** Any file matching `OPP-*-*.md` is a checkpoint.
4. **Ordering checkpoints:** Checkpoints must be ordered lexicographically by filename.
5. **Path preservation:** Original filenames and relative paths must be recorded for provenance.
6. **Detecting duplicates:** If two files have identical names, the compiler must fail.
7. **Missing files:** If `walkthrough.md` or `opportunity.md` is missing, the compiler must explicitly record a failure.
8. **Unsupported files:** Any non-markdown file, or unmapped file, must be logged as `UNSUPPORTED_FILE` in compiler metadata but will not halt compilation.
9. **Source manifest:** A complete manifest of all discovered files must be produced before extraction begins.
**WHERE:** Built into the future input loader component.
**HOW:** Strict filesystem traversal and pattern matching.
**PROOF:** The requirement to preserve provenance lines relies on knowing the exact source files.
**IMPACT:** Deterministic state tracking and clear visibility into what the compiler "saw".

## 5. INPUT NORMALIZATION RULES
**WHY:** To avoid inconsistencies introduced by file encodings or line-endings.
**WHAT:** All discovered Markdown files must be read as UTF-8. Line endings must be normalized to `\n`. File contents must be mapped to an array of lines to ensure exact `line_start` and `line_end` provenance tracking.
**WHERE:** Future input loader.
**HOW:** Pre-processing stage before passing context to the LLM.
**PROOF:** `Provenance` requires integer line numbers in the AIL schema.
**IMPACT:** Accurate line-based provenance generation.

## 6. INVESTIGATION IDENTITY RULES
**WHY:** The compiled JSON must strictly reflect the opportunity metadata without hallucinating details.
**WHAT:** The compiler must extract the following identity fields directly from `opportunity.md` or `walkthrough.md`:
- `investigation_id` (e.g., AOI-SNOW-OPP-002)
- `company`
- `opportunity`
- `investigation_type`
- `research_status`
- `decision` (if present)
**WHERE:** Defined in `src/types/investigationBrief.ts`.
**HOW:** Direct extraction via the Gemini engine with strict constraints against inventing missing values.
**PROOF:** The required fields in `InvestigationBrief`.
**IMPACT:** Ensures AIL displays accurate opportunity metadata.

## 7. SOURCE PROVENANCE RULES
**WHY:** To maintain the epistemic rigor of the ART methodology, every claim must trace back to the source Markdown.
**WHAT:** The LLM extraction engine MUST supply a `Provenance` block for every `evidence`, `claim`, `inference`, `hypothesis`, `checkpoint`, `result`, and `traceability` entry. 
The block must specify:
- `source_file`: The exact relative filename (e.g., `OPP-002-03.md`).
- `section`: The Markdown header under which the extraction occurred.
- `line_start`: The starting line number (integer) or `null`.
- `line_end`: The ending line number (integer) or `null`.
**WHERE:** `src/types/investigationBrief.ts` (`Provenance` interface).
**HOW:** The compiler must enforce this schema strictly.
**PROOF:** AIL relies on this block to render the Reusable Intelligence and Audit interfaces.
**IMPACT:** Full auditability from AIL UI back to the raw researcher notes.

## 8. COMPILER METADATA
**WHY:** To separate the tool's execution details from the actual research intelligence.
**WHAT:** Compiler metadata includes versioning, file manifests, and compilation timestamps. This metadata must be explicitly separated from the research payload. It must never be injected into `evidence`, `claims`, or any research field.
**WHERE:** Internal compiler representation; not part of the `InvestigationBrief` core research payload.
**HOW:** The compiler will wrap the `InvestigationBrief` payload in an envelope during processing, stripping the envelope before saving the final JSON.
**PROOF:** The `InvestigationBrief` schema has no fields for compiler metadata, ensuring purity.
**IMPACT:** AIL receives only the pure research artifact.

## 9. JSON CONTRACT AUTHORITY
**WHY:** To prevent schema fragmentation and ensure the compiled output passes runtime checks.
**WHAT:** The authoritative contract is established by the existing TypeScript implementation in AIL, specifically `src/types/investigationBrief.ts` and `src/data/investigationBriefValidator.ts`.

**⚠️ CRITICAL CONFLICT IDENTIFIED:**
An inspection of the existing AIL implementation reveals competing definitions:
1. `contracts/AIL-INVESTIGATION-BRIEF-JSON-SCHEMA-V1.json` defines `decision.reusable_intelligence` as a `string`, and entirely omits the `sources` array from its properties.
2. `src/types/investigationBrief.ts` defines `decision.reusable_intelligence` as an array of `IntelligenceObject[]`, and requires the `sources: InvestigationSource[]` array.
3. `src/data/investigationBriefValidator.ts` enforces the TypeScript interface rules, explicitly validating `decision.reusable_intelligence` as an array of objects and checking the `sources` array.

**RESOLUTION:** The compiler MUST conform to the runtime implementation: `src/types/investigationBrief.ts` and `src/data/investigationBriefValidator.ts`. The outdated `AIL-INVESTIGATION-BRIEF-JSON-SCHEMA-V1.json` must NOT be used as the compiler's strict target unless it is updated to match the runtime validator.

**WHERE:** `src/types/investigationBrief.ts`.
**HOW:** The LLM schema extraction template will mirror the TypeScript interface.
**PROOF:** The application will crash or reject data if it fails `validateInvestigationBrief()`.
**IMPACT:** Ensures compiled data works flawlessly in the AIL UI.

## 10. VALIDATION BOUNDARY
**WHY:** The compiler must not emit invalid files that could break the application.
**WHAT:** The compiler must invoke a deterministic validator (mirroring `investigationBriefValidator.ts`) against the Candidate InvestigationBrief.
**WHERE:** Output boundary of the compiler pipeline.
**HOW:** If validation fails, the compiler rejects the output and does NOT write the JSON to the AIL data directory.
**PROOF:** Adherence to strict epistemic classification sets (e.g., `VERIFIED`, `UNKNOWN`).
**IMPACT:** Guarantees 100% compliant data at runtime.

## 11. FAILURE CONDITIONS
**WHY:** To fail loudly rather than produce corrupted intelligence.
**WHAT:** The compiler must abort and yield a failure if:
- Required input files (`walkthrough.md`) are missing.
- Duplicate filenames exist in the input package.
- The LLM fails to output valid JSON.
- The deterministic validation step fails (e.g., missing provenance, invalid enums).
- The LLM hallucinates an ID in an `evidence_refs` array that does not exist in the output object.
**WHERE:** Compiler execution lifecycle.
**HOW:** Try/catch blocks and strict return types.
**PROOF:** Cross-reference validation rules in `investigationBriefValidator.ts`.
**IMPACT:** Zero pollution of the AIL environment.

## 12. OUTPUT BOUNDARY
**WHY:** To define a clean ownership boundary where AOI is the intelligence production system and AIL is purely the presentation system.
**WHAT:** The compiler outputs a single UTF-8 JSON file named `[investigation_id].json`. The compiler must NOT directly write into the AIL repository.
**WHERE:** The file is written to a designated output directory within the AOI repository (e.g., `art-opportunities-intelligence/compiled/`).
**HOW:** After validation passes, the JSON is saved to the AOI output directory. A separate, controlled "artifact promotion" step is then responsible for copying the validated JSON into `art-investigation-lab/src/data/investigations/`. 
**PROOF:** This architecture prevents AIL from becoming responsible for research interpretation, extraction, or validation.
**IMPACT:** Establishes a scalable architecture where AOI produces and validates the JSON, and AIL merely consumes it.

## 13. TRACEABILITY MODEL
**WHY:** To ensure relationships between epistemic objects are strictly maintained.
**WHAT:** `claims` reference `evidence_basis` by string ID. `inferences` reference `basis` by string ID. The compiler must ensure that any ID referenced in these arrays actually exists within the compiled document's `evidence`, `claims`, `inferences`, or `hypotheses` arrays. 
**WHERE:** `src/data/investigationBriefValidator.ts` (cross-reference checks).
**HOW:** The compiler validator will maintain a Set of all generated IDs and verify references before writing the file.
**PROOF:** The `checkRefs` function in the AIL validator.
**IMPACT:** The AIL Reasoning Graph will never encounter a broken link.

## 14. SECURITY / DATA-INTEGRITY RULES
**WHY:** To enforce the primary mandate: NO RESEARCH INVENTION.
**WHAT:** The LLM extraction prompt must strictly command the model:
- Do not invent evidence, claims, or hypotheses.
- Do not manufacture missing provenance.
- Do not infer decisions that are not explicitly stated.
- If data is absent, use valid fallback states like `UNKNOWN` or empty arrays as permitted by the schema.
- **AIL must never call Gemini to repair or interpret an InvestigationBrief.** If JSON is invalid, AIL rejects it. The correction happens upstream in AOI.
**WHERE:** Future Gemini Pro 3.1 extraction prompt.
**HOW:** Strong system prompt instructions and strict JSON schema bounding.
**PROOF:** The required `UNKNOWN` enum values in `ResearchStatus` and `IntelligenceEvidenceStatus`.
**IMPACT:** Protects the epistemic integrity of ART Core research.

## 15. PHASE 01 ACCEPTANCE CRITERIA
- [x] Authoritative InvestigationBrief contract identified (and conflicts documented).
- [x] Compiler input boundary explicit.
- [x] Complete research package defined.
- [x] File discovery deterministic.
- [x] Missing and unsupported files detectable.
- [x] Provenance requirements explicit.
- [x] Compiler metadata separated from research content.
- [x] Validation ownership explicit.
- [x] No UI dependency exists in the compiler contract.
- [x] No Markdown parser implementation introduced.
- [x] No JSON extraction performed.
- [x] No research content modified.

## 16. PHASE 02 DELEGATION
**WHY:** To lock the boundary that AOI owns the compilation engine.
**WHAT:** Phase 02 (building the actual Gemini compilation engine) must be implemented strictly within the `art-opportunities-intelligence` repository. AIL will not host the compiler.
**WHERE:** `art-opportunities-intelligence` repository.
**HOW:** The future extraction engine code will be committed to AOI, not AIL.
**PROOF:** The separation of concerns between production (AOI) and presentation (AIL).
**IMPACT:** Prevents coupling of the UI application with the AI extraction logic.

---

### NON-CODER SUMMARY
This document acts as a strict "rulebook" for a future automated tool we are building. The tool's job will be to read through our folders of research notes (the Markdown files) and carefully translate them into a highly structured data file (a JSON file) that the AIL web application can display.

To prevent the AI from "hallucinating" or making up facts, this rulebook strictly defines what files the tool is allowed to look at, exactly what format the final data must be in, and how every single claim must be linked back to the specific line in the original research notes. It explicitly dictates that this "translation tool" lives entirely within our research repository (AOI), NOT our presentation app (AIL). AIL simply consumes the final, validated data file. It also ensures that if the AI makes a mistake or creates broken links, the tool will reject the file instead of sending bad data to our application, and AIL will never try to ask the AI to "fix" the data on the fly. Finally, it identifies a conflict in our existing definitions and dictates that the active code is the final authority.
