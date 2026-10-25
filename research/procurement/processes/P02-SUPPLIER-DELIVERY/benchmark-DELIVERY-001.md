# Benchmark Specification: DELIVERY-001 (Supplier Delivery Confirmation & Delay Escalation)

> **Benchmark ID:** `DELIVERY-001`  
> **Process ID:** `P02-SUPPLIER-DELIVERY`  
> **Process Owner:** Vrushali  
> **Governing Standard:** [`../../RESEARCH_STANDARD.md`](../../RESEARCH_STANDARD.md)  
> **Status:** REVISED BENCHMARK SPECIFICATION (Phase 1 Review Corrections)

---

## 1. Benchmark Overview & Invariants

The `DELIVERY-001` benchmark evaluates the capability of an automated or AI-assisted system to ingest, parse, reconcile, and triage supplier delivery confirmations against purchase order baselines.

### Mandatory Operational Invariants:
1. **No Automatic ERP Writes:** All ERP schedule line updates are strictly **staged** (`STAGE_SCHEDULE_LINE_UPDATE`), never committed directly without validation and policy gate clearance.
2. **No Real Supplier Dispatches:** Outbound supplier communications are strictly generated as **staged drafts** (`DRAFT_CLARIFICATION_INQUIRY`, `DRAFT_EXPEDITING_INQUIRY`) for human buyer approval; zero autonomous emails are dispatched.
3. **No Unauthorized Price or SKU Modifications:** The system is strictly forbidden from altering unit prices or substituting material SKUs.
4. **Mandatory Human Review for Consequential Exceptions:** Any delivery date slippage, partial shipment, unconfirmed date, conflicting date, or contractual alteration requires human buyer/expediter sign-off.
5. **Separation of Operational Delivery Status and EDI Syntax:** Operational delivery status (`ON_TIME`, `DELAYED`, `PARTIAL_DELIVERY`, etc.) is evaluated independently from supplier transmission syntax (`edi_ack_code`).

All entities, organizations, dates, and PO identifiers in this benchmark are strictly synthetic.

---

## 2. Synthetic Baseline Purchase Order Data

```json
{
  "po_number": "PO-2026-90412",
  "buyer_organization": "Apex Industrial Technologies Ltd.",
  "buyer_contact": "Vrushali Poojary (Buyer)",
  "vendor_id": "VEND-88210",
  "vendor_name": "Precision Dynamics Components Corp.",
  "order_date": "2026-10-12",
  "incoterms": "DAP - Buyer Main Dock, Chicago IL",
  "line_items": [
    {
      "line_number": 1,
      "sku": "VALVE-HYDR-440",
      "description": "High-Pressure Hydraulic Actuator Valve 4400 PSI",
      "quantity_ordered": 100,
      "uom": "EA",
      "unit_price": 245.00,
      "requested_delivery_date": "2026-10-26"
    }
  ]
}
```

### 2.1 Business-Day Variance Counting Convention (Process Owner Policy)

Per Process Owner Vrushali's explicit decision (2026-10-09), `variance_business_days` is defined uniformly across all benchmark scenarios as follows:
- **Standard Monday–Friday Weekdays:** Only Monday through Friday are counted as working business days. Saturday and Sunday are strictly non-working weekend days.
- **Exclusion of Baseline Date, Inclusion of Promised Date:** The counting convention excludes the contractual Requested Delivery Date (`RDD`) and counts the Promised Delivery Date (`PDD`).
- **No Undeclared Holidays:** No public, federal, state, or plant shutdown holidays are deducted unless an explicit holiday calendar is declared in a specific scenario.
- **Signed Directional Arithmetic:**
  - **Delayed Delivery ($PDD > RDD$):** Count standard weekdays $d \in (RDD, PDD]$ and keep the count positive ($+(\text{count})$).
  - **Ahead-of-Schedule Delivery ($PDD < RDD$):** Count standard weekdays $d \in [PDD, RDD)$ and negate the count ($-(\text{count})$).
  - **Exact On-Time Delivery ($PDD = RDD$):** Variance is $0$ business days.

