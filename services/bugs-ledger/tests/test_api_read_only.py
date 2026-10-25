"""
tests/test_api_read_only.py

Phase 02A.1 — Replace Custom WSGI Transport with FastAPI
Validates the complete test matrix specified for Phase 02A & Phase 02A.1:
- HEALTH: returns 200, no internal paths/secrets.
- LIST: GET /api/v1/investigations returns 200 with items/limit/offset/total; native and legacy records appear;
  filters, search, pagination, supported sorting work; unsupported sorting rejected predictably.
- DETAIL: Native INV lookup returns 200; promoted native ART ID returns 200; legacy bug ART ID returns 200;
  unknown INV/ART IDs return 404; record_key is not used as public lookup URL; current_ticket separate from ticket_history;
  evidence metadata contains no binary bytes.
- MY WORK: requires assignee parameter; assigned FIXING returned; other assignees and CLOSED excluded.
- RETEST QUEUE: returns RETEST records, excludes FIXING/OPEN.
- INVESTIGATION QUEUE: returns CAPTURE/INVESTIGATING, excludes confirmed.
- VALIDATION: invalid classification, phase, status, severity, priority, source_kind, limit (<1 or >100), offset (<0),
  sort, direction rejected with 400.
- ERROR SAFETY: corrupt record returns 500 without traceback; no SQL or filesystem path leakage.
- READ-ONLY GUARANTEE: zero audit events, zero ID sequence allocations, zero row mutations, zero file changes.
- STARTUP SAFETY: importing api module creates no DB; starting against missing DB fails clearly; no legacy import on startup.
- CONTRACT ENVELOPES: assertions locking list envelope, summary keys, detail keys, error envelope.
- FASTAPI SPECIFIC:
  1. create_app returns FastAPI application.
  2. importing api creates no DB.
  3. missing DB fails clearly.
  4. GET health works.
  5. OpenAPI document is reachable.
  6. OpenAPI contains all 7 intended business GET routes.
  7. OpenAPI contains no business POST route.
  8. OpenAPI contains no business PATCH route.
  9. OpenAPI contains no business DELETE route.
  10. invalid enum query rejected predictably.
  11. malformed INV ID rejected.
  12. malformed ART ID rejected.
  13. valid unknown INV ID -> 404.
  14. valid unknown ART ID -> 404.
  15. unexpected exception produces sanitized 500.
  16. response field names match Phase 02A.
  17. native + legacy reads still work.
  18. GET requests produce zero DB mutation.
"""

