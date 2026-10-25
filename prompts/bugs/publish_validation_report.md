# ART PUBLIC VALIDATION REPORT PUBLISHER
## HARNESS 04 — REUSABLE PRODUCTION PROMPT

## PURPOSE

Generate a sanitized, read-only, local HTML dashboard from the existing ART Product Validation master ledger.

Harness 04 owns PUBLIC REPORT GENERATION ONLY.

Core direction:

`CANONICAL LEDGER → SANITIZED PUBLIC MODEL → STATIC HTML`

Never reverse this direction. The generated report is not a source of truth.

Phase 1 is LOCAL GENERATION ONLY. Do not configure GitHub Pages, publish externally, modify Azure DevOps, canonical bugs, the master ledger, or lifecycle SQLite state.

## 1. INPUT

Primary source:

`ART-Product-Validation/ART_PRODUCT_VALIDATION_LEDGER.md`

Read the existing production ledger directly. Do not require manual table copying.

If it cannot be found, STOP and return:

`REPORT GENERATION: FAILED`
`BLOCKER: CANONICAL LEDGER NOT FOUND`

## 2. SOURCE-OF-TRUTH BOUNDARY

Authoritative sources remain the canonical bug Markdown records, production master ledger, lifecycle SQLite/index, and Azure DevOps for Azure lifecycle facts.

Harness 04 is read-only against all authoritative sources. It MUST NOT update Status, Retest, Owner, Developer Update, lifecycle disposition, Summary, canonical Markdown, bug IDs, SQLite, Azure, or evidence.

If source data is inconsistent, fail safely. Never repair source data from Harness 04.

## 3. OUTPUT

Generate:

`docs/index.html`

Create `docs/` if absent.

The output must be a self-contained static report suitable for later GitHub Pages hosting. Prefer HTML + CSS + minimal vanilla JavaScript.

Do not introduce React, Vue, Angular, Node servers, API backends, databases, authentication systems, external JS/CSS frameworks, analytics, or telemetry.

The report must work by opening `docs/index.html` locally.

## 4. PUBLIC-SAFE DATA CONTRACT

Do not dump the complete ledger into HTML. Construct an explicit public report model.

Allowed Phase 1 fields:

- Bug ID
- Title
- Feature
- Severity
- Status
- Retest Status
- Last Updated

Do NOT expose by default:

- Azure URLs or internal work-item URLs
- Azure numeric work-item IDs
- employee names / Owner / assignee
- email addresses or Azure identity data
- SQLite metadata or database paths
- local filesystem paths
- canonical bug paths
- evidence paths or sensitive evidence filenames
- internal comments/discussion
- full developer comments
- implementation/debug details
- harness metadata
- credentials, tokens, secrets
- stack traces
- internal API endpoints
- investigation guidance
- fix recommendations
- private acceptance evidence

## 5. FEATURE DERIVATION

The primary Bugs table may not contain Feature. Derive it only from reliable existing data, in this order:

1. existing `Azure Resolution & Lifecycle Tracking` row for the Bug ID
2. canonical bug metadata through existing repository utilities
3. unambiguous existing canonical feature mapping

If Feature cannot be determined reliably, use `Not Available`. Do not invent it.

## 6. LAST UPDATED DERIVATION

For lifecycle-synchronized bugs, use the existing lifecycle `Last Azure Sync` when appropriate and render it human-readably.

If unavailable, show `Not Available`.

Do not fabricate an individual bug date from report-generation time. The page may separately show `Report Generated: <timestamp>`.

## 7. SUMMARY CONTRACT

Render cards for Total Bugs, Open, Fixing, Retest, Verified, Closed, Blocked.

Parse the primary `## Bugs` table and independently calculate counts. Compare them with `## Summary`.

Invariant:

`Total Bugs = Open + Fixing + Retest + Verified + Closed + Blocked`

If calculated counts disagree with the ledger Summary, STOP:

`REPORT GENERATION: FAILED`
`BLOCKER: LEDGER SUMMARY INCONSISTENCY`

Never publish inconsistent numbers.

## 8. BUG TABLE

Render one row per Bug ID with:

`Bug ID | Title | Feature | Severity | Status | Retest | Last Updated`

Do not expose the Markdown link target. Bug ID is plain text in Phase 1. Do not link to private canonical bug files.

Each Bug ID must occur exactly once. Duplicate Bug IDs are a generation failure.

## 9. STATUS PRESENTATION

Supported operational statuses:

- OPEN
- FIXING
- RETEST
- VERIFIED
- CLOSED
- BLOCKED

Present the primary ledger Status. Do not derive a new status model. Unknown statuses fail validation.

## 10. RETEST PRESENTATION

Present the primary ledger Retest value in normalized form:

