# ART Investigation Lab — Coordinator Guide

> **Audience:** Project Coordinator Chiranjeevi  
> **Role:** Sole merging authority, canonical bug ID promotion authority, and Azure DevOps integration gatekeeper  

---

## 1. Coordinator Responsibilities & Authority

As Project Coordinator, Chiranjeevi exercises three exclusive authorities:
1. **Pull Request Merging:** Sole reviewer and merging authority for all PRs targeting `main`.
2. **Canonical Bug Promotion:** Sole executor of `promote-bug` (Harness C) promoting contributor drafts (`DRAFT-P0X-...`) to canonical `ART-*` IDs.
3. **Azure DevOps Synchronization:** Sole operator authorized to sync canonical bugs and work items to Azure DevOps.

---

## 2. PR Review & Merge Procedure

When a team member opens a Pull Request:

### Step 1: Inspect Automated CI Status
Check GitHub Actions checks on the PR:
- `Procurement Research PR Check` (`.github/workflows/procurement-pr-check.yml`)
- `Bugs Ledger & Integration Validation` (`.github/workflows/bugs-ledger-ci.yml`)

If either fails, do not review manually; request the author resolve local validation errors.

### Step 2: Scope Boundary Inspection
Verify in the GitHub PR diff:
- The contributor only modified their assigned process directory:
  - Vrushali $\rightarrow$ `research/procurement/processes/P02-SUPPLIER-DELIVERY/`
  - Bhushan $\rightarrow$ `research/procurement/processes/P03-REPLENISHMENT/`
  - Ashwin $\rightarrow$ `research/procurement/processes/P04-INVOICE-EXCEPTIONS/`
- Zero changes exist in `src/`, `contracts/`, `data/`, or root `package.json`.

### Step 3: Run Local Coordinator Audit (Optional / Deep Inspection)
```bash
git fetch origin
git checkout -b review/pr-<number> origin/<branch-name>

# Run full system validation
python3 scripts/art_harness.py validate
```

---

## 3. Promoting Draft Bugs to Canonical ART IDs (Harness C)

When a contributor submits a draft bug (`DRAFT-P0X-...`):

### 1. Review the Draft
Inspect the draft file under `services/bugs-ledger/ART-Product-Validation/bugs/<Feature>/drafts/`:
- Confirm root cause, repro steps, and evidence attachments are legitimate.
- Confirm severity and module classification are accurate.

### 2. Execute Promotion Command
Run the promotion subcommand as coordinator:
```bash
python3 scripts/art_harness.py promote-bug \
  --draft-file services/bugs-ledger/ART-Product-Validation/bugs/Agent\ Lab/drafts/DRAFT-P03-AGENT-001.md \
  --coordinator chiranjeevi
```

**Expected Output:**
```text
✅ Bug promoted successfully:
   Canonical ID: ART-AGENT-010
   Created Folder: services/bugs-ledger/ART-Product-Validation/bugs/Agent Lab/ART-AGENT-010__.../
   Evidence Renamed: ART-AGENT-010__...__01.png
   Cleaned up draft file: DRAFT-P03-AGENT-001.md
```

### 3. Recompile Summary Ledger
After promoting one or more bugs:
```bash
python3 scripts/art_harness.py compile-ledger
```
This updates `services/bugs-ledger/ART-Product-Validation/ART_PRODUCT_VALIDATION_LEDGER.md`.

---

## 4. Azure DevOps Sync & Credential Governance

### Safety Guard
1. **Never Sync Draft Bugs:** Only canonical `ART-*` bugs promoted by the coordinator may be synced.
2. **Never Hardcode Secrets:** Keep the Azure PAT in GitHub Secrets (`AZURE_DEVOPS_PAT`) or local environment variables during synchronization sessions. Never commit `.env` files.
3. **Manual Human Confirmation Required:** Sync scripts require an explicit `--confirm-azure-sync` flag.

```bash
# Example dry-run (safe):
python3 services/bugs-ledger/scripts/migrate_canonical_bugs_to_azure.py --dry-run
```

---

## 5. Rejection & Failure Criteria Reference

| Condition | Action Required |
| :--- | :--- |
| Contributor modified another member's process folder | Reject PR; ask author to extract their process updates only |
| Contributor committed code inside `src/` or root config | Reject PR immediately; remind contributor of research isolation |
| Markdown contains `/home/username/...` absolute links | Reject PR; run `art_harness validate` to detect broken/non-portable links |
| Unauthorized user attempts `promote-bug` | Blocked automatically by permission check in `art_harness.py` |
