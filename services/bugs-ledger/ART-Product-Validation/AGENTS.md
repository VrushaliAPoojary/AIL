# ART Product Validation Instructions

## Purpose

Maintain simple records of actual ART product bugs, their evidence, developer updates and retest results.

## Folder Structure

Each actual bug must use:

bugs/<BUG-ID>__<short-bug-name>/

Inside that folder:

- <BUG-ID>.md
- Related PNG screenshots

Do not create the folder until a real bug is provided.

## Naming Rules

Bug folder:

<BUG-ID>__<short-bug-name>

Bug record:

<BUG-ID>.md

Screenshot:

<BUG-ID>__<short-description>__<date>__<sequence>.png

Use lowercase kebab-case for folder and screenshot descriptions.

Never overwrite an existing screenshot.

## Bug Record Format

Each bug Markdown record must contain only:

# <BUG-ID> — <Bug title>

- **Severity:**
- **Status:**

## Bug

## Expected

## Actual

## Evidence

## Developer Update

## Retest

Do not add any other sections unless explicitly requested.

Do not invent missing information.

## Status Values

Use only:

- OPEN
- FIXING
- RETEST
- VERIFIED
- CLOSED
- BLOCKED

## Update Rules

1. Preserve the original bug description.
2. Add developer information only when it is provided.
3. Change status to RETEST when a developer says a fix is ready.
4. Change status to VERIFIED only after a successful retest.
5. Keep failed and successful retest results in the Retest section.
6. Store every screenshot inside its corresponding bug folder.
7. Update the master ledger whenever a bug is created or its status changes.
8. Do not create mock data or example records.
