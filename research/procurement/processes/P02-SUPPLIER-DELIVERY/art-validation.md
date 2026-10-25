# ART Agent Validation & Architecture: Supplier Delivery Confirmation (P02-SUPPLIER-DELIVERY)

> **Process ID:** `P02-SUPPLIER-DELIVERY`
> **Process Name:** Supplier Delivery Confirmation & Delay Escalation
> **Process Owner:** Vrushali
> **Execution Status:** **CURRENTLY NOT TESTED (Phase 1 Review Corrections)**
> **Governing Standard:** [`../../RESEARCH_STANDARD.md`](../../RESEARCH_STANDARD.md)
> **Last Updated:** 2026-10-09

---

## 1. Candidate ART Architecture Specification

The minimum autonomous ART architecture pipeline for supplier delivery tracking follows a 5-stage sequential topology with strict human governance gates:

```text
[Stage 1: Multi-Channel Ingestion]
        │  (Raw Email / PDF Attachment / Mock Webhook Payload)
        ▼
[Stage 2: Delivery Extraction & Parsing Agent]
        │  (LLM Prompt / Regex Entity Extractor)
        ▼
[Stage 3: Structured Classification & Reconciliation Node]
        │  (Compare PDD vs RDD, Quantity vs Ordered, Calculate Variance)
        ▼
[Stage 4: Governance & Risk Decision Gate]
        │  (Strict Policy Engine: Staging vs. Human Review Escalation)
        ├──────────────────────────────────────┐
        ▼                                      ▼
[Stage 5A: Staged Action Queue]        [Stage 5B: Human Review Gate]
  - Staged ERP Schedule Line Record      - Buyer Expediting Task Card
  - Staged Draft Supplier Clarification  - Buffer Breach Review Form
  - (No Autonomous ERP Writes)           - Downstream Replenishment (P03) Alert
```

---

## 2. Node Capabilities & Inspection Status

*Note: In accordance with repository governance, uninspected platform components are explicitly tagged. Capabilities must be directly confirmed in the ART UI prior to Phase 2 implementation.*

| Pipeline Stage            | Candidate Node / Component         | Functional Responsibility                                                                                                                    | ART Platform Verification Status                                                                                                |
| ------------------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **Input**           | `Email / Webhook Listener Node`  | Ingests incoming supplier email bodies, metadata, and PDF attachments.                                                                       | `[PENDING ART UI INSPECTION]` — Confirm supported trigger types in ART canvas.                                               |
| **Agent / Parser**  | `LLM Structured Extraction Node` | Parses raw text into normalized JSON containing PO number, promised dates, and line quantities.                                              | `[PENDING ART UI INSPECTION]` — Confirm prompt template parameterization and model selection.                                |
| **Reconciliation**  | `Data Mapper / Comparison Node`  | Compares parsed promised delivery date against baseline PO requested delivery date and ordered quantity.                                     | `[PENDING ART UI INSPECTION]` — Confirm whether math/date-diff expressions are native or require Python serverless function. |
| **Governance Gate** | `Decision / Branching Node`      | Routes transactions based on discrepancy severity (`ON_TIME`, `DELAYED`, `PARTIAL_DELIVERY`, `CONFLICTING_DATES`, `MISSING_DATE`). | `[PENDING ART UI INSPECTION]` — Confirm conditional branching controls.                                                      |
| **Output / Review** | `Human-in-the-Loop Review Node`  | Suspends automated processing; generates expediter task card in ART workspace for buyer sign-off.                                            | `[PENDING ART UI INSPECTION]` — Confirm human review task queue mechanics in ART.                                            |
| **ERP Integration** | `Staging REST API Node`          | Emits validated schedule line update to a staged approval buffer (never direct unverified ERP write).                                        | `[PENDING ART UI INSPECTION]` — Confirm HTTP tool action authentication and payload mapping.                                 |

---

## 3. Required Field Schema & Data Contracts

### 3.1 Normalized Reconciliation Output Contract

Every ingested confirmation must produce a standardized output payload conforming to:

