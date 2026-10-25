ART AZURE DEVOPS TICKET HARNESS — HARNESS 02
VERSION: FEATURE-ROUTED AZURE SYNC

PURPOSE

Take an existing canonical ART bug created and stored by Harness 01 and project
it into Azure DevOps as one complete developer-ready and AI-ready Bug work item.

Azure must contain enough information and evidence for:

1. A developer to understand the defect and implement a fix.
2. A repository-aware AI coding agent such as Claude to inspect the repository,
   trace the relevant implementation, determine the actual root cause,
   implement the smallest correct fix, and verify it against the canonical
   Acceptance Criteria.

Harness 02 is:

AZURE SYNCHRONIZATION + VERIFICATION ONLY.

Harness 02 NEVER:

- allocates canonical ART Bug IDs
- creates canonical bugs
- reinvestigates the defect
- rewrites canonical investigation content
- invents missing evidence
- changes the canonical Feature
- creates Azure Features or Epics

Harness 01 remains authoritative for canonical bug content and evidence.

Core principle:

CANONICAL BUG
→ RESOLVE AZURE FEATURE
→ PREFLIGHT
→ CREATE OR RECONCILE ONE AZURE BUG
→ ATTACH EVIDENCE
→ VERIFY
→ PERSIST AZURE REFERENCE
→ WRITE BACK SYNC METADATA

Never create an Azure mutation until preflight has completed successfully.

==================================================

1. INPUT
   =====

The user provides an existing canonical ART Bug ID.

Example:

ART-AGENT-002

Harness 02 must locate the canonical record created by Harness 01.

Current canonical storage pattern:

ART-Product-Validation/
└── bugs/
    └── <FEATURE-FOLDER></feature>/
        └── <BUG-ID></bug>__<slug></slug>/
            ├── <BUG-ID></bug>.md
            └── <evidence files></evidence>

Example:

ART-Product-Validation/
└── bugs/
    └── Agent Lab/
        └── ART-AGENT-002__agent-media-processing-error/
            ├── ART-AGENT-002.md
            ├── ART-AGENT-002__20261005__001.png
            └── ART-AGENT-002__20261005__002.mp4

==================================================
2. CANONICAL RECORD LOOKUP
==========================

Locate the canonical Bug ID across the supported Feature directories.

Do not assume the Feature from the Bug ID prefix.

Do not use a flat:

ART-Product-Validation/bugs/<BUG-ID></bug>...

lookup.

The canonical Markdown is expected at:

ART-Product-Validation/
bugs/
<FEATURE></feature>/
<BUG-ID></bug>__<slug></slug>/
<BUG-ID></bug>.md

Search only the production canonical bug store.

Do not use:

- harness fixtures
- test data
- temporary bug directories
- archived generated output
- Azure as a substitute source

If exactly one canonical record is found:

continue.

If no canonical record exists:

STOP BEFORE AZURE MUTATION.

If more than one production canonical record exists for the same Bug ID:

STOP BEFORE AZURE MUTATION.

Return a duplicate-local-record blocker.

Never allocate another Bug ID.

==================================================
3. SOURCE OF TRUTH
==================

Harness 01 canonical Markdown and its stored evidence are authoritative.

Use the canonical record for:

- Bug ID
- Title
- Feature
- Module
- Classification
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
- Environment
- Severity
- Priority
- Tags
- Assignee information if explicitly stored/supplied
- Evidence
- Discussion

Do not reinvestigate the defect.

Do not rewrite or reinterpret factual evidence.

Do not add missing technical details.

Do not modify evidence files.

Do not generate a new diagnosis.

Harness 02 performs a projection of the canonical record into Azure.

==================================================
4. LOCKED AZURE HIERARCHY
=========================

The Azure DevOps hierarchy is locked to:

Epic #68782
ART - Internal Bug Bounty

        ↓

Existing ART Feature

        ↓

Individual Azure Bug

Harness 02 must create or reconcile the Bug beneath the existing matching
Feature.

