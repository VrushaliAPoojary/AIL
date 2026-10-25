"""
core/storage/service.py

Phase 01H — Transactional Lifecycle Orchestration
Coordinates application domain actions with the pure deterministic lifecycle engine
and SQLite persistence layer under atomic database transactions.

Architecture:
ResolutionService
       │
       ├── Loads current persisted state (BEGIN IMMEDIATE)
       │
       ▼
Lifecycle Engine (core/lifecycle/engine.py)
       │
       ├── TransitionResult: (success, new_state, audit_event, error)
       │
       ▼
Repository writes (core/storage/repository.py)
       │
       ├── update_investigation_state
       ├── insert required artifact (DeveloperUpdate, RetestArtifact, etc.)
       └── insert engine-generated AuditEvent
       │
       ▼
COMMIT (or ROLLBACK on any failure)
"""

import sqlite3
import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, NamedTuple

from core.lifecycle.engine import can_transition, transition, TransitionResult
from core.storage.db import AtomicIdAllocator
from core.storage.repository import InvestigationRepository
from core.identity.generator import CANONICAL_MODULES


class ServiceResult(NamedTuple):
    success: bool
    data: Optional[Dict[str, Any]]
    audit_event: Optional[Dict[str, Any]]
    error: Optional[str]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ResolutionService:
    def __init__(self, connection: sqlite3.Connection):
        self.conn = connection
        self.repo = InvestigationRepository(connection)

    def _state_to_engine_dict(self, inv_row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps a persisted investigation row into the state dictionary expected by the lifecycle engine.
        """
        record_key = inv_row["record_key"]
        
        # Load associated revision IDs, dev IDs, retest IDs, audit IDs
        revs = [r["ticket_id"] for r in self.repo.list_ticket_revisions_for_investigation(record_key)]
        audits = [a["id"] for a in self.repo.list_audit_events_for_investigation(record_key)]
        
        # Load evidence IDs
        evs = [e["id"] for e in self.repo.list_evidence_for_investigation(record_key)]

        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM developer_updates WHERE investigation_key = ?;", (record_key,))
        dev_ids = [r[0] for r in cursor.fetchall()]

        cursor.execute("SELECT id FROM retest_artifacts WHERE investigation_key = ?;", (record_key,))
        retest_ids = [r[0] for r in cursor.fetchall()]

        return {
            "id": inv_row["investigation_id"] or inv_row["canonical_bug_id"] or record_key,
            "canonicalBugId": inv_row["canonical_bug_id"],
            "slug": inv_row["slug"],
            "lifecyclePhase": inv_row["lifecycle_phase"],
            "status": inv_row["status"],
            "classification": inv_row["classification"],
            "module": inv_row["module"],
            "severity": inv_row["severity"],
            "priority": inv_row["priority"],
            "assignee": inv_row["assignee"],
            "originalInputId": inv_row["original_input_id"],
            "evidenceIds": evs,
            "aiAnalysisIds": [],
            "researchIds": [],
            "ticketRevisionIds": revs,
            "activeTicketRevisionId": inv_row["active_ticket_id"],
            "developerUpdateIds": dev_ids,
            "retestIds": retest_ids,
            "auditEventIds": audits,
            "createdAt": inv_row["created_at"],
            "updatedAt": inv_row["updated_at"]
        }

    # 1. Create Investigation (Aggregate Initialization)
    def create_investigation(
        self,
        tester_description: str,
        reporter: str,
        slug: str = "new-investigation",
        date_str: Optional[str] = None,
        initial_evidence_ids: Optional[List[str]] = None
    ) -> ServiceResult:
        """
        Creates a native investigation aggregate:
        Allocates INV ID + inserts Investigation + inserts OriginalInput + inserts initial AuditEvent.
        Atomic write transaction.
        """
        if not tester_description and not initial_evidence_ids:
            return ServiceResult(success=False, data=None, audit_event=None, error="Capture requires description or initial evidence.")

        cursor = self.conn.cursor()
        now = _now_iso()
        dt_str = date_str or datetime.now(timezone.utc).strftime("%Y%m%d")
        record_key = str(uuid.uuid4())
        input_id = f"INP-{uuid.uuid4().hex[:12].upper()}"
        audit_id = f"AUD-{uuid.uuid4().hex[:12].upper()}"

        try:
            cursor.execute("BEGIN IMMEDIATE;")

            # 1. Allocate business INV ID
            inv_id = AtomicIdAllocator.allocate_investigation_id(self.conn, dt_str)

            # 2. Insert Investigation
            inv = self.repo.create_investigation(
                record_key=record_key,
                source_kind="NATIVE",
                slug=slug,
                lifecycle_phase="CAPTURE",
                original_input_id=input_id,
                investigation_id=inv_id,
                canonical_bug_id=None,
                status=None,
                classification=None,
                created_at=now,
                updated_at=now
            )

            # 3. Insert OriginalInput
            self.repo.insert_original_input(
                input_id=input_id,
                investigation_key=record_key,
                tester_description=tester_description,
                reporter=reporter,
                captured_at=now,
                initial_evidence_ids=initial_evidence_ids or [],
                provenance="HUMAN_SUPPLIED"
            )

            # 4. Insert Initial Audit Event
            audit = self.repo.insert_audit_event(
                event_id=audit_id,
                investigation_key=record_key,
                timestamp=now,
                actor=reporter,
                event_type="INVESTIGATION_CAPTURED",
                summary=f"Investigation {inv_id} captured",
                details={"source": "native_capture"}
            )

            cursor.execute("COMMIT;")
            return ServiceResult(success=True, data=inv, audit_event=audit, error=None)

        except Exception as e:
            cursor.execute("ROLLBACK;")
            return ServiceResult(success=False, data=None, audit_event=None, error=f"Create investigation failed: {str(e)}")

    # 2. Confirm BUG / Promotion
    def confirm_bug(
        self,
        record_key: str,
        module: str,
        ticket_data: Dict[str, Any],
        actor: str = "SYSTEM"
    ) -> ServiceResult:
        """
        Promotes an investigation to a confirmed BUG:
        Allocates ART-<MODULE>-### atomically + creates initial TicketRevision + transitions to OPEN + commits audit.
        """
        if not module or module.strip().upper() not in CANONICAL_MODULES:
            return ServiceResult(success=False, data=None, audit_event=None, error=f"Module '{module}' is not an approved canonical module.")

        cursor = self.conn.cursor()
        try:
            cursor.execute("BEGIN IMMEDIATE;")
            inv_row = self.repo.get_investigation_by_record_key(record_key)
            if not inv_row:
                cursor.execute("ROLLBACK;")
                return ServiceResult(success=False, data=None, audit_event=None, error="Investigation not found.")

            engine_state = self._state_to_engine_dict(inv_row)
            module_norm = module.strip().upper()

            # Allocate bug ID inside transaction
            bug_id = AtomicIdAllocator.allocate_bug_id(self.conn, module_norm)

            ticket_id = f"TCK-{uuid.uuid4().hex[:12].upper()}"

            ctx = {
                "actor": actor,
                "classification": "BUG",
                "canonicalBugId": bug_id,
                "ticketArtifactId": ticket_id
            }

            # Consult lifecycle engine
            engine_res = transition(engine_state, "CONFIRM_INVESTIGATION", ctx)
            if not engine_res.success:
                cursor.execute("ROLLBACK;")
                return ServiceResult(success=False, data=None, audit_event=None, error=engine_res.error)

            now = engine_res.new_state["updatedAt"]

            # Insert approved TicketRevision
            self.repo.insert_ticket_revision(
                ticket_id=ticket_id,
                investigation_key=record_key,
                revision=1,
                title=ticket_data.get("title", inv_row["slug"]),
                repro_steps=ticket_data.get("reproSteps", "Not provided"),
                expected_result=ticket_data.get("expectedResult", "Not provided"),
                actual_result=ticket_data.get("actualResult", "Not provided"),
                business_impact=ticket_data.get("businessImpact", "Not provided"),
                recommended_solution=ticket_data.get("recommendedSolution", "Not provided"),
                module=module_norm,
                environment=ticket_data.get("environment", "Not provided"),
                severity=ticket_data.get("severity", "HIGH"),
                priority=ticket_data.get("priority", "Not provided"),
                tags=ticket_data.get("tags", [module_norm.lower()]),
                discussion=ticket_data.get("discussion", []),
                updated_at=now,
                provenance="HUMAN_APPROVED"
            )

            # Update Investigation state
            updated_inv = self.repo.update_investigation_state(
                record_key=record_key,
                lifecycle_phase="CONFIRMED",
                status="OPEN",
                updated_at=now,
                classification="BUG",
                canonical_bug_id=bug_id,
                active_ticket_id=ticket_id,
                module=module_norm,
                severity=ticket_data.get("severity", "HIGH"),
                priority=ticket_data.get("priority", "Not provided")
            )

            # Insert Engine-generated Audit Event
            audit = self.repo.insert_audit_event(
                event_id=engine_res.audit_event["id"],
                investigation_key=record_key,
                timestamp=engine_res.audit_event["timestamp"],
                actor=engine_res.audit_event["actor"],
                event_type=engine_res.audit_event["eventType"],
                summary=engine_res.audit_event["summary"],
                details=engine_res.audit_event.get("details")
            )

            cursor.execute("COMMIT;")
            return ServiceResult(success=True, data=updated_inv, audit_event=audit, error=None)

        except Exception as e:
            cursor.execute("ROLLBACK;")
            return ServiceResult(success=False, data=None, audit_event=None, error=f"Confirm bug failed: {str(e)}")

    # 3. Start Work
    def start_work(self, record_key: str, assignee: str, actor: str) -> ServiceResult:
        cursor = self.conn.cursor()
        try:
            cursor.execute("BEGIN IMMEDIATE;")
            inv_row = self.repo.get_investigation_by_record_key(record_key)
            if not inv_row:
                cursor.execute("ROLLBACK;")
                return ServiceResult(success=False, data=None, audit_event=None, error="Investigation not found.")

            engine_state = self._state_to_engine_dict(inv_row)
            ctx = {"actor": actor, "assignee": assignee}

            engine_res = transition(engine_state, "START_WORK", ctx)
            if not engine_res.success:
                cursor.execute("ROLLBACK;")
                return ServiceResult(success=False, data=None, audit_event=None, error=engine_res.error)

            now = engine_res.new_state["updatedAt"]

            updated_inv = self.repo.update_investigation_state(
                record_key=record_key,
                lifecycle_phase=engine_res.new_state["lifecyclePhase"],
                status=engine_res.new_state["status"],
                updated_at=now,
                assignee=assignee
            )

            audit = self.repo.insert_audit_event(
                event_id=engine_res.audit_event["id"],
                investigation_key=record_key,
                timestamp=engine_res.audit_event["timestamp"],
                actor=engine_res.audit_event["actor"],
                event_type=engine_res.audit_event["eventType"],
                summary=engine_res.audit_event["summary"],
                details=engine_res.audit_event.get("details")
            )

            cursor.execute("COMMIT;")
            return ServiceResult(success=True, data=updated_inv, audit_event=audit, error=None)

        except Exception as e:
            cursor.execute("ROLLBACK;")
            return ServiceResult(success=False, data=None, audit_event=None, error=f"Start work failed: {str(e)}")

    # 4. Submit Fix
    def submit_fix(
        self,
        record_key: str,
        developer_username: str,
        summary_of_changes: str,
        resolved_in_version_or_branch: str,
        test_instructions_for_qa: str,
        commit_hash_or_pr: Optional[str] = None,
        actor: Optional[str] = None
    ) -> ServiceResult:
        cursor = self.conn.cursor()
        try:
            cursor.execute("BEGIN IMMEDIATE;")
            inv_row = self.repo.get_investigation_by_record_key(record_key)
            if not inv_row:
                cursor.execute("ROLLBACK;")
                return ServiceResult(success=False, data=None, audit_event=None, error="Investigation not found.")

            dev_id = f"DEV-{uuid.uuid4().hex[:12].upper()}"
            engine_state = self._state_to_engine_dict(inv_row)
            act = actor or developer_username

            ctx = {
                "actor": act,
                "developerUpdateId": dev_id,
                "developerUpdate": {
                    "id": dev_id,
                    "investigationId": engine_state["id"]
                }
            }

            engine_res = transition(engine_state, "SUBMIT_FIX", ctx)
            if not engine_res.success:
                cursor.execute("ROLLBACK;")
                return ServiceResult(success=False, data=None, audit_event=None, error=engine_res.error)

            now = engine_res.new_state["updatedAt"]

            # Insert DeveloperUpdate
            self.repo.insert_developer_update(
                dev_id=dev_id,
                investigation_key=record_key,
                developer_username=developer_username,
                summary_of_changes=summary_of_changes,
                commit_hash_or_pr=commit_hash_or_pr,
                resolved_in_version_or_branch=resolved_in_version_or_branch,
                test_instructions_for_qa=test_instructions_for_qa,
                submitted_at=now,
                provenance="DEVELOPER_UPDATE"
            )

            updated_inv = self.repo.update_investigation_state(
                record_key=record_key,
                lifecycle_phase=engine_res.new_state["lifecyclePhase"],
                status=engine_res.new_state["status"],
                updated_at=now
            )

            audit = self.repo.insert_audit_event(
                event_id=engine_res.audit_event["id"],
                investigation_key=record_key,
                timestamp=engine_res.audit_event["timestamp"],
                actor=engine_res.audit_event["actor"],
                event_type=engine_res.audit_event["eventType"],
                summary=engine_res.audit_event["summary"],
                details=engine_res.audit_event.get("details")
            )

            cursor.execute("COMMIT;")
            return ServiceResult(success=True, data=updated_inv, audit_event=audit, error=None)

        except Exception as e:
            cursor.execute("ROLLBACK;")
            return ServiceResult(success=False, data=None, audit_event=None, error=f"Submit fix failed: {str(e)}")

    # 5. Submit Retest (Executes retest outcome; can return to FIXING, or stay RETEST if pending decision)
    def submit_retest(
        self,
        record_key: str,
        retest_evidence_ids: List[str],
        human_confirmation: Dict[str, Any],
        actor: str,
        ai_recommendation: Optional[Dict[str, Any]] = None
    ) -> ServiceResult:
        cursor = self.conn.cursor()
        try:
            cursor.execute("BEGIN IMMEDIATE;")
            inv_row = self.repo.get_investigation_by_record_key(record_key)
            if not inv_row:
                cursor.execute("ROLLBACK;")
                return ServiceResult(success=False, data=None, audit_event=None, error="Investigation not found.")

            ret_id = f"RET-{uuid.uuid4().hex[:12].upper()}"
            engine_state = self._state_to_engine_dict(inv_row)

            retest_artifact_payload = {
                "id": ret_id,
                "investigationId": engine_state["id"],
                "retestEvidenceIds": retest_evidence_ids,
                "humanConfirmation": human_confirmation,
                "aiComparisonRecommendation": ai_recommendation
            }

            ctx = {
                "actor": actor,
                "retestArtifact": retest_artifact_payload
            }

            engine_res = transition(engine_state, "SUBMIT_RETEST", ctx)
            if not engine_res.success:
                cursor.execute("ROLLBACK;")
                return ServiceResult(success=False, data=None, audit_event=None, error=engine_res.error)

            now = engine_res.new_state["updatedAt"]

            # Insert RetestArtifact
            self.repo.insert_retest_artifact(
                retest_id=ret_id,
                investigation_key=record_key,
                retest_evidence_ids=retest_evidence_ids,
                human_confirmation=human_confirmation,
                executed_at=now,
                ai_recommendation=ai_recommendation,
                provenance="RETEST_VERIFICATION"
            )

            updated_inv = self.repo.update_investigation_state(
                record_key=record_key,
                lifecycle_phase=engine_res.new_state["lifecyclePhase"],
                status=engine_res.new_state["status"],
                updated_at=now
            )

            audit = self.repo.insert_audit_event(
                event_id=engine_res.audit_event["id"],
                investigation_key=record_key,
                timestamp=engine_res.audit_event["timestamp"],
                actor=engine_res.audit_event["actor"],
                event_type=engine_res.audit_event["eventType"],
                summary=engine_res.audit_event["summary"],
                details=engine_res.audit_event.get("details")
            )

            cursor.execute("COMMIT;")
            return ServiceResult(success=True, data=updated_inv, audit_event=audit, error=None)

        except Exception as e:
            cursor.execute("ROLLBACK;")
            return ServiceResult(success=False, data=None, audit_event=None, error=f"Submit retest failed: {str(e)}")

    # 6. Verify (Explicit Human Decision)
    def verify(
        self,
        record_key: str,
        human_confirmation: Dict[str, Any],
        actor: str,
        actor_role: str = "HUMAN",
        retest_evidence_ids: Optional[List[str]] = None
    ) -> ServiceResult:
        if actor_role == "AI":
            return ServiceResult(success=False, data=None, audit_event=None, error="Verification rejected: AI is forbidden from confirming VERIFIED status.")

        cursor = self.conn.cursor()
        try:
            cursor.execute("BEGIN IMMEDIATE;")
            inv_row = self.repo.get_investigation_by_record_key(record_key)
            if not inv_row:
                cursor.execute("ROLLBACK;")
                return ServiceResult(success=False, data=None, audit_event=None, error="Investigation not found.")

            engine_state = self._state_to_engine_dict(inv_row)
            ret_id = f"RET-{uuid.uuid4().hex[:12].upper()}"

            ctx = {
                "actor": actor,
                "actorRole": actor_role,
                "retestArtifact": {
                    "id": ret_id,
                    "retestEvidenceIds": retest_evidence_ids or ["EVD-VERIFIED-SIGN-OFF"],
                    "humanConfirmation": human_confirmation
                }
            }

            engine_res = transition(engine_state, "VERIFY", ctx)
            if not engine_res.success:
                cursor.execute("ROLLBACK;")
                return ServiceResult(success=False, data=None, audit_event=None, error=engine_res.error)

            now = engine_res.new_state["updatedAt"]

            updated_inv = self.repo.update_investigation_state(
                record_key=record_key,
                lifecycle_phase=engine_res.new_state["lifecyclePhase"],
                status=engine_res.new_state["status"],
                updated_at=now
            )

            audit = self.repo.insert_audit_event(
                event_id=engine_res.audit_event["id"],
                investigation_key=record_key,
                timestamp=engine_res.audit_event["timestamp"],
                actor=engine_res.audit_event["actor"],
                event_type=engine_res.audit_event["eventType"],
                summary=engine_res.audit_event["summary"],
                details=engine_res.audit_event.get("details")
            )

            cursor.execute("COMMIT;")
            return ServiceResult(success=True, data=updated_inv, audit_event=audit, error=None)

        except Exception as e:
            cursor.execute("ROLLBACK;")
            return ServiceResult(success=False, data=None, audit_event=None, error=f"Verify failed: {str(e)}")

    # 7. Close
    def close(self, record_key: str, actor: str, summary: str = "Verified and closed") -> ServiceResult:
        cursor = self.conn.cursor()
        try:
            cursor.execute("BEGIN IMMEDIATE;")
            inv_row = self.repo.get_investigation_by_record_key(record_key)
            if not inv_row:
                cursor.execute("ROLLBACK;")
                return ServiceResult(success=False, data=None, audit_event=None, error="Investigation not found.")

            engine_state = self._state_to_engine_dict(inv_row)
            ctx = {"actor": actor, "summary": summary}

            engine_res = transition(engine_state, "CLOSE", ctx)
            if not engine_res.success:
                cursor.execute("ROLLBACK;")
                return ServiceResult(success=False, data=None, audit_event=None, error=engine_res.error)

            now = engine_res.new_state["updatedAt"]

            updated_inv = self.repo.update_investigation_state(
                record_key=record_key,
                lifecycle_phase=engine_res.new_state["lifecyclePhase"],
                status=engine_res.new_state["status"],
                updated_at=now,
                resolution_json=json.dumps(engine_res.new_state["resolution"])
            )

            audit = self.repo.insert_audit_event(
                event_id=engine_res.audit_event["id"],
                investigation_key=record_key,
                timestamp=engine_res.audit_event["timestamp"],
                actor=engine_res.audit_event["actor"],
                event_type=engine_res.audit_event["eventType"],
                summary=engine_res.audit_event["summary"],
                details=engine_res.audit_event.get("details")
            )

            cursor.execute("COMMIT;")
            return ServiceResult(success=True, data=updated_inv, audit_event=audit, error=None)

        except Exception as e:
            cursor.execute("ROLLBACK;")
            return ServiceResult(success=False, data=None, audit_event=None, error=f"Close failed: {str(e)}")

    # 8. Block
    def block(self, record_key: str, reason: str, actor: str) -> ServiceResult:
        cursor = self.conn.cursor()
        try:
            cursor.execute("BEGIN IMMEDIATE;")
            inv_row = self.repo.get_investigation_by_record_key(record_key)
            if not inv_row:
                cursor.execute("ROLLBACK;")
                return ServiceResult(success=False, data=None, audit_event=None, error="Investigation not found.")

            engine_state = self._state_to_engine_dict(inv_row)
            ctx = {"actor": actor, "reason": reason}

            engine_res = transition(engine_state, "BLOCK", ctx)
            if not engine_res.success:
                cursor.execute("ROLLBACK;")
                return ServiceResult(success=False, data=None, audit_event=None, error=engine_res.error)

            now = engine_res.new_state["updatedAt"]

            updated_inv = self.repo.update_investigation_state(
                record_key=record_key,
                lifecycle_phase=engine_res.new_state["lifecyclePhase"],
                status=engine_res.new_state["status"],
                updated_at=now
            )

            audit = self.repo.insert_audit_event(
                event_id=engine_res.audit_event["id"],
                investigation_key=record_key,
                timestamp=engine_res.audit_event["timestamp"],
                actor=engine_res.audit_event["actor"],
                event_type=engine_res.audit_event["eventType"],
                summary=engine_res.audit_event["summary"],
                details=engine_res.audit_event.get("details")
            )

            cursor.execute("COMMIT;")
            return ServiceResult(success=True, data=updated_inv, audit_event=audit, error=None)

        except Exception as e:
            cursor.execute("ROLLBACK;")
            return ServiceResult(success=False, data=None, audit_event=None, error=f"Block failed: {str(e)}")
