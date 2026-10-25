# OPP-006 — Investigation walkthrough

## Representation metadata

| Field | Value |
|---|---|
| Object ID | `AOI-SNOW-OPP-006` |
| Source research files | [`OPP-006-01.md`](./OPP-006-01.md), [`OPP-006-02.md`](./OPP-006-02.md), [`OPP-006-03.md`](./OPP-006-03.md), [`OPP-006-04.md`](./OPP-006-04.md), [`OPP-006-05.md`](./OPP-006-05.md), [`OPP-006-06.md`](./OPP-006-06.md) |
| Company | ServiceNow |
| Opportunity | Field-Service Policy-Arbitration Decision |
| Checkpoint sequence | OPP-006-01 → OPP-006-02 → OPP-006-03 → OPP-006-04 → OPP-006-05 → OPP-006-06 |
| Investigation type | Discovery → conflict → judgment → policy selection → residual-gap test |
| Research status | KILLED |
| AOI decision | KILL |
| Evidence classification | VERIFIED EXTERNAL EVIDENCE; DIRECT EVIDENCE; INFERENCE; HYPOTHESIS; UNKNOWN |
| Generation metadata | AOI Representation Compiler v0.2; generated 2026-08-20 |

## Causal investigation chain

```text
FIELD-SERVICE COMPLEXITY
   ↓
REAL CONFLICTS AND MULTI-OBJECTIVE JUDGMENT
   ↓
CONTEXT-DEPENDENT POLICY SELECTION
   ↓
NATIVE POLICY / OBJECTIVE / CONSTRAINT / OVERRIDE EVIDENCE
   ↓
NO PROVEN POLICY EXPLOSION OR MATERIAL BURDEN
   ↓
KILL OPP-006
```

## Initial question and hypothesis

The investigation began by searching a new business decision domain after OPP-005. The initial hypothesis was that field-service exceptions might require intelligence beyond native scheduling. After real conflicts were found, it narrowed to whether dispatchers face recurring policy-arbitration burden that cannot be encoded economically.

## Checkpoint history

| Checkpoint | What changed | Evidence that caused the change | Result |
|---|---|---|---|
| [`OPP-006-01`](./OPP-006-01.md) | Field service became a candidate decision domain. | New-domain discovery identified exceptions and dispatch decisions. | CONTINUE; candidate not established. |
| [`OPP-006-02`](./OPP-006-02.md) | Real field-service conflict evidence was reconstructed. | Conflicting priorities, resources, skills, time, and customer consequences were documented. | Continue; ServiceNow gap not yet established. |
| [`OPP-006-03`](./OPP-006-03.md) | The candidate narrowed to multi-objective dispatcher judgment. | External complexity was compared with ServiceNow’s objective/constraint model. | Continue only for final narrowing. |
| [`OPP-006-04`](./OPP-006-04.md) | Context-dependent policy selection was verified as a real pattern. | Multiple operating modes and policy changes were identified. | Hypothesis weakened; native policy selection needed testing. |
| [`OPP-006-05`](./OPP-006-05.md) | The residual claim became policy explosion/arbitration. | No customer evidence showed many conflicting policies, selection errors, or material consequence. | Evidence threshold raised. |
| [`OPP-006-06`](./OPP-006-06.md) | Final residual test covered policy, weights, constraints, optimization, overrides, and dispatcher control. | Current ServiceNow documentation supplied each mechanism. | Residual gap NOT ESTABLISHED; KILL. |

## Evidence → refinement → falsification

- **Evidence:** Field-service scheduling has real multi-objective complexity. **Classification:** VERIFIED EXTERNAL EVIDENCE.
- **Native evidence:** ServiceNow separates hard constraints from soft objectives, supports weights, multiple policies, dynamic/intraday optimization, policy switching, and overrides. **Classification:** DIRECT EVIDENCE.
- **Hypothesis:** Context combinations exceed finite policy representation and cause recurring material human burden. **Classification:** HYPOTHESIS / NOT ESTABLISHED.
- **Counter-evidence:** No reliable customer evidence of policy explosion, recurring selection errors, or material loss was found. **Classification:** UNKNOWN / NOT ESTABLISHED.
- **Decision:** KILL OPP-006.

## What was killed and what survived

| Item | State |
|---|---|
| “ServiceNow cannot handle multi-objective scheduling” | REJECTED |
| “ServiceNow cannot adapt to changing conditions” | REJECTED |
| “ServiceNow cannot use different policies” | REJECTED |
| “Human policy selection is itself a gap” | REJECTED |
| Recurring customer policy-arbitration burden | NOT ESTABLISHED; opportunity KILLED |
| Field-service policy/optimization patterns | SURVIVE as reusable intelligence |

## Traceability

| Derived statement | Research location | Source URL |
|---|---|---|
| Policies, objectives, and constraints are native | [`OPP-006-06`, §§6–8](./OPP-006-06.md) | [Policies](https://www.servicenow.com/docs/r/field-service-management/field-service-scheduling/create-policies-schedule-optimization.html); [constraints](https://www.servicenow.com/docs/r/field-service-management/hard-soft-constraints.html) |
| Policy can change with conditions | [`OPP-006-06`, §§9–13](./OPP-006-06.md) | [On-demand optimization](https://www.servicenow.com/docs/r/field-service-management/field-service-scheduling/configure-on-demand-optimization.html); [intraday optimization](https://www.servicenow.com/docs/r/field-service-management/field-service-scheduling/configure-intraday-optimization.html) |
| Recurring material burden was not established | [`OPP-006-06`, §§17–21](./OPP-006-06.md) | Canonical source register in [`OPP-006-06.md`](./OPP-006-06.md) |

## Research integrity

The progression preserves that the domain became more real while the ServiceNow-specific opportunity became less defensible.