---

## 3. Test Cases Specification

### Test Case 1: `TC-DEL-001` — On-Time Confirmation

- **Scenario:** Supplier confirms full order on or before Requested Delivery Date (`RDD`).
- **Input (Supplier Email):**
  ```text
  From: dispatch@precisiondynamics.example.com
  To: purchasing@apexindustrial.example.com
  Subject: Order Confirmation: PO-2026-90412

  Dear Vrushali,
  We have received and accepted Purchase Order PO-2026-90412. All 100 units of VALVE-HYDR-440 will be delivered to your Chicago dock on October 22, 2026, ahead of your October 26 requested date.
  Tracking and carrier details will follow upon dispatch.

  Best regards,
  Order Fulfillment Team
  Precision Dynamics Components Corp.
  ```
- **Expected Structured Output:**
  ```json
  {
    "test_id": "TC-DEL-001",
    "po_number": "PO-2026-90412",
    "delivery_status": "ON_TIME",
    "edi_ack_code": null,
    "line_reconciliation": [
      {
        "line_number": 1,
        "sku": "VALVE-HYDR-440",
        "quantity_confirmed": 100,
        "quantity_ordered": 100,
        "promised_delivery_date": "2026-10-22",
        "requested_delivery_date": "2026-10-26",
        "variance_business_days": -2
      }
    ],
    "discrepancy_detected": false,
    "recommended_action": "STAGE_SCHEDULE_LINE_UPDATE",
    "human_review_required": false,
    "staged_outbound_communication": null
  }
  ```
- **Acceptance Criteria:** Correctly parses date (`2026-10-22`), confirms full quantity, verifies negative business-day variance (`-2` business days / -4 calendar days, ahead of schedule), assigns delivery status `ON_TIME` with `edi_ack_code: null` (plain email provenance), and stages schedule line update without requiring expediter escalation.
- **Audit Annotation (Process Owner Decision Applied 2026-10-09):**
  1. *Synthetic Date & Dock Semantics Resolution:* Process Owner Vrushali explicitly changed the promised delivery date from Saturday, October 24, 2026 to Thursday, October 22, 2026. This avoids assuming weekend dock receiving hours for the Chicago facility and makes the `-2` business-day variance mathematically unambiguous under the standard Monday–Friday counting convention (counted weekdays in $[PDD, RDD)$: Thursday Oct 22 and Friday Oct 23, excluding baseline Monday Oct 26 = 2 business days earlier, negated to -2).
  2. *EDI Provenance Enforcement:* Changed expected `edi_ack_code` from `"IA"` to `null` because unstructured supplier emails transmit no EDI transaction syntax, preserving data provenance per `evidence.md` (`EVD-P02-002`).
  3. *Acceptance Criteria Alignment:* Criteria updated to reflect the new promised date (`2026-10-22`) and negative business-day variance.

---

### Test Case 2: `TC-DEL-002` — Delayed Delivery

- **Scenario:** Supplier commits to full quantity but pushes delivery date 9 business days past contractual `RDD`.
- **Input (Supplier Email):**
  ```text
  From: dispatch@precisiondynamics.example.com
  To: purchasing@apexindustrial.example.com
  Subject: Acknowledgment & Schedule Revision: PO-2026-90412

  Hello Vrushali,
  We acknowledge receipt of PO-2026-90412 for 100 EA of VALVE-HYDR-440. Due to an unexpected delay in casting alloy raw materials from our foundry, we cannot meet the October 26 requested delivery date.
  Our revised confirmed delivery date at your facility is November 06, 2026. Please update your purchase order schedule accordingly.

  Sincerely,
  Mark Evans, Account Representative
  Precision Dynamics Components Corp.
  ```
