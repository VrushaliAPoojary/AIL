# ART Prompt Registry — Canonical Inventory Manifest

This document provides the authoritative, machine/operator-oriented catalog of all managed prompts within the ART Investigation Lab. It defines the canonical path, execution role, direct execution permissions, calling hierarchy, and required privilege level for each prompt.

## Canonical Registry Manifest

| Prompt Key | Canonical Path | Role | Direct Execution | Caller | Privilege Level |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `bug_pipeline` | `prompts/workflows/bug_pipeline.md` | `ORCHESTRATOR` | YES | User | GENERAL |
| `feature_pipeline` | `prompts/workflows/feature_pipeline.md` | `ORCHESTRATOR` | YES | User | GENERAL |
| `dashboard_sync_pipeline` | `prompts/workflows/dashboard_sync_pipeline.md` | `ORCHESTRATOR` | YES | User / Coordinator | GENERAL |
| `start_work` | `prompts/git/start_work.md` | `ENTRY_POINT` | YES | User | GENERAL |
| `submit_pr` | `prompts/git/submit_pr.md` | `ENTRY_POINT` | YES | User | GENERAL |
| `submit_work` | `prompts/git/submit_work.md` | `INTERNAL_HARNESS` | NO | `submit_pr.md` / User | GENERAL |
| `github_pages_deploy` | `prompts/git/github_pages_deploy.md` | `SPECIALIZED_OPERATION` | YES | User / Coordinator | GENERAL |
| `research` | `prompts/research/research.md` | `ENTRY_POINT` | YES | Process Owner | CONTRIBUTOR |
| `art_validation` | `prompts/research/art_validation.md` | `ENTRY_POINT` | YES | Process Owner | CONTRIBUTOR |
| `bug_intake` | `prompts/bugs/bug_intake.md` | `INTERNAL_HARNESS` | NO | `bug_pipeline` / User | CONTRIBUTOR |
| `retest` | `prompts/bugs/retest.md` | `SPECIALIZED_OPERATION` | YES | Human Tester | CONTRIBUTOR |
| `azure_resolution_sync` | `prompts/bugs/azure_resolution_sync.md` | `INTERNAL_HARNESS` | YES | Contributor / Script | GENERAL |
| `publish_validation_report` | `prompts/bugs/publish_validation_report.md` | `INTERNAL_HARNESS` | YES | Contributor / Script | GENERAL |
| `coordinator` | `prompts/admin/coordinator.md` | `PRIVILEGED_OPERATION` | YES | Coordinator Only | COORDINATOR |

---

## Architectural Principles

1. **Separation of Concerns:**
   - `prompts/README.md` provides human navigation and task-oriented guidance.
   - `prompts/PROMPT_REGISTRY.md` provides canonical metadata and inventory tracking.
   - Individual prompt files define their respective executable behavioral contracts.
2. **Deterministic Invocation:**
   - Every workflow has exactly one canonical path.
   - Orchestrator handoffs (`Harness 01 → Harness 02`) are automated and idempotent.
   - Privileged operations fail closed if coordinator identity cannot be verified.
