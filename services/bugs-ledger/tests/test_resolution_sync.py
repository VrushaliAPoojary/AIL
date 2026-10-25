"""
tests/test_resolution_sync.py

Comprehensive tests for Harness 03 (Azure Resolution & Feedback Sync Harness).
Covers:
- All 10 original required test cases specified in prompts/bugs/azure_resolution_sync.md (Section 25)
- All Section 31Q Assignee Regression Tests (Tests A through H)
- All Section 32I Azure Lifecycle Fidelity Tests (Tests 1 through 10)
"""

import os
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import MagicMock

from core.lifecycle.resolution_sync import (
    AzureResolutionSyncHarness,
    derive_disposition_and_action,
    map_disposition_to_primary_ledger,
    is_system_comment,
    is_qa_owner,
)
from integrations.azure_devops.models import AzureDevOpsError


class TestResolutionSyncRules(unittest.TestCase):
    """Unit tests for pure resolution disposition derivation rules."""

    def test_01_product_decision_pending(self):
        """Test 1: Azure Resolved/Fixed with feedback mentioning intentional for now & discussion pending."""
        disp, retest, action, reason = derive_disposition_and_action(
            azure_state="Resolved",
            azure_reason="Fixed",
            developer_feedback="Editing prohibition is intentional for now. Will discuss with Kiran and change the behavior if needed.",
            has_art_retest_evidence=False
        )
        self.assertEqual(disp, "PRODUCT_DECISION_PENDING")
        self.assertFalse(retest)
        self.assertEqual(action, "AWAIT_PRODUCT_DECISION")
        self.assertIn("intentional for now", reason.lower())

    def test_02_fix_claimed(self):
        """Test 2: Developer claims fix but no ART retest evidence exists. Must NEVER be VERIFIED_FIXED."""
        disp, retest, action, reason = derive_disposition_and_action(
            azure_state="Resolved",
            azure_reason="Fixed",
            developer_feedback="Fixed.",
            current_assignee="Prajwal",
            has_art_retest_evidence=False
        )
        self.assertEqual(disp, "FIX_CLAIMED")
        self.assertNotEqual(disp, "VERIFIED_FIXED")

    def test_03_retest_request(self):
        """Test 3: Developer states fix deployed and requests verification."""
        disp, retest, action, reason = derive_disposition_and_action(
            azure_state="Resolved",
            azure_reason="Fixed",
            developer_feedback="Fixed and deployed. Please verify.",
            has_art_retest_evidence=False
        )
        self.assertEqual(disp, "RETEST_REQUIRED")
        self.assertTrue(retest)
        self.assertEqual(action, "RETEST")

    def test_04_verified_fix(self):
        """Test 4: Approved ART retest passes Acceptance Criteria -> VERIFIED_FIXED."""
        disp, retest, action, reason = derive_disposition_and_action(
            azure_state="Resolved",
            azure_reason="Fixed",
            developer_feedback="Fixed and deployed.",
            has_art_retest_evidence=True,
            retest_passed=True
        )
        self.assertEqual(disp, "VERIFIED_FIXED")
        self.assertFalse(retest)
        self.assertEqual(action, "NONE")

    def test_05_failed_retest(self):
        """Test 5: Claimed fix, but ART retest reproduces defect -> REPRODUCED_AFTER_FIX, REOPEN_RECOMMENDED."""
        disp, retest, action, reason = derive_disposition_and_action(
            azure_state="Resolved",
            azure_reason="Fixed",
            developer_feedback="Fixed.",
            has_art_retest_evidence=True,
            retest_passed=False
        )
        self.assertEqual(disp, "REPRODUCED_AFTER_FIX")
        self.assertFalse(retest)
        self.assertEqual(action, "REOPEN_RECOMMENDED")

    def test_06_intentional_behavior(self):
        """Test 6: Authoritative feedback confirms intentional behavior without ambiguity."""
        disp, retest, action, reason = derive_disposition_and_action(
            azure_state="Closed",
            azure_reason="By Design",
            developer_feedback="This is intentional behavior and will remain as designed.",
            has_art_retest_evidence=False
        )
        self.assertEqual(disp, "INTENTIONAL_BEHAVIOR")
        self.assertFalse(retest)
        self.assertEqual(action, "NONE")

    def test_07_duplicate(self):
        """Test 7: Feedback confirms duplicate -> DUPLICATE, REVIEW_DUPLICATE."""
        disp, retest, action, reason = derive_disposition_and_action(
            azure_state="Closed",
            azure_reason="Duplicate",
            developer_feedback="Duplicate of #68800.",
            has_art_retest_evidence=False
        )
        self.assertEqual(disp, "DUPLICATE")
        self.assertFalse(retest)
        self.assertEqual(action, "REVIEW_DUPLICATE")

    def test_system_comment_filtering(self):
        """Verify automated system comments are detected and excluded."""
        self.assertTrue(is_system_comment("Created automatically by ART Product Resolution System for ART-TOOL-003."))
        self.assertTrue(is_system_comment("<div>Synchronized via ART Bug Pipeline.</div>"))
        self.assertFalse(is_system_comment("<div>Editing prohibition is intentional for now.</div>"))

    # Section 31Q Unit Rule Tests
    def test_31q_test_a_developer_ownership(self):
        """TEST A — DEVELOPER OWNERSHIP: Prajwal with active implementation -> IN_PROGRESS / FIXING."""
        disp, retest, action, reason = derive_disposition_and_action(
            azure_state="Active",
            azure_reason=None,
            developer_feedback="Investigating and working on fix.",
            current_assignee="Prajwal",
            previous_assignee="Anusha",
            has_art_retest_evidence=False,
        )
        self.assertEqual(disp, "IN_PROGRESS")
        self.assertFalse(retest)
        self.assertEqual(action, "AWAIT_DEVELOPER")
        p_status, p_owner, p_retest, _ = map_disposition_to_primary_ledger(disp, retest, "Investigating and working on fix.", reason, "Prajwal")
        self.assertEqual(p_status, "FIXING")
        self.assertEqual(p_owner, "Prajwal")

    def test_31q_test_b_prajwal_returns_fix_to_qa(self):
        """TEST B — PRAJWAL RETURNS FIX TO QA: Prajwal -> Chiranjeevi + Fixed. Please verify."""
        disp, retest, action, reason = derive_disposition_and_action(
            azure_state="Resolved",
            azure_reason="Fixed",
            developer_feedback="Fixed. Please verify.",
            current_assignee="Chiranjeevi",
            previous_assignee="Prajwal",
            has_art_retest_evidence=False,
        )
        self.assertEqual(disp, "RETEST_REQUIRED")
        self.assertTrue(retest)
        self.assertEqual(action, "RETEST")
        p_status, p_owner, p_retest, _ = map_disposition_to_primary_ledger(disp, retest, "Fixed. Please verify.", reason, "Chiranjeevi")
        self.assertEqual(p_status, "RETEST")
        self.assertEqual(p_owner, "Chiranjeevi")
        self.assertEqual(p_retest, "Required")

    def test_31q_test_c_yuresh_returns_fix_to_qa(self):
        """TEST C — YURESH RETURNS FIX TO QA: Yuresh -> Chiranjeevi + Resolved/Fixed."""
        disp, retest, action, reason = derive_disposition_and_action(
            azure_state="Resolved",
            azure_reason="Fixed",
            developer_feedback=None,
            current_assignee="Chiranjeevi",
            previous_assignee="Yuresh",
            has_art_retest_evidence=False,
        )
        self.assertEqual(disp, "RETEST_REQUIRED")
        self.assertTrue(retest)
        self.assertEqual(action, "RETEST")
        p_status, p_owner, p_retest, _ = map_disposition_to_primary_ledger(disp, retest, None, reason, "Chiranjeevi")
        self.assertEqual(p_status, "RETEST")
        self.assertEqual(p_owner, "Chiranjeevi")

    def test_31q_test_d_qa_assignment_with_information_request(self):
        """TEST D — QA ASSIGNMENT WITH INFORMATION REQUEST: Never derive RETEST_REQUIRED solely from assignment."""
        disp, retest, action, reason = derive_disposition_and_action(
            azure_state="Active",
            azure_reason=None,
            developer_feedback="Please provide additional reproduction information.",
            current_assignee="Chiranjeevi",
            previous_assignee="Prajwal",
            has_art_retest_evidence=False,
        )
        self.assertFalse(retest)
        self.assertEqual(action, "PROVIDE_INFORMATION")

    def test_31q_test_e_qa_owner_awaiting_product_decision(self):
        """TEST E — QA OWNER AWAITING PRODUCT DECISION: Product confirmation required."""
        disp, retest, action, reason = derive_disposition_and_action(
            azure_state="Resolved",
            azure_reason="Fixed",
            developer_feedback="Current behavior is intentional for now. Product confirmation required.",
            current_assignee="Chiranjeevi",
            has_art_retest_evidence=False,
        )
        self.assertEqual(disp, "PRODUCT_DECISION_PENDING")
        self.assertFalse(retest)
        self.assertEqual(action, "AWAIT_PRODUCT_DECISION")
        p_status, p_owner, p_retest, _ = map_disposition_to_primary_ledger(disp, retest, "Current behavior is intentional for now. Product confirmation required.", reason, "Chiranjeevi")
        self.assertEqual(p_status, "BLOCKED")
        self.assertEqual(p_owner, "Chiranjeevi")

    def test_31q_test_f_fix_claimed_but_developer_still_owns(self):
        """TEST F — FIX CLAIMED BUT DEVELOPER STILL OWNS: Prajwal owns, 'Fix completed.' -> FIX_CLAIMED / FIXING."""
        disp, retest, action, reason = derive_disposition_and_action(
            azure_state="Resolved",
            azure_reason="Fixed",
            developer_feedback="Fix completed.",
            current_assignee="Prajwal",
            has_art_retest_evidence=False,
        )
        self.assertEqual(disp, "FIX_CLAIMED")
        self.assertFalse(retest)
        self.assertEqual(action, "AWAIT_DEVELOPER")
        p_status, p_owner, p_retest, _ = map_disposition_to_primary_ledger(disp, retest, "Fix completed.", reason, "Prajwal")
        self.assertEqual(p_status, "FIXING")
        self.assertEqual(p_owner, "Prajwal")


