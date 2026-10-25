# Welcome to ART Investigation Lab — START HERE

Welcome to the **ART Investigation Lab (AIL)** repository! This guide provides everything you need to understand the repository architecture, your assignment, your daily workflow, and how to collaborate safely using **Antigravity IDE**.

---

## 1. Repository Architecture & Scope

This repository houses three interconnected engineering and research workspaces:

```text
art-investigation-lab/
├── START_HERE.md                     # You are here: Team entry guide
├── AGENTS.md                         # Protocol for AI agents in Antigravity
├── research/
│   └── procurement/                  # 🔍 Procurement Research Workspace
│       ├── OWNERSHIP.md              # Ownership matrix & process rules
│       ├── RESEARCH_STANDARD.md      # Grounding & evidence standards
│       ├── processes/                # Contributor process directories
│       │   ├── P01-RFP/              # Chiranjeevi (Coordinator)
│       │   ├── P02-SUPPLIER-DELIVERY/# Vrushali
│       │   ├── P03-REPLENISHMENT/    # Bhushan
│       │   └── P04-INVOICE-EXCEPTIONS/# Ashwin
│       └── validation/               # ART test execution logs
├── services/
│   └── bugs-ledger/                  # 🐛 ART Bugs-Ledger Service
│       ├── ART-Product-Validation/   # 37 historical bug records & 98 evidence PNGs
│       ├── core/ & api/              # Ingestion, identity, lifecycle, FastAPI
│       ├── contracts/                # Schemas & contract fixtures
│       └── tests/                    # 264 pytest unit tests
├── scripts/
│   ├── art_harness.py                # 🚀 UNIFIED HARNESS ENTRY POINT
│   ├── validation/                   # Promotion, intake, link validators
│   └── procurement/                  # Workspace boundaries validator
└── src/ & tests/                     # ⚙️ Core AIL Web Application (Next.js/React)
```

> [!IMPORTANT]
> **Strict Scope Isolation:** As a research contributor, you work inside `research/procurement/` and with `scripts/art_harness.py`. You do **not** modify files in `src/`, root `package.json`, or root application configurations.

---

## 2. Team Ownership & Assignments

Each team member has sole ownership of exactly one procurement process:

| Contributor | GitHub Account | Process ID & Scope | Git Branch | Working Directory | Primary Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Chiranjeevi** | `Chiranjeevi005` | `P01-RFP` — RFP Requirement Review & Response Coordination | `research/chiranjeevi` | `research/procurement/processes/P01-RFP/` | Project Coordinator & P01 Owner |
| **Vrushali** | `VrushaliAPoojary` | `P02-SUPPLIER-DELIVERY` — Supplier Delivery Confirmation & Delay Escalation | `research/vrushali` | `research/procurement/processes/P02-SUPPLIER-DELIVERY/` | Process Owner |
| **Bhushan** | `BhushanShenoy07` | `P03-REPLENISHMENT` — Inventory Replenishment & Reorder Exceptions | `research/bhushan` | `research/procurement/processes/P03-REPLENISHMENT/` | Process Owner |
| **Ashwin** | `ashwinash19` | `P04-INVOICE-EXCEPTIONS` — Invoice Discrepancy Resolution | `research/ashwin` | `research/procurement/processes/P04-INVOICE-EXCEPTIONS/` | Process Owner |

---

## 3. Quickstart & Antigravity Setup

### Prerequisites
1. **Git & GitHub CLI:** Ensure `git` and `gh` are installed.
2. **Python 3.11+:** For running the validation harness.
3. **Antigravity IDE:** The pair-programming IDE for all research and development.

### Setup Steps

#### Linux / macOS
```bash
# 1. Clone repository
git clone https://github.com/ART-Automation-Lab/art-investigation-lab.git
cd art-investigation-lab

# 2. Authenticate GitHub CLI (browser-based, no manual token entry)
gh auth login

# 3. Open in Antigravity
agy .
```

