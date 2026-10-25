# Antigravity Task Prompt: Procurement Research Authoring

**File:** `prompts/research/research.md`  
**Purpose:** Author or update procurement process investigations, workflow steps, and grounded evidence within assigned process boundaries.

---

## Instructions for Antigravity

When instructed to "Run prompts/research/research.md" with research notes, vendor analysis, or citations:

### Step 1: Enforce Approved Scope Boundaries
Confirm the contributor and assigned directory from `research/procurement/OWNERSHIP.md`:
- **Chiranjeevi:** `P01-RFP` — RFP Requirement Review & Response Coordination $\rightarrow$ `research/procurement/processes/P01-RFP/`
- **Vrushali:** `P02-SUPPLIER-DELIVERY` — Supplier Delivery Confirmation & Delay Escalation $\rightarrow$ `research/procurement/processes/P02-SUPPLIER-DELIVERY/`
- **Bhushan:** `P03-REPLENISHMENT` — Inventory Replenishment & Reorder Exceptions $\rightarrow$ `research/procurement/processes/P03-REPLENISHMENT/`
- **Ashwin:** `P04-INVOICE-EXCEPTIONS` — Invoice Discrepancy Resolution $\rightarrow$ `research/procurement/processes/P04-INVOICE-EXCEPTIONS/`

> [!CAUTION]
> **Strict Boundary Enforcement:** You are strictly forbidden from modifying files in any other contributor's process directory or outside `research/procurement/`. Cross-process dependencies must be referenced by ID (e.g., `WF-P02-003 -> WF-P03-001`), never duplicated.

### Step 2: Apply Research & Epistemic Standards
When drafting or editing Markdown files (`investigation.md`, `evidence.md`, `workflow.md`, `art-validation.md`):
1. **Epistemic Tagging:** Adhere to `research/procurement/RESEARCH_STANDARD.md`. Tag claims with evidence tiers (`E0` to `E4`) and ambiguity tiers (`A1` to `A4`).
2. **Zero Hallucination:** Every claim must cite a public URL, standard RFP specification, ERP documentation, or physical artifact.
3. **Strict Portable Paths:** All image and document links must be strictly relative (e.g. `[Evidence](./evidence/doc.pdf)` or `![Diagram](./workflow-step-01.png)`). Never use machine-absolute `/home/...` paths.

### Step 3: Run Validation
Verify all Markdown links and directory structures resolve cleanly:
```bash
python3 scripts/art_harness.py validate --skip-unit-tests
```

### Step 4: Completion Report
Output a brief summary:
```markdown
### Research Update Complete
- **Contributor:** <Name>
- **Assigned Process:** <Process ID> — <Process Name>
- **Files Modified:**
  - `research/procurement/processes/<Process ID>/<filename>.md`
- **Citations & Findings Added:** <Brief 1-2 sentence bullet points>
- **Relative Links Check:** ✅ 100% Valid
- **Validation Status:** ✅ Passed
- **Next Step:** Run `prompts/git/submit_pr.md` when ready to stage and prepare your PR.
```
