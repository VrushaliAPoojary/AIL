# P02 Delivery Control Center: implementation and verification

**Date:** 2026-10-25  
**Route:** `/delivery`  
**Process:** `P02-SUPPLIER-DELIVERY`

## Scope delivered

- Added a procurement control-center route for overview, purchase orders, delivery exceptions, automation runs, workflow/evidence states, and configuration.
- Added server-side administrator sign-in with an expiring signed HTTP-only cookie. Live data, run, and configuration endpoints require that session.
- Integrated the documented `@arealtimetech/adk-js` agent/thread API behind a server-only service. A run is successful only after `run.done()` returns a final report that passes the P02 evidence contract.
- Added request idempotency, single-process overlap protection, timeout handling, interrupted-run recovery, and local run/configuration/audit persistence.
- Added deterministic delivery classification using exact purchase-order-item receipt links. Cancelled and draft receipts are excluded, receipt rows are not double-counted, returns reduce received quantity, and incomplete/conflicting evidence becomes `NEEDS_VERIFICATION`.
- Added a configurable due-date basis: contractual item schedule date or supplier expected delivery date. Both fields remain distinct and are never written back.
- Added clearly labeled synthetic demonstration records. They are generated relative to the configured local business date and are not displayed as live results.
- Runtime readiness now distinguishes `DEMO`, `CONFIGURED`, `CONNECTING`, `CONNECTED`, `VALIDATED`, and `FAILED`. `VALIDATED` means the response passed the app contract, not that ART tools or ERPNext were independently verified.
- Receipt quantities require evidence scoped to exact PO and PO-item IDs, explicit completeness, at least one retrieved page, and `hasMore: false`. Missing scope or pagination evidence leaves quantities at `NEEDS VERIFICATION`; optional source tool/response identifiers are preserved when supplied.
- Failed run details exposed to clients are reduced to a generic message; readiness exposes only safe failure categories.

## Important boundaries

- The repository does not contain ART project credentials, the actual P02 agent ID, ART tool JSON schemas, or source guarantees for receipt pagination/completeness. The actual ART project and ERPNext tools could not be inspected from this checkout.
- ART/ERPNext live execution is therefore **not verified**. Tool outputs must establish retrieval scope and exhausted pagination; agent-asserted completeness without that evidence does not verify quantities.
- Existing P02 tools are described as lookup tools; supplier email/PDF ingestion, autonomous communication, ERPNext writes, ASN processing, alternate sourcing, and recurring scheduling are not implemented.
- `DELIVERY-001` remains a synthetic specification and has not been executed.
- `.data/p02-delivery/history.json` is local single-instance persistence. It is not suitable for multiple application instances without shared storage.

## Verification record

- `npm test`: passed, 57 tests (27 existing persistence tests and 30 P02 delivery tests).
- `node node_modules/typescript/bin/tsc --noEmit`: passed.
- `git diff --check`: passed after README whitespace cleanup.
- `npm run build`: passed after running the Next.js worker outside the restricted sandbox.
- `python scripts/procurement/validate-procurement-workspace.py`: failed with 30 workspace errors because this checkout lacks the P01, P03, and P04 process directories, producing missing-file and broken-link reports. Its scope-boundary and secret-scan checks passed; no procurement research files were changed by this implementation.
- No live ART agent run, ERPNext query, or benchmark execution was performed.
- Production smoke check: `/delivery`, `/api/delivery/status`, and `/api/delivery/data` responded successfully; demo data was labeled synthetic and calculated as expected. No live run history was exposed in demo mode.

## Configuration

See the root [`README.md`](../README.md) and [`.env.example`](../.env.example). Keep all actual credentials in a local ignored environment file or secret manager. Do not commit credentials.

