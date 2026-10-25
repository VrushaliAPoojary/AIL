"""
tests/test_public_report.py

Comprehensive test suite for Harness 04 (ART Public Validation Report Publisher).
Validates all requirements including Azure State separation and tests A through F:
TEST A: Azure State: Resolved, ART Status: RETEST, Retest: Required, Developer Comment: Fixed. Please verify.
TEST B: Azure State: Closed, ART Status: FIXING (no silent reconciliation).
TEST C: Azure State: New, ART Status: OPEN.
TEST D: Azure State unavailable -> fallback to '—' (no inference).
TEST E: Future Azure state: 'Ready for Deployment' (not rejected by enum).
TEST F: Azure State filter dynamically matches states represented in report.
Plus tests 1-15:
1. Legacy 6-column table parses.
2. 7-column Owner table parses.
3. Owner is absent from public HTML.
4. Summary mismatch fails.
5. Duplicate Bug ID fails.
6. Private Markdown links are removed.
7. HTML/script-like values are escaped.
8. Azure IDs/URLs are absent.
9. Meaningful lifecycle timestamp is preferred over Last Azure Sync.
10. Search + Status + Feature + Severity + Azure State filters work together.
11. Source ledger/canonical bugs/SQLite remain unchanged.
12. Repeat generation does not duplicate data.
13. Generated page uses the required light theme.
"""

import os
import re
import shutil
import tempfile
import unittest
import hashlib

from core.reporting.public_report import (
    PublicReportGenerator,
)


SAMPLE_6_COLUMN_LEDGER = """# ART Product Validation Ledger

## Summary

- **Total Bugs:** 2
- **Open:** 1
- **Fixing:** 0
- **Retest:** 0
- **Verified:** 0
- **Closed:** 0
- **Blocked:** 1

## Bugs

| Bug ID | Title | Severity | Status | Developer Update | Retest |
| --- | --- | --- | --- | --- | --- |
| [ART-TOOL-001](<bugs/Tool%20Builder/ART-TOOL-001/ART-TOOL-001.md>) | Tool Builder: Added HTTPS Schema Fields Cannot Be Deleted | MEDIUM | OPEN | Pending. | Pending. |
| [ART-TOOL-003](<bugs/Tool%20Builder/ART-TOOL-003/ART-TOOL-003.md>) | Tool Builder existing tools cannot be edited | HIGH | BLOCKED | PRODUCT_DECISION_PENDING: Decision pending. | Not Required |

## Azure Resolution & Lifecycle Tracking

| Bug ID | Feature | Azure ID | Azure State | Azure Reason | ART Disposition | Retest Required | Action Required | Last Azure Sync | Resolution Summary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ART-TOOL-003 | Tool Builder | #68991 | Resolved | Fixed | PRODUCT_DECISION_PENDING | NO | AWAIT_PRODUCT_DECISION | 2026-10-12T06:23:35+00:00 | Editing prohibition is intentional... |
"""