```json
{
  "po_number": "string",
  "vendor_id": "string",
  "confirmation_timestamp": "ISO-8601 string",
  "delivery_status": "ON_TIME | DELAYED | PARTIAL_DELIVERY | MISSING_DATE | CONFLICTING_DATES | CRITICAL_EXCEPTION",
  "edi_ack_code": "IA | BP | AC | DR | RJ | null",
  "ambiguity_tier": "A1 | A2 | A3 | A4 | NONE",
  "line_items": [
    {
      "line_number": "integer",
      "sku": "string",
      "quantity_ordered": "number",
      "quantity_confirmed": "number",
      "requested_delivery_date": "YYYY-MM-DD",
      "promised_delivery_date": "YYYY-MM-DD | null",
      "variance_business_days": "integer"
    }
  ],
  "governance_decision": {
    "staging_action": "STAGE_SCHEDULE_LINE_UPDATE | STAGE_REVISED_DELIVERY_DATE_FOR_HUMAN_REVIEW | STAGE_SPLIT_SCHEDULE_LINES_FOR_HUMAN_REVIEW | STAGE_CLARIFICATION_REQUEST_FOR_HUMAN_APPROVAL | HOLD_TRANSACTION_AND_ESCALATE_TO_BUYER | HALT_PROCESSING_AND_ESCALATE_TO_COMMERCIAL_BUYER",
    "human_review_required": "boolean",
    "escalation_tier": "NONE | LEVEL_1_INVENTORY_ALERT | LEVEL_2_EXPEDITING | LEVEL_3_COMMERCIAL_ENGINEERING_REVIEW",
    "staged_outbound_communication": "object | null",
    "prohibited_actions_enforced": [
      "NO_AUTOMATIC_ERP_WRITE",
      "NO_AUTONOMOUS_SUPPLIER_DISPATCH",
      "NO_PRICE_OR_SKU_MODIFICATION"
    ]
  }
}
```

---

## 4. Final Governance Decision Rules & Safety Invariants

### 4.1 Strict Safety Invariants

1. **Zero Unverified ERP Writes:** The ART agent will **never** directly modify ERP purchase order lines or schedule lines (`EKET`). All outputs are placed in a staged reconciliation buffer awaiting buyer release or standard validation gate approval.
2. **Zero Autonomous Outbound Messaging:** The agent will **never** dispatch live emails to suppliers. All inquiries or chasers are generated as staged drafts (`auto_send: false`) requiring human review.
3. **Zero Price or SKU Modification:** The agent is strictly prohibited from accepting price adjustments, part number substitutions, or altering contractual Incoterms. Any such attempt immediately halts the workflow.
4. **Mandatory Human-in-the-Loop Review for Consequential Exceptions:**
   - Any delivery date slippage (`Promised Delivery Date > Requested Delivery Date`).
   - Any partial shipment or backorder split (`quantity_confirmed < quantity_ordered`).
   - Any missing delivery date (`Ambiguity Tier A2`).
   - Any conflicting dates between email body and attachments (`Ambiguity Tier A2`).
   - Any engineering hold, obsolescence, or contractual modification (`Ambiguity Tier A3/A4`).
5. **Separation of Operational Delivery Status and EDI Syntax:** Operational delivery status reflects date and quantity reconciliation against contractual requirements; it is not conflated with EDI transmission codes.

---

## 5. ART Platform Validation Readiness Checklist

Before Phase 2 live execution or test-runner evaluation can begin, the following platform elements must be inspected:

- [ ] **Canvas Inspection:** Verify available node types in ART UI (Workflow Builder / Canvas).
- [ ] **Data Transformation:** Verify how ART handles JSON schema validation and multi-line array mapping.
- [ ] **Human Review UI:** Confirm how ART presents pending human approval tasks and review forms to operators.
- [ ] **Credential Store:** Verify configuration of mock API tokens and email test webhooks.
- [ ] **Test-Runner Integration:** Verify how synthetic test documents from [`benchmark-DELIVERY-001.md`](./benchmark-DELIVERY-001.md) are injected into the ART test console.

---

## 6. Current Execution Declaration

**CURRENTLY NOT TESTED.**
In strict compliance with onboarding rules and Phase 1 pilot governance, no autonomous execution runs or live system writes have occurred. All specifications above represent design and validation contracts prepared for Phase 2 implementation.
