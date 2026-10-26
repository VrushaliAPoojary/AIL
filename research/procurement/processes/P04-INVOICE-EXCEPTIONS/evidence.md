# Evidence Register: Invoice Discrepancy Resolution (P04-INVOICE-EXCEPTIONS)

> **Process ID:** `P04-INVOICE-EXCEPTIONS`  
> **Process Owner:** Ashwin  
> **Status:** **PLANNED / DRAFT SPECIFICATION (NOT YET IMPLEMENTED IN THIS CHECKOUT)**  
> **Governing Standard:** [`../../RESEARCH_STANDARD.md`](../../RESEARCH_STANDARD.md)  
> **Master Evidence Register:** [`../../EVIDENCE_REGISTER.md`](../../EVIDENCE_REGISTER.md)  
> **Last Updated:** 2026-10-26

---

## 1. Evidence Rules for P04

- All entries carry identifiers formatted as `EVD-P04-xxx`.
- No evidence may be fabricated; ungrounded operational assumptions remain `E0`.
- Citations must preserve exact source locations and verifiable definitions.

---

## 2. Process Evidence Table

| Evidence ID | Level | Source Title & Organization | Canonical URL / Document Locator | Verbatim Citation / Technical Data Point | Supported Finding / Claim ID | Verification Status |
|---|---|---|---|---|---|---|
| `EVD-P04-001` | `E1` | ERPNext / SAP Logistics Invoice Verification Standards | [`https://docs.erpnext.com/docs/v14/user/manual/en/buying/purchase-invoice`](https://docs.erpnext.com/docs/v14/user/manual/en/buying/purchase-invoice) | Standard purchase invoice processing validates billed rate and quantity against accepted purchase receipts; variances exceeding tolerance thresholds require manual intervention or debit note generation. | `CLM-P04-001` | `ACCEPTED_E1` |
| `EVD-P04-002` | `E0` | AP Exception Frequency Baseline | Internal Operational Hypothesis | **Hypothesis (Unverified):** Invoice discrepancies affect between 15% and 25% of all non-EDI supplier invoices, causing significant accounts payable processing delays. | `CLM-P04-002` | `UNVERIFIED_E0` |

---

## 3. Epistemic Traceability Index

- **`CLM-P04-001` (`E1`):** Purchase invoice 3-way matching mechanics. Status: `ACCEPTED_E1`.
- **`CLM-P04-002` (`E0`):** Hypothesis on manual AP exception frequency. Status: `UNVERIFIED_E0`.
