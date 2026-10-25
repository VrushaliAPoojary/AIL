# Investigation Brief

## Overview

- **Investigation ID:** `OPP-001`
- **Company:** Baby Memorial Hospital, Kozhikode
- **Industry:** Healthcare & Pharmaceuticals
- **Opportunity:** Acute Ischemic Stroke Code / Thrombolysis Coordination
- **Investigation Type:** Specific Hospital + Workflow Discovery / Exception Reconstruction / Pain Validation
- **Research Status:** `BLOCKED`
- **Final Decision:** `HOLD`

## Presentation

### Investigation Summary

Baby Memorial Hospital in Kozhikode was investigated as a high-consequence acute ischemic stroke coordination target. The historical study shows a real digital coordination intervention and meaningful door-to-needle improvement, but current public evidence only confirms ongoing stroke services and visible related software; it does not validate current residual pain. The final brief therefore preserves UNKNOWN states and ends at HOLD rather than inventing a current ART opportunity.

### Key Findings

#### KF-001

BMH is a relevant tertiary-hospital stroke workflow target with historical and current stroke-service context.

- Classification: `INFERENCE`
- Source refs: `SRC-FILE-OPP-001-01`, `SRC-URL-BMH-HOSPITAL`, `SRC-URL-NBE-HOSPITAL-PROFILE`

#### KF-002

The historical mobile-app intervention improved door-to-needle time and threshold performance.

- Classification: `RESULT`
- Source refs: `SRC-FILE-OPP-001-01`, `SRC-FILE-OPP-001-03`, `SRC-URL-PUBMED-32992177`

#### KF-003

Historical delay causes explicitly included patient shifting and imaging.

- Classification: `EVIDENCE`
- Source refs: `SRC-FILE-OPP-001-02`, `SRC-URL-TATD-ACEM-2017-4`

#### KF-004

Current public evidence shows active stroke services and a related app ecosystem, but current residual pain remains unknown.

- Classification: `CLAIM`
- Source refs: `SRC-FILE-OPP-001-04`, `SRC-URL-BMH-NEURO`, `SRC-URL-ACTFAST-ADMIN`, `SRC-URL-PUBMED-30838983`

#### KF-005

If a future ART opportunity exists, it must target the residual exception-orchestration layer rather than core stroke care.

- Classification: `DECISION`
- Source refs: `SRC-FILE-OPP-001-04`

## Decision

### Final Decision

`HOLD`

### Reason

The historical BMH stroke workflow problem is real and the app intervention improved treatment timing, but current residual pain is not directly validated. Public evidence confirms ongoing stroke services and visible related software, yet it does not prove a current manual coordination gap that ART should automate. The correct output is HOLD with UNKNOWN preserved, not a forced PASS.

## Reusable Intelligence

### RI-001

**Title:** Time-critical stroke coordination spans emergency, neurology, imaging, and thrombolysis

- **Type:** `WORKFLOW_PATTERN`
- **Domain:** Healthcare and hospital operations
- **Description:** The stroke pathway requires coordination across emergency arrival, neurology activation, imaging, eligibility review, and treatment initiation.
- **Pattern:** Emergency -> stroke recognition -> neurology -> imaging -> eligibility assessment -> thrombolysis.
- **Lesson:** Automation opportunities must preserve the handoff chain, not just one local step.
- **ART Learning:** The useful boundary is the coordination layer across handoffs, not the clinical decision itself.
- **ART Improvement:** Model the workflow as a chain of ownership transitions and time-sensitive states.
- **Conditions:** High-consequence clinical workflow; time window sensitivity; multiple team handoffs
- **Anti-pattern:** Treating a single notification feature as the full workflow problem.
- **Do not assume:** That stroke coordination is only a triage problem; that one team owns the whole pathway
- **Evidence status:** `VERIFIED`
- **Status:** `ACTIVE`
- **Confidence:** `HIGH`
- **Reuse potential:** `HIGH`
- **Applications:** Stroke workflow mapping; exception routing; cross-team handoff modeling
- **Source checkpoint:** `OPP-001-01`
- **Source refs:** `SRC-FILE-OPP-001-01`, `SRC-FILE-OPP-001-02`, `SRC-URL-PUBMED-32992177`
- **Source location:** OPP-001-01 sections 2-6; OPP-001-02 sections 2-4
- **Original source:** `opportunities/Healthcare_and_Pharmaceuticals/Baby_Memorial_Hospital_Kozhikode/opportunity - 01/OPP-001-01.md`
- **Tags:** stroke, handoff, imaging, thrombolysis, coordination

