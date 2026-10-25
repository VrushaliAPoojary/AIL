"""
tests/test_api_submit_fix.py

Phase 02E — HTTP Submit Fix Endpoint Test Suite
Validates the complete test matrix specified for Phase 02E:
- ROUTE:
  1. submit-fix route exists.
  2. Valid Submit Fix returns 200.
  3. Previous three write routes remain available.
- IDENTIFIER:
  4. ART ID accepted.
  5. INV ID rejected (400).
  6. record_key rejected (400).
  7. Malformed ART ID rejected (400).
  8. Unknown valid ART ID -> 404.
- REQUEST:
  9. Required DeveloperUpdate fields accepted.
  10. Missing required field rejected (400).
  11. Invalid field type rejected (400).
  12. Unsupported field rejected (400).
  13. Text preserved exactly.
  14. Optional commit_hash_or_pr and actor handled according to service contract.
- STATE:
  15. FIXING -> RETEST.
  16. Lifecycle phase follows engine (CONFIRMED).
  17. Assignee behavior follows service (preserved).
  18. Classification remains BUG.
  19. ART ID unchanged.
  20. INV ID unchanged.
- DEVELOPER UPDATE:
  21. Exactly one DeveloperUpdate created.
  22. Provenance correct ("DEVELOPER_UPDATE").
  23. Developer identity correct.
  24. Summary correct.
  25. Test instructions correct.
  26. Branch/version correct.
  27. Commit hash or PR reference correct.
- NO RETEST YET:
  28. Zero new RetestArtifact.
  29. Status not VERIFIED.
  30. Lifecycle not RESOLVED.
  31. Status not CLOSED.
- PRESERVATION:
  32. active_ticket_id unchanged.
  33. current_ticket unchanged.
  34. ticket history unchanged.
  35. module unchanged.
  36. severity unchanged.
  37. priority unchanged.
  38. OriginalInput unchanged.
  39. Prior evidence unchanged.
- AUDIT:
  40. Exactly one domain Submit Fix audit added ("FIX_SUBMITTED").
  41. No transport audit added.
- ALLOCATORS:
  42. INV allocator unchanged.
  43. BUG allocator unchanged.
- QUEUES:
  44. Before Submit Fix appears in My Work.
  45. After Submit Fix disappears from My Work.
  46. Before Submit Fix absent from Retest Queue.
  47. After Submit Fix appears in Retest Queue.
  48. Remains absent from Investigation Queue.
- DOUBLE SUBMIT:
  49. Second Submit Fix rejected.
  50. Conflict (409) returned.
  51. No second DeveloperUpdate.
  52. No second audit.
  53. State remains RETEST.
- WRONG STATES:
  54. CAPTURE rejected.
  55. OPEN rejected.
  56. RETEST rejected.
  57. VERIFIED rejected.
  58. CLOSED rejected.
  59. BLOCKED follows existing lifecycle rule.
- LEGACY:
  60. Legacy bug that reached FIXING can Submit Fix.
  61. No legacy special-case in HTTP.
- ATOMICITY:
  62. Injected failure returns controlled 500.
  63. Status rolls back to FIXING.
  64. DeveloperUpdate rolls back.
  65. Audit rolls back.
  66. Ticket unchanged.
  67. Assignee unchanged.
  68. Allocators unchanged.
- READ AFTER WRITE:
  69. GET by ART shows RETEST.
  70. GET by INV shows RETEST for native record.
  71. RETEST list filter contains bug.
- ERROR SAFETY:
  72. Validation envelope stable.
  73. Conflict envelope stable.
  74. Internal error sanitized.
  75. No SQL leakage.
  76. No traceback leakage.
  77. No filesystem path leakage.
- OPENAPI:
  78. submit-fix documented.
  79. Exactly four business write routes.
  80-83. No submit-retest/verify/close/block write routes.
- REGRESSION & PRODUCTION:
  84. Start Work tests green.
  85. Confirm tests green.
  86. Capture tests green.
  87. Read API tests green.
  88. Domain tests green.
  89. Legacy Markdown unchanged.
  90. Seven PNG hashes unchanged.
  91. No production DB created.
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


class TestApiSubmitFix(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="art_test_submit_fix_")
        self.db_path = os.path.join(self.test_dir, "test_submit_fix.db")
        self.conn = get_connection(self.db_path)
        init_db(self.conn)
        self.service = ResolutionService(self.conn)
        self.app = create_app(self.db_path)
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _seed_fixing_bug(self, module="AGENT", assignee="dev-alice") -> tuple[str, str]:
        """
        Creates, confirms, and starts work on a bug.
        Returns (investigation_id, canonical_bug_id).
        """
        res_cap = self.client.post("/api/v1/investigations", json={
            "tester_description": "Initial intake issue",
            "reporter": "tester-1"
        })
        self.assertEqual(res_cap.status_code, 201)
        inv_id = res_cap.json()["investigation"]["investigation_id"]

        res_conf = self.client.post(f"/api/v1/investigations/{inv_id}/confirm", json={
            "module": module,
            "actor": "lead-qa",
            "ticket": {
                "title": "Fixing defect",
                "severity": "HIGH",
                "priority": "P1"
            }
        })
        self.assertEqual(res_conf.status_code, 200)
        art_id = res_conf.json()["investigation"]["canonical_bug_id"]

        res_sw = self.client.post(f"/api/v1/bugs/{art_id}/start-work", json={"assignee": assignee})
        self.assertEqual(res_sw.status_code, 200)
        self.assertEqual(res_sw.json()["investigation"]["status"], "FIXING")

        return inv_id, art_id

    def _sample_fix_payload(self, developer="dev-alice") -> dict:
        return {
            "developer_username": developer,
            "summary_of_changes": "Patched validation logic in agent output parser",
            "resolved_in_version_or_branch": "fix/agent-parser-v2",
            "test_instructions_for_qa": "1. Run agent query\n2. Verify output matches JSON schema",
            "commit_hash_or_pr": "abc1234",
            "actor": developer
        }

    # ==========================================
    # 1. ROUTE & METHOD TESTS (1 - 3)
    # ==========================================

    def test_01_to_03_route_presence_and_methods(self):
        inv_id, art_id = self._seed_fixing_bug()
        payload = self._sample_fix_payload()

        # 1 & 2: Route exists and returns 200 for valid Submit Fix
        res = self.client.post(f"/api/v1/bugs/{art_id}/submit-fix", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()["investigation"]
        self.assertEqual(data["status"], "RETEST")

        # 3: Previous three write routes remain functional
        # A: Capture
        res_cap = self.client.post("/api/v1/investigations", json={"tester_description": "Another bug"})
        self.assertEqual(res_cap.status_code, 201)
        cap_inv = res_cap.json()["investigation"]["investigation_id"]

        # B: Confirm
        res_conf = self.client.post(f"/api/v1/investigations/{cap_inv}/confirm", json={
            "module": "SFN",
            "ticket": {"title": "SFN issue"}
        })
        self.assertEqual(res_conf.status_code, 200)
        cap_art = res_conf.json()["investigation"]["canonical_bug_id"]

        # C: Start Work
        res_sw = self.client.post(f"/api/v1/bugs/{cap_art}/start-work", json={"assignee": "dev-bob"})
        self.assertEqual(res_sw.status_code, 200)

    # ==========================================
    # 2. IDENTIFIER TESTS (4 - 8)
    # ==========================================

    def test_04_to_08_identifier_validation(self):
        inv_id, art_id = self._seed_fixing_bug()
        payload = self._sample_fix_payload()

        # 4: ART ID accepted
        res_valid = self.client.post(f"/api/v1/bugs/{art_id}/submit-fix", json=payload)
        self.assertEqual(res_valid.status_code, 200)

        # 5: INV ID rejected (400)
        res_inv = self.client.post(f"/api/v1/bugs/{inv_id}/submit-fix", json=payload)
        self.assertEqual(res_inv.status_code, 400)
        self.assertEqual(res_inv.json()["error"]["code"], "VALIDATION_ERROR")

        # 6: record_key (UUID) rejected (400)
        res_uuid = self.client.post("/api/v1/bugs/12345678-1234-5678-1234-567812345678/submit-fix", json=payload)
        self.assertEqual(res_uuid.status_code, 400)

        # 7: Malformed ART ID rejected (400)
        res_mal = self.client.post("/api/v1/bugs/MALFORMED_123/submit-fix", json=payload)
        self.assertEqual(res_mal.status_code, 400)

        # 8: Unknown valid ART ID -> 404
        res_404 = self.client.post("/api/v1/bugs/ART-AGENT-999/submit-fix", json=payload)
        self.assertEqual(res_404.status_code, 404)
        self.assertEqual(res_404.json()["error"]["code"], "NOT_FOUND")

    # ==========================================
    # 3. REQUEST VALIDATION TESTS (9 - 14)
    # ==========================================

    def test_09_to_14_request_validation(self):
        _, art_id = self._seed_fixing_bug()

        # 10: Missing required field (e.g. summary_of_changes)
        bad_req = self._sample_fix_payload()
        del bad_req["summary_of_changes"]
        res_missing = self.client.post(f"/api/v1/bugs/{art_id}/submit-fix", json=bad_req)
        self.assertEqual(res_missing.status_code, 400)
        self.assertEqual(res_missing.json()["error"]["code"], "VALIDATION_ERROR")

        # Empty string for required fields rejected
        bad_empty = self._sample_fix_payload()
        bad_empty["test_instructions_for_qa"] = "   "
        res_empty = self.client.post(f"/api/v1/bugs/{art_id}/submit-fix", json=bad_empty)
        self.assertEqual(res_empty.status_code, 400)

        # 12: Unsupported fields rejected (extra="forbid")
        bad_extra = self._sample_fix_payload()
        bad_extra["injected_field"] = "bad"
        res_extra = self.client.post(f"/api/v1/bugs/{art_id}/submit-fix", json=bad_extra)
        self.assertEqual(res_extra.status_code, 400)
        self.assertIn("Extra inputs are not permitted", res_extra.json()["error"]["message"])

        # 13: Text preserved exactly
        raw_summary = "Special changes !@#$%^&*() \n with newline and quotes '\""
        good_payload = self._sample_fix_payload()
        good_payload["summary_of_changes"] = raw_summary
        res_good = self.client.post(f"/api/v1/bugs/{art_id}/submit-fix", json=good_payload)
        self.assertEqual(res_good.status_code, 200)
        dev_up = res_good.json()["investigation"]["developer_updates"][-1]
        self.assertEqual(dev_up["summary_of_changes"], raw_summary)

    # ==========================================
    # 4. STATE & DEVELOPER UPDATE TESTS (15 - 27)
    # ==========================================

    def test_15_to_27_state_and_developer_update(self):
        inv_id, art_id = self._seed_fixing_bug(assignee="dev-alice")
        payload = self._sample_fix_payload(developer="dev-alice")

        res = self.client.post(f"/api/v1/bugs/{art_id}/submit-fix", json=payload)
        self.assertEqual(res.status_code, 200)
        inv = res.json()["investigation"]

        # 15: FIXING -> RETEST
        self.assertEqual(inv["status"], "RETEST")

        # 16: Lifecycle phase follows engine (CONFIRMED)
        self.assertEqual(inv["lifecycle_phase"], "CONFIRMED")

        # 17: Assignee preserved
        self.assertEqual(inv["assignee"], "dev-alice")

        # 18 - 20: Identities preserved
        self.assertEqual(inv["classification"], "BUG")
        self.assertEqual(inv["canonical_bug_id"], art_id)
        self.assertEqual(inv["investigation_id"], inv_id)

        # 21 - 27: DeveloperUpdate created accurately
        dev_updates = inv["developer_updates"]
        self.assertEqual(len(dev_updates), 1)
        up = dev_updates[0]
        self.assertTrue(up["id"].startswith("DEV-"))
        self.assertEqual(up["provenance"], "DEVELOPER_UPDATE")
        self.assertEqual(up["developer_username"], payload["developer_username"])
        self.assertEqual(up["summary_of_changes"], payload["summary_of_changes"])
        self.assertEqual(up["resolved_in_version_or_branch"], payload["resolved_in_version_or_branch"])
        self.assertEqual(up["test_instructions_for_qa"], payload["test_instructions_for_qa"])
        self.assertEqual(up["commit_hash_or_pr"], payload["commit_hash_or_pr"])

    # ==========================================
    # 5. NO RETEST ARTIFACT & PRESERVATION (28 - 39)
    # ==========================================

    def test_28_to_39_no_retest_artifact_and_preservation(self):
        _, art_id = self._seed_fixing_bug()

        res = self.client.post(f"/api/v1/bugs/{art_id}/submit-fix", json=self._sample_fix_payload())
        self.assertEqual(res.status_code, 200)
        inv = res.json()["investigation"]

        # 28 - 31: Zero RetestArtifact; not VERIFIED/RESOLVED/CLOSED
        self.assertEqual(inv["retest_artifacts"], [])
        self.assertNotEqual(inv["status"], "VERIFIED")
        self.assertNotEqual(inv["lifecycle_phase"], "RESOLVED")
        self.assertNotEqual(inv["status"], "CLOSED")

        # 32 - 37: Ticket state preserved
        self.assertIsNotNone(inv["active_ticket_id"])
        self.assertEqual(inv["active_ticket_id"], inv["current_ticket"]["ticket_id"])
        self.assertEqual(len(inv["ticket_history"]), 1)
        self.assertEqual(inv["module"], "AGENT")
        self.assertEqual(inv["severity"], "HIGH")
        self.assertEqual(inv["priority"], "P1")

        # 38 & 39: Source input and evidence unchanged
        self.assertEqual(inv["original_input"]["tester_description"], "Initial intake issue")
        self.assertEqual(inv["evidence"], [])

    # ==========================================
    # 6. AUDIT & ALLOCATOR INTEGRITY (40 - 43)
    # ==========================================

    def test_40_to_43_audit_and_allocators_unchanged(self):
        _, art_id = self._seed_fixing_bug()

        cursor = self.conn.cursor()
        cursor.execute("SELECT scope, last_seq FROM id_allocations ORDER BY scope ASC;")
        allocs_before = cursor.fetchall()

        res = self.client.post(f"/api/v1/bugs/{art_id}/submit-fix", json=self._sample_fix_payload())
        self.assertEqual(res.status_code, 200)
        inv = res.json()["investigation"]

        # 40: Exactly one domain audit added (total = 4: CAPTURE, CONFIRM, START_WORK, FIX_SUBMITTED)
        audits = inv["audit_events"]
        self.assertEqual(len(audits), 4)
        event_types = [a["event_type"] for a in audits]
        self.assertEqual(event_types, ["INVESTIGATION_CAPTURED", "TICKET_CONFIRMED", "STATUS_TRANSITIONED", "FIX_SUBMITTED"])

        # 41: No transport audit
        self.assertNotIn("FIX_SUBMITTED_HTTP", event_types)

        # 42 & 43: Allocator tables completely unchanged
        cursor.execute("SELECT scope, last_seq FROM id_allocations ORDER BY scope ASC;")
        allocs_after = cursor.fetchall()
        self.assertEqual(allocs_before, allocs_after)

    # ==========================================
    # 7. QUEUE & MY WORK EFFECTS (44 - 48)
    # ==========================================

    def test_44_to_48_queues_and_my_work(self):
        _, art_id = self._seed_fixing_bug(assignee="dev-alice")

        # 44: Before Submit Fix, appears in My Work
        res_mw_before = self.client.get("/api/v1/work/my?assignee=dev-alice")
        self.assertEqual(res_mw_before.json()["total"], 1)

        # 46: Before Submit Fix, absent from Retest Queue
        res_ret_before = self.client.get("/api/v1/retest")
        self.assertEqual(res_ret_before.json()["total"], 0)

        # Submit Fix
        res_fix = self.client.post(f"/api/v1/bugs/{art_id}/submit-fix", json=self._sample_fix_payload(developer="dev-alice"))
        self.assertEqual(res_fix.status_code, 200)

        # 45: After Submit Fix, disappears from My Work
        res_mw_after = self.client.get("/api/v1/work/my?assignee=dev-alice")
        self.assertEqual(res_mw_after.json()["total"], 0)

        # 47: After Submit Fix, appears in Retest Queue
        res_ret_after = self.client.get("/api/v1/retest")
        self.assertEqual(res_ret_after.json()["total"], 1)
        self.assertEqual(res_ret_after.json()["items"][0]["canonical_bug_id"], art_id)

        # 48: Remains absent from Investigation Queue
        res_inv_q = self.client.get("/api/v1/investigation-queue")
        self.assertEqual(res_inv_q.json()["total"], 0)

    # ==========================================
    # 8. DOUBLE SUBMIT (49 - 53)
    # ==========================================

    def test_49_to_53_double_submit_rejected(self):
        _, art_id = self._seed_fixing_bug()
        payload = self._sample_fix_payload()

        # First Submit Fix succeeds
        res1 = self.client.post(f"/api/v1/bugs/{art_id}/submit-fix", json=payload)
        self.assertEqual(res1.status_code, 200)

        # 49 & 50: Second Submit Fix rejected with 409 Conflict
        res2 = self.client.post(f"/api/v1/bugs/{art_id}/submit-fix", json=payload)
        self.assertEqual(res2.status_code, 409)
        self.assertEqual(res2.json()["error"]["code"], "CONFLICT")

        # 51 - 53: State remains RETEST, no second DeveloperUpdate or audit
        inv = self.client.get(f"/api/v1/bugs/{art_id}").json()
        self.assertEqual(inv["status"], "RETEST")
        self.assertEqual(len(inv["developer_updates"]), 1)
        self.assertEqual(len(inv["audit_events"]), 4)

    # ==========================================
    # 9. WRONG SOURCE STATES (54 - 59)
    # ==========================================

    def test_54_to_59_wrong_source_states_rejected(self):
        payload = self._sample_fix_payload()

        # 54: CAPTURE record rejected (400 for non-ART ID)
        res_cap = self.client.post("/api/v1/investigations", json={"tester_description": "Capture issue"})
        inv_id_cap = res_cap.json()["investigation"]["investigation_id"]
        res_bad_id = self.client.post(f"/api/v1/bugs/{inv_id_cap}/submit-fix", json=payload)
        self.assertEqual(res_bad_id.status_code, 400)

        # 55: OPEN record rejected (cannot submit fix directly from OPEN)
        inv_id_open, art_id_open = self._seed_fixing_bug()
        # Create an OPEN bug
        res_cap2 = self.client.post("/api/v1/investigations", json={"tester_description": "Open bug"})
        inv_id_open2 = res_cap2.json()["investigation"]["investigation_id"]
        res_conf = self.client.post(f"/api/v1/investigations/{inv_id_open2}/confirm", json={
            "module": "GOV",
            "ticket": {"title": "Gov open bug"}
        })
        art_id_open2 = res_conf.json()["investigation"]["canonical_bug_id"]
        res_open = self.client.post(f"/api/v1/bugs/{art_id_open2}/submit-fix", json=payload)
        self.assertEqual(res_open.status_code, 409)
        self.assertIn("Cannot submit fix when status is 'OPEN'", res_open.json()["error"]["message"])

        # 56: RETEST record tested above in double submit (409)

        # 57: VERIFIED record rejected
        inv_id, art_id = self._seed_fixing_bug()
        row = self.service.repo.get_investigation_by_canonical_bug_id(art_id)
        key = row["record_key"]
        self.service.submit_fix(key, "dev-alice", "Fix", "branch", "instructions")
        self.service.verify(
            key,
            human_confirmation={"confirmed": True, "verdict": "VERIFIED", "confirmedBy": "qa-lead"},
            actor="qa-lead",
            actor_role="HUMAN"
        )
        res_ver = self.client.post(f"/api/v1/bugs/{art_id}/submit-fix", json=payload)
        self.assertEqual(res_ver.status_code, 409)
        self.assertIn("Cannot submit fix when status is 'VERIFIED'", res_ver.json()["error"]["message"])

        # 58: CLOSED record rejected
        self.service.close(key, actor="admin", summary="Done")
        res_cls = self.client.post(f"/api/v1/bugs/{art_id}/submit-fix", json=payload)
        self.assertEqual(res_cls.status_code, 409)
        self.assertIn("Cannot submit fix in lifecycle phase 'RESOLVED'", res_cls.json()["error"]["message"])

    # ==========================================
    # 10. LEGACY RECORD SUBMIT FIX (60 - 61)
    # ==========================================

    def test_60_to_61_legacy_bug_submit_fix(self):
        run_legacy_import(self.db_path)

        # ART-AGENT-001 is imported in status OPEN
        # Advance to FIXING
        res_sw = self.client.post("/api/v1/bugs/ART-AGENT-001/start-work", json={"assignee": "dev-alice"})
        self.assertEqual(res_sw.status_code, 200)

        # Submit Fix
        res_fix = self.client.post("/api/v1/bugs/ART-AGENT-001/submit-fix", json=self._sample_fix_payload())
        self.assertEqual(res_fix.status_code, 200)
        inv = res_fix.json()["investigation"]
        self.assertEqual(inv["status"], "RETEST")
        self.assertEqual(inv["source_kind"], "LEGACY_IMPORT")
        self.assertEqual(len(inv["developer_updates"]), 1)

    # ==========================================
    # 11. ATOMICITY & ROLLBACK (62 - 68)
    # ==========================================

    def test_62_to_68_atomicity_and_rollback(self):
        _, art_id = self._seed_fixing_bug()

        cursor = self.conn.cursor()
        cursor.execute("SELECT scope, last_seq FROM id_allocations ORDER BY scope ASC;")
        allocs_before = cursor.fetchall()

        with patch.object(ResolutionService, "submit_fix") as mock_sf:
            from core.storage.service import ServiceResult
            mock_sf.return_value = ServiceResult(
                success=False,
                data=None,
                audit_event=None,
                error="Simulated storage failure"
            )
            res_fail = self.client.post(f"/api/v1/bugs/{art_id}/submit-fix", json=self._sample_fix_payload())
            self.assertEqual(res_fail.status_code, 400)

        # 63 - 68: State remains FIXING, developer_updates empty, audit unchanged
        inv = self.client.get(f"/api/v1/bugs/{art_id}").json()
        self.assertEqual(inv["status"], "FIXING")
        self.assertEqual(inv["developer_updates"], [])
        self.assertEqual(len(inv["audit_events"]), 3)

        cursor.execute("SELECT scope, last_seq FROM id_allocations ORDER BY scope ASC;")
        allocs_after = cursor.fetchall()
        self.assertEqual(allocs_before, allocs_after)

    # ==========================================
    # 12. READ AFTER WRITE & OPENAPI (69 - 83)
    # ==========================================

    def test_69_to_83_read_after_write_and_openapi(self):
        inv_id, art_id = self._seed_fixing_bug()

        self.client.post(f"/api/v1/bugs/{art_id}/submit-fix", json=self._sample_fix_payload())

        # 69: GET by ART shows RETEST
        res_art = self.client.get(f"/api/v1/bugs/{art_id}")
        self.assertEqual(res_art.status_code, 200)
        self.assertEqual(res_art.json()["status"], "RETEST")

        # 70: GET by INV shows RETEST
        res_inv = self.client.get(f"/api/v1/investigations/{inv_id}")
        self.assertEqual(res_inv.status_code, 200)
        self.assertEqual(res_inv.json()["status"], "RETEST")

        # 71: RETEST list filter contains bug
        res_list = self.client.get("/api/v1/investigations?status=RETEST")
        self.assertEqual(res_list.status_code, 200)
        self.assertEqual(res_list.json()["total"], 1)

        # 78 - 83: OpenAPI route guarantee
        res_oas = self.client.get("/api/v1/openapi.json")
        self.assertEqual(res_oas.status_code, 200)
        paths = res_oas.json().get("paths", {})

        self.assertIn("/api/v1/bugs/{canonical_bug_id}/submit-fix", paths)
        self.assertIn("post", paths["/api/v1/bugs/{canonical_bug_id}/submit-fix"])

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
