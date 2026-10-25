# Procurement Evidence Quality Gate

> **Authority:** [`../RESEARCH_STANDARD.md`](../RESEARCH_STANDARD.md)  
> **Master Evidence Register:** [`../EVIDENCE_REGISTER.md`](../EVIDENCE_REGISTER.md)  
> **Target:** Pull Request Reviewers & Process Owners

---

## 1. Purpose & Invariant Principle

This quality gate establishes the criteria for admitting evidence into the procurement research workspace. 

> [!CRITICAL]
> **Core Quality Invariant:**  
> A synthetic test run, benchmark score, or AI-generated statement can **NEVER** qualify as empirical real-world evidence. Synthetic evaluations (such as [`../validation/RFP-001/`](../validation/RFP-001/)) measure model mechanics, not enterprise reality.

---

## 2. The 12 Mandatory Evidence Acceptance Checks

Every evidence entry in `evidence.md` or [`../EVIDENCE_REGISTER.md`](../EVIDENCE_REGISTER.md) must pass all twelve criteria to be marked `VERIFIED`. Failure on any single item results in `REJECTED` or demotion to `E0`.

| Check # | Verification Item | Pass Condition | Rejection / Demotion Trigger |
|---|---|---|---|---|
| **1** | **Direct Source URL** | Accessible, canonical HTTP/HTTPS link or formal ISBN / DOI / official document identifier. | Broken link, paywalled generic homepage without page number, unverified secondary blog. |
| **2** | **Verbatim Quotation** | Word-for-word excerpt matching the source text. | Paraphrased assertion presented inside quotes; selective truncation that alters context. |
| **3** | **Source Authority & Context** | Recognized industry body, audited financial filing, official vendor manual, or verified domain expert. | Marketing fluff, unverified promotional brochure, SEO-generated content farm. |
| **4** | **What the Quotation Proves** | Explicit, bounded statement of the exact fact or metric established by the quote. | Overclaiming beyond what the quoted words literally state. |
| **5** | **What It Does NOT Prove** | Clear statement of boundaries, caveats, or unaddressed factors. | Omitting critical context (e.g., citing a metric from 2012 as current 2026 reality). |
| **6** | **Evidence Classification (`E0`–`E4`)** | Correct assignment based strictly on definitions in [`../RESEARCH_STANDARD.md`](../RESEARCH_STANDARD.md). | Arbitrary upward promotion (e.g., claiming a whitepaper survey is E4 direct validation). |
| **7** | **Claim Traceability** | Directly mapped to a persistent claim ID (`CLM-P0x-xxx`). | Unlinked quotation floating without explicit investigative hypothesis. |
| **8** | **Contradictory Evidence Audit** | Conflicting sources cross-referenced and logged in [`../AMBIGUITIES.md`](../AMBIGUITIES.md). | Suppressing contrary data points to make an automation case appear cleaner. |
| **9** | **Incumbent Software Context** | Evaluates whether modern ERPs or source-to-pay tools already solve the cited issue. | Claiming a greenfield problem where standard ERP features already provide out-of-the-box automation. |
| **10** | **Practitioner vs. Enterprise Level** | Distinguishes individual practitioner perspective (`E3`) from audited company-wide operations (`E4`). | Treating one consultant's LinkedIn post as proven organizational truth. |
| **11** | **Unresolved Unknowns Tagged** | Open questions logged in process file and central register. | Faking resolution of unanswered implementation details. |
| **12** | **Formal Acceptance Verdict** | Explicit verdict: `ACCEPTED_E1`, `ACCEPTED_E2`, `ACCEPTED_E3`, `ACCEPTED_E4`, or `REJECTED`. | Indeterminate status without documented evaluation. |

---

## 3. Evidence Evaluation Worksheet (Template)

When auditing a new evidence submission, the reviewer uses this mental or written model:

```markdown
### Evidence Item Audit: [EVD-P0x-xxx]
- **Source Citation:** [Author / Entity, Title, Year, Page / Section]
- **URL / Locator:** [Canonical URL]
- **Verbatim Excerpt:** "[Exact words from source]"
- **Claim Supported:** [CLM-P0x-xxx]
- **Audited Level:** [E1 | E2 | E3 | E4]
- **Specific Proof:** [Exactly what this quotation proves]
- **Boundary / Limitation:** [What this quote does NOT prove]
- **Existing Tool Context:** [Does SAP/Oracle/Coupa address this?]
- **Gate Verdict:** [ACCEPTED | PROVISIONAL_E0 | REJECTED]
```

---

## 4. Handling Rejections

- If a quote cannot be verified via canonical URL: **REJECT** entry.
- If a claim asserts enterprise-wide pain but only provides an anecdotal blog: **DEMOTE to E0/E3**.
- If synthetic test results are submitted as evidence: **REJECT IMMEDIATELY** and route to `validation/`.
