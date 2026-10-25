# ART VALIDATION DASHBOARD SYNC ORCHESTRATOR
## Azure Lifecycle → ART Ledger → Public Report → GitHub Pages

## ROLE

ORCHESTRATOR

## EXECUTION

Coordinator/user-facing end-to-end workflow.

This prompt coordinates existing hardened lifecycle/report/deployment prompts.
It MUST NOT duplicate, replace, or weaken their behavioral contracts.

---

# 1. PURPOSE

Synchronize the latest Azure DevOps bug lifecycle information into ART Product
Validation, regenerate the sanitized public validation dashboard, deploy it to
GitHub Pages, and verify the live result.

Canonical flow:

Azure DevOps
→ Harness 03: Azure Resolution Sync
→ Canonical Bug Lifecycle + ART_PRODUCT_VALIDATION_LEDGER.md
→ Harness 04: Public Validation Report
→ docs/index.html
→ GitHub Pages Deployment Harness
→ Verified Live Dashboard

This orchestrator owns ONLY the handoff between these stages.

---

# 2. REQUIRED DEPENDENCIES

Resolve these prompts from the canonical Prompt Registry. Do not guess paths if
the registry defines them.

Expected canonical prompts after prompt-registry migration:

1. `prompts/bugs/azure_resolution_sync.md`
2. `prompts/bugs/publish_validation_report.md`
3. `prompts/git/github_pages_deploy.md`

If the prompt-registry migration has not yet completed, locate the authoritative
equivalent files from the repository and verify their identity before execution.

If any required dependency is missing or ambiguous:

`PIPELINE: BLOCKED`

Report the missing dependency and STOP.

---

# 3. INPUT

Supported execution modes:

## MODE A — SINGLE BUG

Input:

`BUG_ID: ART-<MODULE>-###`

Use when one specific Azure-backed bug must be synchronized before publishing.

## MODE B — APPROVED BATCH

Input:

`BUG_IDS: <explicit list of canonical Bug IDs>`

Use only the supplied Bug IDs.

## MODE C — ALL ELIGIBLE BUGS

Input:

`SYNC_SCOPE: ALL_ELIGIBLE`

This mode is allowed only when the current Harness 03 contract explicitly
supports controlled production reconciliation.

Do not interpret a missing Bug ID as permission to run `--all`.

If scope is unspecified or ambiguous:

STOP and request an explicit scope.

Optional deployment inputs:

`TARGET_OWNER: ART-Automation-Lab`
`TARGET_REPOSITORY: art-validation-report`
`TARGET_VISIBILITY: PUBLIC`
`PAGES_BRANCH: main`
`PAGES_PATH: /`
`NOJEKYLL: YES`

Use existing verified deployment configuration when already established.
Never silently change repository ownership, visibility, branch, or Pages path.

---

# 4. GLOBAL SAFETY BOUNDARIES

This orchestrator MUST preserve the ownership boundaries of all child harnesses.

It MUST NOT independently:

- interpret Azure lifecycle state
- decide ART validation disposition
- edit canonical Bug investigation content
- fabricate developer comments
- infer Azure State from ART Status
- mark a bug VERIFIED_FIXED
- alter Feature records
- create Azure work items
- update Azure work items
- close/reopen Azure work items
- alter repository visibility
- expose the investigation repository through GitHub Pages
- bypass report sanitization
- rewrite Harness 03
- rewrite Harness 04
- rewrite the GitHub Pages deployment harness

Harness 03 owns Azure → ART lifecycle synchronization.
Harness 04 owns Ledger → sanitized HTML generation.
GitHub Pages Deploy owns sanitized HTML → live publication.

---

# 5. PREFLIGHT

Before executing any stage:

1. Read this orchestrator completely.
2. Resolve and read all three dependency prompts completely.
3. Read `prompts/PROMPT_REGISTRY.md` when present.
4. Verify Git working-tree state.
5. Preserve unrelated user changes.
6. Verify the canonical ledger exists.
7. Verify the public report generator/deployment configuration exists.
8. Verify GitHub CLI authentication only if deployment will be reached.
9. Verify requested Bug IDs exist locally for SINGLE BUG / APPROVED BATCH mode.

