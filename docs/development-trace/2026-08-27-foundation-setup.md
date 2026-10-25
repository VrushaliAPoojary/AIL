# Development Trace — Foundation Setup

## Request

Create a durable AI-native development foundation for this repository.

## Objective

Establish a repository-level process layer based on:

PROMPT → IMPLEMENT → UNDERSTAND → HUMAN OWNERSHIP

and the working loop:

LEARN → THINK → IMPLEMENT → VERIFY → UNDERSTAND → ADAPT

## Previous state

- The repository already had a product-oriented AGENTS file.
- No dedicated AI development protocol existed.
- No dedicated current-state document existed.
- No dedicated development-trace location existed.

## Reasoning

The repository already had a clear React/Vite application, a data loader, a validator, and locked contract files.
What it lacked was a durable process layer that tells AI agents how to work without changing product semantics.

The foundation had to stay lightweight because the repository already has a strict schema and contract boundary.

## Implementation

- Added a concise current-state document.
- Added a permanent AI development protocol.
- Replaced the long AGENTS entry with a short pointer to the permanent documentation.
- Added this dated development-trace entry for future work.

## Changed files

- `docs/repository-current-state.md`
- `docs/ai-development-protocol.md`
- `docs/development-trace/2026-08-27-foundation-setup.md`
- `AGENTS.md`

## Verification

Completed verification:

- `python3 -m compileall src` succeeded
- `npm run build` succeeded
- production output was generated at `dist/index.html` with matching bundled assets under `dist/assets/`
- build reported a large-chunk warning, but the build completed successfully
- `npm run lint` is currently blocked because this repo does not have an ESLint flat config file
- `npm run aoi:validate` is currently blocked because the script requires a source argument and no normalized AOI source file is present in this repo path
- no product code, schema, or investigation JSON was changed for this foundation task

## Limitations

- This foundation does not define product behavior.
- This foundation does not modify schemas, contracts, or investigation data.
- This foundation does not add tooling, APIs, dashboards, or automation services.
- The repository still contains only one front-end application and no backend service in this scope.

## Human understanding

The human should know that this is a process foundation only.
It helps AI work consistently, but it does not lock the product into a fixed terminology or workflow.

## Human decision

The human owns all future product, research, and schema decisions.

## Adaptation

If a future task reveals a better durable practice, the trace should record the change and the protocol should be updated carefully without expanding into product policy.
