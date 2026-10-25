# ART AZURE RESOLUTION & FEEDBACK SYNC HARNESS

## HARNESS 03 — REUSABLE PRODUCTION PROMPT

## PURPOSE

Synchronize post-creation Azure DevOps lifecycle changes back into the
canonical ART bug record and master bugs ledger.

Harness 01 owns:

BUG INTAKE + CANONICAL STORAGE

Harness 02 owns:

AZURE CREATION + FORWARD SYNCHRONIZATION

Harness 03 owns:

AZURE FEEDBACK + RESOLUTION LIFECYCLE SYNCHRONIZATION

Harness 03 must detect meaningful changes made in Azure after ticket creation,
including:

- State changes
- Reason changes
- developer comments/discussion
- resolution information
- relevant implementation/retest signals

It must then determine the ART validation disposition without falsely treating
an Azure workflow state as proof that the defect has been fixed.

CORE PRINCIPLE:

AZURE STATE != ART VALIDATION DISPOSITION

A Bug being marked Resolved, Closed, Fixed, Done, or equivalent in Azure does
NOT mean ART has verified the defect as fixed.

Only an actual ART retest against the original bug evidence and Acceptance
Criteria may produce:

VERIFIED_FIXED

==================================================

1. INPUT
   =====

The user will provide an existing canonical ART Bug ID.

Example:

ART-TOOL-003

Optional input:

FORCE_SYNC: YES

Default:

FORCE_SYNC: NO

Harness 03 must use the Bug ID to locate the existing canonical bug and its
Azure reference.

Do not require the user to:

- provide the Azure Work Item ID separately
- attach the canonical bug folder
- copy Azure comments manually
- copy the existing canonical Markdown
- provide the Feature again

The canonical bug record and stored Azure reference must provide the linkage.

==================================================
2. REQUIRED EXISTING BUG
========================

Locate:

ART-Product-Validation/
bugs/
<FEATURE></feature>/
<BUG-ID></bug>__<slug></slug>/
<BUG-ID></bug>.md

Search across Feature directories when necessary.

The canonical bug must already exist.

If no canonical bug exists:

STOP.

Return:

SYNC: FAILED
BLOCKER: CANONICAL BUG NOT FOUND

Never create a new Bug ID.

Harness 03 NEVER performs bug intake.

==================================================
3. REQUIRED AZURE LINK
======================

Load the Azure DevOps metadata stored by Harness 02.

Expected canonical metadata includes:

## Azure DevOps

Work Item ID: <actual ID></actual>
URL: <actual URL></actual>
Parent Feature: <feature></feature>
Parent Feature ID: <ID></id>
Assigned To: <name or Unassigned></name>
Sync Status: SYNCED

Also verify the operational SQLite/external-reference record when available.

The canonical Bug ID must resolve to exactly one Azure Bug.

If:

Work Item ID: Not created

or:

Sync Status: NOT_SYNCED

STOP.

Harness 03 must not create the missing Azure ticket.

Harness 02 owns Azure creation.

If canonical metadata and SQLite reference disagree:

STOP.

Return:

BLOCKER: AZURE REFERENCE CONFLICT

==================================================
4. AZURE READ-ONLY PREFLIGHT
============================

Before any local lifecycle update:

Read the linked Azure Bug.

Verify:

- Work Item Type = Bug
- ART:<BUG-ID></bug> tag exists
- Azure Work Item ID matches canonical reference
- correct parent Feature remains present

If identity cannot be established safely:

STOP.

Do not update the local lifecycle state.

==================================================
5. READ AZURE LIFECYCLE DATA
============================

Read the current Azure Bug state.

Capture at minimum when available:

- Work Item ID
- State
- Reason
- Assigned To
- Changed Date
- Changed By
- Resolution-related fields
- Discussion/comments
- comment author
- comment timestamp
- parent Feature
- relevant linked implementation information when already present

Read enough history to identify changes since the previous Harness 03 sync.

Do not treat ordinary generated/system comments as developer feedback.

For example:

"Created automatically by ART Product Resolution System..."

is not developer resolution feedback.

Preserve genuine human comments exactly enough to retain their meaning.

Do not invent missing comment text or metadata.

==================================================
6. CHANGE DETECTION
===================

Compare current Azure lifecycle data with the last synchronized Azure lifecycle
snapshot/event stored locally.

Detect meaningful changes including:

- Azure State changed
- Azure Reason changed
- new human comment
- new resolution statement
- developer says fix implemented
- developer asks for retest
- developer says behavior is intentional
- developer says issue cannot be reproduced
- developer says ticket is duplicate
- developer requests more information
- product decision is pending
- ticket reopened
- ticket closed
- implementation/build information added

Do not create a new lifecycle event when nothing meaningful changed.

If:

FORCE_SYNC: NO

and there are zero meaningful changes:

perform zero unnecessary writes.

==================================================
7. SOURCE-OF-TRUTH BOUNDARY
===========================

Harness 03 must NEVER rewrite historical bug evidence as though the new Azure
feedback had been known during intake.

Do NOT rewrite:

- original Problem
- original Observed Behavior
- original Reproduction
- original Expected Behavior
- original Business Impact
- original User Experience
- original Investigation Guidance
- original Fix Requirement
- original Recommended Solution
- original Minimum Working Fix
- original Acceptance Criteria
- original evidence files

These represent the canonical validation record at the time the bug was
reported.

Developer feedback is NEW lifecycle evidence.

Append lifecycle information separately.

==================================================
8. ART VALIDATION DISPOSITION
=============================

Maintain an ART-specific validation disposition independently from Azure State.

Allowed dispositions:

OPEN

IN_PROGRESS

FIX_CLAIMED

RETEST_REQUIRED

VERIFIED_FIXED

REPRODUCED_AFTER_FIX

INTENTIONAL_BEHAVIOR

PRODUCT_DECISION_PENDING

NOT_A_BUG

DUPLICATE

BLOCKED

Do not invent additional disposition values without an explicit contract
change.

==================================================
9. DISPOSITION RULES
====================

Use evidence-grounded interpretation.

---

OPEN
----

Use when:

- issue remains open
- no implementation/fix state is established
- investigation has not meaningfully progressed to another disposition

---

IN_PROGRESS
-----------

Use when Azure/developer evidence clearly indicates active implementation or
investigation is underway.

Do not infer IN_PROGRESS only from ticket assignment.

---

FIX_CLAIMED
-----------

Use when engineering states that the issue has been fixed/implemented, but ART
has not yet verified the original Acceptance Criteria.

Examples:

"Fixed."
"Implemented."
"Resolved in latest build."

FIX_CLAIMED does NOT equal VERIFIED_FIXED.

---

RETEST_REQUIRED
---------------

Use when sufficient evidence indicates a changed implementation is available
for ART validation.

Examples:

"Fixed, please verify."
"Available in build X."
"Please retest."
"Change deployed."

Retest must use the original canonical bug and Acceptance Criteria.

---

VERIFIED_FIXED
--------------

CRITICAL:

Harness 03 MUST NOT assign VERIFIED_FIXED solely from Azure data.

VERIFIED_FIXED requires actual ART retest evidence demonstrating that the
original defect no longer reproduces and the required Acceptance Criteria pass.

If no ART retest evidence exists:

VERIFIED_FIXED is prohibited.

---

REPRODUCED_AFTER_FIX
--------------------

Use only after ART performs a real retest following a claimed fix and the
original defect still reproduces.

Requires actual ART retest evidence.

Do not derive this from developer comments alone.