SAMPLE_7_COLUMN_LEDGER = """# ART Product Validation Ledger

## Summary

- **Total Bugs:** 3
- **Open:** 1
- **Fixing:** 0
- **Retest:** 1
- **Verified:** 0
- **Closed:** 0
- **Blocked:** 1

## Bugs

| Bug ID | Title | Severity | Status | Owner | Developer Update | Retest |
| --- | --- | --- | --- | --- | --- | --- |
| [ART-TOOL-001](<bugs/Tool%20Builder/ART-TOOL-001/ART-TOOL-001.md>) | Tool Builder: Added HTTPS Schema Fields Cannot Be Deleted | MEDIUM | OPEN | Unassigned | OPEN: Issue remains open in Azure with no implementation or resolution claim established. | Pending. |
| [ART-AGENT-006](<bugs/Agent%20Lab/ART-AGENT-006/ART-AGENT-006.md>) | Agent Output Schema Allowed Values Are Not Strictly Enforced | HIGH | RETEST | Chiranjeevi P.K | Fixed. Please verify. | Required |
| [ART-TOOL-003](<bugs/Tool%20Builder/ART-TOOL-003/ART-TOOL-003.md>) | Tool Builder existing tools cannot be edited | HIGH | BLOCKED | Anusha Ganesh Hegde | PRODUCT_DECISION_PENDING: Editing prohibition is intentional for now. | Not Required |

## Azure Resolution & Lifecycle Tracking

| Bug ID | Feature | Azure ID | Azure State | Azure Reason | ART Disposition | Retest Required | Action Required | Last Azure Sync | Resolution Summary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ART-AGENT-006 | Agent Lab | #68876 | Resolved | Fixed | RETEST_REQUIRED | YES | RETEST | 2026-10-13T03:33:56.982232+00:00 | Fixed. Please verify. |
| ART-TOOL-003 | Tool Builder | #68991 | Resolved | Fixed | PRODUCT_DECISION_PENDING | NO | AWAIT_PRODUCT_DECISION | 2026-10-13T03:33:31.940884+00:00 | Editing prohibition is intentional... |
"""


