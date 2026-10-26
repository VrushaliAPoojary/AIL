# ART Investigation Lab and P02 Delivery Control Center

This repository contains the ART Investigation Lab, a Next.js application for structured investigation briefs, plus the **P02 Delivery Control Center** at `/delivery` for read-only supplier delivery monitoring.

P02 research documents specify a proposed supplier delivery workflow. They do not prove the end-to-end workflow is live. The control center keeps synthetic demonstration data, validated ART results, and unverified evidence clearly separated.

## Requirements

- Node.js 20.9 or newer
- npm

## Install and run

```bash
npm install
npm run dev
```

Open `http://localhost:3000/delivery` for the control center. Without P02 server settings, it displays explicitly labeled synthetic demonstration records. The existing investigation application remains available at `/`.

## Configure administrator access

Copy `.env.example` to `.env.local` and set unique secret values for:

- `P02_ADMIN_USERNAME`
- `P02_ADMIN_PASSWORD`
- `P02_SESSION_SECRET`

Live procurement data, manual monitoring runs, and configuration changes require administrator sign-in. The session cookie is HTTP-only, same-site strict, and secure in production. Use HTTPS in deployed environments. Do not commit `.env.local`.

## Configure the ART connection

The control center uses the official `@arealtimetech/adk-js` package from the backend. The documented agent execution path uses `adk.agent(agentId).connect()`, `agent.thread()`, `thread.run(input)`, and `run.done()`. A final result is recorded as successful only after it matches the P02 evidence contract.

Set the ART values in `.env.local` after confirming them with the actual ART project configuration:

- `ART_URI` — ART service host without a protocol prefix
- `ART_CLIENT_ID`
- `ART_CLIENT_SECRET`
- `ART_ORG_TITLE`
- `ART_ENVIRONMENT`
- `ART_PROJECT_KEY`
- `ART_AGENT_ID` — ID of the existing P02 monitoring agent

The repository does not contain these project-specific values. ERPNext data is expected to come from the configured agent’s existing read-only tools; the app does not have a direct ERPNext credential or API integration. The agent must return a JSON object with a `purchaseOrders` array. Each purchase order item must include its ERPNext row identifier, date and quantity fields, scoped receipt-retrieval evidence with pagination completeness, and linked receipt rows containing exact PO and PO-item references. If the actual tools cannot establish retrieval scope or exhausted pagination, quantity classification remains `NEEDS VERIFICATION`. An unexpected top-level report shape is a failed run.

Configuration presence is labeled `CONFIGURED`, not connected or operational. Runtime readiness progresses through `CONNECTING`, `CONNECTED`, and `VALIDATED` only during an attempted run; safe failure categories are shown as `FAILED`. `VALIDATED` means the final report passed the application contract, not that the configured agent or tools have been independently audited against ERPNext.

Use an ART test environment with read-only ERPNext permissions. No P02 feature sends supplier email, changes purchase orders, creates receipts, or initiates alternate orders.

## Delivery classification settings

- `P02_TIMEZONE` selects the local business timezone used to calculate the monitoring date. Default: `Asia/Kolkata`.
- `P02_UPCOMING_DAYS` sets the inclusive upcoming window from 1 to 90 days. Default: `7`.
- `P02_DUE_DATE_BASIS` accepts `contractual` or `supplier_promise`. Default: `contractual`.

The contractual basis compares open quantity to the PO item’s `schedule_date`; the supplier-promise basis uses `expected_delivery_date`. Both dates are retained and shown separately. Neither is overwritten. The selected basis changes overdue reporting and is visible in the UI.

Receipt quantity comes from submitted Purchase Receipt Item rows with exact PO item linkage. Draft and cancelled records are ignored. Returns reduce received quantity. Missing item linkage, incomplete receipt enumeration, duplicate evidence, conflicting dates, or impossible quantities produce `NEEDS VERIFICATION`.

## Run history and audit storage

Run history and configuration are saved as JSON under `.data/p02-delivery/` by default. This is a local single-instance storage mechanism, not a shared database. To use another writable location, set `P02_DATA_DIR`. Protect that directory as it may contain supplier and purchase order information. Do not deploy multiple app instances against separate local files when shared history is required.

## Validation

```bash
npm run build
npm test
python scripts/procurement/validate-procurement-workspace.py
```

`npm test` runs persistence tests and P02 delivery classification tests. A unit-test pass does not verify ART connectivity, live ERPNext data, the configured agent’s result schema, or the synthetic DELIVERY-001 benchmark. See [`docs/P02-DELIVERY-CONTROL-CENTER.md`](docs/P02-DELIVERY-CONTROL-CENTER.md) for the implementation boundary and current verification status.

## ART ADK references

- [Official JavaScript ADK package and documented API](https://www.npmjs.com/package/%40arealtimetech/adk-js)
- [ART documentation](https://docs.arealtimetech.com)\n