Do not mutate production state during preflight.

If pre-existing changes conflict with files a child harness must update:

STOP and report the conflict.

---

# 6. STAGE 1 — AZURE LIFECYCLE SYNCHRONIZATION

Invoke the authoritative Azure Resolution Sync / Harness 03 contract.

For each requested Bug ID, Harness 03 must remain authoritative for:

- Azure identity verification
- Azure State
- Azure Reason
- current Azure assignee
- meaningful human developer feedback
- revision/comment readback
- ART disposition
- Retest Required
- Action Required
- canonical Resolution Status
- append-only Resolution History
- SQLite lifecycle projection
- primary ART Product Validation ledger row
- lifecycle tracking row
- Summary recomputation
- consistency verification
- idempotency

Azure remains READ-ONLY during this stage.

Required invariant:

`Azure State != ART Validation Disposition`

Never convert an Azure state directly into an ART validation result.

Examples:

Azure `Resolved`
does NOT automatically mean
ART `VERIFIED_FIXED`.

Azure `Closed`
does NOT automatically mean
ART `VERIFIED`.

Harness 03 decides lifecycle projection according to its existing contract.

---

# 7. STAGE 1 FAILURE GATE

If Harness 03 returns:

FAILED
BLOCKED
IDENTITY_MISMATCH
or another terminal blocker,

STOP THE PIPELINE.

Do NOT regenerate the public report.
Do NOT deploy GitHub Pages.

Return:

`FAILED_STAGE: AZURE_RESOLUTION_SYNC`

with the exact non-sensitive blocker.

For approved batch execution, do not silently publish a partially synchronized
dashboard when any requested Bug fails unless Harness 03 explicitly defines the
batch as successful with documented skips and the user authorized partial
publication.

Default behavior is FAIL CLOSED.

---

# 8. STAGE 1 NO-CHANGE BEHAVIOR

Harness 03 may determine that Azure has no meaningful lifecycle change.

That is not automatically a pipeline failure.

If Harness 03 returns a valid:

NO_CHANGE

and confirms local canonical/SQLite/ledger projections are consistent, continue.

If Azure is unchanged but Harness 03 performs local reconciliation, treat its
authoritative successful result as eligible to continue.

---

# 9. STAGE 2 — PUBLIC REPORT GENERATION

Only after Stage 1 succeeds, invoke:

`prompts/bugs/publish_validation_report.md`

Harness 04 must read the current authoritative:

`ART_PRODUCT_VALIDATION_LEDGER.md`

and regenerate the sanitized static report.

Expected output:

`docs/index.html`

Harness 04 remains READ-ONLY against:

- Azure
- canonical lifecycle truth
- SQLite lifecycle truth
- ledger lifecycle truth

It may generate/update only its approved report artifacts.

---

# 10. REQUIRED PUBLIC REPORT FIDELITY

The generated dashboard must preserve separate fields for:

- Bug ID
- Title
- Feature
- Severity
- Azure State
- ART Status
- Retest
- Developer Comment
- Last Lifecycle Update

Critical rules:

Azure State = synchronized Azure workflow state.

ART Status = ART validation interpretation.

Retest = ART retest state.

Developer Comment = latest approved/sanitized meaningful human developer
comment available from the synchronized report source.

Do NOT infer one field from another.

If Azure State is unavailable:

display the Harness 04-approved fallback.

Do not fabricate it.

If Developer Comment is unavailable:

use the Harness 04-approved fallback.

Do not fabricate a developer statement.

---

# 11. STAGE 2 SECURITY GATE

Harness 04 must complete its privacy/security validation before deployment.

At minimum the report must not expose prohibited internal data such as:

- Azure organization/project URLs
- Azure work item URLs
- Azure numeric work item IDs when prohibited by Harness 04
- credentials
- access tokens
- local filesystem paths
- SQLite/database files
- canonical evidence paths
- internal repository paths
- unapproved email addresses
- private evidence

If Harness 04 reports sanitization failure:

STOP.

