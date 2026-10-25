# Phase 07-0B Structure

This document records the structure-only preparation for receiving the AOI compiler capability in AIL.

## Created directories

- `compiler/`
- `compiler/core/`
- `compiler/input/`
- `compiler/extraction/`
- `compiler/output/`
- `compiler/validation/`

## Package markers added

To make the future Python compiler package boundaries explicit, package markers were added at:

- `compiler/__init__.py`
- `compiler/core/__init__.py`
- `compiler/input/__init__.py`
- `compiler/extraction/__init__.py`
- `compiler/output/__init__.py`
- `compiler/validation/__init__.py`

No implementation modules were copied from AOI.

## Intentionally preserved AIL structure

The existing AIL application layout remains intact:

- `src/`
- `public/`
- `contracts/`
- `docs/repository-current-state.md`
- `docs/ai-development-protocol.md`
- the current loader, validator, and view-model code paths

The Markdown UI and presentation components were not modified in this run.

## Contract authority

The authoritative AIL contract targets remain:

- `contracts/AIL-INVESTIGATION-BRIEF-JSON-SCHEMA-V1.json`
- `contracts/AIL-INVESTIGATION-BRIEF-CONTRACT-V1.md`

No schema revision was introduced.

## Expected Run 3 destinations

The compiler implementation migration should land in:

- `compiler/main.py`
- `compiler/core/`
- `compiler/input/`
- `compiler/extraction/`
- `compiler/output/`
- `compiler/validation/`

This run only prepares those receiving directories.
