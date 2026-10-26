# Development Trace — P02 Delivery Control Center

## Request

Build a functional, read-only P02 supplier delivery application in the existing repository, using the ART JavaScript ADK only through verified API capabilities and preserving the distinction between specification, demo, and live validation.

## Discovery

- The repository is a Next.js 16 and TypeScript app; its old README described a Vite starter and was stale.
- Existing server routes, passkey contributor authentication, and GitHub persistence exist, but there is no configured ART agent, ART environment, ERPNext credential, or P02 tool schema in the checkout.
- P02 research describes lookup tools and an October 12 read-only smoke test, but that is not a validated P02 end-to-end run or an exhaustive receipt-link contract.
- The published ADK documents `agent(id).connect()`, `thread.run(...)`, and `run.done()`. The official package was installed at `@arealtimetech/adk-js` 0.0.25.

## Implementation choices

- Added an isolated `/delivery` route instead of replacing the existing investigation homepage.
- Added a server-only integration boundary. Live execution requires explicit ART environment configuration and an administrator session.
- Defined a strict normalized evidence contract requiring PO item row identifiers, receipt item row identifiers, exact links, submitted receipt status, and explicit receipt-set completeness.
- Kept status calculation deterministic and separate from the UI. Unknown quantities, incomplete receipt evidence, or conflicting dates do not produce a verified delivery state.
- Added an explicit configurable contractual-date versus supplier-promise-date policy. No source date is overwritten.
- Used local JSON persistence to avoid adding a database dependency; documented its single-instance limit.
- Kept supplier messages, ERPNext writes, ASN creation, scheduling, and live benchmark execution out of scope for this initial read-only implementation.

## Verification and unresolved work

See [`P02-DELIVERY-CONTROL-CENTER.md`](../P02-DELIVERY-CONTROL-CENTER.md) for the test and build results. The ADK integration has mocked-boundary tests only; actual ART authentication, configured agent response shape, ERPNext response coverage, and DELIVERY-001 remain unverified until the relevant project configuration and authorized test environment are available.

## Readiness remediation follow-up

- Inspected the installed `@arealtimetech/adk-js` 0.0.25 README and bundled source map. The documented call is `await thread.run(input)` followed by `await run.done()`; the bundled `AgentThread.run` implementation is `async`. The package root declaration re-exports `AgentThread` from `js-adk-common`, but that declaration dependency is not installed in this checkout.
- Fixed the invocation to await `thread.run()` and added tests through `executeAgentRun` for promise resolution order and rejection propagation.
- Replaced `receiptEvidenceComplete` with scoped receipt retrieval evidence. Exact PO and PO-item scope, positive page count, explicit completion, and `hasMore: false` are required to calculate quantities. Source tool/response IDs are retained only if returned. Missing evidence becomes `NEEDS VERIFICATION`.
- Replaced the `live` configuration mode with `configured`; readiness is exposed separately as `DEMO`, `CONFIGURED`, `CONNECTING`, `CONNECTED`, `VALIDATED`, or `FAILED`. `VALIDATED` means the report passed the application normalizer; it does not establish independent ERPNext provenance.
- Sanitized failed-run details returned to clients. Raw credentials and SDK error text are not placed in readiness status or public run records.
- No ART credentials, P02 agent ID, ART tool schemas, or source pagination guarantees are present in this environment. No live run was attempted. The P02 catalog describes lookup tool names only; it does not contain machine-readable input/output schemas and notes receipt lists can be limited.