---

INTENTIONAL_BEHAVIOR
--------------------

Use when an authoritative developer/product decision clearly establishes that
the observed behavior is intentionally designed and no product-decision
ambiguity remains.

Example:

"This behavior is intentional and will remain as designed."

Do not use merely because Azure Reason = Fixed.

---

PRODUCT_DECISION_PENDING
------------------------

Use when developer/product feedback establishes that the observed behavior may
be intentional, but the intended product behavior is still under discussion or
awaiting confirmation.

Example:

"Editing prohibition is intentional for now. Will discuss with Kiran and
change the behavior if needed."

This means:

PRODUCT_DECISION_PENDING

NOT:

VERIFIED_FIXED

NOT:

INTENTIONAL_BEHAVIOR

until the product decision is confirmed.

---

NOT_A_BUG
---------

Use when authoritative feedback confirms that the reported behavior does not
represent a product defect under the intended specification.

Preserve the original validation evidence.

Do not delete the bug.

---

DUPLICATE
---------

Use when Azure/developer feedback confirms that another canonical issue owns
the same defect.

Where available, record:

Duplicate Of: <Bug ID / Azure ID>

Do not delete either historical record.

---

BLOCKED
-------

Use when resolution/retest cannot proceed because a required dependency,
environment, build, decision, information, or access is unavailable.

Record the blocker.

==================================================
10. AZURE STATE MAPPING SAFETY
==============================

Never use a blind mapping such as:

Azure Resolved → VERIFIED_FIXED

Azure Closed → VERIFIED_FIXED

Reason Fixed → VERIFIED_FIXED

Instead evaluate:

Azure state
+
Azure reason
+
human developer feedback
+
implementation availability
+
ART retest evidence

Examples:

Azure:
Resolved / Fixed

Developer:
"Fixed and deployed. Please verify."

ART disposition:

RETEST_REQUIRED

Azure:
Resolved / Fixed

Developer:
"Editing prohibition is intentional for now. Will discuss with Kiran and
change behavior if needed."

ART disposition:

PRODUCT_DECISION_PENDING

Azure:
Resolved / Fixed

Developer:
"Fixed."

No ART retest:

FIX_CLAIMED

Azure:
Closed

ART retest proves Acceptance Criteria pass:

VERIFIED_FIXED

==================================================
11. RETEST DECISION
===================

Maintain:

Retest Required: YES / NO

Use YES when:

- changed implementation is available
- developer explicitly requests verification
- deployment/build containing the fix is available
- ART needs to verify a claimed correction

Use NO when:

- product decision is pending
- behavior is confirmed intentional
- ticket is duplicate
- more information is required before testing
- no implementation change is available
- issue is blocked before retest

Do not ask the tester to retest unchanged behavior merely because Azure moved
to Resolved.

==================================================
12. ACTION REQUIRED
===================

Maintain a concise next-action classification.

Allowed values:

NONE

AWAIT_DEVELOPER

AWAIT_PRODUCT_DECISION

RETEST

PROVIDE_INFORMATION

REOPEN_RECOMMENDED

REVIEW_DUPLICATE

INVESTIGATE_BLOCKER

Examples:

PRODUCT_DECISION_PENDING
→ AWAIT_PRODUCT_DECISION

RETEST_REQUIRED
→ RETEST

REPRODUCED_AFTER_FIX
→ REOPEN_RECOMMENDED

FIX_CLAIMED without available retest environment
→ AWAIT_DEVELOPER or INVESTIGATE_BLOCKER depending on evidence

==================================================
13. CANONICAL LIFECYCLE SECTION
===============================

The canonical Bug Markdown must contain a lifecycle area separate from the
original investigation.

Add if absent:

## Resolution Status

ART Disposition: <disposition></disposition>
Azure State: <state></state>
Azure Reason: <reason or Not provided></reason>
Retest Required: YES / NO
Action Required: <action></action>
Last Azure Sync: <timestamp when available></timestamp>

Do not alter the original bug investigation sections.

==================================================
14. RESOLUTION HISTORY
======================

Maintain an append-only section:

## Resolution History

Each meaningful Azure lifecycle change must create one event.

Format:

### <timestamp/date> — Azure Lifecycle Update

Azure Work Item: #<ID></id>
Azure State: <state></state>
Azure Reason: <reason or Not provided></reason>
Changed By: <name or Not provided></name>

Developer Feedback:

<new relevant human feedback, or Not provided>

ART Assessment:

<disposition>

Retest Required:

YES / NO

Action Required:

<action>

Assessment Reason:

<concise evidence-grounded explanation>

Never delete previous lifecycle events.

Never rewrite an old event because a later developer comment changes the
interpretation.

New information creates a NEW event.

==================================================
15. COMMENT HANDLING
====================

Store only relevant lifecycle feedback in Resolution History.

Relevant examples:

- implementation completed
- intentional behavior
- product decision
- request for retest
- cannot reproduce
- request for more information
- duplicate identification
- blocker
- deployment/build information
- reopening information

Do not duplicate the entire Azure Discussion history on every sync.

Track comment identity/timestamp or equivalent stable metadata so the same
comment is not appended repeatedly.

Preserve the meaning of developer feedback.

Short comments may be preserved verbatim.

Do not alter a developer statement into a stronger conclusion.

Example:

Developer says:

"Editing prohibition is intentional for now. Will discuss with Kiran and
change the behavior if needed."

Do NOT transform this into:

"Editing is confirmed intended behavior."

Correct interpretation:

Product behavior remains pending a decision.

==================================================
16. MASTER BUGS LEDGER UPDATE
=============================

Update the existing production master bugs ledger for the canonical Bug ID.

Do not create a second ledger.

Preserve existing ledger history/contracts.

Add/update lifecycle fields required by the existing ledger implementation.

The ledger must be able to represent at minimum:

- canonical Bug ID
- Feature
- Azure Work Item ID
- Azure State
- Azure Reason
- ART Validation Disposition
- Retest Required
- Action Required
- Last Azure Sync
- latest meaningful resolution summary

If the current ledger schema cannot represent lifecycle status cleanly:

make the smallest backward-compatible extension required.

Do not redesign unrelated ledger structure.

==================================================
16A. PRIMARY LEDGER SYNCHRONIZATION — REQUIRED
===============================================

The existing `## Bugs` table in:

ART-Product-Validation/ART_PRODUCT_VALIDATION_LEDGER.md

is the PRIMARY operational bug ledger.

Harness 03 MUST update the existing canonical Bug row in this table whenever
the ART lifecycle disposition changes.

It is NOT sufficient to:

- append/update `## Azure Resolution & Lifecycle Tracking`
- update only the canonical Bug Markdown
- update only SQLite
- update only Developer Update
- create a secondary lifecycle representation

The primary Bugs table MUST remain synchronized with the current ART lifecycle
state.

There must never be contradictory current states such as:

Primary Bugs table:
ART-TOOL-003 | Status = OPEN | Retest = Pending

while lifecycle tracking says:

ART Disposition = PRODUCT_DECISION_PENDING
Retest Required = NO
Action Required = AWAIT_PRODUCT_DECISION

Such divergence is a ledger synchronization failure.

==================================================
PRIMARY ROW UPDATE
==================

Locate the existing row by canonical Bug ID.

Example:

ART-TOOL-003

Update that SAME row.

Never create another primary Bugs-table row for the same Bug ID.

Preserve:

- Bug ID/link
- Title
- Severity

Update lifecycle-controlled columns:

- Status
- Developer Update
- Retest

