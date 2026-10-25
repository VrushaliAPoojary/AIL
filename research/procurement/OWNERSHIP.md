# Procurement Research Workspace: Team Ownership & Governance

## 1. Ownership Matrix

This document defines the definitive role, process scope, and Git branch assignment for each member of the four-person procurement research team.

| Member | GitHub Account | Assigned Process ID & Name | Role | Git Branch | Working Directory |
|---|---|---|---|---|---|
| **Chiranjeevi** | `Chiranjeevi005` | `P01-RFP` — RFP Requirement Review & Response Coordination | Coordinator & Process Owner | `research/chiranjeevi` | [`processes/P01-RFP/`](./processes/P01-RFP/) |
| **Vrushali** | `VrushaliAPoojary` | `P02-SUPPLIER-DELIVERY` — Supplier Delivery Confirmation & Delay Escalation | Process Owner | `research/vrushali` | [`processes/P02-SUPPLIER-DELIVERY/`](./processes/P02-SUPPLIER-DELIVERY/) |
| **Bhushan** | `BhushanShenoy07` | `P03-REPLENISHMENT` — Inventory Replenishment & Reorder Exceptions | Process Owner | `research/bhushan` | [`processes/P03-REPLENISHMENT/`](./processes/P03-REPLENISHMENT/) |
| **Ashwin** | `ashwinash19` | `P04-INVOICE-EXCEPTIONS` — Invoice Discrepancy Resolution | Process Owner | `research/ashwin` | [`processes/P04-INVOICE-EXCEPTIONS/`](./processes/P04-INVOICE-EXCEPTIONS/) |

---

## 2. Fundamental Ownership Principles

1. **One Person Owns One Process:**
   Each researcher has exclusive authority and responsibility over their assigned procurement process. No researcher may edit or commit changes to another member's process directory without prior consultation and documented co-authorship.

2. **Cross-Process Dependencies Over Duplication:**
   Real-world procurement workflows interconnect (e.g., supplier delivery delays in P02 directly trigger reorder adjustments in P03 and affect goods receipt matching in P04). When an operational relationship exists across process boundaries:
   - **Do NOT duplicate** the workflow or evidence in your own process folder.
   - **Reference** the upstream or downstream process using its standard identifier (e.g., `WF-P02-003 -> WF-P03-001`) and document the explicit handoff boundary in `workflow.md`.

3. **Coordinator Governance:**
   As Project Coordinator, **Chiranjeevi** oversees the integrity of the shared registers:
   - Master Prompt & Standards: [`MASTER_PROMPT.md`](./MASTER_PROMPT.md), [`RESEARCH_STANDARD.md`](./RESEARCH_STANDARD.md)
   - Central Evidence Register: [`EVIDENCE_REGISTER.md`](./EVIDENCE_REGISTER.md)
   - Central Ambiguities Register: [`AMBIGUITIES.md`](./AMBIGUITIES.md)
   - Central Decisions Log: [`DECISIONS.md`](./DECISIONS.md)
   - Pull Request Reviews: All process PRs require coordinator review and approval prior to merging into `main`.

---

## 3. Team Git & Contribution Workflow

To maintain clean Git history and zero disruption to the ART application:

1. **Orientation:** Read [`MASTER_PROMPT.md`](./MASTER_PROMPT.md) and [`RESEARCH_STANDARD.md`](./RESEARCH_STANDARD.md) before initiating research.
2. **Branch Creation:** Ensure your local checkout is updated with the latest `main`, then create your personal research branch:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b research/<your-name>
   ```
3. **Focused Modification:** Work exclusively inside your assigned directory (`research/procurement/processes/P0x-.../`).
4. **Local Verification:** Validate that all internal markdown links resolve and that no external application code or schema files were touched.
5. **Commit:** Commit atomic, descriptive research updates (e.g., `docs(procurement-p02): add verified ASN exception evidence`).
6. **Pull Request:** Push your branch to GitHub and open a Pull Request targeting `main`.
7. **Coordinator Review:** Chiranjeevi reviews the PR for evidentiary compliance, zero-fabrication adherence, and link validity before merging.
