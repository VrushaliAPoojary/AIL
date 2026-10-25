"""
tests/test_transactional_lifecycle.py

Phase 01H — Transactional Lifecycle Orchestration Test Suite
Validates:
- ResolutionService coordinates with core/lifecycle/engine.py
- Atomic co-commit of state + required artifacts + engine audit events
- Stale state detection / safe concurrency in BEGIN IMMEDIATE
- Rollback semantics upon failure injection (no dirty state, no sequence leak)
- Preservation of append-only historical updates
"""

import unittest
import os
import shutil
import tempfile
import sqlite3

from core.storage.schema import init_db
from core.storage.db import get_connection
from core.storage.service import ResolutionService

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class TestTransactionalLifecycle(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="art_test_service_")
        self.db_path = os.path.join(self.test_dir, "test_service.db")
        self.conn = get_connection(self.db_path)
        init_db(self.conn)
        self.service = ResolutionService(self.conn)

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # ==========================================
    # 1. CREATION TESTS (1 - 4)
    # ==========================================

    def test_01_create_investigation_produces_inv_id(self):
        res = self.service.create_investigation(
            tester_description="Sample defect observed in test environment",
            reporter="qa-tester",
            slug="sample-defect"
        )
        self.assertTrue(res.success)
        self.assertIsNotNone(res.data["investigation_id"])
        self.assertTrue(res.data["investigation_id"].startswith("INV-"))
        self.assertEqual(res.data["lifecycle_phase"], "CAPTURE")
        self.assertIsNone(res.data["status"])

    def test_02_create_investigation_stores_original_input(self):
        res = self.service.create_investigation(
            tester_description="Exact text from tester",
            reporter="lead-qa"
        )
        self.assertTrue(res.success)
        record_key = res.data["record_key"]

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM original_inputs WHERE investigation_key = ?;", (record_key,))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["tester_description"], "Exact text from tester")
        self.assertEqual(row["reporter"], "lead-qa")

    def test_03_create_investigation_produces_capture_audit(self):
        res = self.service.create_investigation(
            tester_description="Defect description",
            reporter="lead-qa"
        )
        self.assertTrue(res.success)
        record_key = res.data["record_key"]

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM audit_events WHERE investigation_key = ?;", (record_key,))
        rows = cursor.fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["event_type"], "INVESTIGATION_CAPTURED")

    def test_04_failed_creation_rolls_back_everything(self):
        # Empty description and empty evidence rejected
        res = self.service.create_investigation(
            tester_description="",
            reporter="lead-qa",
            initial_evidence_ids=[]
        )
        self.assertFalse(res.success)
        self.assertIn("Capture requires description or initial evidence", res.error)

        cursor = self.conn.cursor()
        cursor.execute("SELECT count(*) FROM investigations;")
        self.assertEqual(cursor.fetchone()[0], 0)
        cursor.execute("SELECT count(*) FROM original_inputs;")
        self.assertEqual(cursor.fetchone()[0], 0)
        cursor.execute("SELECT count(*) FROM id_allocations;")
        self.assertEqual(cursor.fetchone()[0], 0)

    # ==========================================
    # 2. CONFIRM BUG / PROMOTION TESTS (5 - 12)
    # ==========================================

    def test_05_to_10_confirm_bug_promotion(self):
        # Create initial investigation
        create_res = self.service.create_investigation(
            tester_description="Agent output parser contract violation",
            reporter="tester-1",
            slug="output-contract-violation"
        )
        record_key = create_res.data["record_key"]
        inv_id = create_res.data["investigation_id"]

        # Confirm as BUG
        ticket_data = {
            "title": "Structured output contract is not strictly enforced",
            "expectedResult": "Output matches JSON schema",
            "actualResult": "Output parser produced invalid fields",
            "severity": "HIGH"
        }
        confirm_res = self.service.confirm_bug(
            record_key=record_key,
            module="AGENT",
            ticket_data=ticket_data,
            actor="lead-qa"
        )
        self.assertTrue(confirm_res.success)

        # 5. BUG confirmation succeeds & 6. ART ID allocated atomically
        self.assertEqual(confirm_res.data["canonical_bug_id"], "ART-AGENT-001")
        self.assertEqual(confirm_res.data["status"], "OPEN")
        self.assertEqual(confirm_res.data["lifecycle_phase"], "CONFIRMED")

        # 7. INV ID remains unchanged
        self.assertEqual(confirm_res.data["investigation_id"], inv_id)

        # 8. record_key remains unchanged
        self.assertEqual(confirm_res.data["record_key"], record_key)

        # 9. Aggregate root projection of module, severity, priority
        self.assertEqual(confirm_res.data["module"], "AGENT")
        self.assertEqual(confirm_res.data["severity"], "HIGH")
        self.assertEqual(confirm_res.data["priority"], "Not provided")

        # 10. Audit event created
        cursor = self.conn.cursor()
        cursor.execute("SELECT event_type FROM audit_events WHERE investigation_key = ? ORDER BY timestamp ASC;", (record_key,))
        events = [r[0] for r in cursor.fetchall()]
        self.assertEqual(events, ["INVESTIGATION_CAPTURED", "TICKET_CONFIRMED"])

    def test_11_failed_confirmation_does_not_consume_art_id(self):
        create_res = self.service.create_investigation(tester_description="Defect", reporter="tester")
        record_key = create_res.data["record_key"]

        # Attempt confirm with unapproved module
        res = self.service.confirm_bug(record_key, module="UNAPPROVED_MOD", ticket_data={})
        self.assertFalse(res.success)

        # Allocator table must NOT have committed a sequence for UNAPPROVED_MOD
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM id_allocations WHERE scope LIKE 'BUG:%';")
        self.assertEqual(cursor.fetchall(), [])

    def test_12_not_provided_module_rejected(self):
        create_res = self.service.create_investigation(tester_description="Defect", reporter="tester")
        record_key = create_res.data["record_key"]

        res = self.service.confirm_bug(record_key, module="Not provided", ticket_data={})
        self.assertFalse(res.success)
        self.assertIn("not an approved canonical module", res.error)

    # ==========================================
    # 3. START WORK TESTS (13 - 16)
    # ==========================================

    def test_13_to_15_start_work_lifecycle_transition(self):
        create_res = self.service.create_investigation(tester_description="Defect", reporter="tester")
        record_key = create_res.data["record_key"]
        self.service.confirm_bug(record_key, module="SFN", ticket_data={"title": "SFN defect"})

        # Start work
        work_res = self.service.start_work(record_key, assignee="developer-1", actor="developer-1")
        self.assertTrue(work_res.success)

        # 13. OPEN -> FIXING & 14. Assignee persisted
        self.assertEqual(work_res.data["status"], "FIXING")
        self.assertEqual(work_res.data["assignee"], "developer-1")

        # 15. Audit persisted
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM audit_events WHERE investigation_key = ? AND event_type = 'STATUS_TRANSITIONED';", (record_key,))
        audit = cursor.fetchone()
        self.assertIsNotNone(audit)
        self.assertIn("developer-1", audit["summary"])

    def test_16_start_work_from_invalid_state_rejected(self):
        # Unconfirmed CAPTURE investigation cannot start work
        create_res = self.service.create_investigation(tester_description="Defect", reporter="tester")
        record_key = create_res.data["record_key"]

        work_res = self.service.start_work(record_key, assignee="developer-1", actor="developer-1")
        self.assertFalse(work_res.success)
        self.assertIn("Cannot start work in lifecycle phase 'CAPTURE'", work_res.error)

        # Persisted state unchanged
        row = self.service.repo.get_investigation_by_record_key(record_key)
        self.assertEqual(row["lifecycle_phase"], "CAPTURE")
        self.assertIsNone(row["status"])

    # ==========================================
    # 4. SUBMIT FIX TESTS (17 - 21)
    # ==========================================

    def test_17_to_19_submit_fix_lifecycle_transition(self):
        create_res = self.service.create_investigation(tester_description="Defect", reporter="tester")
        record_key = create_res.data["record_key"]
        self.service.confirm_bug(record_key, module="SFN", ticket_data={"title": "SFN defect"})
        self.service.start_work(record_key, assignee="dev1", actor="dev1")

        fix_res = self.service.submit_fix(
            record_key=record_key,
            developer_username="dev1",
            summary_of_changes="Added input validation checks",
            resolved_in_version_or_branch="fix/sfn-connector",
            test_instructions_for_qa="Verify tool registry loads connector",
            commit_hash_or_pr="pr-123"
        )
        self.assertTrue(fix_res.success)

        # 17. FIXING -> RETEST
        self.assertEqual(fix_res.data["status"], "RETEST")

        # 18. DeveloperUpdate inserted
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM developer_updates WHERE investigation_key = ?;", (record_key,))
        dev_row = cursor.fetchone()
        self.assertIsNotNone(dev_row)
        self.assertEqual(dev_row["developer_username"], "dev1")

        # 19. Audit event FIX_SUBMITTED
        cursor.execute("SELECT * FROM audit_events WHERE investigation_key = ? AND event_type = 'FIX_SUBMITTED';", (record_key,))
        self.assertIsNotNone(cursor.fetchone())

    def test_20_and_21_forced_dev_insert_failure_rolls_back_status(self):
        create_res = self.service.create_investigation(tester_description="Defect", reporter="tester")
        record_key = create_res.data["record_key"]
        self.service.confirm_bug(record_key, module="SFN", ticket_data={"title": "SFN defect"})
        self.service.start_work(record_key, assignee="dev1", actor="dev1")

        # Force failure by violating DeveloperUpdate NOT NULL column (developer_username = None)
        fix_res = self.service.submit_fix(
            record_key=record_key,
            developer_username=None,  # will cause sqlite3.IntegrityError on NOT NULL
            summary_of_changes="Fix",
            resolved_in_version_or_branch="branch",
            test_instructions_for_qa="test"
        )
        self.assertFalse(fix_res.success)

        # 20. Status remains FIXING
        inv = self.service.repo.get_investigation_by_record_key(record_key)
        self.assertEqual(inv["status"], "FIXING")

        # 21. No FIX_SUBMITTED audit event
        cursor = self.conn.cursor()
        cursor.execute("SELECT count(*) FROM audit_events WHERE investigation_key = ? AND event_type = 'FIX_SUBMITTED';", (record_key,))
        self.assertEqual(cursor.fetchone()[0], 0)

    # ==========================================
    # 5. RETEST TESTS (22 - 26)
    # ==========================================

    def test_22_to_24_failed_retest_returns_to_fixing(self):
        create_res = self.service.create_investigation(tester_description="Defect", reporter="tester")
        record_key = create_res.data["record_key"]
        self.service.confirm_bug(record_key, module="SFN", ticket_data={"title": "SFN defect"})
        self.service.start_work(record_key, assignee="dev1", actor="dev1")
        self.service.submit_fix(record_key, "dev1", "Fix", "branch", "instructions")

        # 22. Failed retest
        retest_res = self.service.submit_retest(
            record_key=record_key,
            retest_evidence_ids=["EVD-RETEST-01"],
            human_confirmation={
                "confirmed": True,
                "verdict": "RETURNED_TO_FIXING",
                "confirmedBy": "qa-tester",
                "notes": "Error still reproduces in staging"
            },
            actor="qa-tester"
        )
        self.assertTrue(retest_res.success)

        # 23. State returned to FIXING
        self.assertEqual(retest_res.data["status"], "FIXING")

        # 24. RetestArtifact persisted
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM retest_artifacts WHERE investigation_key = ?;", (record_key,))
        ret_row = cursor.fetchone()
        self.assertIsNotNone(ret_row)

    def test_25_invalid_retest_without_evidence_rejected(self):
        create_res = self.service.create_investigation(tester_description="Defect", reporter="tester")
        record_key = create_res.data["record_key"]
        self.service.confirm_bug(record_key, module="SFN", ticket_data={"title": "SFN defect"})
        self.service.start_work(record_key, assignee="dev1", actor="dev1")
        self.service.submit_fix(record_key, "dev1", "Fix", "branch", "instructions")

        # Empty evidence
        retest_res = self.service.submit_retest(
            record_key=record_key,
            retest_evidence_ids=[],  # Rejected by engine
            human_confirmation={"confirmed": True, "verdict": "RETURNED_TO_FIXING", "confirmedBy": "qa", "notes": "n"},
            actor="qa"
        )
        self.assertFalse(retest_res.success)
        self.assertIn("requires at least one retest evidence reference", retest_res.error)

    def test_26a_passed_retest_remains_retest_and_emits_retest_executed_audit(self):
        create_res = self.service.create_investigation(tester_description="Defect", reporter="tester")
        record_key = create_res.data["record_key"]
        self.service.confirm_bug(record_key, module="SFN", ticket_data={"title": "SFN defect"})
        self.service.start_work(record_key, assignee="dev1", actor="dev1")
        self.service.submit_fix(record_key, "dev1", "Fix", "branch", "instructions")

        retest_res = self.service.submit_retest(
            record_key=record_key,
            retest_evidence_ids=["EVD-RETEST-PASS-01"],
            human_confirmation={
                "confirmed": True,
                "verdict": "PASSED",
                "confirmedBy": "qa-tester",
                "notes": "Test passed completely in staging"
            },
            actor="qa-tester",
            ai_recommendation={"recommendation": "PASSED", "notes": "AI confirmed output matches"}
        )
        self.assertTrue(retest_res.success)
        # PASSED retest MUST NOT establish VERIFIED
        self.assertEqual(retest_res.data["status"], "RETEST")
        self.assertNotEqual(retest_res.data["status"], "VERIFIED")
        self.assertEqual(retest_res.data["lifecycle_phase"], "CONFIRMED")
        self.assertNotEqual(retest_res.data["lifecycle_phase"], "RESOLVED")

        # Emits RETEST_EXECUTED, never VERIFIED
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM audit_events WHERE investigation_key = ? AND event_type = 'RETEST_EXECUTED';", (record_key,))
        audit = cursor.fetchone()
        self.assertIsNotNone(audit)
        self.assertEqual(audit["actor"], "qa-tester")

        # Verify no VERIFIED audit was created
        cursor.execute("SELECT count(*) FROM audit_events WHERE investigation_key = ? AND event_type = 'VERIFIED';", (record_key,))
        self.assertEqual(cursor.fetchone()[0], 0)

        # RetestArtifact persisted correctly
        cursor.execute("SELECT * FROM retest_artifacts WHERE investigation_key = ?;", (record_key,))
        ret_row = cursor.fetchone()
        self.assertIsNotNone(ret_row)

    def test_26b_inconclusive_retest_remains_retest(self):
        create_res = self.service.create_investigation(tester_description="Defect", reporter="tester")
        record_key = create_res.data["record_key"]
        self.service.confirm_bug(record_key, module="SFN", ticket_data={"title": "SFN defect"})
        self.service.start_work(record_key, assignee="dev1", actor="dev1")
        self.service.submit_fix(record_key, "dev1", "Fix", "branch", "instructions")

        retest_res = self.service.submit_retest(
            record_key=record_key,
            retest_evidence_ids=["EVD-RETEST-INC-01"],
            human_confirmation={
                "confirmed": True,
                "verdict": "INCONCLUSIVE",
                "confirmedBy": "qa-tester",
                "notes": "Network hiccup during test execution"
            },
            actor="qa-tester"
        )
        self.assertTrue(retest_res.success)
        self.assertEqual(retest_res.data["status"], "RETEST")
        self.assertEqual(retest_res.data["lifecycle_phase"], "CONFIRMED")

    def test_26c_submit_retest_with_verified_verdict_rejected(self):
        create_res = self.service.create_investigation(tester_description="Defect", reporter="tester")
        record_key = create_res.data["record_key"]
        self.service.confirm_bug(record_key, module="SFN", ticket_data={"title": "SFN defect"})
        self.service.start_work(record_key, assignee="dev1", actor="dev1")
        self.service.submit_fix(record_key, "dev1", "Fix", "branch", "instructions")

        retest_res = self.service.submit_retest(
            record_key=record_key,
            retest_evidence_ids=["EVD-RETEST-01"],
            human_confirmation={
                "confirmed": True,
                "verdict": "VERIFIED",
                "confirmedBy": "qa-tester",
                "notes": "Attempting to bypass verify endpoint"
            },
            actor="qa-tester"
        )
        self.assertFalse(retest_res.success)
        self.assertIn("SUBMIT_RETEST cannot establish VERIFIED status. Use explicit VERIFY action.", retest_res.error)

    # ==========================================
    # 6. VERIFY TESTS (27 - 31)
    # ==========================================

    def test_27_ai_actor_cannot_verify(self):
        create_res = self.service.create_investigation(tester_description="Defect", reporter="tester")
        record_key = create_res.data["record_key"]
        self.service.confirm_bug(record_key, module="SFN", ticket_data={"title": "SFN defect"})
        self.service.start_work(record_key, assignee="dev1", actor="dev1")
        self.service.submit_fix(record_key, "dev1", "Fix", "branch", "instructions")

        verify_res = self.service.verify(
            record_key=record_key,
            human_confirmation={"confirmed": True, "verdict": "VERIFIED", "confirmedBy": "ai", "notes": "ai approved"},
            actor="ai-service",
            actor_role="AI"  # FORBIDDEN
        )
        self.assertFalse(verify_res.success)
        self.assertIn("AI is forbidden from confirming VERIFIED status", verify_res.error)

    def test_28_missing_human_confirmation_cannot_verify(self):
        create_res = self.service.create_investigation(tester_description="Defect", reporter="tester")
        record_key = create_res.data["record_key"]
        self.service.confirm_bug(record_key, module="SFN", ticket_data={"title": "SFN defect"})
        self.service.start_work(record_key, assignee="dev1", actor="dev1")
        self.service.submit_fix(record_key, "dev1", "Fix", "branch", "instructions")

        verify_res = self.service.verify(
            record_key=record_key,
            human_confirmation={"confirmed": False, "verdict": "VERIFIED"},
            actor="qa-lead",
            actor_role="HUMAN"
        )
        self.assertFalse(verify_res.success)
        self.assertIn("explicit human confirmation is strictly required", verify_res.error)

    def test_29_and_30_valid_human_verification_succeeds(self):
        create_res = self.service.create_investigation(tester_description="Defect", reporter="tester")
        record_key = create_res.data["record_key"]
        self.service.confirm_bug(record_key, module="SFN", ticket_data={"title": "SFN defect"})
        self.service.start_work(record_key, assignee="dev1", actor="dev1")
        self.service.submit_fix(record_key, "dev1", "Fix", "branch", "instructions")

        verify_res = self.service.verify(
            record_key=record_key,
            human_confirmation={
                "confirmed": True,
                "verdict": "VERIFIED",
                "confirmedBy": "qa-lead",
                "notes": "Verified in staging"
            },
            actor="qa-lead",
            actor_role="HUMAN",
            retest_evidence_ids=["EVD-VERIFIED-01"]
        )
        self.assertTrue(verify_res.success)
        self.assertEqual(verify_res.data["status"], "VERIFIED")

        # 30. VERIFIED audit event committed
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM audit_events WHERE investigation_key = ? AND event_type = 'VERIFIED';", (record_key,))
        self.assertIsNotNone(cursor.fetchone())

    # ==========================================
    # 7. CLOSE TESTS (32 - 35)
    # ==========================================

    def test_32_to_34_close_verified_ticket(self):
        create_res = self.service.create_investigation(tester_description="Defect", reporter="tester")
        record_key = create_res.data["record_key"]
        self.service.confirm_bug(record_key, module="SFN", ticket_data={"title": "SFN defect"})
        self.service.start_work(record_key, assignee="dev1", actor="dev1")
        self.service.submit_fix(record_key, "dev1", "Fix", "branch", "instructions")
        self.service.verify(record_key, {"confirmed": True, "verdict": "VERIFIED", "confirmedBy": "qa", "notes": "ok"}, actor="qa")

        close_res = self.service.close(record_key, actor="admin", summary="Resolved in v1.0")
        self.assertTrue(close_res.success)

        # 32. CLOSED status & 33. RESOLVED lifecycle phase
        self.assertEqual(close_res.data["status"], "CLOSED")
        self.assertEqual(close_res.data["lifecycle_phase"], "RESOLVED")
        self.assertIsNotNone(close_res.data["resolution_json"])

    def test_35_invalid_close_from_open_rejected(self):
        create_res = self.service.create_investigation(tester_description="Defect", reporter="tester")
        record_key = create_res.data["record_key"]
        self.service.confirm_bug(record_key, module="SFN", ticket_data={"title": "SFN defect"})

        # Cannot close OPEN ticket directly
        close_res = self.service.close(record_key, actor="admin")
        self.assertFalse(close_res.success)
        self.assertIn("Cannot close record with status 'OPEN'. Must be 'VERIFIED'.", close_res.error)

        inv = self.service.repo.get_investigation_by_record_key(record_key)
        self.assertEqual(inv["status"], "OPEN")

    # ==========================================
    # 8. BLOCK TESTS (36 - 38)
    # ==========================================

    def test_36_to_38_block_action(self):
        create_res = self.service.create_investigation(tester_description="Defect", reporter="tester")
        record_key = create_res.data["record_key"]
        self.service.confirm_bug(record_key, module="SFN", ticket_data={"title": "SFN defect"})

        # 37. BLOCK without reason fails
        block_fail = self.service.block(record_key, reason="", actor="dev")
        self.assertFalse(block_fail.success)
        self.assertIn("requires an explicit non-empty reason", block_fail.error)

        # 36. Valid BLOCK succeeds
        block_ok = self.service.block(record_key, reason="Waiting for API gateway v2", actor="dev")
        self.assertTrue(block_ok.success)
        self.assertEqual(block_ok.data["status"], "BLOCKED")

        # 38. UNBLOCK remains unsupported
        # Attempting to start work or submit fix on BLOCKED is rejected
        work_res = self.service.start_work(record_key, assignee="dev", actor="dev")
        self.assertFalse(work_res.success)
        self.assertIn("Must be 'OPEN'", work_res.error)

    # ==========================================
    # 9. CONCURRENCY & STALE STATE (39 - 40)
    # ==========================================

    def test_39_and_40_stale_state_cannot_bypass_lifecycle(self):
        # Two service clients on same DB
        conn2 = get_connection(self.db_path)
        service2 = ResolutionService(conn2)

        create_res = self.service.create_investigation(tester_description="Defect", reporter="tester")
        record_key = create_res.data["record_key"]
        self.service.confirm_bug(record_key, module="SFN", ticket_data={"title": "SFN defect"})

        # User A starts work -> FIXING
        res_a = self.service.start_work(record_key, assignee="dev-A", actor="dev-A")
        self.assertTrue(res_a.success)

        # User B attempts start work assuming it is still OPEN
        res_b = service2.start_work(record_key, assignee="dev-B", actor="dev-B")
        self.assertFalse(res_b.success)
        self.assertIn("Cannot start work when status is 'FIXING'. Must be 'OPEN'.", res_b.error)

        conn2.close()

    # ==========================================
    # 10. AUDIT ATOMICITY (41 - 43)
    # ==========================================

    def test_41_to_43_audit_atomicity_and_rollback(self):
        create_res = self.service.create_investigation(tester_description="Defect", reporter="tester")
        record_key = create_res.data["record_key"]
        self.service.confirm_bug(record_key, module="SFN", ticket_data={"title": "SFN defect"})

        # Monkey-patch repository.insert_audit_event to simulate failure
        original_insert_audit = self.service.repo.insert_audit_event

        def failing_audit(*args, **kwargs):
            raise sqlite3.OperationalError("Simulated disk error writing audit log")

        self.service.repo.insert_audit_event = failing_audit

        # Attempt to start work
        work_res = self.service.start_work(record_key, assignee="dev1", actor="dev1")
        self.assertFalse(work_res.success)
        self.assertIn("Simulated disk error writing audit log", work_res.error)

        # Restore method
        self.service.repo.insert_audit_event = original_insert_audit

        # 43. Status in DB remains OPEN (rolled back atomically)
        inv = self.service.repo.get_investigation_by_record_key(record_key)
        self.assertEqual(inv["status"], "OPEN")
        self.assertIsNone(inv["assignee"])

    # ==========================================
    # 11. HISTORY PRESERVATION (44 - 46)
    # ==========================================

    def test_44_to_46_history_preservation_across_cycles(self):
        create_res = self.service.create_investigation(tester_description="Defect", reporter="tester")
        record_key = create_res.data["record_key"]
        self.service.confirm_bug(record_key, module="SFN", ticket_data={"title": "SFN defect"})

        # Cycle 1: Start -> Fix 1 -> Fail Retest
        self.service.start_work(record_key, "dev1", "dev1")
        self.service.submit_fix(record_key, "dev1", "Fix 1", "b1", "i1")
        self.service.submit_retest(record_key, ["EVD-1"], {"confirmed": True, "verdict": "RETURNED_TO_FIXING", "confirmedBy": "qa", "notes": "fail 1"}, "qa")

        # Cycle 2: Fix 2 -> Retest Pass -> Verify -> Close
        self.service.submit_fix(record_key, "dev1", "Fix 2 after review", "b2", "i2")
        self.service.verify(record_key, {"confirmed": True, "verdict": "VERIFIED", "confirmedBy": "qa", "notes": "pass 2"}, "qa")
        self.service.close(record_key, "admin")

        cursor = self.conn.cursor()
        # 45. Both DeveloperUpdates preserved
        cursor.execute("SELECT summary_of_changes FROM developer_updates WHERE investigation_key = ? ORDER BY submitted_at ASC;", (record_key,))
        dev_summaries = [r[0] for r in cursor.fetchall()]
        self.assertEqual(dev_summaries, ["Fix 1", "Fix 2 after review"])

        # 46. RetestArtifact preserved
        cursor.execute("SELECT id FROM retest_artifacts WHERE investigation_key = ?;", (record_key,))
        self.assertEqual(len(cursor.fetchall()), 1)


if __name__ == "__main__":
    unittest.main()
