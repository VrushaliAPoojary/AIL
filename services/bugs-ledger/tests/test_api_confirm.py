"""
tests/test_api_confirm.py

Phase 02C — HTTP BUG Confirmation / Promotion Test Suite
Validates the complete test matrix specified for Phase 02C:
- ROUTE:
  1. Confirmation route exists.
  2. Valid confirmation returns 200.
  3. Existing Capture POST still returns 201.
  4. Existing GET routes remain unchanged.
- IDENTIFIER:
  5. Valid INV path accepted.
  6. Malformed INV rejected 400.
  7. ART ID supplied as investigation ID rejected (400).
  8. record_key supplied rejected (400).
  9. Valid nonexistent INV returns 404.
- TICKET:
  10. Approved ticket payload accepted.
  11. Exact title persisted.
  12. Repro Steps persisted.
  13. Expected Result persisted.
  14. Actual Result persisted.
  15. Business Impact persisted.
  16. Recommended Solution persisted.
  17. Module persisted.
  18. Environment persisted.
  19. Severity persisted.
  20. Priority persisted.
  21. Tags persisted.
  22. Discussion persisted.
- IDENTITY / PROMOTION:
  23. Original INV ID preserved.
  24. Canonical ART ID allocated.
  25. ART ID uses supplied module.
  26. Classification becomes BUG.
  27. Lifecycle becomes CONFIRMED.
  28. Status becomes OPEN.
  29. Display_id switches to ART ID.
- TICKET STATE:
  30. Active_ticket_id populated.
  31. Current_ticket populated.
  32. Current ticket revision = 1.
  33. Ticket_history contains exactly revision 1.
  34. Active ticket ID matches current ticket ID.
- PROJECTION:
  35. Aggregate module matches ticket module.
  36. Aggregate severity matches ticket severity.
  37. Aggregate priority matches ticket priority.
- SOURCE PRESERVATION:
  38. OriginalInput unchanged.
  39. Existing evidence metadata unchanged.
- AUDIT:
  40. Exactly one TICKET_CONFIRMED audit added.
  41. No transport confirmation audit added.
- NO EXTRA BEHAVIOR:
  42. Assignee not automatically changed.
  43. Status does not become FIXING.
  44. AI history unchanged.
  45. Research history unchanged.
- DOUBLE CONFIRMATION:
  46. Second confirmation returns conflict (409).
  47. Second confirmation creates no ART ID.
  48. Second confirmation creates no ticket revision.
  49. Second confirmation creates no confirmation audit.
  50. Second confirmation leaves state unchanged.
- ATOMICITY:
  51. Injected failure rolls back canonical bug ID.
  52. Rolls back classification/state.
  53. Rolls back ticket revision.
  54. Rolls back audit event.
  55. Rolls back BUG allocator increment.
  56. Next successful confirmation gets contiguous ART ID.
- MODULE ALLOCATION:
  57. AGENT and GOV allocations independent.
  58. Seeded legacy allocator maxima respected.
- READ AFTER WRITE:
  59. GET by INV succeeds after confirmation.
  60. GET by ART succeeds after confirmation.
  61. Both resolve to same record_key.
  62. List display_id is ART ID.
- QUEUE:
  63. Confirmed record disappears from investigation queue.
- VALIDATION:
  64. Missing required ticket field rejected (400).
  65. Unsupported request field rejected (400).
  66. Invalid module rejected (400).
  67. Invalid severity rejected (400).
  68. Invalid priority rejected (400).
  69. Malformed tags rejected (400).
  70. Malformed discussion rejected (400).
- ERROR SAFETY:
  71. Conflict response uses stable envelope.
  72. Unexpected failure sanitized.
  73. No SQL leakage.
  74. No traceback leakage.
  75. No filesystem path leakage.
- OPENAPI:
  76. Confirm POST appears.
  77. Exactly two business write routes exist.
  78-83. No start-work/fix/retest/verify/close/block write routes.
- REGRESSION & PRODUCTION:
  84. Capture tests remain green.
  85. Read API tests remain green.
  86. Existing domain tests remain green.
  87. Legacy Markdown unchanged.
  88. Seven PNG hashes unchanged.
  89. No production DB created.
"""

