# PHASE 07C-00C1 - Resource File Storage Primitives

Date: 2026-08-31

## Objective

Implement server-side storage primitives for file-backed resources without changing the UI or the contribution submission flow.

## Implementation Plan

1. Add a shared server helper that validates file inputs, maps MIME types to safe extensions, computes `content_sha256`, and builds deterministic storage keys.
2. Extend both storage backends with `saveResourceFile(input)` and `getResourceFile(resourceId)`.
3. Enforce the domain errors required by the phase brief.
4. Keep the GitHub path deterministic and server-controlled.
5. Preserve exact bytes in memory storage and verify integrity on read.
6. Add tests for happy path, size mismatch, unsupported MIME type, idempotency, conflict, integrity failure, and not-found behavior.

## What Was Implemented

- Added the shared resource file helper module in [src/server/storage/resourceFiles.js](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/resourceFiles.js).
- Added the new resource file error classes in [src/server/storage/errors.js](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/errors.js).
- Extended GitHub-backed storage with file save and retrieval support in [src/server/storage/githubInvestigationStore.js](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/githubInvestigationStore.js).
- Extended in-memory storage with the same contract in [src/server/storage/memoryInvestigationStore.js](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/memoryInvestigationStore.js).
- Re-exported the new storage primitives from [src/server/storage/index.js](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/index.js).
- Added persistence coverage in [tests/persistence.test.mjs](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/tests/persistence.test.mjs).

## Evidence

- The helper validates supported MIME types, enforces size limits, and computes the SHA-256 hash from actual bytes in [src/server/storage/resourceFiles.js](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/resourceFiles.js:97).
- The GitHub store writes to deterministic paths under `data/resource-files/<resource-id>/` and reads back with integrity checks in [src/server/storage/githubInvestigationStore.js](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/githubInvestigationStore.js:381).
- The memory store stores and returns exact bytes, and rejects conflicting content for the same `resource_id` in [src/server/storage/memoryInvestigationStore.js](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/memoryInvestigationStore.js:150).
- The storage barrel now exposes the new helpers and error types in [src/server/storage/index.js](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/index.js:5).
- The test suite covers:
  - in-memory save/retrieve success in [tests/persistence.test.mjs](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/tests/persistence.test.mjs:329)
  - size mismatch rejection in [tests/persistence.test.mjs](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/tests/persistence.test.mjs:352)
  - unsupported MIME rejection in [tests/persistence.test.mjs](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/tests/persistence.test.mjs:366)
  - idempotency and conflict behavior in [tests/persistence.test.mjs](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/tests/persistence.test.mjs:380)
  - integrity and not-found behavior in [tests/persistence.test.mjs](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/tests/persistence.test.mjs:412)
  - GitHub-backed deterministic path round-trip in [tests/persistence.test.mjs](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/tests/persistence.test.mjs:434)

## Validation

- `npm run build` passed.
- `npm test` passed.

## Notes For The Next Phase

- This phase only adds storage primitives.
- No UI wiring was added.
- No contribution API changes were made.
- The next phase can now attach file upload plumbing to these server-side primitives without changing the storage contract.