- **Expected Structured Output:**
  ```json
  {
    "test_id": "TC-DEL-002",
    "po_number": "PO-2026-90412",
    "delivery_status": "DELAYED",
    "edi_ack_code": null,
    "line_reconciliation": [
      {
        "line_number": 1,
        "sku": "VALVE-HYDR-440",
        "quantity_confirmed": 100,
        "quantity_ordered": 100,
        "promised_delivery_date": "2026-11-06",
        "requested_delivery_date": "2026-10-26",
        "variance_business_days": 9
      }
    ],
    "delay_root_cause": "Foundry raw material delay",
    "discrepancy_detected": true,
    "recommended_action": "STAGE_REVISED_DELIVERY_DATE_FOR_HUMAN_REVIEW",
    "human_review_required": true,
    "escalation_tier": "LEVEL_2_EXPEDITING",
    "staged_outbound_communication": {
      "type": "DRAFT_EXPEDITING_INQUIRY",
      "recipient": "dispatch@precisiondynamics.example.com",
      "subject": "Schedule Discrepancy Inquiry: PO-2026-90412",
      "draft_body": "Staged draft requesting supplier confirmation of expedited freight options to recover the 9-day casting delay.",
      "auto_send": false
    }
  }
  ```
- **Acceptance Criteria:** Computes exact variance (+9 business days / +11 calendar days), extracts root cause, classifies as `DELAYED`, mandates human expediter review, and stages draft inquiry with `auto_send: false`.
- **Audit Annotation (Process Owner Decision Applied 2026-10-09):**
  1. *Date Arithmetic Resolution:* Process Owner Vrushali explicitly applied the uniform Monday–Friday business day counting convention (counted weekdays in $(RDD, PDD]$, strictly excluding baseline RDD 2026-10-26 and counting PDD 2026-11-06, zero undeclared holidays). Elapsed time from Monday Oct 26 to Friday Nov 6 encompasses exactly 9 working business days (Oct 27–30 [4] + Nov 2–6 [5]) and 11 calendar days. Updated expected variance from 8 to 9, resolving the mathematical jump to TC-DEL-003 (Monday Nov 9 = 10 business days).
  2. *EDI Provenance Consistency:* Retained `edi_ack_code: null` in accordance with the plain email data provenance rule.

---

### Test Case 3: `TC-DEL-003` — Partial Delivery & Split Schedule Line

- **Scenario:** Supplier ships 60% of order on time; remaining 40% delayed by 2 weeks.
- **Input (Supplier Email):**
  ```text
  From: dispatch@precisiondynamics.example.com
  To: purchasing@apexindustrial.example.com
  Subject: Partial Fulfillment Notice: PO-2026-90412

  Hi Vrushali,
  Regarding PO-2026-90412 for 100 units of VALVE-HYDR-440:
  We currently have only 60 units in finished goods inventory. We will ship these 60 units to arrive on your original requested date of October 26, 2026.
  The remaining 40 units are currently on our machining line and will arrive at your dock on November 09, 2026.

  Regards,
  Precision Dynamics Shipping
  ```
- **Expected Structured Output:**
  ```json
  {
    "test_id": "TC-DEL-003",
    "po_number": "PO-2026-90412",
    "delivery_status": "PARTIAL_DELIVERY",
    "edi_ack_code": null,
    "line_reconciliation": [
      {
        "line_number": 1,
        "sku": "VALVE-HYDR-440",
        "split_schedule": [
          {
            "schedule_line": 1,
            "quantity_confirmed": 60,
            "promised_delivery_date": "2026-10-26",
            "delivery_status": "ON_TIME"
          },
          {
            "schedule_line": 2,
            "quantity_confirmed": 40,
            "promised_delivery_date": "2026-11-09",
            "delivery_status": "DELAYED",
            "variance_business_days": 10
          }
        ],
        "total_confirmed_quantity": 100,
        "ordered_quantity": 100
      }
    ],
    "discrepancy_detected": true,
    "recommended_action": "STAGE_SPLIT_SCHEDULE_LINES_FOR_HUMAN_REVIEW",
    "human_review_required": true,
    "escalation_tier": "LEVEL_1_INVENTORY_ALERT",
    "staged_outbound_communication": null
  }
  ```