Never:

- create an Epic
- create a Feature
- rename an existing Feature
- move the Epic
- parent a Bug directly to Epic #68782
- create an alternative hierarchy

==================================================
5. CANONICAL FEATURE ROUTING
============================

Harness 01 now stores an explicit canonical:

## Feature

field.

Harness 02 MUST use the canonical Feature field as the primary Azure routing
input.

Do NOT route Azure parentage from Module when a valid canonical Feature exists.

Feature controls Azure hierarchy.

Module describes the affected component.

Supported canonical Features:

1. Agent Lab
2. Orchestrator
3. Tool Builder
4. MCP Servers
5. Triggers
6. Credential Manager
7. Serverless Functions
8. Governance
9. Human-in-the-Loop / Approvals
10. Live Connect
11. ART Deployment Kit (ADK)
12. Agent X

Use the existing:

AzureFeatureRouter

to resolve:

canonical Feature
→ existing Azure Feature name
→ existing Azure Feature Work Item ID

Do not introduce a second Feature router.

Do not hard-code Feature Work Item IDs in scattered implementation locations.

One canonical routing source must remain responsible for Feature resolution.

==================================================
6. FEATURE ROUTING SAFETY
=========================

Before any Azure write:

1. Read canonical `Feature`.
2. Pass it to `AzureFeatureRouter`.
3. Resolve exactly one Azure Feature.
4. Verify that Azure Feature exists.
5. Verify the resolved item is Work Item Type = Feature.
6. Verify that Feature belongs beneath Epic #68782.

If:

- Feature is missing
- Feature is unsupported
- Feature is unmapped
- router returns multiple candidates
- Azure Feature does not exist
- resolved item is not a Feature
- resolved Feature belongs to another Epic
- parent relationship cannot be verified

STOP BEFORE MUTATION.

Do not infer another Feature from Module.

Do not fall back to Epic #68782.

Do not create a Feature automatically.

==================================================
7. PREFLIGHT — READ ONLY
=========================

All preflight operations must be read-only.

Before creating or updating anything in Azure:

1. Load canonical Markdown.
2. Validate canonical Bug ID.
3. Validate canonical Feature.
4. Resolve Feature through AzureFeatureRouter.
5. Verify Feature exists.
6. Verify Feature belongs under Epic #68782.
7. Load canonical evidence manifest/files.
8. Inspect existing local Azure sync metadata.
9. Search Azure for the canonical marker:

   ART:<BUG-ID></bug>
10. Search active/relevant Azure Bug work items for exact title:

    [<BUG-ID></bug>] <canonical title></canonical>
11. If local canonical metadata already contains an Azure Work Item ID,
    read that item directly and reconcile its identity.

Do not mutate Azure during preflight.

==================================================
8. AZURE IDENTITY MARKER
========================

Every synchronized Azure Bug must contain the canonical marker:

ART:<BUG-ID></bug>

Example:

ART:ART-AGENT-002

This marker must be included in:

System.Tags

Use it as the primary cross-system idempotency identity.

The Azure title must also include the Bug ID:

[<BUG-ID></bug>] <canonical title></canonical>

Example:

[ART-AGENT-002] Agent media processing fails after upload

==================================================
9. EXISTING AZURE BUG DETECTION
===============================

Treat an Azure Bug as an existing projection when identity is established using
one or more authoritative signals:

1. Existing local external reference points to the Azure Bug.
2. Azure Bug contains exact canonical marker:

   ART:<BUG-ID></bug>
3. Exact canonical title matches:

   [<BUG-ID></bug>] <canonical title></canonical>

Marker match is stronger than title-only match.

If exactly one matching Azure Bug exists:

DO NOT create another Bug.

Reconcile that work item.

If multiple Azure Bugs contain the same exact canonical marker:

STOP.

Do not guess which work item is correct.

Return a duplicate-Azure-identity blocker.

If title matches but canonical marker belongs to another Bug ID:

STOP.

Do not overwrite another ticket.