Do NOT deploy.

Return:

`FAILED_STAGE: PUBLIC_REPORT_GENERATION`

or

`FAILED_STAGE: REPORT_SANITIZATION`

as appropriate.

---

# 12. STAGE 2 SOURCE-OF-TRUTH CHECK

Before deployment verify:

- report generation succeeded
- `docs/index.html` exists
- ledger summary validation passed
- unique Bug-row validation passed
- Azure State fidelity passed
- ART Status fidelity passed
- Retest fidelity passed
- Developer Comment handling passed
- sanitization passed
- private-data scan passed

Do not deploy stale HTML after a failed report generation.

---

# 13. STAGE 3 — GITHUB PAGES DEPLOYMENT

Only after Stage 2 passes, invoke:

`prompts/git/github_pages_deploy.md`

Use the existing dedicated sanitized publishing repository.

Expected ART configuration unless repository state/config says otherwise:

TARGET_OWNER:
`ART-Automation-Lab`

TARGET_REPOSITORY:
`art-validation-report`

PAGES_BRANCH:
`main`

PAGES_PATH:
`/`

NOJEKYLL:
`YES`

SOURCE_ARTIFACT:
`docs/index.html`

Do not deploy from the investigation repository itself.

The deployment harness owns repository creation/update, isolated publication,
Pages configuration, deployment status verification, and public URL
verification according to its own contract.

---

# 14. DEPLOYMENT ISOLATION

Required architecture:

PRIVATE/INTERNAL SOURCE WORKSPACE
`art-investigation-lab`
        ↓
sanitized `docs/index.html`
        ↓
isolated publishing workspace
        ↓
`ART-Automation-Lab/art-validation-report`
        ↓
GitHub Pages

Never publish canonical Bug folders, Feature folders, evidence, SQLite,
internal Markdown, `.env`, credentials, research data, or source repository
history as part of the dashboard deployment.

---

# 15. STAGE 3 FAILURE GATE

A successful Git push is NOT a successful deployment.

PASS requires the GitHub Pages deployment harness to verify the actual
deployment/public site according to its contract.

If push succeeds but Pages fails:

return pipeline failure at GitHub Pages stage.

If Pages builds but public verification fails:

return pipeline failure at live verification stage.

Do not claim LIVE merely because files were pushed.

---

# 16. IDEMPOTENCY

Repeated execution with no Azure lifecycle changes and no generated-report
changes must not create unnecessary mutations.

Expected behavior may include:

Harness 03:
`NO_CHANGE`

Harness 04:
deterministic regeneration or no material change

GitHub Pages Deploy:
`NO_CHANGE`

Do not create:

- duplicate lifecycle events
- duplicate ledger rows
- duplicate publishing repositories
- empty deployment commits
- duplicate Pages configuration

---

# 17. AUDIT / MUTATION CONTRACT

The final result must distinguish mutations by stage.

Allowed:

Harness 03:
- canonical lifecycle metadata
- Resolution History when a new lifecycle event exists
- SQLite lifecycle projection
- ART_PRODUCT_VALIDATION_LEDGER.md

Harness 04:
- approved public report artifacts such as `docs/index.html`

GitHub Pages Deploy:
- dedicated publishing repository static artifacts
- Pages configuration when necessary

Forbidden:

- Azure writes
- unrelated Bug content changes
- Feature changes
- research changes
- source repository visibility changes
- unrelated Git changes

---

# 18. SOURCE REPOSITORY GIT POLICY

This orchestration is for lifecycle/report publication.

Do not automatically commit/push unrelated changes in
`art-investigation-lab`.

The GitHub Pages deployment harness must use its isolated publishing workflow.

Do not add the public publishing repository as a deployment remote to the
source investigation repository unless its own hardened contract explicitly
requires and safely supports that design.

---

# 19. CONTROLLED VERIFICATION

After all stages succeed, verify the final live dashboard reflects the
synchronized local report.

For SINGLE BUG mode, verify the target Bug is present in the generated report
and that its public fields match the synchronized public model.

For APPROVED BATCH mode, verify all requested publishable Bugs are represented
as expected.