- **Acceptance Criteria:** Computes split allocation (60 / 40), assigns delivery status `PARTIAL_DELIVERY` with `edi_ack_code: null` (reflecting plain-email transmission provenance), verifies second schedule line variance (+10 business days / +14 calendar days), produces dual staged schedule lines, and mandates human review to authorize ERP split and alert P03.
- **Audit Annotation (Process Owner Decision Applied 2026-10-09):**
  1. *EDI Provenance Enforcement:* Changed expected `edi_ack_code` from `"BP"` to `null` because unstructured supplier emails transmit no EDI transaction syntax, preserving data provenance per `evidence.md` (`EVD-P02-002`). The operational split is accurately captured by `delivery_status: "PARTIAL_DELIVERY"`.
  2. *Date Arithmetic Verification:* Confirmed that Monday 2026-11-09 is exactly 10 business days past Monday 2026-10-26 under the uniform Monday–Friday counting convention (counted weekdays in $(RDD, PDD]$: 9 weekdays through Nov 6 + Monday Nov 9) and 14 calendar days.

---

### Test Case 4: `TC-DEL-004` — Missing Delivery Date

- **Scenario:** Supplier acknowledges receipt of order but omits promised delivery or ship date.
- **Input (Supplier Email):**
  ```text
  From: dispatch@precisiondynamics.example.com
  To: purchasing@apexindustrial.example.com
  Subject: RE: PO-2026-90412

  Thank you for your order PO-2026-90412 for the hydraulic valves. We have entered this into our production queue.
  We look forward to doing business with you.

  Kind regards,
  Customer Support
  ```
- **Expected Structured Output:**
  ```json
  {
    "test_id": "TC-DEL-004",
    "po_number": "PO-2026-90412",
    "delivery_status": "MISSING_DATE",
    "edi_ack_code": null,
    "line_reconciliation": [
      {
        "line_number": 1,
        "sku": "VALVE-HYDR-440",
        "quantity_confirmed": null,
        "promised_delivery_date": null,
        "requested_delivery_date": "2026-10-26"
      }
    ],
    "discrepancy_detected": true,
    "ambiguity_tier": "A2",
    "recommended_action": "STAGE_CLARIFICATION_REQUEST_FOR_HUMAN_APPROVAL",
    "human_review_required": true,
    "staged_outbound_communication": {
      "type": "DRAFT_CLARIFICATION_INQUIRY",
      "recipient": "dispatch@precisiondynamics.example.com",
      "subject": "Delivery Date Confirmation Required: PO-2026-90412",
      "draft_body": "Dear Precision Dynamics, thank you for accepting PO-2026-90412. Please confirm your promised dock delivery date for the 100 units of VALVE-HYDR-440.",
      "auto_send": false
    }
  }
  ```
- **Acceptance Criteria:** Rejects incomplete confirmation; does NOT fabricate or default a date; assigns ambiguity `A2`; generates draft clarification inquiry with `auto_send: false`; requires human approval.

---

### Test Case 5: `TC-DEL-005` — Conflicting Delivery Dates

- **Scenario:** Email body states one delivery date, while attached PDF confirmation table states a conflicting date.
- **Input (Supplier Email + Attachment Metadata):**
  ```text
  From: dispatch@precisiondynamics.example.com
  To: purchasing@apexindustrial.example.com
  Subject: PO-2026-90412 Acknowledgment & PDF

  Hi Vrushali,
  We have processed order PO-2026-90412. The valves will be delivered to your dock on October 27, 2026.
  Please see attached formal confirmation slip for your records.

  [Attachment: Precision_Dynamics_Ack_90412.pdf]
  Attachment Text:
  "Line 1 | VALVE-HYDR-440 | Qty: 100 | Estimated Dock Delivery Date: 2026-11-18 | Terms: DAP"
  ```
