"""
core/query/service.py

Phase 01J — Unified Application Read Model / Query Service
Provides application-facing read and query capabilities across both native investigations
and imported legacy bug snapshots using one unified, consistent interface.

Safety guarantees:
- READ-ONLY: Never initiates write transactions (BEGIN IMMEDIATE), mutates state, or allocates IDs.
- Deterministic display_id resolution:
    canonical_bug_id if present, else investigation_id.
- Never accesses or parses historical Markdown files during query execution.
- Respects active_ticket_id pointer for current ticket resolution.
- Deterministic ordering for historical child collections.
- Safe SQL parameterization for all search and filter queries.
- Whitelist-enforced sorting and bounded pagination.
- Handles non-BUG classifications with status = NULL without error.
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional, NamedTuple


ALLOWED_SORT_FIELDS = {
    "updated_at": "inv.updated_at",
    "created_at": "inv.created_at",
    "severity": "inv.severity",
    "status": "inv.status",
    "module": "inv.module",
    "lifecycle_phase": "inv.lifecycle_phase"
}

ALLOWED_SORT_ORDERS = {"ASC", "DESC"}


class PaginatedResult(NamedTuple):
    items: List[Dict[str, Any]]
    limit: int
    offset: int
    total: int


class InvestigationQueryService:
    """
    Application-level read/query service for investigations.
    Operates strictly read-only against the SQLite database.
    """

    def __init__(self, connection: sqlite3.Connection):
        self.conn = connection

    # =========================================================================
    # 1. DISPLAY ID AND SUMMARY MAPPING
    # =========================================================================

    @staticmethod
    def compute_display_id(canonical_bug_id: Optional[str], investigation_id: Optional[str]) -> str:
        """
        Deterministic display identifier rule:
        - For confirmed/promoted BUG: canonical_bug_id (e.g. ART-AGENT-001)
        - For unpromoted native investigation: investigation_id (e.g. INV-20260925-0001)
        - For legacy imported bug: canonical_bug_id (e.g. ART-GOV-003)
        
        Invariant:
        A persisted investigation must have at least one business identifier:
        NATIVE records have investigation_id, while LEGACY_IMPORT records have canonical_bug_id.
        """
        if canonical_bug_id:
            return canonical_bug_id
        if investigation_id:
            return investigation_id
        raise ValueError("Corrupt record: investigation has neither canonical_bug_id nor investigation_id.")

    def _row_to_summary(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        display_id = self.compute_display_id(d.get("canonical_bug_id"), d.get("investigation_id"))
        return {
            "display_id": display_id,
            "record_key": d["record_key"],
            "investigation_id": d["investigation_id"],
            "canonical_bug_id": d["canonical_bug_id"],
            "source_kind": d["source_kind"],
            "classification": d["classification"],
            "lifecycle_phase": d["lifecycle_phase"],
            "status": d["status"],
            "module": d["module"],
            "severity": d["severity"],
            "priority": d["priority"],
            "assignee": d["assignee"],
            "title": d.get("title") or "Not provided",
            "created_at": d["created_at"],
            "updated_at": d["updated_at"]
        }

    # =========================================================================
    # 2. DETAIL COMPOSITION
    # =========================================================================

    def get_investigation_detail(self, record_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the complete aggregate detail for an investigation by its internal record_key.
        Loads all child collections in deterministic order without loading binary evidence bytes.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM investigations WHERE record_key = ?;", (record_key,))
        inv_row = cursor.fetchone()
        if not inv_row:
            return None

        inv = dict(inv_row)
        display_id = self.compute_display_id(inv.get("canonical_bug_id"), inv.get("investigation_id"))

        # Original Input
        cursor.execute("SELECT * FROM original_inputs WHERE investigation_key = ?;", (record_key,))
        oi_row = cursor.fetchone()
        original_input = None
        if oi_row:
            original_input = dict(oi_row)
            original_input["initial_evidence_ids"] = json.loads(original_input.pop("initial_evidence_ids_json", "[]"))

        # Evidence List (Ordered by captured_at ASC, id ASC)
        cursor.execute(
            """
            SELECT id, stage, evidence_type, original_filename, canonical_filename,
                   storage_path, sha256, mime_type, byte_size, uploaded_by,
                   captured_at, notes, provenance
            FROM evidence
            WHERE investigation_key = ?
            ORDER BY captured_at ASC, id ASC;
            """,
            (record_key,)
        )
        evidence_list = [dict(r) for r in cursor.fetchall()]

        # AI Artifacts (Ordered by generated_at ASC, generation_id ASC)
        cursor.execute(
            """
            SELECT generation_id, purpose, model_identifier, input_evidence_ids_json,
                   structured_output_json, optional_usage_metadata_json, generated_at, provenance
            FROM ai_artifacts
            WHERE investigation_key = ?
            ORDER BY generated_at ASC, generation_id ASC;
            """,
            (record_key,)
        )
        ai_artifacts = []
        for r in cursor.fetchall():
            item = dict(r)
            item["input_evidence_ids"] = json.loads(item.pop("input_evidence_ids_json", "[]"))
            item["structured_output"] = json.loads(item.pop("structured_output_json", "{}"))
            usage = item.pop("optional_usage_metadata_json", None)
            item["optional_usage_metadata"] = json.loads(usage) if usage else None
            ai_artifacts.append(item)

        # Research Artifacts (Ordered by generated_at ASC, id ASC)
        cursor.execute(
            """
            SELECT id, research_question, trigger_reason, sources_json, observations_json,
                   relevance_to_art, possible_art_approach, generated_at, provenance
            FROM research_artifacts
            WHERE investigation_key = ?
            ORDER BY generated_at ASC, id ASC;
            """,
            (record_key,)
        )
        research_artifacts = []
        for r in cursor.fetchall():
            item = dict(r)
            item["sources"] = json.loads(item.pop("sources_json", "[]"))
            item["observations"] = json.loads(item.pop("observations_json", "[]"))
            research_artifacts.append(item)

        # Ticket Revisions (Ordered by revision ASC)
        cursor.execute(
            """
            SELECT ticket_id, revision, title, repro_steps, expected_result,
                   actual_result, business_impact, recommended_solution, module,
                   environment, severity, priority, tags_json, discussion_json,
                   provenance, updated_at
            FROM ticket_revisions
            WHERE investigation_key = ?
            ORDER BY revision ASC;
            """,
            (record_key,)
        )
        ticket_history = []
        current_ticket = None
        active_tck_id = inv.get("active_ticket_id")

        for r in cursor.fetchall():
            item = dict(r)
            item["tags"] = json.loads(item.pop("tags_json", "[]"))
            item["discussion"] = json.loads(item.pop("discussion_json", "[]"))
            ticket_history.append(item)
            if active_tck_id and item["ticket_id"] == active_tck_id:
                current_ticket = item

        # Developer Updates (Ordered by submitted_at ASC, id ASC)
        cursor.execute(
            """
            SELECT id, developer_username, summary_of_changes, commit_hash_or_pr,
                   resolved_in_version_or_branch, test_instructions_for_qa, submitted_at, provenance
            FROM developer_updates
            WHERE investigation_key = ?
            ORDER BY submitted_at ASC, id ASC;
            """,
            (record_key,)
        )
        developer_updates = [dict(r) for r in cursor.fetchall()]

        # Retest Artifacts (Ordered by executed_at ASC, id ASC)
        cursor.execute(
            """
            SELECT id, retest_evidence_ids_json, ai_recommendation_json,
                   human_confirmation_json, executed_at, provenance
            FROM retest_artifacts
            WHERE investigation_key = ?
            ORDER BY executed_at ASC, id ASC;
            """,
            (record_key,)
        )
        retest_artifacts = []
        for r in cursor.fetchall():
            item = dict(r)
            item["retest_evidence_ids"] = json.loads(item.pop("retest_evidence_ids_json", "[]"))
            ai_rec = item.pop("ai_recommendation_json", None)
            item["ai_recommendation"] = json.loads(ai_rec) if ai_rec else None
            item["human_confirmation"] = json.loads(item.pop("human_confirmation_json", "{}"))
            retest_artifacts.append(item)

        # Audit Events (Ordered by timestamp ASC, id ASC)
        cursor.execute(
            """
            SELECT id, timestamp, actor, event_type, summary, details_json
            FROM audit_events
            WHERE investigation_key = ?
            ORDER BY timestamp ASC, id ASC;
            """,
            (record_key,)
        )
        audit_events = []
        for r in cursor.fetchall():
            item = dict(r)
            details = item.pop("details_json", None)
            item["details"] = json.loads(details) if details else None
            audit_events.append(item)

        resolution = json.loads(inv["resolution_json"]) if inv.get("resolution_json") else None

        return {
            "display_id": display_id,
            "record_key": inv["record_key"],
            "investigation_id": inv["investigation_id"],
            "canonical_bug_id": inv["canonical_bug_id"],
            "source_kind": inv["source_kind"],
            "slug": inv["slug"],
            "lifecycle_phase": inv["lifecycle_phase"],
            "status": inv["status"],
            "classification": inv["classification"],
            "module": inv["module"],
            "severity": inv["severity"],
            "priority": inv["priority"],
            "assignee": inv["assignee"],
            "original_input_id": inv["original_input_id"],
            "active_ticket_id": inv["active_ticket_id"],
            "resolution": resolution,
            "created_at": inv["created_at"],
            "updated_at": inv["updated_at"],
            "original_input": original_input,
            "evidence": evidence_list,
            "ai_artifacts": ai_artifacts,
            "research_artifacts": research_artifacts,
            "current_ticket": current_ticket,
            "ticket_history": ticket_history,
            "developer_updates": developer_updates,
            "retest_artifacts": retest_artifacts,
            "audit_events": audit_events
        }

    # =========================================================================
    # 3. DIRECT IDENTIFIER LOOKUPS
    # =========================================================================

    def get_by_record_key(self, record_key: str) -> Optional[Dict[str, Any]]:
        return self.get_investigation_detail(record_key)

    def get_by_investigation_id(self, investigation_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT record_key FROM investigations WHERE investigation_id = ?;", (investigation_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return self.get_investigation_detail(row[0])

    def get_by_canonical_bug_id(self, canonical_bug_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT record_key FROM investigations WHERE canonical_bug_id = ?;", (canonical_bug_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return self.get_investigation_detail(row[0])

    def get_by_business_id(self, business_id: str) -> Optional[Dict[str, Any]]:
        """
        Looks up by canonical_bug_id first, then investigation_id.
        """
        detail = self.get_by_canonical_bug_id(business_id)
        if detail:
            return detail
        return self.get_by_investigation_id(business_id)

    # =========================================================================
    # 4. ALL RECORDS QUERY (FILTERS, SEARCH, PAGINATION, SORTING)
    # =========================================================================

    def list_all_records(
        self,
        filters: Optional[Dict[str, Any]] = None,
        search_query: Optional[str] = None,
        sort_by: str = "updated_at",
        sort_order: str = "DESC",
        limit: int = 50,
        offset: int = 0
    ) -> PaginatedResult:
        """
        Queries investigations with optional filtering, text search, sorting, and pagination.
        Performs lightweight single-join on active ticket revision to populate summary titles.
        """
        # Bounds checking on pagination
        safe_limit = max(1, min(limit, 100))
        safe_offset = max(0, offset)

        # Sort validation
        sort_col = ALLOWED_SORT_FIELDS.get(sort_by, "inv.updated_at")
        order_dir = sort_order.upper() if sort_order.upper() in ALLOWED_SORT_ORDERS else "DESC"

        where_clauses: List[str] = []
        params: List[Any] = []

        # Filters
        if filters:
            for k, v in filters.items():
                if v is None:
                    continue
                if k == "classification":
                    where_clauses.append("inv.classification = ?")
                    params.append(v)
                elif k == "lifecycle_phase":
                    where_clauses.append("inv.lifecycle_phase = ?")
                    params.append(v)
                elif k == "status":
                    where_clauses.append("inv.status = ?")
                    params.append(v)
                elif k == "module":
                    where_clauses.append("inv.module = ?")
                    params.append(v)
                elif k == "severity":
                    where_clauses.append("inv.severity = ?")
                    params.append(v)
                elif k == "priority":
                    where_clauses.append("inv.priority = ?")
                    params.append(v)
                elif k == "assignee":
                    where_clauses.append("inv.assignee = ?")
                    params.append(v)
                elif k == "source_kind":
                    where_clauses.append("inv.source_kind = ?")
                    params.append(v)

        # Search Query across: canonical_bug_id, investigation_id, ticket title, original tester description, module
        if search_query and search_query.strip():
            term = f"%{search_query.strip()}%"
            where_clauses.append(
                """(
                    inv.canonical_bug_id LIKE ? OR
                    inv.investigation_id LIKE ? OR
                    tck.title LIKE ? OR
                    oi.tester_description LIKE ? OR
                    inv.module LIKE ?
                )"""
            )
            params.extend([term, term, term, term, term])

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        # Count total
        count_sql = f"""
            SELECT COUNT(*)
            FROM investigations inv
            LEFT JOIN ticket_revisions tck ON inv.active_ticket_id = tck.ticket_id
            LEFT JOIN original_inputs oi ON inv.record_key = oi.investigation_key
            {where_sql};
        """
        cursor = self.conn.cursor()
        cursor.execute(count_sql, params)
        total = cursor.fetchone()[0]

        # Query items
        items_sql = f"""
            SELECT 
                inv.record_key,
                inv.investigation_id,
                inv.canonical_bug_id,
                inv.source_kind,
                inv.slug,
                inv.lifecycle_phase,
                inv.status,
                inv.classification,
                inv.module,
                inv.severity,
                inv.priority,
                inv.assignee,
                tck.title AS title,
                inv.created_at,
                inv.updated_at
            FROM investigations inv
            LEFT JOIN ticket_revisions tck ON inv.active_ticket_id = tck.ticket_id
            LEFT JOIN original_inputs oi ON inv.record_key = oi.investigation_key
            {where_sql}
            ORDER BY {sort_col} {order_dir}, inv.record_key ASC
            LIMIT ? OFFSET ?;
        """
        item_params = list(params) + [safe_limit, safe_offset]
        cursor.execute(items_sql, item_params)
        summaries = [self._row_to_summary(r) for r in cursor.fetchall()]

        return PaginatedResult(
            items=summaries,
            limit=safe_limit,
            offset=safe_offset,
            total=total
        )

    # =========================================================================
    # 5. SPECIALIZED WORK QUEUES
    # =========================================================================

    def list_my_work(self, developer_username: str, limit: int = 50, offset: int = 0) -> PaginatedResult:
        """
        Retrieves active developer work assigned to the specified developer.
        Active developer work in V1 canonical lifecycle is status = 'FIXING'.
        Excludes CLOSED, VERIFIED, RETEST, and unassigned records.
        """
        return self.list_all_records(
            filters={
                "assignee": developer_username,
                "status": "FIXING"
            },
            sort_by="updated_at",
            sort_order="DESC",
            limit=limit,
            offset=offset
        )

    def list_retest_queue(self, limit: int = 50, offset: int = 0) -> PaginatedResult:
        """
        Retrieves records currently requiring QA retest verification.
        Canonical status is 'RETEST'.
        """
        return self.list_all_records(
            filters={"status": "RETEST"},
            sort_by="updated_at",
            sort_order="DESC",
            limit=limit,
            offset=offset
        )

    def list_investigation_queue(self, limit: int = 50, offset: int = 0) -> PaginatedResult:
        """
        Retrieves records in CAPTURE or INVESTIGATING phases before promotion/confirmation.
        """
        cursor = self.conn.cursor()
        count_sql = """
            SELECT COUNT(*) FROM investigations inv
            WHERE inv.lifecycle_phase IN ('CAPTURE', 'INVESTIGATING');
        """
        cursor.execute(count_sql)
        total = cursor.fetchone()[0]

        safe_limit = max(1, min(limit, 100))
        safe_offset = max(0, offset)

        items_sql = """
            SELECT 
                inv.record_key,
                inv.investigation_id,
                inv.canonical_bug_id,
                inv.source_kind,
                inv.slug,
                inv.lifecycle_phase,
                inv.status,
                inv.classification,
                inv.module,
                inv.severity,
                inv.priority,
                inv.assignee,
                tck.title AS title,
                inv.created_at,
                inv.updated_at
            FROM investigations inv
            LEFT JOIN ticket_revisions tck ON inv.active_ticket_id = tck.ticket_id
            WHERE inv.lifecycle_phase IN ('CAPTURE', 'INVESTIGATING')
            ORDER BY inv.updated_at DESC, inv.record_key ASC
            LIMIT ? OFFSET ?;
        """
        cursor.execute(items_sql, (safe_limit, safe_offset))
        summaries = [self._row_to_summary(r) for r in cursor.fetchall()]

        return PaginatedResult(
            items=summaries,
            limit=safe_limit,
            offset=safe_offset,
            total=total
        )