based on the current Harness 03 disposition.

==================================================
PRIMARY STATUS MODEL
====================

The existing Bugs table uses a simplified operational Status.

Map ART lifecycle dispositions into the primary Status as follows:

OPEN
→ OPEN

IN_PROGRESS
→ FIXING

FIX_CLAIMED
→ FIXING

RETEST_REQUIRED
→ RETEST

VERIFIED_FIXED
→ VERIFIED

REPRODUCED_AFTER_FIX
→ OPEN

INTENTIONAL_BEHAVIOR
→ CLOSED

PRODUCT_DECISION_PENDING
→ BLOCKED

NOT_A_BUG
→ CLOSED

DUPLICATE
→ CLOSED

BLOCKED
→ BLOCKED

This mapping controls ONLY the summarized primary ledger Status.

Do not replace the detailed ART Disposition with this simplified value in
canonical lifecycle metadata.

Example:

ART Disposition:
PRODUCT_DECISION_PENDING

Primary Ledger Status:
BLOCKED

The detailed reason remains:

PRODUCT_DECISION_PENDING

==================================================
DEVELOPER UPDATE COLUMN
=======================

Update `Developer Update` with a concise current lifecycle summary.

Format:

<ART_DISPOSITION>: <latest meaningful developer/resolution summary>

Example:

PRODUCT_DECISION_PENDING: Editing prohibition is intentional for now. Will
discuss with Kiran and change the behavior if needed.

Do not replace this with only:

Resolved

Fixed

or:

Pending.

Developer Update should communicate why the operational status changed.

If no meaningful developer feedback exists:

use the latest evidence-grounded lifecycle summary.

Do not invent one.

==================================================
RETEST COLUMN
=============

Synchronize the primary `Retest` column with Harness 03.

Mapping:

Retest Required = YES
→ Required

Retest Required = NO
→ Not Required

VERIFIED_FIXED
→ Passed

REPRODUCED_AFTER_FIX
→ Failed

If a bug has not yet entered any resolution lifecycle and no retest decision
exists:

Pending

Do NOT leave:

Retest = Pending

when Harness 03 has explicitly determined:

Retest Required = NO

==================================================
16B. SUMMARY COUNTERS — REQUIRED
=================================

After ANY primary Bugs-table Status change, recompute the `## Summary` section
from the actual current primary Bugs table.

Never increment/decrement counters manually.

Never trust previous Summary values.

Recalculate by reading every canonical row in `## Bugs`.

Required counters:

Total Bugs
Open
Fixing
Retest
Verified
Closed
Blocked

Mapping:

Status OPEN
→ Open

Status FIXING
→ Fixing

Status RETEST
→ Retest

Status VERIFIED
→ Verified

Status CLOSED
→ Closed

Status BLOCKED
→ Blocked

Invariant:

Total Bugs =
Open + Fixing + Retest + Verified + Closed + Blocked

If this invariant fails:

LEDGER UPDATE = FAILED

Do not report successful lifecycle synchronization.

==================================================
16C. SINGLE CURRENT-STATE CONTRACT
==================================

The following representations must agree after Harness 03 completes:

1. Canonical Bug `## Resolution Status`
2. SQLite lifecycle state
3. Primary `## Bugs` ledger row
4. Ledger `## Summary`
5. `## Azure Resolution & Lifecycle Tracking`

Detailed representations may contain more information, but they must not
contradict one another.

Example for ART-TOOL-003:

Canonical:

ART Disposition: PRODUCT_DECISION_PENDING
Retest Required: NO
Action Required: AWAIT_PRODUCT_DECISION

Primary ledger:

Status: BLOCKED
Developer Update:
PRODUCT_DECISION_PENDING: Editing prohibition is intentional for now. Will
discuss with Kiran and change the behavior if needed.
Retest: Not Required

Lifecycle tracking:

ART Disposition: PRODUCT_DECISION_PENDING
Retest Required: NO
Action Required: AWAIT_PRODUCT_DECISION

Summary:

Blocked count includes ART-TOOL-003.

==================================================
16D. LEDGER WRITE TRANSACTION
=============================

Treat primary ledger synchronization as part of the Harness 03 transaction.

Required order:

1. Read Azure lifecycle state.
2. Derive ART disposition.
3. Update canonical Resolution Status/History.
4. Persist SQLite lifecycle state.
5. Update existing primary Bugs-table row.
6. Update detailed lifecycle tracking row.
7. Recalculate Summary from primary Bugs table.
8. Re-read ledger.
9. Verify all representations agree.

Harness 03 must NOT return:

LEDGER: UPDATED

until steps 5–9 succeed.

If the detailed lifecycle table updates but the primary Bugs table does not:

return:

LEDGER: FAILED

BLOCKER: PRIMARY LEDGER ROW NOT SYNCHRONIZED

If primary row updates but Summary does not:

return:

LEDGER: FAILED

BLOCKER: LEDGER SUMMARY NOT SYNCHRONIZED

==================================================
16E. LEDGER IDEMPOTENCY
=======================

Running Harness 03 again with unchanged Azure data must NOT:

- create another Bugs-table row
- create another lifecycle row
- change Summary counts
- duplicate Developer Update
- duplicate Resolution History

Expected:

RESOLUTION SYNC: NO_CHANGE

The primary ledger must nevertheless be validated for consistency.

IMPORTANT:

NO_CHANGE refers to Azure lifecycle data.

It does NOT mean Harness 03 should ignore existing local ledger inconsistency.

If Azure has not changed but:

- primary Status is stale
- Retest is stale
- Summary is stale
- lifecycle row disagrees with primary row

Harness 03 MUST repair the local projection.

Return:

RESOLUTION SYNC: UPDATED

Reason:

LOCAL_LEDGER_RECONCILIATION

==================================================
16F. ART-TOOL-003 REQUIRED REGRESSION CASE
==========================================

Use ART-TOOL-003 as a mandatory regression test.

Input state:

Azure State:
Resolved

Azure Reason:
Fixed

Developer feedback:

Editing prohibition is intentional for now. Will discuss with Kiran and change
the behavior if needed.

Expected detailed lifecycle:

ART Disposition:
PRODUCT_DECISION_PENDING

Retest Required:
NO

Action Required:
AWAIT_PRODUCT_DECISION

Expected primary Bugs-table row:

Status:
BLOCKED

Developer Update:
PRODUCT_DECISION_PENDING: Editing prohibition is intentional for now. Will
discuss with Kiran and change the behavior if needed.

Retest:
Not Required

Expected Summary:

Total Bugs remains unchanged.

Blocked increases to include ART-TOOL-003.

Open decreases correspondingly if ART-TOOL-003 was previously OPEN.

Expected invariant:

Total Bugs =
Open + Fixing + Retest + Verified + Closed + Blocked

Run Harness 03 again.

Expected:

no duplicate rows
no duplicate history
same summary counts
same disposition

==================================================
16G. LEDGER VALIDATION OUTPUT
=============================

Add these checks to Harness 03 completion validation:

PRIMARY LEDGER ROW: PASS / FAIL
PRIMARY STATUS: <status></status>
PRIMARY RETEST: <value></value>
SUMMARY RECOMPUTED: PASS / FAIL
SUMMARY INVARIANT: PASS / FAIL
LIFECYCLE TABLE: PASS / FAIL
LEDGER CONSISTENCY: PASS / FAIL

Harness 03 cannot report:

LEDGER: UPDATED

unless:

