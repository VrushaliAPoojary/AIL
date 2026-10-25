# PHASE 07C-00C2A — AUTHENTICATED RESOURCE FILE UPLOAD API

Date: 2026-08-31

## Objective

Provide a server-side endpoint and service layer method that accepts binary file content (`multipart/form-data`) for an existing `FILE` contribution record, validates the uploaded payload against the stored Resource metadata, and persists the payload using the `saveResourceFile` storage primitive from Phase 07C-00C1.

---

## Implementation Plan

1. **Service Layer Method**: Implement `attachFileToContributionRecord` in `src/server/contributionService.js` to handle session resolution, contribution ownership verification (`contribution.contributor_id === owner.id`), contribution type checks (`type === 'FILE'`), metadata validation (`original_name`, `mime_type`, `size`), and binary persistence invocation.
2. **HTTP Route Handler**: Create `POST /api/contributions/[id]/file` in `src/app/api/contributions/[id]/file/route.js` to parse `multipart/form-data`, extract file bytes, invoke the service method, and format safe JSON responses.
3. **Error & Status Code Mapping**: Ensure correct domain errors map to HTTP status codes (401, 403, 404, 400, 415, 413, 409, 500). Update `ResourceFileTypeUnsupportedError` status to 415 in `errors.js` and `resourceFiles.js`.
4. **Automated Test Coverage**: Write comprehensive automated unit and integration tests in `tests/persistence.test.mjs` verifying service behavior, ownership security, metadata checks, idempotency/conflict handling, and HTTP route handling.
5. **Build & Test Validation**: Run targeted tests (`npm test`) and Next.js production build (`npm run build`) to ensure 100% pass rate and compilation integrity.

---

## What Was Actually Built

- **Server Service Method**: `attachFileToContributionRecord(store, session, contributionId, uploadedFile)`
  - Authenticates contributor via session token.
  - Loads contribution and verifies ownership.
  - Verifies contribution type is `FILE`.
  - Compares uploaded file properties (`original_name`, `mime_type`, `size`) against stored Resource metadata.
  - Calls `store.saveResourceFile(...)` to compute SHA-256 and write bytes to deterministic storage paths.
  - Returns safe response payload (`resource_id`, `stored: true`, `file`).

- **API Endpoint**: `POST /api/contributions/[id]/file`
  - Accepts `multipart/form-data` requests containing `file`.
  - Converts browser `File` object to buffer bytes.
  - Resolves contribution ID from route context.
  - Handles errors gracefully via `errorResponse` helper.

- **Security & Metadata Guarantees**:
  - Contributor A cannot attach bytes to Contributor B's contribution (HTTP 403 `FORBIDDEN`).
  - Non-FILE contributions cannot receive binary attachments (HTTP 400 `CONTRIBUTION_NOT_FILE`).
  - Size or MIME mismatches are rejected (HTTP 400 / 415).
  - No secret tokens, GitHub credentials, or filesystem absolute paths are exposed in responses.
  - FILE readiness state remains `METADATA_ONLY` / `CONTENT_REQUIRED` in this phase (Requirement 17).

---

## Evidence Links to Exact Code Paths

