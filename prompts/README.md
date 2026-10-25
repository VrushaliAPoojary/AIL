# ART Prompt Registry

## Start Here

Welcome to the **ART Investigation Lab Prompt Registry**. This registry defines the canonical, deterministic prompt routing architecture for all contributor, orchestrator, lifecycle, and administrative workflows across the lab.

### Workflow Task Routing Table

| Task | Prompt | Type | Execution Role | Who Should Run It |
| :--- | :--- | :--- | :--- | :--- |
| **Found a product defect** | [`workflows/bug_pipeline.md`](./workflows/bug_pipeline.md) | Markdown Prompt | End-to-End Orchestrator | Any Contributor |
| **Have a product feature / enhancement request** | [`workflows/feature_pipeline.md`](./workflows/feature_pipeline.md) | Markdown Prompt | End-to-End Orchestrator | Any Contributor |
| **Sync validation dashboard (Azure → Ledger → HTML → Pages)** | [`workflows/dashboard_sync_pipeline.md`](./workflows/dashboard_sync_pipeline.md) | Markdown Prompt | End-to-End Orchestrator | Coordinator / Contributor |
| **Start daily session & workspace bootstrap** | [`git/start_work.md`](./git/start_work.md) | Antigravity Prompt | Git Session Lifecycle | Any Contributor |
| **Conduct research / author findings** | [`research/research.md`](./research/research.md) | Antigravity Prompt | Research Authoring | Process Owner |
| **Log empirical ART test execution** | [`research/art_validation.md`](./research/art_validation.md) | Antigravity Prompt | Empirical Validation | Process Owner |
| **Submit completed work / Prepare PR** | [`git/submit_pr.md`](./git/submit_pr.md) | Markdown Prompt | PR Submission & Validation | Any Contributor |
| **Atomic stage & commit helper** | [`git/submit_work.md`](./git/submit_work.md) | Antigravity Prompt | Git Staging Helper | Any Contributor |
| **Deploy validation report to GitHub Pages** | [`git/github_pages_deploy.md`](./git/github_pages_deploy.md) | Markdown Prompt | Static Publisher | Coordinator / Contributor |
| **Draft bug intake & isolation** | [`bugs/bug_intake.md`](./bugs/bug_intake.md) | Antigravity Prompt | Internal Harness | Contributor / Harness B |
| **Retest a developer fix** | [`bugs/retest.md`](./bugs/retest.md) | Antigravity Prompt | Retest Verification | Verified Human Tester |
| **Sync Azure resolution & developer feedback** | [`bugs/azure_resolution_sync.md`](./bugs/azure_resolution_sync.md) | Markdown Prompt | Lifecycle Sync Harness | Contributor / Harness 03 |
| **Publish sanitized static report** | [`bugs/publish_validation_report.md`](./bugs/publish_validation_report.md) | Markdown Prompt | Report Generation | Contributor / Harness 04 |
| **Coordinator review & canonical promotion** | [`admin/coordinator.md`](./admin/coordinator.md) | Antigravity Prompt | Privileged Governance | Coordinator (Chiranjeevi) |

---

## Execution Levels

To prevent workflow drift and maintain operational discipline, prompt execution is strictly partitioned into three tiers:

### Level 1 — User Entry Points (Direct Contributor Execution)
These are primary operations that human contributors invoke to start work, author research, orchestrate bugs/features, or submit pull requests:
- [`workflows/bug_pipeline.md`](./workflows/bug_pipeline.md)
- [`workflows/feature_pipeline.md`](./workflows/feature_pipeline.md)
- [`workflows/dashboard_sync_pipeline.md`](./workflows/dashboard_sync_pipeline.md)
- [`git/start_work.md`](./git/start_work.md)
- [`research/research.md`](./research/research.md)
- [`research/art_validation.md`](./research/art_validation.md)
- [`git/submit_pr.md`](./git/submit_pr.md)
- [`bugs/retest.md`](./bugs/retest.md)

