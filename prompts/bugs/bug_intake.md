# Antigravity Task Prompt: Bug Intake & Draft Creation

**File:** `prompts/bugs/bug_intake.md`  
**Purpose:** Create structured draft bugs from agent execution failures and screenshots, enforcing duplicate detection and evidence preservation (Harness B).

---

## Instructions for Antigravity

When instructed to "Run prompts/bugs/bug_intake.md" with an issue description or failure report:

### Step 1: Collect Required Bug Details & Verify Ownership
Ensure the following information is provided:
- **Actor:** Contributor username (`chiranjeevi`, `vrushali`, `bhushan`, `ashwin`)
- **Contributor Process Code:**
  - `P01` (Chiranjeevi: RFP Requirement Review & Response Coordination)
  - `P02` (Vrushali: Supplier Delivery Confirmation & Delay Escalation)
  - `P03` (Bhushan: Inventory Replenishment & Reorder Exceptions)
  - `P04` (Ashwin: Invoice Discrepancy Resolution)
- **Module:** Target product module (`Agent`, `Governance`, `Orchestrator`, `Serverless`, `Tool`, `AgentX`)
- **Title:** Concise summary of the bug
- **Severity:** `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`
- **Description / Repro:** Steps to reproduce, expected behavior vs observed actual behavior, operational impact
- **Evidence Files (Optional):** Attached screenshot or artifact paths

> [!CAUTION]
> **Strict Process Ownership Guard:**
> The contributor process code must match the actor's assigned scope. Mismatches (e.g. Ashwin reporting under `P01`) are rejected.

---

### Step 2: Execute Intake Harness (Harness B)
Execute draft creation via the unified harness:
```bash
python3 scripts/art_harness.py draft-bug \
  --actor "<actor-username>" \
  --contributor "<P01|P02|P03|P04>" \
  --module "<Module>" \
  --title "<Title>" \
  --desc "<Description>" \
  --severity "<Severity>" \
  [--evidence "<path1.png>" "<path2.png>"]
```

The harness guarantees:
1. **Duplicate Detection:** Scans the description against all 37 canonical bugs and active drafts. Flags near-duplicates if overlap $\ge 50\%$.
2. **Evidence Preservation:** Copies and renames all attached evidence files into the isolated draft folder with timestamped, deterministic filenames.
3. **Draft Isolation:** Allocates a safe draft identifier (`DRAFT-P0X-<MODULE>-<SEQ>`) and stores records strictly under:  
   `services/bugs-ledger/ART-Product-Validation/drafts/`  
   with status **Pending Coordinator Review**.
4. **Privilege & Human-Only Gate:**  
   - Contributors cannot allocate canonical `ART-*` IDs.
   - The AI assistant cannot mark a bug as verified or closed. Canonical sequence allocation is exclusively reserved for verified Coordinator Chiranjeevi via `prompts/admin/coordinator.md`.

---

### Step 3: Run Validation
Verify draft syntax and link integrity:
```bash
python3 scripts/art_harness.py validate --skip-unit-tests
```

### Step 4: Completion Report
Output a brief summary:
```markdown
### Draft Bug Created
- **Draft ID:** `DRAFT-P0X-<MODULE>-<SEQ>`
- **Contributor:** <Actor> (<Process Code> — <Process Name>)
- **Module:** <Module>
- **Title:** <Title>
- **Severity:** <Severity>
- **Evidence Preserved:** <Count of attached files and relative paths>
- **Duplicate Check:** Passed (overlap score: <Score>)
- **Location:** `services/bugs-ledger/ART-Product-Validation/drafts/<Folder>/`
- **Status:** **Pending Coordinator Review**
- **Next Step:** Notify Coordinator Chiranjeevi in your PR for canonical ID promotion.
```