==================================================
10. CREATE VS EXISTING VS UPDATE
================================

Use these synchronization states:

CREATED
A new Azure Bug was created because no canonical projection existed.

EXISTING
The correct Azure Bug already existed and required no meaningful mutation.

UPDATED
The correct Azure Bug already existed but required supported synchronization
changes to match the canonical projection.

FAILED
Synchronization could not complete safely.

Never create a new Bug merely because an existing Bug is missing one field.

Reconcile the existing Bug instead.

==================================================
11. ASSIGNEE RULE
=================

Azure Bug creation is ANUSHA GANESH HEDGE  by default.

Do NOT send:

System.AssignedTo.Anusha Ganesh Hedge

unless an assignee was explicitly supplied for this Azure synchronization or
explicitly defined in the canonical record as the intended Azure assignee.

An informational project/team default is always:

ANUSHA GANESH HEDGE

must be automatically be written to Azure.

Never automatically choose another team member.

Never infer assignment from Feature, Module, previous bugs, or ownership history.

==================================================
12. ASSIGNEE ON EXISTING AZURE BUGS
===================================

If synchronizing an existing Azure Bug:

Do not clear or replace an existing assignee merely because the canonical record
says UNASSIGNED.

Only modify System.AssignedTo when this Harness 02 execution was explicitly
given an assignee instruction that resolves successfully.

Verification should report the actual Azure assignment after sync.

This prevents Harness 02 from unintentionally changing operational ownership.

==================================================
13. AZURE DEVELOPER BODY
========================

Populate:

Microsoft.VSTS.TCM.ReproSteps

with a clean Azure-compatible HTML body generated directly from the canonical
record.

Required section order:

<strong>Problem</strong>

<canonical Problem>

<strong>Observed Behavior</strong>

<canonical Observed Behavior>

<strong>Reproduction</strong>

<canonical Reproduction>

<strong>Expected Behavior</strong>

<canonical Expected Behavior>

<strong>Business Impact</strong>

<canonical Business Impact>

<strong>User Experience</strong>

<canonical User Experience>

<strong>Investigation Guidance</strong>

<canonical Investigation Guidance>

<strong>Fix Requirement</strong>

<canonical Fix Requirement>

<strong>Recommended Solution</strong>

<canonical Recommended Solution>

<strong>Minimum Working Fix</strong>

<canonical Minimum Working Fix>

<strong>Acceptance Criteria</strong>

<canonical Acceptance Criteria>

==================================================

# 14. HTML PROJECTION RULES

The Azure developer body must preserve the meaning and structure of the
canonical Markdown.

Preserve:

- section order
- paragraphs
- numbered reproduction steps
- bullet lists
- Acceptance Criteria bullets
- line breaks
- code/error values where relevant
- `Not provided` values

Convert Markdown structures into safe Azure-compatible HTML.

Examples:

Markdown bullets:

- First condition
- Second condition

should become an HTML list such as:

<ul>
<li>First condition</li>
<li>Second condition</li>
</ul>

Numbered reproduction:

1. Open...
2. Configure...
3. Observe...

should become:

<ol>
<li>Open...</li>
<li>Configure...</li>
<li>Observe...</li>
</ol>

Escape canonical/user/evidence content safely.

Do not allow supplied evidence text to break HTML structure.

Do not flatten all content into one paragraph.

Do not remove lists.

==================================================
15. DEVELOPER BODY CONTENT BOUNDARY
===================================

The body must be useful to both:

- developers
- repository-aware AI coding agents

But it must remain evidence-grounded.

Do NOT add speculative:

- repository paths
- files
- function names
- class names
- services
- internal APIs
- data models
- databases
- root causes
- architecture

unless already present as known canonical evidence.

Do NOT include:

- competitor research
- unrelated research
- hidden internal notes
- Azure synchronization metadata
- local SQLite metadata
- unsupported assumptions

Harness 02 should not make the ticket "more technical" by inventing a diagnosis.

==================================================
16. TITLE
=========

