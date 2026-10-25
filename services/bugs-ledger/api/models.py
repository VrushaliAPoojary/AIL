"""
api/models.py

Typed request and response models for the HTTP API layer.
Phase 02B: Capture Investigation Request Model.
Phase 02C: Confirm BUG Request Model.
Phase 02D: Start Work Request Model.
"""

from typing import Optional, List, Literal
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field, ConfigDict


class CaptureInvestigationRequest(BaseModel):
    """
    Request model for POST /api/v1/investigations.
    Matches the actual ResolutionService.create_investigation inputs:
    - tester_description: raw unedited text entered by the tester (or None/empty if evidence provided)
    - reporter: username or identifier of reporting human
    - slug: human-readable URL slug for investigation
    - initial_evidence_ids: optional list of existing evidence IDs
    """
    model_config = ConfigDict(extra="forbid")

    tester_description: Optional[str] = Field(None, description="Raw unedited text entered by the tester.")
    reporter: Optional[str] = Field(None, description="Username or identifier of reporting human.")
    slug: Optional[str] = Field(None, description="URL slug for the investigation.")
    initial_evidence_ids: Optional[List[str]] = Field(None, description="List of pre-registered evidence IDs.")


class DiscussionEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    author: str = Field(..., description="Author of the discussion entry.")
    message: str = Field(..., description="Message text.")
    timestamp: str = Field(..., description="ISO timestamp.")


class ApprovedTicketPayload(BaseModel):
    """
    Structured approved ticket payload representing the 12 frozen ticket fields:
    1. title
    2. reproSteps
    3. expectedResult
    4. actualResult
    5. businessImpact
    6. recommendedSolution
    7. module
    8. environment
    9. severity
    10. priority
    11. tags
    12. discussion
    """
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., description="Title of the bug.")
    repro_steps: Optional[str] = Field("Not provided", alias="reproSteps", description="Steps to reproduce.")
    expected_result: Optional[str] = Field("Not provided", alias="expectedResult", description="Expected system behavior.")
    actual_result: Optional[str] = Field("Not provided", alias="actualResult", description="Actual observed behavior.")
    business_impact: Optional[str] = Field("Not provided", alias="businessImpact", description="Business or operational impact.")
    recommended_solution: Optional[str] = Field("Not provided", alias="recommendedSolution", description="Recommended technical fix.")
    environment: Optional[str] = Field("Not provided", description="Test environment.")
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "Not provided"] = Field("HIGH", description="Bug severity.")
    priority: Literal["P0", "P1", "P2", "P3", "Not provided"] = Field("Not provided", description="Bug priority.")
    tags: Optional[List[str]] = Field(None, description="Categorization tags.")
    discussion: Optional[List[DiscussionEntry]] = Field(None, description="Threaded discussions.")


class ConfirmBugRequest(BaseModel):
    """
    Request model for POST /api/v1/investigations/{investigation_id}/confirm.
    Matches the actual ResolutionService.confirm_bug inputs:
    - module: canonical module code ("AGENT", "GOV", "SFN")
    - ticket: approved ticket payload
    - actor: human or authority executing the confirmation
    """
    model_config = ConfigDict(extra="forbid")

    module: str = Field(..., description="Canonical module code ('AGENT', 'GOV', 'SFN').")
    ticket: ApprovedTicketPayload = Field(..., description="Approved ticket revision 1 payload.")
    actor: Optional[str] = Field("lead-qa", description="Human or authority approving confirmation.")


class StartWorkRequest(BaseModel):
    """
    Request model for POST /api/v1/bugs/{canonical_bug_id}/start-work.
    Matches the actual ResolutionService.start_work inputs:
    - assignee: developer username accepting the work
    - actor: human or authority performing the assignment
    """
    model_config = ConfigDict(extra="forbid")

    assignee: str = Field(..., min_length=1, description="Developer username taking ownership of the bug.")
    actor: Optional[str] = Field(None, description="Human or authority initiating the start work action.")