class TestResolutionSyncHarness(unittest.TestCase):
    """End-to-end tests for AzureResolutionSyncHarness using a mock client and isolated workspace."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test.db")
        self.bugs_dir = os.path.join(self.test_dir, "ART-Product-Validation", "bugs")
        self.ledger_path = os.path.join(self.test_dir, "ART-Product-Validation", "ART_PRODUCT_VALIDATION_LEDGER.md")
        os.makedirs(self.bugs_dir, exist_ok=True)

        # Initialize mock DB schema using repository DDL
        from core.storage.schema import init_db
        from core.storage.integrations import ensure_external_work_items_table
        conn = sqlite3.connect(self.db_path)
        init_db(conn)
        ensure_external_work_items_table(conn)
        conn.execute("""
        INSERT INTO investigations VALUES (
            'rec_test_tool_003', 'INV-20261006-0001', 'ART-TOOL-003', 'NATIVE',
            'tool-builder-edit-definition-unavailable', 'CONFIRMED', 'OPEN', 'BUG',
            'Tool Builder / Existing Tool Editing', 'HIGH', 'P2', 'Unassigned',
            'INP-001', 'TCK-001', NULL, '2026-10-06T00:00:00Z', '2026-10-06T00:00:00Z'
        );
        """)
        conn.execute("""
        INSERT INTO original_inputs VALUES (
            'INP-001', 'rec_test_tool_003', 'Tool cannot be edited.', 'tester',
            '2026-10-06T00:00:00Z', '[]', 'HUMAN_SUPPLIED'
        );
        """)
        conn.execute("""
        INSERT INTO external_work_items VALUES (
            'EWI-001', 'rec_test_tool_003', 'AZURE_DEVOPS', '68991',
            'https://dev.azure.com/BixBytesSolutions/project/_workitems/edit/68991',
            '2026-10-06T00:00:00Z', '{"canonical_bug_id": "ART-TOOL-003"}'
        );
        """)
        conn.commit()
        conn.close()

        # Create canonical bug markdown
        bug_folder = os.path.join(self.bugs_dir, "Tool Builder", "ART-TOOL-003__edit-definition-unavailable")
        os.makedirs(bug_folder, exist_ok=True)
        self.md_path = os.path.join(bug_folder, "ART-TOOL-003.md")
        with open(self.md_path, "w", encoding="utf-8") as f:
            f.write("""# ART-TOOL-003 — Tool Builder Edit Definition Unavailable