- Pending
- Required
- Not Required
- Passed
- Failed

Normalize trivial punctuation such as `Pending.` → `Pending`.

Do not reinterpret lifecycle logic. Harness 03 owns classification; Harness 04 presents it.

## 11. UI REQUIREMENTS

Create a clean professional dashboard with:

1. Header
2. Report-generation timestamp
3. Summary cards
4. Search/filter controls
5. Bug table
6. Small disclaimer/footer

Header: `ART Product Validation`
Subtitle: `Product Quality & Resolution Dashboard`

Summary cards: Total, Open, Fixing, Retest, Verified, Closed, Blocked.

Client-side controls:

- text search
- Status filter
- Feature filter
- Severity filter

Search must match Bug ID, Title, and Feature at minimum.

The page must work on desktop, tablet, and mobile. Use semantic HTML and accessible form labels. Avoid unnecessary animation.

## 12. VISUAL STYLE

Use a restrained professional dashboard style: clean spacing, readable typography, clear hierarchy, subtle borders, status badges, responsive table behavior, accessible contrast.

Do not use neon effects, excessive gradients, decorative animation, or marketing clutter.

Do not embed logos unless an approved repository asset is explicitly designated for public use. Do not invent/redraw ART branding.

## 13. JAVASCRIPT BOUNDARY

JavaScript may only provide presentation behavior: search, filtering, visible row count, optional sorting.

No data mutation, Azure calls, GitHub API calls, external service calls, analytics, or telemetry.

## 14. SECURITY / SANITIZATION

Treat ledger content as untrusted text. Escape HTML special characters before insertion. Titles and fields must not inject executable HTML/JavaScript.

Scan generated HTML for accidental exposure of obvious private/internal patterns, including where applicable:

- `dev.azure.com`
- local `/home/` paths
- Windows local paths
- email addresses
- bearer/access tokens
- secrets
- canonical evidence paths
- SQLite/database paths

If prohibited data appears, fail generation and report only the exposure category, never the secret itself.

## 15. RESOLUTION SUMMARY — PHASE 1

Do NOT render Resolution Summary in Phase 1.

Existing lifecycle text may contain developer wording or internal product discussion. A future contract may introduce a separately sanitized public summary.

Do not expose `Developer Update` directly.

## 16. PUBLIC OWNER POLICY — PHASE 1

Do not expose Owner/current Azure assignee in Phase 1. A later explicit contract may allow team-level or named ownership.

## 17. LOCAL REPORT VALIDATION

After generating `docs/index.html`, verify:

- source ledger read successfully
- source ledger unchanged
- primary Bugs table parsed
- every Bug ID appears exactly once
- no duplicates
- all statuses supported
- calculated Summary matches ledger Summary
- Summary invariant passes
- required public columns exist
- Feature derivation is evidence-grounded
- private Markdown link targets absent
- Azure URLs absent
- Azure numeric IDs absent
- Owner/assignee absent
- developer comments absent
- email addresses absent
- local paths absent
- evidence paths absent
- HTML escaping applied
- search works
- Status filter works
- Feature filter works
- Severity filter works
- report opens locally without backend
- zero canonical bug mutations
- zero ledger mutations
- zero SQLite mutations
- zero Azure mutations

## 18. REQUIRED TESTS

TEST 1 — VALID LEDGER
Valid ledger → report generated, unique rows correct, summary correct.

TEST 2 — SUMMARY MISMATCH
Primary table and Summary disagree → generation fails.

TEST 3 — DUPLICATE BUG ID
Same Bug ID twice → generation fails.

TEST 4 — PRIVATE LINK REMOVAL
Markdown Bug link exists → public HTML shows ID but not canonical path.

TEST 5 — HTML INJECTION SAFETY
HTML/script-like title → escaped text, no execution.

TEST 6 — PRIVATE DATA SAFETY
Fixture contains Azure URL/email/local path → prohibited value absent from output.

TEST 7 — FILTERS
Search, Status, Feature, Severity controls function.

TEST 8 — SOURCE IMMUTABILITY
Compare authoritative sources before/after → ledger/canonical bugs/SQLite unchanged.

TEST 9 — REPEAT GENERATION
Run twice unchanged → same report data, no duplicates or accumulated generated content. Generation timestamp may differ.

## 19. PHASE 1 IMPLEMENTATION TASK

Read this entire contract before changing code.

Implement ONLY local public-report generation:

`ART_PRODUCT_VALIDATION_LEDGER.md → parse → validate → sanitized public model → docs/index.html → validate output`

Reuse existing repository parsing/utilities where appropriate.

Do NOT configure GitHub Pages, make the repository public, push to a public repo, add GitHub Actions publishing, add deployment scripts, schedule publishing, alter Harness 01/02/03, process Azure, perform retesting, or alter production lifecycle state.

