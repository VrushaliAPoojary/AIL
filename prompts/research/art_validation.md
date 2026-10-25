# Antigravity Task Prompt: ART Test Execution Logging

**File:** `prompts/research/art_validation.md`  
**Purpose:** Log empirical ART agent test results, capability evaluations, and execution evidence (Harness A).

---

## Instructions for Antigravity

When instructed to "Run prompts/research/art_validation.md" with test execution details:

### Step 1: Parse Input Parameters & Enforce Process Ownership
Extract or prompt for the required test run parameters:
- **Actor:** Contributor name (`chiranjeevi`, `vrushali`, `bhushan`, `ashwin`)
- **Process ID:** Target procurement process:
  - `P01-RFP` — RFP Requirement Review & Response Coordination (Owner: `chiranjeevi`)
  - `P02-SUPPLIER-DELIVERY` — Supplier Delivery Confirmation & Delay Escalation (Owner: `vrushali`)
  - `P03-REPLENISHMENT` — Inventory Replenishment & Reorder Exceptions (Owner: `bhushan`)
  - `P04-INVOICE-EXCEPTIONS` — Invoice Discrepancy Resolution (Owner: `ashwin`)
- **Test ID:** Structured execution ID (e.g. `TEST-P02-001`)
- **Capability:** Evaluated ART capability (e.g. `Supplier Delay Escalation Trigger`)
- **Status:** Execution verdict (`PASS`, `FAIL`, `BLOCKED`, `NOT_TESTED`, `PLANNED`)
- **Notes:** Observation details, timestamps, trace notes, or blocker explanation
- **Screenshot / Evidence File (Optional):** Evidence file path (e.g. `./evidence/screenshot_01.png`)

> [!CAUTION]
> **Strict Process Ownership Guard:**
> Each contributor must record test executions strictly within their assigned process boundary. Mismatches (e.g. Vrushali logging for `P01-RFP`) are rejected.

---

### Step 2: Strict Classification & Execution Evidence Gate
You MUST strictly distinguish between three distinct test categories:

1. **Planned Tests (`PLANNED` or `NOT_TESTED`):**
   - The test scenario is specified in documentation, but has **NOT** yet been executed against a live ART agent or harness.
   - **Rule:** Never claim or record a planned test as `PASS` or `FAIL`.

2. **Actual Executions (`PASS` or `FAIL`):**
   - The test was empirically executed against an active ART agent, tool, or UI workflow.
   - **Mandatory Empirical Evidence Requirement:** Actual executions strictly require verifiable evidence:
     - An existing screenshot or artifact file path on disk, OR
     - Verifiable execution trace notes (session logs, response payload, assertions).
   - **Anti-Hallucination Guard:** Antigravity must **NEVER** claim or infer that an ART execution occurred without real empirical execution evidence. Fabricated executions are strictly rejected by the harness.

3. **Blocked Tests (`BLOCKED`):**
   - Execution was attempted or scheduled, but impeded by prerequisites, environment downtime, or missing dependencies.
   - **Rule:** Specific notes detailing the blocking reason are strictly required.

---

### Step 3: Record Test Run (Harness A)
Execute the unified harness:
```bash
python3 scripts/art_harness.py record-test \
  --actor "<contributor-username>" \
  --process-id "<Process ID>" \
  --test-id "<Test ID>" \
  --capability "<Capability>" \
  --status "<PASS|FAIL|BLOCKED|NOT_TESTED|PLANNED>" \
  --notes "<Notes / Blocker / Trace>" \
  [--screenshot "<Screenshot Path>"]
```

This updates `research/procurement/processes/<Process ID>/art-validation.md` with structured metadata and links.

### Step 4: Run Validation
Verify the test record and links conform to schema:
```bash
python3 scripts/art_harness.py validate --skip-unit-tests
```

### Step 5: Completion Report
Output a brief completion summary:
```markdown
### ART Test Run Recorded
- **Process:** <Process ID> — <Process Name>
- **Contributor:** <Actor>
- **Test ID:** <Test ID>
- **Test Category:** <Actual Execution | Planned Test | Blocked Test>
- **Capability Evaluated:** <Capability>
- **Execution Verdict:** **<PASS | FAIL | BLOCKED | PLANNED>**
- **Evidence Attached:** <Path, Trace Summary, or "N/A (Planned)">
- **Logged In:** `research/procurement/processes/<Process ID>/art-validation.md`
- **Validation Status:** ✅ Passed
```
