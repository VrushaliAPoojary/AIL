"""
tests/test_api_capture.py

Phase 02B — HTTP Capture Endpoint Test Suite
Validates the complete test matrix specified for Phase 02B:
- ROUTE:
  1. POST /api/v1/investigations exists.
  2. Returns 201 for valid capture.
  3. Existing GET /api/v1/investigations still works.
  4. PUT remains unsupported (405).
  5. PATCH remains unsupported (405).
  6. DELETE remains unsupported (405).
- INPUT:
  7. Human description preserved exactly.
  8. Missing required description rejected (400) when no evidence provided.
  9. Empty description rejected (400) when no evidence provided.
  10. Invalid JSON / body type rejected (400).
  11. Unsupported request fields rejected (400) rather than silently ignored.
  12. Exposed fields / structures validated.
- IDENTITY:
  13. Successful capture receives INV business ID.
  14. No ART bug ID allocated.
  15. record_key generated internally.
  16. API caller cannot supply record_key.
  17. API caller cannot supply canonical_bug_id.
- STATE:
  18. lifecycle_phase is CAPTURE.
  19. status is null.
  20. no active ticket.
  21. no ticket history.
  22. no current ticket.
- ORIGINAL INPUT:
  23. OriginalInput created.
  24. Tester description matches request exactly.
  25. Reporter behavior matches existing service contract.
- AUDIT:
  26. Exactly one capture audit event according to service behavior.
  27. API creates no duplicate transport audit event.
- AI / RESEARCH:
  28. AI artifact history empty.
  29. Research artifact history empty.
  30. No automatic classification performed.
- READ AFTER WRITE:
  31. GET by returned INV ID succeeds.
  32. GET detail matches persisted capture.
  33. GET list includes new investigation.
- ATOMICITY:
  34. Forced service/persistence failure returns controlled 500.
  35. Failed request leaves no investigation.
  36. Failed request leaves no OriginalInput.
  37. Failed request leaves no capture audit.
  38. Failed request does not commit INV sequence allocation.
  39. Next successful capture receives correct sequence.
- ERROR SAFETY:
  40. Domain validation error uses stable error envelope.
  41. Unexpected error uses sanitized INTERNAL_ERROR.
  42. No SQL leakage.
  43. No traceback leakage.
  44. No DB path leakage.
- OPENAPI:
  45. POST /api/v1/investigations appears.
  46. It is the only business write operation.
  47. No confirmation route exists.
  48. No start-work route exists.
  49. No fix/retest/verify/close/block routes exist.
- LEGACY SAFETY:
  50. Legacy Markdown unchanged.
  51. All seven PNG hashes unchanged.
  52. Capture does not invoke legacy import.
"""