- **Service Method Implementation**:
  [attachFileToContributionRecord in contributionService.js](file:///home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/contributionService.js#L346-L450)
- **API Endpoint Handler**:
  [POST /api/contributions/[id]/file/route.js](file:///home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/app/api/contributions/[id]/file/route.js#L9-L46)
- **Error Class Status Update (415)**:
  [ResourceFileTypeUnsupportedError in errors.js](file:///home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/errors.js#L56-L63)
  [ResourceFileTypeUnsupportedError in resourceFiles.js](file:///home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/resourceFiles.js#L56-L63)
- **Shared Memory Store Fallback**:
  [createInvestigationStore in storage/index.js](file:///home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/index.js#L56-L69)
- **Automated Test Implementations**:
  [Persistence & Upload API Tests in persistence.test.mjs](file:///home/chiranjeevi/Documents/art-investigation-lab(AIL)/tests/persistence.test.mjs#L510-L746)

---

## Test Coverage That Proves the Behavior

The test suite in [tests/persistence.test.mjs](file:///home/chiranjeevi/Documents/art-investigation-lab(AIL)/tests/persistence.test.mjs#L510-L746) covers 6 core scenarios:

1. **Successful FILE Attachment**:
   - `attachFileToContributionRecord attaches bytes to FILE contribution and leaves readiness unchanged` ([line 510](file:///home/chiranjeevi/Documents/art-investigation-lab(AIL)/tests/persistence.test.mjs#L510))
   - Proves exact bytes stored, exact bytes retrievable, safe response format, and readiness state remains `CONTENT_REQUIRED`.
2. **Unauthorized Contributor Security**:
   - `attachFileToContributionRecord rejects unauthorized contributor` ([line 549](file:///home/chiranjeevi/Documents/art-investigation-lab(AIL)/tests/persistence.test.mjs#L549))
   - Proves Contributor B cannot attach bytes to Contributor A's contribution (HTTP 403).
3. **Non-FILE Contribution Protection**:
   - `attachFileToContributionRecord rejects non-FILE contributions` ([line 573](file:///home/chiranjeevi/Documents/art-investigation-lab(AIL)/tests/persistence.test.mjs#L573))
   - Proves LINK/TEXT/INSIGHT contributions reject binary uploads (HTTP 400).
4. **Metadata Validation**:
   - `attachFileToContributionRecord validates metadata size, MIME, and filename` ([line 595](file:///home/chiranjeevi/Documents/art-investigation-lab(AIL)/tests/persistence.test.mjs#L595))
   - Proves size mismatches (400), MIME mismatches (415), and filename mismatches (400) are rejected.
5. **Idempotency & Conflict**:
   - `attachFileToContributionRecord supports same-byte retry and rejects different-byte overwrite` ([line 638](file:///home/chiranjeevi/Documents/art-investigation-lab(AIL)/tests/persistence.test.mjs#L638))
   - Proves same-byte re-upload succeeds idempotently while different-byte re-upload returns HTTP 409 Conflict.
6. **HTTP Route & Multipart Integration**:
   - `POST /api/contributions/[id]/file route behavior and error mapping` ([line 686](file:///home/chiranjeevi/Documents/art-investigation-lab(AIL)/tests/persistence.test.mjs#L686))
   - Proves unauthenticated request rejection (401), missing file field rejection (400), and end-to-end multipart form data upload.

---

## Validation Results

### `npm test`
```text
> art-investigation-lab@0.0.0 test
> node --test tests/persistence.test.mjs

✔ email normalization preserves plus addressing and dots (2.043907ms)
✔ successful new registration persists contributor and credential (3.073356ms)
✔ registration challenge replay rejected (0.887025ms)
✔ invalid origin rejected (0.274138ms)
✔ invalid challenge rejected (0.241664ms)
✔ successful returning sign-in resolves the existing contributor (0.723289ms)
✔ unknown credential rejected (0.241405ms)
✔ same credential resolves the same contributor and does not create duplicates (0.438483ms)
✔ authentication cannot create duplicate contributor (0.51647ms)
✔ tampered session rejected (0.533873ms)
✔ logout invalidates session (0.187924ms)
✔ returning contributor restores profile through the session payload (0.402625ms)
✔ resource availability and handoff readiness are derived from contribution type (2.232424ms)
✔ same resource from two contributors deduplicates the resource record (7.602506ms)
✔ resource file save and retrieve works in memory (1.491736ms)
✔ resource file save rejects size mismatch (0.575028ms)
✔ resource file save rejects unsupported mime types (0.770568ms)
✔ resource file save is idempotent for matching bytes and conflicts on different bytes (1.080056ms)
✔ resource file retrieval detects tampering and missing records (0.807784ms)
✔ github store saves and restores resource files with deterministic paths (1.882326ms)
✔ browser-authentication tokens are not stored in localStorage (3.43517ms)
✔ attachFileToContributionRecord attaches bytes to FILE contribution and leaves readiness unchanged (1.351212ms)
✔ attachFileToContributionRecord rejects unauthorized contributor (0.873241ms)
✔ attachFileToContributionRecord rejects non-FILE contributions (0.528169ms)
✔ attachFileToContributionRecord validates metadata size, MIME, and filename (0.742242ms)
✔ attachFileToContributionRecord supports same-byte retry and rejects different-byte overwrite (0.719285ms)
✔ POST /api/contributions/[id]/file route behavior and error mapping (11.21026ms)
ℹ tests 27
ℹ suites 0
ℹ pass 27
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 415.532904
```

### `npm run build`
```text
> art-investigation-lab@0.0.0 build
> next build

▲ Next.js 16.3.3 (Turbopack)
- Environments: .env.local
✓ Running next.config.mjs took 14ms

  Creating an optimized production build ...
✓ Compiled successfully in 1529ms
  Finished TypeScript in 4.5s    ✓ Finished TypeScript in 4.5s 
  Collecting page data using 7 workers in 1175ms    ✓ Collecting page data using 7 workers in 1175ms 
✓ Generating static pages using 7 workers (5/5) in 327ms
  Finalizing page optimization in 14ms    ✓ Finalizing page optimization in 14ms 

Route (app)
┌ ○ /
├ ○ /_not-found
├ ƒ /api/contributions
├ ƒ /api/contributions/[id]
├ ƒ /api/contributions/[id]/file
├ ƒ /api/contributors
├ ƒ /api/contributors/[id]
├ ƒ /api/email-verification
├ ƒ /api/health
├ ƒ /api/me
├ ƒ /api/passkeys/authentication/options
├ ƒ /api/passkeys/authentication/verify
├ ƒ /api/passkeys/registration/options
├ ƒ /api/session/logout
├ ƒ /contribute
├ ƒ /onboarding
├ ƒ /start-contributing
├ ○ /walkthrough
└ ○ /workflow
```

---

## Current Scope & Limitations

- **UI Status**: The contribution UI (`ContributeFlow`) is intentionally NOT wired to this endpoint in this phase (scheduled for Phase 07C-00C2B).
- **Resource Readiness**: The Resource state remains `METADATA_ONLY` and `CONTENT_REQUIRED` after upload in Phase 07C-00C2A. Transition to `READY` / `STORED_FILE` is deferred to Phase 07C-00C3.
- **Contribution Metadata API**: `POST /api/contributions` remains unchanged and handles metadata registration only.
