
ART BUG PIPELINE — ORCHESTRATOR
VERSION: HARNESS 01 → HARNESS 02 AUTOMATIC HANDOFF

PURPOSE

Run the complete ART bug-processing workflow from one invocation.

This pipeline orchestrates the existing production harnesses:

Harness 01
ART BUG INTAKE & STORAGE HARNESS

Harness 02
ART AZURE DEVOPS TICKET HARNESS

The pipeline must automatically pass a successfully stored canonical Bug from
Harness 01 to Harness 02.

The user must NOT need to:

- manually locate the newly created bug folder
- attach the canonical bug folder
- paste the canonical Markdown again
- reattach the same evidence
- manually run Harness 02
- manually provide the Bug ID after Harness 01 finishes

This is an ORCHESTRATION layer only.

DO NOT merge Harness 01 and Harness 02 responsibilities.

==================================================

1. INPUT
   ==================================================

The user may provide:

- short/raw bug description
- screenshots
- extracted video stills
- ZIP evidence
- error messages
- logs
- JSON
- reproduction information
- expected behavior
- Feature
- Module
- Environment
- additional observations
- existing Bug ID for an update

The user does NOT need to provide a fully structured canonical ticket.

Harness 01 is responsible for structuring the bug.

Use evidence already available in the current working context/local workspace.

Do not ask the user to provide the same evidence twice.

==================================================
2. REQUIRED FLOW
================

Execute:

RAW BUG + EVIDENCE
        ↓
HARNESS 01
        ↓
CANONICAL BUG STORED
        ↓
READY FOR AZURE?
        ↓
YES
        ↓
READ BUG ID
        ↓
HARNESS 02
        ↓
AZURE CREATE / RECONCILE
        ↓
VERIFY
        ↓
FINAL COMBINED RESULT

There must be no manual stop between Harness 01 and Harness 02 when:

READY FOR AZURE: YES

==================================================
3. HARNESS 01
=============

Run the existing production Harness 01.

Harness 01 remains authoritative for:

- Bug ID allocation
- duplicate/update detection
- canonical Feature
- Module
- Classification
- Title
- Problem
- Observed Behavior
- Reproduction
- Expected Behavior
- Business Impact
- User Experience
- Investigation Guidance
- Fix Requirement
- Recommended Solution
- Minimum Working Fix
- Acceptance Criteria
- Severity
- Priority
- Tags
- local evidence storage
- canonical Markdown
- Feature directory
- SQLite/index
- master validation ledger
- Azure readiness

Do not implement any second Bug ID allocator.

Do not independently create canonical Markdown from this pipeline.

Do not independently update the ledger.

Do not independently move evidence.

==================================================
4. HARNESS 01 GATE
==================

Harness 02 may run only when Harness 01 successfully returns:

BUG STORED: <BUG-ID></bug>

and:

READY FOR AZURE: YES

Example:

BUG STORED: ART-AGENTX-007
READY FOR AZURE: YES

The pipeline must capture:

ART-AGENTX-007

as the canonical handoff identity.

If Harness 01 fails:

STOP.

If:

READY FOR AZURE: NO

STOP.

Do not execute Harness 02.

==================================================
5. AUTOMATIC HANDOFF
====================

The handoff between Harness 01 and Harness 02 must use:

BUG ID ONLY

Example:

run_harness_02("ART-AGENTX-007")

Do NOT require:

- bug folder attachment
- Markdown attachment
- evidence reattachment
- copied ticket body
- manual Feature selection

Harness 02 must locate the canonical bug itself from:

ART-Product-Validation/
bugs/
<FEATURE></feature>/
<BUG-ID></bug>__<slug></slug>/
<BUG-ID></bug>.md

using its existing canonical lookup logic.

==================================================
6. EVIDENCE FLOW
================

Evidence must follow:

User evidence
    ↓
Harness 01
    ↓
canonical evidence directory
    ↓
Harness 02
    ↓
Azure attachments

Harness 01 stores evidence once.

Harness 02 reads that canonical evidence.

Do not create a second production evidence copy for the handoff.

Do not re-upload user-source evidence separately from this pipeline.

Do not rename Harness 01 evidence after storage.

==================================================
7. HARNESS 02
=============

When Harness 01 reports:

READY FOR AZURE: YES

automatically invoke the existing Harness 02 using the returned Bug ID.

Harness 02 remains authoritative for:

- Azure Feature resolution
- Azure hierarchy validation
- Epic #68782 verification
- Azure duplicate detection
- ART:<BUG-ID></bug> identity
- Azure work-item creation
- existing-ticket reconciliation
- developer body projection
- Severity mapping
- Priority mapping
- Tags
- Environment
- Assignee handling
- evidence attachments
- attachment duplicate prevention
- post-sync Azure readback
- Azure external-reference persistence
- canonical Azure metadata writeback
- idempotency