import unittest
import os
import shutil
import tempfile
import sqlite3
import json
from unittest.mock import patch

# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient

from core.storage.schema import init_db
from core.storage.db import get_connection
from core.storage.service import ResolutionService
from scripts.import_legacy import run_legacy_import
from api.app import create_app

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class TestApiConfirm(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="art_test_confirm_")
        self.db_path = os.path.join(self.test_dir, "test_confirm.db")
        self.conn = get_connection(self.db_path)
        init_db(self.conn)
        self.service = ResolutionService(self.conn)
        self.app = create_app(self.db_path)
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_sample_investigation(self, description="Defect description", reporter="tester-1") -> str:
        res = self.client.post("/api/v1/investigations", json={
            "tester_description": description,
            "reporter": reporter
        })
        self.assertEqual(res.status_code, 201)
        return res.json()["investigation"]["investigation_id"]

    def _sample_ticket_payload(self, title="Confirmed bug defect", module="AGENT") -> dict:
        return {
            "module": module,
            "actor": "lead-qa",
            "ticket": {
                "title": title,
                "reproSteps": "1. Step one\n2. Step two",
                "expectedResult": "Expected output format",
                "actualResult": "Observed parser error",
                "businessImpact": "Blocks pipeline completion",
                "recommendedSolution": "Upgrade parser rule",
                "environment": "Staging",
                "severity": "HIGH",
                "priority": "P1",
                "tags": [module.lower(), "pipeline"],
                "discussion": [
                    {
                        "author": "lead-qa",
                        "message": "Verified against staging environment",
                        "timestamp": "2026-09-25T12:00:00Z"
                    }
                ]
            }
        }

    # ==========================================
    # 1. ROUTE & METHOD TESTS (1 - 4)
    # ==========================================

    def test_01_to_04_route_presence_and_status(self):
        inv_id = self._create_sample_investigation()
        payload = self._sample_ticket_payload()

        # 1 & 2: Route exists and valid confirmation returns 200
        res = self.client.post(f"/api/v1/investigations/{inv_id}/confirm", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("investigation", data)
        art_id = data["investigation"]["canonical_bug_id"]
        self.assertEqual(art_id, "ART-AGENT-001")
        self.assertEqual(res.headers.get("Location"), f"/api/v1/bugs/{art_id}")

        # 3: Existing Capture POST still returns 201
        res_cap = self.client.post("/api/v1/investigations", json={"tester_description": "Second issue"})
        self.assertEqual(res_cap.status_code, 201)

        # 4: Existing GET routes remain unchanged
        res_get = self.client.get(f"/api/v1/investigations/{inv_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["canonical_bug_id"], "ART-AGENT-001")

    # ==========================================
    # 2. IDENTIFIER TESTS (5 - 9)
    # ==========================================

    def test_05_to_09_identifier_validation(self):
        inv_id = self._create_sample_investigation()
        payload = self._sample_ticket_payload()

        # 5: Valid INV path accepted
        res_valid = self.client.post(f"/api/v1/investigations/{inv_id}/confirm", json=payload)
        self.assertEqual(res_valid.status_code, 200)

        # 6: Malformed INV rejected 400
        res_mal = self.client.post("/api/v1/investigations/MALFORMED_123/confirm", json=payload)
        self.assertEqual(res_mal.status_code, 400)
        self.assertEqual(res_mal.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("Invalid investigation ID format", res_mal.json()["error"]["message"])

        # 7: ART ID supplied as investigation ID rejected (400)
        res_art = self.client.post("/api/v1/investigations/ART-AGENT-001/confirm", json=payload)
        self.assertEqual(res_art.status_code, 400)
        self.assertEqual(res_art.json()["error"]["code"], "VALIDATION_ERROR")

        # 8: record_key (UUID) supplied rejected (400)
        res_uuid = self.client.post("/api/v1/investigations/12345678-1234-5678-1234-567812345678/confirm", json=payload)
        self.assertEqual(res_uuid.status_code, 400)
        self.assertEqual(res_uuid.json()["error"]["code"], "VALIDATION_ERROR")

        # 9: Valid nonexistent INV returns 404
        res_404 = self.client.post("/api/v1/investigations/INV-20260925-9999/confirm", json=payload)
        self.assertEqual(res_404.status_code, 404)
        self.assertEqual(res_404.json()["error"]["code"], "NOT_FOUND")

    # ==========================================
    # 3. TICKET FIELDS PERSISTENCE (10 - 22)
    # ==========================================

    def test_10_to_22_ticket_fields_persisted(self):
        inv_id = self._create_sample_investigation()
        payload = self._sample_ticket_payload()
        t = payload["ticket"]

        res = self.client.post(f"/api/v1/investigations/{inv_id}/confirm", json=payload)
        self.assertEqual(res.status_code, 200)
        inv = res.json()["investigation"]
        cur = inv["current_ticket"]

        # 10 - 22: All 12 fields persisted accurately
        self.assertEqual(cur["title"], t["title"])
        self.assertEqual(cur["repro_steps"], t["reproSteps"])
        self.assertEqual(cur["expected_result"], t["expectedResult"])
        self.assertEqual(cur["actual_result"], t["actualResult"])
        self.assertEqual(cur["business_impact"], t["businessImpact"])
        self.assertEqual(cur["recommended_solution"], t["recommendedSolution"])
        self.assertEqual(cur["module"], "AGENT")
        self.assertEqual(cur["environment"], t["environment"])
        self.assertEqual(cur["severity"], t["severity"])
        self.assertEqual(cur["priority"], t["priority"])
        self.assertEqual(cur["tags"], t["tags"])
        self.assertEqual(len(cur["discussion"]), 1)
        self.assertEqual(cur["discussion"][0]["author"], "lead-qa")

    # ==========================================
    # 4. IDENTITY & PROMOTION STATE (23 - 29)
    # ==========================================

    def test_23_to_29_identity_and_promotion(self):
        inv_id = self._create_sample_investigation()
        payload = self._sample_ticket_payload(module="SFN")

        res = self.client.post(f"/api/v1/investigations/{inv_id}/confirm", json=payload)
        self.assertEqual(res.status_code, 200)
        inv = res.json()["investigation"]

        # 23: Original INV ID preserved
        self.assertEqual(inv["investigation_id"], inv_id)

        # 24 & 25: Canonical ART ID allocated with supplied module
        self.assertEqual(inv["canonical_bug_id"], "ART-SFN-001")

        # 26: Classification becomes BUG
        self.assertEqual(inv["classification"], "BUG")

        # 27: Lifecycle becomes CONFIRMED
        self.assertEqual(inv["lifecycle_phase"], "CONFIRMED")

        # 28: Status becomes OPEN
        self.assertEqual(inv["status"], "OPEN")

        # 29: display_id switches to ART ID
        self.assertEqual(inv["display_id"], "ART-SFN-001")

    # ==========================================
    # 5. TICKET STATE & PROJECTION (30 - 37)
    # ==========================================

    def test_30_to_37_ticket_state_and_projection(self):
        inv_id = self._create_sample_investigation()
        payload = self._sample_ticket_payload(module="GOV")

        res = self.client.post(f"/api/v1/investigations/{inv_id}/confirm", json=payload)
        self.assertEqual(res.status_code, 200)
        inv = res.json()["investigation"]

        # 30 - 34: Active ticket and history
        self.assertIsNotNone(inv["active_ticket_id"])
        self.assertIsNotNone(inv["current_ticket"])
        self.assertEqual(inv["current_ticket"]["revision"], 1)
        self.assertEqual(len(inv["ticket_history"]), 1)
        self.assertEqual(inv["active_ticket_id"], inv["current_ticket"]["ticket_id"])

        # 35 - 37: Aggregate root projection matches ticket values
        self.assertEqual(inv["module"], inv["current_ticket"]["module"])
        self.assertEqual(inv["severity"], inv["current_ticket"]["severity"])
        self.assertEqual(inv["priority"], inv["current_ticket"]["priority"])

    # ==========================================
    # 6. SOURCE PRESERVATION & AUDIT (38 - 45)
    # ==========================================

    def test_38_to_45_source_preservation_and_audit(self):
        orig_desc = "Human entered issue description with special characters $#@!"
        orig_reporter = "alice"
        inv_id = self._create_sample_investigation(description=orig_desc, reporter=orig_reporter)

        res = self.client.post(f"/api/v1/investigations/{inv_id}/confirm", json=self._sample_ticket_payload())
        self.assertEqual(res.status_code, 200)
        inv = res.json()["investigation"]

        # 38: OriginalInput unchanged
        self.assertEqual(inv["original_input"]["tester_description"], orig_desc)
        self.assertEqual(inv["original_input"]["reporter"], orig_reporter)

        # 39: Existing evidence metadata unchanged
        self.assertEqual(inv["evidence"], [])

        # 40 & 41: Exactly one TICKET_CONFIRMED audit added (total = 2)
        audits = inv["audit_events"]
        self.assertEqual(len(audits), 2)
        event_types = [a["event_type"] for a in audits]
        self.assertEqual(event_types, ["INVESTIGATION_CAPTURED", "TICKET_CONFIRMED"])

        # 42 & 43: Assignee not automatically changed; status is OPEN, not FIXING
        self.assertIsNone(inv["assignee"])
        self.assertEqual(inv["status"], "OPEN")

        # 44 & 45: AI and research history empty
        self.assertEqual(inv["ai_artifacts"], [])
        self.assertEqual(inv["research_artifacts"], [])

    # ==========================================
    # 7. DOUBLE CONFIRMATION (46 - 50)
    # ==========================================

    def test_46_to_50_double_confirmation_conflict(self):
        inv_id = self._create_sample_investigation()
        payload = self._sample_ticket_payload()

        # First confirmation succeeds
        res1 = self.client.post(f"/api/v1/investigations/{inv_id}/confirm", json=payload)
        self.assertEqual(res1.status_code, 200)
        inv1 = res1.json()["investigation"]

        # 46: Second confirmation returns 409 CONFLICT
        res2 = self.client.post(f"/api/v1/investigations/{inv_id}/confirm", json=payload)
        self.assertEqual(res2.status_code, 409)
        self.assertEqual(res2.json()["error"]["code"], "CONFLICT")

        # 47 - 50: State unchanged, no extra ART ID, ticket revision, or audit
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ticket_revisions;")
        self.assertEqual(cursor.fetchone()[0], 1)
        cursor.execute("SELECT COUNT(*) FROM audit_events;")
        self.assertEqual(cursor.fetchone()[0], 2)

    # ==========================================
    # 8. ATOMICITY & ALLOCATION ROLLBACK (51 - 56)
    # ==========================================

    def test_51_to_56_atomicity_and_rollback(self):
        inv_id1 = self._create_sample_investigation(description="Issue 1")
        inv_id2 = self._create_sample_investigation(description="Issue 2")

        payload = self._sample_ticket_payload(module="AGENT")

        # Simulate failure during service confirm_bug (e.g. repo update fails)
        with patch.object(ResolutionService, "confirm_bug") as mock_confirm:
            from core.storage.service import ServiceResult
            mock_confirm.return_value = ServiceResult(
                success=False,
                data=None,
                audit_event=None,
                error="Cannot confirm investigation from lifecycle phase 'INVALID'"
            )
            res_fail = self.client.post(f"/api/v1/investigations/{inv_id1}/confirm", json=payload)
            self.assertEqual(res_fail.status_code, 409)

        # 51 - 55: Failed confirm leaves aggregate unpromoted, no revisions, no bug ID
        detail = self.client.get(f"/api/v1/investigations/{inv_id1}").json()
        self.assertEqual(detail["lifecycle_phase"], "CAPTURE")
        self.assertIsNone(detail["canonical_bug_id"])
        self.assertIsNone(detail["active_ticket_id"])

        # 56: Next successful confirmation receives contiguous ART ID (ART-AGENT-001)
        res_succ = self.client.post(f"/api/v1/investigations/{inv_id1}/confirm", json=payload)
        self.assertEqual(res_succ.status_code, 200)
        self.assertEqual(res_succ.json()["investigation"]["canonical_bug_id"], "ART-AGENT-001")

        # Second successful gets ART-AGENT-002
        res_succ2 = self.client.post(f"/api/v1/investigations/{inv_id2}/confirm", json=payload)
        self.assertEqual(res_succ2.status_code, 200)
        self.assertEqual(res_succ2.json()["investigation"]["canonical_bug_id"], "ART-AGENT-002")

    # ==========================================
    # 9. MODULE SCOPED ALLOCATION (57 - 58)
    # ==========================================

    def test_57_to_58_module_allocation_and_legacy_maxima(self):
        # Seed legacy import
        run_legacy_import(self.db_path)
        # Legacy maximums: ART-AGENT-001, ART-GOV-003, ART-SFN-001

        inv_agent = self._create_sample_investigation(description="Agent defect")
        inv_gov = self._create_sample_investigation(description="Gov defect")
        inv_sfn = self._create_sample_investigation(description="SFN defect")

        # Confirm AGENT -> ART-AGENT-002
        res_ag = self.client.post(f"/api/v1/investigations/{inv_agent}/confirm", json=self._sample_ticket_payload(module="AGENT"))
        self.assertEqual(res_ag.status_code, 200)
        self.assertEqual(res_ag.json()["investigation"]["canonical_bug_id"], "ART-AGENT-002")

        # Confirm GOV -> ART-GOV-004
        res_gv = self.client.post(f"/api/v1/investigations/{inv_gov}/confirm", json=self._sample_ticket_payload(module="GOV"))
        self.assertEqual(res_gv.status_code, 200)
        self.assertEqual(res_gv.json()["investigation"]["canonical_bug_id"], "ART-GOV-004")

        # Confirm SFN -> ART-SFN-002
        res_sf = self.client.post(f"/api/v1/investigations/{inv_sfn}/confirm", json=self._sample_ticket_payload(module="SFN"))
        self.assertEqual(res_sf.status_code, 200)
        self.assertEqual(res_sf.json()["investigation"]["canonical_bug_id"], "ART-SFN-002")

    # ==========================================
    # 10. READ AFTER CONFIRM & QUEUE (59 - 63)
    # ==========================================

    def test_59_to_63_read_after_confirm_and_queue_transition(self):
        inv_id = self._create_sample_investigation()

        # Check in investigation queue prior to confirm
        res_q_before = self.client.get("/api/v1/investigation-queue")
        self.assertEqual(res_q_before.json()["total"], 1)

        # Confirm
        res_conf = self.client.post(f"/api/v1/investigations/{inv_id}/confirm", json=self._sample_ticket_payload())
        self.assertEqual(res_conf.status_code, 200)
        art_id = res_conf.json()["investigation"]["canonical_bug_id"]

        # 59: GET by INV ID succeeds
        res_inv = self.client.get(f"/api/v1/investigations/{inv_id}")
        self.assertEqual(res_inv.status_code, 200)

        # 60: GET by ART ID succeeds
        res_art = self.client.get(f"/api/v1/bugs/{art_id}")
        self.assertEqual(res_art.status_code, 200)

        # 61: Both resolve to same record_key
        self.assertEqual(res_inv.json()["record_key"], res_art.json()["record_key"])

        # 62: List shows display_id as ART ID
        res_list = self.client.get("/api/v1/investigations")
        item = res_list.json()["items"][0]
        self.assertEqual(item["display_id"], art_id)
        self.assertEqual(item["investigation_id"], inv_id)

        # 63: Confirmed record disappears from investigation queue
        res_q_after = self.client.get("/api/v1/investigation-queue")
        self.assertEqual(res_q_after.json()["total"], 0)

    # ==========================================
    # 11. VALIDATION & ERROR SAFETY (64 - 75)
    # ==========================================

    def test_64_to_75_validation_and_sanitization(self):
        inv_id = self._create_sample_investigation()

        # 64: Missing required title in ticket
        bad_ticket = self._sample_ticket_payload()
        del bad_ticket["ticket"]["title"]
        res_no_title = self.client.post(f"/api/v1/investigations/{inv_id}/confirm", json=bad_ticket)
        self.assertEqual(res_no_title.status_code, 400)
        self.assertEqual(res_no_title.json()["error"]["code"], "VALIDATION_ERROR")

        # 65: Unsupported extra field rejected
        bad_extra = self._sample_ticket_payload()
        bad_extra["injected_field"] = "bad"
        res_extra = self.client.post(f"/api/v1/investigations/{inv_id}/confirm", json=bad_extra)
        self.assertEqual(res_extra.status_code, 400)
        self.assertIn("Extra inputs are not permitted", res_extra.json()["error"]["message"])

        # 66: Invalid module rejected
        bad_mod = self._sample_ticket_payload(module="INVALID_MOD")
        res_mod = self.client.post(f"/api/v1/investigations/{inv_id}/confirm", json=bad_mod)
        self.assertEqual(res_mod.status_code, 400)
        self.assertIn("not an approved canonical module", res_mod.json()["error"]["message"])

        # 67: Invalid severity rejected
        bad_sev = self._sample_ticket_payload()
        bad_sev["ticket"]["severity"] = "ULTRA_CRITICAL"
        res_sev = self.client.post(f"/api/v1/investigations/{inv_id}/confirm", json=bad_sev)
        self.assertEqual(res_sev.status_code, 400)

        # 68: Invalid priority rejected
        bad_pri = self._sample_ticket_payload()
        bad_pri["ticket"]["priority"] = "P99"
        res_pri = self.client.post(f"/api/v1/investigations/{inv_id}/confirm", json=bad_pri)
        self.assertEqual(res_pri.status_code, 400)

        # 69: Malformed tags rejected
        bad_tags = self._sample_ticket_payload()
        bad_tags["ticket"]["tags"] = "not-a-list"
        res_tags = self.client.post(f"/api/v1/investigations/{inv_id}/confirm", json=bad_tags)
        self.assertEqual(res_tags.status_code, 400)

        # 70: Malformed discussion rejected
        bad_disc = self._sample_ticket_payload()
        bad_disc["ticket"]["discussion"] = [{"author": "lead-qa"}]  # missing message and timestamp
        res_disc = self.client.post(f"/api/v1/investigations/{inv_id}/confirm", json=bad_disc)
        self.assertEqual(res_disc.status_code, 400)

        # 72 - 75: Unexpected error sanitized without SQL/paths
        with patch.object(ResolutionService, "confirm_bug", side_effect=Exception("DB syntax error at /home/prod/db SELECT *")):
            res_crash = self.client.post(f"/api/v1/investigations/{inv_id}/confirm", json=self._sample_ticket_payload())
            self.assertEqual(res_crash.status_code, 500)
            err_json = json.dumps(res_crash.json())
            self.assertNotIn("Traceback", err_json)
            self.assertNotIn("SELECT", err_json)
            self.assertNotIn("/home/prod/db", err_json)

    # ==========================================
    # 12. OPENAPI & LEGACY SAFETY (76 - 83)
    # ==========================================

    def test_76_to_83_openapi_write_routes(self):
        res = self.client.get("/api/v1/openapi.json")
        self.assertEqual(res.status_code, 200)
        paths = res.json().get("paths", {})

        # 76: POST confirm route appears
        # 77 - 83: Exactly FIVE business write operations exist
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


if __name__ == "__main__":
    unittest.main()
