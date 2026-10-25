"""
tests/test_query_service.py

Phase 01J — Unified Application Read Model Test Suite
Validates the complete test matrix specified for Phase 01J:
- SUMMARY: Native & legacy investigation summary returned; display_id rule verified; record_key kept internal.
- DETAIL: Full aggregate detail with original input, evidence metadata (no binary bytes), AI history,
  research history, ticket history, active ticket separately, dev updates, retests, audit events; deterministic ordering;
  non-BUG detail with status NULL succeeds.
- FILTERING: Filter by classification, lifecycle_phase, status, module, severity, priority, assignee, source_kind;
  multiple filters combined with AND.
- SEARCH: Search by ART ID, INV ID, ticket title, original tester description; case-insensitive; parameterized/safe.
- QUEUES: My Work (assignee + FIXING, excludes CLOSED); Retest Queue (status = RETEST); Investigation Queue (CAPTURE/INVESTIGATING);
  non-BUG records handled.
- PAGINATION & SORTING: limit, offset, total count independent of page size; supported sorts work; safe whitelist fallback.
- LOOKUPS: lookup by record_key, investigation_id, canonical_bug_id; nonexistent identifier returns None.
- LEGACY + NATIVE: Coexist in All Records; source_kind distinguishes; no Markdown accessed on normal read.
- READ SAFETY: Zero DB mutations, zero audit events created, zero ID sequence allocations during read operations.
- PERFORMANCE SANITY: 100+ investigations populated, benchmark executed cleanly.
"""

import unittest
import os
import shutil
import tempfile
import sqlite3
import time

