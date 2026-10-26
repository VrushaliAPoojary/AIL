# Investigation: Inventory Replenishment & Reorder Exceptions (P03-REPLENISHMENT)

> **Process ID:** `P03-REPLENISHMENT`  
> **Process Name:** Inventory Replenishment & Reorder Exceptions  
> **Process Owner:** Bhushan (Process Owner)  
> **Status:** **PLANNED / DRAFT SPECIFICATION (NOT YET IMPLEMENTED IN THIS CHECKOUT)**  
> **Governing Standard:** [`../../RESEARCH_STANDARD.md`](../../RESEARCH_STANDARD.md)  
> **Master Prompt:** [`../../MASTER_PROMPT.md`](../../MASTER_PROMPT.md)  
> **Current Epistemic Level:** Pilot Planning (`E0` Hypotheses / `E1` Technical ERP Architecture)

---

> [!IMPORTANT]
> **Operational Status Notice:** This process workspace is explicitly marked as **PLANNED**. It documents the planned architecture, requirements, and evidence boundary for P03. Live execution, ERP integrations, and web surfaces for P03 are scheduled for future development phases. In the current repository checkout, only **P02 (Supplier Delivery Confirmation & Delay Escalation)** is actively implemented in the Next.js delivery control center.

---

## 1. Process Scope & Operational Boundary

### In-Scope:
- Monitoring safety stock breaches, stockout projections, and lead-time variability.
- MRP reorder exception generation (e.g. reschedule in, reschedule out, cancel order).
- Supplier lead-time discrepancy tracking caused by confirmed delivery delays.
- Buffer stock recalculation and replenishment requisition proposals.

### Out-of-Scope (Handoffs):
- Upstream vendor sourcing agreements and contract terms (managed in [`../P01-RFP/`](../P01-RFP/)).
- Supplier delivery confirmation tracking, ASN monitoring, and expediting (managed in [`../P02-SUPPLIER-DELIVERY/`](../P02-SUPPLIER-DELIVERY/)).
- Physical warehouse dock receipt and invoice 3-way matching (managed in [`../P04-INVOICE-EXCEPTIONS/`](../P04-INVOICE-EXCEPTIONS/)).

---

## 2. Research Categories & Epistemic Boundaries

### 2.1 MRP Exception Messages & Schedule Adjustments
- **MRP Exception Logic (`CLM-P03-001` / `E1`):** In enterprise ERP systems (e.g. SAP MRP, ERPNext Stock Reorder), delayed supplier delivery confirmations from P02 directly trigger rescheduling exception messages (e.g., Exception 10 "Bring process forward", Exception 15 "Postpone process").
- **Safety Stock Consumption (`CLM-P03-002` / `E0`):** Buffer depletion rates and demand spike handling require dynamic recalculation of reorder points.

---

## 3. Related Process Documents

- Evidence Register: [`./evidence.md`](./evidence.md)
- Workflow Specification: [`./workflow.md`](./workflow.md)
- ART Platform Validation: [`./art-validation.md`](./art-validation.md)
- Central Decisions: [`../../DECISIONS.md`](../../DECISIONS.md)
- Central Ambiguities: [`../../AMBIGUITIES.md`](../../AMBIGUITIES.md)
