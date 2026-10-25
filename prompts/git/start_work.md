# Antigravity Task Prompt: Start Work & Session Bootstrap

**File:** `prompts/git/start_work.md`  
**Purpose:** Initialize daily contributor work session, synchronize branch with `main`, and verify local environment readiness.

---

## Instructions for Antigravity

When instructed to "Run prompts/git/start_work.md" (or "Start work on P0X", "Begin session as <Name>"):

### Step 1: Identify Contributor & Approved Process Scope
Determine the contributor's identity and assigned process based on user prompt or current context:
- **Chiranjeevi (`Chiranjeevi005`):** Project Coordinator & Process `P01-RFP` — RFP Requirement Review & Response Coordination  
  - *Branch:* `research/chiranjeevi`  
  - *Scope:* `research/procurement/processes/P01-RFP/`
- **Vrushali (`VrushaliAPoojary`):** Process Owner `P02-SUPPLIER-DELIVERY` — Supplier Delivery Confirmation & Delay Escalation  
  - *Branch:* `research/vrushali`  
  - *Scope:* `research/procurement/processes/P02-SUPPLIER-DELIVERY/`
- **Bhushan (`BhushanShenoy07`):** Process Owner `P03-REPLENISHMENT` — Inventory Replenishment & Reorder Exceptions  
  - *Branch:* `research/bhushan`  
  - *Scope:* `research/procurement/processes/P03-REPLENISHMENT/`
- **Ashwin (`ashwinash19`):** Process Owner `P04-INVOICE-EXCEPTIONS` — Invoice Discrepancy Resolution  
  - *Branch:* `research/ashwin`  
  - *Scope:* `research/procurement/processes/P04-INVOICE-EXCEPTIONS/`

If unspecified, ask the contributor to confirm their name and assigned process ID.

### Step 2: Read Context & Verify Git State
1. Check current Git status:
   ```bash
   git status
   ```
2. Verify existing work is clean or committed. (Never discard uncommitted work).
3. If switching branches, ensure no uncommitted files collide. Fetch latest `main`:
   ```bash
   git fetch origin main
   ```
4. Safe, non-destructive branch checkout (never use `checkout -B` or `reset --hard`, which destroy unpushed contributor commits):
   ```bash
   git checkout research/<contributor-name>
   ```

### Step 3: Verify Local Validation Baseline
Run baseline validation using the unified harness:
```bash
python3 scripts/art_harness.py validate --skip-unit-tests
```

### Step 4: Completion Report
Output a brief session bootstrap summary:
```markdown
### Session Initialized: <Contributor Name>
- **Assigned Process:** <Process ID> — <Process Name>
- **Working Directory:** `research/procurement/processes/<Process ID>/`
- **Active Git Branch:** `research/<contributor-name>`
- **Environment Status:** ✅ Clean & Validated
- **Next Step:** You are ready to research (`prompts/research/research.md`), test (`prompts/research/art_validation.md`), or log bugs (`prompts/bugs/bug_intake.md`).
```
