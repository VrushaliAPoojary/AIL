"""
api/app.py

Phase 02A.1 / Phase 02B / Phase 02C / Phase 02D / Phase 02E — HTTP API Application
Provides a minimal FastAPI HTTP adapter for InvestigationQueryService and ResolutionService.

Safety Guarantees:
- Zero SQL, zero persistence logic, zero lifecycle rules in the HTTP adapter.
- Strictly controlled write routes: exactly FOUR business write endpoints:
  1. POST /api/v1/investigations (Capture)
  2. POST /api/v1/investigations/{investigation_id}/confirm (Confirm BUG)
  3. POST /api/v1/bugs/{canonical_bug_id}/start-work (Start Work / Developer Assignment)
  4. POST /api/v1/bugs/{canonical_bug_id}/submit-fix (Submit Fix / Retest Handoff)
- Write authority remains ResolutionService (atomic ID allocation + persistence + audit).
- Versioned routing under /api/v1/.
- Query validation preserving frozen contract enums and constraints.
- Predictable JSON error envelopes: {"error": {"code": "...", "message": "..."}}.
- Masked internal errors (zero tracebacks, SQL statements, or filesystem paths leaked).
- Configurable DB location via factory argument or ART_DB_PATH environment variable.
- Fails startup clearly if configured database file does not exist.
- Does not import legacy records or create production databases on import/startup.
"""

import os
import sqlite3
from typing import Dict, Any, List, Optional, Tuple

from fastapi import FastAPI, Request, Response, Query, Path, HTTPException, status
# pyrefly: ignore [missing-import]
from fastapi.responses import JSONResponse
# pyrefly: ignore [missing-import]
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.storage.db import get_connection
from core.storage.service import ResolutionService
from core.query.service import InvestigationQueryService, ALLOWED_SORT_FIELDS, ALLOWED_SORT_ORDERS
from api.models import (
    CaptureInvestigationRequest,
    ConfirmBugRequest,
    StartWorkRequest,
    SubmitFixRequest,
    RetestRequest,
    AzureDevOpsExportRequest,
    AzureDevOpsExportResponse
)
from core.storage.integrations import get_external_work_item, record_external_work_item
from integrations.azure_devops.models import (
    AzureDevOpsConfig,
    AzureDevOpsError,
    AzureFeatureRouter,
    ArtAssigneeRegistry
)
from integrations.azure_devops.client import AzureDevOpsClient

# Frozen Contract Enums (from contracts/schemas/common.json and investigation.json)
VALID_CLASSIFICATIONS = {"BUG", "PRODUCT_IMPROVEMENT", "COMPETITOR_INSIGHT", "PRODUCT_CONCEPT"}
VALID_LIFECYCLE_PHASES = {"CAPTURE", "INVESTIGATING", "CONFIRMED", "RESOLVED"}
VALID_STATUSES = {"OPEN", "FIXING", "RETEST", "VERIFIED", "CLOSED", "BLOCKED"}
VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "Not provided"}
VALID_PRIORITIES = {"P0", "P1", "P2", "P3", "Not provided"}
VALID_SOURCE_KINDS = {"NATIVE", "LEGACY_IMPORT"}


def _get_query_service(db_path: str) -> Tuple[sqlite3.Connection, InvestigationQueryService]:
    conn = get_connection(db_path)
    return conn, InvestigationQueryService(conn)


