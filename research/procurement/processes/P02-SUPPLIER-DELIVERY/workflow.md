# Operational Workflow: Supplier Delivery Confirmation & Delay Escalation (P02-SUPPLIER-DELIVERY)

> **Process ID:** `P02-SUPPLIER-DELIVERY`  
> **Process Owner:** Vrushali  
> **Governing Standard:** [`../../RESEARCH_STANDARD.md`](../../RESEARCH_STANDARD.md)
> **Last Updated:** 2026-10-12 (Use Case, Benchmark & ART Tool Status Update)

---

## 1. As-Is Operational Workflow Topology

```text
[PO Issued to Supplier] (EDI 850 / Email / Portal)
             │
             ▼
   [WF-P02-001: PO Transmission & Delivery Acknowledgment Clock]
             │
    ┌────────┴────────┐
    ▼                 ▼
[Acknowledged]    [Unacknowledged > 48h] ───► [WF-P02-002: Staged Chaser Drafting]
    │                                                   │
    ▼                                                   ▼
[WF-P02-003: Delivery Date & Quantity Reconciliation Gate] ◄┘
    │
    ├────────────────────────┬────────────────────────┐
    ▼                        ▼                        ▼
[On-Schedule Full]     [Partial Split / Backorder]  [Delay Detected / Reschedule Request]
    │                        │                        │
    │                        │                        ▼
    │                        │         [WF-P02-004: Buffer & Production Impact Triage]
    │                        │                        │
    │                        │            ┌───────────┴───────────┐
    │                        │            ▼                       ▼
    │                        │     [Buffer Absorbed]       [Stockout Risk / Critical Breach]
    │                        │            │                       │
    │                        │            │                       ▼
    │                        │            │           [WF-P02-005: Tiered Escalation]
    │                        │            │           (Expediting / Dual-Sourcing / SLA Notice)
    │                        │            │                       │
    │                        ▼            ▼                       ▼
    └────────────────► [WF-P02-006: In-Transit ASN & Dock Gate Handoff]
                                 │
                                 ▼
                          [Dock Receiving] ───► Handoff to P03 (Inventory) & P04 (Invoice Match)
```

---

## 2. Detailed Step Specifications

### `WF-P02-001`: PO Transmission & Acknowledgment SLA Clock
- **Trigger:** Approved Purchase Order dispatched to supplier via EDI 850, ERP email connector, or vendor portal.
- **Operator:** Purchasing Specialist / Automated ERP Dispatcher.
- **Inputs:** Released Purchase Order document, Vendor Email/EDI Endpoint, Requested Delivery Date (`RDD`), Incoterms.
- **Activities:** Dispatch PO payload; start the 48-hour acknowledgment countdown timer (`SLA-ACK-48H`).
- **Outputs:** Timestamped dispatch record; active monitoring queue entry.
- **Evidence Reference:** ANSI ASC X12 850/855 standards ([`evidence.md#evd-p02-002`](./evidence.md)).

### `WF-P02-002`: Unacknowledged Order Follow-Up (Staged Chaser Drafting)
- **Trigger:** Timer expires at T+48 hours with zero incoming acknowledgment record.
- **Operator:** Procurement Expediter / Automated Chaser Agent.
- **Inputs:** Open PO record, vendor contact profile, days elapsed.
- **Activities:** Generate a staged draft inquiry for supplier sales contact (`auto_send: false`). At T+72 hours without response, assign expediter task card for phone outreach.
- **Outputs:** Staged draft chaser record; expediting priority queue update. Zero autonomous outbound emails are dispatched.
- **Evidence Reference:** Expediting operational burden ([`evidence.md#evd-p02-004`](./evidence.md)).

