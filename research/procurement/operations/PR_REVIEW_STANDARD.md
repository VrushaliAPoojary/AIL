# Pull Request Review Standard: Procurement Research

> **Authority:** [`../RESEARCH_STANDARD.md`](../RESEARCH_STANDARD.md), [`EVIDENCE_QUALITY_GATE.md`](./EVIDENCE_QUALITY_GATE.md)  
> **Reviewer Authority:** Coordinator Chiranjeevi  
> **Applies to:** All PRs targeting `main` modifying `research/procurement/`

---

## 1. Review Philosophy & Contract Boundary

Every research contribution is a durable addition to the repository's epistemic knowledge base. 

> [!WARNING]
> **Core Review Principle:**  
> **Passing CI checks does NOT equate to evidence validity.**  
> Automated workflows verify structural Markdown validity, link integrity, and scope limits. They cannot verify whether a quoted statistic is authentic, whether a source is reputable, or whether an operational deduction is sound. That remains the human responsibility of the Coordinator.

---

## 2. Mandatory PR Submission Contract

Every PR modifying procurement research must supply the following 13 fields in its description (enforced via `.github/PULL_REQUEST_TEMPLATE.md`):

1. **Contributor & Process:** Verified match with [`../OWNERSHIP.md`](../OWNERSHIP.md).
2. **Investigation IDs:** Explicit list of affected IDs (`CLM-P0x-xxx`, `WF-P0x-xxx`).
3. **Executive Summary:** Plain-language summary of what was investigated and concluded.
4. **Findings Added or Changed:** Granular bulleted list of new operational insights.
5. **Exact Evidence References:** Table or list linking `EVD-P0x-xxx` entries to source URLs and exact quotes.
6. **New Ambiguities Logged:** Any `AMB-P0x-xxx` items identified or resolved.
7. **Existing Automation Reviewed:** Explicit audit of incumbent software (SAP, Oracle, Coupa, etc.).
8. **Proposed ART Opportunity (if any):** Narrow, bounded agent role with guardrails.
9. **ART Execution Status:** Explicitly stated as `CURRENTLY NOT TESTED` or backed by logged test runs.
10. **Changed Files:** Path list verifying changes are strictly within assigned process folder.
11. **Automated Checks Result:** Output of local or CI validation scripts.
12. **Risks and Limitations:** Known caveats, biases, or statutory constraints.
13. **Coordinator Decision Requested:** Explicit call to action for the review.

---

## 3. The Four Review Decisions

When evaluating a PR, Coordinator Chiranjeevi must issue one of four formal verdicts:

### 1. `APPROVE`
- **Criteria:**
  - Changes are 100% scoped to contributor's assigned process folder.
  - Zero application code, contracts, or schemas modified.
  - All new evidence entries pass the [`EVIDENCE_QUALITY_GATE.md`](./EVIDENCE_QUALITY_GATE.md) (verbatim quotes, working URLs).
  - Ambiguities are registered with appropriate severity (`A1`–`A4`).
  - No synthetic data is represented as empirical findings.
  - GitHub Actions automated checks pass.
- **Action:** Approve and merge into `main`.

### 2. `REQUEST CHANGES`
- **Criteria:**
  - Minor link error, missing table column, unlinked claim ID, or incomplete citation.
  - Quoted text is paraphrased rather than verbatim.
  - Evidence level inappropriately tagged (e.g., hypothesis tagged as `E1`).
- **Action:** Provide clear, actionable feedback comments directly on the PR lines. Contributor updates the same branch.

### 3. `BLOCKED`
- **Criteria:**
  - Material architectural ambiguity (`A3`) or authorization/compliance risk (`A4`) identified.
  - Research reveals a statutory legal conflict or dependency on unresolved upstream process data.
- **Action:** Mark PR as blocked, record issue in [`../AMBIGUITIES.md`](../AMBIGUITIES.md), and hold until external clarification is obtained.

### 4. `REJECT`
- **Criteria:**
  - Willful or ungrounded AI fabrication of quotes, sources, or metrics.
  - Unapproved modifications to application contracts, schemas, or production code.
  - Attempted modification of another contributor's assigned process without authorization.
- **Action:** Close PR without merging with a formal rejection explanation referencing [`AI_AGENT_RULES.md`](./AI_AGENT_RULES.md).