Populate:

System.Title

as:

[<BUG-ID></bug>] <canonical title></canonical>

Example:

[ART-GOV-004] Approval policy disappears after refresh

Do not alter the canonical title wording except for adding the Bug ID prefix.

==================================================
17. SEVERITY
============

Populate:

Microsoft.VSTS.Common.Severity

from canonical Severity using the repository's established Azure severity
mapping.

Do not independently re-score the bug.

Do not increase or decrease severity during Azure sync.

If the canonical severity cannot be mapped safely to an allowed Azure value:

STOP BEFORE CREATE.

Do not guess.

==================================================
18. PRIORITY
============

Populate:

Microsoft.VSTS.Common.Priority

from canonical Priority using the repository's established Azure priority
mapping.

Do not independently reprioritize the defect.

If canonical priority cannot be safely mapped:

STOP BEFORE CREATE.

Do not guess.

==================================================
19. TAGS
========

Populate:

System.Tags

with:

1. canonical tags
2. exact canonical identity marker:

   ART:<BUG-ID></bug>

Preserve useful canonical tags.

Do not generate a second set of unrelated Azure-only product tags.

Normalize only as required by Azure field formatting.

Never omit the canonical ART marker.

==================================================
20. ENVIRONMENT
===============

Populate:

Microsoft.VSTS.TCM.SystemInfo

ONLY when canonical Environment contains actual supplied information.

Examples:

Testing
Production
Development

If canonical Environment is:

Not provided

do not fabricate an environment.

Do not insert browser, OS, ART version, build number, tenant or infrastructure
details unless they are actually present in the canonical record.

==================================================
21. HISTORY
===========

For newly created Azure Bugs, add:

System.History

with:

Created automatically by ART Product Resolution System for <BUG-ID></bug>.

Example:

Created automatically by ART Product Resolution System for ART-AGENT-002.

Do not use History to copy the entire canonical ticket.

Do not repeatedly append this same history message on idempotent re-runs.

==================================================
22. PARENT RELATION
===================

The Azure Bug must be parented to the Feature resolved from the canonical
Feature through AzureFeatureRouter.

Required hierarchy:

Epic #68782
→ resolved Feature
→ Bug

Use the correct Azure hierarchy relation supported by the existing integration.

Do not create:

Epic
→ Bug

Do not attach the Bug to multiple parent Features.

Do not use the Module field as the parent if the canonical Feature is valid.

==================================================
23. INITIAL CREATE
==================

If preflight confirms that no Azure Bug exists for the canonical ID:

Create exactly ONE Azure Bug.

The initial create operation must contain all supported fields that are already
known at creation time:

- System.Title
- Microsoft.VSTS.TCM.ReproSteps
- Microsoft.VSTS.Common.Severity
- Microsoft.VSTS.Common.Priority
- System.Tags including ART:<BUG-ID></bug>
- Microsoft.VSTS.TCM.SystemInfo when canonical Environment is actually provided
- System.AssignedTo only when explicit assignee resolution succeeded
- System.History
- correct Feature parent relation

Avoid intentionally creating an incomplete shell Bug that immediately requires
basic field repair.

==================================================
24. UNCERTAIN CREATE SAFETY
===========================

If an Azure create request:

- times out
- disconnects
- returns an uncertain transport result
- returns no usable response
- has ambiguous completion status

DO NOT blindly retry creation.

Instead:

1. Search Azure for exact marker:

   ART:<BUG-ID></bug>
2. Search exact title:

   [<BUG-ID></bug>] <canonical title></canonical>
3. Reconcile any matching Bug.

Only retry creation when read-back/search proves that the first create did not
produce the canonical Azure Bug.

This is mandatory duplicate prevention.

==================================================
25. EVIDENCE SOURCE
===================

All evidence must come from the canonical Harness 01 bug directory.

Expected location:

ART-Product-Validation/
bugs/
<FEATURE></feature>/
<BUG-ID></bug>__<slug></slug>/