### RI-002

**Title:** Historical clinical-time gains are not labor-savings evidence

- **Type:** `NEGATIVE_INTELLIGENCE`
- **Domain:** Research validation
- **Description:** The BMH study measures door-to-needle time and threshold performance, but it does not measure staff minutes or manual coordination effort.
- **Pattern:** Elapsed clinical time can improve without proving reduced labor.
- **Lesson:** Do not infer current manual pain or labor savings from historical time metrics alone.
- **ART Learning:** Separate outcome improvement from operational workload reduction.
- **ART Improvement:** Require direct current operational evidence before claiming pain reduction.
- **Conditions:** Historical study data only; no staffing or work-logging metrics
- **Anti-pattern:** Equating faster treatment time with less human work.
- **Do not assume:** That a 16 minute DNT reduction equals 16 minutes of labor saved; that historical performance means current pain persists
- **Evidence status:** `VERIFIED`
- **Status:** `ACTIVE`
- **Confidence:** `HIGH`
- **Reuse potential:** `HIGH`
- **Applications:** Current pain validation; economic evaluation; avoiding false ROI claims
- **Source checkpoint:** `OPP-001-03`
- **Source refs:** `SRC-FILE-OPP-001-03`, `SRC-URL-PUBMED-32992177`
- **Source location:** OPP-001-03 sections 2-6
- **Original source:** `opportunities/Healthcare_and_Pharmaceuticals/Baby_Memorial_Hospital_Kozhikode/opportunity - 01/OPP-001-03.md`
- **Tags:** negative intelligence, labor, DNT, validation, ROI

### RI-003

**Title:** Existing stroke software means the opportunity must target residual stalls

- **Type:** `GUARDRAIL`
- **Domain:** Opportunity scoping
- **Description:** Public evidence shows related stroke software and current stroke services, so a new opportunity must focus on what still stalls after the digital state exists.
- **Pattern:** Existing software -> stall -> identify blocker -> assign owner -> follow up -> escalate -> close.
- **Lesson:** The residual opportunity is exception orchestration, not duplication of core stroke features.
- **ART Learning:** Scope future work to the ownership and closure layer after a stalled state.
- **ART Improvement:** Screen for follow-up and escalation gaps rather than rebuilding notification, checklist, or timer features.
- **Conditions:** Related software already visible; current pain not directly validated
- **Anti-pattern:** Building another copy of stroke notification and checklist tooling.
- **Do not assume:** That public software listing proves internal usage; that current residual pain is already demonstrated
- **Evidence status:** `VERIFIED`
- **Status:** `ACTIVE`
- **Confidence:** `MEDIUM`
- **Reuse potential:** `HIGH`
- **Applications:** Residual-gap discovery; exception-management design; ART scope control
- **Source checkpoint:** `OPP-001-04`
- **Source refs:** `SRC-FILE-OPP-001-04`, `SRC-URL-ACTFAST-ADMIN`, `SRC-URL-PUBMED-30838983`, `SRC-URL-BMH-NEURO`
- **Source location:** OPP-001-04 sections 10-15
- **Original source:** `opportunities/Healthcare_and_Pharmaceuticals/Baby_Memorial_Hospital_Kozhikode/opportunity - 01/OPP-001-04.md`
- **Tags:** guardrail, residual gap, software, stall, escalation

### RI-004

**Title:** Current pain requires contemporaneous operational evidence