### Level 2 — Internal / Reusable Harness Prompts
These prompts perform a single bounded lifecycle stage (Harness 01, Harness 02, Harness 03, Harness 04). They are normally invoked automatically by orchestrators or used specifically for debugging, retesting, or publishing:
- [`bugs/bug_intake.md`](./bugs/bug_intake.md) — Bug draft intake (Harness B / Harness 01)
- [`bugs/azure_resolution_sync.md`](./bugs/azure_resolution_sync.md) — Azure feedback & resolution sync (Harness 03)
- [`bugs/publish_validation_report.md`](./bugs/publish_validation_report.md) — Static report generator (Harness 04)
- [`git/github_pages_deploy.md`](./git/github_pages_deploy.md) — Isolated static Pages deployment
- [`git/submit_work.md`](./git/submit_work.md) — Internal staging and validation checklist invoked by `submit_pr.md`

### Level 3 — Privileged Operations (Coordinator-Only)
Restricted operations requiring verified multi-factor identity (OS username `chiranjeevi` and Git authentication `Chiranjeevi005`). Privilege escalation is blocked and fails closed:
- [`admin/coordinator.md`](./admin/coordinator.md) — Canonical bug promotion (Harness C), ledger recompilation, and authorized Azure synchronization.

---

## Do Not Duplicate Workflows

To guarantee single sources of truth and eliminate pipeline fragmentation:

> [!IMPORTANT]
> **Bug Pipeline Execution Rule:**
> When logging or updating defects, **always execute [`workflows/bug_pipeline.md`](./workflows/bug_pipeline.md)**.
> Do NOT manually chain Harness 01 (`bug-intake-storage-prompt.md`) and Harness 02 (`azure-ticket-creator-prompt.md`) unless debugging or performing isolated testing. The pipeline handles automatic, verified handoff between local storage and Azure.

> [!IMPORTANT]
> **Feature Backlog Pipeline Execution Rule:**
> When proposing or updating feature requests, **always execute [`workflows/feature_pipeline.md`](./workflows/feature_pipeline.md)**.
> Do NOT manually run Feature Intake (`feature-intake-storage-prompt.md`) then Azure Sync (`azure-feature-ticket-creator-prompt.md`) separately. The pipeline guarantees atomic module routing, ID allocation, and Azure User Story creation.

> [!IMPORTANT]
> **Validation Dashboard Sync Pipeline Execution Rule:**
> When synchronizing Azure lifecycle states and publishing the public validation dashboard, **always execute [`workflows/dashboard_sync_pipeline.md`](./workflows/dashboard_sync_pipeline.md)**.
> Do NOT manually chain Azure Resolution Sync (`bugs/azure_resolution_sync.md`), Report Generator (`bugs/publish_validation_report.md`), and Pages Deploy (`git/github_pages_deploy.md`) unless debugging or doing isolated testing.

---

## Target Registry Taxonomy & Future Placement Rules

When introducing new prompts, adhere strictly to the following directory taxonomy:

| Directory | Purpose | Placement Criteria |
| :--- | :--- | :--- |
| `prompts/workflows/` | End-to-end user orchestrators | Genuine multi-stage pipelines coordinating multiple harnesses |
| `prompts/bugs/` | Bug lifecycle harnesses | Reusable bug intake, retest, resolution sync, or report publishers |
| `prompts/features/` | Feature backlog harnesses | Reusable feature intake, storage, or Azure feature sync operations |
| `prompts/git/` | Git / GitHub repository lifecycle | Workspace bootstrapping, atomic commits, PR submissions, Pages deployment |
| `prompts/research/` | Investigation & empirical testing | Procurement process authoring, citations, and ART agent evaluation logs |
| `prompts/admin/` | Privileged coordinator governance | Operations requiring coordinator identity verification and promotion |

Before adding any prompt, verify that an existing orchestrator or harness does not already own the responsibility.