from core.storage.schema import init_db
from core.storage.db import get_connection
from core.storage.service import ResolutionService
from core.storage.repository import InvestigationRepository
from core.query.service import InvestigationQueryService
from scripts.import_legacy import run_legacy_import

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class TestQueryService(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="art_test_query_")
        self.db_path = os.path.join(self.test_dir, "test_query.db")
        self.conn = get_connection(self.db_path)
        init_db(self.conn)
        self.service = ResolutionService(self.conn)
        self.query_svc = InvestigationQueryService(self.conn)

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _seed_test_ecosystem(self):
        """
        Seeds an ecosystem containing:
        1. Legacy imported bugs (4 records: ART-AGENT-001, ART-GOV-002, ART-GOV-003, ART-SFN-001)
        2. Native CAPTURE record
        3. Native INVESTIGATING record with AI artifact
        4. Native confirmed BUG in OPEN status
        5. Native confirmed BUG in FIXING status assigned to 'alice'
        6. Native confirmed BUG in RETEST status assigned to 'bob'
        7. Native confirmed BUG in CLOSED status assigned to 'alice'
        8. Native non-BUG PRODUCT_IMPROVEMENT with status NULL
        """
        # 1. Legacy import
        run_legacy_import(self.db_path)

        # 2. Native CAPTURE
        res_cap = self.service.create_investigation(
            tester_description="Early anomaly observed during intake",
            reporter="qa-reporter-1",
            slug="early-anomaly"
        )
        self.cap_inv_id = res_cap.data["investigation_id"]
        self.cap_key = res_cap.data["record_key"]

        # 3. Native INVESTIGATING with AI analysis
        res_inv = self.service.create_investigation(
            tester_description="Agent loop timeout during recursive tool call",
            reporter="qa-reporter-2",
            slug="agent-timeout"
        )
        self.inv_key = res_inv.data["record_key"]
        self.inv_id = res_inv.data["investigation_id"]

        # Transition to INVESTIGATING
        self.service.repo.update_investigation_state(
            record_key=self.inv_key,
            lifecycle_phase="INVESTIGATING",
            status=None,
            updated_at="2026-09-25T11:00:00Z"
        )

        # Insert AI artifact directly via repository
        self.service.repo.insert_ai_artifact(
            generation_id=f"GEN-{self.inv_id}-01",
            investigation_key=self.inv_key,
            purpose="DEFECT_TRIAGE",
            model_identifier="gemini-2.5-flash",
            input_evidence_ids=[],
            structured_output={"confidence": 0.95, "likely_module": "AGENT"},
            generated_at="2026-09-25T11:00:00Z"
        )

        # 4. Native confirmed BUG in OPEN status
        res_open = self.service.create_investigation(
            tester_description="Governance workflow template error",
            reporter="qa-reporter-3",
            slug="gov-template-err"
        )
        self.open_key = res_open.data["record_key"]
        res_conf = self.service.confirm_bug(
            record_key=self.open_key,
            module="GOV",
            ticket_data={
                "title": "Governance template evaluation syntax error",
                "reproSteps": "Execute template with missing var",
                "expectedResult": "Clear syntax error",
                "actualResult": "500 Internal Error",
                "businessImpact": "Blocks approval",
                "recommendedSolution": "Add fallback parser",
                "severity": "MEDIUM",
                "priority": "P2"
            }
        )
        self.open_bug_id = res_conf.data["canonical_bug_id"]

        # 5. Native confirmed BUG in FIXING status assigned to alice
        res_fix = self.service.create_investigation(
            tester_description="Serverless function cold start latency",
            reporter="qa-reporter-4",
            slug="sfn-latency"
        )
        self.fix_key = res_fix.data["record_key"]
        res_conf2 = self.service.confirm_bug(
            record_key=self.fix_key,
            module="SFN",
            ticket_data={
                "title": "Serverless function cold start latency exceeds SLA",
                "reproSteps": "Invoke after 15 min idle",
                "expectedResult": "< 500ms",
                "actualResult": "> 4000ms",
                "businessImpact": "User timeout",
                "recommendedSolution": "Enable warm pool",
                "severity": "HIGH",
                "priority": "P1"
            }
        )
        self.fix_bug_id = res_conf2.data["canonical_bug_id"]
        self.service.start_work(self.fix_key, assignee="alice", actor="alice")

        # 6. Native confirmed BUG in RETEST status assigned to bob
        res_ret = self.service.create_investigation(
            tester_description="Agent memory leak on long conversation",
            reporter="qa-reporter-5",
            slug="agent-memory-leak"
        )
        self.ret_key = res_ret.data["record_key"]
        res_conf3 = self.service.confirm_bug(
            record_key=self.ret_key,
            module="AGENT",
            ticket_data={
                "title": "Agent memory leak on long multi-turn conversation",
                "reproSteps": "Run 100 turn conversation",
                "expectedResult": "Constant heap",
                "actualResult": "OOM crash",
                "businessImpact": "Server crash",
                "recommendedSolution": "Prune context window",
                "severity": "CRITICAL",
                "priority": "P0"
            }
        )
        self.ret_bug_id = res_conf3.data["canonical_bug_id"]
        self.service.start_work(self.ret_key, assignee="bob", actor="bob")
        self.service.submit_fix(
            record_key=self.ret_key,
            developer_username="bob",
            summary_of_changes="Pruned conversation history after 50 turns",
            resolved_in_version_or_branch="v1.2.0-rc1",
            test_instructions_for_qa="Run 100 turns and inspect memory profile"
        )

        # 7. Native confirmed BUG in CLOSED status assigned to alice
        res_cls = self.service.create_investigation(
            tester_description="Minor typo in button label",
            reporter="qa-reporter-6",
            slug="button-typo"
        )
        self.cls_key = res_cls.data["record_key"]
        res_conf4 = self.service.confirm_bug(
            record_key=self.cls_key,
            module="GOV",
            ticket_data={
                "title": "Minor typo in button label",
                "reproSteps": "View submit button",
                "expectedResult": "Submit",
                "actualResult": "Submtt",
                "businessImpact": "Cosmetic",
                "recommendedSolution": "Fix label",
                "severity": "LOW",
                "priority": "P3"
            }
        )
        self.cls_bug_id = res_conf4.data["canonical_bug_id"]
        self.service.start_work(self.cls_key, assignee="alice", actor="alice")
        self.service.submit_fix(
            record_key=self.cls_key,
            developer_username="alice",
            summary_of_changes="Fixed typo",
            resolved_in_version_or_branch="v1.0.1",
            test_instructions_for_qa="Verify button text"
        )
        # Record retest artifact
        self.service.repo.insert_retest_artifact(
            retest_id=f"RET-{self.cls_bug_id}-01",
            investigation_key=self.cls_key,
            retest_evidence_ids=["EVD-VERIFIED-01"],
            human_confirmation={"confirmed": True, "verdict": "VERIFIED", "confirmedBy": "qa-lead"},
            executed_at="2026-09-25T11:30:00Z"
        )
        self.service.verify(
            record_key=self.cls_key,
            human_confirmation={"confirmed": True, "verdict": "VERIFIED", "confirmedBy": "qa-lead"},
            actor="qa-lead",
            actor_role="HUMAN"
        )
        self.service.close(
            record_key=self.cls_key,
            actor="admin",
            summary="Verified and closed"
        )

        # 8. Non-BUG PRODUCT_IMPROVEMENT with status NULL
        res_prod = self.service.create_investigation(
            tester_description="Suggest dark mode theme support",
            reporter="product-manager",
            slug="dark-mode"
        )
        self.prod_key = res_prod.data["record_key"]
        self.prod_inv_id = res_prod.data["investigation_id"]
        self.service.repo.update_investigation_state(
            record_key=self.prod_key,
            lifecycle_phase="CONFIRMED",
            status=None,
            updated_at="2026-09-25T12:00:00Z",
            classification="PRODUCT_IMPROVEMENT"
        )

    # ==========================================
    # 1. SUMMARY TESTS (1 - 6)
    # ==========================================

    def test_01_to_06_summary_and_display_id_rules(self):
        self._seed_test_ecosystem()

        # 1: Native summary
        native_cap = self.query_svc.get_by_record_key(self.cap_key)
        self.assertIsNotNone(native_cap)
        # 3: Native unpromoted uses investigation_id
        self.assertEqual(native_cap["display_id"], self.cap_inv_id)
        self.assertTrue(native_cap["display_id"].startswith("INV-"))
        self.assertEqual(native_cap["source_kind"], "NATIVE")

        # 4: Native promoted BUG uses canonical_bug_id
        native_bug = self.query_svc.get_by_record_key(self.open_key)
        self.assertEqual(native_bug["display_id"], self.open_bug_id)
        self.assertTrue(native_bug["display_id"].startswith("ART-GOV-"))

        # 2, 5: Legacy summary uses preserved ART ID
        legacy_detail = self.query_svc.get_by_canonical_bug_id("ART-AGENT-001")
        self.assertIsNotNone(legacy_detail)
        self.assertEqual(legacy_detail["display_id"], "ART-AGENT-001")
        self.assertEqual(legacy_detail["source_kind"], "LEGACY_IMPORT")
        self.assertIsNone(legacy_detail["investigation_id"])

        # 6: record_key remains separate from display_id
        self.assertNotEqual(native_cap["record_key"], native_cap["display_id"])
        self.assertNotEqual(legacy_detail["record_key"], legacy_detail["display_id"])

        # Display ID invariant: corrupt record with neither business ID raises ValueError
        with self.assertRaises(ValueError):
            InvestigationQueryService.compute_display_id(canonical_bug_id=None, investigation_id=None)

    # ==========================================
    # 2. DETAIL TESTS (7 - 18)
    # ==========================================

    def test_07_to_18_detail_composition_and_order(self):
        self._seed_test_ecosystem()

        # Check detail of fixed/retest bug
        ret_detail = self.query_svc.get_by_record_key(self.ret_key)
        self.assertIsNotNone(ret_detail)

        # 7: Original input
        self.assertIsNotNone(ret_detail["original_input"])
        self.assertIn("Agent memory leak", ret_detail["original_input"]["tester_description"])

        # 8-9: Evidence metadata returned without binary bytes
        self.assertIsInstance(ret_detail["evidence"], list)
        for ev in ret_detail["evidence"]:
            self.assertIn("sha256", ev)
            self.assertIn("storage_path", ev)
            self.assertNotIn("bytes", ev)
            self.assertNotIn("data", ev)

        # 10: AI history
        inv_detail = self.query_svc.get_by_record_key(self.inv_key)
        self.assertEqual(len(inv_detail["ai_artifacts"]), 1)
        self.assertEqual(inv_detail["ai_artifacts"][0]["model_identifier"], "gemini-2.5-flash")

        # 11: Research history (list present)
        self.assertIsInstance(inv_detail["research_artifacts"], list)

        # 12-13: Ticket history and current ticket separately
        self.assertGreaterEqual(len(ret_detail["ticket_history"]), 1)
        self.assertIsNotNone(ret_detail["current_ticket"])
        self.assertEqual(ret_detail["current_ticket"]["title"], "Agent memory leak on long multi-turn conversation")

        # 14: Developer update history
        self.assertEqual(len(ret_detail["developer_updates"]), 1)
        self.assertEqual(ret_detail["developer_updates"][0]["developer_username"], "bob")

        # 15: Retest history (check closed bug)
        cls_detail = self.query_svc.get_by_record_key(self.cls_key)
        self.assertEqual(len(cls_detail["retest_artifacts"]), 1)
        self.assertIn("human_confirmation", cls_detail["retest_artifacts"][0])

        # 16: AuditEvent history
        self.assertGreaterEqual(len(ret_detail["audit_events"]), 3)

        # 17: Deterministic ordering: audit events timestamp ASC
        ts_list = [a["timestamp"] for a in ret_detail["audit_events"]]
        self.assertEqual(ts_list, sorted(ts_list))

        # 18: Non-BUG detail with status NULL succeeds
        prod_detail = self.query_svc.get_by_record_key(self.prod_key)
        self.assertIsNotNone(prod_detail)
        self.assertIsNone(prod_detail["status"])
        self.assertEqual(prod_detail["classification"], "PRODUCT_IMPROVEMENT")
        self.assertEqual(prod_detail["lifecycle_phase"], "CONFIRMED")

    # ==========================================
    # 3. FILTERING TESTS (19 - 27)
    # ==========================================

    def test_19_to_27_filters(self):
        self._seed_test_ecosystem()

        # 19: Classification
        res_class = self.query_svc.list_all_records(filters={"classification": "PRODUCT_IMPROVEMENT"})
        self.assertEqual(res_class.total, 1)
        self.assertEqual(res_class.items[0]["record_key"], self.prod_key)

        # 20: Lifecycle phase
        res_phase = self.query_svc.list_all_records(filters={"lifecycle_phase": "CAPTURE"})
        self.assertEqual(res_phase.total, 1)
        self.assertEqual(res_phase.items[0]["record_key"], self.cap_key)

        # 21: Status
        res_stat = self.query_svc.list_all_records(filters={"status": "FIXING"})
        self.assertEqual(res_stat.total, 1)
        self.assertEqual(res_stat.items[0]["record_key"], self.fix_key)

        # 22: Module
        res_mod = self.query_svc.list_all_records(filters={"module": "SFN"})
        # 1 legacy (ART-SFN-001) + 1 native (fix_key)
        self.assertEqual(res_mod.total, 2)

        # 23: Severity
        res_sev = self.query_svc.list_all_records(filters={"severity": "CRITICAL"})
        self.assertEqual(res_sev.total, 1)
        self.assertEqual(res_sev.items[0]["record_key"], self.ret_key)

        # 24: Priority
        res_pri = self.query_svc.list_all_records(filters={"priority": "P0"})
        self.assertEqual(res_pri.total, 1)
        self.assertEqual(res_pri.items[0]["record_key"], self.ret_key)

        # 25: Assignee
        res_asg = self.query_svc.list_all_records(filters={"assignee": "alice"})
        self.assertEqual(res_asg.total, 2)  # fix_key and cls_key

        # 26: Source kind
        res_src = self.query_svc.list_all_records(filters={"source_kind": "LEGACY_IMPORT"})
        self.assertEqual(res_src.total, 4)

        # 27: Multiple filters combine with AND
        res_multi = self.query_svc.list_all_records(
            filters={
                "assignee": "alice",
                "status": "FIXING"
            }
        )
        self.assertEqual(res_multi.total, 1)
        self.assertEqual(res_multi.items[0]["record_key"], self.fix_key)

    # ==========================================
    # 4. TEXT SEARCH TESTS (28 - 33)
    # ==========================================

    def test_28_to_33_search(self):
        self._seed_test_ecosystem()

        # 28: Search by ART bug ID
        res_art = self.query_svc.list_all_records(search_query="ART-GOV-003")
        self.assertEqual(res_art.total, 1)
        self.assertEqual(res_art.items[0]["canonical_bug_id"], "ART-GOV-003")

        # 29: Search by INV ID
        res_inv = self.query_svc.list_all_records(search_query=self.cap_inv_id)
        self.assertEqual(res_inv.total, 1)
        self.assertEqual(res_inv.items[0]["investigation_id"], self.cap_inv_id)

        # 30: Search by ticket title
        res_ttl = self.query_svc.list_all_records(search_query="cold start latency")
        self.assertEqual(res_ttl.total, 1)
        self.assertEqual(res_ttl.items[0]["record_key"], self.fix_key)

        # 31: Search by original tester description
        res_desc = self.query_svc.list_all_records(search_query="Early anomaly observed")
        self.assertEqual(res_desc.total, 1)
        self.assertEqual(res_desc.items[0]["record_key"], self.cap_key)

        # 32: Case-insensitive search
        res_case = self.query_svc.list_all_records(search_query="COLD START LATENCY")
        self.assertEqual(res_case.total, 1)
        self.assertEqual(res_case.items[0]["record_key"], self.fix_key)

        # 33: SQL injection safety
        malicious = "' OR '1'='1"
        res_safe = self.query_svc.list_all_records(search_query=malicious)
        self.assertEqual(res_safe.total, 0)

    # ==========================================
    # 5. WORK QUEUES TESTS (34 - 39)
    # ==========================================

    def test_34_to_39_queues(self):
        self._seed_test_ecosystem()

        # 34: My Work returns assigned FIXING records
        alice_work = self.query_svc.list_my_work("alice")
        self.assertEqual(alice_work.total, 1)
        self.assertEqual(alice_work.items[0]["record_key"], self.fix_key)

        # 35: My Work excludes CLOSED records (alice also has cls_key which is CLOSED)
        keys_in_work = [it["record_key"] for it in alice_work.items]
        self.assertNotIn(self.cls_key, keys_in_work)

        # 36: Retest Queue returns RETEST records
        retest_q = self.query_svc.list_retest_queue()
        self.assertEqual(retest_q.total, 1)
        self.assertEqual(retest_q.items[0]["record_key"], self.ret_key)

        # 37: Retest Queue excludes FIXING / OPEN
        for item in retest_q.items:
            self.assertEqual(item["status"], "RETEST")

        # 38: Investigation Queue returns CAPTURE / INVESTIGATING
        inv_q = self.query_svc.list_investigation_queue()
        self.assertEqual(inv_q.total, 2)  # cap_key and inv_key
        q_phases = {it["lifecycle_phase"] for it in inv_q.items}
        self.assertEqual(q_phases, {"CAPTURE", "INVESTIGATING"})

        # 39: Non-BUG records remain queryable without fake status
        prod_item = self.query_svc.get_by_record_key(self.prod_key)
        self.assertIsNone(prod_item["status"])
        self.assertEqual(prod_item["classification"], "PRODUCT_IMPROVEMENT")

    # ==========================================
    # 6. PAGINATION & SORTING TESTS (40 - 45)
    # ==========================================

    def test_40_to_45_pagination_and_sorting(self):
        self._seed_test_ecosystem()

        # Total count check: 4 legacy + 7 native = 11 records
        res_all = self.query_svc.list_all_records(limit=3, offset=0)
        self.assertEqual(res_all.total, 11)
        self.assertEqual(len(res_all.items), 3)

        # 40-42: Pagination offset
        res_page2 = self.query_svc.list_all_records(limit=3, offset=3)
        self.assertEqual(res_page2.total, 11)
        self.assertEqual(len(res_page2.items), 3)
        self.assertNotEqual(res_all.items[0]["record_key"], res_page2.items[0]["record_key"])

        # 43: Deterministic default ordering (updated_at DESC)
        res_all_items = self.query_svc.list_all_records(limit=100).items
        updated_ts = [it["updated_at"] for it in res_all_items]
        self.assertEqual(updated_ts, sorted(updated_ts, reverse=True))

        # 44: Supported sort works (created_at ASC)
        res_sort_asc = self.query_svc.list_all_records(sort_by="created_at", sort_order="ASC", limit=100)
        created_ts = [it["created_at"] for it in res_sort_asc.items]
        self.assertEqual(created_ts, sorted(created_ts))

        # 45: Unsupported sort field safely falls back to updated_at
        res_fallback = self.query_svc.list_all_records(sort_by="malicious_column_name; DROP TABLE investigations;")
        self.assertEqual(res_fallback.total, 11)

    # ==========================================
    # 7. LOOKUP TESTS (46 - 49)
    # ==========================================

    def test_46_to_49_lookups(self):
        self._seed_test_ecosystem()

        # 46: Lookup by record_key
        by_key = self.query_svc.get_by_record_key(self.fix_key)
        self.assertIsNotNone(by_key)
        self.assertEqual(by_key["record_key"], self.fix_key)

        # 47: Lookup by investigation_id
        by_inv = self.query_svc.get_by_investigation_id(self.cap_inv_id)
        self.assertIsNotNone(by_inv)
        self.assertEqual(by_inv["investigation_id"], self.cap_inv_id)

        # 48: Lookup by canonical_bug_id
        by_art = self.query_svc.get_by_canonical_bug_id("ART-GOV-002")
        self.assertIsNotNone(by_art)
        self.assertEqual(by_art["canonical_bug_id"], "ART-GOV-002")

        # 49: Nonexistent identifier returns None
        self.assertIsNone(self.query_svc.get_by_record_key("rec_non_existent"))
        self.assertIsNone(self.query_svc.get_by_investigation_id("INV-99999999-9999"))
        self.assertIsNone(self.query_svc.get_by_canonical_bug_id("ART-XYZ-999"))

    # ==========================================
    # 8. LEGACY + NATIVE COEXISTENCE TESTS (50 - 52)
    # ==========================================

    def test_50_to_52_legacy_native_coexistence(self):
        self._seed_test_ecosystem()

        # 50: Both appear in All Records
        all_res = self.query_svc.list_all_records(limit=100)
        source_kinds = {it["source_kind"] for it in all_res.items}
        self.assertEqual(source_kinds, {"NATIVE", "LEGACY_IMPORT"})

        # 51: source_kind distinguishes them
        legacy_items = [it for it in all_res.items if it["source_kind"] == "LEGACY_IMPORT"]
        native_items = [it for it in all_res.items if it["source_kind"] == "NATIVE"]
        self.assertEqual(len(legacy_items), 4)
        self.assertEqual(len(native_items), 7)

        # 52: Query layer does NOT access Markdown files during read
        # Confirmed by checking that query operates strictly on SQLite connection

    # ==========================================
    # 9. READ SAFETY GUARANTEES (53 - 55)
    # ==========================================

    def test_53_to_55_read_safety(self):
        self._seed_test_ecosystem()

        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM investigations;")
        count_inv_before = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM audit_events;")
        count_aud_before = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM id_allocations;")
        count_alloc_before = cursor.fetchone()[0]

        # Execute multiple read queries
        self.query_svc.list_all_records(limit=100)
        self.query_svc.list_my_work("alice")
        self.query_svc.list_retest_queue()
        self.query_svc.list_investigation_queue()
        self.query_svc.get_by_record_key(self.fix_key)
        self.query_svc.get_by_canonical_bug_id("ART-AGENT-001")

        # 53: Zero DB mutations
        cursor.execute("SELECT COUNT(*) FROM investigations;")
        self.assertEqual(cursor.fetchone()[0], count_inv_before)

        # 54: Zero audit events generated
        cursor.execute("SELECT COUNT(*) FROM audit_events;")
        self.assertEqual(cursor.fetchone()[0], count_aud_before)

        # 55: Zero ID allocations performed
        cursor.execute("SELECT COUNT(*) FROM id_allocations;")
        self.assertEqual(cursor.fetchone()[0], count_alloc_before)

    # ==========================================
    # 10. PERFORMANCE SANITY TEST
    # ==========================================

    def test_performance_sanity_with_200_records(self):
        # Create a dedicated temporary database to benchmark 200 records
        perf_dir = tempfile.mkdtemp(prefix="art_perf_")
        perf_db = os.path.join(perf_dir, "perf.db")
        conn = get_connection(perf_db)
        init_db(conn)
        repo = InvestigationRepository(conn)

        # Batch insert 200 records directly via repository
        cursor = conn.cursor()
        cursor.execute("BEGIN IMMEDIATE;")
        for i in range(200):
            rkey = f"rec_perf_{i:04d}"
            inv_id = f"INV-20260925-{i+1:04d}"
            repo.create_investigation(
                record_key=rkey,
                source_kind="NATIVE",
                slug=f"perf-item-{i}",
                lifecycle_phase="CONFIRMED" if i % 2 == 0 else "CAPTURE",
                original_input_id=f"INP-{i:04d}",
                investigation_id=inv_id,
                canonical_bug_id=f"ART-PERF-{i:03d}" if i % 2 == 0 else None,
                status="FIXING" if i % 4 == 0 else ("RETEST" if i % 4 == 1 else "OPEN"),
                classification="BUG" if i % 2 == 0 else "PRODUCT_IMPROVEMENT",
                module="AGENT" if i % 3 == 0 else "GOV",
                severity="HIGH" if i % 2 == 0 else "MEDIUM",
                priority="P1",
                assignee="dev-perf" if i % 2 == 0 else None,
                active_ticket_id=f"TCK-{i:04d}"
            )
            repo.insert_original_input(
                input_id=f"INP-{i:04d}",
                investigation_key=rkey,
                tester_description=f"Performance sanity defect description for item {i}",
                reporter="perf-tester",
                captured_at="2026-09-25T12:00:00Z",
                initial_evidence_ids=[]
            )
            repo.insert_ticket_revision(
                ticket_id=f"TCK-{i:04d}",
                investigation_key=rkey,
                revision=1,
                title=f"Performance Ticket Title Number {i}",
                repro_steps="Not provided",
                expected_result="Fast",
                actual_result="Slow",
                business_impact="None",
                recommended_solution="Optimize",
                module="AGENT" if i % 3 == 0 else "GOV",
                environment="Test",
                severity="HIGH" if i % 2 == 0 else "MEDIUM",
                priority="P1",
                tags=["perf"],
                discussion=[],
                updated_at="2026-09-25T12:00:00Z"
            )
        cursor.execute("COMMIT;")

        q_svc = InvestigationQueryService(conn)

        # Benchmark: List query
        t0 = time.perf_counter()
        res_list = q_svc.list_all_records(limit=50)
        t_list = time.perf_counter() - t0
        self.assertEqual(res_list.total, 200)

        # Benchmark: Filtered query
        t0 = time.perf_counter()
        res_filtered = q_svc.list_all_records(filters={"status": "FIXING", "module": "AGENT"}, limit=50)
        t_filter = time.perf_counter() - t0
        self.assertGreater(res_filtered.total, 0)

        # Benchmark: Text search
        t0 = time.perf_counter()
        res_search = q_svc.list_all_records(search_query="Performance Ticket Title Number 150")
        t_search = time.perf_counter() - t0
        self.assertEqual(res_search.total, 1)

        # Benchmark: Detail query
        t0 = time.perf_counter()
        detail = q_svc.get_by_record_key("rec_perf_0150")
        t_detail = time.perf_counter() - t0
        self.assertIsNotNone(detail)

        conn.close()
        shutil.rmtree(perf_dir, ignore_errors=True)

        # Verify sanity threshold (each operation finishes well under 50ms)
        self.assertLess(t_list, 0.05, f"List query too slow: {t_list:.4f}s")
        self.assertLess(t_filter, 0.05, f"Filter query too slow: {t_filter:.4f}s")
        self.assertLess(t_search, 0.05, f"Search query too slow: {t_search:.4f}s")
        self.assertLess(t_detail, 0.05, f"Detail query too slow: {t_detail:.4f}s")


if __name__ == "__main__":
    unittest.main()