- **Type:** `RESEARCH_METHOD`
- **Domain:** Research methodology
- **Description:** Historical evidence establishes the existence of a past problem, but current validation needs current metrics and current operational observation.
- **Pattern:** Historical proof -> current uncertainty unless contemporaneous evidence exists.
- **Lesson:** Do not promote an opportunity to PASS without direct current operational validation.
- **ART Learning:** Preserve UNKNOWN when the available sources do not prove current pain.
- **ART Improvement:** Use current service and software visibility as context only, not as proof of pain.
- **Conditions:** Current measurements missing; public current service evidence available
- **Anti-pattern:** Using eight-year-old evidence as if it were current operational proof.
- **Do not assume:** That current service continuity equals current pain continuity; that public visibility equals internal deployment
- **Evidence status:** `VERIFIED`
- **Status:** `ACTIVE`
- **Confidence:** `HIGH`
- **Reuse potential:** `HIGH`
- **Applications:** Primary validation; current-state discovery; audit gating
- **Source checkpoint:** `OPP-001-04`
- **Source refs:** `SRC-FILE-OPP-001-04`, `SRC-URL-BMH-HOSPITAL`
- **Source location:** OPP-001-04 sections 7-12
- **Original source:** `opportunities/Healthcare_and_Pharmaceuticals/Baby_Memorial_Hospital_Kozhikode/opportunity - 01/OPP-001-04.md`
- **Tags:** research method, current state, validation gate, UNKNOWN

## Sources

### Internal Research Sources

- `SRC-FILE-OPP-001-01` - `OPP-001-01.md`
- `SRC-FILE-OPP-001-02` - `OPP-001-02.md`
- `SRC-FILE-OPP-001-03` - `OPP-001-03.md`
- `SRC-FILE-OPP-001-04` - `OPP-001-04.md`

### External Sources

- `SRC-URL-BMH-HOSPITAL` - Baby Memorial Hospital Kozhikode official site
- `SRC-URL-NBE-HOSPITAL-PROFILE` - National Board of Examinations hospital profile
- `SRC-URL-PUBMED-32992177` - PubMed 32992177
- `SRC-URL-SCIENCEDIRECT-S1052305720307370` - ScienceDirect abstract S1052305720307370
- `SRC-URL-TATD-ACEM-2017-4` - ACEM 2017-4 PDF
- `SRC-URL-BMH-NEURO` - BMH neurointervention overview
- `SRC-URL-ACTFAST-ADMIN` - Act FAST Admin App Store listing
- `SRC-URL-PUBMED-30838983` - PubMed 30838983

## Checkpoints

### CP-001 - Specific Hospital + Workflow Discovery

The investigation established Baby Memorial Hospital as the target hospital and acute ischemic stroke thrombolysis coordination as the workflow boundary.

- Status: `PASSED`
- Tested: Whether the target hospital, capacity context, and workflow boundary are specific enough for investigation.
- Found: BMH is a mid-scale tertiary hospital with current stroke-service context and a historically documented acute stroke coordination workflow.
- What changed: Established the hospital and workflow boundary while preserving the bed-count discrepancy instead of reconciling it away.
- Resulting state: Proceed to exception reconstruction.

### CP-002 - Exception + Human Investigation Reconstruction

The investigation reconstructed the historical exception classes and the human investigation structure.

- Status: `PASSED`
- Tested: Whether the BMH study and presentation identify concrete delay classes and a human investigation path.
- Found: BMH had a digital coordination intervention and historical delay causes explicitly included patient shifting and imaging.
- What changed: Shifted the investigation from what to automate to what residual coordination remains after the first digital intervention.
- Resulting state: Proceed to human effort quantification.

### CP-003 - Human Effort / Pain Quantification

The investigation tested whether the study quantifies labor, handoffs, follow-up, or economic value rather than only clinical timing.

- Status: `PASSED`
- Tested: Whether the study quantifies labor, handoffs, follow-up, or economic value rather than only clinical timing.
- Found: The study quantifies elapsed clinical time and threshold performance, but not staff minutes or manual coordination effort.
- What changed: Separated elapsed clinical time from labor savings and preserved UNKNOWN for human effort.
- Resulting state: Proceed to current operational validation.

### CP-004 - Direct Operational Evidence / Pain Validation

The investigation tested whether current residual pain, current human effort, and current automation gap are observable from public sources.

- Status: `BLOCKED`
- Tested: Whether current residual pain, current human effort, and current automation gap are observable from public sources.
- Found: Current public evidence confirms ongoing stroke services and related software visibility, but current residual pain is unknown.
- What changed: Kept the direct operational validation gate open and ended the investigation at HOLD instead of forcing PASS.
- Resulting state: Stop unless new current evidence appears.

## Evidence

### E-001

