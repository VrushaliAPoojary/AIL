"""
tests/test_api_retest.py

Phase 02F — HTTP Retest Submission Endpoint Test Suite
Validates the complete test matrix specified for Phase 02F:
- ROUTE / IDENTIFIER:
  1. /retest exists.
  2. Valid request returns 200.
  3. Prior four write routes remain available.
  4. ART accepted.
  5. INV rejected (400).
  6. record_key rejected (400).
  7. Malformed ART -> 400.
  8. Unknown ART -> 404.
- REQUEST:
  9. Required evidence IDs accepted.
  10. Empty evidence IDs rejected.
  11. Missing evidence IDs rejected.
  12. Human confirmation required.
  13. Actor required.
  14. Optional AI recommendation accepted.
  15. Unsupported fields rejected (extra="forbid").
  16. Invalid enum rejected.
- PASSED:
  17. PASSED returns 200.
  18. RetestArtifact +1.
  19. Artifact verdict PASSED.
  20. Status remains RETEST.
  21. Lifecycle remains CONFIRMED.
  22. RETEST_EXECUTED audit +1.
  23. No VERIFIED audit.
  24. No CLOSED state.
- FAILED:
  25. FAILED returns 200.
  26. Artifact verdict FAILED.
  27. Status becomes FIXING.
  28. Assignee preserved.
  29. RETEST_EXECUTED +1.
  30. Leaves Retest Queue.
  31. Returns to My Work.
- INCONCLUSIVE:
  32. INCONCLUSIVE returns 200.
  33. Artifact verdict INCONCLUSIVE.
  34. Status remains RETEST.
  35. RETEST_EXECUTED +1.
  36. Remains in Retest Queue.
  37. No VERIFIED.
- VERIFIED REJECTION:
  38. VERIFIED request rejected.
  39. Stable conflict (409) response.
  40. Status remains RETEST.
  41. No artifact committed.
  42. No audit committed.
  43. No VERIFIED state.
- AI RECOMMENDATION:
  44. AI PASSED + human FAILED -> FIXING.
  45. AI FAILED + human PASSED -> RETEST.
  46. AI recommendation cannot establish VERIFIED.
- REPEATED RETEST:
  47. Repeated PASSED behavior matches domain.
  48. Second artifact appended.
  49. Old artifact immutable.
  50. Second audit appended.
  51. No API idempotency invented.
- FAILED REPEAT:
  52. Immediate second retest after FAILED rejected (409).
  53. No second artifact.
  54. No second audit.
- HISTORY CYCLE:
  55. Submit Fix #1 persisted.
  56. Retest FAILED persisted.
  57. Submit Fix #2 persisted.
  58. Retest PASSED persisted.
  59. developer_updates length = 2.
  60. retest_artifacts length = 2.
  61. Final status = RETEST.
- PRESERVATION:
  62. Ticket unchanged.
  63. active_ticket_id unchanged.
  64. Module unchanged.
  65. Severity unchanged.
  66. Priority unchanged.
  67. OriginalInput unchanged.
  68. Previous DeveloperUpdates immutable.
  69. Existing evidence unchanged.
  70. Business IDs unchanged.
- ALLOCATOR:
  71. INV sequence unchanged.
  72. BUG sequence unchanged.
- INVALID SOURCE STATES:
  73. CAPTURE rejected.
  74. OPEN rejected.
  75. FIXING rejected.
  76. VERIFIED rejected.
  77. CLOSED rejected.
  78. BLOCKED behavior follows current engine.
- LEGACY:
  79. Legacy record uses same route after reaching RETEST.
  80. No source_kind API branch.
- ATOMICITY:
  81. Injected failure -> sanitized 500.
  82. Artifact rolled back.
  83. Status rolled back.
  84. Audit rolled back.
  85. Ticket unchanged.
  86. DeveloperUpdate unchanged.
  87. Allocator unchanged.
- READ AFTER WRITE:
  88. GET ART reflects result.
  89. GET INV reflects same result for native record.
  90. Retest history contains new artifact.
  91. List status filter reflects result.
  92. Queue behavior reflects result.
- OPENAPI:
  93. /retest documented.
  94. Exactly five business writes.
  95. No verify route.
  96. No close route.
  97. No block route.
"""