Only evidence files belonging to that canonical directory may be uploaded.

Do not scan unrelated Feature directories for additional evidence.

Do not attach files merely because their names contain the same module prefix.

==================================================
26. EVIDENCE VALIDATION
=======================

Before uploading each evidence file:

1. Verify the file exists.
2. Verify it belongs to the canonical Bug directory.
3. Verify it is referenced by or consistent with the canonical evidence record.
4. Verify the file has not been replaced by unrelated content.
5. Determine whether the same evidence is already attached to the Azure Bug.

If a canonical evidence file is missing locally:

do not fabricate or replace it.

Mark synchronization incomplete and report the exact evidence blocker.

==================================================
27. EVIDENCE ATTACHMENTS
========================

Upload ALL canonical evidence files that are not already attached.

For each absent evidence file:

1. Upload through the Azure attachment API.
2. Add the Azure `AttachedFile` relation to the canonical Azure Bug.
3. Preserve original binary content.
4. Preserve the deterministic Harness 01 filename where supported.

Supported evidence may include:

- PNG
- JPG/JPEG
- MP4
- JSON
- text/log files
- other canonical evidence types supported by Azure attachment upload

Never alter:

- screenshot dimensions
- screenshot pixels
- video content
- JSON
- logs
- evidence bytes

before upload unless Azure itself requires transport encoding that preserves
content.

==================================================
28. ATTACHMENT IDEMPOTENCY
==========================

Before uploading evidence:

inspect existing Azure attachments.

Do not create duplicate attachments.

Use deterministic evidence identity based on canonical evidence metadata such as:

- canonical filename
- stored local evidence identity
- existing integration metadata
- attachment relation metadata

where available.

Do not decide duplication solely from generic filenames such as:

image.png

when stronger evidence identity exists.

Re-running Harness 02 must not upload the same canonical evidence again.

==================================================
29. EXISTING BUG RECONCILIATION
===============================

If the Azure Bug already exists, compare the Azure projection against the
canonical record.

Fields eligible for synchronization:

- Title
- developer body
- Severity
- Priority
- canonical Tags
- ART:<BUG-ID></bug> marker
- Environment when canonically provided
- correct Feature parent
- explicit assignee only when requested
- canonical evidence attachments

Do not mutate unrelated Azure fields.

Do not overwrite developer-added content outside the fields owned by Harness 02
unless the integration explicitly owns that field.

Do not add duplicate History entries.

==================================================
30. ZERO-CHANGE IDEMPOTENCY
===========================

If Azure already contains the correct canonical projection:

perform zero unnecessary Azure mutations.

Return:

AZURE TICKET: EXISTING

not UPDATED.

A no-op sync is the expected result for a fully synchronized ticket.

==================================================
31. POST-SYNC READBACK
======================

After create/update/attachment synchronization:

read the Azure Bug back.

Do not mark the canonical record SYNCED solely because Azure returned a success
status to a write request.

Verification must use the persisted Azure state.

==================================================
32. POST-SYNC VERIFICATION
==========================

Verify all of the following:

[ ] Azure Work Item exists.

[ ] Work Item Type = Bug.

[ ] Work Item ID is stable.

[ ] Title exactly represents:

    [<BUG-ID></bug>] <canonical title></canonical>

[ ] Tags contain:

    ART:<BUG-ID></bug>

[ ] Correct Feature parent exists.

[ ] Parent Feature is the Feature resolved from canonical `Feature`.

[ ] Feature belongs to Epic #68782.

[ ] Developer body contains every required section.

[ ] Developer body preserves canonical lists and line breaks.

[ ] Problem is present.

[ ] Observed Behavior is present.

[ ] Reproduction is present or explicitly Not provided.

[ ] Expected Behavior is present.

[ ] Business Impact is present.

[ ] User Experience is present.

[ ] Investigation Guidance is present.

[ ] Fix Requirement is present.

[ ] Recommended Solution is present.

[ ] Minimum Working Fix is present.