- **Expected Structured Output:**
  ```json
  {
    "test_id": "TC-DEL-005",
    "po_number": "PO-2026-90412",
    "delivery_status": "CONFLICTING_DATES",
    "edi_ack_code": null,
    "discrepancy_details": {
      "body_date": "2026-10-27",
      "attachment_date": "2026-11-18",
      "variance_between_sources_calendar_days": 22
    },
    "discrepancy_detected": true,
    "ambiguity_tier": "A2",
    "recommended_action": "HOLD_TRANSACTION_AND_ESCALATE_TO_BUYER",
    "human_review_required": true,
    "escalation_tier": "HUMAN_EXPEDITER_REVIEW",
    "staged_outbound_communication": null
  }
  ```
- **Acceptance Criteria:** Detects 22-day contradiction between body and attachment; halts automated processing; tags ambiguity as `A2`; mandates human expediter review.

---

### Test Case 6: `TC-DEL-006` — Critical Exception Requiring Human Review

- **Scenario:** Supplier reports component obsolescence and engineering hold, proposing part substitution and price increase.
- **Input (Supplier Email):**
  ```text
  From: engineering@precisiondynamics.example.com
  To: purchasing@apexindustrial.example.com
  Subject: URGENT: Engineering Hold on PO-2026-90412 (VALVE-HYDR-440)

  Dear Vrushali,
  We cannot fulfill Purchase Order PO-2026-90412 as specified. The internal spool casting for VALVE-HYDR-440 has been declared obsolete by our engineering division due to material fatigue bulletins.
  We cannot commit to any delivery date at this time. An Engineering Change Order (ECO) is required to substitute with model VALVE-HYDR-450 (unit cost $285.00). Please advise immediately.

  Best regards,
  Dr. Alan Reynolds, VP Quality
  Precision Dynamics Components Corp.
  ```
- **Expected Structured Output:**
  ```json
  {
    "test_id": "TC-DEL-006",
    "po_number": "PO-2026-90412",
    "delivery_status": "CRITICAL_EXCEPTION",
    "edi_ack_code": null,
    "exception_type": "PART_OBSOLESCENCE_AND_SUBSTITUTION_REQUEST",
    "discrepancy_details": {
      "substitute_part": "VALVE-HYDR-450",
      "price_delta": 40.00,
      "delivery_date": null
    },
    "discrepancy_detected": true,
    "ambiguity_tier": "A3",
    "recommended_action": "HALT_PROCESSING_AND_ESCALATE_TO_COMMERCIAL_BUYER",
    "human_review_required": true,
    "escalation_tier": "LEVEL_3_COMMERCIAL_ENGINEERING_REVIEW",
    "prohibited_actions": [
      "DO_NOT_AUTO_APPROVE_PRICE_INCREASE",
      "DO_NOT_AUTO_SUBSTITUTE_SKU",
      "DO_NOT_CLOSE_PO",
      "DO_NOT_DISPATCH_UNAPPROVED_SUPPLIER_REPLY"
    ],
    "staged_outbound_communication": null
  }
  ```
- **Acceptance Criteria:** Identifies unauthorized price increase ($245 $\rightarrow$ $285) and SKU substitution attempt; halts all automation; strictly enforces prohibition against price/SKU modifications; routes to commercial buyer.

---

## 4. Proposed Shared Validation Structure

To enable shared automated testing across the team without violating contributor folder boundaries, the following directory structure is proposed for Coordinator Chiranjeevi's approval:

```text
research/procurement/validation/DELIVERY-001/
├── README.md                          # Benchmark introduction, scope, and evaluation harness instructions
├── DELIVERY-001-ART-Agent-Prompt.md   # System prompt and input contracts for the test runner
├── DELIVERY-001-Gold-Answer-Key.md    # Definitive expected JSON outputs for TC-DEL-001 through TC-DEL-006
├── DELIVERY-001-Test-Checklist.md     # Pass/Fail verification scorecard for human and automated review
└── DELIVERY-001-Test-Document.md      # Synthetic raw input corpus containing the 6 test emails/attachments
```

