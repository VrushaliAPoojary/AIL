# Server-Capable Next Deployment

## Previous state

ART Investigation Lab previously ran as a static export.
The production build was tied to `output: 'export'`, and legacy packaging artifacts such as `out/` and `standalone.html` were treated as deployment outputs.

## Current state

AIL now uses a server-capable Next.js production deployment.
The app keeps the existing App Router pages and adds server route capability through the normal Next runtime.

## Why this matters

This change enables the next persistence phase to place GitHub credentials on the server side only.
The browser can talk to application API routes, and those routes can then talk to GitHub without exposing tokens to client code.

Target flow:

```text
Frontend
↓
Server API
↓
GitHub persistence layer
↓
Private data repository
```

## Safety boundary

The browser must never receive GitHub credentials.
Any future `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_DATA_REPO`, and `GITHUB_BRANCH` values belong in server-only environment variables.

## Legacy artifacts

The following remain in the repository as legacy static deployment material:

- `out/`
- `standalone.html`
- `scripts/make_standalone.py`

They are retained for historical reference and packaging compatibility, but they are not the authoritative production runtime for this deployment mode.