## 20. IMPLEMENTATION SAFETY

Inspect the existing repository first and use the smallest appropriate implementation consistent with the bugs-ledger service.

Conceptual paths, only if consistent with the repository:

- `core/reporting/public_report.py`
- `scripts/publish_validation_report.py`
- `tests/test_public_report.py`
- `docs/index.html`

Do not refactor unrelated lifecycle code.

## 21. PRODUCTION LEDGER VALIDATION

After unit/mocked tests pass, generate the local report once from the current production ledger.

This is allowed because Harness 04 is read-only.

Expected:

- exactly one public row per primary bug
- calculated counts match ledger
- no source mutation
- no prohibited internal exposure

Do not publish externally. The user must review local HTML before hosting is configured.

## 22. COMPLETION OUTPUT

Return only:

IMPLEMENTATION: PASS / PARTIAL / BLOCKED
HARNESS: HARNESS 04
SOURCE LEDGER: PASS / FAIL
PUBLIC MODEL: PASS / FAIL
SUMMARY VALIDATION: PASS / FAIL
UNIQUE BUG ROWS: PASS / FAIL
HTML GENERATION: PASS / FAIL
SEARCH: PASS / FAIL
STATUS FILTER: PASS / FAIL
FEATURE FILTER: PASS / FAIL
SEVERITY FILTER: PASS / FAIL
SANITIZATION: PASS / FAIL
PRIVATE DATA SCAN: PASS / FAIL
SOURCE IMMUTABILITY: PASS / FAIL
LOCAL REPORT: <path or NOT_GENERATED>
PUBLICATION: NOT PERFORMED
AZURE MUTATIONS: 0
LEDGER MUTATIONS: 0
SQLITE MUTATIONS: 0
FILES CHANGED:
<list>
BLOCKER: <reason or NONE>

STOP.

## 23. STAGE TERMINATION

After the completion output, STOP.

Do not configure GitHub Pages, publish, change repository visibility, or proceed into deployment.

The generated local `docs/index.html` must be reviewed before the next stage.

## 24. CORE RULE

Harness 01 records what ART observed.
Harness 02 projects the canonical bug into Azure.
Harness 03 synchronizes post-creation Azure lifecycle state into ART validation.
Harness 04 publishes a sanitized READ-ONLY representation of approved validation state.

Harness 04 never owns validation truth.

Preserve:

`CANONICAL VALIDATION STATE → SANITIZED PUBLIC REPORT → STATIC HTML`

Never reverse it.

# HARNESS 04 REFINEMENT — CURRENT LEDGER + PUBLIC UI CONTRACT

This refinement supersedes conflicting presentation/parser rules above.

## A. Harness boundary
Harness 04 remains read-only presentation. It MUST NOT modify Harness 03, Azure client/config, canonical bug Markdown, master ledger, or SQLite. It must not contact Azure.

## B. Owner-column compatibility
The primary Bugs table may now contain:
`Bug ID | Title | Severity | Status | Owner | Developer Update | Retest`

Parse all columns by header name, not fixed position. Continue supporting the prior table without Owner. `Owner` is internal and MUST NOT appear in the public HTML.

## C. Lifecycle fidelity
Status and Retest MUST come from the primary ledger projection produced by Harness 03. Harness 04 must not independently interpret Azure state/reason, comments, assignee, fix claims, or retest handoffs.

If upstream state is inconsistent, fail with:
`BLOCKER: UPSTREAM LIFECYCLE INCONSISTENCY`

## D. Public-safe Latest Update
Add `Latest Update`.

Do not expose raw developer comments or raw internal Developer Update text. Translate synchronized ART lifecycle state into a public-safe phrase:

- OPEN → Awaiting engineering action
- IN_PROGRESS → Engineering work in progress
- FIX_CLAIMED → Fix reported; awaiting validation handoff
- RETEST_REQUIRED → Fix available; awaiting ART verification
- VERIFIED_FIXED → Fix verified by ART
- REPRODUCED_AFTER_FIX → Issue reproduced after fix attempt
- PRODUCT_DECISION_PENDING → Awaiting product decision
- INTENTIONAL_BEHAVIOR → Closed as intended behavior
- NOT_A_BUG → Closed after validation review
- DUPLICATE → Closed as duplicate
- BLOCKED → Blocked pending required dependency or decision

Never include employee/product-person names, raw comments, internal discussion, or Azure IDs.

## E. Meaningful lifecycle timestamp
Public column: `Last Lifecycle Update`.

Prefer Harness 03's `Latest Lifecycle Update` or equivalent meaningful lifecycle-change timestamp.

Do NOT use `Last Azure Sync` as a substitute merely because it is newer.