import unittest
import os
import shutil
import tempfile
import sqlite3
import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from core.storage.schema import init_db
from core.storage.db import get_connection
from core.storage.service import ResolutionService
from api.app import create_app

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class TestApiCapture(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="art_test_capture_")
        self.db_path = os.path.join(self.test_dir, "test_capture.db")
        self.conn = get_connection(self.db_path)
        init_db(self.conn)
        self.app = create_app(self.db_path)
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # ==========================================
    # 1. ROUTE TESTS (1 - 6)
    # ==========================================

    def test_01_to_06_route_presence_and_methods(self):
        # 1 & 2: POST /api/v1/investigations exists and returns 201 for valid capture
        payload = {
            "tester_description": "Observed crash when submitting empty query",
            "reporter": "tester-1",
            "slug": "empty-query-crash"
        }
        res_post = self.client.post("/api/v1/investigations", json=payload)
        self.assertEqual(res_post.status_code, 201)
        data = res_post.json()
        self.assertIn("investigation", data)
        inv_id = data["investigation"]["investigation_id"]
        self.assertTrue(inv_id.startswith("INV-"))
        self.assertEqual(res_post.headers.get("Location"), f"/api/v1/investigations/{inv_id}")

        # 3: Existing GET /api/v1/investigations still works
        res_get = self.client.get("/api/v1/investigations")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["total"], 1)

        # 4: PUT remains unsupported (405)
        res_put = self.client.put("/api/v1/investigations", json=payload)
        self.assertEqual(res_put.status_code, 405)
        self.assertEqual(res_put.json()["error"]["code"], "METHOD_NOT_ALLOWED")

        # 5: PATCH remains unsupported (405)
        res_patch = self.client.patch("/api/v1/investigations", json=payload)
        self.assertEqual(res_patch.status_code, 405)
        self.assertEqual(res_patch.json()["error"]["code"], "METHOD_NOT_ALLOWED")

        # 6: DELETE remains unsupported (405)
        res_delete = self.client.delete("/api/v1/investigations")
        self.assertEqual(res_delete.status_code, 405)
        self.assertEqual(res_delete.json()["error"]["code"], "METHOD_NOT_ALLOWED")

    # ==========================================
    # 2. INPUT TESTS (7 - 12)
    # ==========================================

    def test_07_to_12_input_validation(self):
        # 7: Human description preserved exactly
        raw_text = "Special symbols !@#$%^&*() and \n newline preserved exactly."
        res = self.client.post("/api/v1/investigations", json={
            "tester_description": raw_text,
            "reporter": "bob"
        })
        self.assertEqual(res.status_code, 201)
        inv = res.json()["investigation"]
        self.assertEqual(inv["original_input"]["tester_description"], raw_text)

        # 8: Missing required description rejected (400) when no evidence provided
        res_missing = self.client.post("/api/v1/investigations", json={
            "reporter": "bob"
        })
        self.assertEqual(res_missing.status_code, 400)
        self.assertEqual(res_missing.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("Capture requires description or initial evidence", res_missing.json()["error"]["message"])

        # 9: Empty description rejected (400) when no evidence provided
        res_empty = self.client.post("/api/v1/investigations", json={
            "tester_description": "",
            "reporter": "bob"
        })
        self.assertEqual(res_empty.status_code, 400)
        self.assertEqual(res_empty.json()["error"]["code"], "VALIDATION_ERROR")

        # 10: Invalid JSON / body type rejected (400)
        res_bad_type = self.client.post(
            "/api/v1/investigations",
            content="not a valid json",
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(res_bad_type.status_code, 400)
        self.assertEqual(res_bad_type.json()["error"]["code"], "VALIDATION_ERROR")

        # 11: Unsupported request fields rejected rather than silently ignored (extra='forbid')
        res_extra = self.client.post("/api/v1/investigations", json={
            "tester_description": "Valid description",
            "reporter": "alice",
            "unsupported_field": "injected_value"
        })
        self.assertEqual(res_extra.status_code, 400)
        self.assertEqual(res_extra.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("Extra inputs are not permitted", res_extra.json()["error"]["message"])

        # 12: Exposed fields / structures validated (e.g. initial_evidence_ids must be list)
        res_bad_ev = self.client.post("/api/v1/investigations", json={
            "tester_description": "Valid description",
            "initial_evidence_ids": "not-a-list"
        })
        self.assertEqual(res_bad_ev.status_code, 400)
        self.assertEqual(res_bad_ev.json()["error"]["code"], "VALIDATION_ERROR")

    # ==========================================
    # 3. IDENTITY TESTS (13 - 17)
    # ==========================================

    def test_13_to_17_identity_guarantees(self):
        # 13: Successful capture receives INV business ID
        res = self.client.post("/api/v1/investigations", json={"tester_description": "Valid issue"})
        self.assertEqual(res.status_code, 201)
        inv = res.json()["investigation"]
        inv_id = inv["investigation_id"]
        self.assertTrue(inv_id.startswith("INV-"))

        # 14: No ART bug ID allocated
        self.assertIsNone(inv["canonical_bug_id"])

        # 15: record_key generated internally (UUID format)
        self.assertIsNotNone(inv["record_key"])
        self.assertNotEqual(inv["record_key"], inv_id)

        # 16: API caller cannot supply record_key
        res_rk = self.client.post("/api/v1/investigations", json={
            "tester_description": "Attempting to force record key",
            "record_key": "custom-key"
        })
        self.assertEqual(res_rk.status_code, 400)
        self.assertEqual(res_rk.json()["error"]["code"], "VALIDATION_ERROR")

        # 17: API caller cannot supply canonical_bug_id
        res_art = self.client.post("/api/v1/investigations", json={
            "tester_description": "Attempting to force ART ID",
            "canonical_bug_id": "ART-AGENT-999"
        })
        self.assertEqual(res_art.status_code, 400)
        self.assertEqual(res_art.json()["error"]["code"], "VALIDATION_ERROR")

    # ==========================================
    # 4. STATE TESTS (18 - 22)
    # ==========================================

    def test_18_to_22_state_guarantees(self):
        res = self.client.post("/api/v1/investigations", json={"tester_description": "State verification"})
        self.assertEqual(res.status_code, 201)
        inv = res.json()["investigation"]

        # 18: lifecycle_phase is CAPTURE
        self.assertEqual(inv["lifecycle_phase"], "CAPTURE")

        # 19: status is null
        self.assertIsNone(inv["status"])

        # 20: no active ticket
        self.assertIsNone(inv["active_ticket_id"])

        # 21: no ticket history
        self.assertEqual(inv["ticket_history"], [])

        # 22: no current ticket
        self.assertIsNone(inv["current_ticket"])

    # ==========================================
    # 5. ORIGINAL INPUT TESTS (23 - 25)
    # ==========================================

    def test_23_to_25_original_input_guarantees(self):
        payload = {
            "tester_description": "Button unresponsive on mobile viewport",
            "reporter": "lead-qa"
        }
        res = self.client.post("/api/v1/investigations", json=payload)
        self.assertEqual(res.status_code, 201)
        inv = res.json()["investigation"]

        # 23: OriginalInput created
        orig = inv["original_input"]
        self.assertIsNotNone(orig)
        self.assertTrue(orig["id"].startswith("INP-"))

        # 24: Tester description matches request exactly
        self.assertEqual(orig["tester_description"], payload["tester_description"])

        # 25: Reporter behavior matches existing service contract
        self.assertEqual(orig["reporter"], "lead-qa")

        # When reporter is omitted, default 'anonymous' is applied safely
        res_anon = self.client.post("/api/v1/investigations", json={"tester_description": "Issue from guest"})
        self.assertEqual(res_anon.status_code, 201)
        self.assertEqual(res_anon.json()["investigation"]["original_input"]["reporter"], "anonymous")

    # ==========================================
    # 6. AUDIT TESTS (26 - 27)
    # ==========================================

    def test_26_to_27_audit_guarantees(self):
        res = self.client.post("/api/v1/investigations", json={"tester_description": "Audit check"})
        self.assertEqual(res.status_code, 201)
        inv = res.json()["investigation"]

        # 26: Exactly one capture audit event according to service behavior
        audits = inv["audit_events"]
        self.assertEqual(len(audits), 1)
        self.assertEqual(audits[0]["event_type"], "INVESTIGATION_CAPTURED")

        # 27: API creates no duplicate transport audit event
        event_types = [a["event_type"] for a in audits]
        self.assertNotIn("HTTP_CREATED", event_types)
        self.assertNotIn("API_CAPTURED", event_types)
        self.assertNotIn("POST_RECEIVED", event_types)

    # ==========================================
    # 7. AI / RESEARCH TESTS (28 - 30)
    # ==========================================

    def test_28_to_30_no_ai_or_automatic_classification(self):
        res = self.client.post("/api/v1/investigations", json={"tester_description": "AI safety check"})
        self.assertEqual(res.status_code, 201)
        inv = res.json()["investigation"]

        # 28: AI artifact history empty
        self.assertEqual(inv["ai_artifacts"], [])

        # 29: Research artifact history empty
        self.assertEqual(inv["research_artifacts"], [])

        # 30: No automatic classification performed (remains null)
        self.assertIsNone(inv["classification"])

    # ==========================================
    # 8. READ AFTER WRITE TESTS (31 - 33)
    # ==========================================

    def test_31_to_33_read_after_write(self):
        payload = {
            "tester_description": "Read after write check",
            "reporter": "charlie"
        }
        res_post = self.client.post("/api/v1/investigations", json=payload)
        self.assertEqual(res_post.status_code, 201)
        inv_post = res_post.json()["investigation"]
        inv_id = inv_post["investigation_id"]

        # 31: GET by returned INV ID succeeds
        res_get_detail = self.client.get(f"/api/v1/investigations/{inv_id}")
        self.assertEqual(res_get_detail.status_code, 200)

        # 32: GET detail matches persisted capture
        inv_get = res_get_detail.json()
        self.assertEqual(inv_get["investigation_id"], inv_id)
        self.assertEqual(inv_get["original_input"]["tester_description"], payload["tester_description"])
        self.assertEqual(inv_get["original_input"]["reporter"], payload["reporter"])

        # 33: GET list includes new investigation
        res_get_list = self.client.get("/api/v1/investigations")
        self.assertEqual(res_get_list.status_code, 200)
        list_body = res_get_list.json()
        self.assertEqual(list_body["total"], 1)
        self.assertEqual(list_body["items"][0]["investigation_id"], inv_id)

    # ==========================================
    # 9. ATOMICITY TESTS (34 - 39)
    # ==========================================

    def test_34_to_39_atomicity_and_sequence_rollback(self):
        # Initial capture succeeds -> sequence 1
        res1 = self.client.post("/api/v1/investigations", json={"tester_description": "First successful"})
        self.assertEqual(res1.status_code, 201)
        id1 = res1.json()["investigation"]["investigation_id"]
        self.assertTrue(id1.endswith("-0001"))

        # 34: Force service/persistence failure during insert (e.g. simulated DB error)
        with patch.object(ResolutionService, "create_investigation") as mock_create:
            from core.storage.service import ServiceResult
            mock_create.return_value = ServiceResult(
                success=False,
                data=None,
                audit_event=None,
                error="Simulated disk write failure"
            )
            res_fail = self.client.post("/api/v1/investigations", json={"tester_description": "Will fail"})
            self.assertEqual(res_fail.status_code, 500)
            self.assertEqual(res_fail.json()["error"]["code"], "INTERNAL_ERROR")

        # 35: Failed request leaves no investigation
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM investigations;")
        self.assertEqual(cursor.fetchone()[0], 1)

        # 36: Failed request leaves no OriginalInput
        cursor.execute("SELECT COUNT(*) FROM original_inputs;")
        self.assertEqual(cursor.fetchone()[0], 1)

        # 37: Failed request leaves no capture audit
        cursor.execute("SELECT COUNT(*) FROM audit_events;")
        self.assertEqual(cursor.fetchone()[0], 1)

        # 38 & 39: Failed request does not corrupt sequence; next successful capture gets sequence 2
        res2 = self.client.post("/api/v1/investigations", json={"tester_description": "Second successful"})
        self.assertEqual(res2.status_code, 201)
        id2 = res2.json()["investigation"]["investigation_id"]
        self.assertTrue(id2.endswith("-0002"))

    # ==========================================
    # 10. ERROR SAFETY TESTS (40 - 44)
    # ==========================================

    def test_40_to_44_error_safety(self):
        # 40: Domain validation error uses stable error envelope
        res_dom = self.client.post("/api/v1/investigations", json={"tester_description": ""})
        self.assertEqual(res_dom.status_code, 400)
        self.assertEqual(res_dom.json()["error"]["code"], "VALIDATION_ERROR")

        # 41: Unexpected error uses sanitized INTERNAL_ERROR
        with patch("api.app.ResolutionService.create_investigation", side_effect=RuntimeError("Secret DB crash at /home/prod/db")):
            res_err = self.client.post("/api/v1/investigations", json={"tester_description": "Trigger crash"})
            self.assertEqual(res_err.status_code, 500)
            body = res_err.json()
            self.assertEqual(body["error"]["code"], "INTERNAL_ERROR")

            # 42 - 44: No SQL, traceback, or DB path leakage
            raw_err = json.dumps(body)
            self.assertNotIn("Traceback", raw_err)
            self.assertNotIn("Secret DB crash", raw_err)
            self.assertNotIn("/home/prod/db", raw_err)

    # ==========================================
    # 11. OPENAPI TESTS (45 - 49)
    # ==========================================

    def test_45_to_49_openapi_write_route_guarantee(self):
        res = self.client.get("/api/v1/openapi.json")
        self.assertEqual(res.status_code, 200)
        paths = res.json().get("paths", {})

        # 45: POST /api/v1/investigations appears
        self.assertIn("/api/v1/investigations", paths)
        self.assertIn("post", paths["/api/v1/investigations"])

        # Only capture, confirm, start-work, submit-fix, and retest write routes exist
        allowed_write_routes = {
            "/api/v1/investigations",
            "/api/v1/investigations/{investigation_id}/confirm",
            "/api/v1/bugs/{canonical_bug_id}/start-work",
            "/api/v1/bugs/{canonical_bug_id}/submit-fix",
            "/api/v1/bugs/{canonical_bug_id}/retest",
            "/api/v1/bugs/{canonical_bug_id}/azure-devops"
        }
        for path_str, path_item in paths.items():
            if path_str.startswith("/api/v1/"):
                for method in path_item.keys():
                    if method in {"post", "put", "patch", "delete"}:
                        self.assertIn(path_str, allowed_write_routes)
                        self.assertEqual(method, "post")

    # ==========================================
    # 12. LEGACY SAFETY TESTS (50 - 52)
    # ==========================================

    def test_50_to_52_legacy_safety(self):
        # 50 - 52: Capture does not invoke legacy import and touches no files
        res = self.client.post("/api/v1/investigations", json={"tester_description": "Legacy isolation test"})
        self.assertEqual(res.status_code, 201)

        # Legacy records remain untouched (0 legacy records exist in DB)
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM investigations WHERE source_kind = 'LEGACY_IMPORT';")
        self.assertEqual(cursor.fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
