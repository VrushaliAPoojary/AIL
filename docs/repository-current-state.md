# Repository Current State

Last updated: 2026-08-31

## What this repository does

ART Investigation Lab is a Next.js application for presenting and exploring structured investigation briefs.
It renders investigation data from repository JSON files into five main product surfaces:

- Homepage (`/`)
- Onboarding (`/onboarding`)
- Contribute (`/contribute`)
- Walkthrough (`/walkthrough`)
- Workflow (`/workflow`)

## Major architecture

- `src/app/` defines the Next.js App Router routes (`layout.tsx`, `page.tsx`, `onboarding/page.tsx`, `contribute/page.tsx`, `walkthrough/page.tsx`, `workflow/page.tsx`, and API route handlers under `src/app/api/`).
- `src/components/Header/` contains the global header shell.
- `src/features/home/` contains the landing page.
- `src/features/onboarding/` contains the onboarding flow.
- `src/features/contribute/` contains the contribution flow.
- `src/features/core/walkthrough/` contains the walkthrough experience, including Markdown rendering and presentation helpers.
- `src/features/core/workflow/` contains the workflow canvas.
- `src/features/aoi/` contains the AOI explorer surface.
- `src/data/` contains the InvestigationBrief loader, validator, and repository data.
- `src/server/` contains server-only persistence, validation, and API helpers.
- `src/types/` contains the TypeScript types for the app data models.
- `contracts/` contains the locked schema and contract documents.
- `deployment/` contains legacy static deployment assets and packaging material.

## Important data flows

1. InvestigationBrief JSON files are stored under `src/data/investigations/industries/...`.
2. `src/data/investigationBriefLoader.ts` loads the JSON files.
3. `src/data/investigationBriefValidator.ts` validates the loaded JSON against the InvestigationBrief shape.
4. Next.js routes render the validated briefs in the homepage, onboarding, contribute, walkthrough, and workflow views.
5. The production build now targets the normal Next.js server runtime, while `out/` and `standalone.html` remain legacy static deployment artifacts.
6. Contributor and contribution persistence now flows through server API routes and a storage abstraction that can target a private GitHub repository.

## Source-of-truth boundaries

- InvestigationBrief JSON files in `src/data/investigations/` are the working source of truth for the UI.
- `contracts/AIL-INVESTIGATION-BRIEF-JSON-SCHEMA-V1.json` is the schema contract.
- `contracts/AIL-INVESTIGATION-BRIEF-CONTRACT-V1.md` and `contracts/INVESTIGATION-BRIEF-COMPILER-CONTRACT-V1.md` describe the locked contract expectations.
- Presentation code must not invent missing research meaning, provenance, or decision states.
- Legacy static packaging files are no longer authoritative for production runtime decisions.
- GitHub persistence is an MVP storage layer behind `InvestigationStore`, not a replacement for the locked research data model.

## Important directories

- `src/` — application code, App Router, data loading, validation, server storage, and UI features
- `src/data/investigations/` — investigation JSON inputs used by the UI
- `contracts/` — schema and contract documentation
- `deployment/` — deployable static assets and packaging files, retained as legacy material
- `public/` — browser-served static files
- `tests/` — repository tests, where present
- `scripts/` — build and validation helpers, including legacy static packaging scripts and persistence verification helpers

## Build and test state

- The repository is a Next.js (App Router) + TypeScript app with a server-capable production runtime.
- `npm run build` runs `next build`.
- `npm run start` runs the standard Next.js production server.
- `npm run build:standalone` remains available as a legacy static packaging helper.
- `npm run aoi:validate` validates AOI integrity.
- `npm run test` runs the repository's focused persistence tests.

## Known limitations

- The repository keeps product data and presentation code separate, but the UI still depends on the local JSON data being valid.
- The app is intentionally data-driven, so missing or malformed InvestigationBrief JSON will fail validation rather than being silently repaired.
- GitHub-backed persistence is an MVP durability layer and is not a substitute for relational storage or realtime collaboration.
- Legacy static export artifacts may still exist in the repository, but they are not the authoritative production runtime for the server-capable deployment.