### `WF-P02-003`: Delivery Date & Quantity Reconciliation Gate
- **Trigger:** Vendor response received (EDI 855 message, unstructured email body, or PDF confirmation).
- **Operator:** Expediter / Supplier Response Parser Agent.
- **Inputs:** Supplier confirmation payload, ERP PO baseline schedule line.
- **Activities:**
  1. Extract Promised Delivery Date (`PDD`), promised line quantities, and status code.
  2. Reconcile against baseline PO:
     - Scenario A: Full acceptance on-schedule (`IA` status) $\rightarrow$ Stage schedule line update for ingestion buffer (`STAGE_SCHEDULE_LINE_UPDATE`).
     - Scenario B: Partial shipment committed (`BP` status) $\rightarrow$ Calculate backorder quantity, stage split schedule lines (`EKET`), route to `WF-P02-004` and human review.
     - Scenario C: Date slippage (`PDD > RDD`) $\rightarrow$ Calculate variance in business days, stage revised date, route to `WF-P02-004` and human review.
     - Scenario D: Ambiguous or conflicting response $\rightarrow$ Halt automated processing; stage draft clarification; route to Human Review Gate.
     - Scenario E: Contractual alteration (price increase, part substitution) $\rightarrow$ Halt workflow; enforce strict prohibition against price/SKU modification; route to commercial buyer.
- **Outputs:** Normalized structured confirmation payload; discrepancy classification.
- **Safety Invariant:** Zero direct unverified ERP writes. All actions are staged.
- **Evidence Reference:** ANSI ASC X12 855 ACK Codes ([`evidence.md#evd-p02-002`](./evidence.md)), SAP Confirmation Control Keys ([`evidence.md#evd-p02-003`](./evidence.md)).

### `WF-P02-004`: Buffer & Production Impact Triage
- **Trigger:** Confirmed delay or split delivery received from `WF-P02-003`.
- **Operator:** Material Planner / Inventory Replenishment Specialist.
- **Inputs:** Revised delivery date, material part number, current on-hand inventory, daily consumption rate / safety stock threshold.
- **Activities:** Compute projected inventory level on original `RDD` vs. new `PDD`. Determine whether safety stock buffer absorbs the delay or whether stockout occurs.
- **Outputs:** Impact classification (`BUFFER_ABSORBED` vs. `STOCKOUT_RISK`); handoff trigger to [`../P03-REPLENISHMENT/`](../P03-REPLENISHMENT/).

### `WF-P02-005`: Tiered Escalation & Alternative Sourcing
- **Trigger:** `STOCKOUT_RISK` or unmitigated delay exceeding operational tolerance.
- **Operators:** Procurement Category Manager, Supply Chain Director.
- **Activities:**
  - **Tier 1:** Supplier account manager negotiation for production prioritization.
  - **Tier 2:** Supplier-funded expedited air freight authorization to recover transit days.
  - **Tier 3:** Emergency purchase split from secondary qualified vendor (handoff to P03).
  - **Tier 4:** Issuance of formal SLA liquidated damages penalty or breach notice based on contract terms negotiated in P01.
- **Outputs:** Escalation log; authorized recovery action plan; ERP revision record.
- **Evidence Reference:** Incoterms risk allocation ([`evidence.md#evd-p02-005`](./evidence.md)).

### `WF-P02-006`: Advance Shipping Notice (ASN) & Dock Gate Handoff
- **Trigger:** Goods dispatched from vendor facility.
- **Operator:** Inbound Logistics Coordinator.
- **Inputs:** EDI 856 ASN, carrier Bill of Lading (BOL), GPS/container tracking milestone data.
- **Activities:** Match ASN to PO schedule line; monitor carrier milestones; notify warehouse receiving team.
- **Outputs:** Verified inbound delivery document (`LA` confirmation in ERP); handoff to physical dock receiving.
- **Handoff:** Downstream handoff to [`../P03-REPLENISHMENT/`](../P03-REPLENISHMENT/) for stock availability and [`../P04-INVOICE-EXCEPTIONS/`](../P04-INVOICE-EXCEPTIONS/) for 3-way matching goods receipt note (GRN).

---

## 3. Proposed ART-Supported Use Case & System Boundaries

### 3.1 Plain Use Case Description
The proposed ART assistant is designed to support a human procurement buyer in retrieving ERP purchase-order and supplier information from ERPNext and reviewing that data against a supplier's delivery promise.

