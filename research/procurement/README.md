# ART Procurement Research Workspace

Welcome to the **Procurement Research Workspace** within the ART Investigation Lab.

This workspace establishes a structured, forensic, four-person investigative environment dedicated to exploring enterprise procurement processes, quantifying real-world operational friction, auditing incumbent software limitations, and evaluating candidate ART agent capabilities.

---

## 1. Architectural Boundary & Governance

- **Repository Default Branch:** `main` remains the default branch for the ART Investigation Lab Next.js application.
- **Strict Workspace Isolation:** All procurement research is isolated under `research/procurement/`. It does **not** alter, modify, or interfere with application code in `src/`, locked schemas in `contracts/`, or existing test suites.
- **Epistemic Discipline:** Guided by strict standards where marketing assertions, AI hallucinations, and unverified assumptions are forbidden. All findings require empirical grounding.

---

## 2. Team Ownership Matrix

Each team member has sole ownership of exactly one core procurement process:

| Member | Assigned Process ID & Name | Role | Git Branch | Working Directory |
|---|---|---|---|---|
| **Chiranjeevi** | `P01-RFP` — RFP Requirement Review & Response Coordination | Coordinator & Process Owner | `research/chiranjeevi` | [`processes/P01-RFP/`](./processes/P01-RFP/) |
| **Vrushali** | `P02-SUPPLIER-DELIVERY` — Supplier Delivery Confirmation & Delay Escalation | Process Owner | `research/vrushali` | [`processes/P02-SUPPLIER-DELIVERY/`](./processes/P02-SUPPLIER-DELIVERY/) |
| **Bhushan** | `P03-REPLENISHMENT` — Inventory Replenishment & Reorder Exceptions | Process Owner | `research/bhushan` | [`processes/P03-REPLENISHMENT/`](./processes/P03-REPLENISHMENT/) |
| **Ashwin** | `P04-INVOICE-EXCEPTIONS` — Invoice Discrepancy Resolution | Process Owner | `research/ashwin` | [`processes/P04-INVOICE-EXCEPTIONS/`](./processes/P04-INVOICE-EXCEPTIONS/) |

*Rule: One person owns one process. Cross-process interactions must be documented as cross-process dependencies and handoffs, never duplicated across folders.*

---

## 3. Directory Layout

```text
research/
└── procurement/
    ├── README.md                 # Workspace guide, overview, and workflow protocols (this file)
    ├── MASTER_PROMPT.md          # Shared instruction document for ChatGPT research sessions
    ├── RESEARCH_STANDARD.md      # Grounding rules, evidence (E0-E4) & ambiguity (A1-A4) standards
    ├── OWNERSHIP.md              # Detailed team matrix, process boundaries, and Git rules
    ├── EVIDENCE_REGISTER.md      # Central register for verified citations and data points
    ├── AMBIGUITIES.md            # Central registry tracking unknowns, gaps, and contradictions
    ├── DECISIONS.md              # Architecture and governance decision records (ADRs)
    ├── processes/
    │   ├── P01-RFP/              # RFP Requirement Review & Response Coordination (Chiranjeevi)
    │   │   ├── investigation.md  # Core investigation brief and software audit
    │   │   ├── evidence.md       # Process-specific evidence citations
    │   │   ├── workflow.md       # Operational workflow and exception paths
    │   │   └── art-validation.md # ART agent role, guardrails, and validation status
    │   ├── P02-SUPPLIER-DELIVERY/# Supplier Delivery Confirmation & Delay Escalation (Vrushali)
    │   │   ├── investigation.md
    │   │   ├── evidence.md
    │   │   ├── workflow.md
    │   │   └── art-validation.md
    │   ├── P03-REPLENISHMENT/    # Inventory Replenishment & Reorder Exceptions (Bhushan)
    │   │   ├── investigation.md
    │   │   ├── evidence.md
    │   │   ├── workflow.md
    │   │   └── art-validation.md
    │   └── P04-INVOICE-EXCEPTIONS/# Invoice Discrepancy Resolution (Ashwin)
    │       ├── investigation.md
    │       ├── evidence.md
    │       ├── workflow.md
    │       └── art-validation.md
    ├── operations/               # Operational guides, checklists, and AI rules
    │   ├── TEAM_ONBOARDING.md    # Contributor setup, Git workflow, and troubleshooting
    │   ├── RESEARCH_EXECUTION.md # 12-step repeatable evidence investigation procedure
    │   ├── EVIDENCE_QUALITY_GATE.md # 12-point evidence acceptance criteria
    │   ├── PR_REVIEW_STANDARD.md # PR review contract and 4 decision verdicts
    │   ├── AI_AGENT_RULES.md     # 12 non-negotiable rules for AI assistants
    │   ├── AMBIGUITY_RESOLUTION.md # A1-A4 operational ambiguity protocol
    │   ├── SESSION_HANDOFF.md    # Inter-session handoff template for AI/human continuity
    │   └── COORDINATOR_PLAYBOOK.md # Chiranjeevi review and PR merge procedure
    ├── validation/
    │   └── RFP-001/              # Synthetic test validation kit
    │       ├── README.md         # Protocol: synthetic status, answer key isolation
    │       ├── RFP-001-ART-Agent-Prompt.md
    │       ├── RFP-001-Gold-Answer-Key.md
    │       ├── RFP-001-Test-Checklist.md
    │       └── RFP-001-Test-Document.md
    └── reviews/
        └── README.md             # Coordinator PR review checklist and audit log
```