Baby Memorial Hospital is presented as a private tertiary referral hospital in Kozhikode with 490 operational beds, while a National Board of Examinations profile lists 600 beds.

- Classification: `EVIDENCE`
- Source: `SRC-FILE-OPP-001-01`

### E-002

The published BMH stroke study reports 76 app-treated patients and 100 historical controls, with mean door-to-needle time falling from 57 to 41 minutes and 60-minute treatment rising from 67 percent to 89 percent.

- Classification: `EVIDENCE`
- Source: `SRC-FILE-OPP-001-01`

### E-003

The BMH app supported patient-parameter entry, NIHSS, thrombolysis checklist, dose calculation, team synchronization, patient-movement notification, and radiological-image sharing.

- Classification: `EVIDENCE`
- Source: `SRC-FILE-OPP-001-02`

### E-004

The historical BMH presentation explicitly names delays in patient shifting and imaging as delay causes.

- Classification: `EVIDENCE`
- Source: `SRC-FILE-OPP-001-02`

### E-005

The study quantifies elapsed clinical time and threshold performance, but not staff minutes, calls, handoffs, manual investigation time, or staff cost.

- Classification: `EVIDENCE`
- Source: `SRC-FILE-OPP-001-03`

### E-006

Current public evidence shows that BMH stroke services remain active and that a related stroke app ecosystem is publicly visible.

- Classification: `EVIDENCE`
- Source: `SRC-FILE-OPP-001-04`

### E-007

Current BMH residual pain, current DNT, current patient-shifting delay, current imaging delay, current manual follow-up, current human minutes, current residual exception rate, current avoidable delay, and current ROI are all unknown.

- Classification: `EVIDENCE`
- Source: `SRC-FILE-OPP-001-04`

### E-008

The investigation concludes that the historical pain was real, but the current pain is unverified, so the opportunity remains HOLD rather than PASS.

- Classification: `EVIDENCE`
- Source: `SRC-FILE-OPP-001-04`

### E-009

If a residual opportunity exists, it is an exception-orchestration layer around stall detection, blocker ownership, follow-up, escalation, and closure, not stroke diagnosis, thrombolysis decision, or medication selection.

- Classification: `EVIDENCE`
- Source: `SRC-FILE-OPP-001-04`

## Claims

### C-001

Baby Memorial Hospital is a relevant tertiary-hospital target for acute stroke workflow investigation because it is publicly described as a mid-scale hospital with current stroke services and a historically documented stroke coordination workflow.

- Evidence basis: `E-001`, `E-006`

### C-002

BMH historically used a digital coordination intervention for acute ischemic stroke thrombolysis and explicitly identified patient shifting and imaging as delay causes.

- Evidence basis: `E-002`, `E-003`, `E-004`

### C-003

The historical intervention improved elapsed stroke-treatment performance, but it did not quantify labor savings or manual coordination effort.

- Evidence basis: `E-002`, `E-005`

### C-004

Current public evidence shows ongoing stroke services and visible related software, but it does not validate current residual pain.

- Evidence basis: `E-006`, `E-007`

### C-005

Any residual ART opportunity would need to target the exception-orchestration layer after the existing digital state stalls.

- Evidence basis: `E-009`

## Inferences

### I-001

Historical door-to-needle improvement cannot be treated as proof of reduced human labor or current pain.

- Basis: `C-002`, `C-003`
- Implication: Human effort remains unknown even though clinical time improved.

### I-002

Because current service and software are visible while current operational pain is unmeasured, the current automation gap is unproven.

- Basis: `C-004`
- Implication: The investigation should stop at HOLD rather than pass as a validated opportunity.

### I-003

If ART proceeds later, its scope should be follow-up, escalation, and closure of stalled workflow states, not core stroke diagnosis or medication selection.

- Basis: `C-005`
- Implication: The plausible future product boundary is exception orchestration around existing digital workflow states.

## Hypotheses

### H-001

A residual exception-orchestration layer may still exist around the current digital stroke workflow.

- Status: `UNKNOWN`
- Supporting basis: `C-005`, `I-003`
- Falsification basis: none provided

## Results

### R-001

Historical mobile coordination improved mean door-to-needle time from 57 to 41 minutes and improved threshold performance.

- Status: `PASSED`

### R-002

