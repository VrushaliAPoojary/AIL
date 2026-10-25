# Phase 07B Implementation and Endpoint Map

Date: 2026-08-31

This note records, in plain terms, what was requested across the Phase 07B work, what was actually implemented in the repository, and where the current API entry points live for resource capture, analysis, and agent handoff.

## 1. What Was Requested

Across the Phase 07B prompts, the requested work was:

- Remove static-export-only deployment and make the app server-capable.
- Add server routes and server-only environment support.
- Preserve the homepage, onboarding, contribute, and investigation routes.
- Add a health endpoint.
- Harden contributor identity and session handling.
- Move from email-verification-based contributor auth to passkey-first auth.
- Remove flicker by resolving contributor session state on the server.
- Update the contribution UI so file contributions feel like a Dropbox-style drop area.
- Keep GitHub-backed persistence behind server-side APIs only.
- Document the implementation and the exact endpoints to use next.

## 2. What Was Built

### Server-capable Next deployment

- Removed the static export blocker from the Next configuration.
- Kept the app on the normal Next.js production runtime.
- Confirmed server routes now exist and build in production mode.

Evidence:

- [`next.config.mjs`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/next.config.mjs)
- `npm run build` passes.
- `npm run start` runs the Next production server.

### Session-aware routing without flicker

- Added a canonical server-resolved entry route:
  - `/start-contributing`
- Homepage CTA and header CTA now point to `/start-contributing`.
- `/start-contributing` resolves the signed session on the server and redirects:
  - authenticated contributor -> `/contribute`
  - unauthenticated user -> `/onboarding`
- `/contribute` now checks the signed session on the server before rendering.
- `/onboarding` now redirects authenticated contributors back to `/contribute` before rendering.

Evidence:

- [`src/app/start-contributing/page.tsx`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/app/start-contributing/page.tsx)
- [`src/app/contribute/page.tsx`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/app/contribute/page.tsx)
- [`src/app/onboarding/page.tsx`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/app/onboarding/page.tsx)
- [`src/server/auth/session-route.js`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/auth/session-route.js)
- [`src/features/home/Homepage.tsx`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/features/home/Homepage.tsx)
- [`src/components/Header/Header.tsx`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/components/Header/Header.tsx)

### Passkey-first contributor authentication

- New users create a passkey profile during onboarding.
- Returning users authenticate with a passkey and the server restores the contributor session.
- Contributor identity is stored server-side and the browser does not own the durable identity.
- Signed HttpOnly session cookies are used for auth state.

Evidence:

- [`src/features/onboarding/OnboardingFlow.tsx`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/features/onboarding/OnboardingFlow.tsx)
- [`src/app/api/passkeys/registration/options/route.ts`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/app/api/passkeys/registration/options/route.ts)
- [`src/app/api/passkeys/authentication/options/route.ts`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/app/api/passkeys/authentication/options/route.ts)
- [`src/app/api/passkeys/authentication/verify/route.ts`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/app/api/passkeys/authentication/verify/route.ts)
- [`src/app/api/contributors/route.ts`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/app/api/contributors/route.ts)
- [`src/server/auth/webauthn.js`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/auth/webauthn.js)
- [`src/server/auth/session.js`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/auth/session.js)

### Server-only storage and identity foundation

- Contributor IDs are server-generated.
- Sessions are signed on the server and stored in HttpOnly cookies.
- The storage layer supports GitHub-backed persistence and in-memory testing.
- `GET /api/me` restores the authenticated contributor from the server session.
- `POST /api/session/logout` clears the session.
- `GET /api/health` proves the server runtime is active.

Evidence:

- [`src/server/contributionService.js`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/contributionService.js)
- [`src/server/storage/index.js`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/index.js)
- [`src/server/storage/githubInvestigationStore.js`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/githubInvestigationStore.js)
- [`src/server/storage/memoryInvestigationStore.js`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/server/storage/memoryInvestigationStore.js)
- [`src/app/api/me/route.ts`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/app/api/me/route.ts)
- [`src/app/api/session/logout/route.ts`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/app/api/session/logout/route.ts)
- [`src/app/api/health/route.ts`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/app/api/health/route.ts)

### Contribution UI update

- File contributions now use a Dropbox-style drop area.
- The file mode accepts:
  - `jpg`
  - `jpeg`
  - `png`
  - `gif`
  - `webp`
  - `pdf`
  - `md`
  - `markdown`
  - `txt`
- The other modes remain available as:
  - `Link`
  - `Key insights`
- The UI still stores file metadata in the current MVP instead of binary uploads.

Evidence:

- [`src/features/contribute/ContributeFlow.tsx`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/features/contribute/ContributeFlow.tsx)
- [`src/features/persistence/Persistence.css`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/src/features/persistence/Persistence.css)

## 3. Validation Evidence

### Build and runtime