---

## 4. Team Workflow Guide

Every team member must follow the detailed onboarding guide in [`operations/TEAM_ONBOARDING.md`](./operations/TEAM_ONBOARDING.md):

1. **Review Standards:** Carefully read [`MASTER_PROMPT.md`](./MASTER_PROMPT.md), [`RESEARCH_STANDARD.md`](./RESEARCH_STANDARD.md), and [`operations/RESEARCH_EXECUTION.md`](./operations/RESEARCH_EXECUTION.md) before conducting any research.
2. **Strict Scope Discipline:** Work **only** on your assigned process directory under `processes/`.
3. **Branch from Latest `main`:**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b research/<your-name>
   ```
   *(Recommended branches: `research/chiranjeevi`, `research/vrushali`, `research/bhushan`, `research/ashwin`).*
4. **Conduct Grounded Research:** Use the instructions in [`MASTER_PROMPT.md`](./MASTER_PROMPT.md) during AI research sessions. Do not accept hallucinations. Require exact quotes and canonical URLs.
5. **Update Markdown Documents:** Populate `investigation.md`, `evidence.md`, `workflow.md`, and `art-validation.md` in your process directory.
6. **Commit Meaningful Updates:** Commit with clear, descriptive commit messages (e.g., `docs(p02): add supplier EDI acknowledgment evidence`).
7. **Open Pull Request into `main`:** Push your branch and open a PR targeting `main`.
8. **Wait for Coordinator Review:** Coordinator **Chiranjeevi** will review your PR against the [`reviews/README.md`](./reviews/README.md) checklist before merging.

---

## 5. Evidence & Ambiguity Standards Summary

### Evidence Levels ([`RESEARCH_STANDARD.md`](./RESEARCH_STANDARD.md))
- **E0:** Hypothesis (Not Validated)
- **E1:** Public Process Documentation
- **E2:** Public Documented Industry Pain Point
- **E3:** Individual Practitioner Testimony
- **E4:** Direct Enterprise Operational Validation  
*Rule: Never automatically promote evidence levels.*

### Ambiguity Severities ([`AMBIGUITIES.md`](./AMBIGUITIES.md))
- **A1:** Minor uncertainty — log and continue.
- **A2:** Material uncertainty — investigate before drawing conclusions.
- **A3:** Critical unknown — blocks automation proposals.
- **A4:** Authorization / safety risk — stop consequential action immediately.

---

## 6. Synthetic Benchmark Validation (RFP-001)

The kit under [`validation/RFP-001/`](./validation/RFP-001/) is a synthetic benchmarking environment:
- **Synthetic Data:** Contains 20 seeded test requirements; does **not** represent real tender evidence.
- **Answer Key Isolation:** [`validation/RFP-001/RFP-001-Gold-Answer-Key.md`](./validation/RFP-001/RFP-001-Gold-Answer-Key.md) must **NEVER** be provided to tested agents.
- **Execution Status:** **CURRENTLY NOT TESTED**.
- **Separation:** Benchmark results must **never** be mixed into empirical research registers.
