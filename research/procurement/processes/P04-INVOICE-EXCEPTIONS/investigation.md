# Investigation: Invoice Discrepancy Resolution (P04-INVOICE-EXCEPTIONS)

> **Process ID:** `P04-INVOICE-EXCEPTIONS`  
> **Process Name:** Invoice Discrepancy Resolution  
> **Process Owner:** Ashwin (Process Owner)  
> **Status:** **PLANNED / DRAFT SPECIFICATION (NOT YET IMPLEMENTED IN THIS CHECKOUT)**  
> **Governing Standard:** [`../../RESEARCH_STANDARD.md`](../../RESEARCH_STANDARD.md)  
> **Master Prompt:** [`../../MASTER_PROMPT.md`](../../MASTER_PROMPT.md)  
> **Current Epistemic Level:** Pilot Planning (`E0` Hypotheses / `E1` Technical Standards)

---

> [!IMPORTANT]
> **Operational Status Notice:** This process workspace is explicitly marked as **PLANNED**. It documents the planned architecture, requirements, and evidence boundary for P04. Live execution, ERP integrations, and web surfaces for P04 are scheduled for future development phases. In the current repository checkout, only **P02 (Supplier Delivery Confirmation & Delay Escalation)** is actively implemented in the Next.js delivery control center.

---

## 1. Process Scope & Operational Boundary

### In-Scope:
- 3-way matching between Purchase Order lines, Goods Receipt Notes (GRN), and vendor invoices.
- Quantity variance identification (over-shipment, short shipment, damaged goods).
- Unit price discrepancies, unapproved freight or tax surcharges, and payment term mismatches.
- Credit note requisition and accounts payable block management.

### Out-of-Scope (Handoffs):
- Upstream contract pricing and payment terms baselining (managed in [`../P01-RFP/`](../P01-RFP/)).
- Supplier delivery confirmation tracking, ASN verification, and expediting (managed in [`../P02-SUPPLIER-DELIVERY/`](../P02-SUPPLIER-DELIVERY/)).
- Safety stock rebalancing and reorder quantity adjustments (managed in [`../P03-REPLENISHMENT/`](../P03-REPLENISHMENT/)).

---

## 2. Research Categories & Epistemic Boundaries

### 2.1 3-Way Matching Architecture
- **ERP 3-Way Match Rules (`CLM-P04-001` / `E1`):** In enterprise ERPs (e.g. ERPNext / SAP MIRO), invoices require exact item-level reconciliation against purchase order quantities and posted receipt records. Discrepancies exceeding defined price or quantity tolerances automatically apply payment blocks (`R-Block`).
- **Vendor Discrepancy Resolution (`CLM-P04-002` / `E0`):** Price/quantity mismatch root cause distribution (pricing master vs invoice transcription vs dock miscount) is tracked as an operational hypothesis.

---

## 3. Related Process Documents

- Evidence Register: [`./evidence.md`](./evidence.md)
- Workflow Specification: [`./workflow.md`](./workflow.md)
- ART Platform Validation: [`./art-validation.md`](./art-validation.md)
- Central Decisions: [`../../DECISIONS.md`](../../DECISIONS.md)
- Central Ambiguities: [`../../AMBIGUITIES.md`](../../AMBIGUITIES.md)
