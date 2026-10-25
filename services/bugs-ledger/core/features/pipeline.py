"""
core/features/pipeline.py

Unified ART Feature Backlog Pipeline.
Orchestrates Feature Intake (Harness 01) and Azure User Story Sync (Harness 02)
with zero manual handoff friction, duplicate prevention, and failure safety.
"""

from typing import Dict, Any, List, Optional, NamedTuple

from core.features.models import FeatureRecord, AzureSyncStatus
from core.features.storage import FeatureStorageManager
from core.features.intake import FeatureIntakeHarness, IntakeResult
from core.features.azure_sync import AzureFeatureSyncHarness, AzureSyncResult


class PipelineResult(NamedTuple):
    success: bool
    status: str  # COMPLETE, LOCAL_ONLY_COMPLETE, FAILED
    feature_id: Optional[str]
    title: Optional[str]
    module: Optional[str]
    classification: Optional[str]
    local_storage_path: Optional[str]
    work_item_id: Optional[int]
    work_item_url: Optional[str]
    parent_feature_id: Optional[int]
    azure_status: str  # NOT_RUN, CREATED, EXISTING, UPDATED, FAILED
    blocker: Optional[str] = None
    advisory: Optional[str] = None


class FeaturePipeline:
    """
    Unified Orchestrator for the Feature Backlog Pipeline.
    """

    def __init__(
        self,
        intake_harness: Optional[FeatureIntakeHarness] = None,
        sync_harness: Optional[AzureFeatureSyncHarness] = None,
        storage_manager: Optional[FeatureStorageManager] = None
    ):
        self.storage = storage_manager or FeatureStorageManager()
        self.intake = intake_harness or FeatureIntakeHarness(self.storage)
        self.sync = sync_harness or AzureFeatureSyncHarness(storage_manager=self.storage)

    def run(
        self,
        raw_input: Dict[str, Any],
        evidence_files: Optional[List[str]] = None,
        local_only: bool = False,
        assigned_to: Optional[str] = None,
        is_test: bool = False,
        dry_run: bool = False
    ) -> PipelineResult:
        """
        Executes the end-to-end feature pipeline:
        1. Harness 01: Ingest, structure, duplicate check, and save canonical feature.
        2. Gate: If failed or not ready for Azure, stops cleanly.
        3. Local-only: If local_only is True, stops cleanly without Azure mutation.
        4. Harness 02: Calls Azure sync with feature ID only.
        """
        # Step 1: Harness 01 Intake
        intake_res: IntakeResult = self.intake.process_intake(
            raw_input=raw_input,
            evidence_files=evidence_files,
            is_test=is_test
        )

        if not intake_res.success or not intake_res.record:
            return PipelineResult(
                success=False,
                status="FAILED",
                feature_id=intake_res.feature_id,
                title=raw_input.get("title"),
                module=raw_input.get("module"),
                classification=raw_input.get("classification"),
                local_storage_path=None,
                work_item_id=None,
                work_item_url=None,
                parent_feature_id=None,
                azure_status="NOT_RUN",
                blocker=f"Intake Harness failed: {intake_res.blocker}",
                advisory=intake_res.advisory
            )

        feature_id = intake_res.record.feature_id
        record = intake_res.record

        # Step 2: LOCAL_ONLY Gate
        if local_only:
            return PipelineResult(
                success=True,
                status="LOCAL_ONLY_COMPLETE",
                feature_id=feature_id,
                title=record.title,
                module=record.module,
                classification=record.classification,
                local_storage_path=intake_res.storage_path,
                work_item_id=record.azure_work_item_id,
                work_item_url=None,
                parent_feature_id=None,
                azure_status="NOT_RUN",
                advisory=intake_res.advisory
            )

        # Step 3: Azure Readiness Gate
        if not intake_res.ready_for_azure:
            return PipelineResult(
                success=False,
                status="FAILED",
                feature_id=feature_id,
                title=record.title,
                module=record.module,
                classification=record.classification,
                local_storage_path=intake_res.storage_path,
                work_item_id=None,
                work_item_url=None,
                parent_feature_id=None,
                azure_status="NOT_RUN",
                blocker=f"Feature is not ready for Azure synchronization: {intake_res.readiness_report or 'missing mandatory specification fields.'}",
                advisory=intake_res.advisory
            )

        # Step 4: Harness 02 Azure Sync
        sync_res: AzureSyncResult = self.sync.sync_feature(
            feature_id=feature_id,
            assigned_to=assigned_to,
            dry_run=dry_run
        )

        if not sync_res.success:
            return PipelineResult(
                success=False,
                status="FAILED",
                feature_id=feature_id,
                title=record.title,
                module=record.module,
                classification=record.classification,
                local_storage_path=intake_res.storage_path,
                work_item_id=record.azure_work_item_id,
                work_item_url=None,
                parent_feature_id=sync_res.parent_feature_id,
                azure_status="FAILED",
                blocker=f"Azure Ticket Harness failed: {sync_res.blocker}",
                advisory=intake_res.advisory
            )

        azure_action = "EXISTING" if sync_res.is_existing else "CREATED"

        return PipelineResult(
            success=True,
            status="COMPLETE",
            feature_id=feature_id,
            title=record.title,
            module=record.module,
            classification=record.classification,
            local_storage_path=intake_res.storage_path,
            work_item_id=sync_res.work_item_id,
            work_item_url=sync_res.work_item_url,
            parent_feature_id=sync_res.parent_feature_id,
            azure_status=azure_action,
            advisory=intake_res.advisory
        )