class SubmitFixRequest(BaseModel):
    """
    Request model for POST /api/v1/bugs/{canonical_bug_id}/submit-fix.
    Matches the actual ResolutionService.submit_fix inputs:
    - developer_username: developer submitting the fix
    - summary_of_changes: description of what was changed
    - resolved_in_version_or_branch: git branch or build version containing fix
    - test_instructions_for_qa: instructions for QA retesting
    - commit_hash_or_pr: optional commit SHA or pull request reference
    - actor: optional actor name (defaults to developer_username in service)
    """
    model_config = ConfigDict(extra="forbid")

    developer_username: str = Field(..., min_length=1, description="Developer username submitting the fix.")
    summary_of_changes: str = Field(..., min_length=1, description="Description of the changes made.")
    resolved_in_version_or_branch: str = Field(..., min_length=1, description="Branch or release version containing the fix.")
    test_instructions_for_qa: str = Field(..., min_length=1, description="Clear instructions for QA to test the fix.")
    commit_hash_or_pr: Optional[str] = Field(None, description="Optional commit hash or pull request link/reference.")
    actor: Optional[str] = Field(None, description="Optional actor identifier.")


class HumanConfirmationPayload(BaseModel):
    """
    Human verification/finding payload matching RetestArtifact.humanConfirmation contract.
    """
    model_config = ConfigDict(extra="forbid")

    confirmed: bool = Field(..., description="Whether human confirmation was performed.")
    verdict: str = Field(..., min_length=1, description="Retest verdict ('PASSED', 'FAILED', 'INCONCLUSIVE', 'VERIFIED', 'RETURNED_TO_FIXING', 'BLOCKED').")
    confirmedBy: str = Field(..., min_length=1, description="Tester or authority who confirmed the result.")
    notes: str = Field(..., description="Tester observation notes.")


class AIRecommendationPayload(BaseModel):
    """
    Optional AI comparison recommendation payload matching RetestArtifact.aiComparisonRecommendation contract.
    """
    model_config = ConfigDict(extra="forbid")

    recommendation: str = Field(..., description="AI comparison verdict ('PASSED', 'FAILED', 'INCONCLUSIVE').")
    notes: str = Field(..., description="AI comparison analysis notes.")


class RetestRequest(BaseModel):
    """
    Request model for POST /api/v1/bugs/{canonical_bug_id}/retest.
    Matches the actual ResolutionService.submit_retest inputs:
    - retest_evidence_ids: list of evidence reference IDs (minItems: 1)
    - human_confirmation: human confirmation and verdict finding
    - actor: identifier of the actor executing the retest
    - ai_recommendation: optional AI recommendation
    """
    model_config = ConfigDict(extra="forbid")

    retest_evidence_ids: List[str] = Field(..., min_length=1, description="List of retest evidence reference IDs (at least 1 required).")
    human_confirmation: HumanConfirmationPayload = Field(..., description="Human confirmation and verdict.")
    actor: str = Field(..., min_length=1, description="Actor submitting the retest.")
    ai_recommendation: Optional[AIRecommendationPayload] = Field(None, description="Optional AI comparison recommendation.")


class AzureDevOpsExportRequest(BaseModel):
    """
    Optional request payload for POST /api/v1/bugs/{canonical_bug_id}/azure-devops.
    Allows specifying an assignee (alias or full name) resolved via ArtAssigneeRegistry.
    If omitted or empty, bug is created unassigned.
    """
    model_config = ConfigDict(extra="forbid")

    assignee: Optional[str] = Field(None, description="Optional assignee alias (e.g. 'Karthik', 'Unnikkannan') or verified identity.")


class AzureDevOpsExportResponse(BaseModel):
    """
    Response model for POST /api/v1/bugs/{canonical_bug_id}/azure-devops.
    Returns the persisted external Azure DevOps Work Item reference.
    """
    canonical_bug_id: str = Field(..., description="Canonical ART Bug ID.")
    work_item_id: int = Field(..., description="Azure DevOps Work Item ID.")
    work_item_url: str = Field(..., description="Azure DevOps Work Item Web URL.")
    created_at: str = Field(..., description="Timestamp when the work item was linked/created.")
    is_duplicate: bool = Field(False, description="True if this bug had already been exported and the existing reference was returned.")