Direct current operational validation was not passed because current residual pain is unknown.

- Status: `BLOCKED`

## Traceability

### Traceability 1

Hospital discovery, workflow selection, and bed-capacity context trace to OPP-001-01 plus the publicly cited hospital and NBE pages.

- Research location: OPP-001-01 sections 1-4
- Source URLs:
  - https://www.babymemorialhospitals.com/hospitals/bmh-kozhikode
  - https://accr.natboard.edu.in/online_user/hospital_profile.php
  - https://pubmed.ncbi.nlm.nih.gov/32992177/
  - https://www.sciencedirect.com/science/article/abs/pii/S1052305720307370

### Traceability 2

Historical exception reconstruction traces to OPP-001-02 and the published delay-cause abstract.

- Research location: OPP-001-02 sections 2-7
- Source URLs:
  - https://pubmed.ncbi.nlm.nih.gov/32992177/
  - https://tatd.org.tr/wp-content/uploads/2021/10/ACEM-2017-4.pdf

### Traceability 3

Human-effort quantification traces to OPP-001-03, which preserves the distinction between elapsed clinical time and labor.

- Research location: OPP-001-03 sections 2-7
- Source URLs:
  - https://pubmed.ncbi.nlm.nih.gov/32992177/

### Traceability 4

Current validation, hold decision, and the exception-orchestration boundary trace to OPP-001-04.

- Research location: OPP-001-04 sections 4-15
- Source URLs:
  - https://www.babymemorialhospitals.com/specialities/neurointervention-and-neuroradiology/overview
  - https://apps.apple.com/gb/app/act-fast-admin/id1286140587
  - https://pubmed.ncbi.nlm.nih.gov/30838983/

## Workflows

### WF-001 - Acute Ischemic Stroke Code / Thrombolysis Coordination

**Workflow type:** `RECONSTRUCTED`

The stroke pathway requires coordination across emergency arrival, neurology activation, imaging, eligibility review, and treatment initiation. Historical app support improved synchronization and timing, but current residual pain remains unverified.

#### Steps

##### WF1-S1 - Emergency arrival and stroke recognition

- Actor: Patient / Emergency Medicine
- System: Emergency Department
- Handoff to: Neurology
- State information: Possible acute ischemic stroke requiring urgent triage.

##### WF1-S2 - Neurology activation and clinical capture

- Actor: Neurology / Stroke Team
- System: Stroke coordination app
- Handoff to: Radiology
- State information: Clinical parameters and checklist data are captured for coordination.

##### WF1-S3 - Imaging and radiology review

- Actor: Radiology
- System: Imaging systems
- Handoff to: Eligibility assessment
- State information: Image acquisition and review determine next action.

##### WF1-S4 - Eligibility review and thrombolysis decision

- Actor: Neurology / Emergency Medicine
- System: Checklist and dose calculator
- Handoff to: Treatment
- State information: Decision point for thrombolysis and dose calculation.

##### WF1-S5 - Treatment initiation and current service boundary

- Actor: Stroke Team
- System: Current stroke service and related app ecosystem
- Handoff to: Unknown residual follow-up
- State information: Treatment has occurred historically; current pain remains unmeasured.

## Sections

### SEC-001 - Discovery Thesis and Hospital Scale

The investigation establishes Baby Memorial Hospital as the target hospital and preserves the bed-count discrepancy rather than reconciling it away.

### SEC-002 - Historical App Intervention and Delay Causes

The historical stroke app improved door-to-needle time and documented patient-shifting and imaging delays.

### SEC-003 - Human Effort and Performance Limits

The evidence distinguishes elapsed clinical time from labor savings and keeps staffing pain unknown.

### SEC-004 - Current Validation and Decision Boundary

Current public evidence confirms stroke services and related software visibility, but the residual pain gate is not passed.

## Relationships

- `REL-001`: `E-002` SUPPORTS `C-002`
- `REL-002`: `E-003` SUPPORTS `C-002`
- `REL-003`: `E-004` SUPPORTS `C-002`
- `REL-004`: `C-002` SUPPORTS `I-001`
- `REL-005`: `C-004` SUPPORTS `I-002`
- `REL-006`: `C-005` SUPPORTS `I-003`
- `REL-007`: `H-001` DEPENDS_ON `C-005`
