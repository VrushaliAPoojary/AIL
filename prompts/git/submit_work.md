# Antigravity Task Prompt: Submit Work & Prepare Pull Request

**File:** `prompts/git/submit_work.md`  
**Purpose:** Pre-PR verification, safety audits, atomic commit staging, and pull request preparation.

---

## Instructions for Antigravity

When instructed to "Run prompts/git/submit_work.md" to submit research, test logs, drafts, or retests:

### Step 1: Scope & Boundary Safety Audit
1. Inspect modified and untracked files:
   ```bash
   git status
   ```
2. Verify that **only** files in your assigned scope or explicit contribution targets are staged:
   - Chiranjeevi $\rightarrow$ `research/procurement/processes/P01-RFP/`
   - Vrushali $\rightarrow$ `research/procurement/processes/P02-SUPPLIER-DELIVERY/`
   - Bhushan $\rightarrow$ `research/procurement/processes/P03-REPLENISHMENT/`
   - Ashwin $\rightarrow$ `research/procurement/processes/P04-INVOICE-EXCEPTIONS/`
   - Draft bug folder $\rightarrow$ `services/bugs-ledger/ART-Product-Validation/drafts/`
   - Retest updates $\rightarrow$ `services/bugs-ledger/ART-Product-Validation/bugs/...`
3. Verify **zero** application files (`src/`, root `package.json`, `contracts/`) or other members' process directories are touched.
4. **Preserve Phase 07C:** Existing work on other branches or uncommitted application modifications must be strictly preserved.

> [!CAUTION]
> **Secret & Database Scan:**
> Check that no `.env`, credentials, or SQLite databases (`*.db`, `*.sqlite`) are staged. If present, remove them immediately:
> ```bash
> git reset HEAD -- .env *.db *.sqlite .local/
> ```

---

### Step 2: Run Full System Validation
Execute the comprehensive validation suite:
```bash
python3 scripts/art_harness.py validate
```
Ensure all checks pass cleanly before proceeding (Procurement workspace, bug ledger, and 264 unit tests).

---

### Step 3: Atomic Staging & Commit
1. Stage your approved contribution files:
   ```bash
   git add <target-files>
   ```
2. Commit with conventional commit format:
   ```bash
   git commit -m "docs(p0x): <descriptive summary of contribution>"
   ```

---

### Step 4: Push & Open Pull Request (Human Authorized Only)
If the user explicitly authorizes pushing to GitHub:
```bash
git push -u origin <branch-name>
gh pr create --base main --fill
```
> [!IMPORTANT]
> **No Automated Merges:** Contributor prompts and AI assistants must **never** auto-merge into `main`. Merging is strictly reserved for Project Coordinator Chiranjeevi after peer review.

---

### Step 5: Completion Report
Output a brief PR preparation summary:
```markdown
### Work Submitted / PR Prepared
- **Branch:** `<branch-name>`
- **Contributor:** <Name> (<Process ID>)
- **Files Committed:** <List of files>
- **System Validation Status:** ✅ All checks passed cleanly
- **Ready for Review:** PR created or push commands provided for user execution.
```
