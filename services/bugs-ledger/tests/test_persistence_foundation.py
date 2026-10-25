"""
tests/test_persistence_foundation.py

Phase 01G — SQLite Schema & Persistence Foundation Test Suite
Validates:
- All 10 tables, indexes, and constraints
- Foreign key enforcement
- Internal vs business identity separation (record_key vs investigation_id / canonical_bug_id)
- Atomic ID allocation and legacy seeding
- Concurrency test with multiple workers on a file-backed SQLite database
- Duplicate byte content evidence allowed
- Append-only artifact collections
- Legacy sequence seeding
"""

import unittest
import os
import shutil
import tempfile
import sqlite3
import concurrent.futures
from typing import List

from core.storage.schema import init_db
from core.storage.db import get_connection, AtomicIdAllocator
from core.storage.repository import InvestigationRepository

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BUGS_DIR = os.path.join(BASE_DIR, "ART-Product-Validation/bugs")


class TestPersistenceFoundation(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="art_test_db_")
        self.db_path = os.path.join(self.test_dir, "test_resolution.db")
        self.conn = get_connection(self.db_path)
        init_db(self.conn)
        self.repo = InvestigationRepository(self.conn)

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # ==========================================
    # SCHEMA & CONSTRAINTS TESTS (1 - 9)
    # ==========================================

    def test_01_all_10_tables_created(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = set([r[0] for r in cursor.fetchall()])
        expected_tables = {
            "id_allocations",
            "investigations",
            "original_inputs",
            "evidence",
            "ai_artifacts",
            "research_artifacts",
            "ticket_revisions",
            "developer_updates",
            "retest_artifacts",
            "audit_events"
        }
        self.assertTrue(expected_tables.issubset(tables))

    def test_02_foreign_keys_are_enabled(self):
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA foreign_keys;")
        self.assertEqual(cursor.fetchone()[0], 1)

    def test_03_invalid_source_kind_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.create_investigation(
                record_key="REC-01",
                source_kind="INVALID_KIND",  # must be NATIVE or LEGACY_IMPORT
                slug="test",
                lifecycle_phase="CAPTURE",
                original_input_id="INP-01"
            )

    def test_04_invalid_lifecycle_phase_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.create_investigation(
                record_key="REC-01",
                source_kind="NATIVE",
                slug="test",
                lifecycle_phase="INVALID_PHASE",
                original_input_id="INP-01"
            )

    def test_05_invalid_canonical_status_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.create_investigation(
                record_key="REC-01",
                source_kind="NATIVE",
                slug="test",
                lifecycle_phase="CONFIRMED",
                status="INVALID_STATUS",
                original_input_id="INP-01"
            )

    def test_06_invalid_classification_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.create_investigation(
                record_key="REC-01",
                source_kind="NATIVE",
                slug="test",
                lifecycle_phase="CAPTURE",
                classification="INVALID_CLASSIFICATION",
                original_input_id="INP-01"
            )

    def test_07_invalid_evidence_stage_rejected(self):
        self.repo.create_investigation(
            record_key="REC-01",
            source_kind="NATIVE",
            slug="test",
            lifecycle_phase="CAPTURE",
            original_input_id="INP-01"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.insert_evidence(
                evidence_id="EVD-01",
                investigation_key="REC-01",
                stage="INVALID_STAGE",
                evidence_type="SCREENSHOT",
                original_filename="a.png",
                canonical_filename="a.png",
                storage_path="path/a.png",
                sha256="abc",
                mime_type="image/png",
                byte_size=100,
                uploaded_by="user",
                captured_at="2026-09-25T00:00:00Z"
            )

    def test_08_invalid_evidence_type_rejected(self):
        self.repo.create_investigation(
            record_key="REC-01",
            source_kind="NATIVE",
            slug="test",
            lifecycle_phase="CAPTURE",
            original_input_id="INP-01"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.insert_evidence(
                evidence_id="EVD-01",
                investigation_key="REC-01",
                stage="ORIGINAL",
                evidence_type="INVALID_TYPE",
                original_filename="a.png",
                canonical_filename="a.png",
                storage_path="path/a.png",
                sha256="abc",
                mime_type="image/png",
                byte_size=100,
                uploaded_by="user",
                captured_at="2026-09-25T00:00:00Z"
            )

    def test_09_foreign_key_violation_rejected(self):
        # Insert evidence for nonexistent investigation record_key
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.insert_evidence(
                evidence_id="EVD-01",
                investigation_key="NONEXISTENT_KEY",
                stage="ORIGINAL",
                evidence_type="SCREENSHOT",
                original_filename="a.png",
                canonical_filename="a.png",
                storage_path="path/a.png",
                sha256="abc",
                mime_type="image/png",
                byte_size=100,
                uploaded_by="user",
                captured_at="2026-09-25T00:00:00Z"
            )

    # ==========================================
    # IDENTITY & PERSISTENCE KEY TESTS (10 - 13)
    # ==========================================

    def test_10_native_investigation_stores_inv_business_id(self):
        inv = self.repo.create_investigation(
            record_key="KEY-UUID-001",
            investigation_id="INV-20260925-0001",
            canonical_bug_id=None,
            source_kind="NATIVE",
            slug="native-defect",
            lifecycle_phase="CAPTURE",
            original_input_id="INP-01"
        )
        self.assertEqual(inv["record_key"], "KEY-UUID-001")
        self.assertEqual(inv["investigation_id"], "INV-20260925-0001")
        self.assertIsNone(inv["canonical_bug_id"])

        fetched = self.repo.get_investigation_by_investigation_id("INV-20260925-0001")
        self.assertEqual(fetched["record_key"], "KEY-UUID-001")

    def test_11_legacy_investigation_stores_null_inv_id(self):
        legacy = self.repo.create_investigation(
            record_key="LEGACY-AGENT-001",
            investigation_id=None,
            canonical_bug_id="ART-AGENT-001",
            source_kind="LEGACY_IMPORT",
            slug="structured-output-contract",
            lifecycle_phase="CONFIRMED",
            status="OPEN",
            classification="BUG",
            module="AGENT",
            original_input_id="INP-LEG-01"
        )
        self.assertIsNone(legacy["investigation_id"])
        self.assertEqual(legacy["canonical_bug_id"], "ART-AGENT-001")
        self.assertEqual(legacy["source_kind"], "LEGACY_IMPORT")

        fetched = self.repo.get_investigation_by_canonical_bug_id("ART-AGENT-001")
        self.assertEqual(fetched["record_key"], "LEGACY-AGENT-001")

    def test_12_duplicate_investigation_id_rejected(self):
        self.repo.create_investigation(
            record_key="KEY-01",
            investigation_id="INV-20260925-0001",
            source_kind="NATIVE",
            slug="one",
            lifecycle_phase="CAPTURE",
            original_input_id="INP-01"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.create_investigation(
                record_key="KEY-02",
                investigation_id="INV-20260925-0001",  # duplicate business ID
                source_kind="NATIVE",
                slug="two",
                lifecycle_phase="CAPTURE",
                original_input_id="INP-02"
            )

    def test_13_duplicate_canonical_bug_id_rejected(self):
        self.repo.create_investigation(
            record_key="KEY-01",
            canonical_bug_id="ART-AGENT-001",
            source_kind="LEGACY_IMPORT",
            slug="one",
            lifecycle_phase="CONFIRMED",
            original_input_id="INP-01"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.create_investigation(
                record_key="KEY-02",
                canonical_bug_id="ART-AGENT-001",  # duplicate bug ID
                source_kind="NATIVE",
                slug="two",
                lifecycle_phase="CONFIRMED",
                original_input_id="INP-02"
            )

    # ==========================================
    # ATOMIC ALLOCATOR TESTS (14 - 22)
    # ==========================================

    def test_14_inv_allocation_starts_correctly(self):
        inv_id = AtomicIdAllocator.allocate_investigation_id(self.conn, "20260925")
        self.assertEqual(inv_id, "INV-20260925-0001")

    def test_15_inv_allocation_increments_correctly(self):
        id1 = AtomicIdAllocator.allocate_investigation_id(self.conn, "20260925")
        id2 = AtomicIdAllocator.allocate_investigation_id(self.conn, "20260925")
        id3 = AtomicIdAllocator.allocate_investigation_id(self.conn, "20260925")
        self.assertEqual(id1, "INV-20260925-0001")
        self.assertEqual(id2, "INV-20260925-0002")
        self.assertEqual(id3, "INV-20260925-0003")

    def test_16_different_dates_use_independent_scopes(self):
        id_day1 = AtomicIdAllocator.allocate_investigation_id(self.conn, "20260924")
        id_day2 = AtomicIdAllocator.allocate_investigation_id(self.conn, "20260925")
        self.assertEqual(id_day1, "INV-20260924-0001")
        self.assertEqual(id_day2, "INV-20260925-0001")

    def test_17_art_bug_allocation_increments_per_module(self):
        agent1 = AtomicIdAllocator.allocate_bug_id(self.conn, "AGENT")
        gov1 = AtomicIdAllocator.allocate_bug_id(self.conn, "GOV")
        agent2 = AtomicIdAllocator.allocate_bug_id(self.conn, "AGENT")
        self.assertEqual(agent1, "ART-AGENT-001")
        self.assertEqual(gov1, "ART-GOV-001")
        self.assertEqual(agent2, "ART-AGENT-002")

    def test_18_ensure_minimum_sequence_initializes_missing(self):
        res = AtomicIdAllocator.ensure_minimum_sequence(self.conn, "BUG:GOV", 3)
        self.assertEqual(res, 3)
        # Next allocate should be 4
        next_gov = AtomicIdAllocator.allocate_bug_id(self.conn, "GOV")
        self.assertEqual(next_gov, "ART-GOV-004")

    def test_19_ensure_minimum_sequence_advances_lower(self):
        # Allocate 1
        id1 = AtomicIdAllocator.allocate_bug_id(self.conn, "SFN")
        self.assertEqual(id1, "ART-SFN-001")
        # Advance to 5
        res = AtomicIdAllocator.ensure_minimum_sequence(self.conn, "BUG:SFN", 5)
        self.assertEqual(res, 5)
        # Next allocate should be 6
        id6 = AtomicIdAllocator.allocate_bug_id(self.conn, "SFN")
        self.assertEqual(id6, "ART-SFN-006")

    def test_20_ensure_minimum_sequence_never_decreases(self):
        AtomicIdAllocator.ensure_minimum_sequence(self.conn, "BUG:SFN", 10)
        # Attempt to set lower (e.g. 4)
        res = AtomicIdAllocator.ensure_minimum_sequence(self.conn, "BUG:SFN", 4)
        self.assertEqual(res, 10)
        # Next allocate remains 11
        id11 = AtomicIdAllocator.allocate_bug_id(self.conn, "SFN")
        self.assertEqual(id11, "ART-SFN-011")

    def test_21_rolled_back_allocation_restores_previous_counter(self):
        # Start manual transaction
        cursor = self.conn.cursor()
        cursor.execute("BEGIN IMMEDIATE;")
        inv_id = AtomicIdAllocator.allocate_investigation_id(self.conn, "20260925")
        self.assertEqual(inv_id, "INV-20260925-0001")
        # Rollback transaction
        cursor.execute("ROLLBACK;")

        # Next allocation on the scope re-allocates 0001 because SQLite rolled back the row update
        next_id = AtomicIdAllocator.allocate_investigation_id(self.conn, "20260925")
        self.assertEqual(next_id, "INV-20260925-0001")

    def test_22_concurrent_allocation_no_duplicates(self):
        # File-backed database concurrency proof
        def worker(db_file: str, date_str: str) -> str:
            c = get_connection(db_file)
            cur = c.cursor()
            cur.execute("BEGIN IMMEDIATE;")
            allocated_id = AtomicIdAllocator.allocate_investigation_id(c, date_str)
            cur.execute("COMMIT;")
            c.close()
            return allocated_id

        num_workers = 15
        date_str = "20260925"
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker, self.db_path, date_str) for _ in range(num_workers)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        self.assertEqual(len(results), num_workers)
        # Verify 100% unique sequence allocations
        unique_results = set(results)
        self.assertEqual(len(unique_results), num_workers)

    # ==========================================
    # EVIDENCE DUPLICATE CONTENT TESTS (23 - 27)
    # ==========================================

    def test_23_to_25_evidence_metadata_and_duplicates(self):
        self.repo.create_investigation(
            record_key="INV-REC-01",
            investigation_id="INV-20260925-0001",
            source_kind="NATIVE",
            slug="defect",
            lifecycle_phase="CAPTURE",
            original_input_id="INP-01"
        )
        same_hash = "d4beaebc28b722aec6ace580b836782e517fe9129a8e568f67c546a0482b4874"

        # 23. Insert evidence
        ev1 = self.repo.insert_evidence(
            evidence_id="EVD-01",
            investigation_key="INV-REC-01",
            stage="ORIGINAL",
            evidence_type="SCREENSHOT",
            original_filename="screen1.png",
            canonical_filename="EVD-01__screen1.png",
            storage_path="data/evidence/screen1.png",
            sha256=same_hash,
            mime_type="image/png",
            byte_size=1024,
            uploaded_by="user",
            captured_at="2026-09-25T12:00:00Z"
        )
        self.assertEqual(ev1["id"], "EVD-01")

        # 24. Duplicate SHA-256 in same investigation is ALLOWED
        ev2 = self.repo.insert_evidence(
            evidence_id="EVD-02",
            investigation_key="INV-REC-01",
            stage="RETEST",
            evidence_type="SCREENSHOT",
            original_filename="screen2.png",
            canonical_filename="EVD-02__screen2.png",
            storage_path="data/evidence/screen2.png",
            sha256=same_hash,  # IDENTICAL HASH
            mime_type="image/png",
            byte_size=1024,
            uploaded_by="user",
            captured_at="2026-09-25T14:00:00Z"
        )
        self.assertEqual(ev2["id"], "EVD-02")
        self.assertEqual(ev1["sha256"], ev2["sha256"])

        # 25. Duplicate Evidence ID is REJECTED
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.insert_evidence(
                evidence_id="EVD-01",  # duplicate ID
                investigation_key="INV-REC-01",
                stage="SUPPLEMENTAL",
                evidence_type="SCREENSHOT",
                original_filename="screen3.png",
                canonical_filename="EVD-01__dup.png",
                storage_path="data/evidence/screen3.png",
                sha256="different_hash",
                mime_type="image/png",
                byte_size=100,
                uploaded_by="user",
                captured_at="2026-09-25T15:00:00Z"
            )

    def test_26_evidence_for_nonexistent_inv_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.insert_evidence(
                evidence_id="EVD-99",
                investigation_key="NONEXISTENT",
                stage="ORIGINAL",
                evidence_type="SCREENSHOT",
                original_filename="a.png",
                canonical_filename="a.png",
                storage_path="p/a.png",
                sha256="h",
                mime_type="image/png",
                byte_size=10,
                uploaded_by="u",
                captured_at="2026-09-25T12:00:00Z"
            )

    def test_27_no_binary_evidence_stored_in_db(self):
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(evidence);")
        columns = {r[1]: r[2] for r in cursor.fetchall()}
        self.assertNotIn("bytes", columns)
        self.assertNotIn("content", columns)
        self.assertNotIn("data", columns)
        self.assertIn("storage_path", columns)
        self.assertIn("sha256", columns)

    # ==========================================
    # APPEND-ONLY HISTORY TESTS (28 - 34)
    # ==========================================

    def test_28_to_34_append_only_history_collections(self):
        self.repo.create_investigation(
            record_key="INV-KEY-HIST",
            investigation_id="INV-20260925-0001",
            source_kind="NATIVE",
            slug="history-test",
            lifecycle_phase="CONFIRMED",
            original_input_id="INP-01"
        )

        # 28. Multiple AI artifacts
        self.repo.insert_ai_artifact(
            generation_id="GEN-01",
            investigation_key="INV-KEY-HIST",
            purpose="CAPTURE_ANALYSIS",
            model_identifier="gpt-4o",
            input_evidence_ids=["EVD-01"],
            structured_output={"facts": []},
            generated_at="2026-09-25T12:00:00Z"
        )
        self.repo.insert_ai_artifact(
            generation_id="GEN-02",
            investigation_key="INV-KEY-HIST",
            purpose="TICKET_DRAFTING",
            model_identifier="gpt-4o",
            input_evidence_ids=["EVD-01"],
            structured_output={"facts": []},
            generated_at="2026-09-25T12:01:00Z"
        )

        # 29. Multiple research artifacts
        self.repo.insert_research_artifact(
            research_id="RES-01",
            investigation_key="INV-KEY-HIST",
            research_question="Question 1?",
            trigger_reason="Trigger 1",
            sources=[],
            observations=[],
            relevance_to_art="Rel 1",
            possible_art_approach="App 1",
            generated_at="2026-09-25T12:02:00Z"
        )
        self.repo.insert_research_artifact(
            research_id="RES-02",
            investigation_key="INV-KEY-HIST",
            research_question="Question 2?",
            trigger_reason="Trigger 2",
            sources=[],
            observations=[],
            relevance_to_art="Rel 2",
            possible_art_approach="App 2",
            generated_at="2026-09-25T12:03:00Z"
        )

        # 30. Multiple ticket revisions
        self.repo.insert_ticket_revision(
            ticket_id="TCK-01",
            investigation_key="INV-KEY-HIST",
            revision=1,
            title="Title Rev 1",
            repro_steps="Not provided",
            expected_result="Exp 1",
            actual_result="Act 1",
            business_impact="Not provided",
            recommended_solution="Sol 1",
            module="AGENT",
            environment="Not provided",
            severity="HIGH",
            priority="Not provided",
            tags=[],
            discussion=[],
            updated_at="2026-09-25T12:04:00Z"
        )
        self.repo.insert_ticket_revision(
            ticket_id="TCK-02",
            investigation_key="INV-KEY-HIST",
            revision=2,
            title="Title Rev 2",
            repro_steps="Not provided",
            expected_result="Exp 2",
            actual_result="Act 2",
            business_impact="Not provided",
            recommended_solution="Sol 2",
            module="AGENT",
            environment="Not provided",
            severity="HIGH",
            priority="Not provided",
            tags=[],
            discussion=[],
            updated_at="2026-09-25T12:05:00Z"
        )

        # 31. Duplicate ticket revision rejected
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.insert_ticket_revision(
                ticket_id="TCK-03",
                investigation_key="INV-KEY-HIST",
                revision=1,  # DUPLICATE revision=1 for same investigation
                title="Duplicate Rev",
                repro_steps="Not provided",
                expected_result="Exp",
                actual_result="Act",
                business_impact="Not provided",
                recommended_solution="Sol",
                module="AGENT",
                environment="Not provided",
                severity="HIGH",
                priority="Not provided",
                tags=[],
                discussion=[],
                updated_at="2026-09-25T12:06:00Z"
            )

        # 32. Multiple developer updates
        self.repo.insert_developer_update(
            dev_id="DEV-01",
            investigation_key="INV-KEY-HIST",
            developer_username="dev1",
            summary_of_changes="Fix 1",
            commit_hash_or_pr="c1",
            resolved_in_version_or_branch="fix/1",
            test_instructions_for_qa="test 1",
            submitted_at="2026-09-25T12:07:00Z"
        )
        self.repo.insert_developer_update(
            dev_id="DEV-02",
            investigation_key="INV-KEY-HIST",
            developer_username="dev1",
            summary_of_changes="Fix 2 after failed retest",
            commit_hash_or_pr="c2",
            resolved_in_version_or_branch="fix/2",
            test_instructions_for_qa="test 2",
            submitted_at="2026-09-25T12:08:00Z"
        )

        # 33. Multiple retest artifacts
        self.repo.insert_retest_artifact(
            retest_id="RET-01",
            investigation_key="INV-KEY-HIST",
            retest_evidence_ids=["EVD-01"],
            human_confirmation={"confirmed": True, "verdict": "RETURNED_TO_FIXING", "confirmedBy": "qa", "notes": "failed"},
            executed_at="2026-09-25T12:09:00Z"
        )
        self.repo.insert_retest_artifact(
            retest_id="RET-02",
            investigation_key="INV-KEY-HIST",
            retest_evidence_ids=["EVD-02"],
            human_confirmation={"confirmed": True, "verdict": "VERIFIED", "confirmedBy": "qa", "notes": "passed"},
            executed_at="2026-09-25T12:10:00Z"
        )

        # 34. Multiple audit events
        self.repo.insert_audit_event(
            event_id="AUD-01",
            investigation_key="INV-KEY-HIST",
            timestamp="2026-09-25T12:00:00Z",
            actor="tester",
            event_type="INVESTIGATION_CAPTURED",
            summary="Captured"
        )
        self.repo.insert_audit_event(
            event_id="AUD-02",
            investigation_key="INV-KEY-HIST",
            timestamp="2026-09-25T12:10:00Z",
            actor="tester",
            event_type="VERIFIED",
            summary="Verified"
        )

        # Verify query primitives
        revs = self.repo.list_ticket_revisions_for_investigation("INV-KEY-HIST")
        self.assertEqual(len(revs), 2)
        audits = self.repo.list_audit_events_for_investigation("INV-KEY-HIST")
        self.assertEqual(len(audits), 2)

    # ==========================================
    # LEGACY REPOSITORY SEEDING TESTS (35 - 36)
    # ==========================================

    def test_35_and_36_legacy_id_seeding(self):
        # 35. Read-only scan of actual legacy bugs
        legacy_dirs = [d for root, dirs, _ in os.walk(BUGS_DIR) for d in dirs if d.startswith("ART-")]
        legacy_bug_ids = set([d.split("__")[0] for d in legacy_dirs if d.split("__")[0] in {"ART-AGENT-001", "ART-GOV-002", "ART-GOV-003", "ART-SFN-001"}])
        self.assertEqual(legacy_bug_ids, {"ART-AGENT-001", "ART-GOV-002", "ART-GOV-003", "ART-SFN-001"})

        # Seed scopes into allocator
        AtomicIdAllocator.ensure_minimum_sequence(self.conn, "BUG:AGENT", 1)
        AtomicIdAllocator.ensure_minimum_sequence(self.conn, "BUG:GOV", 3)
        AtomicIdAllocator.ensure_minimum_sequence(self.conn, "BUG:SFN", 1)

        # 36. Next candidate allocations
        next_agent = AtomicIdAllocator.allocate_bug_id(self.conn, "AGENT")
        next_gov = AtomicIdAllocator.allocate_bug_id(self.conn, "GOV")
        next_sfn = AtomicIdAllocator.allocate_bug_id(self.conn, "SFN")

        self.assertEqual(next_agent, "ART-AGENT-002")
        self.assertEqual(next_gov, "ART-GOV-004")
        self.assertEqual(next_sfn, "ART-SFN-002")


if __name__ == "__main__":
    unittest.main()
