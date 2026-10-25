# ART Investigation Lab — Contributor Guide

> **Audience:** Research & Validation Contributors (Vrushali, Bhushan, Ashwin, and Chiranjeevi as P01 Owner)  
> **Prerequisites:** Python 3.11+, Git, Antigravity IDE  

This guide provides concrete, copy-pasteable commands, expected outputs, and troubleshooting steps for all day-to-day contributor activities.

---

## 1. Daily Setup & Workflow

### Start of Work Session
```bash
git checkout main
git pull origin main
git checkout -b research/<your-name>  # e.g., research/vrushali
```

### End of Work Session
```bash
# 1. Run local validation
python3 scripts/art_harness.py validate

# 2. Stage only your assigned process files
git add research/procurement/processes/P0X-.../
# (or draft bug / validation files)

# 3. Commit with semantic message
git commit -m "docs(p02): add supplier delay escalation evidence and workflow diagram"

# 4. Push branch and open Pull Request
git push -u origin research/<your-name>
gh pr create --base main --fill
```

---

## 2. Activity Guides & Command Reference

### A. Authoring Research in Your Process Directory
1. Work **only** within your directory:
   - Chiranjeevi (`Chiranjeevi005`) $\rightarrow$ `research/procurement/processes/P01-RFP/`
   - Vrushali (`VrushaliAPoojary`) $\rightarrow$ `research/procurement/processes/P02-SUPPLIER-DELIVERY/`
   - Bhushan (`BhushanShenoy07`) $\rightarrow$ `research/procurement/processes/P03-REPLENISHMENT/`
   - Ashwin (`ashwinash19`) $\rightarrow$ `research/procurement/processes/P04-INVOICE-EXCEPTIONS/`
2. Add evidence citations with verified URLs or verbatim quotes.
3. Keep all image and document references **strictly relative** (e.g. `![Workflow](./diagram.png)`).

---

### B. Recording an ART Test Execution (Harness A)
When you run a validation scenario against an ART agent or workflow:

```bash
python3 scripts/art_harness.py record-test \
  --process-id P02-SUPPLIER-DELIVERY \
  --opportunity-id OPP-002-01 \
  --run-id RUN-$(date +%Y%m%d)-01 \
  --actor vrushali \
  --verdict PASS \
  --summary "Validated delivery confirmation agent properly flags 48h lead-time breach."
```

**Expected Output:**
```text
✅ ART test run recorded successfully: RUN-20261008-01 (PASS) in research/procurement/validation/ART_TEST_LOG.md
```

---

### C. Logging an ART Execution Anomaly / Bug (Harness B)
If you encounter an ART failure, schema breach, or agent bug:

```bash
python3 scripts/art_harness.py draft-bug \
  --author P03 \
  --module Agent \
  --title "Replenishment agent fails to parse split invoice line items" \
  --severity HIGH \
  --description "Agent output parser drops item lines 5-10 when table contains merged cells."
```

**Expected Output:**
```text
✅ Draft bug created: DRAFT-P03-AGENT-001
   Location: services/bugs-ledger/ART-Product-Validation/bugs/Agent Lab/drafts/DRAFT-P03-AGENT-001.md
   Duplicate Check: PASSED (similarity score 0.12, no duplicate found)
   Status: Pending Coordinator Review
```

> [!TIP]
> **Duplicate Detection:** The harness automatically runs duplicate detection against all existing canonical bugs and active drafts. If a similarity score exceeds 0.85, you will be warned with the existing bug ID.

---

### D. Submitting a Fix Retest (Harness B)
When verifying a fix for an existing bug:

```bash
python3 scripts/art_harness.py retest \
  --bug-id ART-AGENT-001 \
  --tester ashwin \
  --verdict VERIFIED_FIXED \
  --notes "Re-tested output parser against 50 complex JSON responses. Zero violations observed."
```

**Expected Output:**
```text
✅ Retest recorded for ART-AGENT-001: VERIFIED_FIXED
   Updated frontmatter in ART-AGENT-001.md
   Status updated: RESOLVED
```

---

### E. Pre-Submission Local Validation
Always run the validation suite before pushing:

```bash
python3 scripts/art_harness.py validate
```

**Expected Output:**
```text
============================================================
ART INVESTIGATION LAB — UNIFIED SYSTEM VALIDATION
============================================================
[1/3] Validating Procurement Research Workspace...
✅ Procurement workspace validation PASSED
[2/3] Validating ART Bugs Ledger & Evidence Links...
✅ Bugs ledger validation PASSED
[3/3] Running Bugs Ledger Unit Tests (pytest)...
✅ All 264 unit tests PASSED
============================================================
🎉 ALL VALIDATIONS PASSED CLEANLY
```

---

## 3. Common Errors & Troubleshooting

| Error Symptom | Cause | Solution |
| :--- | :--- | :--- |
| `Scope Boundary Violation: File outside assigned process` | You edited files in another member's folder or in `src/` | Restore those files using `git restore <file>` |
| `Broken relative link: ./image.png not found` | The referenced file does not exist at that path | Ensure the evidence asset is saved in the same directory |
| `Absolute path rejected: /home/...` | Markdown contains host-specific absolute paths | Change `/home/user/.../file.png` to `./file.png` |
| `Filename too long (unable to create file ...)` | Windows 260-char path length limitation | Run `git config core.longpaths true` then `git restore --source=HEAD :/` |
| `npm.ps1 cannot be loaded (script execution disabled)` | Windows PowerShell script execution policy | Use `npm.cmd` directly in PowerShell (e.g. `npm.cmd ci`, `npm.cmd test`) |
| `UnicodeEncodeError: 'charmap' codec can't encode ...` | Windows console default cp1252 codepage | Set `$env:PYTHONUTF8 = "1"` in PowerShell before running Python commands |
| `Permission Denied: Only coordinator may promote` | You attempted to run `promote-bug` without coordinator authorization | Canonical ID promotion is restricted to verified Project Coordinator Chiranjeevi |
| `Duplicate Bug Warning: Similarity > 0.85` | A bug with almost identical wording already exists | Inspect the existing bug ID and append your notes to it instead |
