# Antigravity Task Prompt: Bug Retest Verification

**File:** `prompts/bugs/retest.md`  
**Purpose:** Record verification and retest outcomes against existing canonical bugs while preserving lifecycle integrity and human-only verification requirements (Harness B).

---

## Instructions for Antigravity

When instructed to "Run prompts/bugs/retest.md" with retest results:

### Step 1: Parse Retest Inputs & Enforce Human-Only Verification
Ensure the following parameters are provided:
- **Canonical Bug ID:** Target bug (e.g. `ART-AGENT-001`, `ART-GOV-004`)
- **Actor:** Human contributor username (`chiranjeevi`, `vrushali`, `bhushan`, `ashwin`)
- **Actor Role:** Must be `HUMAN`. (AI actors are strictly forbidden).
- **Verdict:** One of `PASSED`, `FAILED`, `INCONCLUSIVE`, `VERIFIED`
- **Notes:** Detailed observations, test environment, timestamps, and findings
- **Evidence Files (Optional):** Attached retest screenshots or reproduction logs

> [!CAUTION]
> **Human-Only Verification Requirement:**
> The AI assistant is **strictly forbidden** from self-certifying bug verification, marking a defect as `VERIFIED`, or closing lifecycle states autonomously. Verification must be executed and affirmed by a verified human contributor. Requests declaring an AI actor role are blocked.

---

### Step 2: Execute Retest Harness (Harness B)
Execute retest recording via the unified harness:
```bash
python3 scripts/art_harness.py retest \
  --bug-id "<Bug ID>" \
  --actor "<human-username>" \
  --actor-role HUMAN \
  --verdict "<PASSED|FAILED|INCONCLUSIVE|VERIFIED>" \
  --notes "<Notes>" \
  [--evidence "<path1.png>"]
```

The harness guarantees:
1. **Historical Preservation:** Locates the canonical bug record in `services/bugs-ledger/ART-Product-Validation/bugs/` and updates **only** the `## Retest` section. Historical root causes, developer fix proposals, original reproduction steps, and historical evidence are strictly preserved.
2. **Lifecycle State Machine:** Transitions status according to existing lifecycle rules:
   - `PASSED` / `VERIFIED` $\rightarrow$ `RESOLVED` / `VERIFIED`
   - `FAILED` $\rightarrow$ `REOPENED`
   - `INCONCLUSIVE` $\rightarrow$ `RETEST`
3. **Evidence Preservation:** Retest screenshots and logs are linked into the bug record.

---

### Step 3: Run Validation
Verify the updated bug record and links:
```bash
python3 scripts/art_harness.py validate --skip-unit-tests
```

### Step 4: Completion Report
Output a brief summary:
```markdown
### Retest Verification Recorded
- **Target Bug:** <Bug ID>
- **Human Tester:** <Actor>
- **Verification Verdict:** **<Verdict>**
- **Updated Status:** <New Status>
- **Notes Summary:** <Notes>
- **Evidence Attached:** <Count of files or "None">
- **Validation Status:** ✅ Passed
- **Next Step:** Run `prompts/git/submit_pr.md` to stage and commit your retest update.
```