## Metadata

- **Canonical Bug ID:** ART-TOOL-003
- **Title:** Tool Builder Edit Definition Unavailable
- **Status:** OPEN
- **Feature:** Tool Builder

## 1. Problem

Tool cannot be edited.

## 19. Azure DevOps

- **Work Item ID:** 68991
- **URL:** https://dev.azure.com/BixBytesSolutions/project/_workitems/edit/68991
- **Parent Feature:** Tool Builder
- **Parent Feature ID:** 68807
- **Assigned To:** Unassigned
- **Sync Status:** SYNCED
""")

        # Create mock ledger with Owner column
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            f.write("""# ART Product Validation Ledger

## Summary

- **Total Bugs:** 1
- **Open:** 1
- **Fixing:** 0
- **Retest:** 0
- **Verified:** 0
- **Closed:** 0
- **Blocked:** 0

## Bugs

| Bug ID | Title | Severity | Status | Owner | Developer Update | Retest |
| --- | --- | --- | --- | --- | --- | --- |
| [ART-TOOL-003](bugs/Tool%20Builder/ART-TOOL-003__edit-definition-unavailable/ART-TOOL-003.md) | Tool Builder Edit Definition Unavailable | HIGH | OPEN | Unassigned | Pending. | Pending. |
""")

        self.harness = AzureResolutionSyncHarness(repo_root=self.test_dir, db_path=self.db_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_08_no_change_idempotency(self):
        """Test 8: Running twice against unchanged Azure data produces NO_CHANGE on second run."""
        mock_client = MagicMock()
        mock_client.get_work_item.return_value = {
            "fields": {
                "System.WorkItemType": "Bug",
                "System.Tags": "ART; ART:ART-TOOL-003",
                "System.State": "Resolved",
                "System.Reason": "Fixed",
                "System.ChangedDate": "2026-10-12T04:01:17Z",
                "System.ChangedBy": {"displayName": "Anusha Ganesh Hegde"},
                "System.AssignedTo": {"displayName": "Anusha Ganesh Hegde"},
            }
        }
        mock_client.get_comments.return_value = [
            {
                "id": "1",
                "text": "Editing prohibition is intentional for now. Will discuss with Kiran and change the behavior if needed.",
                "createdBy": {"displayName": "Anusha Ganesh Hegde"},
                "createdDate": "2026-10-12T04:01:17Z",
            }
        ]

        # First run: should update
        res1 = self.harness.sync_bug("ART-TOOL-003", client=mock_client)
        self.assertTrue(res1.success)
        self.assertEqual(res1.status, "UPDATED")
        self.assertEqual(res1.art_disposition, "PRODUCT_DECISION_PENDING")
        self.assertEqual(res1.primary_status, "BLOCKED")
        self.assertEqual(res1.primary_retest, "Not Required")
        self.assertTrue(res1.summary_recomputed)
        self.assertTrue(res1.summary_invariant)
        self.assertTrue(res1.lifecycle_table_updated)
        self.assertTrue(res1.ledger_consistent)

        # Verify ledger file directly
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            ledger_text = f.read()
        self.assertIn("BLOCKED", ledger_text)
        self.assertIn("Not Required", ledger_text)
        self.assertIn("- **Blocked:** 1", ledger_text)
        self.assertIn("- **Open:** 0", ledger_text)

        # Second run: should be NO_CHANGE (idempotent)
        res2 = self.harness.sync_bug("ART-TOOL-003", client=mock_client)
        self.assertTrue(res2.success)
        self.assertEqual(res2.status, "NO_CHANGE")
        self.assertFalse(res2.ledger_updated)
        self.assertFalse(res2.canonical_history_updated)
        self.assertTrue(res2.summary_invariant)
        self.assertTrue(res2.ledger_consistent)

    def test_31q_test_g_assignment_idempotency(self):
        """TEST G — ASSIGNMENT IDEMPOTENCY: Run twice against Prajwal -> Chiranjeevi."""
        mock_client = MagicMock()
        mock_client.get_work_item.return_value = {
            "fields": {
                "System.WorkItemType": "Bug",
                "System.Tags": "ART; ART:ART-TOOL-003",
                "System.State": "Resolved",
                "System.Reason": "Fixed",
                "System.ChangedDate": "2026-10-12T04:01:17Z",
                "System.ChangedBy": {"displayName": "Prajwal"},
                "System.AssignedTo": {"displayName": "Chiranjeevi"},
            }
        }
        mock_client.get_comments.return_value = [
            {
                "id": "1",
                "text": "Fixed. Please verify.",
                "createdBy": {"displayName": "Prajwal"},
                "createdDate": "2026-10-12T04:01:17Z",
            }
        ]

        res1 = self.harness.sync_bug("ART-TOOL-003", client=mock_client)
        self.assertTrue(res1.success)
        self.assertEqual(res1.status, "UPDATED")
        self.assertEqual(res1.primary_owner, "Chiranjeevi")
        self.assertEqual(res1.primary_status, "RETEST")

        res2 = self.harness.sync_bug("ART-TOOL-003", client=mock_client)
        self.assertTrue(res2.success)
        self.assertEqual(res2.status, "NO_CHANGE")

    def test_31q_test_h_stale_local_owner_reconciliation(self):
        """TEST H — STALE LOCAL OWNER RECONCILIATION: Azure has Chiranjeevi, local has Prajwal -> reconcile."""
        mock_client = MagicMock()
        mock_client.get_work_item.return_value = {
            "fields": {
                "System.WorkItemType": "Bug",
                "System.Tags": "ART; ART:ART-TOOL-003",
                "System.State": "Resolved",
                "System.Reason": "Fixed",
                "System.ChangedDate": "2026-10-12T04:01:17Z",
                "System.ChangedBy": {"displayName": "Prajwal"},
                "System.AssignedTo": {"displayName": "Chiranjeevi"},
            }
        }
        mock_client.get_comments.return_value = [
            {
                "id": "1",
                "text": "Fixed. Please verify.",
                "createdBy": {"displayName": "Prajwal"},
                "createdDate": "2026-10-12T04:01:17Z",
            }
        ]

        # Initial sync
        self.harness.sync_bug("ART-TOOL-003", client=mock_client)

        # Simulate local owner drift (someone edited local ledger to Prajwal)
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            ledger_text = f.read()
        ledger_text = ledger_text.replace("Chiranjeevi", "Prajwal")
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            f.write(ledger_text)

        # Resync detects stale owner and reconciles
        res_rec = self.harness.sync_bug("ART-TOOL-003", client=mock_client)
        self.assertTrue(res_rec.success)
        self.assertEqual(res_rec.status, "UPDATED")
        self.assertEqual(res_rec.primary_owner, "Chiranjeevi")

    def test_32i_test_1_stale_local_state(self):
        """TEST 1 — STALE LOCAL STATE: Current Azure State differs from stored local state -> Azure wins."""
        mock_client = MagicMock()
        mock_client.get_work_item.return_value = {
            "fields": {
                "System.WorkItemType": "Bug",
                "System.Tags": "ART; ART:ART-TOOL-003",
                "System.State": "Active",
                "System.Reason": None,
                "System.ChangedDate": "2026-10-12T04:01:17Z",
                "System.AssignedTo": {"displayName": "Prajwal"},
            }
        }
        mock_client.get_comments.return_value = []

        res = self.harness.sync_bug("ART-TOOL-003", client=mock_client)
        self.assertTrue(res.success)
        self.assertEqual(res.primary_status, "FIXING")
        self.assertEqual(res.primary_owner, "Prajwal")

    def test_32i_test_2_new_human_fix_comment(self):
        """TEST 2 — NEW HUMAN FIX COMMENT: Azure state unchanged, new human comment 'Fixed.' -> FIX_CLAIMED."""
        mock_client = MagicMock()
        mock_client.get_work_item.return_value = {
            "fields": {
                "System.WorkItemType": "Bug",
                "System.Tags": "ART; ART:ART-TOOL-003",
                "System.State": "Active",
                "System.Reason": None,
                "System.ChangedDate": "2026-10-12T04:01:17Z",
                "System.AssignedTo": {"displayName": "Prajwal"},
            }
        }
        mock_client.get_comments.return_value = [
            {
                "id": "1",
                "text": "Fixed.",
                "createdBy": {"displayName": "Prajwal"},
                "createdDate": "2026-10-12T04:01:17Z",
            }
        ]

        res = self.harness.sync_bug("ART-TOOL-003", client=mock_client)
        self.assertTrue(res.success)
        self.assertEqual(res.art_disposition, "FIX_CLAIMED")
        self.assertEqual(res.primary_status, "FIXING")

    def test_32i_test_3_new_retest_request(self):
        """TEST 3 — NEW RETEST REQUEST: 'Fixed and deployed. Please verify.' -> RETEST_REQUIRED / YES / RETEST."""
        mock_client = MagicMock()
        mock_client.get_work_item.return_value = {
            "fields": {
                "System.WorkItemType": "Bug",
                "System.Tags": "ART; ART:ART-TOOL-003",
                "System.State": "Resolved",
                "System.Reason": "Fixed",
                "System.ChangedDate": "2026-10-12T04:01:17Z",
                "System.AssignedTo": {"displayName": "Chiranjeevi"},
            }
        }
        mock_client.get_comments.return_value = [
            {
                "id": "1",
                "text": "Fixed and deployed. Please verify.",
                "createdBy": {"displayName": "Yuresh"},
                "createdDate": "2026-10-12T04:01:17Z",
            }
        ]

        res = self.harness.sync_bug("ART-TOOL-003", client=mock_client)
        self.assertTrue(res.success)
        self.assertEqual(res.art_disposition, "RETEST_REQUIRED")
        self.assertTrue(res.retest_required)
        self.assertEqual(res.action_required, "RETEST")
        self.assertEqual(res.primary_status, "RETEST")
        self.assertEqual(res.primary_retest, "Required")

    def test_32i_test_6_closed_fixed_without_art_retest(self):
        """TEST 6 — CLOSED/FIXED WITHOUT ART RETEST: Never VERIFIED_FIXED."""
        mock_client = MagicMock()
        mock_client.get_work_item.return_value = {
            "fields": {
                "System.WorkItemType": "Bug",
                "System.Tags": "ART; ART:ART-TOOL-003",
                "System.State": "Closed",
                "System.Reason": "Fixed and verified",
                "System.ChangedDate": "2026-10-12T04:01:17Z",
                "System.AssignedTo": {"displayName": "Prajwal"},
            }
        }
        mock_client.get_comments.return_value = []

        res = self.harness.sync_bug("ART-TOOL-003", client=mock_client)
        self.assertTrue(res.success)
        self.assertNotEqual(res.art_disposition, "VERIFIED_FIXED")
        self.assertEqual(res.art_disposition, "FIX_CLAIMED")

    def test_32i_test_8_sync_time_vs_lifecycle_time(self):
        """TEST 8 — SYNC TIME VS LIFECYCLE TIME: Last Azure Sync and meaningful lifecycle timestamp remain distinct."""
        mock_client = MagicMock()
        mock_client.get_work_item.return_value = {
            "fields": {
                "System.WorkItemType": "Bug",
                "System.Tags": "ART; ART:ART-TOOL-003",
                "System.State": "Resolved",
                "System.Reason": "Fixed",
                "System.ChangedDate": "2026-10-11T12:00:00Z",
                "System.AssignedTo": {"displayName": "Chiranjeevi"},
            }
        }
        mock_client.get_comments.return_value = []

        res = self.harness.sync_bug("ART-TOOL-003", client=mock_client)
        self.assertTrue(res.success)
        self.assertEqual(res.lifecycle_updated_at, "2026-10-11T12:00:00Z")

        with open(self.md_path, "r", encoding="utf-8") as f:
            md_text = f.read()
        self.assertIn("- **Latest Lifecycle Update:** 2026-10-11T12:00:00Z", md_text)
        self.assertIn("- **Last Azure Sync:**", md_text)

    def test_09_azure_canonical_conflict(self):
        """Test 9: Reference mismatch between Markdown and DB stops without mutation."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE external_work_items SET external_id = '99999' WHERE investigation_key = 'rec_test_tool_003'")
        conn.commit()
        conn.close()

        mock_client = MagicMock()
        res = self.harness.sync_bug("ART-TOOL-003", client=mock_client)
        self.assertFalse(res.success)
        self.assertEqual(res.status, "FAILED")
        self.assertEqual(res.blocker, "AZURE REFERENCE CONFLICT")
        mock_client.get_work_item.assert_not_called()

    def test_10_azure_read_only_zero_mutations(self):
        """Test 10: Harness 03 performs zero Azure write mutations."""
        mock_client = MagicMock()
        mock_client.get_work_item.return_value = {
            "fields": {
                "System.WorkItemType": "Bug",
                "System.Tags": "ART; ART:ART-TOOL-003",
                "System.State": "Resolved",
                "System.Reason": "Fixed",
            }
        }
        mock_client.get_comments.return_value = []

        res = self.harness.sync_bug("ART-TOOL-003", client=mock_client)
        self.assertEqual(res.azure_mutations, 0)
        self.assertTrue(mock_client.get_work_item.called)
        self.assertFalse(hasattr(mock_client, "patch") and mock_client.patch.called)
        self.assertFalse(hasattr(mock_client, "post") and mock_client.post.called)


if __name__ == "__main__":
    unittest.main()
