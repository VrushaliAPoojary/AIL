# Central Ambiguities & Uncertainty Register

> **Standard:** Defined in [`RESEARCH_STANDARD.md`](./RESEARCH_STANDARD.md)  
> **Master Prompt:** Defined in [`MASTER_PROMPT.md`](./MASTER_PROMPT.md)  
> **Coordinator:** Chiranjeevi  
> **Last Updated:** 2026-10-08

---

## 1. Ambiguity Severity Classification

| Level | Severity | Definition | Action Required |
|---|---|---|---|
| **A1** | Minor | Minor uncertainty or minor semantic inconsistency that does not affect process boundaries. | Record and proceed with investigation. |
| **A2** | Material | Material uncertainty regarding process steps, pain point magnitude, or software capability. | Investigate and gather evidence before drawing conclusions. |
| **A3** | Critical | Critical unknown regarding operational feasibility, data availability, or system integration. | Blocks agent architecture or automation proposals. |
| **A4** | Fatal / Safety | Fundamental authorization, safety, statutory compliance, or financial liability hazard. | Stop consequential execution immediately. |

---

## 2. Central Ambiguity Log

| Ambiguity ID | Process | Owner | Level | Affected Claim / Area | Nature of Uncertainty | Required Evidence to Resolve | Status | Resolution Summary |
|---|---|---|---|---|---|---|---|---|
| `AMB-P01-001` | `P01-RFP` | Chiranjeevi | `A2` | Live Tender Variability | Extent to which actual public tenders use unstructured portals vs. standard PDF documents. | Direct review of active enterprise/government tender portals. | `OPEN` | Pending live discovery. |
| `AMB-P02-001` | `P02-SUPPLIER-DELIVERY` | Vrushali | `A2` | Supplier EDI Adoption | Percentage of Tier-1 vs. Tier-2/3 suppliers that utilize automated EDI (856 ASN) vs. manual email delivery promises. | Empirical industry benchmarks across manufacturing/retail sectors. | `OPEN` | Pending literature review. |
| `AMB-P03-001` | `P03-REPLENISHMENT` | Bhushan | `A3` | Dynamic Lead-Time Variance | How enterprise MRP systems dynamically recalculate reorder points during unexpected supplier lead-time surges. | SAP/Oracle SCM documentation and practitioner testimony on MRP exception overrides. | `OPEN` | Pending ERP capability audit. |
| `AMB-P04-001` | `P04-INVOICE-EXCEPTIONS` | Ashwin | `A2` | Invoice Discrepancy Tolerance Limits | Standard organizational price and quantity variance tolerance thresholds before triggering manual AP hold. | Documented corporate AP policy benchmarks and Sarbanes-Oxley audit rules. | `OPEN` | Pending AP benchmark review. |

---

## 3. Ambiguity Resolution Protocol

1. **Logging:** When an unknown, contradictory data point, or systemic assumption is encountered during research, the process owner immediately logs it in this register.
2. **Escalation:**
   - `A1` and `A2` are researched by the process owner.
   - `A3` must be flagged to Coordinator **Chiranjeevi** during weekly sync or PR review.
   - `A4` immediately halts any autonomous workflow design or decision document.
3. **Closing:** An ambiguity is marked `RESOLVED` only when an explicit evidence reference (`EVD-P0x-xxx`) is linked that directly eliminates the uncertainty.