class TestPublicReportRefinement(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.ledger_path = os.path.join(self.test_dir, "ART_PRODUCT_VALIDATION_LEDGER.md")
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            f.write(SAMPLE_7_COLUMN_LEDGER)

        self.output_path = os.path.join(self.test_dir, "docs", "index.html")
        self.generator = PublicReportGenerator(repo_root=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_01_legacy_6_column_parses(self):
        """1. Legacy 6-column table parses."""
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            f.write(SAMPLE_6_COLUMN_LEDGER)

        res = self.generator.generate_report(ledger_path=self.ledger_path, output_path=self.output_path)
        self.assertTrue(res.success)
        self.assertTrue(res.six_column_compatibility_ok)
        self.assertIsNone(res.blocker)

        with open(self.output_path, "r", encoding="utf-8") as f:
            html_text = f.read()

        self.assertIn("ART-TOOL-001", html_text)
        self.assertIn("ART-TOOL-003", html_text)

    def test_02_7_column_owner_parses(self):
        """2. 7-column Owner table parses."""
        res = self.generator.generate_report(ledger_path=self.ledger_path, output_path=self.output_path)
        self.assertTrue(res.success)
        self.assertTrue(res.seven_column_owner_compatibility_ok)
        self.assertIsNone(res.blocker)

        with open(self.output_path, "r", encoding="utf-8") as f:
            html_text = f.read()

        self.assertIn("ART-TOOL-001", html_text)
        self.assertIn("ART-AGENT-006", html_text)
        self.assertIn("ART-TOOL-003", html_text)

    def test_03_owner_absent_from_public_html(self):
        """3. Owner is absent from public HTML."""
        res = self.generator.generate_report(ledger_path=self.ledger_path, output_path=self.output_path)
        self.assertTrue(res.success)
        self.assertTrue(res.owner_privacy_ok)

        with open(self.output_path, "r", encoding="utf-8") as f:
            html_text = f.read()

        self.assertNotIn("Chiranjeevi P.K", html_text)
        self.assertNotIn("Anusha Ganesh Hegde", html_text)
        self.assertNotIn("<th>Owner</th>", html_text)
        self.assertNotIn(">Owner<", html_text)

    def test_04_summary_mismatch_fails(self):
        """4. Summary mismatch fails."""
        mismatch_ledger = SAMPLE_7_COLUMN_LEDGER.replace("- **Open:** 1", "- **Open:** 2")
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            f.write(mismatch_ledger)

        res = self.generator.generate_report(ledger_path=self.ledger_path, output_path=self.output_path)
        self.assertFalse(res.success)
        self.assertIsNotNone(res.blocker)
        assert res.blocker is not None
        self.assertIn("LEDGER SUMMARY INCONSISTENCY", res.blocker)

    def test_05_duplicate_bug_id_fails(self):
        """5. Duplicate Bug ID fails."""
        duplicate_ledger = SAMPLE_7_COLUMN_LEDGER.replace(
            "| [ART-TOOL-001](<bugs/Tool%20Builder/ART-TOOL-001/ART-TOOL-001.md>) | Tool Builder: Added HTTPS Schema Fields Cannot Be Deleted | MEDIUM | OPEN | Unassigned | OPEN: Issue remains open in Azure with no implementation or resolution claim established. | Pending. |",
            "| [ART-TOOL-001](<bugs/Tool%20Builder/ART-TOOL-001/ART-TOOL-001.md>) | Tool Builder: Added HTTPS Schema Fields Cannot Be Deleted | MEDIUM | OPEN | Unassigned | OPEN: Issue remains open in Azure with no implementation or resolution claim established. | Pending. |\n| [ART-TOOL-001](<bugs/Tool%20Builder/ART-TOOL-001/ART-TOOL-001.md>) | Duplicate Row | MEDIUM | OPEN | Unassigned | Duplicate. | Pending. |",
        ).replace("- **Total Bugs:** 3", "- **Total Bugs:** 4").replace("- **Open:** 1", "- **Open:** 2")
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            f.write(duplicate_ledger)

        res = self.generator.generate_report(ledger_path=self.ledger_path, output_path=self.output_path)
        self.assertFalse(res.success)
        self.assertIsNotNone(res.blocker)
        assert res.blocker is not None
        self.assertIn("DUPLICATE BUG ID", res.blocker)

    def test_06_private_markdown_links_removed(self):
        """6. Private Markdown links are removed."""
        res = self.generator.generate_report(ledger_path=self.ledger_path, output_path=self.output_path)
        self.assertTrue(res.success)

        with open(self.output_path, "r", encoding="utf-8") as f:
            html_text = f.read()

        self.assertIn("<code>ART-TOOL-001</code>", html_text)
        self.assertNotIn("bugs/Tool%20Builder", html_text)
        self.assertNotIn("ART-TOOL-001.md", html_text)
        self.assertNotIn(".md", html_text)

    def test_07_html_injection_escaped(self):
        """7. HTML/script-like values are escaped."""
        injection_ledger = SAMPLE_7_COLUMN_LEDGER.replace(
            "Tool Builder: Added HTTPS Schema Fields Cannot Be Deleted",
            "XSS Attack <script>alert('pwned')</script> &amp; \"quote\" <img src=x onerror=alert(1)>",
        )
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            f.write(injection_ledger)

        res = self.generator.generate_report(ledger_path=self.ledger_path, output_path=self.output_path)
        self.assertTrue(res.success)

        with open(self.output_path, "r", encoding="utf-8") as f:
            html_text = f.read()

        self.assertNotIn("<script>alert('pwned')</script>", html_text)
        self.assertNotIn("<img src=x onerror=alert(1)>", html_text)
        self.assertIn("&lt;script&gt;alert(&#x27;pwned&#x27;)&lt;/script&gt;", html_text)

    def test_08_azure_ids_and_urls_absent(self):
        """8. Azure IDs/URLs are absent."""
        res = self.generator.generate_report(ledger_path=self.ledger_path, output_path=self.output_path)
        self.assertTrue(res.success)

        with open(self.output_path, "r", encoding="utf-8") as f:
            html_text = f.read()

        self.assertNotIn("dev.azure.com", html_text)
        self.assertNotIn("#68876", html_text)
        self.assertNotIn("#68991", html_text)

    def test_09_meaningful_lifecycle_timestamp_preferred(self):
        """9. Meaningful lifecycle timestamp is preferred over Last Azure Sync."""
        bug_dir = os.path.join(self.test_dir, "bugs", "Agent Lab", "ART-AGENT-006")
        os.makedirs(bug_dir, exist_ok=True)
        canonical_md_path = os.path.join(bug_dir, "ART-AGENT-006.md")
        with open(canonical_md_path, "w", encoding="utf-8") as f:
            f.write(
                "# ART-AGENT-006\n\n"
                "- **Canonical Bug ID:** ART-AGENT-006\n"
                "- **Status:** RETEST\n\n"
                "## Resolution Status\n\n"
                "- **ART Disposition:** RETEST_REQUIRED\n"
                "- **Latest Lifecycle Update:** 2026-10-12T10:59:12.793Z\n"
                "- **Last Azure Sync:** 2026-10-13T03:33:56.982232+00:00\n"
            )

        res = self.generator.generate_report(ledger_path=self.ledger_path, output_path=self.output_path)
        self.assertTrue(res.success)

        with open(self.output_path, "r", encoding="utf-8") as f:
            html_text = f.read()

        self.assertIn("2026-10-12 16:29 IST", html_text)
        self.assertNotIn("2026-10-13 09:03 IST", html_text)
        self.assertIn("Not Available", html_text)

    def test_10_filters_and_search_ui(self):
        """10. Search + Status + Feature + Severity + Azure State filters work together."""
        res = self.generator.generate_report(ledger_path=self.ledger_path, output_path=self.output_path)
        self.assertTrue(res.success)

        with open(self.output_path, "r", encoding="utf-8") as f:
            html_text = f.read()

        self.assertIn('id="search-input"', html_text)
        self.assertIn('id="azure-state-filter"', html_text)
        self.assertIn('id="status-filter"', html_text)
        self.assertIn('id="feature-filter"', html_text)
        self.assertIn('id="severity-filter"', html_text)
        self.assertIn('id="reset-filters"', html_text)
        self.assertIn('id="results-count"', html_text)
        self.assertIn('id="visible-count"', html_text)
        self.assertIn('id="total-count"', html_text)

        self.assertIn('data-id="ART-TOOL-001"', html_text)
        self.assertIn('data-feature="Tool Builder"', html_text)
        self.assertIn('data-severity="MEDIUM"', html_text)
        self.assertIn('data-azure-state="—"', html_text)
        self.assertIn('data-status="OPEN"', html_text)

        self.assertIn("matchesAzureState", html_text)

    def test_11_source_immutability(self):
        """11. Source ledger/canonical bugs/SQLite remain unchanged."""
        with open(self.ledger_path, "rb") as f:
            before_hash = hashlib.sha256(f.read()).hexdigest()

        res = self.generator.generate_report(ledger_path=self.ledger_path, output_path=self.output_path)
        self.assertTrue(res.success)
        self.assertTrue(res.source_immutability_ok)
        self.assertEqual(res.ledger_mutations, 0)
        self.assertEqual(res.azure_mutations, 0)
        self.assertEqual(res.sqlite_mutations, 0)
        self.assertFalse(res.h03_files_modified)
        self.assertFalse(res.azure_contacted)

        with open(self.ledger_path, "rb") as f:
            after_hash = hashlib.sha256(f.read()).hexdigest()

        self.assertEqual(before_hash, after_hash)

    def test_12_repeat_generation_no_duplicates(self):
        """12. Repeat generation does not duplicate data."""
        res1 = self.generator.generate_report(ledger_path=self.ledger_path, output_path=self.output_path)
        self.assertTrue(res1.success)
        with open(self.output_path, "r", encoding="utf-8") as f:
            html1 = f.read()

        res2 = self.generator.generate_report(ledger_path=self.ledger_path, output_path=self.output_path)
        self.assertTrue(res2.success)
        with open(self.output_path, "r", encoding="utf-8") as f:
            html2 = f.read()

        h1_clean = re.sub(r'id="gen-time">[^<]+</span>', "", html1)
        h2_clean = re.sub(r'id="gen-time">[^<]+</span>', "", html2)
        self.assertEqual(h1_clean, h2_clean)

    def test_13_light_corporate_theme(self):
        """13. Generated page uses the required light theme."""
        res = self.generator.generate_report(ledger_path=self.ledger_path, output_path=self.output_path)
        self.assertTrue(res.success)
        self.assertTrue(res.light_theme_ok)

        with open(self.output_path, "r", encoding="utf-8") as f:
            html_text = f.read()

        self.assertIn("--bg: #f8fafc;", html_text)
        self.assertIn("--card-bg: #ffffff;", html_text)
        self.assertIn("--text-main: #0f172a;", html_text)
        self.assertIn("--accent: #0891b2;", html_text)

        self.assertIn("<h1>ART Product Validation</h1>", html_text)
        self.assertIn("<p>Product Quality & Resolution Dashboard</p>", html_text)

        self.assertIn(
            "Report reflects the latest lifecycle data synchronized into the ART validation ledger.",
            html_text,
        )
        self.assertNotIn("background-color: #0f172a;", html_text)

    # =========================================================================
    # REFINEMENT TESTS A - F: Azure State & Separation of Concerns
    # =========================================================================

    def test_a_azure_state_art_status_developer_comment(self):
        """
        TEST A
        Lifecycle:
        Azure State: Resolved
        ART Status: RETEST
        Retest: Required
        Developer Comment: Fixed. Please verify.
        Expected dashboard:
        Azure State = Resolved
        ART Status = RETEST
        Retest = Required
        Developer Comment = Fixed. Please verify.
        """
        res = self.generator.generate_report(ledger_path=self.ledger_path, output_path=self.output_path)
        self.assertTrue(res.success)
        self.assertTrue(res.azure_state_source_ok)
        self.assertTrue(res.azure_state_fidelity_ok)
        self.assertTrue(res.azure_art_status_separation_ok)

        with open(self.output_path, "r", encoding="utf-8") as f:
            html_text = f.read()

        # Check that row ART-AGENT-006 has all four distinct fields rendered
        row_match = re.search(r'<tr[^>]*data-id="ART-AGENT-006"[^>]*>(.*?)</tr>', html_text, flags=re.DOTALL)
        self.assertIsNotNone(row_match)
        row_content = row_match.group(1)

        self.assertIn('<span class="badge badge-azure">Resolved</span>', row_content)
        self.assertIn('<span class="badge badge-retest">RETEST</span>', row_content)
        self.assertIn('Required', row_content)
        self.assertIn('Fixed. Please verify.', row_content)

    def test_b_unreconciled_azure_closed_art_fixing(self):
        """
        TEST B
        Azure State: Closed
        ART Status: FIXING
        Expected: both values remain unchanged. Harness 04 must not reconcile them.
        """
        fixture_ledger = """# ART Product Validation Ledger

## Summary

- **Total Bugs:** 1
- **Open:** 0
- **Fixing:** 1
- **Retest:** 0
- **Verified:** 0
- **Closed:** 0
- **Blocked:** 0

## Bugs

| Bug ID | Title | Severity | Status | Owner | Developer Comment | Retest |
| --- | --- | --- | --- | --- | --- | --- |
| [ART-AGENTX-001](<bugs/Agent%20X/ART-AGENTX-001/ART-AGENTX-001.md>) | Agent X auth padding error | LOW | FIXING | Unassigned | Fixed. | Not Required |

## Azure Resolution & Lifecycle Tracking

| Bug ID | Feature | Azure ID | Azure State | Azure Reason | ART Disposition | Retest Required | Action Required | Last Azure Sync | Resolution Summary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ART-AGENTX-001 | Agent X | #68969 | Closed | Fixed and verified | FIX_CLAIMED | NO | AWAIT_DEVELOPER | 2026-10-13T03:34:03+00:00 | Fixed |
"""
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            f.write(fixture_ledger)

        res = self.generator.generate_report(ledger_path=self.ledger_path, output_path=self.output_path)
        self.assertTrue(res.success)
        self.assertTrue(res.azure_art_status_separation_ok)

        with open(self.output_path, "r", encoding="utf-8") as f:
            html_text = f.read()

        row_match = re.search(r'<tr[^>]*data-id="ART-AGENTX-001"[^>]*>(.*?)</tr>', html_text, flags=re.DOTALL)
        self.assertIsNotNone(row_match)
        row_content = row_match.group(1)

        # Both values remain exactly as provided without silent reconciliation
        self.assertIn('<span class="badge badge-azure">Closed</span>', row_content)
        self.assertIn('<span class="badge badge-fixing">FIXING</span>', row_content)

    def test_c_azure_state_new_art_status_open(self):
        """
        TEST C
        Azure State: New
        ART Status: OPEN
        Expected: Azure State = New, ART Status = OPEN
        """
        fixture_ledger = """# ART Product Validation Ledger

## Summary

- **Total Bugs:** 1
- **Open:** 1
- **Fixing:** 0
- **Retest:** 0
- **Verified:** 0
- **Closed:** 0
- **Blocked:** 0

## Bugs

| Bug ID | Title | Severity | Status | Owner | Developer Comment | Retest |
| --- | --- | --- | --- | --- | --- | --- |
| [ART-ADK-001](<bugs/ADK/ART-ADK-001/ART-ADK-001.md>) | ADK upload fails 402 | HIGH | OPEN | Unassigned | — | Pending |

## Azure Resolution & Lifecycle Tracking

| Bug ID | Feature | Azure ID | Azure State | Azure Reason | ART Disposition | Retest Required | Action Required | Last Azure Sync | Resolution Summary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ART-ADK-001 | ADK | #69122 | New | New | OPEN | NO | AWAIT_DEVELOPER | 2026-10-12T06:44:54+00:00 | Pending |
"""
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            f.write(fixture_ledger)

        res = self.generator.generate_report(ledger_path=self.ledger_path, output_path=self.output_path)
        self.assertTrue(res.success)

        with open(self.output_path, "r", encoding="utf-8") as f:
            html_text = f.read()

        row_match = re.search(r'<tr[^>]*data-id="ART-ADK-001"[^>]*>(.*?)</tr>', html_text, flags=re.DOTALL)
        self.assertIsNotNone(row_match)
        row_content = row_match.group(1)

        self.assertIn('<span class="badge badge-azure">New</span>', row_content)
        self.assertIn('<span class="badge badge-open">OPEN</span>', row_content)

    def test_d_azure_state_unavailable_fallback(self):
        """
        TEST D
        Azure State unavailable.
        Expected: Azure State = —, No inference.
        """
        # In SAMPLE_7_COLUMN_LEDGER, ART-TOOL-001 is NOT present in ## Azure Resolution & Lifecycle Tracking
        res = self.generator.generate_report(ledger_path=self.ledger_path, output_path=self.output_path)
        self.assertTrue(res.success)
        self.assertTrue(res.azure_state_fallback_ok)

        with open(self.output_path, "r", encoding="utf-8") as f:
            html_text = f.read()

        row_match = re.search(r'<tr[^>]*data-id="ART-TOOL-001"[^>]*>(.*?)</tr>', html_text, flags=re.DOTALL)
        self.assertIsNotNone(row_match)
        row_content = row_match.group(1)

        # Must display em dash "—" and NOT infer "New" from OPEN status
        self.assertIn('<span class="badge badge-azure">—</span>', row_content)
        self.assertNotIn('<span class="badge badge-azure">New</span>', row_content)

    def test_e_future_azure_state_not_rejected(self):
        """
        TEST E
        Future Azure state: Ready for Deployment
        Expected: display: Ready for Deployment. Do not fail because the state was not hardcoded.
        """
        fixture_ledger = """# ART Product Validation Ledger

## Summary

- **Total Bugs:** 1
- **Open:** 1
- **Fixing:** 0
- **Retest:** 0
- **Verified:** 0
- **Closed:** 0
- **Blocked:** 0

## Bugs

| Bug ID | Title | Severity | Status | Owner | Developer Comment | Retest |
| --- | --- | --- | --- | --- | --- | --- |
| [ART-AGENT-099](<bugs/Agent/ART-AGENT-099.md>) | Future ticket | LOW | OPEN | Unassigned | Deployed to staging | Pending |

## Azure Resolution & Lifecycle Tracking

| Bug ID | Feature | Azure ID | Azure State | Azure Reason | ART Disposition | Retest Required | Action Required | Last Azure Sync | Resolution Summary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ART-AGENT-099 | Agent | #69999 | Ready for Deployment | Deployed | OPEN | NO | AWAIT_DEVELOPER | 2026-10-12T06:44:54+00:00 | Deployed to staging |
"""
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            f.write(fixture_ledger)

        res = self.generator.generate_report(ledger_path=self.ledger_path, output_path=self.output_path)
        self.assertTrue(res.success)
        self.assertTrue(res.azure_state_fidelity_ok)

        with open(self.output_path, "r", encoding="utf-8") as f:
            html_text = f.read()

        self.assertIn("Ready for Deployment", html_text)
        self.assertIn('<span class="badge badge-azure">Ready for Deployment</span>', html_text)

    def test_f_azure_state_filter_dynamic(self):
        """
        TEST F
        Azure State filter.
        Expected: filter options dynamically match states represented in generated report.
        """
        fixture_ledger = """# ART Product Validation Ledger

## Summary

- **Total Bugs:** 2
- **Open:** 1
- **Fixing:** 0
- **Retest:** 1
- **Verified:** 0
- **Closed:** 0
- **Blocked:** 0

## Bugs

| Bug ID | Title | Severity | Status | Owner | Developer Comment | Retest |
| --- | --- | --- | --- | --- | --- | --- |
| [ART-TEST-001](<bugs/TEST/ART-TEST-001/ART-TEST-001.md>) | Ticket 1 | LOW | OPEN | Unassigned | None | Pending |
| [ART-TEST-002](<bugs/TEST/ART-TEST-002/ART-TEST-002.md>) | Ticket 2 | HIGH | RETEST | Unassigned | Fixed | Required |

## Azure Resolution & Lifecycle Tracking

| Bug ID | Feature | Azure ID | Azure State | Azure Reason | ART Disposition | Retest Required | Action Required | Last Azure Sync | Resolution Summary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ART-TEST-001 | F1 | #69001 | Ready for Deployment | New | OPEN | NO | AWAIT_DEVELOPER | 2026-10-12T06:44:54+00:00 | None |
| ART-TEST-002 | F2 | #69002 | QA Approved | Fixed | RETEST_REQUIRED | YES | RETEST | 2026-10-12T06:44:54+00:00 | Fixed |
"""
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            f.write(fixture_ledger)

        res = self.generator.generate_report(ledger_path=self.ledger_path, output_path=self.output_path)
        self.assertTrue(res.success)
        self.assertTrue(res.azure_state_filter_ok)

        with open(self.output_path, "r", encoding="utf-8") as f:
            html_text = f.read()

        # Both dynamically represented states must be present in the <select id="azure-state-filter">
        select_match = re.search(r'<select id="azure-state-filter"[^>]*>(.*?)</select>', html_text, flags=re.DOTALL)
        self.assertIsNotNone(select_match)
        select_content = select_match.group(1)

        self.assertIn('<option value="Ready for Deployment">Ready for Deployment</option>', select_content)
        self.assertIn('<option value="QA Approved">QA Approved</option>', select_content)


if __name__ == "__main__":
    unittest.main()