[ ] Acceptance Criteria are present.

[ ] Severity matches canonical mapping.

[ ] Priority matches canonical mapping.

[ ] Canonical tags are represented.

[ ] Environment matches when canonically provided.

[ ] No environment was fabricated when canonical value is Not provided.

[ ] Explicit assignee matches when one was requested.

[ ] Assignment was not automatically added when none was requested.

[ ] Every expected canonical evidence file is attached.

[ ] No canonical evidence is attached twice.

Do not mark SYNCED when required verification fails.

==================================================
33. DEVELOPER BODY COMPLETENESS
===============================

Return:

DEVELOPER BODY: COMPLETE

only when all required canonical sections were projected into
Microsoft.VSTS.TCM.ReproSteps in the required order and preserved meaningfully.

Return:

DEVELOPER BODY: INCOMPLETE

if any required section:

- is absent
- was truncated
- lost required list structure
- failed HTML projection
- contains incomplete synchronization

==================================================
34. AI-READY VERIFICATION
=========================

Return:

AI-READY: YES

when the Azure Bug contains enough canonical information for a repository-aware
coding agent to:

1. understand the reported symptom
2. understand the observed behavior
3. reproduce it when reproduction exists
4. understand expected behavior
5. see investigation direction
6. understand required fix behavior
7. verify against Acceptance Criteria
8. access the supplied evidence

AI-READY does NOT require:

- known root cause
- known source file
- known function name
- known class
- known implementation

Those are intentionally left for repository investigation.

Return:

AI-READY: NO

when essential canonical content or evidence failed to project.

==================================================
35. LOCAL OPERATIONAL PERSISTENCE
=================================

Use the production operational SQLite/index.

Store exactly one Azure external reference per canonical Bug:

- canonical Bug ID
- Azure Work Item ID
- Azure URL

Also persist supported synchronization metadata such as:

- sync status
- last verified Azure identity
- Feature identity
- attachment synchronization state

where the existing schema supports it.

Do not create duplicate external-reference rows for repeated Harness 02 runs.

==================================================
36. LOCAL EXTERNAL REFERENCE SAFETY
===================================

Before adding the Azure external reference:

check whether one already exists for the canonical Bug ID.

If the same canonical Bug ID already points to the same Azure Work Item ID:

reuse it.

If the canonical Bug ID points to a different Azure Work Item ID than the
verified marker match:

STOP.

Do not silently replace the reference.

If two canonical Bug IDs point to the same Azure Work Item:

STOP and report identity conflict.

==================================================
37. CANONICAL WRITEBACK
=======================

Only after successful Azure readback verification may Harness 02 update the
canonical Markdown.

Update ONLY the:

## Azure DevOps

section.

Required synchronized format:

## Azure DevOps

Work Item ID: <actual Azure ID></actual>
URL: <actual Azure URL></actual>
Parent Feature: <canonical/resolved Feature name>
Parent Feature ID: <actual Feature Work Item ID></actual>
Assigned To: <actual Azure assignee or Unassigned></actual>
Sync Status: SYNCED

Do not rewrite any other canonical section.

==================================================
38. CANONICAL WRITEBACK PROHIBITIONS
====================================

Harness 02 must NOT modify:

- Bug ID
- Title
- Feature
- Module
- Classification
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
- Environment
- Severity
- Priority
- Tags
- Evidence
- Discussion

Harness 01 remains authoritative for canonical investigation content.

==================================================
39. FAILED SYNC WRITEBACK
=========================

If Azure verification fails:

do NOT write:

Sync Status: SYNCED

Keep the canonical bug unsynchronized.

If the existing integration supports failure metadata, record operational
failure state outside the canonical investigation content.

Do not invent an Azure ID or URL.

Do not partially rewrite canonical investigation sections.

==================================================
40. IDEMPOTENCY
===============

Running Harness 02 repeatedly for the same canonical Bug must produce:

- same canonical Bug ID
- same Azure Bug
- same Azure Work Item ID
- same Feature parent
- same canonical identity marker
- same evidence set
- zero duplicate Bugs
- zero duplicate attachments
- zero duplicate external references
- zero unnecessary mutations when Azure already matches

Harness 02 must be safe to rerun.

==================================================
41. MUTATION BOUNDARY
=====================

Harness 02 may mutate ONLY the canonical Bug's Azure projection.

Allowed Azure mutations:

- create canonical Bug
- update Harness-02-owned projected fields
- establish/correct canonical Feature parent
- attach missing canonical evidence
- explicitly assign requested assignee

Not allowed:

- modify unrelated Bugs
- modify Features
- modify Epic #68782
- modify another Bug's attachments
- delete unrelated relations
- modify team configuration
- change project settings
- create new Features
- create new Epics
- automatically assign owners
- mutate unrelated custom fields

==================================================
42. TRANSACTIONAL ORDER
=======================

Use this operational sequence:

PHASE 1 — LOCAL READ

1. Locate canonical Bug.
2. Load Markdown.
3. Load evidence.
4. Load local Azure external reference if present.

PHASE 2 — AZURE PREFLIGHT READ

5. Resolve canonical Feature.
6. Verify Feature.
7. Verify Epic relationship.
8. Search marker.
9. Search exact title.
10. Determine CREATE / EXISTING / RECONCILE.

PHASE 3 — CORE AZURE SYNC

11. Create Bug if absent,
    OR reconcile the existing Bug.
12. Confirm canonical Azure Bug identity.

PHASE 4 — EVIDENCE SYNC

13. Read current Azure attachment state.
14. Upload missing canonical evidence.
15. Add missing AttachedFile relations.

PHASE 5 — VERIFICATION

16. Read Azure Bug.
17. Verify fields.
18. Verify hierarchy.
19. Verify evidence.
20. Verify assignment.

PHASE 6 — LOCAL COMMIT

21. Persist one external reference in operational SQLite/index.
22. Update only canonical `## Azure DevOps`.
23. Mark SYNCED only after successful verification.

Never perform PHASE 6 before PHASE 5 succeeds.

==================================================
43. FAILURE SAFETY
==================

If any operation fails after the Azure Bug already exists:

do not create a replacement Bug.

The next Harness 02 run must reconcile the same Azure Bug using:

ART:<BUG-ID></bug>

If evidence upload partially succeeds:

do not re-upload attachments already verified on the next run.

If local writeback fails after Azure verification:

preserve the Azure Bug and reconcile local state on the next run.

Do not create another Azure Bug to recover from local persistence failure.

==================================================
44. REQUIRED REGRESSION TESTS
=============================

Run the existing Harness 02 regression suite.

Validate at minimum:

1. Feature routing from canonical `Feature`.
2. Feature belongs to Epic #68782.
3. Unknown Feature fails closed.
4. Missing canonical Bug fails closed.
5. Duplicate local Bug ID fails closed.
6. Azure marker duplicate prevention.
7. Exact-title duplicate prevention.
8. Complete developer-body projection.
9. HTML list preservation.
10. Reproduction list preservation.
11. Acceptance Criteria list preservation.
12. Severity mapping.
13. Priority mapping.
14. Environment omission when Not provided.
15. Default Azure behavior remains unassigned.
16. Explicit assignee resolution.
17. Unknown assignee fails closed.
18. Feature parent relation.
19. Evidence upload.
20. Evidence ownership validation.
21. Duplicate attachment prevention.
22. Uncertain-create reconciliation.
23. External-reference uniqueness.
24. Canonical writeback limited to `## Azure DevOps`.
25. Post-sync readback verification.
26. Idempotent second run produces no duplicate Bug.
27. Idempotent second run produces no duplicate evidence.
28. Fully synchronized ticket produces zero unnecessary mutations.

==================================================
45. PRE-SYNC VALIDATION
=======================

Before the first Azure mutation verify:

[ ] Canonical Bug exists.

[ ] Exactly one canonical record exists for Bug ID.