Rather than replacing human oversight, the agent acts as an investigative copilot:
- It connects to ERPNext to pull open purchase order records, item schedule dates, ordered quantities, and supplier contact details.
- It compares the baseline ERP commitment against a supplier delivery promise provided during the buyer's workflow.
- It identifies variances (e.g. on-time fulfillment, date slippages, partial shipments, missing dates, or unauthorized price/SKU modifications) and categorizes them according to the governance rules.

### 3.2 Connected Tools & Read-Only Scope
The tools currently connected to the agent platform for P02 are strictly **read-only**:
1. **`p02_delivery_list_purchase_orders`:** Lists open Purchase Orders in ERPNext with pagination controls (e.g., limit).
2. **`p02_delivery_get_purchase_order`:** Retrieves a complete Purchase Order record by its exact document name (e.g., `PUR-ORD-2026-00011`), exposing both header-level and line-item schedules.
3. **`p02_delivery_get_supplier`:** Retrieves a Supplier record by its exact document name (e.g., `P02 Test Supplier`) for supplier context.

### 3.3 Critical Input & Ingestion Boundary
- **No Native Email or PDF Ingestion:** The currently connected ERPNext tools do **not** read supplier emails, parse email inboxes, or extract text from attached PDF confirmation slips.
- **Input Provenance Requirement:** In the current prototype state, any supplier delivery promise must be manually provided by the user in the prompt or supplied through a separately configured, verified input mechanism.
- The system must not assume that configuring ERP connector tools enables automatic email or document parsing.

### 3.4 Buyer Responsibilities & Safety Invariants
- **Human Authority:** The buyer remains exclusively responsible for interpreting delivery discrepancies, contacting suppliers, negotiating revised dates, and authorizing any consequential actions.
- **No Autonomous Writes:** The agent has zero authorization and zero connected capabilities to update ERPNext document state, modify schedule lines, or close orders.
- **No Autonomous Messaging:** The agent must not send emails, trigger chasers, or dispatch external communications to suppliers. Any proposed chaser text is produced strictly as a staged draft for human buyer review.

### 3.5 Evidence & Value Proposition Reality
- **Unverified Operational Prevalence:** In accordance with [`evidence.md`](./evidence.md) (`EVD-P02-001`), the organizational prevalence of email/PDF confirmations versus EDI across suppliers remains an unverified hypothesis (`E0`).
- **Unverified Expediting Savings:** In accordance with [`evidence.md`](./evidence.md) (`EVD-P02-004`), industry expediting workload and cost savings claims remain unverified (`E0`) due to secondary source access restrictions.
- **No Claim of Proven Savings:** This prototype is **not** claimed or demonstrated to reduce delivery delays, lower purchasing costs, or cut buyer expediting hours in production.

---

## 4. Synthetic Benchmark Specification (`DELIVERY-001`)

The benchmark test suite [`benchmark-DELIVERY-001.md`](./benchmark-DELIVERY-001.md) defines six deterministic test scenarios designed to validate reconciliation logic against baseline purchase order `PO-2026-90412`.

> [!IMPORTANT]
> **Execution Status:** **Specified but not executed.**
> These test cases represent synthetic benchmark specifications. They are **not** live supplier transactions or empirical operational evidence. No automated test runner or live ART agent execution was run against this suite in the repository; expected outputs have not been observed in an execution environment.

### Summary of Synthetic Test Cases

