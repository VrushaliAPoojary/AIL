"""
tests/test_lifecycle_engine.py

Phase 01D — Deterministic Lifecycle Engine Test Suite
Validates pure deterministic transition rules, guard evaluations, human-verification requirements,
audit event creation, state immutability, and legacy record safety.
"""

import unittest
import copy
import json
import os
import jsonschema

from core.lifecycle.engine import can_transition, transition, TransitionResult

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCHEMAS_DIR = os.path.join(BASE_DIR, "contracts/schemas")
FIXTURES_DIR = os.path.join(BASE_DIR, "contracts/fixtures")


def load_schemas():
    store = {}
    for fname in os.listdir(SCHEMAS_DIR):
        if fname.endswith(".json"):
            fpath = os.path.join(SCHEMAS_DIR, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                store[fname] = data
                if "$id" in data:
                    store[data["$id"]] = data
    return store


class TestLifecycleEngine(unittest.TestCase):
    def setUp(self):
        self.schemas = load_schemas()
        self.resolver = jsonschema.RefResolver.from_schema(self.schemas["common.json"], store=self.schemas)
        self.investigation_validator = jsonschema.Draft202012Validator(self.schemas["investigation.json"], resolver=self.resolver)
        self.audit_validator = jsonschema.Draft202012Validator(self.schemas["audit_event.json"], resolver=self.resolver)

        # Baseline capture state (Investigation schema compliant)
        self.base_capture_state = {
            "id": "INV-20260925-0001",
            "canonicalBugId": None,
            "slug": "sample-investigation",
            "lifecyclePhase": "CAPTURE",
            "status": None,
            "classification": None,
            "module": "Not provided",
            "severity": "Not provided",
            "priority": "Not provided",
            "assignee": None,
            "originalInputId": "INP-001",
            "evidenceIds": ["EVD-001"],
            "aiAnalysisIds": [],
            "researchIds": [],
            "ticketRevisionIds": [],
            "activeTicketRevisionId": None,
            "developerUpdateIds": [],
            "retestIds": [],
            "auditEventIds": ["AUD-001"],
            "createdAt": "2026-09-25T12:00:00Z",
            "updatedAt": "2026-09-25T12:00:00Z"
        }

    # 1. CAPTURE → INVESTIGATING allowed
    def test_01_capture_to_investigating_allowed(self):
        allowed, err = can_transition(self.base_capture_state, "START_INVESTIGATION")
        self.assertTrue(allowed)
        self.assertIsNone(err)

        res = transition(self.base_capture_state, "START_INVESTIGATION", {"actor": "tester"})
        self.assertTrue(res.success)
        self.assertEqual(res.new_state["lifecyclePhase"], "INVESTIGATING")
        self.assertIsNone(res.new_state["status"])  # status remains None in pre-ticket flow
        self.audit_validator.validate(res.audit_event)

    # 2. Invalid pre-ticket transition rejected
    def test_02_invalid_pre_ticket_transition_rejected(self):
        # Cannot start work on a CAPTURE state
        allowed, err = can_transition(self.base_capture_state, "START_WORK", {"assignee": "dev1"})
        self.assertFalse(allowed)
        self.assertIn("Cannot start work in lifecycle phase 'CAPTURE'", err)

        res = transition(self.base_capture_state, "START_WORK", {"assignee": "dev1"})
        self.assertFalse(res.success)
        self.assertIsNone(res.new_state)
        self.assertIsNone(res.audit_event)

    # 3. Confirmed BUG can become OPEN according to contract
    def test_03_confirm_bug_becomes_open(self):
        ctx = {
            "classification": "BUG",
            "canonicalBugId": "ART-AGENT-002",
            "ticketArtifactId": "TCK-AGENT-002-01",
            "actor": "lead-tester"
        }
        allowed, err = can_transition(self.base_capture_state, "CONFIRM_INVESTIGATION", ctx)
        self.assertTrue(allowed)

        res = transition(self.base_capture_state, "CONFIRM_INVESTIGATION", ctx)
        self.assertTrue(res.success)
        self.assertEqual(res.new_state["lifecyclePhase"], "CONFIRMED")
        self.assertEqual(res.new_state["status"], "OPEN")
        self.assertEqual(res.new_state["canonicalBugId"], "ART-AGENT-002")
        self.assertEqual(res.new_state["activeTicketRevisionId"], "TCK-AGENT-002-01")
        self.investigation_validator.validate(res.new_state)
        self.audit_validator.validate(res.audit_event)

    # 4. OPEN → FIXING allowed when guards pass
    def test_04_open_to_fixing_allowed_when_guards_pass(self):
        open_state = copy.deepcopy(self.base_capture_state)
        open_state["lifecyclePhase"] = "CONFIRMED"
        open_state["status"] = "OPEN"
        open_state["canonicalBugId"] = "ART-AGENT-002"

        ctx = {"actor": "dev1", "assignee": "dev1"}
        allowed, err = can_transition(open_state, "START_WORK", ctx)
        self.assertTrue(allowed)

        res = transition(open_state, "START_WORK", ctx)
        self.assertTrue(res.success)
        self.assertEqual(res.new_state["status"], "FIXING")
        self.assertEqual(res.new_state["assignee"], "dev1")
        self.investigation_validator.validate(res.new_state)

    # 5. OPEN → RETEST rejected
    def test_05_open_to_retest_rejected(self):
        open_state = copy.deepcopy(self.base_capture_state)
        open_state["lifecyclePhase"] = "CONFIRMED"
        open_state["status"] = "OPEN"
        open_state["canonicalBugId"] = "ART-AGENT-002"

        allowed, err = can_transition(open_state, "SUBMIT_FIX", {"developerUpdateId": "DEV-001"})
        self.assertFalse(allowed)
        self.assertIn("Cannot submit fix when status is 'OPEN'. Must be 'FIXING'.", err)

    # 6. FIXING → RETEST allowed when guards pass
    def test_06_fixing_to_retest_allowed(self):
        fixing_state = copy.deepcopy(self.base_capture_state)
        fixing_state["lifecyclePhase"] = "CONFIRMED"
        fixing_state["status"] = "FIXING"
        fixing_state["canonicalBugId"] = "ART-AGENT-002"
        fixing_state["assignee"] = "dev1"

        ctx = {"developerUpdateId": "DEV-001", "actor": "dev1"}
        allowed, err = can_transition(fixing_state, "SUBMIT_FIX", ctx)
        self.assertTrue(allowed)

        res = transition(fixing_state, "SUBMIT_FIX", ctx)
        self.assertTrue(res.success)
        self.assertEqual(res.new_state["status"], "RETEST")
        self.assertIn("DEV-001", res.new_state["developerUpdateIds"])
        self.investigation_validator.validate(res.new_state)

    # 7. FIXING → VERIFIED rejected
    def test_07_fixing_to_verified_rejected(self):
        fixing_state = copy.deepcopy(self.base_capture_state)
        fixing_state["lifecyclePhase"] = "CONFIRMED"
        fixing_state["status"] = "FIXING"

        allowed, err = can_transition(fixing_state, "VERIFY", {
            "retestArtifact": {
                "id": "RET-01",
                "retestEvidenceIds": ["EVD-RET-01"],
                "humanConfirmation": {"confirmed": True, "verdict": "VERIFIED"}
            }
        })
        self.assertFalse(allowed)
        self.assertIn("Cannot verify record when status is 'FIXING'. Must be 'RETEST'.", err)

    # 8. RETEST → FIXING allowed after failed retest
    def test_08_retest_to_fixing_allowed_on_failed_retest(self):
        retest_state = copy.deepcopy(self.base_capture_state)
        retest_state["lifecyclePhase"] = "CONFIRMED"
        retest_state["status"] = "RETEST"
        retest_state["canonicalBugId"] = "ART-AGENT-002"

        ctx = {
            "actor": "qa-tester",
            "retestArtifact": {
                "id": "RET-001",
                "investigationId": "ART-AGENT-002",
                "retestEvidenceIds": ["EVD-RET-01"],
                "humanConfirmation": {
                    "confirmed": True,
                    "verdict": "FAILED",
                    "confirmedBy": "qa-tester",
                    "notes": "Bug still repros in build 12"
                }
            }
        }
        allowed, err = can_transition(retest_state, "SUBMIT_RETEST", ctx)
        self.assertTrue(allowed)

        res = transition(retest_state, "SUBMIT_RETEST", ctx)
        self.assertTrue(res.success)
        self.assertEqual(res.new_state["status"], "FIXING")
        self.assertIn("RET-001", res.new_state["retestIds"])
        self.assertEqual(res.audit_event["eventType"], "RETEST_EXECUTED")

    def test_08a_retest_passed_remains_retest(self):
        retest_state = copy.deepcopy(self.base_capture_state)
        retest_state["lifecyclePhase"] = "CONFIRMED"
        retest_state["status"] = "RETEST"
        retest_state["canonicalBugId"] = "ART-AGENT-002"

        ctx = {
            "actor": "qa-tester",
            "retestArtifact": {
                "id": "RET-002",
                "investigationId": "ART-AGENT-002",
                "retestEvidenceIds": ["EVD-RET-02"],
                "humanConfirmation": {
                    "confirmed": True,
                    "verdict": "PASSED",
                    "confirmedBy": "qa-tester",
                    "notes": "Feature behaves as expected"
                }
            }
        }
        allowed, err = can_transition(retest_state, "SUBMIT_RETEST", ctx)
        self.assertTrue(allowed)

        res = transition(retest_state, "SUBMIT_RETEST", ctx)
        self.assertTrue(res.success)
        self.assertEqual(res.new_state["status"], "RETEST")
        self.assertEqual(res.new_state["lifecyclePhase"], "CONFIRMED")
        self.assertNotEqual(res.new_state["status"], "VERIFIED")
        self.assertNotEqual(res.new_state["status"], "CLOSED")
        self.assertNotEqual(res.new_state["lifecyclePhase"], "RESOLVED")
        self.assertEqual(res.audit_event["eventType"], "RETEST_EXECUTED")
        self.assertIn("RET-002", res.new_state["retestIds"])

    def test_08b_retest_inconclusive_remains_retest(self):
        retest_state = copy.deepcopy(self.base_capture_state)
        retest_state["lifecyclePhase"] = "CONFIRMED"
        retest_state["status"] = "RETEST"
        retest_state["canonicalBugId"] = "ART-AGENT-002"

        ctx = {
            "actor": "qa-tester",
            "retestArtifact": {
                "id": "RET-003",
                "investigationId": "ART-AGENT-002",
                "retestEvidenceIds": ["EVD-RET-03"],
                "humanConfirmation": {
                    "confirmed": True,
                    "verdict": "INCONCLUSIVE",
                    "confirmedBy": "qa-tester",
                    "notes": "Environment was unstable, need fresh run"
                }
            }
        }
        allowed, err = can_transition(retest_state, "SUBMIT_RETEST", ctx)
        self.assertTrue(allowed)

        res = transition(retest_state, "SUBMIT_RETEST", ctx)
        self.assertTrue(res.success)
        self.assertEqual(res.new_state["status"], "RETEST")
        self.assertEqual(res.audit_event["eventType"], "RETEST_EXECUTED")
        self.assertIn("RET-003", res.new_state["retestIds"])

    def test_08c_submit_retest_cannot_produce_verified(self):
        retest_state = copy.deepcopy(self.base_capture_state)
        retest_state["lifecyclePhase"] = "CONFIRMED"
        retest_state["status"] = "RETEST"

        ctx = {
            "actor": "qa-tester",
            "retestArtifact": {
                "id": "RET-004",
                "investigationId": "ART-AGENT-002",
                "retestEvidenceIds": ["EVD-RET-04"],
                "humanConfirmation": {
                    "confirmed": True,
                    "verdict": "VERIFIED",
                    "confirmedBy": "qa-tester",
                    "notes": "Trying to bypass verify"
                }
            }
        }
        allowed, err = can_transition(retest_state, "SUBMIT_RETEST", ctx)
        self.assertFalse(allowed)
        self.assertIn("SUBMIT_RETEST cannot establish VERIFIED status. Use explicit VERIFY action.", err)

    # 9. RETEST → VERIFIED rejected without human confirmation
    def test_09_retest_to_verified_rejected_without_human_confirmation(self):
        retest_state = copy.deepcopy(self.base_capture_state)
        retest_state["lifecyclePhase"] = "CONFIRMED"
        retest_state["status"] = "RETEST"

        # AI recommends passed, but humanConfirmation is False or missing
        ctx = {
            "actorRole": "AI",
            "retestArtifact": {
                "id": "RET-001",
                "retestEvidenceIds": ["EVD-RET-01"],
                "aiComparisonRecommendation": {"recommendation": "PASSED", "notes": "Diff is clean"},
                "humanConfirmation": {"confirmed": False, "verdict": "VERIFIED"}
            }
        }
        allowed, err = can_transition(retest_state, "VERIFY", ctx)
        self.assertFalse(allowed)
        self.assertIn("human confirmation is strictly required", err)

        # AI actor role directly blocked from VERIFY action
        ctx["retestArtifact"]["humanConfirmation"]["confirmed"] = True
        allowed, err = can_transition(retest_state, "VERIFY", ctx)
        self.assertFalse(allowed)
        self.assertIn("AI is forbidden from confirming VERIFIED status", err)

    # 10. RETEST → VERIFIED rejected without retest evidence
    def test_10_retest_to_verified_rejected_without_evidence(self):
        retest_state = copy.deepcopy(self.base_capture_state)
        retest_state["lifecyclePhase"] = "CONFIRMED"
        retest_state["status"] = "RETEST"

        ctx = {
            "actor": "lead-qa",
            "actorRole": "HUMAN",
            "retestArtifact": {
                "id": "RET-001",
                "retestEvidenceIds": [],  # Empty evidence
                "humanConfirmation": {"confirmed": True, "verdict": "VERIFIED"}
            }
        }
        allowed, err = can_transition(retest_state, "VERIFY", ctx)
        self.assertFalse(allowed)
        self.assertIn("Verification requires at least one retest evidence reference", err)

    # 11. RETEST → VERIFIED allowed with completed retest, evidence, and human confirmation
    def test_11_retest_to_verified_allowed(self):
        retest_state = copy.deepcopy(self.base_capture_state)
        retest_state["lifecyclePhase"] = "CONFIRMED"
        retest_state["status"] = "RETEST"
        retest_state["canonicalBugId"] = "ART-AGENT-002"

        ctx = {
            "actor": "lead-qa",
            "actorRole": "HUMAN",
            "retestArtifact": {
                "id": "RET-001",
                "retestEvidenceIds": ["EVD-RET-LOG-01.txt"],
                "humanConfirmation": {
                    "confirmed": True,
                    "verdict": "VERIFIED",
                    "confirmedBy": "lead-qa",
                    "notes": "Verified against staging log output"
                }
            }
        }
        allowed, err = can_transition(retest_state, "VERIFY", ctx)
        self.assertTrue(allowed)

        res = transition(retest_state, "VERIFY", ctx)
        self.assertTrue(res.success)
        self.assertEqual(res.new_state["status"], "VERIFIED")
        self.investigation_validator.validate(res.new_state)
        self.audit_validator.validate(res.audit_event)

    # 12. VERIFIED → CLOSED allowed
    def test_12_verified_to_closed_allowed(self):
        verified_state = copy.deepcopy(self.base_capture_state)
        verified_state["lifecyclePhase"] = "CONFIRMED"
        verified_state["status"] = "VERIFIED"
        verified_state["canonicalBugId"] = "ART-AGENT-002"

        ctx = {"actor": "admin", "summary": "Ticket verified and resolved in release 1.0"}
        allowed, err = can_transition(verified_state, "CLOSE", ctx)
        self.assertTrue(allowed)

        res = transition(verified_state, "CLOSE", ctx)
        self.assertTrue(res.success)
        self.assertEqual(res.new_state["status"], "CLOSED")
        self.assertEqual(res.new_state["lifecyclePhase"], "RESOLVED")
        self.assertIsNotNone(res.new_state["resolution"])
        self.investigation_validator.validate(res.new_state)

    # 13. CLOSED → FIXING rejected
    def test_13_closed_to_fixing_rejected(self):
        closed_state = copy.deepcopy(self.base_capture_state)
        closed_state["lifecyclePhase"] = "RESOLVED"
        closed_state["status"] = "CLOSED"

        allowed, err = can_transition(closed_state, "START_WORK", {"assignee": "dev1"})
        self.assertFalse(allowed)
        self.assertIn("Cannot start work in lifecycle phase 'RESOLVED'", err)

    # 14. BLOCK requires reason and produces BLOCKED
    def test_14_block_requires_reason(self):
        open_state = copy.deepcopy(self.base_capture_state)
        open_state["lifecyclePhase"] = "CONFIRMED"
        open_state["status"] = "OPEN"

        # Missing reason
        allowed, err = can_transition(open_state, "BLOCK", {"reason": ""})
        self.assertFalse(allowed)
        self.assertIn("requires an explicit non-empty reason", err)

        # Valid reason produces BLOCKED
        ctx = {"reason": "Blocked waiting for upstream auth gateway upgrade", "actor": "dev1"}
        allowed, err = can_transition(open_state, "BLOCK", ctx)
        self.assertTrue(allowed)

        res = transition(open_state, "BLOCK", ctx)
        self.assertTrue(res.success)
        self.assertEqual(res.new_state["status"], "BLOCKED")
        self.audit_validator.validate(res.audit_event)

        blocked_state = res.new_state

        # UNBLOCK action is rejected as unsupported
        unblock_allowed, unblock_err = can_transition(blocked_state, "UNBLOCK", {"restoreStatus": "OPEN"})
        self.assertFalse(unblock_allowed)
        self.assertIn("Unknown action", unblock_err)

        unblock_res = transition(blocked_state, "UNBLOCK", {"restoreStatus": "OPEN"})
        self.assertFalse(unblock_res.success)
        self.assertIsNone(unblock_res.new_state)

        # BLOCKED -> OPEN cannot be requested through another action
        start_work_allowed, start_work_err = can_transition(blocked_state, "START_WORK", {"assignee": "dev1"})
        self.assertFalse(start_work_allowed)
        self.assertIn("Must be 'OPEN'", start_work_err)

        # BLOCKED -> FIXING cannot be requested through another action
        submit_fix_allowed, submit_fix_err = can_transition(blocked_state, "SUBMIT_FIX", {"developerUpdateId": "DEV-01"})
        self.assertFalse(submit_fix_allowed)
        self.assertIn("Must be 'FIXING'", submit_fix_err)

        # BLOCKED -> RETEST cannot be requested through another action
        submit_retest_allowed, submit_retest_err = can_transition(blocked_state, "SUBMIT_RETEST", {
            "retestArtifact": {
                "id": "RET-01",
                "retestEvidenceIds": ["EVD-01"],
                "humanConfirmation": {"confirmed": True, "verdict": "VERIFIED"}
            }
        })
        self.assertFalse(submit_retest_allowed)
        self.assertIn("Must be 'RETEST'", submit_retest_err)

    # 15. Invalid arbitrary status assignment is impossible through public lifecycle actions
    def test_15_arbitrary_status_rejected(self):
        allowed, err = can_transition(self.base_capture_state, "SET_STATUS_DIRECTLY", {"status": "VERIFIED"})
        self.assertFalse(allowed)
        self.assertIn("Unknown action", err)

    # 16. Transition returns a new object and does not mutate input
    def test_16_state_immutability(self):
        original_copy = copy.deepcopy(self.base_capture_state)
        res = transition(self.base_capture_state, "START_INVESTIGATION", {"actor": "tester"})
        self.assertTrue(res.success)
        # Verify self.base_capture_state was not modified
        self.assertEqual(self.base_capture_state, original_copy)
        self.assertNotEqual(id(self.base_capture_state), id(res.new_state))

    # 17. Successful transition returns audit event
    def test_17_successful_transition_returns_audit_event(self):
        res = transition(self.base_capture_state, "START_INVESTIGATION", {"actor": "tester"})
        self.assertTrue(res.success)
        self.assertIsNotNone(res.audit_event)
        self.assertEqual(res.audit_event["actor"], "tester")
        self.assertEqual(res.audit_event["investigationId"], self.base_capture_state["id"])

    # 18. Failed transition does not return successful audit mutation
    def test_18_failed_transition_no_audit(self):
        res = transition(self.base_capture_state, "START_WORK", {"assignee": "dev1"})
        self.assertFalse(res.success)
        self.assertIsNone(res.audit_event)
        self.assertIsNone(res.new_state)

    # 19. LEGACY SAFETY TEST: Loading and evaluating historical record causes zero mutation
    def test_19_legacy_safety_test(self):
        fixture_path = os.path.join(FIXTURES_DIR, "legacy_art_agent_001_fixture.json")
        with open(fixture_path, "r", encoding="utf-8") as f:
            legacy_data = json.load(f)
        legacy_inv = legacy_data["Investigation"]
        legacy_copy = copy.deepcopy(legacy_inv)

        # Check guard against START_WORK (allowed)
        allowed, err = can_transition(legacy_inv, "START_WORK", {"assignee": "dev-agent", "actor": "dev-agent"})
        self.assertTrue(allowed)

        # Execute transition on a branch
        res = transition(legacy_inv, "START_WORK", {"assignee": "dev-agent", "actor": "dev-agent"})
        self.assertTrue(res.success)

        # Ensure historical legacy object remained bitwise identical
        self.assertEqual(legacy_inv, legacy_copy)
        self.assertEqual(legacy_inv["status"], "OPEN")
        self.assertEqual(legacy_inv["assignee"], None)


if __name__ == "__main__":
    unittest.main()
