# Ambiguity Resolution Protocol: A1 – A4 Operational Standard

> **Standard Authority:** [`../RESEARCH_STANDARD.md`](../RESEARCH_STANDARD.md)  
> **Central Register:** [`../AMBIGUITIES.md`](../AMBIGUITIES.md)  
> **Scope:** Cross-Process Ambiguity Governance

---

## 1. Ambiguity Severity Framework & Execution Gates

Enterprise research inevitably encounters conflicting data, undocumented internal procedures, and unknown software limitations. This protocol defines how to classify, log, and resolve these uncertainties without stalling progress on safe tasks while strictly stopping consequential action on dangerous ones.

| Severity | Level Name | Operational Impact | Research Execution Gate | Implementation / Agent Gate |
|---|---|---|---|---|
| **A1** | Minor Uncertainty | Low; minor terminology, historical date, or non-critical configuration variance. | **CONTINUE:** Log item in register, apply provisional working definition, proceed with research. | **PERMITTED:** Does not affect code or workflow logic. |
| **A2** | Material Uncertainty | Medium; conflicting metrics, unknown exception frequency, or unverified manual workaround. | **INVESTIGATE:** Process owner must actively seek evidence before drawing final conclusions. | **GATED:** Agent workflow may be designed conceptually, but prompt parameters remain provisional. |
| **A3** | Critical Unknown | High; fundamental architectural gap, unknown system API feasibility, or unproven primary premise. | **BLOCKED ON CLAIM:** Cannot advance associated claim beyond `E0`. Must coordinate with team. | **HALTED:** Any autonomous agent proposal or implementation touching this area is blocked. |
| **A4** | Authorization / Safety Risk | Critical; financial liability exposure, statutory tax/legal breach, data privacy violation, or safety issue. | **IMMEDIATE STOP:** Freeze research on affected sub-process; escalate immediately to Coordinator. | **STRICTLY FORBIDDEN:** All consequential execution is locked. |

---

## 2. Mandatory Ambiguity Record Schema

Every ambiguity logged in [`../AMBIGUITIES.md`](../AMBIGUITIES.md) or process files must contain all nine fields:

1. **Ambiguity ID:** Unique identifier formatted as `AMB-P0x-xxx` (e.g., `AMB-P02-003`).
2. **Process & Owner:** Assigned process (`P01`–`P04`) and responsible researcher.
3. **Affected Claim / Step:** Traceable ID of the claim (`CLM-P0x-xxx`) or workflow step (`WF-P0x-xxx`) impacted.
4. **Missing Information:** Clear description of what specific data, rule, or metric is unknown.
5. **Operational Impact:** Analysis of what goes wrong if an incorrect assumption is made.
6. **Required Evidence:** Specific artifact or primary documentation needed to eliminate the uncertainty (e.g., *S/4HANA 2023 release notes for BAPI_PO_CHANGE*).
7. **Responsible Resolver:** Person designated to investigate (typically the process owner).
8. **Status:** One of `OPEN`, `INVESTIGATING`, `RESOLVED`, or `REJECTED_AS_IRRELEVANT`.
9. **Decision & Resolution Date:** Documented resolution summary and date closed.

---

## 3. Step-by-Step Resolution Lifecycle

```text
[Discovery of Gap / Conflict]
             │
             ▼
   [Triage: Classify A1 - A4]
             │
     ┌───────┴───────┐
     ▼               ▼
  [A1 / A2]       [A3 / A4]
     │               │
[Log & Continue]  [Halt Consequential Action & Escalate]
     │               │
     └───────┬───────┘
             ▼
   [Evidence Gathering (Targeted Search / Vendor Manual / Interview)]
             │
             ▼
   [Verification against Quality Gate]
             │
             ▼
   [Close in Central Register: Update Status to RESOLVED]
```

### Resolution Rules:
- **No Resolution by Assertion:** An ambiguity cannot be resolved by an ungrounded opinion or AI assertion. It requires an explicit reference to an accepted evidence record (`EVD-P0x-xxx`).
- **Contradiction Preservation:** If two reputable sources contradict each other (e.g., different lead times), the ambiguity is resolved not by picking one, but by documenting that both behaviors occur in the market under different conditions.
