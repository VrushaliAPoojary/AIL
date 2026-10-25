# Phase 07C-00A Resource Pipeline Audit

Date: 2026-08-31

This note is audit-only. It documents the current AIL contribution/resource persistence implementation and establishes the exact starting point for the future ART processing pipeline.

No new functionality is implemented here.

## 1. Audit Scope

Read and inspected:

- `AGENTS.md`
- [`docs/architecture/phase-07b-implementation-and-endpoints.md`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/docs/architecture/phase-07b-implementation-and-endpoints.md)
- [`src/features/contribute/ContributeFlow.tsx`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/features/contribute/ContributeFlow.tsx)
- [`src/server/contributionService.js`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/contributionService.js)
- [`src/server/storage/index.js`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/index.js)
- [`src/server/storage/githubInvestigationStore.js`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/githubInvestigationStore.js)
- [`src/server/storage/memoryInvestigationStore.js`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/memoryInvestigationStore.js)
- [`src/server/storage/validation.js`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/validation.js)
- [`src/server/auth/identity.js`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/auth/identity.js)
- [`src/app/api/contributions/route.ts`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/app/api/contributions/route.ts)
- [`src/app/api/contributions/[id]/route.ts`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/app/api/contributions/[id]/route.ts)
- [`src/app/api/contributors/route.ts`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/app/api/contributors/route.ts)

## 2. Current Resource Implementation

### Resource identity

Yes, a Resource already has:

- resource ID
- fingerprint
- type
- canonical URL or text payload
- created_at
- updated_at

No, a Resource does not currently have:

- created_by

Evidence:

- Resource IDs come from `createResourceId()` in [`src/server/auth/identity.js`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/auth/identity.js)
- Fingerprints come from `createResourceFingerprint()` in the same file
- Resources are created in `resolveResourceRecord()` in [`src/server/contributionService.js`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/contributionService.js)

### Resource persistence

Current storage path:

- `data/resources/<resource-id>.json`

Current fingerprint index path:

- `data/indexes/resources/by-fingerprint/<hash>.json`

Behavior:

- same normalized resource payload
  - same fingerprint
  - same Resource ID is reused if already stored
- different contributor
  - different Contribution ID
  - may still point to the same Resource ID

Evidence:

- `resolveResourceRecord()` in [`src/server/contributionService.js`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/contributionService.js)
- `createResource()` and `createResourceFingerprintIndex()` in [`src/server/storage/githubInvestigationStore.js`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/githubInvestigationStore.js)
- `createResource()` and `createResourceFingerprintIndex()` in [`src/server/storage/memoryInvestigationStore.js`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/memoryInvestigationStore.js)

## 3. What Is Actually Persisted By Type

Current accepted contribution types are:

- `LINK`
- `TEXT`
- `FILE`
- `INSIGHT`

The current implementation does **not** define separate persisted types for `MARKDOWN`, `TXT`, `PDF`, `IMAGE`, or `VIDEO`.

Those are handled as file inputs or file-like content inside the existing `FILE` contribution mode, but the server persists only metadata for them.

### Persistence matrix

| Type | Metadata | Actual content | ART-ready? |
| --- | --- | --- | --- |
| LINK | YES | PARTIAL | PARTIAL |
| TEXT | YES | YES | PARTIAL |
| KEY INSIGHT / INSIGHT | YES | YES | PARTIAL |
| MARKDOWN | YES | NO | NO |
| TXT | YES | NO | NO |
| PDF | YES | NO | NO |
| IMAGE | YES | NO | NO |
| VIDEO | YES | NO | NO |

Clarification:

- `LINK` stores a canonical URL in the resource payload.
- `TEXT` and `INSIGHT` store text in the resource payload.
- `FILE` stores file metadata only:
  - file name
  - MIME type if provided
  - size
- The server does **not** persist binary file content.
- The server does **not** currently extract PDF, image, video, markdown, or text file contents.

Evidence:

- Validation rules in [`src/server/storage/validation.js`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/validation.js)
- Canonical payload normalization in [`src/server/auth/identity.js`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/auth/identity.js)
- Contribution resource resolution in [`src/server/contributionService.js`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/contributionService.js)
- File mode UI in [`src/features/contribute/ContributeFlow.tsx`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/features/contribute/ContributeFlow.tsx)

## 4. File Handling Audit

For file contributions:

- Is binary content transmitted to server? `NO`
- Is it persisted anywhere? `NO`
- Is only metadata persisted? `YES`
- Is there a storage key/reference? `NO`
- Is maximum file size enforced? `YES`
- Is MIME type validated? `PARTIAL`
- Can the server later retrieve the exact submitted file? `NO`

Details:

- The client accepts file input in the UI.
- The submit request only sends `type`, `resource.file.name`, `resource.file.mime_type`, and `resource.file.size`.
- There is no binary upload endpoint and no blob/object storage integration.
- The server therefore cannot reconstruct the exact file later.

Evidence:

- UI file drop area in [`src/features/contribute/ContributeFlow.tsx`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/features/contribute/ContributeFlow.tsx)
- Validation for `resource.file.name`, `resource.file.mime_type`, and `resource.file.size` in [`src/server/storage/validation.js`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/validation.js)
- No binary upload path appears in the current contribution routes.

## 5. Current Contribution Model

The persisted contribution record currently contains:

- `id`
- `contributor_id`
- `contributor_name`
- `resource_id`
- `type`
- `context` when provided
- `status`
- `created_at`
- `updated_at`

Current status model:

- persisted status: `RECEIVED`
- no persisted resource processing statuses yet

Activity event emitted on successful save:

- `CONTRIBUTION_CREATED`

Evidence:

- [`createContributionRecord()`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/contributionService.js)
- [`src/app/api/contributions/route.ts`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/app/api/contributions/route.ts)

## 6. Storage Interface Audit

### Existing methods related to contributors

Memory store:

- `createContributor`
- `getContributor`
- `createContributorEmailIndex`
- `getContributorEmailIndex`
- `getContributorByEmailKey`
- `createContributorIdempotencyIndex`
- `getContributorIdempotencyIndex`

GitHub store:

- same contributor methods, backed by GitHub content files

### Existing methods related to contributions

Memory store:

- `createContribution`
- `getContribution`
- `listContributions`
- `deleteContribution`

GitHub store:

- same contribution methods, backed by GitHub content files

### Existing methods related to resources and indexes

Memory store:

- `createResource`
- `getResource`
- `createResourceFingerprintIndex`
- `getResourceFingerprintIndex`
- `getResourceByFingerprint`

GitHub store:

- same resource methods, backed by GitHub content files

### Existing methods related to activity

Memory store:

- `createActivity`
- `getActivity`

GitHub store:

- `createActivity`

### Missing methods for the future processing pipeline

Not currently present:

- processing job creation
- processing job update
- processing job retrieval
- analysis job queueing
- agent payload persistence

That means the ART processing pipeline still has to be introduced as a new server-side layer.

## 7. API Response Audit

### `POST /api/contributions`

Current behavior:

- requires a valid signed session
- validates the request body
- resolves or creates a Resource
- creates a Contribution
- creates an Activity event
- returns the contribution JSON only

Current response:

- `201 Created`
- JSON contribution record

Not currently returned:

- resource object
- resource ID separately
- dedupe metadata
- activity event

Evidence:

- [`src/app/api/contributions/route.ts`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/app/api/contributions/route.ts)
- [`createContributionRecord()`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/contributionService.js)

### `GET /api/contributions`

Current behavior:

- returns `{ contributions }`
- each contribution is hydrated with its resource, if available

### `GET /api/contributions/[id]`

Current behavior:

- returns one hydrated contribution record

## 8. Current Status Model

### Persisted state

Current persisted statuses found in the implementation:

- Contribution: `RECEIVED`

### Visual or UI state

The current contribution UI has loading, error, and success presentation states, but those are not persisted resource-processing states.

There is no persisted state yet for:

- ART analysing
- claims extracted
- completed processing
- compiler agent queued
- database agent queued

## 9. ART Pipeline Gaps

The current implementation is a good starting point, but it stops at contribution capture and resource deduplication.

What is missing for the future ART pipeline:

- separate persisted processing jobs
- a resource-to-processing-job handoff
- agent orchestration endpoints
- extraction output storage
- deterministic validation output storage
- investigation assembly persistence

## 10. Current Endpoints You Can Use Now

### For conducting operations

- `GET /api/me`
- `GET /api/contributions`
- `GET /api/contributions/[id]`
- `POST /api/contributions`

### For analysis

There is no dedicated analysis endpoint yet.

Use the current contribution/resource APIs as the data source:

- `GET /api/contributions`
- `GET /api/contributions/[id]`

### For sending resources into a future agent pipeline

There is no dedicated agent endpoint yet.

The next safe server-only endpoints to add would be:

- `POST /api/processing-jobs`
- `GET /api/processing-jobs/[id]`
- `POST /api/agents/extract`
- `POST /api/agents/analyze`
- `POST /api/agents/construct`

Those are not implemented yet. They are listed here as the correct future contract shape for the next build phase.

## 11. Current Starting Point For ART Processing

The current starting point is:

1. contributor session is established through server-authenticated passkey flow
2. contribution is submitted through `POST /api/contributions`
3. contribution gets normalized and persisted
4. resource gets deduplicated by fingerprint
5. activity event is written
6. response returns the contribution record

That is the exact place where the future processing pipeline should attach.

## 12. Summary

Current AIL behavior is:

- contributor/session aware
- resource deduplicated
- contribution persisted separately from resource
- file uploads handled as metadata-only contributions
- no processing jobs yet
- no analysis endpoint yet
- no agent pipeline yet

The most important audit result is this:

- AIL currently stores contribution records and resource records.
- AIL does **not** store the binary file content.
- AIL does **not** yet have the job/agent pipeline required for ART extraction, analysis, and investigation construction.