The pipeline itself must not write directly to Azure.

==================================================
8. NO MANUAL CONTINUE STEP
==========================

After Harness 01 succeeds, do NOT ask:

"Do you want me to continue to Azure?"

Do NOT ask:

"Please attach the generated folder."

Do NOT ask:

"Please provide the Bug ID."

Do NOT ask:

"Please run Harness 02."

Running this pipeline means:

Run Harness 01 and, if READY FOR AZURE: YES, continue automatically through
Harness 02.

==================================================
9. FAILURE SAFETY
=================

If Harness 01 fails:

STOP.

Never attempt Azure synchronization.

Examples:

- Feature unresolved
- duplicate local identity unresolved
- ID allocation failure
- evidence storage failure
- SQLite/index failure
- ledger failure
- canonical record failure

If Harness 02 fails:

STOP.

Do NOT create another Azure Bug.

Keep the canonical bug stored locally.

Return the exact Harness 02 blocker.

Examples:

- Azure Feature unresolved
- Azure parent hierarchy invalid
- duplicate Azure identity conflict
- Severity/Priority mapping failure
- attachment failure
- Azure verification failure
- external-reference conflict

==================================================
10. DUPLICATE / UPDATE BEHAVIOR
===============================

Harness 01 owns local duplicate/update logic.

Harness 02 owns Azure idempotency.

If Harness 01 determines that supplied evidence belongs to an existing Bug:

preserve the existing Bug ID.

Pass that same Bug ID to Harness 02.

Do not force a new bug.

If Harness 02 returns:

AZURE TICKET: EXISTING

this is a successful result.

If Harness 02 returns:

AZURE TICKET: UPDATED

this is also a successful result.

==================================================
11. LOCAL_ONLY MODE
===================

Support:

LOCAL_ONLY: YES

When explicitly provided:

Run Harness 01 only.

Do not run Harness 02.

Return the Harness 01 result.

Default:

LOCAL_ONLY: NO

Meaning:

Run the complete Harness 01 → Harness 02 workflow.

==================================================
12. INTERNAL PIPELINE STATES
============================

Use:

RECEIVED
HARNESS_01_RUNNING
LOCAL_STORED
READY_FOR_AZURE
HARNESS_02_RUNNING
AZURE_VERIFIED
COMPLETE
FAILED

COMPLETE requires:

Harness 01 successful

and, unless LOCAL_ONLY: YES:

Harness 02 final result:

SYNC STATUS: SYNCED

==================================================
13. IMPLEMENTATION MODEL
========================

Implement this as a small wrapper around the existing production harnesses.

Preferred conceptual flow:

process_bug_pipeline(input, evidence, local_only=False)

result_01 = run_harness_01(input, evidence)

if result_01 failed:
    return HARNESS_01 failure

if local_only:
    return local success

if result_01.ready_for_azure != YES:
    return blocked before Azure

bug_id = result_01.bug_id

result_02 = run_harness_02(bug_id)

if result_02 failed:
    return HARNESS_02 failure

if result_02.sync_status != SYNCED:
    return HARNESS_02 failure

return COMPLETE

Reuse existing callable functions/commands when available.

Do not reproduce both harnesses inside this orchestration file.

==================================================
14. INITIAL IMPLEMENTATION CONSTRAINT
=====================================

For the first version:

DO NOT refactor Harness 01.

DO NOT refactor Harness 02.

Only expose/invoke their existing production entry points as required.

Do not change:

- canonical Markdown schema
- Bug ID semantics
- Feature folder structure
- evidence naming
- SQLite schema unless absolutely required
- ledger format
- AzureFeatureRouter
- Azure hierarchy
- ART identity marker
- duplicate behavior
- attachment behavior

The objective of V1 is:

REMOVE MANUAL HANDOFF FRICTION

not redesign the existing system.

==================================================
15. REQUIRED TESTS
==================

Test:

1. NEW BUG

Input:
new bug + evidence

Expected:

Harness 01
→ new canonical Bug

Harness 02
→ one Azure Bug

No manual folder handoff.

2. EXISTING BUG UPDATE

Expected:

same canonical Bug ID
new evidence stored
same Azure Bug reconciled

3. ALREADY SYNCED BUG

Expected:

same Azure Work Item
AZURE TICKET: EXISTING
zero duplicate Bug
zero duplicate attachments

4. HARNESS 01 FAILURE

Expected:

Harness 02 never executes.

5. READY FOR AZURE: NO

Expected:

Harness 02 never executes.

6. HARNESS 02 FAILURE

Expected:

canonical Bug remains stored.
Azure Sync Status remains NOT_SYNCED.

7. EVIDENCE

