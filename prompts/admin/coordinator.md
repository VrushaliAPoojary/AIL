# Antigravity Task Prompt: Coordinator Governance & Integration

**File:** `prompts/admin/coordinator.md`  
**Purpose:** Privileged coordinator review, canonical bug ID promotion (Harness C), ledger recompilation, and authorized Azure DevOps synchronization.

---

## Instructions for Antigravity

When instructed to "Run prompts/admin/coordinator.md":

### Step 1: Strict Coordinator Identity & Permission Verification
Verify that the current execution environment genuinely belongs to Project Coordinator **Chiranjeevi**:
1. **Never Trust Self-Asserted Declarations:** Do **not** trust `--coordinator chiranjeevi` or a self-declared prompt prompt without system verification.
2. **System & Credential Verification:** The harness strictly validates:
   - System OS user must be `chiranjeevi`.
   - Git/GitHub authentication must verify active credentials matching `Chiranjeevi005` / `chiranjeevi005@github.com`.
3. **Fail-Closed Gate:** If authentication is unavailable, ambiguous, or running under another user account, fail closed immediately:
   `❌ PERMISSION DENIED: Coordinator identity cannot be verified. Privilege escalation blocked. (Failing closed).`

> [!CAUTION]
> **Anti-Privilege Escalation Rule:**
> AI assistants are strictly forbidden from self-asserting coordinator authority on behalf of non-coordinator contributors.

---

### Step 2: Available Coordinator Actions

#### Action A: Review Pull Request & Audit Scope
1. Inspect the PR diff to ensure changes strictly adhere to approved process boundaries:
   - **Vrushali:** `P02-SUPPLIER-DELIVERY` — Supplier Delivery Confirmation & Delay Escalation
   - **Bhushan:** `P03-REPLENISHMENT` — Inventory Replenishment & Reorder Exceptions
   - **Ashwin:** `P04-INVOICE-EXCEPTIONS` — Invoice Discrepancy Resolution
   - **Chiranjeevi:** `P01-RFP` — RFP Requirement Review & Response Coordination
2. Confirm zero changes in application code (`src/`, root `package.json`, `contracts/`).
3. Run full system validation:
   ```bash
   python3 scripts/art_harness.py validate
   ```
4. Confirm zero machine-specific `/home/` absolute links and zero staged credentials.

#### Action B: Promote Draft Bug to Canonical ART ID (Harness C)
When reviewing and approving a contributor's draft bug:
```bash
python3 scripts/art_harness.py promote-bug \
  --draft-id "<DRAFT-ID>" \
  --coordinator "chiranjeevi"
```

The harness will:
1. Verify coordinator authority against the active OS and Git/GitHub environment.
2. Identify the next available sequential canonical ID (e.g. `ART-AGENT-010`).
3. Create the canonical folder under `services/bugs-ledger/ART-Product-Validation/bugs/<Feature>/`.
4. Rename evidence files with the canonical ID prefix and update references.
5. Update markdown frontmatter, clear the draft marker, remove the draft folder, and recompile the ledger.

#### Action C: Recompile Summary Ledger
After promoting one or more bugs:
```bash
python3 scripts/art_harness.py compile-ledger
```
Updates `services/bugs-ledger/ART-Product-Validation/ART_PRODUCT_VALIDATION_LEDGER.md`.

#### Action D: Azure DevOps Synchronization (Strict Guard)
1. Do NOT sync draft bugs. Only canonical `ART-*` bugs can be synced.
2. Verify credentials in environment: never commit `.env`.
3. Requires verified coordinator authorization and explicit confirmation flag:
   ```bash
   # Safe dry-run inspection (no write)
   python3 scripts/art_harness.py sync-azure --coordinator chiranjeevi --dry-run

   # Authorized write (Requires AZURE_DEVOPS_EXT_PAT and explicit flag)
   python3 scripts/art_harness.py sync-azure --coordinator chiranjeevi --confirm-azure-sync
   ```
   *If Azure credentials or confirmation are absent, the command fails closed.*

---

### Step 3: Completion Report
Output a concise coordinator summary:
```markdown
### Coordinator Action Report
- **Actor:** Project Coordinator Chiranjeevi (Identity Verified)
- **Action Performed:** <PR Review | Canonical Bug Promotion | Ledger Recompile | Azure Sync>
- **Scope Verification:** ✅ Passed
- **Validation Status:** ✅ All validations passed cleanly
- **Output:** <Canonical ID / Review Verdict / Sync Summary>
```