PRIMARY LEDGER ROW = PASS
SUMMARY RECOMPUTED = PASS
SUMMARY INVARIANT = PASS
LIFECYCLE TABLE = PASS
LEDGER CONSISTENCY = PASS

==================================================
17. SQLITE / LOCAL STATE
========================

Use the existing production operational SQLite/index.

Store enough lifecycle synchronization metadata to support:

- last Azure lifecycle sync
- last observed Azure state
- last observed Azure reason
- processed comment identity/timestamp
- current ART disposition
- Retest Required
- Action Required

Do not use test/harness databases for production bug lifecycle state.

Schema changes, if required, must be minimal and backward compatible.

==================================================
18. IDEMPOTENCY
===============

Harness 03 must be idempotent.

Running Harness 03 repeatedly when Azure has not changed must produce:

- zero duplicate Resolution History entries
- zero duplicate developer comments
- zero duplicate ledger records
- zero unnecessary canonical writes

Expected:

SYNC: NO_CHANGE

when nothing meaningful changed.

==================================================
19. AZURE MUTATION BOUNDARY
===========================

Harness 03 is READ-ONLY against Azure by default.

DO NOT:

- change Azure State
- change Azure Reason
- modify title
- modify Repro Steps
- modify Severity
- modify Priority
- modify Tags
- assign users
- create comments
- delete comments
- upload evidence
- modify attachments
- modify parent relationships
- create work items
- reopen work items

Harness 03 synchronizes Azure lifecycle information INTO the ART validation
system.

Any future Azure writeback/reopen workflow must be implemented separately and
must not be silently introduced here.

==================================================
20. CONFLICT HANDLING
=====================

When Azure fields and developer comments conflict:

preserve both.

Example:

Azure:

State: Resolved
Reason: Fixed

Developer:

"Editing prohibition is intentional for now. Will discuss with Kiran and
change the behavior if needed."

Do not discard either source.

Record:

Azure State: Resolved
Azure Reason: Fixed

ART Disposition:
PRODUCT_DECISION_PENDING

Assessment Reason:
Azure is marked Resolved/Fixed, but the developer states that the observed
behavior is currently intentional and that the desired behavior remains under
discussion. No changed implementation has been established for ART retest.

Do not silently resolve contradictory lifecycle information.

==================================================
21. ART-TOOL-003 REFERENCE BEHAVIOR
===================================

Use the following only as a classification contract example.

Given:

Bug:
ART-TOOL-003

Azure:
Resolved

Azure Reason:
Fixed

Developer Feedback:
"Editing prohibition is intentional for now. Will discuss with Kiran and
change the behavior if needed."

Expected Harness 03 interpretation:

ART Disposition:
PRODUCT_DECISION_PENDING

Retest Required:
NO

Action Required:
AWAIT_PRODUCT_DECISION

Do NOT classify:

VERIFIED_FIXED

Do NOT classify:

INTENTIONAL_BEHAVIOR

because the comment explicitly indicates that the intended behavior may still
change after product discussion.

==================================================
22. RETEST EVIDENCE BOUNDARY
============================

Harness 03 may recognize existing ART retest evidence if it is already stored
through the approved validation process.

Harness 03 must NOT fabricate a retest.

A developer comment is not ART retest evidence.

An Azure State change is not ART retest evidence.

An Azure Reason of Fixed is not ART retest evidence.

A code commit alone is not ART retest evidence.

VERIFIED_FIXED requires actual ART validation evidence.

If a fix is available but no ART retest exists:

use:

RETEST_REQUIRED

or:

FIX_CLAIMED

as appropriate.

==================================================
23. REOPEN RECOMMENDATION
=========================

Harness 03 must not automatically reopen Azure Bugs.

If ART retest evidence demonstrates that a claimed fix failed:

ART Disposition:
REPRODUCED_AFTER_FIX

Action Required:
REOPEN_RECOMMENDED

Return this state to the tester.

A future explicit Azure resolution-action harness may perform the reopen
operation.

Harness 03 remains read-only.

==================================================
24. VALIDATION
==============

Before completing a sync verify:

[ ] canonical Bug exists

[ ] exactly one Azure external reference exists

[ ] Azure identity matches canonical Bug ID

[ ] Azure Work Item Type = Bug

[ ] ART:<BUG-ID></bug> marker exists

[ ] current Azure State captured

[ ] current Azure Reason captured when available

[ ] new human comments identified correctly

[ ] system-generated comments excluded from developer interpretation

[ ] original canonical investigation remains unchanged

[ ] ART disposition derived from evidence

[ ] Azure State was not treated as proof of fix

[ ] VERIFIED_FIXED was not assigned without ART retest evidence

[ ] Retest Required correctly determined

[ ] Action Required correctly determined

[ ] Resolution History appended only when meaningful change exists

[ ] ledger updated

[ ] SQLite/index lifecycle state updated

[ ] zero duplicate lifecycle events

[ ] zero Azure mutations

==================================================
25. REQUIRED TESTS
==================

Test at minimum:

TEST 1 — PRODUCT DECISION PENDING

Azure:
Resolved / Fixed

Comment:
"Editing prohibition is intentional for now. Will discuss with Kiran and
change the behavior if needed."

Expected:

PRODUCT_DECISION_PENDING
Retest Required: NO
Action Required: AWAIT_PRODUCT_DECISION

TEST 2 — FIX CLAIMED

Developer:
"Fixed."

No ART retest.

Expected:

FIX_CLAIMED

Never VERIFIED_FIXED.

TEST 3 — RETEST REQUEST

Developer:
"Fixed and deployed. Please verify."

Expected:

RETEST_REQUIRED
Retest Required: YES
Action Required: RETEST

TEST 4 — VERIFIED FIX

Existing approved ART retest evidence demonstrates original Acceptance Criteria
pass.

Expected:

VERIFIED_FIXED

TEST 5 — FAILED RETEST

Developer claims fix.

ART retest reproduces original defect.

Expected:

REPRODUCED_AFTER_FIX
Action Required: REOPEN_RECOMMENDED

TEST 6 — INTENTIONAL BEHAVIOR

Authoritative feedback:

"This is intentional behavior and will remain as designed."

Expected:

INTENTIONAL_BEHAVIOR
Retest Required: NO

TEST 7 — DUPLICATE

Developer confirms another bug owns the defect.

Expected:

DUPLICATE

TEST 8 — NO CHANGE

Run Harness 03 twice against unchanged Azure data.

Expected second run:

SYNC: NO_CHANGE

Zero duplicate Resolution History events.

TEST 9 — AZURE/CANONICAL CONFLICT

Azure reference does not match canonical Bug.

Expected:

STOP
No local lifecycle mutation.

TEST 10 — AZURE READ-ONLY

Verify Harness 03 performs zero Azure mutations.

==================================================
26. FIRST LIVE VALIDATION
=========================

Use:

ART-TOOL-003

as the first controlled real validation case.

Expected source:

Azure Work Item #68991

Expected observed Azure state:

Resolved

Expected observed Azure reason:

Fixed

Expected developer feedback:

Editing prohibition is intentional for now. Will discuss with Kiran and change
the behavior if needed.

Expected ART result:

ART Disposition:
PRODUCT_DECISION_PENDING

Retest Required:
NO

Action Required:
AWAIT_PRODUCT_DECISION

Expected:

- canonical original bug remains intact
- one Resolution History event is appended
- master ledger reflects PRODUCT_DECISION_PENDING
- local lifecycle state is persisted
- Azure receives zero mutations

Run Harness 03 again immediately.

Expected:

SYNC: NO_CHANGE