#### Windows (PowerShell)
```powershell
# 1. Enable long paths during clone to avoid Windows MAX_PATH errors:
git clone -c core.longpaths=true https://github.com/ART-Automation-Lab/art-investigation-lab.git
cd art-investigation-lab
git config core.longpaths true

# 2. Ensure UTF-8 console output:
$env:PYTHONUTF8 = "1"

# 3. Authenticate GitHub CLI or Git Credential Manager securely (browser-based):
gh auth login

# 4. If invoking npm scripts in PowerShell, use npm.cmd to bypass script execution policy:
npm.cmd --version

# 5. Open in Antigravity
agy .
```

---

## 4. Daily Workflow with Antigravity

All daily work is coordinated through the unified harness script: `python3 scripts/art_harness.py`.

```text
[Sync main] ──► [Create Branch] ──► [Edit / Research / Test] ──► [Run art_harness validate] ──► [Open PR]
```

### 1. Synchronize & Create Your Branch
```bash
git checkout main
git pull origin main
git checkout -b research/<your-name>   # e.g., research/vrushali
```

### 2. Common Daily Actions

#### A. Record an ART Test Outcome (Harness A)
When evaluating an ART workflow or simulated run:
```bash
python3 scripts/art_harness.py record-test \
  --process-id P02-SUPPLIER-DELIVERY \
  --opportunity-id OPP-002-01 \
  --run-id RUN-20261008-01 \
  --actor vrushali \
  --verdict PASS \
  --summary "Verified supplier delay escalation triggered notification correctly."
```

#### B. Log an ART Execution Bug (Harness B)
When you discover an anomaly or bug in an ART agent:
```bash
python3 scripts/art_harness.py draft-bug \
  --author P03 \
  --module Agent \
  --title "Agent response times out during multi-line quote extraction" \
  --severity HIGH \
  --description "During PO line matching, agent times out when quote table exceeds 20 rows."
```
*Note: This creates a draft (`DRAFT-P03-AGENT-001`). Only Coordinator Chiranjeevi promotes drafts to canonical `ART-*` IDs.*

#### C. Record a Retest Verification (Harness B)
When re-verifying a resolved bug:
```bash
python3 scripts/art_harness.py retest \
  --bug-id ART-AGENT-001 \
  --tester ashwin \
  --verdict VERIFIED_FIXED \
  --notes "Re-tested output parser against 50 complex JSON responses. Zero violations observed."
```

#### D. Validate Everything Locally Before Committing
Always run the validation suite before pushing:
```bash
python3 scripts/art_harness.py validate
```
This automatically runs:
1. Procurement workspace boundary checks
2. Bug ledger schema and link validations
3. All 264 pytest unit tests

---

## 5. Security & Zero-Fabrication Rules

1. **Never Commit Secrets:** Never stage `.env` files, credentials, or API keys.
2. **Never Commit Databases:** SQLite files (`*.db`, `*.sqlite`) are ignored and forbidden.
3. **Portable Relative Paths:** Never use `/home/username/...` absolute paths in Markdown. Always use relative paths (`./image.png`).
4. **Epistemic Discipline:** Zero AI hallucinations. Every evidence claim must include a verified citation or verifiable execution log.
5. **Coordinator Approval:** Only Chiranjeevi merges PRs into `main` and manages Azure DevOps synchronization.

---

## 6. Next Steps & Guides

- Contributor Guide: [`docs/CONTRIBUTOR_GUIDE.md`](./docs/CONTRIBUTOR_GUIDE.md)
- Coordinator Playbook: [`docs/COORDINATOR_GUIDE.md`](./docs/COORDINATOR_GUIDE.md)
- Procurement Research Standard: [`research/procurement/RESEARCH_STANDARD.md`](./research/procurement/RESEARCH_STANDARD.md)
- Ownership Rules: [`research/procurement/OWNERSHIP.md`](./research/procurement/OWNERSHIP.md)
