# ART Procurement Research Standard v1.0

## 1. Scope and Authority

This standard defines the mandatory epistemological rigor, evidence classification, ambiguity handling, and verification requirements for all research conducted in the ART Procurement Research Workspace.

This standard applies strictly to:
- [`processes/P01-RFP/`](./processes/P01-RFP/)
- [`processes/P02-SUPPLIER-DELIVERY/`](./processes/P02-SUPPLIER-DELIVERY/)
- [`processes/P03-REPLENISHMENT/`](./processes/P03-REPLENISHMENT/)
- [`processes/P04-INVOICE-EXCEPTIONS/`](./processes/P04-INVOICE-EXCEPTIONS/)
- Shared registers: [`EVIDENCE_REGISTER.md`](./EVIDENCE_REGISTER.md), [`AMBIGUITIES.md`](./AMBIGUITIES.md), [`DECISIONS.md`](./DECISIONS.md)

All researchers and AI research sessions must adhere to this document without exception.

---

## 2. Core Epistemic Categories

Researchers must strictly separate five categories of information. Never blur or conflate them:

1. **Fact (Verified Truth):** A claim supported by direct primary documentation, verifiable system specifications, or audited transactional data.
2. **Practitioner Testimony:** First-hand accounts, interviews, or professional commentary from real-world procurement professionals describing their lived operational experience.
3. **Inference:** A logical deduction drawn from verified facts or practitioner reports. Must be explicitly labeled as an inference with the underlying premises stated.
4. **Hypothesis:** An unverified conjecture, proposed capability, or anticipated pain point. Must remain classified at level `E0` until proven.
5. **Unknown / Contradiction:** Any gap in documentation, conflicting metric, or unreconciled source discrepancy. Must be recorded explicitly rather than averaged or smoothed over.

---

## 3. Evidence Classification Taxonomy (E0 – E4)

All research claims, citations, and observations must be tagged with exactly one of the following five evidence levels:

| Level | Code | Classification | Definition & Grounding Criteria | Typical Sources |
|---|---|---|---|---|
| Level 0 | **E0** | Hypothesis (Not Validated) | An assumption, preliminary proposal, or AI-generated hypothesis with zero empirical verification. | Brainstorming notes, initial hypotheses. |
| Level 1 | **E1** | Public Process Verification | Public documentation confirms the standard procedural steps, architectural topology, or regulatory framework of a process. | Official ERP manuals (SAP, Oracle, Coupa), regulatory mandates, APICS/ASCM standards. |
| Level 2 | **E2** | Documented Industry Pain Point | Public documentation explicitly supports and quantifies the operational friction, exception frequency, or delay cost. | Peer-reviewed supply chain studies, industry benchmark whitepapers (Gartner, Hackett, ISM), public court filings. |
| Level 3 | **E3** | Practitioner Testimony | Direct statement, interview, or detailed testimonial from an identified domain practitioner describing hands-on friction. | Field interviews, recorded expert Q&A, verified practitioner accounts. |
| Level 4 | **E4** | Direct Operational Validation | Direct, primary-source validation inside a specific enterprise: verified desk-level SOPs, audited system logs, live screen walkthroughs, or observed transaction data. | Customer site walkthroughs, primary operational data audits, internal exception logs. |

### Invariant Rules for Evidence:
- **Never Automatically Promote:** An `E0` hypothesis cannot become `E1` or `E2` without explicit public source documentation. An `E2` or `E3` finding cannot become `E4` without primary operational verification inside a specific enterprise.
- **Exact Quotations & Provenance:** Every evidence item must preserve verbatim quotes and an active, canonical URL or precise document locator. Paraphrasing that alters epistemic strength is prohibited.
- **Zero Fabrication:** Invented citations, synthetic benchmark scores, hypothetical stakeholder quotes, or non-existent API parameters are strictly prohibited.

---

## 4. Ambiguity Classification Taxonomy (A1 – A4)

Any uncertainty, missing data point, conflicting statement, or unverified assumption must be logged in [`AMBIGUITIES.md`](./AMBIGUITIES.md) using this four-tier severity model:

| Level | Severity | Name | Operational Rule |
|---|---|---|---|
| **A1** | Low | Minor Uncertainty | Minor factual or terminology variance that does not impede process understanding. Record in register and continue. |
| **A2** | Medium | Material Uncertainty | Substantial variance or missing step that affects workflow logic or pain quantification. Must investigate and resolve before formulating conclusions. |
| **A3** | High | Critical Unknown | Fundamental gap in feasibility, legal boundary, or integration requirement. Blocks automation proposal and implementation. |
| **A4** | Critical | Authorization / Safety Risk | Involves financial liability, data privacy exposure, statutory violation, or safety breach. Immediately stops any consequential execution. |

### Ambiguity Record Schema:
Each entry in [`AMBIGUITIES.md`](./AMBIGUITIES.md) and process files must record:
1. `Ambiguity ID` (e.g., `AMB-P01-001`)
2. `Process` (`P01`, `P02`, `P03`, `P04`)
3. `Owner` (Chiranjeevi, Vrushali, Bhushan, Ashwin)
4. `Level` (`A1`, `A2`, `A3`, `A4`)
5. `Affected Claim / Requirement`
6. `Nature of Uncertainty`
7. `Required Evidence to Resolve`
8. `Resolution Status` (`OPEN`, `INVESTIGATING`, `RESOLVED`, `BLOCKED`)

---

## 5. Traceable Identifier Standards

To ensure auditability across processes and future compilation, use standardized ID prefixes:

- **Claims / Findings:** `CLM-P0x-xxx` (e.g., `CLM-P01-001`)
- **Evidence Records:** `EVD-P0x-xxx` (e.g., `EVD-P02-005`)
- **Ambiguities:** `AMB-P0x-xxx` (e.g., `AMB-P03-002`)
- **Decisions:** `DEC-PROC-xxx` (e.g., `DEC-PROC-001`)
- **Workflow Steps:** `WF-P0x-xxx` (e.g., `WF-P04-003`)

---

## 6. Investigation Protocol for Software Automation

Before asserting that any procurement process requires a new autonomous agent or AI tool:
1. **Existing Solution Audit:** The researcher must thoroughly document incumbent software capabilities (SAP S/4HANA MM, Oracle Cloud SCM, Coupa BSM, ServiceNow Procurement Service Management, Jaggaer, etc.).
2. **Failure Analysis:** The researcher must demonstrate *why* existing software fails, is bypassed, or requires human intervention (e.g., rigid exception rules, unstandardized supplier inputs, cross-silo data gaps).
3. **Operational Realism:** Automation proposals must respect organizational boundaries, separation of duties, and audit controls.

---

## 7. Preservation of Contracts and Schemas

- Research findings under `research/procurement/` are structured research intelligence.
- **Contract Boundary:** This research does **NOT** alter, redefine, or supersede application contracts under `contracts/` (such as `AIL-INVESTIGATION-BRIEF-CONTRACT-V1.md` or `AIL-INVESTIGATION-BRIEF-JSON-SCHEMA-V1.json`).
- If procurement research later requires integration into the AIL web application, that integration must happen through a dedicated compiler pipeline or approved schema extension, never by ad-hoc modification of production contracts.