No duplicate lifecycle event.

==================================================
27. COMPLETION OUTPUT
=====================

Return only:

RESOLUTION SYNC: UPDATED / NO_CHANGE / FAILED
BUG ID: <canonical Bug ID></canonical>
WORK ITEM: #<Azure ID></azure>
AZURE STATE: <state></state>
AZURE REASON: <reason or Not provided></reason>
NEW DEVELOPER FEEDBACK: YES / NO
ART DISPOSITION: <disposition></disposition>
RETEST REQUIRED: YES / NO
ACTION REQUIRED: <action></action>
LEDGER: UPDATED / NO_CHANGE / FAILED
CANONICAL HISTORY: UPDATED / NO_CHANGE / FAILED
AZURE MUTATIONS: 0

If ART Disposition = RETEST_REQUIRED:

RETEST: REQUIRED

If ART Disposition = PRODUCT_DECISION_PENDING:

WAITING ON: PRODUCT DECISION

If ART Disposition = REPRODUCED_AFTER_FIX:

REOPEN: RECOMMENDED

If FAILED:

BLOCKER: <exact reason></exact>

STOP.

==================================================
28. IMPLEMENTATION MODE
=======================

If Harness 03 does not yet exist in the repository:

implement it using the existing production architecture.

Reuse existing:

- canonical bug resolver
- SQLite/index
- Azure authentication/client
- Azure Work Item lookup
- ART identity marker
- Feature verification
- master bugs ledger

Do not duplicate existing infrastructure.

Prefer extending existing Azure read capabilities rather than creating a
parallel Azure client.

Make only the minimum changes necessary to support lifecycle synchronization.

After implementation, run the required tests before the live ART-TOOL-003
validation.

==================================================
29. IMPLEMENTATION COMPLETION OUTPUT
====================================

If this prompt required implementation of Harness 03, return only:

IMPLEMENTATION: PASS / PARTIAL / BLOCKED
HARNESS: HARNESS 03
HARNESS FILE: <path></path>
AZURE READ: PASS / FAIL
AZURE WRITE OPERATIONS: 0
CANONICAL LIFECYCLE: PASS / FAIL
RESOLUTION HISTORY: PASS / FAIL
LEDGER SYNC: PASS / FAIL
SQLITE STATE: PASS / FAIL
IDEMPOTENCY: PASS / FAIL
ART-TOOL-003 TEST: PASS / FAIL / NOT_RUN
ART-TOOL-003 DISPOSITION: <disposition or NOT_RUN></disposition>
FILES CHANGED:
<list></list>
BLOCKER: <reason or NONE></reason>

STOP.

==================================================
30. CORE RULE
=============

HARNESS 01 records what ART observed.

HARNESS 02 projects that canonical bug into Azure.

HARNESS 03 records what happens after engineering receives the bug.

Never rewrite history.

Never equate developer resolution with validation.

Never mark a bug VERIFIED_FIXED without actual ART retest evidence.

Preserve the complete lifecycle:

OBSERVED
→ REPORTED
→ ENGINEERING FEEDBACK
→ PRODUCT/IMPLEMENTATION DECISION
→ RETEST WHEN REQUIRED
→ VERIFIED OUTCOME

==================================================
31. ASSIGNEE & OWNERSHIP HANDOFF — REQUIRED
============================================

Azure assignment is part of the bug lifecycle and MUST be synchronized.
Harness 03 must capture the CURRENT Azure assignee on every execution.

Do not assume ANUSHA GANESH HEGDE is the current assignee. The original/default
assignee used during ticket creation is historical creation context only.
After creation, Azure is authoritative for current assignment.

Developers may include Anusha, Prajwal, Yuresh, or other engineering members.
The ticket may later be assigned back to Chiranjeevi. This transition may
represent a QA/retest handoff.

Harness 03 remains Azure READ-ONLY. It MUST NOT perform the retest itself and
MUST NOT update Azure assignment, state, comments, or resolution.

==================================================
31A. CURRENT ASSIGNEE
=====================

Read System.AssignedTo and capture when available:

- display name
- stable Azure identity/email if available
- changed date
- previous assignee when determinable from Azure revision/history data

Persist current assignment in lifecycle state.

Do NOT rewrite the original bug intake Assignee field. Add/update under
`## Resolution Status`:

Current Azure Assignee: <display name or Unassigned></display>

The current Azure assignee must also be represented in SQLite/local lifecycle
state so assignment changes can be detected idempotently.

==================================================
31B. QA OWNER CONFIGURATION
===========================

For the current ART Product Validation workflow:

QA / Retest Owner: Chiranjeevi

Do NOT scatter a hardcoded string comparison throughout Harness 03. Use the
existing identity/registry/configuration mechanism if one exists. Otherwise
introduce the smallest backward-compatible reusable configuration, conceptually:

ART_QA_OWNER=Chiranjeevi

Prefer stable Azure identity/email when available. Display-name matching is a
controlled fallback only. Do not require a fixed list of developers.

==================================================
31C. ASSIGNEE CHANGE DETECTION
==============================

An assignee change is a meaningful lifecycle event.

Example:
Prajwal → Chiranjeevi

must NOT produce `RESOLUTION SYNC: NO_CHANGE` even if State, Reason, and
comments are unchanged.

Compare the last synchronized assignee with the current Azure assignee. Where
Azure revision/history information is available, use it to strengthen the
transition evidence. Persist the new assignee only after successful local sync.

==================================================
31D. ASSIGNMENT HISTORY
=======================

Record meaningful ownership changes append-only in `## Resolution History`.

Example:
Assignment: Prajwal → Chiranjeevi

Never erase previous ownership events. Never duplicate the same assignment
transition. If the previous owner cannot be established safely, record only:

Current Azure Assignee: <name></name>

Do not invent a previous owner.

==================================================
31E. QA HANDOFF DETECTION
=========================

Assignment back to the configured QA owner is a strong workflow signal.
However:

ASSIGNMENT TO QA ALONE != RETEST_REQUIRED

Determine QA/retest handoff using:
current assignee + Azure State/Reason + developer feedback + fix/deployment or
retest evidence.

A valid retest handoff normally requires both:

1. ownership returned to QA or an explicit QA/retest request; and
2. evidence that a fix/change is available for validation.

Example:
Previous Assignee: Prajwal
Current Assignee: Chiranjeevi
Developer Feedback: "Fixed. Please verify."

Expected:
ART Disposition: RETEST_REQUIRED
Retest Required: YES
Action Required: RETEST
Current Azure Assignee: Chiranjeevi
Primary Status: RETEST

==================================================
31F. FIXED/RESOLVED + RETURN TO QA
==================================

Common lifecycle:
Developer owns Bug → developer implements fix → Azure state/reason changes →
Bug assigned back to Chiranjeevi → ART retest required.

Example:
Previous: Yuresh
Current: Chiranjeevi
Azure State: Resolved
Azure Reason: Fixed
Fix evidence exists.

Expected:
ART Disposition: RETEST_REQUIRED
Retest Required: YES
Action Required: RETEST

Do NOT classify VERIFIED_FIXED. Actual ART retesting belongs to a separate
retest task/harness.

==================================================
31G. ASSIGNMENT TO QA WITHOUT FIX SIGNAL
========================================

Do NOT automatically classify RETEST_REQUIRED merely because the ticket is
assigned to Chiranjeevi.

Example:
Previous: Prajwal
Current: Chiranjeevi
Developer Feedback: "Can you provide the workflow used to reproduce this?"