For ALL_ELIGIBLE mode, verify the generated report's row count against the
current ledger-derived count.

Do not hardcode historical counts such as 39.

---

# 20. PIPELINE RESULT RULES

Return:

`PIPELINE: COMPLETE`

only when:

1. Azure Resolution Sync succeeded or validly returned NO_CHANGE.
2. Canonical/local lifecycle consistency passed.
3. ART_PRODUCT_VALIDATION_LEDGER.md is current for requested scope.
4. Public report generation passed.
5. Sanitization passed.
6. GitHub Pages deployment passed or validly returned NO_CHANGE.
7. Actual public site verification passed.

Return:

`PIPELINE: BLOCKED`

when a dependency/precondition prevents safe execution.

Return:

`PIPELINE: FAILED`

when an attempted stage fails.

Never continue past a failed mandatory stage.

---

# 21. REQUIRED COMPLETION OUTPUT

Return:

PIPELINE:
COMPLETE / NO_CHANGE / BLOCKED / FAILED

WORKFLOW:
VALIDATION DASHBOARD SYNC

SYNC SCOPE:
SINGLE_BUG / APPROVED_BATCH / ALL_ELIGIBLE

BUGS REQUESTED:
<count or list>

BUGS SYNCHRONIZED:
<count>

BUGS NO_CHANGE:
<count>

BUGS BLOCKED:
<count>

HARNESS 03:
PASS / NO_CHANGE / BLOCKED / FAILED

AZURE READ:
PASS / NOT_RUN

AZURE MUTATIONS:
0

CANONICAL LIFECYCLE:
UPDATED / NO_CHANGE / NOT_RUN

SQLITE LIFECYCLE:
UPDATED / RECONCILED / NO_CHANGE / NOT_RUN

ART PRODUCT VALIDATION LEDGER:
UPDATED / RECONCILED / NO_CHANGE / NOT_RUN

LEDGER CONSISTENCY:
PASS / FAIL / NOT_RUN

HARNESS 04:
PASS / NO_CHANGE / BLOCKED / FAILED

PUBLIC REPORT:
UPDATED / NO_CHANGE / NOT_RUN

REPORT PATH:
docs/index.html / NOT_AVAILABLE

REPORT SANITIZATION:
PASS / FAIL / NOT_RUN

AZURE STATE FIDELITY:
PASS / FAIL / NOT_RUN

ART STATUS FIDELITY:
PASS / FAIL / NOT_RUN

DEVELOPER COMMENT:
PASS / FAIL / NOT_RUN

GITHUB PAGES DEPLOY:
PASS / NO_CHANGE / BLOCKED / FAILED

PUBLISHING REPOSITORY:
<owner/repository or NOT_RUN>

PAGES DEPLOYMENT:
PASS / NO_CHANGE / FAIL / NOT_RUN

PUBLIC URL:
<verified GitHub-returned URL or NOT_AVAILABLE>

LIVE HTTP CHECK:
PASS / FAIL / NOT_RUN

LIVE CONTENT CHECK:
PASS / FAIL / NOT_RUN

PRIVATE FILE EXPOSURE:
NONE / DETECTED / NOT_CHECKED

SOURCE REPOSITORY VISIBILITY CHANGED:
NO

SOURCE REPOSITORY PUSH:
NOT PERFORMED unless separately and explicitly authorized

FAILED_STAGE:
NONE / PREFLIGHT / AZURE_RESOLUTION_SYNC / LEDGER_CONSISTENCY /
PUBLIC_REPORT_GENERATION / REPORT_SANITIZATION / GITHUB_PAGES_DEPLOY /
LIVE_VERIFICATION

BLOCKER:
<exact reason or NONE>

STOP.

---

# 22. CORE INVARIANT

This orchestrator coordinates authoritative stages.

It does not become a fourth source of lifecycle truth.

Azure
→ Harness 03
→ ART Ledger
→ Harness 04
→ Sanitized HTML
→ GitHub Pages Deploy
→ Verified Live Dashboard

If any authoritative stage fails, stop at that boundary.
