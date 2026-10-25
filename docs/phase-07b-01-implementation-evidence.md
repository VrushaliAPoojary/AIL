# PHASE-07B-01 Implementation Evidence

Date: 2026-08-31

This note records exactly what was requested in the contributor identity hardening phase and what was implemented in the repository, with evidence from the codebase and validation steps.

## What Was Requested

The requested architecture and behavior were:

- Verified email -> normalized email -> server-side HMAC identity key -> unique email index -> existing contributor or new contributor -> signed HttpOnly session
- Server-generated contributor IDs
- Email normalization without provider-specific assumptions
- `email_key = HMAC-SHA256(IDENTITY_PEPPER, normalized_email)`
- Server-only `IDENTITY_PEPPER`
- Contributor records under `data/contributors/<contributor-id>.json`
- Unique email index under `data/indexes/contributors/by-email/<email-key>.json`
- Deduplicate contributors by verified email
- Support `Idempotency-Key` on `POST /api/contributors`
- Replace localStorage identity with a signed HttpOnly session
- Add `GET /api/me`
- Add `POST /api/session/logout`
- Do not let the browser supply authoritative persisted contributor identity
- Do not store raw email unless strictly necessary
- Separate resources from contributions
- Add resource fingerprint indexing

## What Was Implemented

### Server identity and session hardening

- Added server-side identity helpers for:
  - email normalization
  - HMAC identity key generation
  - server-generated ULID-style record IDs
  - resource fingerprint generation
- Added signed HttpOnly session helpers.
- Added email verification challenge handling so signup requires verified ownership first.

### Storage and persistence layout

- Contributor records now persist as:
  - `data/contributors/<contributor-id>.json`
- Email identity uniqueness now persists as:
  - `data/indexes/contributors/by-email/<email-key>.json`
- Resource deduplication now persists as:
  - `data/resources/<resource-id>.json`
  - `data/indexes/resources/by-fingerprint/<hash>.json`
- Contribution records remain separate from resource records.

### API changes

- `POST /api/contributors`
  - now requires verified email ownership
  - now uses server-side identity and session creation
  - now supports idempotency
- `GET /api/me`
  - restores the current contributor from the signed session
- `POST /api/session/logout`
  - clears the server session
- `GET /api/health`
  - confirms server-capable deployment behavior

### Browser flow changes

- Onboarding no longer relies on localStorage for authoritative contributor identity.
- Onboarding now creates a verified contributor on the server and then redirects to `/contribute`.
- Contribute flow now restores identity from the signed session.
- Contributor identity and contribution submission no longer depend on browser-supplied authoritative contributor IDs.

### Environment safety

- Added `.env.example` placeholders for server-only secrets:
  - `IDENTITY_PEPPER=`
  - `SESSION_SECRET=`
  - `GITHUB_TOKEN=`
  - `GITHUB_OWNER=`
  - `GITHUB_DATA_REPO=`
  - `GITHUB_BRANCH=main`
- No `NEXT_PUBLIC_` prefix is used for these secrets.

## Evidence

### Code evidence

- [Server identity helpers](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/auth/identity.js)
- [Signed session helpers](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/auth/session.js)
- [Verification flow helpers](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/auth/verification.js)
- [Contributor service](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/contributionService.js)
- [GitHub-backed store](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/githubInvestigationStore.js)
- [In-memory store](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/memoryInvestigationStore.js)
- [Validation helpers](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/validation.js)
- [Email verification route](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/app/api/email-verification/route.ts)
- [Contributor API route](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/app/api/contributors/route.ts)
- [Me API route](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/app/api/me/route.ts)
- [Logout API route](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/app/api/session/logout/route.ts)
- [Onboarding flow](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/features/onboarding/OnboardingFlow.tsx)
- [Contribute flow](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/features/contribute/ContributeFlow.tsx)
- [.env.example](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/.env.example)

### Validation evidence

- `npm run test` passed.
- `npm run build` passed.
- Production server responded successfully to `GET /api/health` with:
  - `{"status":"ok","service":"ail"}`
- Server routes for `/`, `/onboarding`, and `/contribute` returned successful responses during runtime validation.

## Current Status

- Request implemented: yes
- Server-capable Next deployment: yes
- GitHub persistence groundwork: yes
- Browser validation screenshots: not recorded in this note
- GitHub-backed contributor/contribution persistence: not started in this phase

## Notes

- This note intentionally documents only the contributor identity hardening and persistence foundation work.
- It does not introduce GitHub-backed contributor/contribution persistence beyond the requested groundwork.