Expected:
Retest Required: NO
Action Required: PROVIDE_INFORMATION

Use the evidence-supported disposition. Assignment changes ownership; it does
not prove implementation changed.

==================================================
31H. PRODUCT DECISION HANDOFF
=============================

Example:
Current Assignee: Chiranjeevi
Developer Feedback: "This behavior is intentional for now. Need product confirmation."

Expected:
ART Disposition: PRODUCT_DECISION_PENDING
Retest Required: NO
Action Required: AWAIT_PRODUCT_DECISION

Do NOT classify RETEST_REQUIRED because no changed implementation is established.

==================================================
31I. DEVELOPER OWNERSHIP
========================

If the Bug is assigned to an engineering member and evidence clearly indicates
active investigation or implementation:

ART Disposition: IN_PROGRESS
Retest Required: NO
Action Required: AWAIT_DEVELOPER

Do not infer IN_PROGRESS from assignment alone. Do not depend on a fixed list
of developer names.

==================================================
31J. FIX CLAIMED BUT STILL DEVELOPER OWNED
==========================================

Example:
Current Assignee: Prajwal
Developer Feedback: "Fix completed."
No explicit QA handoff/retest request.

Expected:
ART Disposition: FIX_CLAIMED
Retest Required: NO
Action Required: AWAIT_DEVELOPER

If feedback explicitly requests retest before assignment changes, the explicit
request may establish RETEST_REQUIRED under existing rules.

==================================================
31K. PRIMARY LEDGER OWNER — REQUIRED
=====================================

The primary `## Bugs` table must expose CURRENT actionable ownership.
Extend the existing table, if needed, with `Owner`.

Preferred columns:
Bug ID | Title | Severity | Status | Owner | Developer Update | Retest

Owner means current workflow ownership, not reporter, creator, historical
assignee, or default Harness 02 assignee.

Examples:
Prajwal → Owner = Prajwal
Yuresh → Owner = Yuresh
Chiranjeevi → Owner = Chiranjeevi
No current assignee → Owner = Unassigned

Update the SAME existing Bug row. Never create a duplicate row or second
ownership ledger.

==================================================
31L. PRIMARY LEDGER + RETEST HANDOFF
====================================

When disposition is RETEST_REQUIRED, primary ledger must reflect:
Status: RETEST
Owner: Chiranjeevi (or configured QA owner/current QA assignee)
Retest: Required
Developer Update: <concise evidence-grounded fix/retest handoff summary>

Recompute Summary using Section 16B. The Retest counter must include the Bug.

==================================================
31M. SUMMARY SAFETY
===================

Assignee changes alone do NOT directly modify Summary counters. Summary is
always derived from operational Status.

==================================================
31N. SINGLE CURRENT-STATE CONTRACT — OWNERSHIP
===============================================

After sync, these must agree:

1. Azure current assignee
2. canonical Resolution Status Current Azure Assignee
3. SQLite/local lifecycle current assignee
4. primary ledger Owner
5. lifecycle tracking representation when ownership is included

If they disagree:
LEDGER CONSISTENCY: FAIL

Harness 03 must not report successful synchronization.

==================================================
31O. LOCAL RECONCILIATION
=========================

NO_CHANGE reconciliation also applies to ownership. If Azure is unchanged but
local ownership is stale, Harness 03 MUST repair the local projection and return:

RESOLUTION SYNC: UPDATED
Reason: LOCAL_LEDGER_RECONCILIATION

==================================================
31P. ASSIGNMENT IDEMPOTENCY
===========================

Repeated execution against unchanged assignment must produce no duplicate
assignment event, Resolution History event, primary row, unnecessary ledger
rewrite, or Summary drift. If everything agrees, return NO_CHANGE.

==================================================
31Q. REQUIRED ASSIGNEE REGRESSION TESTS
=======================================

TEST A — DEVELOPER OWNERSHIP
Previous: Anusha
Current: Prajwal
Active implementation evidence exists.
Expected: IN_PROGRESS / NO / AWAIT_DEVELOPER / Owner Prajwal / Status FIXING.

TEST B — PRAJWAL RETURNS FIX TO QA
Previous: Prajwal
Current: Chiranjeevi
Developer: "Fixed. Please verify."
Expected: RETEST_REQUIRED / YES / RETEST / Owner Chiranjeevi / Status RETEST /
Retest Required.

TEST C — YURESH RETURNS FIX TO QA
Previous: Yuresh
Current: Chiranjeevi
Azure: Resolved / Fixed
Fix evidence exists.
Expected: RETEST_REQUIRED / YES / RETEST / Owner Chiranjeevi.

TEST D — QA ASSIGNMENT WITH INFORMATION REQUEST
Previous: Prajwal
Current: Chiranjeevi
Developer: "Please provide additional reproduction information."
Expected: Retest NO / PROVIDE_INFORMATION. Never derive RETEST_REQUIRED solely
from assignment.

TEST E — QA OWNER AWAITING PRODUCT DECISION
Current: Chiranjeevi
Developer: "Current behavior is intentional for now. Product confirmation required."
Expected: PRODUCT_DECISION_PENDING / NO / AWAIT_PRODUCT_DECISION / Owner
Chiranjeevi / Status BLOCKED.

TEST F — FIX CLAIMED BUT DEVELOPER STILL OWNS
Current: Prajwal
Developer: "Fix completed."
No retest request/handoff.
Expected: FIX_CLAIMED / NO / AWAIT_DEVELOPER / Owner Prajwal / Status FIXING.

TEST G — ASSIGNMENT IDEMPOTENCY
Prajwal → Chiranjeevi, run twice.
Expected second run: no duplicate history, row, or counter changes.

TEST H — STALE LOCAL OWNER RECONCILIATION
Azure: Chiranjeevi
Local canonical/ledger: Prajwal
No new Azure comment/state change.
Expected: UPDATED / LOCAL_LEDGER_RECONCILIATION / Owner Chiranjeevi.

==================================================
31R. VALIDATION ADDITIONS
=========================

Before completion verify:
[ ] current Azure assignee read
[ ] QA owner configuration resolved
[ ] assignee stored in canonical lifecycle
[ ] assignee stored in SQLite/local lifecycle
[ ] primary ledger Owner matches Azure
[ ] assignment transition detected when applicable
[ ] transition appended only once
[ ] QA assignment alone did not falsely trigger RETEST_REQUIRED
[ ] fix + QA handoff correctly triggered RETEST_REQUIRED
[ ] Summary remains derived from Status
[ ] zero Azure mutations

==================================================
31S. IMPLEMENTATION BOUNDARY
============================

Implement ONLY Harness 03 ownership/handoff synchronization in this stage.

DO NOT implement:

- ART retest execution
- retest evidence intake
- Azure reopen/close
- Azure state mutation
- Azure assignment mutation
- Azure comment creation
- Azure resolution writeback
- automatic mass processing of all production Bugs

Harness 03 remains AZURE → ART LOCAL STATE and READ-ONLY against Azure.

==================================================
31T. IMPLEMENTATION EXECUTION TASK
==================================

Read this entire `azure_resolution_sync.md` contract before changing code.
Implement ONLY Section 31 Assignee & Ownership Handoff requirements.

Preserve all previously passing Harness 03 behavior:

- Azure lifecycle read
- developer comment handling
- disposition classification
- canonical lifecycle synchronization
- append-only Resolution History
- primary ledger synchronization
- Summary recomputation
- SQLite lifecycle state
- local reconciliation
- idempotency
- Azure read-only boundary