| Test Case ID | Scenario Name | Key Stimulus / Input | Expected Classification | Expected Action | Human Review? | Full Spec Link |
|---|---|---|---|---|---|---|
| `TC-DEL-001` | On-Time Confirmation | Supplier confirms full 100 EA for 2026-10-22 (ahead of 2026-10-26 RDD; -2 business days variance) | `delivery_status: ON_TIME`<br>`edi_ack_code: null` | `STAGE_SCHEDULE_LINE_UPDATE` | **No** (`false`) | [`benchmark-DELIVERY-001.md#tc-del-001`](./benchmark-DELIVERY-001.md#test-case-1-tc-del-001-on-time-confirmation) |
| `TC-DEL-002` | Delayed Delivery | Supplier commits full 100 EA but delays delivery to 2026-11-06 (+9 business days variance) due to raw material delay | `delivery_status: DELAYED`<br>`edi_ack_code: null` | `STAGE_REVISED_DELIVERY_DATE_FOR_HUMAN_REVIEW`<br>Escalation: `LEVEL_2_EXPEDITING`<br>Staged draft inquiry (`auto_send: false`) | **Yes** (`true`) | [`benchmark-DELIVERY-001.md#tc-del-002`](./benchmark-DELIVERY-001.md#test-case-2-tc-del-002-delayed-delivery) |
| `TC-DEL-003` | Partial Delivery & Split Line | Supplier ships 60 EA on-time (2026-10-26) and 40 EA delayed to 2026-11-09 (+10 business days variance) | `delivery_status: PARTIAL_DELIVERY`<br>`edi_ack_code: null` | `STAGE_SPLIT_SCHEDULE_LINES_FOR_HUMAN_REVIEW`<br>Escalation: `LEVEL_1_INVENTORY_ALERT` | **Yes** (`true`) | [`benchmark-DELIVERY-001.md#tc-del-003`](./benchmark-DELIVERY-001.md#test-case-3-tc-del-003-partial-delivery-split-schedule-line) |
| `TC-DEL-004` | Missing Delivery Date | Supplier acknowledges order receipt into production queue but specifies no promised date (Tier A2 ambiguity) | `delivery_status: MISSING_DATE`<br>`edi_ack_code: null` | `STAGE_CLARIFICATION_REQUEST_FOR_HUMAN_APPROVAL`<br>Staged draft reminder (`auto_send: false`) | **Yes** (`true`) | [`benchmark-DELIVERY-001.md#tc-del-004`](./benchmark-DELIVERY-001.md#test-case-4-tc-del-004-missing-delivery-date) |
| `TC-DEL-005` | Conflicting Delivery Dates | Email body states 2026-10-27 while attached PDF slip states 2026-11-18 (22-day conflict; Tier A2 ambiguity) | `delivery_status: CONFLICTING_DATES`<br>`edi_ack_code: null` | `HOLD_TRANSACTION_AND_ESCALATE_TO_BUYER`<br>Escalation: `HUMAN_EXPEDITER_REVIEW` | **Yes** (`true`) | [`benchmark-DELIVERY-001.md#tc-del-005`](./benchmark-DELIVERY-001.md#test-case-5-tc-del-005-conflicting-delivery-dates) |
| `TC-DEL-006` | Critical Exception | Supplier reports part obsolescence on VALVE-HYDR-440, proposes substitution VALVE-HYDR-450 with +$40.00 price increase | `delivery_status: CRITICAL_EXCEPTION`<br>`edi_ack_code: null` | `HALT_PROCESSING_AND_ESCALATE_TO_COMMERCIAL_BUYER`<br>Escalation: `LEVEL_3_COMMERCIAL_ENGINEERING_REVIEW`<br>Strict price/SKU freeze enforced | **Yes** (`true`) | [`benchmark-DELIVERY-001.md#tc-del-006`](./benchmark-DELIVERY-001.md#test-case-6-tc-del-006-critical-exception-requiring-human-review) |

*Full scenario payloads, raw text inputs, and complete JSON schema contracts are maintained in [`benchmark-DELIVERY-001.md`](./benchmark-DELIVERY-001.md).*

---

## 5. Reported ART Tool-Test Status (2026-10-12 Test Conversation)

> [!NOTE]
> **Provenance & Evidence Limitations:**
> The outcomes in this section reflect results **reported from the interactive ART testing conversation on 2026-10-12**. Independent backend API logs or persistent execution traces are not currently stored in the repository; therefore, these outcomes are documented as reported session observations rather than independently verified backend audit records.

### 5.1 Read-Only Three-Tool Smoke Test (Reported Passed)
A read-only smoke test of the three configured ERPNext connector tools was conducted during the 2026-10-12 session with the following reported results:

1. **`p02_delivery_list_purchase_orders` (Limit 5):**
   - **Reported Outcome:** Success.
   - **Reported Output:** Returned two purchase orders:
     - `PUR-ORD-2026-00011` (Status: `"To Receive and Bill"`)
     - `PUR-ORD-2026-00012` (Status: `"To Bill"`)

2. **`p02_delivery_get_purchase_order` (`PUR-ORD-2026-00011`):**
   - **Reported Outcome:** Success.
   - **Reported Output:**
     - Supplier: `P02 Test Supplier`
     - Status: `"To Receive and Bill"`
     - Header-level schedule date: `2026-10-22`
     - Line items: 1 item (`item_code: "P02-TEST-ITEM-001"`, `qty: 1.0`, `schedule_date: "2026-10-20"`)

3. **`p02_delivery_get_supplier` (`P02 Test Supplier`):**
   - **Reported Outcome:** Success.
   - **Reported Output:** Retrieved document confirming supplier name `P02 Test Supplier` and supplier type `Company`.

#### Critical Note on ERPNext Date Fields
In ERPNext purchase orders, the **header-level schedule date** (`schedule_date: 2026-10-22`) and the **line-item schedule date** (`items[0].schedule_date: 2026-10-20`) are distinct, independent database fields. A variance between header and item schedule dates reflects ERP document structure and does not, in itself, constitute an operational defect or date error.

### 5.2 Item-Code Search Tool Status (Failed / Unvalidated)
- **Tool Attempted:** `p02_delivery_find_po_item_lines_by_item_code` (intended to query `Purchase Order Item` lines by `item_code`).
- **Reported Outcome:** **Failed with HTTP 403 (Forbidden) in ART.**
- **Validation Status:** **FAILED / UNVALIDATED.**
- **Root Cause:** **Unknown.** Without backend server logs, the root cause cannot be confirmed (e.g. whether due to Frappe DocType read permissions, query parameter formatting, or connector configuration). No permission or configuration hypothesis is asserted as fact.
- This tool is **not** part of the passed three-tool smoke-test baseline described above.

### 5.3 Expedite and Write Tool Status (Not Tested)
- **Status:** **NOT RUN / NOT TESTED.**
- The proposed expediting write tool was not invoked or evaluated during the test session.
- **Invariant Upheld:** No purchase order write, schedule line modification, or ERP data update was tested or executed.

---

## 6. Cross-Process Boundaries & Dependencies

- **Upstream from P01 (RFP):** Ingests negotiated supplier lead times, carrier routing compliance rules, and liquidated damage SLA terms negotiated in [`../P01-RFP/`](../P01-RFP/).
- **Downstream to P03 (Replenishment):** Transmits confirmed delivery dates, split lots, and lead-time delays to [`../P03-REPLENISHMENT/`](../P03-REPLENISHMENT/) to trigger safety stock recalculations or emergency reorders.
- **Downstream to P04 (Invoice Exceptions):** Transmits confirmed delivery milestones and dock goods receipts to [`../P04-INVOICE-EXCEPTIONS/`](../P04-INVOICE-EXCEPTIONS/) to provide clean receiving lines for 3-way invoice matching.

---

## 7. References & Documentation

- Investigation Brief: [`investigation.md`](./investigation.md)
- Evidence Register: [`evidence.md`](./evidence.md)
- Candidate ART Validation Architecture: [`art-validation.md`](./art-validation.md)
- Synthetic Benchmark Specification: [`benchmark-DELIVERY-001.md`](./benchmark-DELIVERY-001.md)
- ERPNext Lookup Tools Overview: [`toolusecase.md`](./toolusecase.md)
- Process Outcomes & Audit Report: [`vrushali-task-outcomes-report.md`](./vrushali-task-outcomes-report.md)
- Governance Log: [`governance.md`](./governance.md)