def create_app(db_path: Optional[str] = None) -> FastAPI:
    """
    Application factory for ART Product Resolution System HTTP API.
    Resolves db_path from parameter or ART_DB_PATH environment variable.
    Fails startup clearly if db_path is missing or non-existent.
    """
    resolved_path = db_path or os.environ.get("ART_DB_PATH")
    if not resolved_path:
        raise ValueError("Database path must be supplied to create_app or set in ART_DB_PATH environment variable.")
    if resolved_path != ":memory:" and not os.path.exists(resolved_path):
        raise FileNotFoundError(f"Configured database does not exist: {resolved_path}")

    app = FastAPI(
        title="ART Product Resolution System API",
        version="1.0.0",
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc"
    )

    # State
    app.state.db_path = resolved_path

    # =========================================================================
    # CENTRALIZED EXCEPTION HANDLERS (Preserve Option A Error Envelope)
    # =========================================================================

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        first_err = exc.errors()[0] if exc.errors() else {}
        loc = ".".join(str(l) for l in first_err.get("loc", []) if l not in {"query", "path", "body"})
        msg = first_err.get("msg", "Validation error")
        error_msg = f"{loc}: {msg}" if loc else msg
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "VALIDATION_ERROR", "message": error_msg}}
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        code_map = {
            400: "VALIDATION_ERROR",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            409: "CONFLICT",
            429: "RATE_LIMITED",
            500: "INTERNAL_ERROR",
            502: "EXTERNAL_SERVICE_ERROR",
            504: "GATEWAY_TIMEOUT"
        }
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        message = str(exc.detail) if exc.detail else "An error occurred."
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": code, "message": message}}
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        # Mask internal tracebacks, SQL statements, and filesystem paths
        error_msg = "Internal server error occurred."
        if "Corrupt record" in str(exc) or "Data corruption" in str(exc):
            error_msg = "Data corruption detected in stored record."
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": error_msg}}
        )

    # =========================================================================
    # WRITE ENDPOINTS (Phase 02B: Capture, Phase 02C: Confirm BUG, Phase 02D: Start Work, Phase 02E: Submit Fix)
    # =========================================================================

    @app.post("/api/v1/investigations", status_code=status.HTTP_201_CREATED)
    def capture_investigation(payload: CaptureInvestigationRequest, response: Response):
        """
        Captures a new investigation aggregate.
        Delegates atomic allocation and persistence entirely to ResolutionService.
        Returns the unified investigation detail read model and sets Location header.
        """
        conn = get_connection(app.state.db_path)
        try:
            res_service = ResolutionService(conn)

            kwargs: Dict[str, Any] = {
                "tester_description": payload.tester_description or "",
                "reporter": payload.reporter or "anonymous"
            }
            if payload.slug is not None:
                kwargs["slug"] = payload.slug
            if payload.initial_evidence_ids is not None:
                kwargs["initial_evidence_ids"] = payload.initial_evidence_ids

            service_result = res_service.create_investigation(**kwargs)
            if not service_result.success:
                error_detail = service_result.error or "Failed to capture investigation."
                if "requires description or initial evidence" in error_detail:
                    raise HTTPException(status_code=400, detail=error_detail)
                raise HTTPException(status_code=500, detail="Internal server error occurred.")

            inv_data = service_result.data
            inv_id = inv_data.get("investigation_id") if inv_data else None
            if not inv_id:
                raise HTTPException(status_code=500, detail="Internal server error occurred.")

            q_service = InvestigationQueryService(conn)
            detail = q_service.get_by_investigation_id(inv_id)
            if not detail:
                raise HTTPException(status_code=500, detail="Internal server error occurred.")

            response.headers["Location"] = f"/api/v1/investigations/{inv_id}"
            return {"investigation": detail}

        finally:
            conn.close()

    @app.post("/api/v1/investigations/{investigation_id}/confirm", status_code=status.HTTP_200_OK)
    def confirm_investigation(
        payload: ConfirmBugRequest,
        response: Response,
        investigation_id: str = Path(...)
    ):
        """
        Confirms an investigation as a canonical BUG.
        Allocates canonical ART-<MODULE>-### ID and creates approved TicketRevision 1.
        Delegates atomic state transition and persistence entirely to ResolutionService.
        """
        if not investigation_id or not investigation_id.startswith("INV-"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid investigation ID format '{investigation_id}'."
            )

        conn = get_connection(app.state.db_path)
        try:
            res_service = ResolutionService(conn)
            inv_row = res_service.repo.get_investigation_by_investigation_id(investigation_id)
            if not inv_row:
                raise HTTPException(
                    status_code=404,
                    detail=f"Investigation '{investigation_id}' not found."
                )

            record_key = inv_row["record_key"]

            ticket_data = {
                "title": payload.ticket.title,
                "reproSteps": payload.ticket.repro_steps,
                "expectedResult": payload.ticket.expected_result,
                "actualResult": payload.ticket.actual_result,
                "businessImpact": payload.ticket.business_impact,
                "recommendedSolution": payload.ticket.recommended_solution,
                "environment": payload.ticket.environment,
                "severity": payload.ticket.severity,
                "priority": payload.ticket.priority
            }
            if payload.ticket.tags is not None:
                ticket_data["tags"] = payload.ticket.tags
            if payload.ticket.discussion is not None:
                ticket_data["discussion"] = [d.model_dump() for d in payload.ticket.discussion]

            service_result = res_service.confirm_bug(
                record_key=record_key,
                module=payload.module,
                ticket_data=ticket_data,
                actor=payload.actor or "lead-qa"
            )

            if not service_result.success:
                error_detail = service_result.error or "Failed to confirm bug."
                if "is not an approved canonical module" in error_detail:
                    raise HTTPException(status_code=400, detail=error_detail)
                if "Cannot confirm investigation from lifecycle phase" in error_detail or "already" in error_detail.lower():
                    raise HTTPException(status_code=409, detail=error_detail)
                raise HTTPException(status_code=400, detail=error_detail)

            q_service = InvestigationQueryService(conn)
            detail = q_service.get_by_investigation_id(investigation_id)
            if not detail:
                raise HTTPException(status_code=500, detail="Internal server error occurred.")

            canonical_bug_id = detail.get("canonical_bug_id")
            if canonical_bug_id:
                response.headers["Location"] = f"/api/v1/bugs/{canonical_bug_id}"

            return {"investigation": detail}

        finally:
            conn.close()

    @app.post("/api/v1/bugs/{canonical_bug_id}/start-work", status_code=status.HTTP_200_OK)
    def start_work(
        payload: StartWorkRequest,
        response: Response,
        canonical_bug_id: str = Path(...)
    ):
        """
        Transitions a confirmed BUG from OPEN to FIXING and assigns the specified developer.
        Delegates atomic state transition and audit creation to ResolutionService.
        """
        if not canonical_bug_id or not canonical_bug_id.startswith("ART-"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid canonical bug ID format '{canonical_bug_id}'."
            )

        assignee = payload.assignee.strip()
        if not assignee:
            raise HTTPException(
                status_code=400,
                detail="Starting work requires a non-empty assignee."
            )

        conn = get_connection(app.state.db_path)
        try:
            res_service = ResolutionService(conn)
            inv_row = res_service.repo.get_investigation_by_canonical_bug_id(canonical_bug_id)
            if not inv_row:
                raise HTTPException(
                    status_code=404,
                    detail=f"Bug '{canonical_bug_id}' not found."
                )

            record_key = inv_row["record_key"]
            actor = payload.actor or assignee

            service_result = res_service.start_work(
                record_key=record_key,
                assignee=assignee,
                actor=actor
            )

            if not service_result.success:
                error_detail = service_result.error or "Failed to start work."
                if any(conflict_kw in error_detail for conflict_kw in ["Cannot start work", "Must be 'CONFIRMED'", "Must be 'OPEN'"]):
                    raise HTTPException(status_code=409, detail=error_detail)
                raise HTTPException(status_code=400, detail=error_detail)

            q_service = InvestigationQueryService(conn)
            detail = q_service.get_by_canonical_bug_id(canonical_bug_id)
            if not detail:
                raise HTTPException(status_code=500, detail="Internal server error occurred.")

            return {"investigation": detail}

        finally:
            conn.close()

    @app.post("/api/v1/bugs/{canonical_bug_id}/submit-fix", status_code=status.HTTP_200_OK)
    def submit_fix(
        payload: SubmitFixRequest,
        response: Response,
        canonical_bug_id: str = Path(...)
    ):
        """
        Submits a developer fix for a confirmed BUG currently in FIXING, transitioning it to RETEST.
        Persists DeveloperUpdate record and records FIX_SUBMITTED domain audit event atomically.
        """
        if not canonical_bug_id or not canonical_bug_id.startswith("ART-"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid canonical bug ID format '{canonical_bug_id}'."
            )

        developer_username = payload.developer_username.strip()
        summary_of_changes = payload.summary_of_changes.strip()
        resolved_in_version_or_branch = payload.resolved_in_version_or_branch.strip()
        test_instructions_for_qa = payload.test_instructions_for_qa.strip()

        if not all([developer_username, summary_of_changes, resolved_in_version_or_branch, test_instructions_for_qa]):
            raise HTTPException(
                status_code=400,
                detail="developer_username, summary_of_changes, resolved_in_version_or_branch, and test_instructions_for_qa must be non-empty strings."
            )

        conn = get_connection(app.state.db_path)
        try:
            res_service = ResolutionService(conn)
            inv_row = res_service.repo.get_investigation_by_canonical_bug_id(canonical_bug_id)
            if not inv_row:
                raise HTTPException(
                    status_code=404,
                    detail=f"Bug '{canonical_bug_id}' not found."
                )

            record_key = inv_row["record_key"]

            service_result = res_service.submit_fix(
                record_key=record_key,
                developer_username=developer_username,
                summary_of_changes=summary_of_changes,
                resolved_in_version_or_branch=resolved_in_version_or_branch,
                test_instructions_for_qa=test_instructions_for_qa,
                commit_hash_or_pr=payload.commit_hash_or_pr,
                actor=payload.actor or developer_username
            )

            if not service_result.success:
                error_detail = service_result.error or "Failed to submit fix."
                if any(conflict_kw in error_detail for conflict_kw in ["Cannot submit fix", "Must be 'FIXING'"]):
                    raise HTTPException(status_code=409, detail=error_detail)
                raise HTTPException(status_code=400, detail=error_detail)

            q_service = InvestigationQueryService(conn)
            detail = q_service.get_by_canonical_bug_id(canonical_bug_id)
            if not detail:
                raise HTTPException(status_code=500, detail="Internal server error occurred.")

            return {"investigation": detail}

        finally:
            conn.close()

    @app.post("/api/v1/bugs/{canonical_bug_id}/retest", status_code=status.HTTP_200_OK)
    def submit_retest(
        payload: RetestRequest,
        response: Response,
        canonical_bug_id: str = Path(...)
    ):
        """
        Submits a QA retest result for a confirmed BUG currently in RETEST.
        Persists RetestArtifact and records RETEST_EXECUTED domain audit event atomically.
        Does NOT perform human verification (status remains RETEST on PASSED, returns to FIXING on FAILED).
        """
        if not canonical_bug_id or not canonical_bug_id.startswith("ART-"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid canonical bug ID format '{canonical_bug_id}'."
            )

        if not payload.retest_evidence_ids:
            raise HTTPException(
                status_code=400,
                detail="retest_evidence_ids must contain at least one evidence ID reference."
            )

        actor = payload.actor.strip()
        if not actor:
            raise HTTPException(
                status_code=400,
                detail="actor must be a non-empty string."
            )

        conn = get_connection(app.state.db_path)
        try:
            res_service = ResolutionService(conn)
            inv_row = res_service.repo.get_investigation_by_canonical_bug_id(canonical_bug_id)
            if not inv_row:
                raise HTTPException(
                    status_code=404,
                    detail=f"Bug '{canonical_bug_id}' not found."
                )

            record_key = inv_row["record_key"]

            human_conf_dict = payload.human_confirmation.model_dump()
            ai_rec_dict = payload.ai_recommendation.model_dump() if payload.ai_recommendation else None

            service_result = res_service.submit_retest(
                record_key=record_key,
                retest_evidence_ids=payload.retest_evidence_ids,
                human_confirmation=human_conf_dict,
                actor=actor,
                ai_recommendation=ai_rec_dict
            )

            if not service_result.success:
                error_detail = service_result.error or "Failed to submit retest."
                if any(conflict_kw in error_detail for conflict_kw in [
                    "Cannot submit retest",
                    "Cannot evaluate retest",
                    "Must be 'RETEST'",
                    "SUBMIT_RETEST cannot establish VERIFIED status",
                    "Invalid retest human verdict"
                ]):
                    raise HTTPException(status_code=409, detail=error_detail)
                raise HTTPException(status_code=400, detail=error_detail)

            q_service = InvestigationQueryService(conn)
            detail = q_service.get_by_canonical_bug_id(canonical_bug_id)
            if not detail:
                raise HTTPException(status_code=500, detail="Internal server error occurred.")

            return {"investigation": detail}

        finally:
            conn.close()

    @app.post("/api/v1/bugs/{canonical_bug_id}/azure-devops", response_model=AzureDevOpsExportResponse, status_code=status.HTTP_200_OK)
    def export_to_azure_devops(
        response: Response,
        canonical_bug_id: str = Path(...),
        payload: Optional[AzureDevOpsExportRequest] = None
    ):
        """
        Creates an Azure DevOps Bug work item for a confirmed BUG ticket.
        If already exported, returns the existing external reference without creating duplicates.
        Supports optional assignee resolution via ArtAssigneeRegistry.
        """
        if not canonical_bug_id or not canonical_bug_id.startswith("ART-"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid canonical bug ID format '{canonical_bug_id}'."
            )

        conn = get_connection(app.state.db_path)
        try:
            q_service = InvestigationQueryService(conn)
            detail = q_service.get_by_canonical_bug_id(canonical_bug_id)
            if not detail:
                raise HTTPException(
                    status_code=404,
                    detail=f"Bug '{canonical_bug_id}' not found."
                )

            record_key = detail["record_key"]

            # 1. Local duplicate check
            existing = get_external_work_item(conn, record_key, system="AZURE_DEVOPS")
            if existing:
                return AzureDevOpsExportResponse(
                    canonical_bug_id=canonical_bug_id,
                    work_item_id=int(existing["external_id"]),
                    work_item_url=existing.get("external_url") or "",
                    created_at=existing["created_at"],
                    is_duplicate=True
                )

            current_ticket = detail.get("current_ticket")
            if not current_ticket:
                raise HTTPException(
                    status_code=400,
                    detail=f"Bug '{canonical_bug_id}' has no approved ticket revision to export."
                )

            # 2. Resolve parent Feature ID from ticket module (fail-closed if unconfigured)
            module_name = current_ticket.get("module") or detail.get("module")
            try:
                parent_feature_id = AzureFeatureRouter.resolve_feature_id(module_name)
            except AzureDevOpsError as ade:
                raise HTTPException(
                    status_code=ade.status_code,
                    detail=ade.message
                )

            # 3. Load configuration
            try:
                config = AzureDevOpsConfig.from_env()
            except ValueError as ve:
                raise HTTPException(
                    status_code=500,
                    detail=f"Azure DevOps integration configuration error: {str(ve)}"
                )

            # 4. Resolve optional assignee
            # Flow A: User provides assignee in request payload -> Resolve alias/full name -> Fail if unresolvable
            # Flow B: User provides no assignee in request payload -> assigned_to is None (Do not use default config unless explicitly provided)
            resolved_assignee = None
            if payload and payload.assignee is not None:
                try:
                    resolved_assignee = ArtAssigneeRegistry.resolve_assignee(payload.assignee)
                except AzureDevOpsError as ade:
                    raise HTTPException(
                        status_code=ade.status_code,
                        detail=ade.message
                    )

            # 5. Invoke Azure DevOps adapter with parent link and optional assignment
            client = AzureDevOpsClient(config)
            try:
                res = client.create_bug(
                    ticket=current_ticket,
                    canonical_bug_id=canonical_bug_id,
                    parent_work_item_id=parent_feature_id,
                    assigned_to=resolved_assignee
                )
            except AzureDevOpsError as ade:
                raise HTTPException(
                    status_code=ade.status_code,
                    detail=ade.message
                )

            # 5. Atomically persist external reference
            recorded = record_external_work_item(
                conn=conn,
                investigation_key=record_key,
                external_id=str(res.work_item_id),
                external_url=res.work_item_url,
                system="AZURE_DEVOPS",
                metadata={"canonical_bug_id": canonical_bug_id}
            )

            return AzureDevOpsExportResponse(
                canonical_bug_id=canonical_bug_id,
                work_item_id=int(recorded["external_id"]),
                work_item_url=recorded.get("external_url") or "",
                created_at=recorded["created_at"],
                is_duplicate=res.is_existing
            )

        finally:
            conn.close()

    # =========================================================================
    # BUSINESS READ ROUTES (GET ONLY)
    # =========================================================================

    @app.get("/api/v1/health")
    def health():
        conn, _ = _get_query_service(app.state.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            return {"status": "ok"}
        finally:
            conn.close()

    @app.get("/api/v1/investigations")
    def list_investigations(
        classification: Optional[str] = Query(None),
        lifecycle_phase: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        module: Optional[str] = Query(None),
        severity: Optional[str] = Query(None),
        priority: Optional[str] = Query(None),
        assignee: Optional[str] = Query(None),
        source_kind: Optional[str] = Query(None),
        search: Optional[str] = Query(None),
        limit: int = Query(50, ge=1, le=100),
        offset: int = Query(0, ge=0),
        sort: str = Query("updated_at"),
        direction: str = Query("DESC")
    ):
        filters: Dict[str, Any] = {}

        if classification is not None:
            if classification not in VALID_CLASSIFICATIONS:
                raise HTTPException(status_code=400, detail=f"Invalid classification '{classification}'.")
            filters["classification"] = classification

        if lifecycle_phase is not None:
            if lifecycle_phase not in VALID_LIFECYCLE_PHASES:
                raise HTTPException(status_code=400, detail=f"Invalid lifecycle_phase '{lifecycle_phase}'.")
            filters["lifecycle_phase"] = lifecycle_phase

        if status is not None:
            if status not in VALID_STATUSES:
                raise HTTPException(status_code=400, detail=f"Invalid status '{status}'.")
            filters["status"] = status

        if module is not None:
            filters["module"] = module

        if severity is not None:
            if severity not in VALID_SEVERITIES:
                raise HTTPException(status_code=400, detail=f"Invalid severity '{severity}'.")
            filters["severity"] = severity

        if priority is not None:
            if priority not in VALID_PRIORITIES:
                raise HTTPException(status_code=400, detail=f"Invalid priority '{priority}'.")
            filters["priority"] = priority

        if assignee is not None:
            filters["assignee"] = assignee

        if source_kind is not None:
            if source_kind not in VALID_SOURCE_KINDS:
                raise HTTPException(status_code=400, detail=f"Invalid source_kind '{source_kind}'.")
            filters["source_kind"] = source_kind

        if sort not in ALLOWED_SORT_FIELDS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sort field '{sort}'. Allowed: {', '.join(sorted(ALLOWED_SORT_FIELDS.keys()))}"
            )

        direction_upper = direction.upper()
        if direction_upper not in ALLOWED_SORT_ORDERS:
            raise HTTPException(status_code=400, detail="direction must be 'ASC' or 'DESC'.")

        conn, q_svc = _get_query_service(app.state.db_path)
        try:
            res = q_svc.list_all_records(
                filters=filters if filters else None,
                search_query=search,
                sort_by=sort,
                sort_order=direction_upper,
                limit=limit,
                offset=offset
            )
            return {
                "items": res.items,
                "limit": res.limit,
                "offset": res.offset,
                "total": res.total
            }
        finally:
            conn.close()

    @app.get("/api/v1/investigations/{investigation_id}")
    def get_by_investigation_id(investigation_id: str = Path(...)):
        if not investigation_id or not investigation_id.startswith("INV-"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid investigation ID format '{investigation_id}'."
            )

        conn, q_svc = _get_query_service(app.state.db_path)
        try:
            detail = q_svc.get_by_investigation_id(investigation_id)
            if not detail:
                raise HTTPException(
                    status_code=404,
                    detail=f"Investigation '{investigation_id}' not found."
                )
            return detail
        finally:
            conn.close()

    @app.get("/api/v1/bugs/{canonical_bug_id}")
    def get_by_canonical_bug_id(canonical_bug_id: str = Path(...)):
        if not canonical_bug_id or not canonical_bug_id.startswith("ART-"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid canonical bug ID format '{canonical_bug_id}'."
            )

        conn, q_svc = _get_query_service(app.state.db_path)
        try:
            detail = q_svc.get_by_canonical_bug_id(canonical_bug_id)
            if not detail:
                raise HTTPException(
                    status_code=404,
                    detail=f"Bug '{canonical_bug_id}' not found."
                )
            return detail
        finally:
            conn.close()

    @app.get("/api/v1/work/my")
    def list_my_work(
        assignee: Optional[str] = Query(None),
        limit: int = Query(50, ge=1, le=100),
        offset: int = Query(0, ge=0)
    ):
        if not assignee:
            raise HTTPException(status_code=400, detail="assignee query parameter is required.")

        conn, q_svc = _get_query_service(app.state.db_path)
        try:
            res = q_svc.list_my_work(developer_username=assignee, limit=limit, offset=offset)
            return {
                "items": res.items,
                "limit": res.limit,
                "offset": res.offset,
                "total": res.total
            }
        finally:
            conn.close()

    @app.get("/api/v1/retest")
    def list_retest_queue(
        limit: int = Query(50, ge=1, le=100),
        offset: int = Query(0, ge=0)
    ):
        conn, q_svc = _get_query_service(app.state.db_path)
        try:
            res = q_svc.list_retest_queue(limit=limit, offset=offset)
            return {
                "items": res.items,
                "limit": res.limit,
                "offset": res.offset,
                "total": res.total
            }
        finally:
            conn.close()

    @app.get("/api/v1/investigation-queue")
    def list_investigation_queue(
        limit: int = Query(50, ge=1, le=100),
        offset: int = Query(0, ge=0)
    ):
        conn, q_svc = _get_query_service(app.state.db_path)
        try:
            res = q_svc.list_investigation_queue(limit=limit, offset=offset)
            return {
                "items": res.items,
                "limit": res.limit,
                "offset": res.offset,
                "total": res.total
            }
        finally:
            conn.close()

    return app
