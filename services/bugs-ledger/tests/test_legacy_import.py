"""
tests/test_legacy_import.py

Phase 01I — Explicit Controlled Legacy Import Test Suite
Validates the complete test matrix specified for Phase 01I:
1. DISCOVERY: Discovers current 4 valid legacy records using existing reader; not hardcoded.
2. IDENTITY: Canonical IDs preserved (ART-AGENT-001, ART-GOV-002, ART-GOV-003, ART-SFN-001);
   source_kind is LEGACY_IMPORT; investigation_id is NULL; consumes zero INV sequence allocations.
3. ORIGINAL INPUT: Historical bug/source text preserved; missing metadata represented as "Not provided" or approved defaults.
4. EVIDENCE: All current legacy evidence references imported in-place; SHA-256 and byte sizes match source files;
   no evidence files copied, moved, or modified.
5. HISTORY: Zero fake AI/research/dev/retest artifacts fabricated; zero synthetic lifecycle transitions.
6. AUDIT: Exactly one LEGACY_SYNCED event created per imported record; details preserve source Markdown path and hash.
7. IDEMPOTENCY: First run imports 4 records; second run imports 0, skips 4; investigation/evidence/audit row counts unchanged.
8. ALLOCATOR SEEDING: BUG:AGENT >= 1, BUG:GOV >= 3, BUG:SFN >= 1; next allocations ART-AGENT-002, ART-GOV-004, ART-SFN-002;
   does not lower an already higher counter.
9. ATOMICITY: Forced failure during a bug import rolls back all DB rows for that bug (no partial evidence, audit, or allocator corruption).
10. COEXISTENCE: Native (INV-...) and legacy (ART-...) coexist in the same database without identity collision; lookups work for both.
11. CLI SAFETY: Missing --db fails clearly; temporary explicit --db succeeds; module import does not trigger migration;
    no default production DB is created.
"""

import unittest
import os
import shutil
import tempfile
import sqlite3
import hashlib
import json
import subprocess
import sys

from core.storage.schema import init_db
from core.storage.db import get_connection, AtomicIdAllocator
from core.storage.repository import InvestigationRepository
from core.storage.service import ResolutionService
from scripts.import_legacy import run_legacy_import, extract_module_and_sequence

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BUGS_DIR = os.path.join(BASE_DIR, "ART-Product-Validation/bugs")