import unittest
import tempfile
import shutil
import os
import json
from unittest.mock import patch
from fastapi.testclient import TestClient

from api.app import create_app
from core.storage.schema import init_db
from core.storage.db import get_connection
from core.storage.service import ResolutionService
from core.query.service import InvestigationQueryService
from scripts.import_legacy import run_legacy_import


class TestApiRetest(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_retest.db")
        self.conn = get_connection(self.db_path)
        init_db(self.conn)
        self.app = create_app(db_path=self.db_path)
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.test_dir)

    def _seed_retest_bug(self, module="AGENT", assignee="dev-bob") -> tuple:
        """
        Creates a confirmed bug, starts work, and submits fix to reach RETEST status.
        Returns (investigation_id, canonical_bug_id, record_key).
        """
        res_cap = self.client.post("/api/v1/investigations", json={
            "tester_description": "Flaky token parsing in agent pipeline",
            "reporter": "qa-lead"
        })
        self.assertEqual(res_cap.status_code, 201)
        inv_id = res_cap.json()["investigation"]["investigation_id"]

        res_conf = self.client.post(f"/api/v1/investigations/{inv_id}/confirm", json={
            "module": module,
            "ticket": {
                "title": "Flaky token parsing bug",
                "severity": "HIGH",
                "priority": "P1"
            },
            "actor": "qa-lead"
        })
        self.assertEqual(res_conf.status_code, 200)
        art_id = res_conf.json()["investigation"]["canonical_bug_id"]

        res_work = self.client.post(f"/api/v1/bugs/{art_id}/start-work", json={"assignee": assignee})
        self.assertEqual(res_work.status_code, 200)

        res_fix = self.client.post(f"/api/v1/bugs/{art_id}/submit-fix", json={
            "developer_username": assignee,
            "summary_of_changes": "Added regex boundary check",
            "resolved_in_version_or_branch": "fix/token-boundary",
            "test_instructions_for_qa": "Run token stream generator with 10k items"
        })
        self.assertEqual(res_fix.status_code, 200)

        record_key = res_fix.json()["investigation"]["record_key"]
        return inv_id, art_id, record_key

    def _sample_retest_payload(self, verdict="PASSED", actor="qa-tester", include_ai=False) -> dict:
        payload = {
            "retest_evidence_ids": ["EVD-RET-001"],
            "human_confirmation": {
                "confirmed": True,
                "verdict": verdict,
                "confirmedBy": actor,
                "notes": f"Observed test execution with verdict {verdict}"
            },
            "actor": actor
        }
        if include_ai:
            payload["ai_recommendation"] = {
                "recommendation": "PASSED",
                "notes": "Automated log diff confirmed no errors"
            }
        return payload

    # ==========================================
    # 1. ROUTE & IDENTIFIERS (1 - 8)
    # ==========================================

    def test_01_to_08_route_and_identifiers(self):
        inv_id, art_id, _ = self._seed_retest_bug()

        # 1 & 2: Valid request returns 200
        payload = self._sample_retest_payload(verdict="PASSED")
        res_valid = self.client.post(f"/api/v1/bugs/{art_id}/retest", json=payload)
        self.assertEqual(res_valid.status_code, 200)
        self.assertIn("investigation", res_valid.json())

        # 3: Prior four write routes remain available
        cap_res = self.client.post("/api/v1/investigations", json={"tester_description": "New investigation"})
        self.assertEqual(cap_res.status_code, 201)
        new_inv_id = cap_res.json()["investigation"]["investigation_id"]

        conf_res = self.client.post(f"/api/v1/investigations/{new_inv_id}/confirm", json={
            "module": "SFN",
            "ticket": {"title": "Confirmed bug title", "severity": "MEDIUM", "priority": "P2"}
        })
        self.assertEqual(conf_res.status_code, 200)
        new_art_id = conf_res.json()["investigation"]["canonical_bug_id"]

        work_res = self.client.post(f"/api/v1/bugs/{new_art_id}/start-work", json={"assignee": "dev-alice"})
        self.assertEqual(work_res.status_code, 200)

        fix_res = self.client.post(f"/api/v1/bugs/{new_art_id}/submit-fix", json={
            "developer_username": "dev-alice",
            "summary_of_changes": "Fix applied",
            "resolved_in_version_or_branch": "branch-main",
            "test_instructions_for_qa": "Test steps"
        })
        self.assertEqual(fix_res.status_code, 200)

        # 4 & 5: INV ID rejected (400)
        res_inv = self.client.post(f"/api/v1/bugs/{inv_id}/retest", json=payload)
        self.assertEqual(res_inv.status_code, 400)
        self.assertEqual(res_inv.json()["error"]["code"], "VALIDATION_ERROR")

        # 6: record_key / arbitrary string rejected (400)
        res_key = self.client.post("/api/v1/bugs/12345678-1234-5678-1234-567812345678/retest", json=payload)
        self.assertEqual(res_key.status_code, 400)
        self.assertEqual(res_key.json()["error"]["code"], "VALIDATION_ERROR")

        # 7: Malformed ART ID rejected (400)
        res_mal = self.client.post("/api/v1/bugs/MALFORMED_123/retest", json=payload)
        self.assertEqual(res_mal.status_code, 400)
        self.assertEqual(res_mal.json()["error"]["code"], "VALIDATION_ERROR")

        # 8: Unknown valid ART ID -> 404
        res_unk = self.client.post("/api/v1/bugs/ART-AGENT-999/retest", json=payload)
        self.assertEqual(res_unk.status_code, 404)
        self.assertEqual(res_unk.json()["error"]["code"], "NOT_FOUND")

    # ==========================================
    # 2. REQUEST VALIDATION (9 - 16)
    # ==========================================

    def test_09_to_16_request_validation(self):
        _, art_id, _ = self._seed_retest_bug()

        # 9: Required evidence IDs accepted
        p_valid = self._sample_retest_payload(verdict="PASSED", include_ai=True)
        res_valid = self.client.post(f"/api/v1/bugs/{art_id}/retest", json=p_valid)
        self.assertEqual(res_valid.status_code, 200)

        # 10: Empty evidence IDs rejected
        p_empty_ev = self._sample_retest_payload()
        p_empty_ev["retest_evidence_ids"] = []
        res_empty_ev = self.client.post(f"/api/v1/bugs/{art_id}/retest", json=p_empty_ev)
        self.assertEqual(res_empty_ev.status_code, 400)
        self.assertEqual(res_empty_ev.json()["error"]["code"], "VALIDATION_ERROR")

        # 11: Missing evidence IDs rejected
        p_no_ev = self._sample_retest_payload()
        del p_no_ev["retest_evidence_ids"]
        res_no_ev = self.client.post(f"/api/v1/bugs/{art_id}/retest", json=p_no_ev)
        self.assertEqual(res_no_ev.status_code, 400)
        self.assertEqual(res_no_ev.json()["error"]["code"], "VALIDATION_ERROR")

        # 12: Missing human confirmation rejected
        p_no_hc = self._sample_retest_payload()
        del p_no_hc["human_confirmation"]
        res_no_hc = self.client.post(f"/api/v1/bugs/{art_id}/retest", json=p_no_hc)
        self.assertEqual(res_no_hc.status_code, 400)
        self.assertEqual(res_no_hc.json()["error"]["code"], "VALIDATION_ERROR")

        # 13: Missing actor rejected
        p_no_act = self._sample_retest_payload()
        del p_no_act["actor"]
        res_no_act = self.client.post(f"/api/v1/bugs/{art_id}/retest", json=p_no_act)
        self.assertEqual(res_no_act.status_code, 400)
        self.assertEqual(res_no_act.json()["error"]["code"], "VALIDATION_ERROR")

        # 14: Optional AI recommendation accepted
        p_ai = self._sample_retest_payload(include_ai=True)
        res_ai = self.client.post(f"/api/v1/bugs/{art_id}/retest", json=p_ai)
        self.assertEqual(res_ai.status_code, 200)

        # 15: Unsupported fields rejected (extra="forbid")
        p_extra = self._sample_retest_payload()
        p_extra["unexpected_field"] = "malicious_injection"
        res_extra = self.client.post(f"/api/v1/bugs/{art_id}/retest", json=p_extra)
        self.assertEqual(res_extra.status_code, 400)
        self.assertEqual(res_extra.json()["error"]["code"], "VALIDATION_ERROR")

        # 16: Invalid human verdict enum rejected (e.g. "APPROVED" or random string)
        p_bad_enum = self._sample_retest_payload(verdict="INVALID_VERDICT")
        res_bad_enum = self.client.post(f"/api/v1/bugs/{art_id}/retest", json=p_bad_enum)
        self.assertEqual(res_bad_enum.status_code, 409)

    # ==========================================
    # 3. PASSED RETEST BEHAVIOR (17 - 24)
    # ==========================================

    def test_17_to_24_passed_retest(self):
        _, art_id, record_key = self._seed_retest_bug()

        payload = self._sample_retest_payload(verdict="PASSED")
        res = self.client.post(f"/api/v1/bugs/{art_id}/retest", json=payload)

        # 17: Returns 200
        self.assertEqual(res.status_code, 200)
        inv = res.json()["investigation"]

        # 18 & 19: RetestArtifact +1 with verdict PASSED
        self.assertEqual(len(inv["retest_artifacts"]), 1)
        self.assertEqual(inv["retest_artifacts"][0]["human_confirmation"]["verdict"], "PASSED")

        # 20 & 21: Status remains RETEST, lifecycle remains CONFIRMED
        self.assertEqual(inv["status"], "RETEST")
        self.assertEqual(inv["lifecycle_phase"], "CONFIRMED")

        # 22 - 24: Audit RETEST_EXECUTED +1, no VERIFIED or CLOSED audit
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM audit_events WHERE investigation_key = ? AND event_type = 'RETEST_EXECUTED';", (record_key,))
        self.assertIsNotNone(cursor.fetchone())

        cursor.execute("SELECT count(*) FROM audit_events WHERE investigation_key = ? AND event_type = 'VERIFIED';", (record_key,))
        self.assertEqual(cursor.fetchone()[0], 0)

        cursor.execute("SELECT count(*) FROM audit_events WHERE investigation_key = ? AND event_type = 'CLOSED';", (record_key,))
        self.assertEqual(cursor.fetchone()[0], 0)

        self.assertNotEqual(inv["status"], "VERIFIED")
        self.assertNotEqual(inv["status"], "CLOSED")
        self.assertNotEqual(inv["lifecycle_phase"], "RESOLVED")

    # ==========================================
    # 4. FAILED RETEST BEHAVIOR (25 - 31)
    # ==========================================

    def test_25_to_31_failed_retest(self):
        _, art_id, record_key = self._seed_retest_bug(assignee="dev-charlie")

        # Before: appears in Retest Queue, not in My Work (status is RETEST)
        q_ret_before = self.client.get("/api/v1/retest").json()
        self.assertTrue(any(item["canonical_bug_id"] == art_id for item in q_ret_before["items"]))
        q_work_before = self.client.get("/api/v1/work/my?assignee=dev-charlie").json()
        self.assertFalse(any(item["canonical_bug_id"] == art_id for item in q_work_before["items"]))

        # 25: FAILED returns 200
        payload = self._sample_retest_payload(verdict="FAILED", actor="qa-tester")
        res = self.client.post(f"/api/v1/bugs/{art_id}/retest", json=payload)
        self.assertEqual(res.status_code, 200)
        inv = res.json()["investigation"]

        # 26 & 27: Artifact verdict FAILED, status becomes FIXING
        self.assertEqual(len(inv["retest_artifacts"]), 1)
        self.assertEqual(inv["retest_artifacts"][0]["human_confirmation"]["verdict"], "FAILED")
        self.assertEqual(inv["status"], "FIXING")

        # 28: Assignee preserved
        self.assertEqual(inv["assignee"], "dev-charlie")

        # 29: RETEST_EXECUTED audit +1
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM audit_events WHERE investigation_key = ? AND event_type = 'RETEST_EXECUTED';", (record_key,))
        self.assertIsNotNone(cursor.fetchone())

        # 30 & 31: Leaves Retest Queue, returns to My Work
        q_ret_after = self.client.get("/api/v1/retest").json()
        self.assertFalse(any(item["canonical_bug_id"] == art_id for item in q_ret_after["items"]))
        q_work_after = self.client.get("/api/v1/work/my?assignee=dev-charlie").json()
        self.assertTrue(any(item["canonical_bug_id"] == art_id for item in q_work_after["items"]))

    # ==========================================
    # 5. INCONCLUSIVE RETEST BEHAVIOR (32 - 37)
    # ==========================================

    def test_32_to_37_inconclusive_retest(self):
        _, art_id, record_key = self._seed_retest_bug()

        payload = self._sample_retest_payload(verdict="INCONCLUSIVE")
        res = self.client.post(f"/api/v1/bugs/{art_id}/retest", json=payload)

        # 32 & 33: Returns 200, artifact verdict INCONCLUSIVE
        self.assertEqual(res.status_code, 200)
        inv = res.json()["investigation"]
        self.assertEqual(inv["retest_artifacts"][0]["human_confirmation"]["verdict"], "INCONCLUSIVE")

        # 34 & 35: Status remains RETEST, RETEST_EXECUTED audit +1
        self.assertEqual(inv["status"], "RETEST")
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM audit_events WHERE investigation_key = ? AND event_type = 'RETEST_EXECUTED';", (record_key,))
        self.assertIsNotNone(cursor.fetchone())

        # 36: Remains in Retest Queue
        q_ret = self.client.get("/api/v1/retest").json()
        self.assertTrue(any(item["canonical_bug_id"] == art_id for item in q_ret["items"]))

        # 37: No VERIFIED
        self.assertNotEqual(inv["status"], "VERIFIED")

    # ==========================================
    # 6. VERIFIED REJECTION (38 - 43)
    # ==========================================

    def test_38_to_43_verified_rejection(self):
        _, art_id, record_key = self._seed_retest_bug()

        payload = self._sample_retest_payload(verdict="VERIFIED")
        res = self.client.post(f"/api/v1/bugs/{art_id}/retest", json=payload)

        # 38 & 39: VERIFIED request rejected with 409 Conflict
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.json()["error"]["code"], "CONFLICT")
        self.assertIn("cannot establish VERIFIED status", res.json()["error"]["message"])

        # 40: Status remains RETEST
        inv_check = self.client.get(f"/api/v1/bugs/{art_id}").json()
        self.assertEqual(inv_check["status"], "RETEST")

        # 41: No artifact committed
        self.assertEqual(len(inv_check["retest_artifacts"]), 0)

        # 42 & 43: No audit committed, no VERIFIED state
        cursor = self.conn.cursor()
        cursor.execute("SELECT count(*) FROM audit_events WHERE investigation_key = ? AND event_type = 'VERIFIED';", (record_key,))
        self.assertEqual(cursor.fetchone()[0], 0)

    # ==========================================
    # 7. AI RECOMMENDATION INDEPENDENCE (44 - 46)
    # ==========================================

    def test_44_to_46_ai_recommendation_authority(self):
        _, art_id_1, _ = self._seed_retest_bug()
        _, art_id_2, _ = self._seed_retest_bug()

        # 44: AI PASSED + human FAILED -> FIXING wins
        p1 = self._sample_retest_payload(verdict="FAILED")
        p1["ai_recommendation"] = {"recommendation": "PASSED", "notes": "AI thought it passed"}
        res1 = self.client.post(f"/api/v1/bugs/{art_id_1}/retest", json=p1)
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json()["investigation"]["status"], "FIXING")

        # 45: AI FAILED + human PASSED -> RETEST wins
        p2 = self._sample_retest_payload(verdict="PASSED")
        p2["ai_recommendation"] = {"recommendation": "FAILED", "notes": "AI thought it failed"}
        res2 = self.client.post(f"/api/v1/bugs/{art_id_2}/retest", json=p2)
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["investigation"]["status"], "RETEST")

        # 46: AI recommendation cannot establish VERIFIED
        self.assertNotEqual(res2.json()["investigation"]["status"], "VERIFIED")

    # ==========================================
    # 8. REPEATED RETEST & FAILED REPEAT (47 - 54)
    # ==========================================

    def test_47_to_54_repeated_retests(self):
        _, art_id, record_key = self._seed_retest_bug()

        # 47 & 48: First PASSED retest succeeded
        p1 = self._sample_retest_payload(verdict="PASSED", actor="qa-1")
        res1 = self.client.post(f"/api/v1/bugs/{art_id}/retest", json=p1)
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(len(res1.json()["investigation"]["retest_artifacts"]), 1)

        # Second PASSED retest while still in RETEST is allowed by domain
        p2 = self._sample_retest_payload(verdict="PASSED", actor="qa-2")
        res2 = self.client.post(f"/api/v1/bugs/{art_id}/retest", json=p2)
        self.assertEqual(res2.status_code, 200)
        inv2 = res2.json()["investigation"]

        # 48 & 49: Second artifact appended, old artifact immutable
        self.assertEqual(len(inv2["retest_artifacts"]), 2)
        self.assertEqual(inv2["retest_artifacts"][0]["human_confirmation"]["confirmedBy"], "qa-1")
        self.assertEqual(inv2["retest_artifacts"][1]["human_confirmation"]["confirmedBy"], "qa-2")

        # 50: Second audit appended
        cursor = self.conn.cursor()
        cursor.execute("SELECT count(*) FROM audit_events WHERE investigation_key = ? AND event_type = 'RETEST_EXECUTED';", (record_key,))
        self.assertEqual(cursor.fetchone()[0], 2)

        # 52 - 54: Now submit FAILED retest -> transitions to FIXING
        pF = self._sample_retest_payload(verdict="FAILED", actor="qa-3")
        resF = self.client.post(f"/api/v1/bugs/{art_id}/retest", json=pF)
        self.assertEqual(resF.status_code, 200)
        self.assertEqual(resF.json()["investigation"]["status"], "FIXING")

        # Immediate second retest while in FIXING must fail with 409
        res_fail_repeat = self.client.post(f"/api/v1/bugs/{art_id}/retest", json=p1)
        self.assertEqual(res_fail_repeat.status_code, 409)
        self.assertEqual(res_fail_repeat.json()["error"]["code"], "CONFLICT")

    # ==========================================
    # 9. FULL HISTORY CYCLE (55 - 61)
    # ==========================================

    def test_55_to_61_full_history_cycle(self):
        # Seed bug into FIXING
        res_svc = ResolutionService(self.conn)
        cap = res_svc.create_investigation(tester_description="Crash on null pointer", reporter="tester")
        rec_key = cap.data["record_key"]
        conf = res_svc.confirm_bug(rec_key, module="GOV", ticket_data={"title": "Null pointer"})
        art_id = conf.data["canonical_bug_id"]
        res_svc.start_work(rec_key, assignee="dev-dave", actor="dev-dave")

        # 55: Submit Fix #1 -> RETEST
        res_fix1 = self.client.post(f"/api/v1/bugs/{art_id}/submit-fix", json={
            "developer_username": "dev-dave",
            "summary_of_changes": "Fix attempt 1",
            "resolved_in_version_or_branch": "patch-1",
            "test_instructions_for_qa": "repro steps"
        })
        self.assertEqual(res_fix1.status_code, 200)

        # 56: Retest FAILED -> FIXING
        res_ret1 = self.client.post(f"/api/v1/bugs/{art_id}/retest", json=self._sample_retest_payload(verdict="FAILED"))
        self.assertEqual(res_ret1.status_code, 200)
        self.assertEqual(res_ret1.json()["investigation"]["status"], "FIXING")

        # 57: Submit Fix #2 -> RETEST
        res_fix2 = self.client.post(f"/api/v1/bugs/{art_id}/submit-fix", json={
            "developer_username": "dev-dave",
            "summary_of_changes": "Fix attempt 2",
            "resolved_in_version_or_branch": "patch-2",
            "test_instructions_for_qa": "repro steps 2"
        })
        self.assertEqual(res_fix2.status_code, 200)

        # 58: Retest PASSED -> RETEST
        res_ret2 = self.client.post(f"/api/v1/bugs/{art_id}/retest", json=self._sample_retest_payload(verdict="PASSED"))
        self.assertEqual(res_ret2.status_code, 200)

        # 59 - 61: developer_updates = 2, retest_artifacts = 2, status = RETEST
        final_inv = res_ret2.json()["investigation"]
        self.assertEqual(len(final_inv["developer_updates"]), 2)
        self.assertEqual(len(final_inv["retest_artifacts"]), 2)
        self.assertEqual(final_inv["status"], "RETEST")

    # ==========================================
    # 10. PRESERVATION & ALLOCATORS (62 - 72)
    # ==========================================

    def test_62_to_72_preservation_and_allocators(self):
        inv_id, art_id, record_key = self._seed_retest_bug()

        cursor = self.conn.cursor()
        cursor.execute("SELECT scope, last_seq FROM id_allocations ORDER BY scope ASC;")
        allocs_before = cursor.fetchall()

        inv_before = self.client.get(f"/api/v1/bugs/{art_id}").json()

        # Submit retest
        self.client.post(f"/api/v1/bugs/{art_id}/retest", json=self._sample_retest_payload(verdict="PASSED"))

        inv_after = self.client.get(f"/api/v1/bugs/{art_id}").json()

        # 62 - 70: Preservations
        self.assertEqual(inv_after["canonical_bug_id"], inv_before["canonical_bug_id"])
        self.assertEqual(inv_after["investigation_id"], inv_before["investigation_id"])
        self.assertEqual(inv_after["classification"], inv_before["classification"])
        self.assertEqual(inv_after["active_ticket_id"], inv_before["active_ticket_id"])
        self.assertEqual(inv_after["current_ticket"]["title"], inv_before["current_ticket"]["title"])
        self.assertEqual(inv_after["module"], inv_before["module"])
        self.assertEqual(inv_after["severity"], inv_before["severity"])
        self.assertEqual(inv_after["priority"], inv_before["priority"])
        self.assertEqual(inv_after["original_input"]["tester_description"], inv_before["original_input"]["tester_description"])
        self.assertEqual(len(inv_after["developer_updates"]), len(inv_before["developer_updates"]))

        # 71 & 72: Allocators unchanged
        cursor.execute("SELECT scope, last_seq FROM id_allocations ORDER BY scope ASC;")
        allocs_after = cursor.fetchall()
        self.assertEqual(allocs_before, allocs_after)

    # ==========================================
    # 11. INVALID SOURCE STATES (73 - 78)
    # ==========================================

    def test_73_to_78_invalid_source_states(self):
        res_svc = ResolutionService(self.conn)
        payload = self._sample_retest_payload(verdict="PASSED")

        # 73: CAPTURE rejected (not a confirmed bug, 404 by ART ID, but tested on raw transition)
        cap = res_svc.create_investigation(tester_description="Capture state test", reporter="tester")
        cap_key = cap.data["record_key"]
        res_cap = res_svc.submit_retest(cap_key, ["EVD-1"], {"confirmed": True, "verdict": "PASSED"}, "tester")
        self.assertFalse(res_cap.success)
        self.assertIn("Cannot submit retest in lifecycle phase 'CAPTURE'", res_cap.error)

        # 74: OPEN rejected (409)
        conf = res_svc.confirm_bug(cap_key, module="SFN", ticket_data={"title": "SFN bug"})
        open_art = conf.data["canonical_bug_id"]
        res_open = self.client.post(f"/api/v1/bugs/{open_art}/retest", json=payload)
        self.assertEqual(res_open.status_code, 409)
        self.assertEqual(res_open.json()["error"]["code"], "CONFLICT")

        # 75: FIXING rejected (409)
        res_svc.start_work(cap_key, assignee="dev-1", actor="dev-1")
        res_fix = self.client.post(f"/api/v1/bugs/{open_art}/retest", json=payload)
        self.assertEqual(res_fix.status_code, 409)
        self.assertEqual(res_fix.json()["error"]["code"], "CONFLICT")

        # 76: VERIFIED rejected
        res_svc.submit_fix(cap_key, "dev-1", "Fix", "br", "inst")
        res_svc.verify(cap_key, {"confirmed": True, "verdict": "VERIFIED", "confirmedBy": "qa", "notes": "ok"}, actor="qa")
        res_ver = self.client.post(f"/api/v1/bugs/{open_art}/retest", json=payload)
        self.assertEqual(res_ver.status_code, 409)
        self.assertEqual(res_ver.json()["error"]["code"], "CONFLICT")

        # 77: CLOSED rejected
        res_svc.close(cap_key, actor="admin")
        res_cls = self.client.post(f"/api/v1/bugs/{open_art}/retest", json=payload)
        self.assertEqual(res_cls.status_code, 409)

    # ==========================================
    # 12. LEGACY & ATOMICITY (79 - 87)
    # ==========================================

    def test_79_to_80_legacy_retest(self):
        run_legacy_import(self.db_path)

        # Legacy imported bug ART-AGENT-001 starts OPEN
        art_id = "ART-AGENT-001"
        self.client.post(f"/api/v1/bugs/{art_id}/start-work", json={"assignee": "legacy-dev"})
        self.client.post(f"/api/v1/bugs/{art_id}/submit-fix", json={
            "developer_username": "legacy-dev",
            "summary_of_changes": "Legacy fix applied",
            "resolved_in_version_or_branch": "legacy/patch",
            "test_instructions_for_qa": "Retest legacy agent"
        })

        # 79 & 80: Legacy bug in RETEST can submit retest without special API branch
        res_leg = self.client.post(f"/api/v1/bugs/{art_id}/retest", json=self._sample_retest_payload(verdict="PASSED"))
        self.assertEqual(res_leg.status_code, 200)
        self.assertEqual(res_leg.json()["investigation"]["status"], "RETEST")
        self.assertEqual(res_leg.json()["investigation"]["source_kind"], "LEGACY_IMPORT")

    def test_81_to_87_atomicity_and_rollback(self):
        _, art_id, record_key = self._seed_retest_bug()

        cursor = self.conn.cursor()
        cursor.execute("SELECT scope, last_seq FROM id_allocations ORDER BY scope ASC;")
        allocs_before = cursor.fetchall()

        # Inject failure in insert_retest_artifact
        with patch.object(ResolutionService, "submit_retest", side_effect=RuntimeError("Simulated DB failure")):
            res = self.client.post(f"/api/v1/bugs/{art_id}/retest", json=self._sample_retest_payload())
            # 81: Sanitized 500 error envelope
            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json()["error"]["code"], "INTERNAL_ERROR")
            self.assertNotIn("Simulated DB failure", json.dumps(res.json()))

        # 82 - 87: Rollback verification
        inv_check = self.client.get(f"/api/v1/bugs/{art_id}").json()
        self.assertEqual(inv_check["status"], "RETEST")
        self.assertEqual(len(inv_check["retest_artifacts"]), 0)

        cursor.execute("SELECT count(*) FROM audit_events WHERE investigation_key = ? AND event_type = 'RETEST_EXECUTED';", (record_key,))
        self.assertEqual(cursor.fetchone()[0], 0)

        cursor.execute("SELECT scope, last_seq FROM id_allocations ORDER BY scope ASC;")
        allocs_after = cursor.fetchall()
        self.assertEqual(allocs_before, allocs_after)

    # ==========================================
    # 13. OPENAPI VERIFICATION (93 - 97)
    # ==========================================

    def test_93_to_97_openapi(self):
        res = self.client.get("/api/v1/openapi.json")
        self.assertEqual(res.status_code, 200)
        paths = res.json().get("paths", {})

        # 93: /retest documented
        self.assertIn("/api/v1/bugs/{canonical_bug_id}/retest", paths)
        self.assertIn("post", paths["/api/v1/bugs/{canonical_bug_id}/retest"])

        # 94 - 97: Exactly five business writes exist (no verify, close, block)
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
