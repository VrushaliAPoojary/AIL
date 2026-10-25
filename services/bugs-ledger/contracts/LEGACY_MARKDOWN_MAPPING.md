# Legacy Markdown to Canonical Ticket Contract Mapping

This document specifies the exact mapping between the existing Markdown bug records stored in `ART-Product-Validation/bugs/` and the new Canonical Ticket Contract (`TicketArtifact`).

---

## 1. Direct Field Mapping

| Existing Markdown Source | Canonical Ticket Field | Provenance | Handling When Unsupported / Missing in Markdown |
| :--- | :--- | :--- | :--- |
| **Title Header** (`# ART-AGENT-001 — Structured output...`) | `Title` | `HUMAN_APPROVED` | Required. Extracted after `# <ID> — `. |
| *(None in legacy schema)* | `Repro Steps` | `HUMAN_APPROVED` | `"Not provided"` |
| **`## Expected`** | `Expected Result` | `HUMAN_APPROVED` | Content preserved verbatim. |
| **`## Actual`** | `Actual Result` | `HUMAN_APPROVED` | Content preserved verbatim. |
| *(None in legacy schema)* | `Business Impact` | `HUMAN_APPROVED` | `"Not provided"` |
| **`## Production-Grade Fix Proposal`** (and subsections) | `Recommended Solution` | `HUMAN_APPROVED` | Content preserved verbatim. |
| Extracted from Bug ID prefix (`ART-<MODULE>-###`) | `Module` | `HUMAN_APPROVED` | Module code extracted (`AGENT`, `GOV`, `SFN`), or `"Not provided"` |
| *(None in legacy schema)* | `Environment` | `HUMAN_APPROVED` | `"Not provided"` |
| **`- **Severity:** HIGH`** | `Severity` | `HUMAN_APPROVED` | Parsed as enum (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), or `"Not provided"` |
| *(None in legacy schema)* | `Priority` | `HUMAN_APPROVED` | `"Not provided"` |
| *(None in legacy schema)* | `Tags` | `HUMAN_APPROVED` | Derived from module or empty list `[]`. |
| *(None in legacy schema)* | `Discussion` | `HUMAN_APPROVED` | Empty list `[]`. |

---

## 2. Evidence, Developer Update, and Retest Mapping

The legacy sections that are not part of the 12 core ticket fields map directly to their dedicated first-class contract entities:

1. **`## Evidence`**:
   - Maps to **`Evidence[]`** objects with `stage: "ORIGINAL"` and `provenance: "EVIDENCE_BACKED_FACT"`.
   - Links the existing PNG screenshot filenames stored alongside the Markdown record.
2. **`## Developer Update`**:
   - Maps to **`DeveloperUpdate[]`** objects.
   - If the markdown contains `"Pending."` or is blank, no active `DeveloperUpdate` object is recorded.
   - When a developer submits real fix info, a new `DeveloperUpdate` object is appended.
3. **`## Retest`**:
   - Maps to **`RetestArtifact[]`** objects.
   - If the markdown contains `"Pending."` or is blank, no `RetestArtifact` is recorded.
   - When verification occurs, a `RetestArtifact` records the evidence and human sign-off.

---

## 3. Bidirectional Compatibility Guarantee

- **Reading Legacy Records:** When reading legacy Markdown files from `ART-Product-Validation/bugs/`, missing fields are filled with `"Not provided"` without altering the on-disk Markdown record.
- **Serializing Back to Disk:** When the application writes updates back to `ART-Product-Validation/bugs/<BUG-ID>__<short-name>/<BUG-ID>.md`, it preserves the standard sections specified in `AGENTS.md`:
  - `# <BUG-ID> — <Bug title>`
  - `- **Severity:**`
  - `- **Status:**`
  - `## Bug`
  - `## Expected`
  - `## Actual`
  - `## Evidence`
  - `## Production-Grade Fix Proposal`
  - `## Developer Update`
  - `## Retest`
- This ensures zero breaking changes to existing repository assets.
