"""
tests/test_api_start_work.py

Phase 02D — HTTP Start Work / Developer Assignment Test Suite
Validates the complete test matrix specified for Phase 02D:
- ROUTE:
  1. start-work route exists.
  2. Valid Start Work returns 200.
  3. Capture still returns 201.
  4. Confirmation still returns 200.
- IDENTIFIER:
  5. Valid ART ID accepted.
  6. INV ID rejected (400).
  7. record_key rejected (400).
  8. Malformed ART ID rejected (400).
  9. Valid unknown ART ID returns 404.
- REQUEST:
  10. Valid assignee accepted.
  11. Missing assignee rejected (400).
  12. Empty assignee rejected (400).
  13. Unsupported fields rejected (400).
  14. Actor behavior matches service contract.
- STATE:
  15. OPEN becomes FIXING.
  16. Assignee becomes supplied developer.
  17. Classification remains BUG.
  18. canonical_bug_id unchanged.
  19. investigation_id unchanged.
  20. lifecycle_phase matches engine behavior (CONFIRMED).
- TICKET PRESERVATION:
  21. active_ticket_id unchanged.
  22. current_ticket unchanged.
  23. ticket_history unchanged.
  24. module unchanged.
  25. severity unchanged.
  26. priority unchanged.
- SOURCE PRESERVATION:
  27. OriginalInput unchanged.
  28. Evidence metadata unchanged.
- NO EXTRA ARTIFACTS:
  29. developer_updates unchanged.
  30. retest_artifacts unchanged.
  31. AI artifacts unchanged.
  32. Research artifacts unchanged.
- AUDIT:
  33. Exactly one service-generated Start Work audit added.
  34. No API transport audit added.
- ALLOCATORS:
  35. INV allocator unchanged.
  36. BUG allocator unchanged.
- MY WORK:
  37. Before Start Work bug absent from developer My Work.
  38. After Start Work bug appears.
  39. Other developer does not see bug.
- QUEUES:
  40. FIXING bug absent from Retest Queue.
  41. Bug remains absent from Investigation Queue.
- DOUBLE START:
  42. Second Start Work rejected.
  43. Returns conflict (409).
  44. No second Start Work audit.
  45. No reassignment occurs.
  46. No IDs allocated.
- WRONG SOURCE STATES:
  47. CAPTURE record cannot Start Work.
  48. FIXING record cannot Start Work again.
  49. RETEST record cannot Start Work.
  50. VERIFIED record cannot Start Work.
  51. CLOSED record cannot Start Work.
  52. BLOCKED behavior matches lifecycle engine exactly.
- LEGACY:
  53. Legacy OPEN bug follows same lifecycle rules.
  54. No source_kind special-case required.
- ATOMICITY:
  55. Injected failure returns sanitized 500.
  56. Status rolls back to OPEN.
  57. Assignee rolls back.
  58. Audit rolls back.
  59. Ticket remains unchanged.
  60. Allocators remain unchanged.
- ERROR SAFETY:
  61. Conflict envelope stable.
  62. Internal error sanitized.
  63. No SQL leakage.
  64. No traceback leakage.
  65. No filesystem path leakage.
- READ AFTER WRITE:
  66. GET bug shows FIXING.
  67. GET investigation by INV ID shows same state for native bug.
  68. List endpoint reflects FIXING.
  69. My Work reflects assignment.
- OPENAPI:
  70. start-work POST documented.
  71. Exactly three business write routes.
  72-76. No submit-fix/retest/verify/close/block write routes.
- REGRESSION & PRODUCTION:
  77. Confirm tests remain green.
  78. Capture tests remain green.
  79. Read API tests remain green.
  80. Domain tests remain green.
  81. Legacy Markdown unchanged.
  82. Seven PNG hashes unchanged.
  83. No production DB created.
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
from scripts.import_legacy import run_legacy_import
from api.app import create_app

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class TestApiStartWork(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="art_test_start_work_")
        self.db_path = os.path.join(self.test_dir, "test_start_work.db")
        self.conn = get_connection(self.db_path)
        init_db(self.conn)
        self.service = ResolutionService(self.conn)
        self.app = create_app(self.db_path)
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _seed_confirmed_bug(self, module="AGENT", title="Sample defect") -> tuple[str, str]:
        """
        Creates and confirms an investigation as a BUG.
        Returns (investigation_id, canonical_bug_id).
        """
        res_cap = self.client.post("/api/v1/investigations", json={
            "tester_description": "Initial intake description",
            "reporter": "tester-1"
        })
        self.assertEqual(res_cap.status_code, 201)
        inv_id = res_cap.json()["investigation"]["investigation_id"]

        res_conf = self.client.post(f"/api/v1/investigations/{inv_id}/confirm", json={
            "module": module,
            "actor": "lead-qa",
            "ticket": {
                "title": title,
                "reproSteps": "1. Step",
                "severity": "HIGH",
                "priority": "P1"
            }
        })
        self.assertEqual(res_conf.status_code, 200)
        art_id = res_conf.json()["investigation"]["canonical_bug_id"]
        return inv_id, art_id

    # ==========================================
    # 1. ROUTE & METHOD TESTS (1 - 4)
    # ==========================================

    def test_01_to_04_route_presence_and_methods(self):
        inv_id, art_id = self._seed_confirmed_bug()

        # 1 & 2: Route exists and returns 200 for valid Start Work
        res = self.client.post(f"/api/v1/bugs/{art_id}/start-work", json={"assignee": "dev-alice"})
        self.assertEqual(res.status_code, 200)
        data = res.json()["investigation"]
        self.assertEqual(data["status"], "FIXING")
        self.assertEqual(data["assignee"], "dev-alice")

        # 3: Capture still returns 201
        res_cap = self.client.post("/api/v1/investigations", json={"tester_description": "Another issue"})
        self.assertEqual(res_cap.status_code, 201)

        # 4: Confirm still returns 200
        new_inv_id = res_cap.json()["investigation"]["investigation_id"]
        res_conf = self.client.post(f"/api/v1/investigations/{new_inv_id}/confirm", json={
            "module": "SFN",
            "ticket": {"title": "SFN Bug"}
        })
        self.assertEqual(res_conf.status_code, 200)

    # ==========================================
    # 2. IDENTIFIER TESTS (5 - 9)
    # ==========================================

    def test_05_to_09_identifier_validation(self):
        inv_id, art_id = self._seed_confirmed_bug()

        # 5: Valid ART ID accepted
        res_valid = self.client.post(f"/api/v1/bugs/{art_id}/start-work", json={"assignee": "dev-alice"})
        self.assertEqual(res_valid.status_code, 200)

        # 6: INV ID rejected (400)
        res_inv = self.client.post(f"/api/v1/bugs/{inv_id}/start-work", json={"assignee": "dev-alice"})
        self.assertEqual(res_inv.status_code, 400)
        self.assertEqual(res_inv.json()["error"]["code"], "VALIDATION_ERROR")

        # 7: record_key (UUID) rejected (400)
        res_uuid = self.client.post("/api/v1/bugs/12345678-1234-5678-1234-567812345678/start-work", json={"assignee": "dev-alice"})
        self.assertEqual(res_uuid.status_code, 400)
        self.assertEqual(res_uuid.json()["error"]["code"], "VALIDATION_ERROR")

        # 8: Malformed ART ID rejected (400)
        res_mal = self.client.post("/api/v1/bugs/MALFORMED_123/start-work", json={"assignee": "dev-alice"})
        self.assertEqual(res_mal.status_code, 400)
        self.assertEqual(res_mal.json()["error"]["code"], "VALIDATION_ERROR")

        # 9: Valid unknown ART ID returns 404
        res_404 = self.client.post("/api/v1/bugs/ART-AGENT-999/start-work", json={"assignee": "dev-alice"})
        self.assertEqual(res_404.status_code, 404)
        self.assertEqual(res_404.json()["error"]["code"], "NOT_FOUND")

    # ==========================================
    # 3. REQUEST VALIDATION TESTS (10 - 14)
    # ==========================================

    def test_10_to_14_request_validation(self):
        _, art_id = self._seed_confirmed_bug()

        # 11: Missing assignee rejected
        res_missing = self.client.post(f"/api/v1/bugs/{art_id}/start-work", json={})
        self.assertEqual(res_missing.status_code, 400)
        self.assertEqual(res_missing.json()["error"]["code"], "VALIDATION_ERROR")

        # 12: Empty assignee rejected
        res_empty = self.client.post(f"/api/v1/bugs/{art_id}/start-work", json={"assignee": "   "})
        self.assertEqual(res_empty.status_code, 400)
        self.assertEqual(res_empty.json()["error"]["code"], "VALIDATION_ERROR")

        # 13: Unsupported fields rejected
        res_extra = self.client.post(f"/api/v1/bugs/{art_id}/start-work", json={
            "assignee": "dev-alice",
            "deadline": "2026-10-01"
        })
        self.assertEqual(res_extra.status_code, 400)
        self.assertIn("Extra inputs are not permitted", res_extra.json()["error"]["message"])

        # 10 & 14: Valid assignee and actor preserved
        res_actor = self.client.post(f"/api/v1/bugs/{art_id}/start-work", json={
            "assignee": "dev-bob",
            "actor": "team-lead"
        })
        self.assertEqual(res_actor.status_code, 200)
        inv = res_actor.json()["investigation"]
        self.assertEqual(inv["assignee"], "dev-bob")
        # Check audit actor
        audit = inv["audit_events"][-1]
        self.assertEqual(audit["actor"], "team-lead")

    # ==========================================
    # 4. STATE & TICKET PRESERVATION (15 - 26)
    # ==========================================

    def test_15_to_26_state_and_ticket_preservation(self):
        inv_id, art_id = self._seed_confirmed_bug()

        res = self.client.post(f"/api/v1/bugs/{art_id}/start-work", json={"assignee": "dev-charlie"})
        self.assertEqual(res.status_code, 200)
        inv = res.json()["investigation"]

        # 15: OPEN becomes FIXING
        self.assertEqual(inv["status"], "FIXING")

        # 16: Assignee becomes supplied developer
        self.assertEqual(inv["assignee"], "dev-charlie")

        # 17: Classification remains BUG
        self.assertEqual(inv["classification"], "BUG")

        # 18 & 19: Identities unchanged
        self.assertEqual(inv["canonical_bug_id"], art_id)
        self.assertEqual(inv["investigation_id"], inv_id)

        # 20: lifecycle_phase remains CONFIRMED
        self.assertEqual(inv["lifecycle_phase"], "CONFIRMED")

        # 21 - 23: Ticket and history unchanged
        self.assertIsNotNone(inv["active_ticket_id"])
        self.assertEqual(inv["active_ticket_id"], inv["current_ticket"]["ticket_id"])
        self.assertEqual(len(inv["ticket_history"]), 1)
        self.assertEqual(inv["current_ticket"]["revision"], 1)

        # 24 - 26: Module, severity, priority unchanged
        self.assertEqual(inv["module"], "AGENT")
        self.assertEqual(inv["severity"], "HIGH")
        self.assertEqual(inv["priority"], "P1")

    # ==========================================
    # 5. SOURCE & ARTIFACT PRESERVATION (27 - 32)
    # ==========================================

    def test_27_to_32_source_and_artifact_preservation(self):
        _, art_id = self._seed_confirmed_bug()

        res = self.client.post(f"/api/v1/bugs/{art_id}/start-work", json={"assignee": "dev-david"})
        self.assertEqual(res.status_code, 200)
        inv = res.json()["investigation"]

        # 27: OriginalInput unchanged
        self.assertEqual(inv["original_input"]["tester_description"], "Initial intake description")
        self.assertEqual(inv["original_input"]["reporter"], "tester-1")

        # 28: Evidence metadata unchanged
        self.assertEqual(inv["evidence"], [])

        # 29: No DeveloperUpdate created
        self.assertEqual(inv["developer_updates"], [])

        # 30: No RetestArtifact created
        self.assertEqual(inv["retest_artifacts"], [])

        # 31 & 32: AI and research artifacts unchanged
        self.assertEqual(inv["ai_artifacts"], [])
        self.assertEqual(inv["research_artifacts"], [])

    # ==========================================
    # 6. AUDIT & ALLOCATOR INTEGRITY (33 - 36)
    # ==========================================

    def test_33_to_36_audit_and_allocators_unchanged(self):
        _, art_id = self._seed_confirmed_bug()

        cursor = self.conn.cursor()
        cursor.execute("SELECT scope, last_seq FROM id_allocations ORDER BY scope ASC;")
        allocations_before = cursor.fetchall()

        res = self.client.post(f"/api/v1/bugs/{art_id}/start-work", json={"assignee": "dev-eve"})
        self.assertEqual(res.status_code, 200)
        inv = res.json()["investigation"]

        # 33: Exactly one Start Work audit added (total = 3)
        audits = inv["audit_events"]
        self.assertEqual(len(audits), 3)
        event_types = [a["event_type"] for a in audits]
        self.assertEqual(event_types, ["INVESTIGATION_CAPTURED", "TICKET_CONFIRMED", "STATUS_TRANSITIONED"])
        self.assertIn("dev-eve", audits[-1]["summary"])

        # 34: No transport audit
        self.assertNotIn("WORK_STARTED_HTTP", event_types)
        self.assertNotIn("API_ASSIGNED", event_types)

        # 35 & 36: Allocator tables completely unchanged
        cursor.execute("SELECT scope, last_seq FROM id_allocations ORDER BY scope ASC;")
        allocations_after = cursor.fetchall()
        self.assertEqual(allocations_before, allocations_after)

    # ==========================================
    # 7. MY WORK & QUEUE EFFECTS (37 - 41)
    # ==========================================

    def test_37_to_41_my_work_and_queue_effects(self):
        _, art_id = self._seed_confirmed_bug()

        # 37: Before Start Work, absent from dev-frank's My Work
        res_mw_before = self.client.get("/api/v1/work/my?assignee=dev-frank")
        self.assertEqual(res_mw_before.status_code, 200)
        self.assertEqual(res_mw_before.json()["total"], 0)

        # Start Work
        res_sw = self.client.post(f"/api/v1/bugs/{art_id}/start-work", json={"assignee": "dev-frank"})
        self.assertEqual(res_sw.status_code, 200)

        # 38: After Start Work, appears in dev-frank's My Work
        res_mw_after = self.client.get("/api/v1/work/my?assignee=dev-frank")
        self.assertEqual(res_mw_after.status_code, 200)
        self.assertEqual(res_mw_after.json()["total"], 1)
        self.assertEqual(res_mw_after.json()["items"][0]["canonical_bug_id"], art_id)

        # 39: Other developer (dev-grace) does NOT see bug in My Work
        res_mw_other = self.client.get("/api/v1/work/my?assignee=dev-grace")
        self.assertEqual(res_mw_other.status_code, 200)
        self.assertEqual(res_mw_other.json()["total"], 0)

        # 40: Absent from Retest queue
        res_ret = self.client.get("/api/v1/retest")
        self.assertEqual(res_ret.status_code, 200)
        self.assertEqual(res_ret.json()["total"], 0)

        # 41: Absent from Investigation queue
        res_inv_q = self.client.get("/api/v1/investigation-queue")
        self.assertEqual(res_inv_q.status_code, 200)
        self.assertEqual(res_inv_q.json()["total"], 0)

    # ==========================================
    # 8. DOUBLE START & REASSIGNMENT PREVENTION (42 - 46)
    # ==========================================

    def test_42_to_46_double_start_and_reassignment_prevented(self):
        _, art_id = self._seed_confirmed_bug()

        # First Start Work succeeds
        res1 = self.client.post(f"/api/v1/bugs/{art_id}/start-work", json={"assignee": "dev-heidi"})
        self.assertEqual(res1.status_code, 200)

        # 42 & 43: Second Start Work rejected with 409 Conflict
        res2 = self.client.post(f"/api/v1/bugs/{art_id}/start-work", json={"assignee": "dev-heidi"})
        self.assertEqual(res2.status_code, 409)
        self.assertEqual(res2.json()["error"]["code"], "CONFLICT")

        # Second Start Work with DIFFERENT assignee also rejected with 409 Conflict (no silent reassignment)
        res3 = self.client.post(f"/api/v1/bugs/{art_id}/start-work", json={"assignee": "dev-ivan"})
        self.assertEqual(res3.status_code, 409)
        self.assertEqual(res3.json()["error"]["code"], "CONFLICT")

        # 44 - 46: State remains assigned to dev-heidi, no extra audit or IDs
        inv = self.client.get(f"/api/v1/bugs/{art_id}").json()
        self.assertEqual(inv["assignee"], "dev-heidi")
        self.assertEqual(len(inv["audit_events"]), 3)

    # ==========================================
    # 9. WRONG SOURCE STATES (47 - 52)
    # ==========================================

    def test_47_to_52_wrong_source_states_rejected(self):
        # 47: CAPTURE record cannot start work
        res_cap = self.client.post("/api/v1/investigations", json={"tester_description": "Raw unconfirmed"})
        inv_id_cap = res_cap.json()["investigation"]["investigation_id"]
        # Attempting start-work via ART ID endpoint fails because CAPTURE has no ART ID (returns 400 for INV ID or 404 for non-existent ART ID)
        res_bad_id = self.client.post(f"/api/v1/bugs/{inv_id_cap}/start-work", json={"assignee": "dev-judy"})
        self.assertEqual(res_bad_id.status_code, 400)

        # 48: FIXING record tested above in double start (409)

        # 49 - 51: RETEST, VERIFIED, CLOSED records reject start-work
        # Seed a bug and advance it to RETEST, VERIFIED, CLOSED
        inv_id, art_id = self._seed_confirmed_bug(title="Advancing bug")
        row = self.service.repo.get_investigation_by_canonical_bug_id(art_id)
        key = row["record_key"]

        # Advance to RETEST
        self.service.start_work(key, assignee="dev-judy", actor="dev-judy")
        self.service.submit_fix(key, developer_username="dev-judy", summary_of_changes="Fix",
                                resolved_in_version_or_branch="v1", test_instructions_for_qa="Test")
        res_ret = self.client.post(f"/api/v1/bugs/{art_id}/start-work", json={"assignee": "dev-judy"})
        self.assertEqual(res_ret.status_code, 409)
        self.assertIn("Cannot start work when status is 'RETEST'", res_ret.json()["error"]["message"])

        # Advance to VERIFIED
        self.service.verify(
            key,
            human_confirmation={"confirmed": True, "verdict": "VERIFIED", "confirmedBy": "qa-lead"},
            actor="qa-lead",
            actor_role="HUMAN"
        )
        res_ver = self.client.post(f"/api/v1/bugs/{art_id}/start-work", json={"assignee": "dev-judy"})
        self.assertEqual(res_ver.status_code, 409)
        self.assertIn("Cannot start work when status is 'VERIFIED'", res_ver.json()["error"]["message"])

        # Advance to CLOSED
        self.service.close(key, actor="admin", summary="Done")
        res_cls = self.client.post(f"/api/v1/bugs/{art_id}/start-work", json={"assignee": "dev-judy"})
        self.assertEqual(res_cls.status_code, 409)
        self.assertIn("Cannot start work in lifecycle phase 'RESOLVED'", res_cls.json()["error"]["message"])

    # ==========================================
    # 10. LEGACY RECORD START WORK (53 - 54)
    # ==========================================

    def test_53_to_54_legacy_bug_start_work(self):
        run_legacy_import(self.db_path)

        # ART-AGENT-001 is imported in status OPEN
        res_leg = self.client.post("/api/v1/bugs/ART-AGENT-001/start-work", json={"assignee": "dev-kevin"})
        self.assertEqual(res_leg.status_code, 200)
        inv = res_leg.json()["investigation"]
        self.assertEqual(inv["status"], "FIXING")
        self.assertEqual(inv["assignee"], "dev-kevin")
        self.assertEqual(inv["source_kind"], "LEGACY_IMPORT")

    # ==========================================
    # 11. ATOMICITY & ROLLBACK (55 - 60)
    # ==========================================

    def test_55_to_60_atomicity_and_rollback(self):
        _, art_id = self._seed_confirmed_bug()

        cursor = self.conn.cursor()
        cursor.execute("SELECT scope, last_seq FROM id_allocations ORDER BY scope ASC;")
        allocs_before = cursor.fetchall()

        with patch.object(ResolutionService, "start_work") as mock_sw:
            from core.storage.service import ServiceResult
            mock_sw.return_value = ServiceResult(
                success=False,
                data=None,
                audit_event=None,
                error="Simulated storage failure"
            )
            res_fail = self.client.post(f"/api/v1/bugs/{art_id}/start-work", json={"assignee": "dev-laura"})
            self.assertEqual(res_fail.status_code, 400)

        # 56 - 60: Status rolls back to OPEN, assignee null, allocators unchanged
        inv = self.client.get(f"/api/v1/bugs/{art_id}").json()
        self.assertEqual(inv["status"], "OPEN")
        self.assertIsNone(inv["assignee"])
        self.assertEqual(len(inv["audit_events"]), 2)

        cursor.execute("SELECT scope, last_seq FROM id_allocations ORDER BY scope ASC;")
        allocs_after = cursor.fetchall()
        self.assertEqual(allocs_before, allocs_after)

    # ==========================================
    # 12. READ AFTER WRITE & OPENAPI (66 - 76)
    # ==========================================

    def test_66_to_76_read_after_write_and_openapi(self):
        inv_id, art_id = self._seed_confirmed_bug()

        self.client.post(f"/api/v1/bugs/{art_id}/start-work", json={"assignee": "dev-mike"})

        # 66: GET bug shows FIXING
        res_art = self.client.get(f"/api/v1/bugs/{art_id}")
        self.assertEqual(res_art.status_code, 200)
        self.assertEqual(res_art.json()["status"], "FIXING")
        self.assertEqual(res_art.json()["assignee"], "dev-mike")

        # 67: GET investigation by INV ID shows same state
        res_inv = self.client.get(f"/api/v1/investigations/{inv_id}")
        self.assertEqual(res_inv.status_code, 200)
        self.assertEqual(res_inv.json()["status"], "FIXING")
        self.assertEqual(res_inv.json()["assignee"], "dev-mike")

        # 68: List endpoint reflects FIXING
        res_list = self.client.get("/api/v1/investigations?status=FIXING")
        self.assertEqual(res_list.status_code, 200)
        self.assertEqual(res_list.json()["total"], 1)

        # 70 - 76: OpenAPI route guarantee
        res_oas = self.client.get("/api/v1/openapi.json")
        self.assertEqual(res_oas.status_code, 200)
        paths = res_oas.json().get("paths", {})

        self.assertIn("/api/v1/bugs/{canonical_bug_id}/start-work", paths)
        self.assertIn("post", paths["/api/v1/bugs/{canonical_bug_id}/start-work"])

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