- `npm run build` passed after the routing and UI changes.
- `npm run start` was used to validate the production server behavior.
- The route map now includes:
  - `/start-contributing`
  - `/contribute`
  - `/onboarding`
  - `/api/me`
  - `/api/session/logout`
  - `/api/health`
  - passkey API routes

### Browser validation artifacts

Captured screenshots:

- [`artifacts/ui-validation/phase-07b-01b/01-home-server-mode.png`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/artifacts/ui-validation/phase-07b-01b/01-home-server-mode.png)
- [`artifacts/ui-validation/phase-07b-01b/02-onboarding-server-mode.png`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/artifacts/ui-validation/phase-07b-01b/02-onboarding-server-mode.png)
- [`artifacts/ui-validation/phase-07b-01b/03-contribute-server-mode.png`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/artifacts/ui-validation/phase-07b-01b/03-contribute-server-mode.png)
- [`artifacts/ui-validation/phase-07b-01b/02-onboarding-server-mode-mobile.png`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/artifacts/ui-validation/phase-07b-01b/02-onboarding-server-mode-mobile.png)
- [`artifacts/ui-validation/phase-07b-01b/03-contribute-server-mode-mobile.png`](/home/chiranjeevi/Documents/art-investigation-lab(AIL)/artifacts/ui-validation/phase-07b-01b/03-contribute-server-mode-mobile.png)

The validation script also confirmed:

- authenticated contributor session restoration
- resource deduplication by fingerprint
- same resource ID reused across submissions

## 4. Current API Map

This is the current server contract you can build against.

### Auth and session

- `POST /api/passkeys/registration/options`
  - Starts passkey registration.
  - Returns registration options.
- `POST /api/contributors`
  - Finalizes new contributor creation after successful passkey registration.
  - Sets the signed HttpOnly session.
- `POST /api/passkeys/authentication/options`
  - Starts passkey sign-in for returning contributors.
- `POST /api/passkeys/authentication/verify`
  - Verifies passkey sign-in and restores the contributor session.
- `GET /api/me`
  - Returns the current contributor from the signed session.
- `POST /api/session/logout`
  - Clears the session.
- `GET /api/health`
  - Health check for the server runtime.

### Contribution data

- `GET /api/contributions`
  - Lists recent contributions.
- `POST /api/contributions`
  - Creates a contribution using the current authenticated contributor.
- `GET /api/contributions/[id]`
  - Fetches a single contribution.

### Contributor data

- `GET /api/contributors/[id]`
  - Fetches a contributor record by ID.

## 5. Where To Read Resources For The Next Build

You asked for the exact endpoint details to continue the build. The current split is:

### A. Resources for conducting operations

Use the contribution APIs:

- `GET /api/contributions`
  - Use this to read existing contribution records.
  - Best for listing what has already been captured.
- `GET /api/contributions/[id]`
  - Use this to inspect one contribution in detail.
- `POST /api/contributions`
  - Use this to create a new contribution from the authenticated session.

If your next step is “what does the current contributor see and submit?”, start here:

1. `GET /api/me`
2. `GET /api/contributions`
3. `POST /api/contributions`

### B. Resources for analysis

There is not yet a dedicated analysis endpoint in the current implementation.

At the moment, analysis should be driven from the stored contribution records and the investigation data already served by the app:

- contribution records: `GET /api/contributions`
- individual contributions: `GET /api/contributions/[id]`
- investigation UI/data surfaces: homepage, walkthrough, workflow, and the investigation JSON-backed surfaces already in the app

If you want a clean future endpoint for analysis, the next safe addition would be a server-only route such as:

- `GET /api/analysis`
- `POST /api/analysis`

but that is not implemented yet.

### C. Resources to send to an agent for extraction, analysis, and construction

There is not yet a dedicated agent endpoint in the current codebase.

For the next build phase, the clean contract would be:

- input: contribution IDs, resource IDs, or investigation brief IDs
- server fetches the data from the current APIs or storage layer
- server sends structured payloads to the agent pipeline

Recommended future endpoint shapes:

- `POST /api/agents/extract`
- `POST /api/agents/analyze`
- `POST /api/agents/construct`

These are not built yet, but they are the safest endpoints to add next because they keep the browser out of the trusted data path.

## 6. What Is Still True And What Is Not

### Current truth

- The app is server-capable.
- Contributor identity is server-authenticated.
- The browser should not be treated as authoritative for contributor identity.
- File contributions are now presented as a Dropbox-style drop area.

### Not yet built

- Dedicated analysis endpoints.
- Dedicated agent extraction/analysis/construction endpoints.
- Realtime collaboration.
- ART agents.
- Any client-side direct GitHub access.

## 7. Short Build Summary

The repository now has:

- server-capable Next deployment
- zero-flicker session-aware routing
- passkey-first contributor authentication
- Dropbox-style file contribution UI
- server-backed session restoration
- documented screenshot evidence
- a clear API surface for contributions and future analysis/agent work

