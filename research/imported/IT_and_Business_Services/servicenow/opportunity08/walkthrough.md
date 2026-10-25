# OPP-008 — Investigation walkthrough

## Representation metadata

| Field | Value |
|---|---|
| Object ID | `AOI-SNOW-OPP-008` |
| Source research files | [`OPP-008-01.md`](./OPP-008-01.md) through [`OPP-008-07.md`](./OPP-008-07.md) |
| Company | ServiceNow |
| Opportunity | Hospital Patient-Flow Cross-System Decision Synthesis |
| Checkpoint sequence | OPP-008-01 → OPP-008-02 → OPP-008-03 → OPP-008-04 → OPP-008-05 → OPP-008-06 → OPP-008-07 |
| Investigation type | Discovery → decision reconstruction → native test → criteria → cross-system reconciliation |
| Research status | KILLED |
| AOI decision | KILL |
| Evidence classification | VERIFIED EXTERNAL EVIDENCE; DIRECT EVIDENCE; INFERENCE; HYPOTHESIS; UNKNOWN; NOT DEMONSTRATED |
| Generation metadata | AOI Representation Compiler v0.2; generated 2026-08-20; no additional research |

## Causal investigation chain

```text
HOSPITAL PATIENT-FLOW COMPLEXITY
   ↓
REAL CENTRAL COORDINATION AND BOTTLENECK ACTION
   ↓
NATIVE COORDINATION / RESOURCE / AI TESTS
   ↓
CROSS-SYSTEM SYNTHESIS HYPOTHESIS
   ↓
GENERAL FRAGMENTATION AND VERIFICATION EVIDENCE
   ↓
NO COMPLETE EVENT-LEVEL RECONCILIATION CHAIN
   ↓
KILL OPP-008
```

## Initial question and hypothesis

The initial question was whether patient-flow coordination exposed a decision domain not covered by ServiceNow. The initial hypothesis was broad: hospital-wide, multi-constraint coordination might need a specialized decision layer. It narrowed to a much stronger requirement: one real event with multiple systems, conflict or stale data, human reconciliation, explicit criteria, trade-off, action, and outcome.

## Checkpoint history and causal relationships

| Checkpoint | What changed | Evidence / counter-evidence | Result |
|---|---|---|---|
| [`OPP-008-01`](./OPP-008-01.md) | Patient-flow coordination became a candidate domain. | Real hospital command-centre patterns and decisions were identified. | CONTINUE; ServiceNow gap not established. |
| [`OPP-008-02`](./OPP-008-02.md) | A real patient-flow decision was reconstructed. | Central capacity, demand, and discharge decisions were documented. | Native capability test required. |
| [`OPP-008-03`](./OPP-008-03.md) | Basic workflow, healthcare AI coordination, capacity optimization, and integration were tested. | Existing capabilities killed broad coordination/resource gaps; a narrower synthesis hypothesis survived. | REFINE. |
| [`OPP-008-04`](./OPP-008-04.md) | Multi-constraint decision criteria and coordination were reconstructed. | Basic workflow and generic optimization were killed; hospital-wide synthesis remained a hypothesis. | CONTINUE narrowly. |
| [`OPP-008-05`](./OPP-008-05.md) | Decision modes and context-dependent criteria were made explicit. | Generic workflow, resource, predictive, and information gaps were killed; cross-system synthesis remained a hypothesis. | CONTINUE narrowly. |
| [`OPP-008-06`](./OPP-008-06.md) | The hypothesis required a real cross-system reconciliation event. | Seven-system fragmentation, verification, command-centre integration, prescriptive support, and human adjudication were found. | Continue to final event test. |
| [`OPP-008-07`](./OPP-008-07.md) | Hospital U supplied a real intervention, but not the required conflict/reconciliation/trade-off/outcome chain. | Evidence matrix left key event-level elements unknown. | NOT DEMONSTRATED; KILL. |

## Evidence → counter-evidence → decision

- **Evidence:** Multiple hospital systems, integration difficulty, data verification, central coordination, prescriptive analytics, and bottleneck intervention are real. **Classification:** VERIFIED EXTERNAL EVIDENCE.
- **Counter-evidence:** Hopkins already had prescriptive bed-placement support; modern command centres integrate data and may orchestrate conflicting actions. **Classification:** VERIFIED EXTERNAL / industry evidence.
- **Hypothesis:** A material, repeatable cross-system reconciliation burden remains. **Classification:** HYPOTHESIS.
- **Final test result:** No single documented event established multiple systems in the same decision, conflict, human reconciliation, trade-off, and measured outcome together. **Classification:** NOT DEMONSTRATED.
- **Decision:** KILL OPP-008 as formulated.

## What was killed and what survived

| Item | State |
|---|---|
| Generic patient-flow coordination gap | KILLED / existing capability and workflow evidence |
| Generic resource-allocation gap | KILLED |
| Information-only / dashboard gap | KILLED by prescriptive counter-evidence |
| Cross-system fragmentation and verification problem | SURVIVES as verified workflow pattern |
| Specific cross-system reconciliation opportunity | NOT DEMONSTRATED; KILLED |
| Integration, data trust, bottleneck, and autonomy patterns | SURVIVE as reusable intelligence |

## Traceability

| Derived statement | Research location | Source URL |
|---|---|---|
| Seven-system fragmentation and prescriptive placement | [`OPP-008-07`, §§3–4, 12](./OPP-008-07.md) | [Hopkins paper](https://doi.org/10.1016/j.jcjq.2018.11.006) |
| Workflow-level data verification | [`OPP-008-07`, §§6–7](./OPP-008-07.md) | [NHS AI command centre](https://www.ncbi.nlm.nih.gov/books/NBK608696/) |
| Real bottleneck action but incomplete event | [`OPP-008-07`, §§8–10](./OPP-008-07.md) | [2026 patient-flow study](https://doi.org/10.1080/09537287.2026.2655748) |
| Required reconciliation chain not demonstrated | [`OPP-008-07`, §§14–16](./OPP-008-07.md) | Canonical source register in [`OPP-008-07.md`](./OPP-008-07.md) |

## Research integrity

The final decision reflects the absence of event-level proof, not a claim that hospitals never reconcile conflicting information.
