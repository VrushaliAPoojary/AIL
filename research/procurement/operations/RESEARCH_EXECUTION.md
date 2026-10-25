# Procurement Research Execution Procedure

> **Standard Authority:** [`../RESEARCH_STANDARD.md`](../RESEARCH_STANDARD.md)  
> **Master Prompt Reference:** [`../MASTER_PROMPT.md`](../MASTER_PROMPT.md)  
> **Applies to:** Process Owners (Chiranjeevi, Vrushali, Bhushan, Ashwin)

---

## 1. Overview & Perspective Boundary

This standard establishes the mandatory 12-step evidence-based investigation lifecycle for enterprise procurement research. 

### Critical Perspective Boundary: Buyer vs. Supplier
Researchers must maintain clear perspective boundaries:
- **Buyer-Side Evaluation:** Involves requisitioning, publishing requirements, evaluating bids, selecting suppliers, issuing POs, receiving shipments, and auditing vendor invoices (P02, P03, P04, and the procurement side of P01).
- **Supplier-Side Response:** Involves parsing client tenders, extracting vendor obligations, coordinating SME bid responses, and submitting commercial proposals (the bid-response side of P01).

Never conflate buyer operational friction with supplier response friction.

---

## 2. The 12-Step Investigation Lifecycle

```text
[1. Scope Boundary] ──► [2. Enterprise Context] ──► [3. As-Is Process Map]
         │
         ▼
[4. Primary Sources] ──► [5. Epistemic Tagging] ──► [6. Incumbent Software Audit]
         │
         ▼
[7. Residual Gap Proof] ──► [8. Ambiguity & Contradiction Log] ──► [9. Public Contacts]
         │
         ▼
[10. Bounded ART Opportunity] ──► [11. Controlled Test Plan] ──► [12. PR Submission]
```

### Step 1: Define Narrowly Scoped Process Boundary
Define the exact trigger, scope, and end boundary of the process under investigation. Do not attempt to investigate "procurement in general." Focus on a specific failure mode (e.g., *EDI 856 ASN delay notification failures* or *3-way match price tolerance breaks*).

### Step 2: Identify Industry, Organizational & Scale Context
Establish the operational environment:
- Sector: Manufacturing, Healthcare, Retail, Technology, or Public Sector.
- Organizational Scale: Enterprise ($1B+ spend), Mid-Market ($50M-$500M spend), or SME.
- Regulatory & Compliance Environment: SOX compliance, HIPAA, FAR/DFARS, or local statutory tax laws (e.g., GST/VAT).

### Step 3: Establish the Documented Current Process (As-Is)
Map the baseline operational workflow step-by-step:
- Standard Path: The sequence when no anomalies occur.
- Human Touchpoints: Where human operators transcribe, verify, or review.
- Exception Loops: The path taken when errors, missing fields, or discrepancies occur.

### Step 4: Collect Original Sources & Verbatim Quotations
Gather verifiable documentation from primary sources:
- Official technical documentation (SAP, Oracle, Coupa, Jaggaer manuals).
- Industry benchmarks (Institute for Supply Management, Hackett Group, APQC, IOFM).
- Academic supply-chain studies and audited enterprise case studies.
- Capture **verbatim quotes** and canonical URLs. Paraphrasing that softens or exaggerates operational pain is forbidden.

### Step 5: Separate Epistemic Categories (E0 – E4)
Apply the strict epistemic rules in [`../RESEARCH_STANDARD.md`](../RESEARCH_STANDARD.md):
- **Fact:** Verifiable system rules, published APIs, statutory requirements.
- **Practitioner Testimony:** First-hand accounts from procurement buyers or expediters.
- **Inference:** Deductions logically derived from facts (state premises explicitly).
- **Hypothesis:** Unvalidated proposals or assumptions (`E0`).

### Step 6: Identify Existing Software & Incumbent Automation
Before asserting that an autonomous agent is needed, document existing commercial solutions:
- What does SAP S/4HANA, Coupa, or ServiceNow already automate?
- What configured workflow rules, EDI transactions, or robotic process automations (RPA) are already in production use?

### Step 7: Investigate Whether a Residual Problem Remains
Prove why existing tools fail or are bypassed:
- Is data unstructured (unstandardized emails, scanned PDF delivery slips)?
- Does the system enforce rigid all-or-nothing rules that cause exception queues to explode?
- Does resolving the exception require cross-silo human negotiation and judgment?

### Step 8: Explicitly Record Unknowns & Contradictions
If two sources disagree on benchmark metrics (e.g., AP exception rates reported as 12% vs. 35%), do not average them. Record both citations in [`../AMBIGUITIES.md`](../AMBIGUITIES.md) as a documented contradiction.

### Step 9: Identify Public, Role-Relevant Outreach Contacts
Where practitioner interviews are justified:
- Use only lawful, public professional information (e.g., public LinkedIn job titles, conference speaker rosters, published corporate org charts).
- Document only professional role and organization type.
- Never record private personal contact information, home addresses, or credentials.

### Step 10: Propose a Bounded ART Automation Opportunity
Define a realistic, narrow agent role:
- What specific human task does the agent assist or perform?
- What is the explicit decision boundary?
- What hard guardrails prevent unauthorized financial commitments or legal liabilities?

### Step 11: Define Controlled ART Test Plans Without Fabricating Results
Draft test scenarios and validation criteria:
- Document what inputs the agent receives.
- Define what constitutes an objective pass or fail.
- Clearly state execution status as **`CURRENTLY NOT TESTED`**. Never report simulated or imagined test results as factual execution outcomes.

### Step 12: Submit for Independent Peer Review
Submit updates via a focused pull request against `main`. Follow [`PR_REVIEW_STANDARD.md`](./PR_REVIEW_STANDARD.md) and wait for Coordinator Chiranjeevi's evaluation.