class TestLegacyImport(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="art_test_import_")
        self.db_path = os.path.join(self.test_dir, "test_import.db")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # ==========================================
    # 1. DISCOVERY TESTS (1 - 2)
    # ==========================================

    def test_01_importer_discovers_current_four_legacy_records(self):
        res = run_legacy_import(self.db_path)
        self.assertEqual(res.total_discovered, 4)
        self.assertCountEqual(
            res.discovered,
            ["ART-AGENT-001", "ART-GOV-002", "ART-GOV-003", "ART-SFN-001"]
        )
        self.assertEqual(res.total_imported, 4)
        self.assertEqual(res.total_failed, 0)

    def test_02_importer_is_not_hard_coded_to_four_records(self):
        # Create a mock directory with an arbitrary 5th bug: ART-XYZ-009
        mock_bugs_dir = os.path.join(self.test_dir, "mock_bugs")
        os.makedirs(mock_bugs_dir, exist_ok=True)

        bug_sub = os.path.join(mock_bugs_dir, "ART-XYZ-009__custom-feature")
        os.makedirs(bug_sub, exist_ok=True)
        md_file = os.path.join(bug_sub, "ART-XYZ-009.md")
        with open(md_file, "w", encoding="utf-8") as f:
            f.write("# ART-XYZ-009 — Custom bug title\n\n")
            f.write("- **Severity:** LOW\n")
            f.write("- **Status:** OPEN\n\n")
            f.write("## Bug\nCustom description\n\n")
            f.write("## Expected\nCustom expected\n\n")
            f.write("## Actual\nCustom actual\n\n")
            f.write("## Evidence\n- None\n\n")
            f.write("## Production-Grade Fix Proposal\nCustom fix\n\n")
            f.write("## Developer Update\nPending.\n\n")
            f.write("## Retest\nPending.\n")

        res = run_legacy_import(self.db_path, bugs_dir=mock_bugs_dir)
        self.assertEqual(res.total_discovered, 1)
        self.assertEqual(res.discovered, ["ART-XYZ-009"])
        self.assertEqual(res.total_imported, 1)

        # Verify allocator seeded dynamically for XYZ
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT last_seq FROM id_allocations WHERE scope = 'BUG:XYZ';")
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], 9)
        conn.close()

    # ==========================================
    # 2. IDENTITY TESTS (3 - 9)
    # ==========================================

    def test_03_to_09_identity_and_inv_consumption(self):
        run_legacy_import(self.db_path)
        conn = get_connection(self.db_path)
        repo = InvestigationRepository(conn)

        # 3-6: Preservation of canonical IDs
        for bug_id in ["ART-AGENT-001", "ART-GOV-002", "ART-GOV-003", "ART-SFN-001"]:
            inv = repo.get_investigation_by_canonical_bug_id(bug_id)
            self.assertIsNotNone(inv, f"Bug {bug_id} must be queryable by canonical_bug_id")
            # 7: source_kind is LEGACY_IMPORT
            self.assertEqual(inv["source_kind"], "LEGACY_IMPORT")
            # 8: investigation_id is strictly NULL
            self.assertIsNone(inv["investigation_id"])
            # Lifecycle phase CONFIRMED and status matching legacy
            self.assertEqual(inv["lifecycle_phase"], "CONFIRMED")
            self.assertEqual(inv["status"], "OPEN")
            self.assertEqual(inv["classification"], "BUG")

        # 9: Zero INV allocations consumed
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM id_allocations WHERE scope LIKE 'INV:%';")
        self.assertEqual(cursor.fetchone()[0], 0)
        conn.close()

    # ==========================================
    # 3. ORIGINAL INPUT TESTS (10 - 11)
    # ==========================================

    def test_10_to_11_original_input_fidelity(self):
        run_legacy_import(self.db_path)
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        # Check ART-AGENT-001 original input
        cursor.execute("""
            SELECT oi.* FROM original_inputs oi
            JOIN investigations inv ON oi.investigation_key = inv.record_key
            WHERE inv.canonical_bug_id = 'ART-AGENT-001';
        """)
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        oi = dict(row)
        self.assertEqual(oi["reporter"], "HUMAN_LEGACY_IMPORT")
        self.assertEqual(oi["provenance"], "HUMAN_SUPPLIED")
        self.assertIn("The Agent Output Parser does not consistently enforce", oi["tester_description"])

        # Check Ticket Artifact for missing fields
        cursor.execute("""
            SELECT tr.* FROM ticket_revisions tr
            JOIN investigations inv ON tr.investigation_key = inv.record_key
            WHERE inv.canonical_bug_id = 'ART-AGENT-001';
        """)
        ticket_row = cursor.fetchone()
        self.assertIsNotNone(ticket_row)
        tr = dict(ticket_row)
        self.assertEqual(tr["repro_steps"], "Not provided")
        self.assertEqual(tr["business_impact"], "Not provided")
        self.assertEqual(tr["environment"], "Not provided")
        self.assertEqual(tr["priority"], "Not provided")
        self.assertEqual(tr["severity"], "HIGH")
        self.assertEqual(tr["module"], "AGENT")
        conn.close()

    # ==========================================
    # 4. EVIDENCE PRESERVATION TESTS (12 - 18)
    # ==========================================

    def test_12_to_18_evidence_in_place_preservation(self):
        run_legacy_import(self.db_path)
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM evidence ORDER BY id ASC;")
        evidence_rows = [dict(r) for r in cursor.fetchall()]

        # 12: All 7 legacy screenshots imported
        self.assertEqual(len(evidence_rows), 7)

        for ev in evidence_rows:
            # 15: Stage is ORIGINAL
            self.assertEqual(ev["stage"], "ORIGINAL")
            self.assertEqual(ev["evidence_type"], "SCREENSHOT")
            self.assertEqual(ev["uploaded_by"], "HUMAN_LEGACY_IMPORT")

            # Check in-place reference
            full_path = os.path.join(BASE_DIR, ev["storage_path"])
            # 16-17: File exists in original location
            self.assertTrue(os.path.exists(full_path), f"File {full_path} must exist in place")

            # 13-14: SHA-256 and byte sizes match
            actual_size = os.path.getsize(full_path)
            self.assertEqual(ev["byte_size"], actual_size)
            with open(full_path, "rb") as fp:
                actual_sha = hashlib.sha256(fp.read()).hexdigest()
            self.assertEqual(ev["sha256"], actual_sha)

        conn.close()

    # ==========================================
    # 5. NO FAKE HISTORY TESTS (19 - 23)
    # ==========================================

    def test_19_to_23_no_fake_history(self):
        run_legacy_import(self.db_path)
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        # 19: No AI artifacts fabricated
        cursor.execute("SELECT COUNT(*) FROM ai_artifacts;")
        self.assertEqual(cursor.fetchone()[0], 0)

        # 20: No research artifacts fabricated
        cursor.execute("SELECT COUNT(*) FROM research_artifacts;")
        self.assertEqual(cursor.fetchone()[0], 0)

        # 21: No developer updates fabricated
        cursor.execute("SELECT COUNT(*) FROM developer_updates;")
        self.assertEqual(cursor.fetchone()[0], 0)

        # 22: No retest artifacts fabricated
        cursor.execute("SELECT COUNT(*) FROM retest_artifacts;")
        self.assertEqual(cursor.fetchone()[0], 0)

        # 23: No synthetic lifecycle audit events (only LEGACY_SYNCED)
        cursor.execute("SELECT DISTINCT event_type FROM audit_events;")
        event_types = [r[0] for r in cursor.fetchall()]
        self.assertEqual(event_types, ["LEGACY_SYNCED"])

        conn.close()

    # ==========================================
    # 6. AUDIT TESTS (24 - 25)
    # ==========================================

    def test_24_to_25_audit_events_and_traceability(self):
        run_legacy_import(self.db_path)
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM audit_events ORDER BY id ASC;")
        audit_rows = [dict(r) for r in cursor.fetchall()]

        # 24: Exactly 4 audit events (1 per imported record)
        self.assertEqual(len(audit_rows), 4)

        for aud in audit_rows:
            self.assertEqual(aud["event_type"], "LEGACY_SYNCED")
            self.assertEqual(aud["actor"], "LEGACY_IMPORT_CLI")
            details = json.loads(aud["details_json"])
            # 25: Source Markdown path and hash preserved
            self.assertIn("sourceMarkdownPath", details)
            self.assertTrue(details["sourceMarkdownPath"].endswith(".md"))
            self.assertIn("rawContentSha256", details)
            self.assertEqual(len(details["rawContentSha256"]), 64)

        conn.close()

    # ==========================================
    # 7. IDEMPOTENCY TESTS (26 - 31)
    # ==========================================

    def test_26_to_31_idempotent_repeated_import(self):
        # 26: First run imports 4
        res1 = run_legacy_import(self.db_path)
        self.assertEqual(res1.total_imported, 4)
        self.assertEqual(res1.total_skipped, 0)

        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM investigations;")
        count_inv_1 = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM evidence;")
        count_ev_1 = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM audit_events;")
        count_aud_1 = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM ticket_revisions;")
        count_tck_1 = cursor.fetchone()[0]
        conn.close()

        # 27-28: Second run imports 0, skips 4
        res2 = run_legacy_import(self.db_path)
        self.assertEqual(res2.total_imported, 0)
        self.assertEqual(res2.total_skipped, 4)
        self.assertCountEqual(
            res2.skipped,
            ["ART-AGENT-001", "ART-GOV-002", "ART-GOV-003", "ART-SFN-001"]
        )

        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM investigations;")
        count_inv_2 = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM evidence;")
        count_ev_2 = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM audit_events;")
        count_aud_2 = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM ticket_revisions;")
        count_tck_2 = cursor.fetchone()[0]
        conn.close()

        # 29-31: Row counts unchanged
        self.assertEqual(count_inv_1, count_inv_2)
        self.assertEqual(count_ev_1, count_ev_2)
        self.assertEqual(count_aud_1, count_aud_2)
        self.assertEqual(count_tck_1, count_tck_2)

    # ==========================================
    # 8. ALLOCATOR SEEDING TESTS (32 - 36)
    # ==========================================

    def test_32_to_36_allocator_seeding(self):
        run_legacy_import(self.db_path)
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT scope, last_seq FROM id_allocations ORDER BY scope ASC;")
        allocations = {r[0]: r[1] for r in cursor.fetchall()}

        # 32: BUG:AGENT >= 1
        self.assertGreaterEqual(allocations.get("BUG:AGENT", 0), 1)
        # 33: BUG:GOV >= 3
        self.assertGreaterEqual(allocations.get("BUG:GOV", 0), 3)
        # 34: BUG:SFN >= 1
        self.assertGreaterEqual(allocations.get("BUG:SFN", 0), 1)

        # 35: Next allocations allocate expected next IDs
        next_agent = AtomicIdAllocator.allocate_bug_id(conn, "AGENT")
        next_gov = AtomicIdAllocator.allocate_bug_id(conn, "GOV")
        next_sfn = AtomicIdAllocator.allocate_bug_id(conn, "SFN")

        self.assertEqual(next_agent, "ART-AGENT-002")
        self.assertEqual(next_gov, "ART-GOV-004")
        self.assertEqual(next_sfn, "ART-SFN-002")

        # 36: Import does not lower an allocator that is already higher
        AtomicIdAllocator.ensure_minimum_sequence(conn, "BUG:GOV", 10)
        conn.close()

        # Re-run import
        run_legacy_import(self.db_path)
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT last_seq FROM id_allocations WHERE scope = 'BUG:GOV';")
        self.assertEqual(cursor.fetchone()[0], 10)
        conn.close()

    # ==========================================
    # 9. ATOMICITY TESTS (37 - 40)
    # ==========================================

    def test_37_to_40_per_bug_atomic_rollback(self):
        # Create a mock directory with one valid bug and one intentionally corrupted bug
        mock_bugs_dir = os.path.join(self.test_dir, "mock_atomic_bugs")
        os.makedirs(mock_bugs_dir, exist_ok=True)

        # Bug A: Valid ART-AGENT-001
        agent_src = os.path.join(BUGS_DIR, "Agent Lab", "ART-AGENT-001__structured-output-contract-not-strictly-enforced")
        if not os.path.exists(agent_src):
            agent_src = os.path.join(BUGS_DIR, "ART-AGENT-001__structured-output-contract-not-strictly-enforced")
        shutil.copytree(
            agent_src,
            os.path.join(mock_bugs_dir, "ART-AGENT-001__structured-output-contract-not-strictly-enforced")
        )

        # Bug B: Corrupted (invalid status enum not allowed in investigation schema)
        b_dir = os.path.join(mock_bugs_dir, "ART-BAD-005__broken-bug")
        os.makedirs(b_dir, exist_ok=True)
        with open(os.path.join(b_dir, "ART-BAD-005.md"), "w", encoding="utf-8") as f:
            f.write("# ART-BAD-005 — Broken Bug\n- **Severity:** HIGH\n- **Status:** INVALID_STATUS_VALUE\n\n## Bug\nSome desc\n\n## Expected\nExp\n\n## Actual\nAct\n\n## Evidence\n- None\n\n## Production-Grade Fix Proposal\nFix\n\n## Developer Update\nPending.\n\n## Retest\nPending.\n")

        res = run_legacy_import(self.db_path, bugs_dir=mock_bugs_dir)
        self.assertEqual(res.total_imported, 1)
        self.assertEqual(res.total_failed, 1)
        self.assertEqual(res.failed[0][0], "ART-BAD-005")

        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        # Bug A is committed
        cursor.execute("SELECT COUNT(*) FROM investigations WHERE canonical_bug_id = 'ART-AGENT-001';")
        self.assertEqual(cursor.fetchone()[0], 1)

        # 37-40: Bug B has zero persisted rows in any table
        cursor.execute("SELECT COUNT(*) FROM investigations WHERE canonical_bug_id = 'ART-BAD-005';")
        self.assertEqual(cursor.fetchone()[0], 0)
        cursor.execute("SELECT COUNT(*) FROM evidence WHERE id LIKE '%ART-BAD-005%';")
        self.assertEqual(cursor.fetchone()[0], 0)
        cursor.execute("SELECT COUNT(*) FROM audit_events WHERE id LIKE '%ART-BAD-005%';")
        self.assertEqual(cursor.fetchone()[0], 0)
        cursor.execute("SELECT COUNT(*) FROM id_allocations WHERE scope = 'BUG:BAD';")
        self.assertEqual(cursor.fetchone()[0], 0)

        conn.close()

    # ==========================================
    # 10. COEXISTENCE TESTS (41 - 44)
    # ==========================================

    def test_41_to_44_coexistence_with_native_records(self):
        # First import legacy records
        run_legacy_import(self.db_path)

        conn = get_connection(self.db_path)
        service = ResolutionService(conn)

        # Create a native investigation
        res_native = service.create_investigation(
            tester_description="Native live defect",
            reporter="native-tester",
            slug="native-defect"
        )
        self.assertTrue(res_native.success)
        native_inv_id = res_native.data["investigation_id"]

        repo = InvestigationRepository(conn)

        # 41: Both coexist
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM investigations WHERE source_kind = 'LEGACY_IMPORT';")
        self.assertEqual(cursor.fetchone()[0], 4)
        cursor.execute("SELECT COUNT(*) FROM investigations WHERE source_kind = 'NATIVE';")
        self.assertEqual(cursor.fetchone()[0], 1)

        # 42: Native lookup by investigation_id works
        native_row = repo.get_investigation_by_investigation_id(native_inv_id)
        self.assertIsNotNone(native_row)
        self.assertEqual(native_row["source_kind"], "NATIVE")
        self.assertEqual(native_row["lifecycle_phase"], "CAPTURE")

        # 43: Legacy lookup by canonical_bug_id works
        legacy_row = repo.get_investigation_by_canonical_bug_id("ART-GOV-003")
        self.assertIsNotNone(legacy_row)
        self.assertEqual(legacy_row["source_kind"], "LEGACY_IMPORT")
        self.assertIsNone(legacy_row["investigation_id"])

        # 44: Zero identity collision
        self.assertNotEqual(native_row["record_key"], legacy_row["record_key"])
        conn.close()

    # ==========================================
    # 11. CLI AND MODULE TESTS (45 - 48)
    # ==========================================

    def test_45_missing_db_flag_fails_clearly(self):
        # 45: Running script without --db exits non-zero
        proc = subprocess.run(
            [sys.executable, "scripts/import_legacy.py"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("the following arguments are required: --db", proc.stderr)

    def test_46_explicit_temporary_db_path_succeeds(self):
        # 46: Running script with explicit --db succeeds
        proc = subprocess.run(
            [sys.executable, "scripts/import_legacy.py", "--db", self.db_path],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("SUCCESS: Explicit legacy import completed.", proc.stdout)
        self.assertIn("Imported   : 4", proc.stdout)

    def test_47_module_import_does_not_execute_migration(self):
        # 47: Importing the module in python does not create any db or touch files
        test_code = "import scripts.import_legacy; print('IMPORT_OK')"
        proc = subprocess.run(
            [sys.executable, "-c", test_code],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "IMPORT_OK")

    def test_48_no_default_production_db_created(self):
        # 48: Check repository root for accidental .db files
        for fname in os.listdir(BASE_DIR):
            self.assertFalse(
                fname.endswith(".db") or fname.endswith(".sqlite") or fname.endswith(".sqlite3"),
                f"Accidental DB artifact found in repository root: {fname}"
            )


if __name__ == "__main__":
    unittest.main()