*Status: Proposal ready for coordinator review. Files will only be created in the shared validation directory after Chiranjeevi's explicit sign-off.*

---

## 5. Specification Audit Notes & Process Owner Decision Log (Audited & Decided 2026-10-09)

This section documents the formal specification audit conducted on October 9, 2026 by Vrushali (Owner of P02-SUPPLIER-DELIVERY) in accordance with `RESEARCH_STANDARD.md` and `evidence.md`, together with the formal resolutions applied to the synthetic benchmark.

*Execution Notice:* This document remains a synthetic benchmark specification. No ART tests were executed, no test runner was invoked, and no synthetic test case is claimed to have passed.

### 5.1 Audit Findings & Technical Reconciliation Summary

1. **TC-DEL-001 Date & Sign Arithmetic Reconciliation:**
   - *Previous State:* Expected JSON specified `"promised_delivery_date": "2026-10-24"` (Saturday) and `"variance_business_days": -2`, while Acceptance Criteria ambiguously stated "verifies non-negative variance". Furthermore, October 24, 2026 was a Saturday, introducing ambiguity regarding Chicago dock receiving operations.
   - *Resolution:* Process Owner Vrushali explicitly changed the synthetic promised delivery date to **Thursday, October 22, 2026**. Under the adopted counting convention (counting weekdays in $[PDD, RDD)$ and negating the count, strictly excluding baseline RDD Monday Oct 26 and counting promised PDD Thursday Oct 22), the counted working days are Thursday Oct 22 and Friday Oct 23, yielding unambiguously **-2 business days** (and -4 calendar days) ahead of schedule without assuming weekend dock operations. Acceptance criteria updated to verify negative business-day variance.

2. **TC-DEL-002 Date Arithmetic Alignment (+9 Business Days):**
   - *Previous State:* Scenario text, expected JSON, and criteria stated 8 business days for a promised date of Friday, November 6, 2026 against baseline Monday, October 26, 2026. This conflicted with TC-DEL-003 (Monday, November 9 stated as 10 business days).
   - *Resolution:* Under the adopted uniform counting convention (Monday–Friday weekdays, counted in $(RDD, PDD]$, excluding baseline RDD, counting PDD, zero undeclared holidays), the weekdays elapsed between Oct 26 and Nov 6 are Oct 27–30 (4 days) + Nov 2–6 (5 days) = **9 business days** (and 11 calendar days). Updated scenario text, expected JSON (`variance_business_days: 9`), staged outbound inquiry draft text, and acceptance criteria to 9 business days, achieving mathematical harmony with TC-DEL-003.

3. **TC-DEL-003 Date Arithmetic Verification (+10 Business Days):**
   - *Audit Verification:* For the second schedule line promised for Monday, November 9, 2026 against baseline Monday, October 26, 2026, the counted weekdays in $(RDD, PDD]$ are Oct 27–30 (4 days) + Nov 2–6 (5 days) + Nov 9 (1 day) = **10 business days** (and 14 calendar days / 2 calendar weeks). Value verified and retained.

4. **EDI Transmission Code vs. Plain Email Provenance Boundary:**
   - *Previous State:* `TC-DEL-001` assigned `"edi_ack_code": "IA"` and `TC-DEL-003` assigned `"edi_ack_code": "BP"`, whereas `TC-DEL-002`, `TC-DEL-004`, `TC-DEL-005`, and `TC-DEL-006` assigned `"edi_ack_code": null`.
   - *Governing Evidence:* Per `evidence.md` (`EVD-P02-002`), unstructured supplier emails contain no EDI transmission syntax or segment envelopes. Assigning an EDI transaction code to an email extraction conflates an EDI syntax standard with an analytical classification.
   - *Resolution:* Process Owner Vrushali ordered strict data provenance: `"edi_ack_code": null` is enforced across all email-only test cases (`TC-DEL-001` through `TC-DEL-006`). Analytical delivery status remains independently evaluated via `"delivery_status"` (`ON_TIME`, `DELAYED`, `PARTIAL_DELIVERY`, etc.).