Do not modify Harness 01 or Harness 02 contracts.
Do not implement the later ART retest/writeback workflow.

Required outcomes:

1. Current Azure assignee synchronized.
2. Assignee changes are meaningful lifecycle events.
3. Assignment persisted for idempotent comparison.
4. Developer → Chiranjeevi handoff + fix/retest evidence => RETEST_REQUIRED.
5. Assignment to Chiranjeevi alone != RETEST_REQUIRED.
6. Current Owner reflected in existing primary Bugs ledger.
7. Summary remains synchronized with Status.
8. Assignment history append-only and idempotent.
9. Existing lifecycle/ledger regression behavior remains intact.
10. Azure write operations remain exactly zero.

Use mocked regression cases from Section 31Q. Run Harness 03-specific tests,
then the complete existing bugs-ledger regression suite.

Do NOT mass-process production Bugs during this implementation task.

==================================================
31U. IMPLEMENTATION COMPLETION OUTPUT
=====================================

Return only:

IMPLEMENTATION: PASS / PARTIAL / BLOCKED
HARNESS: HARNESS 03
ASSIGNEE READ: PASS / FAIL
ASSIGNEE CHANGE DETECTION: PASS / FAIL
QA OWNER CONFIG: PASS / FAIL
QA HANDOFF CLASSIFICATION: PASS / FAIL
PRIMARY LEDGER OWNER: PASS / FAIL
ASSIGNMENT HISTORY: PASS / FAIL
LOCAL OWNER RECONCILIATION: PASS / FAIL
SUMMARY CONSISTENCY: PASS / FAIL
IDEMPOTENCY: PASS / FAIL
EXISTING REGRESSION SUITE: PASS / FAIL
AZURE WRITE OPERATIONS: 0
FILES CHANGED:
<list></list>
BLOCKER: <reason or NONE></reason>

STOP.

==================================================
31V. STAGE TERMINATION
======================

After producing Section 31U completion output: STOP.

Do not continue into retest automation.
Do not create another harness.
Do not modify Azure.

The next lifecycle stage will be introduced through a separate explicit `.md`
task after this Harness 03 ownership/handoff implementation is reviewed and
accepted.

==================================================
32. AZURE LIFECYCLE FIDELITY & PUBLIC-REPORT READINESS — REQUIRED
==================================================================

This section hardens Harness 03 after local public-report validation exposed
that ledger lifecycle status and developer updates may not match the current
Azure DevOps ticket state/comments closely enough.

Harness 03 remains the ONLY component responsible for translating Azure
lifecycle evidence into ART lifecycle state. Harness 04 must never compensate
for stale or incorrectly synchronized Azure data.

CORE RULE:

AZURE CURRENT STATE + CURRENT ASSIGNEE + NEW HUMAN FEEDBACK
→ HARNESS 03 INTERPRETATION
→ CANONICAL LIFECYCLE
→ PRIMARY LEDGER
→ PUBLIC REPORT

Do not patch the public HTML to hide upstream lifecycle synchronization errors.

==================================================
32A. CURRENT AZURE SNAPSHOT — REQUIRED
=======================================

For every Harness 03 execution, read the current Azure Bug and construct one
current Azure lifecycle snapshot containing, when available:

- Work Item ID
- Work Item Type
- State
- Reason
- Assigned To display name
- Assigned To stable identity/email internally when available
- Changed Date
- Changed By
- Parent Feature
- latest relevant human lifecycle comment(s)
- comment author
- comment timestamp
- implementation/fix/deployment/retest signal

The current Azure snapshot must be evaluated BEFORE deriving ART disposition.

Do not classify from stale locally cached State, Reason, assignee, or comment
text when the current Azure read succeeds.

==================================================
32B. HUMAN COMMENT FIDELITY
===========================

Developer/human lifecycle feedback must be synchronized from Azure accurately.

Exclude:

- system-generated comments
- automated ticket-creation comments
- comments already processed with the same stable identity/timestamp
- unrelated discussion that does not change lifecycle interpretation

Include relevant new human feedback such as:

- fixed / implemented
- deployed / available in build
- please verify / please retest
- intentional behavior
- product decision pending
- cannot reproduce
- duplicate
- request for reproduction information
- blocker/dependency
- reopened

Do not paraphrase a human comment into a stronger claim than Azure supports.

The internal ledger `Developer Update` may use a concise lifecycle summary, but
it must remain semantically consistent with the latest relevant Azure feedback.

==================================================
32C. AZURE STATE / COMMENT / ASSIGNEE CLASSIFICATION MATRIX
===========================================================

Use the complete current evidence, not State alone.

CASE 1 — NEW/ACTIVE, NO FIX SIGNAL

Expected:
ART Disposition: OPEN or IN_PROGRESS as supported by evidence
Retest Required: NO
Action Required: AWAIT_DEVELOPER

CASE 2 — RESOLVED/FIXED, FIX CLAIM ONLY, STILL DEVELOPER OWNED

Example:
State: Resolved
Reason: Fixed
Assignee: Prajwal
Feedback: "Fixed."

Expected:
ART Disposition: FIX_CLAIMED
Retest Required: NO
Action Required: AWAIT_DEVELOPER

CASE 3 — FIX AVAILABLE + EXPLICIT RETEST REQUEST

Example:
Feedback: "Fixed and deployed. Please verify."

Expected:
ART Disposition: RETEST_REQUIRED
Retest Required: YES
Action Required: RETEST

This may be valid even before assignment changes when the explicit retest
request is authoritative.

CASE 4 — FIX AVAILABLE + RETURNED TO QA

Example:
State: Resolved
Reason: Fixed
Previous Assignee: Yuresh
Current Assignee: Chiranjeevi
Fix evidence exists.

Expected:
ART Disposition: RETEST_REQUIRED
Retest Required: YES
Action Required: RETEST

CASE 5 — QA ASSIGNMENT WITHOUT FIX

Example:
Current Assignee: Chiranjeevi
Feedback: "Please provide additional reproduction information."

Expected:
Retest Required: NO
Action Required: PROVIDE_INFORMATION

Never infer RETEST_REQUIRED from QA assignment alone.

CASE 6 — PRODUCT DECISION PENDING

Example:
State: Resolved
Reason: Fixed
Feedback indicates behavior is intentional for now but product confirmation is
still required.

Expected:
ART Disposition: PRODUCT_DECISION_PENDING
Retest Required: NO
Action Required: AWAIT_PRODUCT_DECISION

CASE 7 — AZURE CLOSED/FIXED WITHOUT ART RETEST

Azure Closed, Fixed, or "Fixed and verified" wording does NOT by itself prove
ART verification.

If approved ART retest evidence does not exist:

Never set VERIFIED_FIXED.

Classify according to the available implementation/retest evidence, normally
FIX_CLAIMED or RETEST_REQUIRED.

==================================================
32D. LATEST MEANINGFUL UPDATE
=============================

Maintain a concise internal lifecycle summary suitable for downstream reporting.

The summary must answer:

"What is the latest evidence-grounded lifecycle development?"

Examples:

- Issue remains open in Azure; no fix has been claimed.
- Fix claimed by engineering; awaiting QA handoff.
- Fix available; ART retest required.
- Additional reproduction information requested.
- Product behavior decision pending.
- ART retest passed.  [Only when approved ART retest evidence exists.]
- ART retest failed; reopen recommended. [Only with actual ART retest evidence.]

Do not expose raw private developer discussion as a public-report contract.
Harness 04 may later consume a separately approved/sanitized version.