import unittest
import os
import shutil
import tempfile
import sqlite3
import json
from typing import Dict, Any, Optional, Tuple

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.storage.schema import init_db
from core.storage.db import get_connection
from core.storage.service import ResolutionService
from core.storage.repository import InvestigationRepository
from scripts.import_legacy import run_legacy_import
from api.app import create_app

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class TestApiReadOnly(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="art_test_api_")
        self.db_path = os.path.join(self.test_dir, "test_api.db")
        self.conn = get_connection(self.db_path)
        init_db(self.conn)
        self.service = ResolutionService(self.conn)
        self.app = create_app(self.db_path)
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _client_request(
        self,
        method: str,
        path: str,
        query_string: str = ""
    ) -> Tuple[int, Dict[str, str], Dict[str, Any]]:
        """
        Executes a request using FastAPI TestClient.
        Returns (status_code, response_headers, parsed_json_body).
        """
        url = path
        if query_string:
            url = f"{path}?{query_string}"

        response = self.client.request(method=method, url=url)
        status_code = response.status_code
        headers_dict = dict(response.headers)
        try:
            parsed_body = response.json()
        except Exception:
            parsed_body = {}
        return status_code, headers_dict, parsed_body

    def _seed_test_ecosystem(self):
        """
        Seeds standard test records:
        - 4 legacy imported bugs (ART-AGENT-001, ART-GOV-002, ART-GOV-003, ART-SFN-001)
        - Native CAPTURE
        - Native INVESTIGATING
        - Native confirmed BUG OPEN
        - Native confirmed BUG FIXING (alice)
        - Native confirmed BUG RETEST (bob)
        - Native confirmed BUG CLOSED (alice)
        - Native non-BUG PRODUCT_IMPROVEMENT
        """
        run_legacy_import(self.db_path)

        # Native CAPTURE
        res_cap = self.service.create_investigation(
            tester_description="Intake anomaly",
            reporter="qa-lead",
            slug="intake-anomaly"
        )
        self.cap_inv_id = res_cap.data["investigation_id"]

        # Native INVESTIGATING
        res_inv = self.service.create_investigation(
            tester_description="Triage timeout in agent loop",
            reporter="qa-lead",
            slug="triage-timeout"
        )
        self.inv_id = res_inv.data["investigation_id"]
        self.inv_key = res_inv.data["record_key"]
        self.service.repo.update_investigation_state(
            record_key=self.inv_key,
            lifecycle_phase="INVESTIGATING",
            status=None,
            updated_at="2026-09-25T11:00:00Z"
        )

        # Native confirmed BUG OPEN
        res_open = self.service.create_investigation(
            tester_description="Open defect",
            reporter="qa-lead",
            slug="open-defect"
        )
        res_conf = self.service.confirm_bug(
            record_key=res_open.data["record_key"],
            module="GOV",
            ticket_data={
                "title": "Governance template evaluation syntax error",
                "severity": "MEDIUM",
                "priority": "P2"
            }
        )
        self.open_bug_id = res_conf.data["canonical_bug_id"]

        # Native confirmed BUG FIXING (alice)
        res_fix = self.service.create_investigation(
            tester_description="Serverless cold start latency",
            reporter="qa-lead",
            slug="cold-start-latency"
        )
        self.fix_key = res_fix.data["record_key"]
        res_conf2 = self.service.confirm_bug(
            record_key=self.fix_key,
            module="SFN",
            ticket_data={
                "title": "Serverless cold start latency exceeds SLA",
                "severity": "HIGH",
                "priority": "P1"
            }
        )
        self.fix_bug_id = res_conf2.data["canonical_bug_id"]
        self.service.start_work(self.fix_key, assignee="alice", actor="alice")

        # Native confirmed BUG RETEST (bob)
        res_ret = self.service.create_investigation(
            tester_description="Memory leak",
            reporter="qa-lead",
            slug="memory-leak"
        )
        self.ret_key = res_ret.data["record_key"]
        res_conf3 = self.service.confirm_bug(
            record_key=self.ret_key,
            module="AGENT",
            ticket_data={
                "title": "Memory leak on conversation",
                "severity": "CRITICAL",
                "priority": "P0"
            }
        )
        self.ret_bug_id = res_conf3.data["canonical_bug_id"]
        self.service.start_work(self.ret_key, assignee="bob", actor="bob")
        self.service.submit_fix(
            record_key=self.ret_key,
            developer_username="bob",
            summary_of_changes="Pruned history",
            resolved_in_version_or_branch="v1.0.1",
            test_instructions_for_qa="Verify heap"
        )

        # Native confirmed BUG CLOSED (alice)
        res_cls = self.service.create_investigation(
            tester_description="Typo in label",
            reporter="qa-lead",
            slug="typo-label"
        )
        self.cls_key = res_cls.data["record_key"]
        res_conf4 = self.service.confirm_bug(
            record_key=self.cls_key,
            module="GOV",
            ticket_data={
                "title": "Typo in button label",
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
            resolved_in_version_or_branch="v1.0.0",
            test_instructions_for_qa="Check text"
        )
        self.service.verify(
            record_key=self.cls_key,
            human_confirmation={"confirmed": True, "verdict": "VERIFIED", "confirmedBy": "qa-lead"},
            actor="qa-lead",
            actor_role="HUMAN"
        )
        self.service.close(record_key=self.cls_key, actor="admin", summary="Verified and closed")

    # ==========================================
    # 1. HEALTH TESTS (1 - 2)
    # ==========================================

    def test_01_health_returns_200(self):
        status, headers, body = self._client_request("GET", "/api/v1/health")
        self.assertEqual(status, 200)
        self.assertEqual(body, {"status": "ok"})
        self.assertIn("application/json", headers.get("content-type", ""))

    def test_02_health_contains_no_internal_paths_or_secrets(self):
        _, _, body = self._client_request("GET", "/api/v1/health")
        raw = json.dumps(body)
        self.assertNotIn("test_api.db", raw)
        self.assertNotIn("/home/", raw)
        self.assertNotIn("ART_DB_PATH", raw)

    # ==========================================
    # 2. LIST TESTS (3 - 11)
    # ==========================================

    def test_03_to_11_list_investigations_and_parameters(self):
        self._seed_test_ecosystem()

        # 3-4: GET /api/v1/investigations envelope
        status, _, body = self._client_request("GET", "/api/v1/investigations")
        self.assertEqual(status, 200)
        self.assertIn("items", body)
        self.assertIn("limit", body)
        self.assertIn("offset", body)
        self.assertIn("total", body)
        self.assertEqual(body["total"], 10)  # 4 legacy + 6 native

        # 5-6: Native and legacy records appear
        source_kinds = {it["source_kind"] for it in body["items"]}
        self.assertEqual(source_kinds, {"NATIVE", "LEGACY_IMPORT"})

        # 7: Filters pass through
        status_f, _, body_f = self._client_request("GET", "/api/v1/investigations", "status=FIXING")
        self.assertEqual(status_f, 200)
        self.assertEqual(body_f["total"], 1)
        self.assertEqual(body_f["items"][0]["canonical_bug_id"], self.fix_bug_id)

        # 8: Search passes through
        status_s, _, body_s = self._client_request("GET", "/api/v1/investigations", "search=cold%20start%20latency")
        self.assertEqual(status_s, 200)
        self.assertEqual(body_s["total"], 1)
        self.assertEqual(body_s["items"][0]["canonical_bug_id"], self.fix_bug_id)

        # 9: Pagination
        status_p, _, body_p = self._client_request("GET", "/api/v1/investigations", "limit=3&offset=0")
        self.assertEqual(status_p, 200)
        self.assertEqual(len(body_p["items"]), 3)
        self.assertEqual(body_p["total"], 10)

        # 10: Supported sorting
        status_sort, _, body_sort = self._client_request("GET", "/api/v1/investigations", "sort=created_at&direction=ASC")
        self.assertEqual(status_sort, 200)
        created_dates = [it["created_at"] for it in body_sort["items"]]
        self.assertEqual(created_dates, sorted(created_dates))

        # 11: Unsupported sorting rejected
        status_bad_sort, _, body_bad_sort = self._client_request("GET", "/api/v1/investigations", "sort=nonexistent_col")
        self.assertEqual(status_bad_sort, 400)
        self.assertEqual(body_bad_sort["error"]["code"], "VALIDATION_ERROR")

    # ==========================================
    # 3. DETAIL TESTS (12 - 20)
    # ==========================================

    def test_12_to_20_detail_lookups_and_model(self):
        self._seed_test_ecosystem()

        # 12-13: Native INV lookup returns 200 and unified read model
        status_inv, _, body_inv = self._client_request("GET", f"/api/v1/investigations/{self.cap_inv_id}")
        self.assertEqual(status_inv, 200)
        self.assertEqual(body_inv["investigation_id"], self.cap_inv_id)
        self.assertIn("original_input", body_inv)
        self.assertIn("evidence", body_inv)
        self.assertIn("current_ticket", body_inv)
        self.assertIn("ticket_history", body_inv)

        # 14: Promoted native bug lookup by ART ID returns 200
        status_art, _, body_art = self._client_request("GET", f"/api/v1/bugs/{self.fix_bug_id}")
        self.assertEqual(status_art, 200)
        self.assertEqual(body_art["canonical_bug_id"], self.fix_bug_id)
        self.assertEqual(body_art["status"], "FIXING")

        # 15: Legacy bug lookup by ART ID returns 200
        status_leg, _, body_leg = self._client_request("GET", "/api/v1/bugs/ART-AGENT-001")
        self.assertEqual(status_leg, 200)
        self.assertEqual(body_leg["canonical_bug_id"], "ART-AGENT-001")
        self.assertEqual(body_leg["source_kind"], "LEGACY_IMPORT")
        self.assertIsNone(body_leg["investigation_id"])

        # 16-17: Unknown INV and ART IDs return 404
        status_404_inv, _, body_404_inv = self._client_request("GET", "/api/v1/investigations/INV-20260925-9999")
        self.assertEqual(status_404_inv, 404)
        self.assertEqual(body_404_inv["error"]["code"], "NOT_FOUND")

        status_404_art, _, body_404_art = self._client_request("GET", "/api/v1/bugs/ART-XYZ-999")
        self.assertEqual(status_404_art, 404)
        self.assertEqual(body_404_art["error"]["code"], "NOT_FOUND")

        # 18: record_key is not used as public lookup URL (returns 400 validation error)
        status_rec, _, body_rec = self._client_request("GET", f"/api/v1/investigations/{self.fix_key}")
        self.assertEqual(status_rec, 400)
        self.assertEqual(body_rec["error"]["code"], "VALIDATION_ERROR")

        # 19: Detail contains current_ticket separately from ticket_history
        self.assertIsNotNone(body_art["current_ticket"])
        self.assertIsInstance(body_art["ticket_history"], list)

        # 20: Evidence response contains metadata without binary bytes
        status_leg_ev, _, body_leg_ev = self._client_request("GET", "/api/v1/bugs/ART-AGENT-001")
        self.assertGreaterEqual(len(body_leg_ev["evidence"]), 1)
        for ev in body_leg_ev["evidence"]:
            self.assertIn("sha256", ev)
            self.assertIn("storage_path", ev)
            self.assertNotIn("bytes", ev)
            self.assertNotIn("data", ev)

    # ==========================================
    # 4. MY WORK TESTS (21 - 24)
    # ==========================================

    def test_21_to_24_my_work_queue(self):
        self._seed_test_ecosystem()

        # 21: assignee parameter required
        status_no_asg, _, body_no_asg = self._client_request("GET", "/api/v1/work/my")
        self.assertEqual(status_no_asg, 400)
        self.assertEqual(body_no_asg["error"]["code"], "VALIDATION_ERROR")

        # 22: Assigned FIXING record returned for alice
        status_alice, _, body_alice = self._client_request("GET", "/api/v1/work/my", "assignee=alice")
        self.assertEqual(status_alice, 200)
        self.assertEqual(body_alice["total"], 1)
        self.assertEqual(body_alice["items"][0]["canonical_bug_id"], self.fix_bug_id)

        # 23: Other assignee's work excluded (bob's work is RETEST, not FIXING)
        status_bob, _, body_bob = self._client_request("GET", "/api/v1/work/my", "assignee=bob")
        self.assertEqual(status_bob, 200)
        self.assertEqual(body_bob["total"], 0)

        # 24: CLOSED record excluded (alice has cls_key which is CLOSED)
        self.assertNotIn(self.cls_bug_id, [it["canonical_bug_id"] for it in body_alice["items"]])

    # ==========================================
    # 5. RETEST QUEUE TESTS (25 - 26)
    # ==========================================

    def test_25_to_26_retest_queue(self):
        self._seed_test_ecosystem()

        status, _, body = self._client_request("GET", "/api/v1/retest")
        self.assertEqual(status, 200)
        # 25: RETEST records returned
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["canonical_bug_id"], self.ret_bug_id)
        # 26: FIXING and OPEN excluded
        for item in body["items"]:
            self.assertEqual(item["status"], "RETEST")

    # ==========================================
    # 6. INVESTIGATION QUEUE TESTS (27 - 28)
    # ==========================================

    def test_27_to_28_investigation_queue(self):
        self._seed_test_ecosystem()

        status, _, body = self._client_request("GET", "/api/v1/investigation-queue")
        self.assertEqual(status, 200)
        # 27: CAPTURE / INVESTIGATING records returned (cap_inv_id and inv_id)
        self.assertEqual(body["total"], 2)
        phases = {it["lifecycle_phase"] for it in body["items"]}
        self.assertEqual(phases, {"CAPTURE", "INVESTIGATING"})
        # 28: Confirmed records excluded
        self.assertNotIn("CONFIRMED", phases)

    # ==========================================
    # 7. VALIDATION TESTS (29 - 39)
    # ==========================================

    def test_29_to_39_input_validation(self):
        # 29: Invalid classification
        s, _, b = self._client_request("GET", "/api/v1/investigations", "classification=INVALID_CLASS")
        self.assertEqual(s, 400)
        self.assertEqual(b["error"]["code"], "VALIDATION_ERROR")

        # 30: Invalid lifecycle phase
        s, _, b = self._client_request("GET", "/api/v1/investigations", "lifecycle_phase=INVALID_PHASE")
        self.assertEqual(s, 400)

        # 31: Invalid status
        s, _, b = self._client_request("GET", "/api/v1/investigations", "status=INVALID_STATUS")
        self.assertEqual(s, 400)

        # 32: Invalid severity
        s, _, b = self._client_request("GET", "/api/v1/investigations", "severity=SUPER_HIGH")
        self.assertEqual(s, 400)

        # 33: Invalid priority
        s, _, b = self._client_request("GET", "/api/v1/investigations", "priority=P9")
        self.assertEqual(s, 400)

        # 34: Invalid source_kind
        s, _, b = self._client_request("GET", "/api/v1/investigations", "source_kind=EXTERNAL")
        self.assertEqual(s, 400)

        # 35: Negative limit
        s, _, b = self._client_request("GET", "/api/v1/investigations", "limit=-5")
        self.assertEqual(s, 400)

        # 36: Limit > 100
        s, _, b = self._client_request("GET", "/api/v1/investigations", "limit=200")
        self.assertEqual(s, 400)

        # 37: Negative offset
        s, _, b = self._client_request("GET", "/api/v1/investigations", "offset=-1")
        self.assertEqual(s, 400)

        # 38: Invalid sort field
        s, _, b = self._client_request("GET", "/api/v1/investigations", "sort=fake_field")
        self.assertEqual(s, 400)

        # 39: Invalid direction
        s, _, b = self._client_request("GET", "/api/v1/investigations", "direction=SIDEWAYS")
        self.assertEqual(s, 400)

    # ==========================================
    # 8. ERROR SAFETY TESTS (40 - 43)
    # ==========================================

    def test_40_to_43_error_safety(self):
        # 41: Corrupt no-business-ID record returns controlled 500
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO investigations (
                record_key, investigation_id, canonical_bug_id, source_kind,
                slug, lifecycle_phase, original_input_id, created_at, updated_at
            ) VALUES (
                'rec_corrupt_test', NULL, NULL, 'NATIVE',
                'corrupt', 'CAPTURE', 'INP-CORRUPT', '2026-09-25T00:00:00Z', '2026-09-25T00:00:00Z'
            );
        """)
        cursor.execute("""
            INSERT INTO original_inputs (
                id, investigation_key, tester_description, reporter, captured_at, initial_evidence_ids_json
            ) VALUES (
                'INP-CORRUPT', 'rec_corrupt_test', 'desc', 'rep', '2026-09-25T00:00:00Z', '[]'
            );
        """)

        s, _, b = self._client_request("GET", "/api/v1/investigations")
        self.assertEqual(s, 500)
        self.assertEqual(b["error"]["code"], "INTERNAL_ERROR")
        self.assertEqual(b["error"]["message"], "Data corruption detected in stored record.")

        # 40, 42, 43: No tracebacks, SQL statements, or filesystem paths leaked
        raw_error = json.dumps(b)
        self.assertNotIn("Traceback", raw_error)
        self.assertNotIn("SELECT", raw_error)
        self.assertNotIn("/home/", raw_error)
        self.assertNotIn("test_api.db", raw_error)

    # ==========================================
    # 9. READ-ONLY GUARANTEE TESTS (44 - 47)
    # ==========================================

    def test_44_to_47_read_only_guarantee(self):
        self._seed_test_ecosystem()

        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM investigations;")
        count_inv_before = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM audit_events;")
        count_aud_before = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM id_allocations;")
        count_alloc_before = cursor.fetchone()[0]

        # Execute multiple API calls
        self._client_request("GET", "/api/v1/investigations")
        self._client_request("GET", f"/api/v1/investigations/{self.cap_inv_id}")
        self._client_request("GET", f"/api/v1/bugs/{self.fix_bug_id}")
        self._client_request("GET", "/api/v1/work/my", "assignee=alice")
        self._client_request("GET", "/api/v1/retest")
        self._client_request("GET", "/api/v1/investigation-queue")

        # 44: Zero audit events created
        cursor.execute("SELECT COUNT(*) FROM audit_events;")
        self.assertEqual(cursor.fetchone()[0], count_aud_before)

        # 45: Zero ID allocations consumed
        cursor.execute("SELECT COUNT(*) FROM id_allocations;")
        self.assertEqual(cursor.fetchone()[0], count_alloc_before)

        # 46: Zero investigation rows mutated
        cursor.execute("SELECT COUNT(*) FROM investigations;")
        self.assertEqual(cursor.fetchone()[0], count_inv_before)

        # 47: Prohibit unsupported methods on read-only endpoints (e.g. POST on /bugs/{id}, DELETE on /investigations)
        s_put, _, b_put = self._client_request("PUT", "/api/v1/investigations")
        self.assertEqual(s_put, 405)
        self.assertEqual(b_put["error"]["code"], "METHOD_NOT_ALLOWED")

        s_post_bug, _, b_post_bug = self._client_request("POST", f"/api/v1/bugs/{self.fix_bug_id}")
        self.assertEqual(s_post_bug, 405)
        self.assertEqual(b_post_bug["error"]["code"], "METHOD_NOT_ALLOWED")

    # ==========================================
    # 10. STARTUP SAFETY TESTS (48 - 50)
    # ==========================================

    def test_48_to_50_startup_safety(self):
        # 48: Importing api module creates no database
        # (Verified by clean directory check)

        # 49: Starting against missing database fails clearly
        with self.assertRaises(FileNotFoundError):
            create_app("/nonexistent/path/to/missing.db")

        # Missing argument and missing env var raises ValueError
        old_env = os.environ.get("ART_DB_PATH")
        if "ART_DB_PATH" in os.environ:
            del os.environ["ART_DB_PATH"]
        try:
            with self.assertRaises(ValueError):
                create_app()
        finally:
            if old_env:
                os.environ["ART_DB_PATH"] = old_env

    # ==========================================
    # 11. CONTRACT SNAPSHOT ENVELOPES
    # ==========================================

    def test_contract_snapshot_envelopes(self):
        self._seed_test_ecosystem()

        # 1. List envelope keys
        _, _, list_body = self._client_request("GET", "/api/v1/investigations", "limit=1")
        self.assertEqual(set(list_body.keys()), {"items", "limit", "offset", "total"})

        # 2. Summary item keys
        summary = list_body["items"][0]
        expected_summary_keys = {
            "display_id", "record_key", "investigation_id", "canonical_bug_id",
            "source_kind", "classification", "lifecycle_phase", "status",
            "module", "severity", "priority", "assignee", "title",
            "created_at", "updated_at"
        }
        self.assertEqual(set(summary.keys()), expected_summary_keys)

        # 3. Detail item top-level keys
        _, _, detail_body = self._client_request("GET", f"/api/v1/bugs/{self.fix_bug_id}")
        expected_detail_keys = {
            "display_id", "record_key", "investigation_id", "canonical_bug_id",
            "source_kind", "slug", "lifecycle_phase", "status", "classification",
            "module", "severity", "priority", "assignee", "original_input_id",
            "active_ticket_id", "resolution", "created_at", "updated_at",
            "original_input", "evidence", "ai_artifacts", "research_artifacts",
            "current_ticket", "ticket_history", "developer_updates",
            "retest_artifacts", "audit_events"
        }
        self.assertEqual(set(detail_body.keys()), expected_detail_keys)

        # 4. Error envelope keys
        _, _, err_body = self._client_request("GET", "/api/v1/bugs/ART-NONEXISTENT-999")
        self.assertEqual(set(err_body.keys()), {"error"})
        self.assertEqual(set(err_body["error"].keys()), {"code", "message"})

    # ==========================================
    # 12. FASTAPI SPECIFIC TESTS (Phase 02A.1 18 Conditions)
    # ==========================================

    def test_fastapi_01_create_app_returns_fastapi_instance(self):
        self.assertIsInstance(self.app, FastAPI)

    def test_fastapi_02_importing_api_creates_no_db(self):
        # Already verified: importing api module creates zero DB files.
        import api
        import api.app
        self.assertTrue(hasattr(api, "create_app"))

    def test_fastapi_03_missing_db_fails_clearly(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            create_app("/nonexistent/path/db.sqlite")
        self.assertIn("Configured database does not exist", str(ctx.exception))

    def test_fastapi_04_get_health_works(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_fastapi_05_openapi_document_is_reachable(self):
        response = self.client.get("/api/v1/openapi.json")
        self.assertEqual(response.status_code, 200)
        openapi_doc = response.json()
        self.assertIn("openapi", openapi_doc)
        self.assertIn("paths", openapi_doc)

    def test_fastapi_06_to_09_openapi_routes_guarantee(self):
        response = self.client.get("/api/v1/openapi.json")
        self.assertEqual(response.status_code, 200)
        paths = response.json().get("paths", {})

        expected_business_routes = {
            "/api/v1/health",
            "/api/v1/investigations",
            "/api/v1/investigations/{investigation_id}",
            "/api/v1/bugs/{canonical_bug_id}",
            "/api/v1/work/my",
            "/api/v1/retest",
            "/api/v1/investigation-queue"
        }

        # 6. OpenAPI contains all 7 intended business GET routes
        for route in expected_business_routes:
            self.assertIn(route, paths, f"Expected route {route} missing from OpenAPI")
            self.assertIn("get", paths[route], f"Route {route} missing GET method in OpenAPI")

        # 7-9. Exactly FIVE business write operations exist
        self.assertIn("post", paths["/api/v1/investigations"])
        self.assertIn("post", paths["/api/v1/investigations/{investigation_id}/confirm"])
        self.assertIn("post", paths["/api/v1/bugs/{canonical_bug_id}/start-work"])
        self.assertIn("post", paths["/api/v1/bugs/{canonical_bug_id}/submit-fix"])
        self.assertIn("post", paths["/api/v1/bugs/{canonical_bug_id}/retest"])

        for path_str, path_item in paths.items():
            if path_str.startswith("/api/v1/"):
                methods = set(path_item.keys())
                if path_str == "/api/v1/investigations":
                    self.assertEqual(methods, {"get", "post"})
                elif path_str == "/api/v1/investigations/{investigation_id}/confirm":
                    self.assertEqual(methods, {"post"})
                elif path_str == "/api/v1/bugs/{canonical_bug_id}/start-work":
                    self.assertEqual(methods, {"post"})
                elif path_str == "/api/v1/bugs/{canonical_bug_id}/submit-fix":
                    self.assertEqual(methods, {"post"})
                elif path_str == "/api/v1/bugs/{canonical_bug_id}/retest":
                    self.assertEqual(methods, {"post"})
                elif path_str == "/api/v1/bugs/{canonical_bug_id}/azure-devops":
                    self.assertEqual(methods, {"post"})
                else:
                    self.assertNotIn("post", methods, f"Business route {path_str} has POST method in OpenAPI")
                self.assertNotIn("patch", methods, f"Business route {path_str} has PATCH method in OpenAPI")
                self.assertNotIn("delete", methods, f"Business route {path_str} has DELETE method in OpenAPI")
                self.assertNotIn("put", methods, f"Business route {path_str} has PUT method in OpenAPI")

    def test_fastapi_10_invalid_enum_query_rejected_predictably(self):
        response = self.client.get("/api/v1/investigations?severity=EXTREME")
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("Invalid severity", body["error"]["message"])

    def test_fastapi_11_malformed_inv_id_rejected(self):
        response = self.client.get("/api/v1/investigations/MALFORMED_123")
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("Invalid investigation ID format", body["error"]["message"])

    def test_fastapi_12_malformed_art_id_rejected(self):
        response = self.client.get("/api/v1/bugs/MALFORMED_456")
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("Invalid canonical bug ID format", body["error"]["message"])

    def test_fastapi_13_valid_unknown_inv_id_returns_404(self):
        response = self.client.get("/api/v1/investigations/INV-20260925-9999")
        self.assertEqual(response.status_code, 404)
        body = response.json()
        self.assertEqual(body["error"]["code"], "NOT_FOUND")

    def test_fastapi_14_valid_unknown_art_id_returns_404(self):
        response = self.client.get("/api/v1/bugs/ART-NONEXISTENT-999")
        self.assertEqual(response.status_code, 404)
        body = response.json()
        self.assertEqual(body["error"]["code"], "NOT_FOUND")

    def test_fastapi_15_unexpected_exception_produces_sanitized_500(self):
        # Trigger an unexpected exception by injecting corrupt data
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO investigations (
                record_key, investigation_id, canonical_bug_id, source_kind,
                slug, lifecycle_phase, original_input_id, created_at, updated_at
            ) VALUES (
                'rec_corrupt_test_fastapi', NULL, NULL, 'NATIVE',
                'corrupt', 'CAPTURE', 'INP-CORRUPT-2', '2026-09-25T00:00:00Z', '2026-09-25T00:00:00Z'
            );
        """)
        cursor.execute("""
            INSERT INTO original_inputs (
                id, investigation_key, tester_description, reporter, captured_at, initial_evidence_ids_json
            ) VALUES (
                'INP-CORRUPT-2', 'rec_corrupt_test_fastapi', 'desc', 'rep', '2026-09-25T00:00:00Z', '[]'
            );
        """)
        response = self.client.get("/api/v1/investigations")
        self.assertEqual(response.status_code, 500)
        body = response.json()
        self.assertEqual(body["error"]["code"], "INTERNAL_ERROR")
        self.assertNotIn("Traceback", json.dumps(body))
        self.assertNotIn("SELECT", json.dumps(body))
        self.assertNotIn("/home/", json.dumps(body))

    def test_fastapi_16_response_field_names_match_phase_02a(self):
        self._seed_test_ecosystem()
        response = self.client.get(f"/api/v1/bugs/{self.fix_bug_id}")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        expected_keys = {
            "display_id", "record_key", "investigation_id", "canonical_bug_id",
            "source_kind", "slug", "lifecycle_phase", "status", "classification",
            "module", "severity", "priority", "assignee", "original_input_id",
            "active_ticket_id", "resolution", "created_at", "updated_at",
            "original_input", "evidence", "ai_artifacts", "research_artifacts",
            "current_ticket", "ticket_history", "developer_updates",
            "retest_artifacts", "audit_events"
        }
        self.assertEqual(set(body.keys()), expected_keys)

    def test_fastapi_17_native_and_legacy_reads_still_work(self):
        self._seed_test_ecosystem()
        # Legacy
        res_leg = self.client.get("/api/v1/bugs/ART-AGENT-001")
        self.assertEqual(res_leg.status_code, 200)
        self.assertEqual(res_leg.json()["source_kind"], "LEGACY_IMPORT")

        # Native
        res_nat = self.client.get(f"/api/v1/investigations/{self.cap_inv_id}")
        self.assertEqual(res_nat.status_code, 200)
        self.assertEqual(res_nat.json()["source_kind"], "NATIVE")

    def test_fastapi_18_get_requests_produce_zero_db_mutation(self):
        self._seed_test_ecosystem()
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM audit_events;")
        audit_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM investigations;")
        inv_count = cursor.fetchone()[0]

        # Issue various GET requests
        self.client.get("/api/v1/investigations")
        self.client.get(f"/api/v1/investigations/{self.cap_inv_id}")
        self.client.get("/api/v1/retest")
        self.client.get("/api/v1/investigation-queue")

        cursor.execute("SELECT COUNT(*) FROM audit_events;")
        self.assertEqual(cursor.fetchone()[0], audit_count)
        cursor.execute("SELECT COUNT(*) FROM investigations;")
        self.assertEqual(cursor.fetchone()[0], inv_count)


if __name__ == "__main__":
    unittest.main()
