# AI Development Protocol

This repository uses a process-first AI development protocol.
It governs how AI assists development.
It does not define product names, product workflows, schemas, research terms, or UI design.

## Core principle

Human ownership is always the final authority.

AI may inspect, propose, implement, and verify.
Humans own meaning, scope, and final product decisions.

## Working cycle

### LEARN

- Inspect the current repository state first.
- Read the relevant docs, source files, tests, and data flow boundaries.
- Identify the actual source of truth before making changes.

### THINK

- Decide the smallest safe change.
- Separate facts from assumptions.
- Flag risks that could affect schema, contracts, research meaning, or product behavior.

### IMPLEMENT

- Make the minimum change needed.
- Reuse existing patterns and conventions.
- Do not rewrite source-of-truth data to force a result.

### VERIFY

- Run the relevant tests or build checks.
- Confirm the change works in the real code path.
- Check for unintended side effects.

### UNDERSTAND

- Record what changed and why.
- Note what stayed unknown or unresolved.
- Summarize any evidence limitations or tradeoffs.

### ADAPT

- Update the development trace when a new pattern or constraint appears.
- Adjust the process if the repository reveals a better durable convention.
- Keep the protocol stable and lightweight.

## Rules

- Do not change schemas, contracts, or research source files unless the task explicitly requires it.
- Do not fabricate missing data.
- Do not hide uncertainty.
- Do not treat generated output as upstream evidence.
- Prefer durable documentation over temporary memory.
- Preserve provenance and traceability.
- Escalate to a human when a change would alter product semantics or require a new architectural decision.

## What this protocol is for

This protocol keeps AI-assisted work:

- explainable
- repeatable
- auditable
- safe for the repository's long-term evolution

It is a development method, not a product method.