==================================================
32E. MEANINGFUL LIFECYCLE TIMESTAMP
===================================

Distinguish:

- Azure Changed Date
- latest relevant human comment timestamp
- Last Azure Sync

`Last Azure Sync` is synchronization metadata. It is NOT necessarily the time of
the meaningful engineering lifecycle change.

Where the schema supports it, persist:

Latest Lifecycle Update: <Azure Changed Date or latest relevant lifecycle event timestamp></azure>

Do not fabricate this timestamp from report-generation time.

This value is intended to support later reporting without misrepresenting sync
time as engineering update time.

==================================================
32F. LEDGER FIDELITY — REQUIRED
================================

After classification, the primary Bugs row must reflect the current ART
interpretation of the Azure snapshot.

Required current-state fields:

- Status
- Owner
- Developer Update
- Retest

The detailed Azure lifecycle tracking representation must reflect at minimum:

- Azure State
- Azure Reason
- Current Owner/Assignee when the schema supports it
- ART Disposition
- Retest Required
- Action Required
- Last Azure Sync
- latest meaningful lifecycle summary

The primary ledger and detailed lifecycle representation must not disagree on
current ART lifecycle meaning.

==================================================
32G. PUBLIC REPORT READINESS GATE
=================================

Harness 03 does NOT generate or publish the public report.

However, before reporting a successful sync, validate that downstream Harness 04
can consume a coherent lifecycle state.

For the synchronized Bug verify:

[ ] Azure State/Reason are current
[ ] current Azure assignee is current
[ ] latest relevant human feedback has been evaluated
[ ] ART disposition matches the evidence
[ ] primary Status maps from ART disposition
[ ] primary Owner matches current Azure ownership
[ ] primary Retest matches Retest Required
[ ] Developer Update matches the current lifecycle interpretation
[ ] lifecycle tracking row matches canonical lifecycle
[ ] no Azure state was treated as ART verification

If any current-state representation is stale or contradictory:

RESOLUTION SYNC: FAILED
BLOCKER: LIFECYCLE PROJECTION INCONSISTENCY

Do not allow Harness 04 to become the correction layer.

==================================================
32H. CONTROLLED PRODUCTION VERIFICATION — NO MASS BATCH
========================================================

Before any future `--all` production run, validate Harness 03 against a small
controlled set of real Azure tickets representing different lifecycle states.

Select at minimum, when available:

1. one OPEN/New ticket
2. one developer-owned FIX_CLAIMED ticket
3. one ticket returned to Chiranjeevi for retest
4. ART-TOOL-003 product-decision-pending case

For each controlled ticket compare:

Azure UI
vs
Harness 03 current Azure snapshot
vs
canonical Resolution Status
vs
primary ledger row
vs
lifecycle tracking row

The comparison must PASS before production batch synchronization is allowed.

Do NOT run `python3 scripts/resolution_sync.py --all` as part of implementing or
testing this section.

==================================================
32I. REQUIRED REGRESSION TESTS
==============================

Add tests for:

TEST 1 — STALE LOCAL STATE
Current Azure State differs from stored local state.
Expected: current Azure wins; local projections update.

TEST 2 — NEW HUMAN FIX COMMENT
Azure State unchanged, new human comment says "Fixed."
Expected: meaningful lifecycle change detected; FIX_CLAIMED unless stronger
retest evidence exists.

TEST 3 — NEW RETEST REQUEST
Azure State unchanged, new human comment says "Fixed and deployed. Please verify."
Expected: RETEST_REQUIRED / YES / RETEST.

TEST 4 — ASSIGNEE RETURN TO QA WITH FIX
Developer → Chiranjeevi plus fix evidence.
Expected: RETEST_REQUIRED / YES / RETEST.

TEST 5 — ASSIGNEE RETURN TO QA WITHOUT FIX
Developer → Chiranjeevi plus information request.
Expected: no false RETEST_REQUIRED.

TEST 6 — CLOSED/FIXED WITHOUT ART RETEST
Expected: never VERIFIED_FIXED.

TEST 7 — COMMENT IDEMPOTENCY
Same Azure comment processed twice.
Expected: no duplicate history or lifecycle transition.

TEST 8 — SYNC TIME VS LIFECYCLE TIME
Expected: Last Azure Sync and meaningful lifecycle timestamp remain distinct.

TEST 9 — PROJECTION CONSISTENCY
Canonical, SQLite, primary ledger and lifecycle tracking disagree before run.
Expected: reconcile when safe or fail with explicit blocker.

TEST 10 — AZURE READ-ONLY
Expected: zero Azure mutations.

==================================================
32J. IMPLEMENTATION EXECUTION TASK
==================================

Read the entire Harness 03 contract before changing code.

Implement Sections 31 and 32 as the current Harness 03 hardening scope if any
part is not already implemented correctly.

Do not redesign Harness 01, Harness 02, or Harness 04.

Do not modify public HTML to compensate for lifecycle problems.

Do not implement ART retest execution.

Do not implement Azure writeback/reopen/close.

Do not mass-process production bugs.

Required implementation outcome:

1. current Azure State/Reason read accurately
2. latest relevant human lifecycle feedback read accurately
3. current Azure assignee read accurately
4. changes to any of those inputs are meaningful lifecycle events
5. ART disposition uses the complete current Azure snapshot
6. developer → QA handoff works only with sufficient retest evidence
7. primary ledger Status/Owner/Developer Update/Retest remain coherent
8. detailed lifecycle tracking remains coherent
9. meaningful lifecycle timestamp is distinct from sync timestamp where feasible
10. local inconsistencies are reconciled safely
11. VERIFIED_FIXED remains impossible without actual ART retest evidence
12. Azure write operations remain zero

Run mocked/unit regression tests first.
Run the complete bugs-ledger regression suite second.

Then perform ONLY the controlled production verification from Section 32H.
Do not use `--all`.

==================================================
32K. COMPLETION OUTPUT
======================

Return only:

IMPLEMENTATION: PASS / PARTIAL / BLOCKED
HARNESS: HARNESS 03
AZURE STATE READ: PASS / FAIL
AZURE REASON READ: PASS / FAIL
HUMAN COMMENT SYNC: PASS / FAIL
ASSIGNEE READ: PASS / FAIL
ASSIGNEE CHANGE DETECTION: PASS / FAIL
QA HANDOFF CLASSIFICATION: PASS / FAIL
ART DISPOSITION CLASSIFICATION: PASS / FAIL
PRIMARY LEDGER PROJECTION: PASS / FAIL
LIFECYCLE TRACKING PROJECTION: PASS / FAIL
DEVELOPER UPDATE FIDELITY: PASS / FAIL
LIFECYCLE TIMESTAMP: PASS / FAIL
LOCAL RECONCILIATION: PASS / FAIL
IDEMPOTENCY: PASS / FAIL
PUBLIC REPORT READINESS: PASS / FAIL
CONTROLLED PRODUCTION VERIFICATION: PASS / FAIL / NOT_RUN
PRODUCTION BATCH RUN: NO
EXISTING REGRESSION SUITE: PASS / FAIL
AZURE WRITE OPERATIONS: 0
FILES CHANGED:
<list></list>
BLOCKER: <reason or NONE></reason>

STOP.

==================================================
32L. STAGE TERMINATION
======================

After the Section 32K completion output:

STOP.

Do not run the production batch.
Do not regenerate/publish the public report as part of this task.
Do not proceed into ART retest execution.
Do not mutate Azure.

The next task begins only after Harness 03 lifecycle fidelity is reviewed and
accepted.