Expected:

evidence stored once locally
evidence attached once to Azure

8. SECOND RUN

Expected:

zero duplicate canonical Bugs
zero duplicate Azure Bugs
zero duplicate Azure attachments

9. LOCAL_ONLY: YES

Expected:

Harness 01 runs.
Harness 02 does not run.

10. FEATURE LOOKUP

Expected:

Harness 02 finds the canonical Bug using Bug ID without the user attaching the
Feature folder.

==================================================
16. FIRST LIVE VALIDATION
=========================

After implementation, test with ONE disposable real bug.

Verify:

[ ] User runs one pipeline command/prompt.

[ ] Harness 01 receives the raw bug/evidence.

[ ] Harness 01 allocates the canonical Bug ID.

[ ] Bug is stored under the correct Feature directory.

[ ] Evidence is stored correctly.

[ ] SQLite/index is updated.

[ ] Master ledger is updated.

[ ] Pipeline captures the Bug ID.

[ ] No manual bug-folder attachment occurs.

[ ] Harness 02 starts automatically.

[ ] Harness 02 locates the bug using Bug ID.

[ ] Correct Azure Feature is resolved.

[ ] Exactly one Azure Bug exists.

[ ] Canonical evidence is attached.

[ ] Azure readback passes.

[ ] Canonical Azure metadata is written back.

[ ] Sync Status becomes SYNCED.

Then run the exact same Bug again.

Verify:

[ ] No second canonical Bug.

[ ] No second Azure Bug.

[ ] No duplicate attachments.

[ ] Same Azure Work Item ID.

==================================================
17. FINAL USER-FACING OUTPUT
============================

Return one result only.

SUCCESS:

PIPELINE: COMPLETE
BUG ID: <canonical Bug ID></canonical>
TITLE: <canonical title></canonical>
FEATURE: <Feature></feature>
MODULE: <Module></module>
LOCAL STORAGE: STORED
LEDGER: UPDATED
AZURE TICKET: CREATED / EXISTING / UPDATED
WORK ITEM: #<Azure ID></azure>
AZURE FEATURE: <Feature name></feature> (#<Feature ID></feature>)
ASSIGNEE: <actual assignee or Unassigned></actual>
SEVERITY: <Severity></severity>
PRIORITY: <Priority></priority>
EVIDENCE: <attached></attached>/<expected></expected>
AI-READY: YES / NO
SYNC STATUS: SYNCED

LOCAL ONLY:

PIPELINE: LOCAL_ONLY_COMPLETE
BUG ID: <canonical Bug ID></canonical>
TITLE: <canonical title></canonical>
FEATURE: <Feature></feature>
MODULE: <Module></module>
LOCAL STORAGE: STORED
LEDGER: UPDATED
AZURE: NOT_RUN
AI-READY: YES / NO
READY FOR AZURE: YES / NO

HARNESS 01 FAILURE:

PIPELINE: FAILED
STAGE: HARNESS_01
BUG ID: <Bug ID or Not created></bug>
SYNC STATUS: NOT_SYNCED
BLOCKER: <exact blocker></exact>

HARNESS 02 FAILURE:

PIPELINE: FAILED
STAGE: HARNESS_02
BUG ID: <canonical Bug ID></canonical>
LOCAL STORAGE: STORED
AZURE TICKET: FAILED
SYNC STATUS: NOT_SYNCED
BLOCKER: <exact blocker></exact>

Do not print the complete canonical Bug unless explicitly requested.

Do not print internal API payloads.

Do not print credentials/tokens.

==================================================
18. IMPLEMENTATION COMPLETION OUTPUT
====================================

After building this pipeline, return only:

IMPLEMENTATION: PASS / PARTIAL / BLOCKED
PIPELINE FILE: <path></path>
HARNESS 01: CONNECTED / FAILED
HARNESS 02: CONNECTED / FAILED
AUTOMATIC HANDOFF: PASS / FAIL
MANUAL FOLDER HANDOFF REQUIRED: NO / YES
LOCAL_ONLY MODE: PASS / FAIL
TEST BUG: <Bug ID or NOT_RUN></bug>
AZURE RESULT: CREATED / EXISTING / UPDATED / NOT_RUN / FAILED
IDEMPOTENCY: PASS / FAIL / NOT_TESTED
FILES CHANGED:
<list></list>
BLOCKER: <reason or NONE></reason>

STOP.

==================================================
19. CORE RULE
=============

HARNESS 01 OWNS CANONICAL BUG STORAGE.

HARNESS 02 OWNS AZURE SYNCHRONIZATION.

THE PIPELINE OWNS ONLY THE HANDOFF.

Do not merge the harnesses.

Do not duplicate their logic.

Do not require the tester to manually transfer files or folders between them.
