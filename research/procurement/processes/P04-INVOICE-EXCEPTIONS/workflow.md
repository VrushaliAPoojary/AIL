# Workflow Specification: Invoice Discrepancy Resolution (P04-INVOICE-EXCEPTIONS)

> **Process ID:** `P04-INVOICE-EXCEPTIONS`  
> **Process Name:** Invoice Discrepancy Resolution  
> **Process Owner:** Ashwin  
> **Status:** **PLANNED / DRAFT SPECIFICATION (NOT YET IMPLEMENTED IN THIS CHECKOUT)**  
> **Governing Standard:** [`../../RESEARCH_STANDARD.md`](../../RESEARCH_STANDARD.md)

---

## 1. Planned End-to-End Workflow Architecture

```text
[Supplier Invoice Ingested]
             │
             ▼
[3-Way Reconciliation Engine]
  - PO Line Item & Price (From: ../P01-RFP/ & ../P02-SUPPLIER-DELIVERY/)
  - Goods Receipt Note (GRN) Quantity & Quality
             │
             ├─────────────────────────────┐
             ▼                             ▼
     [Variance Detected]             [Zero Variance]
             │                             │
             ▼                             ▼
 [Categorize Discrepancy]          [Post for Payment]
   - Quantity Over/Short
   - Price Variance
   - Tax / Freight Surcharge
             │
             ▼
 [Human Review / Credit Request]
```

---

## 2. Operational Interfaces & Handoffs

1. **Upstream Inputs:**
   - Contracted pricing and payment terms from [`../P01-RFP/`](../P01-RFP/).
   - Verified receipt quantities and delivery confirmation records from [`../P02-SUPPLIER-DELIVERY/`](../P02-SUPPLIER-DELIVERY/).
   - Replenishment stock adjustments from [`../P03-REPLENISHMENT/`](../P03-REPLENISHMENT/).
2. **Downstream Outputs:**
   - Accounts payable release authorization or supplier debit/credit memo request.

---

## 3. Human Governance & Decision Points

- Unapproved price increases above contract require buyer confirmation.
- Quantity short-shipment credits require dock receiving supervisor verification.