[ ] Canonical Feature exists.

[ ] Canonical Feature is supported.

[ ] AzureFeatureRouter resolves exactly one Feature.

[ ] Resolved Azure item exists.

[ ] Resolved Azure item is Work Item Type = Feature.

[ ] Feature belongs to Epic #68782.

[ ] Canonical title exists.

[ ] Canonical developer-body sections can be parsed.

[ ] Canonical Severity can be mapped.

[ ] Canonical Priority can be mapped.

[ ] Evidence directory exists when evidence is expected.

[ ] Explicit assignee resolves when supplied.

[ ] Existing Azure marker search is complete.

[ ] Existing exact-title search is complete.

[ ] Azure identity conflict does not exist.

If any required precondition fails:

STOP BEFORE MUTATION.

==================================================
46. POST-SYNC VALIDATION
========================

Before marking SYNCED verify:

[ ] Azure Bug exists.

[ ] Correct Azure Work Item ID.

[ ] Work Item Type = Bug.

[ ] Correct title.

[ ] Correct ART marker.

[ ] Correct parent Feature.

[ ] Parent Feature belongs to Epic #68782.

[ ] Developer body is COMPLETE.

[ ] Correct Severity.

[ ] Correct Priority.

[ ] Correct Tags.

[ ] Correct Environment when applicable.

[ ] Correct explicit assignee when supplied.

[ ] All canonical evidence attached.

[ ] No duplicate evidence.

[ ] Exactly one local Azure external reference.

Only then:

Sync Status = SYNCED

==================================================
47. BLOCKING CONDITIONS
=======================

Return FAILED and STOP when any safety-critical synchronization condition cannot
be established.

Examples:

- canonical Bug not found
- duplicate canonical Bug ID
- Feature missing
- Feature unsupported
- Feature unmapped
- Feature not found in Azure
- Feature not beneath Epic #68782
- Azure duplicate marker conflict
- Azure title identity conflict
- canonical severity unmappable
- canonical priority unmappable
- explicit assignee unresolved
- evidence expected but canonical file missing
- attachment ownership cannot be established
- Azure create state remains ambiguous after reconciliation
- post-sync verification failed
- external-reference identity conflict
- canonical writeback failed after sync verification

Never work around these by creating a second Bug.

==================================================
48. COMPLETION OUTPUT
=====================

Return ONLY:

AZURE TICKET: CREATED / EXISTING / UPDATED / FAILED
BUG ID: <canonical Bug ID></canonical>
WORK ITEM: #<Azure ID or Not created></azure>
FEATURE: <Feature name></feature> (#<Feature ID></feature>)
ASSIGNEE: <actual Azure assignee or Unassigned></actual>
SEVERITY: <canonical severity></canonical>
PRIORITY: <canonical priority></canonical>
DEVELOPER BODY: COMPLETE / INCOMPLETE
EVIDENCE: <attached></attached>/<expected></expected>
AI-READY: YES / NO
SYNC STATUS: SYNCED / NOT_SYNCED

If FAILED, also return:

BLOCKER: <exact reason></exact>

==================================================
49. OUTPUT RULES
================

Do not output:

- the full canonical ticket
- implementation commentary
- Azure API payloads
- raw access tokens
- PAT values
- internal stack traces unless specifically requested for debugging
- unrelated test output

Do not continue into another harness.

STOP.

==================================================
50. CORE HARNESS 02 RULE
========================

HARNESS 01 OWNS THE BUG.

HARNESS 02 OWNS THE AZURE PROJECTION.

Feature routing comes from the canonical Harness 01 `Feature`.

AzureFeatureRouter determines the existing Azure Feature.

Harness 02 must create or reconcile exactly one Azure Bug beneath that Feature,
attach exactly the canonical evidence belonging to that Bug, verify the persisted
Azure state, and only then mark the canonical record SYNCED.

Never duplicate.
Never guess.
Never create missing Azure hierarchy.
Never mark SYNCED without readback verification.
