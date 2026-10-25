"""
core/lifecycle/engine.py

Phase 01D — Deterministic Lifecycle Engine
Implements deterministic, pure lifecycle transition rules for the canonical Investigation contract.

Safety guarantees:
- Pure functions: Does NOT mutate input state objects in-place.
- No AI in transition decisions: Human confirmation is strictly required for VERIFIED.
- Non-bug investigations remain in valid lifecycle phases without forcing bug status flow.
- Append-only audit events returned alongside new state.
"""

from typing import Dict, Any, Optional, Tuple, NamedTuple
from datetime import datetime, timezone
import copy
import uuid

# Canonical Statuses (from common.json)
VALID_CANONICAL_STATUSES = {"OPEN", "FIXING", "RETEST", "VERIFIED", "CLOSED", "BLOCKED"}

# Lifecycle Phases (from common.json)
VALID_LIFECYCLE_PHASES = {"CAPTURE", "INVESTIGATING", "CONFIRMED", "RESOLVED"}

class TransitionResult(NamedTuple):
    success: bool
    new_state: Optional[Dict[str, Any]]
    audit_event: Optional[Dict[str, Any]]
    error: Optional[str]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def can_transition(current_state: Dict[str, Any], action: str, context: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
    """
    Evaluates whether an action can be performed on the given state given the context guards.
    Returns (True, None) if allowed, or (False, reason) if rejected.
    """
    ctx = context or {}
    phase = current_state.get("lifecyclePhase")
    status = current_state.get("status")
    classification = current_state.get("classification")

    # 1. START_INVESTIGATION
    if action == "START_INVESTIGATION":
        if phase != "CAPTURE":
            return False, f"Cannot start investigation from lifecycle phase '{phase}'. Must be in 'CAPTURE'."
        return True, None

    # 2. CONFIRM_INVESTIGATION
    elif action == "CONFIRM_INVESTIGATION":
        if phase not in {"CAPTURE", "INVESTIGATING"}:
            return False, f"Cannot confirm investigation from lifecycle phase '{phase}'."
        target_classification = ctx.get("classification") or classification
        if not target_classification:
            return False, "Cannot confirm investigation without classification."
        if target_classification == "BUG":
            canonical_bug_id = ctx.get("canonicalBugId") or current_state.get("canonicalBugId")
            if not canonical_bug_id:
                return False, "Confirming a BUG requires a canonicalBugId (e.g. ART-AGENT-002)."
            if not ctx.get("ticketArtifactId") and not current_state.get("activeTicketRevisionId"):
                return False, "Confirming a BUG requires an approved ticket artifact reference."
        return True, None

    # 3. START_WORK
    elif action == "START_WORK":
        if phase != "CONFIRMED":
            return False, f"Cannot start work in lifecycle phase '{phase}'. Must be 'CONFIRMED'."
        if status != "OPEN":
            return False, f"Cannot start work when status is '{status}'. Must be 'OPEN'."
        if not current_state.get("canonicalBugId"):
            return False, "Cannot start work on an unconfirmed bug without canonicalBugId."
        actor = ctx.get("actor")
        assignee = ctx.get("assignee") or current_state.get("assignee") or actor
        if not assignee:
            return False, "Starting work requires an assignee."
        return True, None

    # 4. SUBMIT_FIX
    elif action == "SUBMIT_FIX":
        if phase != "CONFIRMED":
            return False, f"Cannot submit fix in lifecycle phase '{phase}'."
        if status != "FIXING":
            return False, f"Cannot submit fix when status is '{status}'. Must be 'FIXING'."
        developer_update = ctx.get("developerUpdate")
        developer_update_id = ctx.get("developerUpdateId")
        if not developer_update and not developer_update_id:
            return False, "Submitting a fix requires a DeveloperUpdate record or reference."
        return True, None

    # 5. SUBMIT_RETEST
    elif action == "SUBMIT_RETEST":
        if phase != "CONFIRMED":
            return False, f"Cannot submit retest in lifecycle phase '{phase}'."
        if status != "RETEST":
            return False, f"Cannot evaluate retest when status is '{status}'. Must be 'RETEST'."
        retest_artifact = ctx.get("retestArtifact")
        if not retest_artifact:
            return False, "Retest submission requires a RetestArtifact."
        evidence_ids = retest_artifact.get("retestEvidenceIds", [])
        if not evidence_ids:
            return False, "Retest submission requires at least one retest evidence reference."
        human_conf = retest_artifact.get("humanConfirmation", {})
        verdict = human_conf.get("verdict")
        if verdict == "VERIFIED":
            return False, "SUBMIT_RETEST cannot establish VERIFIED status. Use explicit VERIFY action."
        if verdict not in {"PASSED", "FAILED", "INCONCLUSIVE", "RETURNED_TO_FIXING", "BLOCKED"}:
            return False, f"Invalid retest human verdict '{verdict}'."
        return True, None

    # 6. VERIFY
    elif action == "VERIFY":
        if phase != "CONFIRMED":
            return False, f"Cannot verify in lifecycle phase '{phase}'."
        if status != "RETEST":
            return False, f"Cannot verify record when status is '{status}'. Must be 'RETEST'."
        retest_artifact = ctx.get("retestArtifact")
        if not retest_artifact:
            return False, "Verification requires a completed RetestArtifact."
        evidence_ids = retest_artifact.get("retestEvidenceIds", [])
        if not evidence_ids:
            return False, "Verification requires at least one retest evidence reference."
        human_conf = retest_artifact.get("humanConfirmation")
        if not human_conf or not human_conf.get("confirmed"):
            return False, "Verification rejected: explicit human confirmation is strictly required."
        if human_conf.get("verdict") != "VERIFIED":
            return False, f"Human verdict is '{human_conf.get('verdict')}', not 'VERIFIED'."
        actor_role = ctx.get("actorRole")
        if actor_role == "AI":
            return False, "Verification rejected: AI is forbidden from confirming VERIFIED status."
        return True, None

    # 7. CLOSE
    elif action == "CLOSE":
        if status != "VERIFIED":
            return False, f"Cannot close record with status '{status}'. Must be 'VERIFIED'."
        return True, None

    # 8. BLOCK
    elif action == "BLOCK":
        reason = ctx.get("reason")
        if not reason or not str(reason).strip():
            return False, "Blocking a record requires an explicit non-empty reason."
        if status in {"CLOSED", "VERIFIED"}:
            return False, f"Cannot block record in terminal/verified status '{status}'."
        return True, None

    return False, f"Unknown action: '{action}'"


def transition(current_state: Dict[str, Any], action: str, context: Optional[Dict[str, Any]] = None) -> TransitionResult:
    """
    Executes a deterministic state transition.
    Pure function: Leaves current_state untouched, returning a TransitionResult with new_state and AuditEvent.
    """
    ctx = context or {}
    allowed, reason = can_transition(current_state, action, ctx)
    if not allowed:
        return TransitionResult(success=False, new_state=None, audit_event=None, error=reason)

    new_state = copy.deepcopy(current_state)
    now = _now_iso()
    new_state["updatedAt"] = now
    investigation_id = new_state.get("id")
    actor = ctx.get("actor", "SYSTEM")

    audit_event = {
        "id": f"AUD-{uuid.uuid4().hex[:12].upper()}",
        "investigationId": investigation_id,
        "timestamp": now,
        "actor": actor,
        "eventType": "STATUS_TRANSITIONED",
        "summary": "",
        "details": {}
    }

    if action == "START_INVESTIGATION":
        new_state["lifecyclePhase"] = "INVESTIGATING"
        audit_event["eventType"] = "AI_ANALYSIS_COMPLETED"
        audit_event["summary"] = "Started investigation analysis"

    elif action == "CONFIRM_INVESTIGATION":
        new_state["lifecyclePhase"] = "CONFIRMED"
        target_classification = ctx.get("classification") or new_state.get("classification")
        new_state["classification"] = target_classification
        if target_classification == "BUG":
            new_state["status"] = "OPEN"
            if ctx.get("canonicalBugId"):
                new_state["canonicalBugId"] = ctx["canonicalBugId"]
            if ctx.get("ticketArtifactId"):
                new_state["activeTicketRevisionId"] = ctx["ticketArtifactId"]
                if ctx["ticketArtifactId"] not in new_state["ticketRevisionIds"]:
                    new_state["ticketRevisionIds"].append(ctx["ticketArtifactId"])
        audit_event["eventType"] = "TICKET_CONFIRMED"
        audit_event["summary"] = f"Investigation confirmed as {target_classification}"

    elif action == "START_WORK":
        new_state["status"] = "FIXING"
        assignee = ctx.get("assignee") or ctx.get("actor") or new_state.get("assignee")
        new_state["assignee"] = assignee
        audit_event["eventType"] = "STATUS_TRANSITIONED"
        audit_event["summary"] = f"Developer started work. Assignee: {assignee}"
        audit_event["details"] = {"previousStatus": "OPEN", "newStatus": "FIXING", "assignee": assignee}

    elif action == "SUBMIT_FIX":
        new_state["status"] = "RETEST"
        dev_id = ctx.get("developerUpdateId") or (ctx.get("developerUpdate", {}).get("id"))
        if dev_id and dev_id not in new_state["developerUpdateIds"]:
            new_state["developerUpdateIds"].append(dev_id)
        audit_event["eventType"] = "FIX_SUBMITTED"
        audit_event["summary"] = f"Developer submitted fix. Transitioned to RETEST"
        audit_event["details"] = {"previousStatus": "FIXING", "newStatus": "RETEST", "developerUpdateId": dev_id}

    elif action == "SUBMIT_RETEST":
        retest_artifact = ctx["retestArtifact"]
        ret_id = retest_artifact.get("id")
        if ret_id and ret_id not in new_state["retestIds"]:
            new_state["retestIds"].append(ret_id)
        human_verdict = retest_artifact["humanConfirmation"]["verdict"]
        if human_verdict == "PASSED":
            # Retest passed execution; stays in RETEST awaiting explicit human verification
            audit_event["eventType"] = "RETEST_EXECUTED"
            audit_event["summary"] = "Retest passed execution. Awaiting human verification"
            audit_event["details"] = {"previousStatus": "RETEST", "newStatus": "RETEST", "verdict": "PASSED", "retestId": ret_id}
        elif human_verdict == "INCONCLUSIVE":
            # Retest inconclusive; stays in RETEST
            audit_event["eventType"] = "RETEST_EXECUTED"
            audit_event["summary"] = "Retest inconclusive. Remains in RETEST"
            audit_event["details"] = {"previousStatus": "RETEST", "newStatus": "RETEST", "verdict": "INCONCLUSIVE", "retestId": ret_id}
        elif human_verdict in {"FAILED", "RETURNED_TO_FIXING"}:
            new_state["status"] = "FIXING"
            audit_event["eventType"] = "RETEST_EXECUTED"
            audit_event["summary"] = "Retest failed. Record returned to FIXING"
            audit_event["details"] = {"previousStatus": "RETEST", "newStatus": "FIXING", "verdict": human_verdict, "retestId": ret_id}
        elif human_verdict == "BLOCKED":
            new_state["status"] = "BLOCKED"
            audit_event["eventType"] = "STATUS_TRANSITIONED"
            audit_event["summary"] = "Retest resulted in BLOCKED status"
            audit_event["details"] = {"previousStatus": "RETEST", "newStatus": "BLOCKED", "retestId": ret_id}

    elif action == "VERIFY":
        new_state["status"] = "VERIFIED"
        retest_id = ctx.get("retestArtifact", {}).get("id")
        if retest_id and retest_id not in new_state["retestIds"]:
            new_state["retestIds"].append(retest_id)
        audit_event["eventType"] = "VERIFIED"
        audit_event["summary"] = f"Human verified resolution. Actor: {actor}"
        audit_event["details"] = {"previousStatus": "RETEST", "newStatus": "VERIFIED"}

    elif action == "CLOSE":
        new_state["status"] = "CLOSED"
        new_state["lifecyclePhase"] = "RESOLVED"
        new_state["resolution"] = {
            "resolvedAt": now,
            "summary": ctx.get("summary", "Resolution verified and ticket closed"),
            "verifiedBy": actor
        }
        audit_event["eventType"] = "STATUS_TRANSITIONED"
        audit_event["summary"] = "Closed and resolved ticket"
        audit_event["details"] = {"previousStatus": "VERIFIED", "newStatus": "CLOSED"}

    elif action == "BLOCK":
        previous_status = new_state.get("status")
        new_state["status"] = "BLOCKED"
        reason = ctx.get("reason", "No reason provided")
        audit_event["eventType"] = "STATUS_TRANSITIONED"
        audit_event["summary"] = f"Status changed to BLOCKED: {reason}"
        audit_event["details"] = {"previousStatus": previous_status, "newStatus": "BLOCKED", "reason": reason}

    # Append audit event id to new state
    new_state["auditEventIds"].append(audit_event["id"])
    return TransitionResult(success=True, new_state=new_state, audit_event=audit_event, error=None)
