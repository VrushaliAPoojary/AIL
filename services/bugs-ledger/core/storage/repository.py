"""
core/storage/repository.py

Phase 01G — Minimal Persistence Primitives
Provides minimal primitives to create, insert, and query investigations, original inputs,
evidence metadata, and append-only artifacts.

Safety constraints:
- Immutability Boundary: Does NOT expose general UPDATE methods for append-only entities
  (original_inputs, evidence, ai_artifacts, research_artifacts, ticket_revisions,
   developer_updates, retest_artifacts, audit_events).
- No business lifecycle orchestration (start_work, submit_fix, etc. belong to Phase 01H).
"""

from datetime import datetime
from datetime import timezone
import sqlite3
import json
import uuid
from typing import Dict, Any, Optional, List


class InvestigationRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.conn = connection

    # 1. Investigation Primitives
    def create_investigation(
        self,
        record_key: str,
        source_kind: str,
        slug: str,
        lifecycle_phase: str,
        original_input_id: str,
        investigation_id: Optional[str] = None,
        canonical_bug_id: Optional[str] = None,
        status: Optional[str] = None,
        classification: Optional[str] = None,
        module: str = "Not provided",
        severity: str = "Not provided",
        priority: str = "Not provided",
        assignee: Optional[str] = None,
        active_ticket_id: Optional[str] = None,
        resolution_json: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        ts_created = created_at or now
        ts_updated = updated_at or now

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO investigations (
                record_key, investigation_id, canonical_bug_id, source_kind,
                slug, lifecycle_phase, status, classification, module,
                severity, priority, assignee, original_input_id,
                active_ticket_id, resolution_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                record_key, investigation_id, canonical_bug_id, source_kind,
                slug, lifecycle_phase, status, classification, module,
                severity, priority, assignee, original_input_id,
                active_ticket_id, resolution_json, ts_created, ts_updated
            )
        )
        return self.get_investigation_by_record_key(record_key)

    def get_investigation_by_record_key(self, record_key: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM investigations WHERE record_key = ?;", (record_key,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_investigation_by_investigation_id(self, investigation_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM investigations WHERE investigation_id = ?;", (investigation_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_investigation_by_canonical_bug_id(self, canonical_bug_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM investigations WHERE canonical_bug_id = ?;", (canonical_bug_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_investigation_state(
        self,
        record_key: str,
        lifecycle_phase: str,
        status: Optional[str],
        updated_at: str,
        classification: Optional[str] = None,
        canonical_bug_id: Optional[str] = None,
        assignee: Optional[str] = None,
        active_ticket_id: Optional[str] = None,
        resolution_json: Optional[str] = None,
        module: Optional[str] = None,
        severity: Optional[str] = None,
        priority: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Updates the aggregate root investigation state columns.
        Used strictly by ResolutionService to persist state returned by the lifecycle engine.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE investigations SET
                lifecycle_phase = ?,
                status = ?,
                updated_at = ?,
                classification = COALESCE(?, classification),
                canonical_bug_id = COALESCE(?, canonical_bug_id),
                assignee = CASE WHEN ? IS NOT NULL THEN ? ELSE assignee END,
                active_ticket_id = COALESCE(?, active_ticket_id),
                resolution_json = COALESCE(?, resolution_json),
                module = COALESCE(?, module),
                severity = COALESCE(?, severity),
                priority = COALESCE(?, priority)
            WHERE record_key = ?;
            """,
            (
                lifecycle_phase,
                status,
                updated_at,
                classification,
                canonical_bug_id,
                assignee,
                assignee,
                active_ticket_id,
                resolution_json,
                module,
                severity,
                priority,
                record_key
            )
        )
        return self.get_investigation_by_record_key(record_key)

    # 2. Original Input Primitive (Immutable)
    def insert_original_input(
        self,
        input_id: str,
        investigation_key: str,
        tester_description: str,
        reporter: str,
        captured_at: str,
        initial_evidence_ids: List[str],
        provenance: str = "HUMAN_SUPPLIED"
    ) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO original_inputs (
                id, investigation_key, tester_description, reporter,
                captured_at, initial_evidence_ids_json, provenance
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                input_id, investigation_key, tester_description, reporter,
                captured_at, json.dumps(initial_evidence_ids), provenance
            )
        )
        cursor.execute("SELECT * FROM original_inputs WHERE id = ?;", (input_id,))
        return dict(cursor.fetchone())

    # 3. Evidence Metadata Primitive (Immutable)
    def insert_evidence(
        self,
        evidence_id: str,
        investigation_key: str,
        stage: str,
        evidence_type: str,
        original_filename: str,
        canonical_filename: str,
        storage_path: str,
        sha256: str,
        mime_type: str,
        byte_size: int,
        uploaded_by: str,
        captured_at: str,
        notes: Optional[str] = None,
        provenance: str = "HUMAN_SUPPLIED"
    ) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO evidence (
                id, investigation_key, stage, evidence_type, original_filename,
                canonical_filename, storage_path, sha256, mime_type, byte_size,
                uploaded_by, captured_at, notes, provenance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                evidence_id, investigation_key, stage, evidence_type, original_filename,
                canonical_filename, storage_path, sha256, mime_type, byte_size,
                uploaded_by, captured_at, notes, provenance
            )
        )
        cursor.execute("SELECT * FROM evidence WHERE id = ?;", (evidence_id,))
        return dict(cursor.fetchone())

    # 4. Append-Only Artifact Primitives
    def insert_ai_artifact(
        self,
        generation_id: str,
        investigation_key: str,
        purpose: str,
        model_identifier: str,
        input_evidence_ids: List[str],
        structured_output: Dict[str, Any],
        generated_at: str,
        optional_usage_metadata: Optional[Dict[str, Any]] = None,
        provenance: str = "AI_INFERENCE"
    ) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO ai_artifacts (
                generation_id, investigation_key, purpose, model_identifier,
                input_evidence_ids_json, structured_output_json,
                optional_usage_metadata_json, generated_at, provenance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                generation_id, investigation_key, purpose, model_identifier,
                json.dumps(input_evidence_ids), json.dumps(structured_output),
                json.dumps(optional_usage_metadata) if optional_usage_metadata else None,
                generated_at, provenance
            )
        )
        cursor.execute("SELECT * FROM ai_artifacts WHERE generation_id = ?;", (generation_id,))
        return dict(cursor.fetchone())

    def insert_research_artifact(
        self,
        research_id: str,
        investigation_key: str,
        research_question: str,
        trigger_reason: str,
        sources: List[Dict[str, Any]],
        observations: List[Dict[str, Any]],
        relevance_to_art: str,
        possible_art_approach: str,
        generated_at: str,
        provenance: str = "AI_RECOMMENDATION"
    ) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO research_artifacts (
                id, investigation_key, research_question, trigger_reason,
                sources_json, observations_json, relevance_to_art,
                possible_art_approach, generated_at, provenance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                research_id, investigation_key, research_question, trigger_reason,
                json.dumps(sources), json.dumps(observations), relevance_to_art,
                possible_art_approach, generated_at, provenance
            )
        )
        cursor.execute("SELECT * FROM research_artifacts WHERE id = ?;", (research_id,))
        return dict(cursor.fetchone())

    def insert_ticket_revision(
        self,
        ticket_id: str,
        investigation_key: str,
        revision: int,
        title: str,
        repro_steps: str,
        expected_result: str,
        actual_result: str,
        business_impact: str,
        recommended_solution: str,
        module: str,
        environment: str,
        severity: str,
        priority: str,
        tags: List[str],
        discussion: List[Dict[str, Any]],
        updated_at: str,
        provenance: str = "HUMAN_APPROVED"
    ) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO ticket_revisions (
                ticket_id, investigation_key, revision, title, repro_steps,
                expected_result, actual_result, business_impact, recommended_solution,
                module, environment, severity, priority, tags_json, discussion_json,
                provenance, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                ticket_id, investigation_key, revision, title, repro_steps,
                expected_result, actual_result, business_impact, recommended_solution,
                module, environment, severity, priority, json.dumps(tags), json.dumps(discussion),
                provenance, updated_at
            )
        )
        cursor.execute("SELECT * FROM ticket_revisions WHERE ticket_id = ?;", (ticket_id,))
        return dict(cursor.fetchone())

    def insert_developer_update(
        self,
        dev_id: str,
        investigation_key: str,
        developer_username: str,
        summary_of_changes: str,
        commit_hash_or_pr: Optional[str],
        resolved_in_version_or_branch: str,
        test_instructions_for_qa: str,
        submitted_at: str,
        provenance: str = "DEVELOPER_UPDATE"
    ) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO developer_updates (
                id, investigation_key, developer_username, summary_of_changes,
                commit_hash_or_pr, resolved_in_version_or_branch,
                test_instructions_for_qa, submitted_at, provenance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                dev_id, investigation_key, developer_username, summary_of_changes,
                commit_hash_or_pr, resolved_in_version_or_branch,
                test_instructions_for_qa, submitted_at, provenance
            )
        )
        cursor.execute("SELECT * FROM developer_updates WHERE id = ?;", (dev_id,))
        return dict(cursor.fetchone())

    def insert_retest_artifact(
        self,
        retest_id: str,
        investigation_key: str,
        retest_evidence_ids: List[str],
        human_confirmation: Dict[str, Any],
        executed_at: str,
        ai_recommendation: Optional[Dict[str, Any]] = None,
        provenance: str = "RETEST_VERIFICATION"
    ) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO retest_artifacts (
                id, investigation_key, retest_evidence_ids_json,
                ai_recommendation_json, human_confirmation_json,
                executed_at, provenance
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                retest_id, investigation_key, json.dumps(retest_evidence_ids),
                json.dumps(ai_recommendation) if ai_recommendation else None,
                json.dumps(human_confirmation), executed_at, provenance
            )
        )
        cursor.execute("SELECT * FROM retest_artifacts WHERE id = ?;", (retest_id,))
        return dict(cursor.fetchone())

    def insert_audit_event(
        self,
        event_id: str,
        investigation_key: str,
        timestamp: str,
        actor: str,
        event_type: str,
        summary: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO audit_events (
                id, investigation_key, timestamp, actor, event_type, summary, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                event_id, investigation_key, timestamp, actor, event_type, summary,
                json.dumps(details) if details else None
            )
        )
        cursor.execute("SELECT * FROM audit_events WHERE id = ?;", (event_id,))
        return dict(cursor.fetchone())

    # 5. Queries for Child Artifacts
    def list_evidence_for_investigation(self, investigation_key: str) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM evidence WHERE investigation_key = ? ORDER BY captured_at ASC;", (investigation_key,))
        return [dict(r) for r in cursor.fetchall()]

    def list_ticket_revisions_for_investigation(self, investigation_key: str) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM ticket_revisions WHERE investigation_key = ? ORDER BY revision ASC;", (investigation_key,))
        return [dict(r) for r in cursor.fetchall()]

    def list_audit_events_for_investigation(self, investigation_key: str) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM audit_events WHERE investigation_key = ? ORDER BY timestamp ASC;", (investigation_key,))
        return [dict(r) for r in cursor.fetchall()]