If unavailable display `Not Available`.

The page may separately show `Report Generated`.

## F. Public table
Render exactly:
`Bug ID | Title | Feature | Severity | Status | Retest | Latest Update | Last Lifecycle Update`

Bug ID must be plain text. No canonical/private Markdown links.

## G. Light corporate theme — REQUIRED
Replace the previous dark dashboard.

Use:
- white or very light neutral page background
- white cards
- dark charcoal text
- muted secondary text
- restrained cyan/ART-style accent
- subtle borders and shadows
- compact professional summary cards
- clear status badges
- responsive table
- sticky header where practical
- visible focus states

Do NOT use:
- full-page dark/navy background
- neon/glowing treatment
- heavy gradients
- excessive animation
- invented ART logo variants

Header:
`ART Product Validation`

Subtitle:
`Product Quality & Resolution Dashboard`

## H. Search/filter UX
Provide:
- text search
- Status filter
- Feature filter
- Severity filter
- `Showing X of Y bugs`

Search matches Bug ID, Title, Feature, Latest Update. Filters work together entirely client-side.

## I. Public privacy
Do not render:
- Owner/assignee
- developer names/email
- Azure IDs/URLs
- raw Azure state/reason
- raw comments
- local paths
- canonical/evidence paths
- SQLite paths/metadata
- credentials/tokens/secrets
- internal APIs/debug details

Escape all ledger-derived text before HTML insertion.

## J. Production-readiness wording
A generated report does not prove every Azure ticket is currently synchronized.

Unless a separate approved reconciliation state proves that, footer must say:

`Report reflects the latest lifecycle data synchronized into the ART validation ledger.`

Do not claim `Live Azure data`, `Real-time`, or that all Azure tickets are current.

## K. Required refinement tests
1. Legacy 6-column table parses.
2. 7-column Owner table parses.
3. Owner is absent from public HTML.
4. Summary mismatch fails.
5. Duplicate Bug ID fails.
6. Private Markdown links are removed.
7. HTML/script-like values are escaped.
8. Azure IDs/URLs are absent.
9. RETEST_REQUIRED gives `Fix available; awaiting ART verification`.
10. PRODUCT_DECISION_PENDING gives `Awaiting product decision`.
11. Meaningful lifecycle timestamp is preferred over Last Azure Sync.
12. Search + Status + Feature + Severity filters work together.
13. Source ledger/canonical bugs/SQLite remain unchanged.
14. Repeat generation does not duplicate data.
15. Generated page uses the required light theme.

## L. Implementation scope
Implement only in Harness 04-owned areas, expected:
- `core/reporting/public_report.py`
- `scripts/publish_validation_report.py`
- `tests/test_public_report.py`
- generated `docs/index.html`

If a Harness 03 change appears necessary, STOP:
`IMPLEMENTATION: BLOCKED`
`BLOCKER: HARNESS 03 CHANGE REQUIRED`

After tests pass, generate `docs/index.html` once from the current ledger. Do not run Harness 03, contact Azure, mass-sync bugs, or alter lifecycle state.

## M. Completion output
Return only:

IMPLEMENTATION: PASS / PARTIAL / BLOCKED
HARNESS: HARNESS 04
SOURCE LEDGER: PASS / FAIL
6-COLUMN COMPATIBILITY: PASS / FAIL
7-COLUMN OWNER COMPATIBILITY: PASS / FAIL
OWNER PRIVACY: PASS / FAIL
PUBLIC MODEL: PASS / FAIL
SUMMARY VALIDATION: PASS / FAIL
UNIQUE BUG ROWS: PASS / FAIL
STATUS FIDELITY: PASS / FAIL
RETEST FIDELITY: PASS / FAIL
LATEST UPDATE: PASS / FAIL
LIFECYCLE TIMESTAMP: PASS / FAIL
HTML GENERATION: PASS / FAIL
LIGHT THEME: PASS / FAIL
SEARCH: PASS / FAIL
STATUS FILTER: PASS / FAIL
FEATURE FILTER: PASS / FAIL
SEVERITY FILTER: PASS / FAIL
SANITIZATION: PASS / FAIL
PRIVATE DATA SCAN: PASS / FAIL
SOURCE IMMUTABILITY: PASS / FAIL
H03 FILES MODIFIED: NO
AZURE CONTACTED: NO
AZURE MUTATIONS: 0
LEDGER MUTATIONS: 0
SQLITE MUTATIONS: 0
LOCAL REPORT: <path or NOT_GENERATED>
PUBLICATION: NOT PERFORMED
FILES CHANGED:
<list>
BLOCKER: <reason or NONE>

STOP.

Do not configure GitHub Pages or publish externally until the generated HTML has been manually reviewed.
