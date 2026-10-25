# OPP-008 — Hospital Patient-Flow Cross-System Decision Synthesis

## Opportunity identity

| Field | Value |
|---|---|
| Object ID | `AOI-SNOW-OPP-008` |
| Company | ServiceNow |
| Original opportunity | Hospital-Wide Patient-Flow Decision Coordination |
| Refined opportunity | Cross-System Decision-Synthesis / Reconciliation |
| Scope | Whether hospital command centres retain a material, repeatable decision burden when specialized systems are incomplete, conflicting, or context-dependent |
| Checkpoints | [`OPP-008-01`](./OPP-008-01.md) → [`OPP-008-02`](./OPP-008-02.md) → [`OPP-008-03`](./OPP-008-03.md) → [`OPP-008-04`](./OPP-008-04.md) → [`OPP-008-05`](./OPP-008-05.md) → [`OPP-008-06`](./OPP-008-06.md) → [`OPP-008-07`](./OPP-008-07.md) |
| Investigation types | Discovery; real patient-flow decision; native reconstruction; multi-constraint test; criteria reconstruction; cross-system synthesis; real reconciliation test |
| Research status | KILLED — required event-level residual hypothesis not demonstrated |
| AOI decision | KILL |
| AIL status | NOT READY FOR AIL |
| Evidence classification | VERIFIED EXTERNAL EVIDENCE; DIRECT EVIDENCE; INFERENCE; HYPOTHESIS; UNKNOWN; NOT DEMONSTRATED |
| Generation metadata | AOI Representation Compiler v0.2; generated 2026-08-20; canonical Markdown only |

## Consolidated intelligence state

Hospital patient-flow complexity, multi-system architecture, data-quality problems, human verification, central coordination, prescriptive support, and bottleneck intervention are verified. The final checkpoint could not reconstruct one real event containing multiple systems, conflict or stale data, human reconciliation, explicit trade-off, action, and measured outcome. A ServiceNow-specific gap is therefore not established.

## Hypothesis lifecycle

1. Hospital-wide patient flow was identified as a new consequential decision domain.
2. Real patient-flow and bottleneck decisions were reconstructed.
3. Broad coordination, generic resource allocation, and workflow gaps were killed by existing capability evidence.
4. The hypothesis narrowed to cross-system decision synthesis and human reconciliation.
5. Seven-system fragmentation and general data verification were found, but not in one complete event. Prescriptive analytics and human adjudication were counter-evidence to a generic “dashboard only” gap.
6. **Final:** specific cross-system reconciliation opportunity NOT DEMONSTRATED. **KILL.**

## Evidence and counter-evidence

| Finding | Classification | Effect |
|---|---|---|
| Seven disconnected systems at Johns Hopkins | DIRECT VERIFIED EXTERNAL EVIDENCE | Integration problem established generally. |
| Predictive and prescriptive analytics with recommended bed placement | DIRECT VERIFIED EXTERNAL EVIDENCE | Weakens assumption that humans manually synthesize everything. |
| Human adjudication of disputed beds and complex transfers | DIRECT VERIFIED EXTERNAL EVIDENCE | Human role established, exact burden not. |
| NHS triangulation and data verification | DIRECT VERIFIED EXTERNAL EVIDENCE | Workflow-level discrepancy established, not event-level reconciliation. |
| Hospital U discharge-bottleneck intervention | DIRECT VERIFIED EXTERNAL EVIDENCE | Real action established, but not multi-system conflict/trade-off/outcome chain. |
| Required real cross-system reconciliation event | NOT DEMONSTRATED | Final hypothesis killed. |

## Reusable intelligence

| Pattern | Intelligence | Limitation |
|---|---|---|
| Seven-system integration | Disconnected systems → integration layer → real-time command centre. | Do not assume integration problem equals decision-synthesis problem. |
| Progressive analytics maturity | Descriptive → predictive → prescriptive → recommended placement → human decision. | Test the exact residual layer. |
| Human adjudication | Central human role may be clinical judgment, governance, exception handling, conflict resolution, or data verification. | Human involvement alone is not an automation gap. |
| Data verification despite integration | Integrated systems can still require triangulation because records are stale, incomplete, or inaccurate. | Each data-trust opportunity requires independent evidence. |
| Bottleneck intervention | Expected state → actual state → variance → barrier → targeted intervention. | The source did not provide a measured event-level outcome. |
| Centralization with local autonomy | Recommend does not equal command; authority and professional autonomy remain relevant. | General pattern, not a ServiceNow opportunity. |

## Final decision

**KILL OPP-008.** Preserve the workflow and implementation patterns, but do not create AIL intake or rescue the unsupported residual hypothesis.

## Source register

- [Johns Hopkins command-centre design](https://doi.org/10.1016/j.jcjq.2018.11.006)
- [Johns Hopkins implementation PDF](https://www.gehccommandcenter.com/hubfs/CC2020/docs/JCJQPS-Johns-Hopkins-Use-of-Systems-Engineering-to-Design-A-Hospital-Command-Center.pdf)
- [2026 hospital patient-flow study](https://doi.org/10.1080/09537287.2026.2655748)
- [NHS AI command-centre scientific summary](https://www.ncbi.nlm.nih.gov/books/NBK608696/)
- [NHS ethnographic findings](https://www.ncbi.nlm.nih.gov/books/NBK608708/)
- [Hospital control-centre human-factors review](https://doi.org/10.1007/s10916-024-02071-1)
- [NHS command-centre outcome evaluation](https://doi.org/10.1093/intqhc/mzad072)
- [Dedalus AI command-centre architecture](https://www.dedalus.com/global/wp-content/uploads/sites/9/2026/06/Why-hospitals-must-rethink-operations-in-the-age-of-AI-compress.pdf)

## Research integrity

The final state distinguishes verified workflow patterns from the missing event-level proof. It does not claim that cross-system reconciliation never occurs.