5. **Safety Invariants Compliance:**
   - *Audit Result: FULLY COMPLIANT.* All 6 scenarios strictly adhere to safety invariants: no direct ERP writes (`STAGE_*`), no automatic dispatches (`auto_send: false`), strict prohibition on unauthorized price/SKU modifications (`TC-DEL-006`), and mandatory human review for consequential exceptions (`human_review_required: true`).

6. **Extracted vs. Inferred/Defaulted Values:**
   - Baseline PO context (`requested_delivery_date: 2026-10-26`, `quantity_ordered: 100`, unit price `$245.00`) is correctly joined with email extraction. In `TC-DEL-006`, the `$40.00` price delta is an inferred calculation ($285.00 - $245.00), not an explicit string extracted from the email.

---

### 5.2 Process Owner Explicit Decisions Applied (Vrushali, 2026-10-09)

The following three formal policy decisions were explicitly established by Process Owner Vrushali and applied across the benchmark:

1. **Decision 1: Business-Day Variance Counting Convention:**
   - *Policy Adopted:* Standard Monday–Friday weekdays only; strictly excludes the baseline contractual Requested Delivery Date (`RDD`) and counts the Promised Delivery Date (`PDD`). For early delivery ($PDD < RDD$), count standard weekdays in $[PDD, RDD)$ and negate the count; for late delivery ($PDD > RDD$), count standard weekdays in $(RDD, PDD]$ and keep the count positive. No public, federal, state, or plant shutdown holidays are excluded unless an explicit holiday calendar is declared in a specific test scenario.
   - *Mathematical Outcomes Confirmed:*
     - `TC-DEL-001` (Promised 2026-10-22 vs RDD 2026-10-26): **-2 business days** (calendar delta = -4 days).
     - `TC-DEL-002` (Promised 2026-11-06 vs RDD 2026-10-26): **+9 business days** (calendar delta = +11 days).
     - `TC-DEL-003` Line 2 (Promised 2026-11-09 vs RDD 2026-10-26): **+10 business days** (calendar delta = +14 days).

2. **Decision 2: Synthetic Promised Delivery Date for TC-DEL-001:**
   - *Policy Adopted:* Synthetic promised delivery date changed from Saturday, October 24, 2026 to **Thursday, October 22, 2026**.
   - *Rationale:* Eliminates ungrounded assumptions regarding weekend dock operations at the Chicago receiving facility while keeping the scenario an ahead-of-schedule confirmation with an unambiguous `-2` business-day variance.

3. **Decision 3: EDI Acknowledgment Code Provenance in Unstructured Emails:**
   - *Policy Adopted:* Set `"edi_ack_code": null` across all email-only test cases (`TC-DEL-001` through `TC-DEL-006`).
   - *Rationale:* Strictly enforces the semantic boundary documented in `evidence.md` (`EVD-P02-002`). Unstructured emails do not transmit EDI transactions; analytical status is captured by `delivery_status` rather than relabeling interpretations as transmitted EDI codes.

---

### 5.3 Genuinely Unresolved Governance & Cross-Process Matters

The following items remain pending external coordinator or cross-process alignment:
1. **Shared Validation Directory Authorization:**
   - Creation of shared test files under `research/procurement/validation/DELIVERY-001/` remains a proposal awaiting formal sign-off from Coordinator Chiranjeevi (`Chiranjeevi005`).
2. **Central Register Synchronization:**
   - Integration of P02 findings into central shared registers ([`EVIDENCE_REGISTER.md`](../../EVIDENCE_REGISTER.md), [`AMBIGUITIES.md`](../../AMBIGUITIES.md), [`DECISIONS.md`](../../DECISIONS.md)) remains blocked pending coordinator authorization.
3. **External Benchmarking Portals (`EVD-P02-004`):**
   - Access to APQC and CAPS Research portals returned HTTP 403 Forbidden; quantitative expediting savings claims remain unverified `E0` hypotheses.
