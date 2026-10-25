# OPP-006 — Field-Service Policy-Arbitration Decision

## Opportunity identity

| Field | Value |
|---|---|
| Object ID | `AOI-SNOW-OPP-006` |
| Company | ServiceNow |
| Original opportunity | Field Service Exception Decision Intelligence |
| Refined opportunity | Residual policy-arbitration intelligence |
| Scope | Whether complex field-service context creates recurring human policy-selection burden beyond finite policies, objectives, constraints, overrides, and optimization |
| Checkpoints | [`OPP-006-01`](./OPP-006-01.md) → [`OPP-006-02`](./OPP-006-02.md) → [`OPP-006-03`](./OPP-006-03.md) → [`OPP-006-04`](./OPP-006-04.md) → [`OPP-006-05`](./OPP-006-05.md) → [`OPP-006-06`](./OPP-006-06.md) |
| Investigation types | Discovery; conflict reconstruction; dispatcher judgment; policy selection; complexity test; residual arbitration test |
| Research status | KILLED — residual ServiceNow gap not established |
| AOI decision | KILL |
| AIL status | NOT READY FOR AIL |
| Evidence classification | VERIFIED EXTERNAL EVIDENCE; DIRECT EVIDENCE; INFERENCE; HYPOTHESIS; UNKNOWN |
| Generation metadata | AOI Representation Compiler v0.2; generated 2026-08-20; canonical Markdown only |

## Consolidated intelligence state

Field-service scheduling complexity, competing objectives, changing conditions, policy variation, and human exceptions are real. Current ServiceNow evidence shows policies, weighted objectives, hard/soft constraints, dynamic and intraday optimization, policy switching, contextual overrides, preferred technicians, appointment overrides, and manual exceptions. The proposed recurring material policy-arbitration burden was not established.

## Hypothesis lifecycle

1. Field-service exceptions may expose a new decision domain.
2. Real conflicts and multi-objective dispatcher judgment were verified.
3. The hypothesis narrowed to context-dependent policy selection and then policy explosion/arbitration.
4. Native capability testing showed the platform can encode objectives, constraints, policies, dynamic reoptimization, context variation, and human override.
5. **Final:** recurring material customer burden and ServiceNow-specific gap remain NOT ESTABLISHED. **KILL.**

## Evidence and counter-evidence

| Finding | Classification | Effect |
|---|---|---|
| Multi-skill, multi-objective field-service scheduling | VERIFIED EXTERNAL EVIDENCE | Underlying complexity is real. |
| Policies, objectives, weights, and constraints | DIRECT EVIDENCE | Core decision representation is native. |
| Dynamic and intraday optimization | DIRECT EVIDENCE | Changing conditions are supported. |
| Dispatcher-selected policy and contextual overrides | DIRECT EVIDENCE | Policy adaptation is supported. |
| Manual exception and preference mechanisms | DIRECT EVIDENCE | Human involvement is designed into the workflow. |
| Policy explosion, recurring error, material loss | UNKNOWN / NOT ESTABLISHED | Residual opportunity fails. |

## Reusable intelligence

| Pattern | Intelligence | Classification |
|---|---|---|
| Policy + objective + constraint stack | `POLICY → OBJECTIVES + WEIGHTS + CONSTRAINTS → OPTIMIZATION` | DIRECT EVIDENCE |
| Automatic reoptimization + human exception | Normal conditions automate; material exceptions permit dispatcher policy change or override; reoptimize. | DIRECT EVIDENCE |
| Contextual configuration overrides | Group, territory, time, and attribute context can change behavior. | DIRECT EVIDENCE |
| Configuration-first falsification | Test policy, objective, constraint, override, automation, and human-exception surfaces before claiming an AI gap. | REUSABLE RESEARCH METHODOLOGY |

## Final decision

**KILL OPP-006.** Do not create another field-service checkpoint or convert it to AIL. Start a new decision domain.

## Source register

- [Create policies for Schedule Optimization](https://www.servicenow.com/docs/r/field-service-management/field-service-scheduling/create-policies-schedule-optimization.html)
- [Objectives and constraints](https://www.servicenow.com/docs/r/field-service-management/hard-soft-constraints.html)
- [On-demand optimization](https://www.servicenow.com/docs/r/field-service-management/field-service-scheduling/configure-on-demand-optimization.html)
- [Intraday optimization](https://www.servicenow.com/docs/r/field-service-management/field-service-scheduling/configure-intraday-optimization.html)
- [Dynamic Scheduling](https://www.servicenow.com/docs/r/field-service-management/field-service-scheduling/Configure-dynamic-scheduling.html)
- [Prevent excluded technicians](https://www.servicenow.com/docs/r/field-service-management/field-service-scheduling/prevent-excluded-agents.html)
- [Multi-objective field-service research](https://doi.org/10.1016/j.cor.2020.104908)
- [Field-service routing and scheduling research](https://doi.org/10.1016/j.cor.2021.105472)

## Research integrity

KILL reflects an evidence failure at the residual opportunity boundary, not a claim that field-service complexity or human judgment is unreal.
