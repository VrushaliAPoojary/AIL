"""
core/features/intake.py

Feature Intake & Storage Harness (Harness 01 for Features)
Interprets feature requests, resolves modules, prevents duplicates,
allocates canonical IDs atomically, stores evidence once, and compiles ledger.
"""

import os
import re
from typing import Dict, Any, List, Optional, Tuple, NamedTuple
from difflib import SequenceMatcher

from core.repository.paths import resolve_feature_folder, FEATURE_ALIASES, CANONICAL_FEATURES
from core.identity.generator import generate_feature_id, FEATURE_MODULE_CODES
from core.features.models import (
    FeatureRecord,
    FeatureClassification,
)
from core.features.storage import FeatureStorageManager, slugify


class IntakeResult(NamedTuple):
    success: bool
    feature_id: Optional[str]
    is_existing: bool
    record: Optional[FeatureRecord]
    storage_path: Optional[str]
    ready_for_azure: bool
    blocker: Optional[str] = None
    advisory: Optional[str] = None
    readiness_report: Optional[str] = None


def compute_similarity(str1: str, str2: str) -> float:
    """Computes basic word-set and sequence similarity score [0.0 - 1.0]."""
    if not str1 or not str2:
        return 0.0
    s1, s2 = str1.lower().strip(), str2.lower().strip()
    sm = SequenceMatcher(None, s1, s2).ratio()
    tokens1 = set(re.findall(r"\w+", s1))
    tokens2 = set(re.findall(r"\w+", s2))
    if tokens1 and tokens2:
        jaccard = len(tokens1 & tokens2) / len(tokens1 | tokens2)
    else:
        jaccard = 0.0
    return max(sm, jaccard)


class FeatureIntakeHarness:
    """
    Production Feature Intake Harness.
    """

    def __init__(self, storage_manager: Optional[FeatureStorageManager] = None):
        self.storage = storage_manager or FeatureStorageManager()

    def resolve_module(self, raw_module: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """
        Resolves a user-provided module or alias to canonical feature name.
        Returns (canonical_feature_name, error_message).
        Fails closed on unknown or unapproved modules.
        """
        if not raw_module or not str(raw_module).strip():
            return None, "BLOCKED — UNKNOWN FEATURE MODULE: Module is required."

        from core.repository.registry import resolve_canonical_module
        try:
            canonical = resolve_canonical_module(raw_module)
            return canonical, None
        except ValueError:
            return None, f"BLOCKED — UNKNOWN FEATURE MODULE: '{raw_module}' is not an approved ART feature module."

    def check_duplicate(
        self,
        title: str,
        problem: str,
        module: str,
        threshold: float = 0.65
    ) -> Optional[Tuple[str, float, str]]:
        """
        Searches existing canonical feature records for near-duplicates.
        Returns (existing_feature_id, score, existing_title) if a duplicate is found.
        """
        all_features = self.storage.list_all_features()
        for feat in all_features:
            # If in the same module, check title and problem similarity
            if feat.module.lower() == module.lower() or feat.module == module:
                title_sim = compute_similarity(title, feat.title)
                prob_sim = compute_similarity(problem, feat.problem_opportunity)
                combined_score = max(title_sim, (title_sim * 0.7 + prob_sim * 0.3))
                if combined_score >= threshold:
                    return feat.feature_id, combined_score, feat.title

        return None

    def allocate_next_id(self, module: str, is_test: bool = False) -> str:
        """
        Allocates the next atomic, collision-resistant Feature ID.
        Inspects all existing on-disk records.
        """
        existing = [f.feature_id for f in self.storage.list_all_features()]
        norm_mod = FEATURE_MODULE_CODES.get(module.upper(), module.upper())
        return generate_feature_id(module=norm_mod, existing_ids=existing, is_test=is_test)

    def process_intake(
        self,
        raw_input: Dict[str, Any],
        evidence_files: Optional[List[str]] = None,
        is_test: bool = False
    ) -> IntakeResult:
        """
        Executes the feature intake process:
        1. Parse and validate input
        2. Resolve module
        3. Check duplicates or locate existing feature for update
        4. Allocate or preserve Feature ID
        5. Build canonical record and save to disk
        6. Determine readiness for Azure synchronization
        """
        title = (raw_input.get("title") or "").strip()
        raw_module = raw_input.get("module")
        existing_id = raw_input.get("feature_id") or raw_input.get("existing_feature_id")

        if not title:
            return IntakeResult(
                success=False,
                feature_id=None,
                is_existing=False,
                record=None,
                storage_path=None,
                ready_for_azure=False,
                blocker="Feature title is required."
            )

        # Module resolution
        canonical_module, mod_err = self.resolve_module(raw_module)
        if mod_err:
            return IntakeResult(
                success=False,
                feature_id=None,
                is_existing=False,
                record=None,
                storage_path=None,
                ready_for_azure=False,
                blocker=mod_err
            )

        # Classification check
        classification = raw_input.get("classification", FeatureClassification.NEW_FEATURE.value)
        if str(classification).upper() in ("ENHANCEMENT", "FEATURE_ENHANCEMENT", "IMPROVEMENT"):
            classification = FeatureClassification.ENHANCEMENT.value
        else:
            classification = FeatureClassification.NEW_FEATURE.value

        problem = (raw_input.get("problem_opportunity") or raw_input.get("description") or "").strip()
        current_behavior = (raw_input.get("current_behavior") or "").strip()
        proposed_behavior = (raw_input.get("proposed_behavior") or raw_input.get("expected_behavior") or "").strip()
        business_impact = (raw_input.get("business_impact") or "").strip()
        user_experience = (raw_input.get("user_experience") or "").strip()
        implementation_guidance = (raw_input.get("implementation_guidance") or "").strip()

        criteria = raw_input.get("acceptance_criteria") or []
        if isinstance(criteria, str):
            criteria = [c.strip() for c in criteria.splitlines() if c.strip()]

        related_bugs = raw_input.get("related_bugs") or []
        if isinstance(related_bugs, str):
            related_bugs = [b.strip() for b in related_bugs.split(",") if b.strip()]

        # Check existing vs new
        is_existing = False
        target_id = None

        if existing_id:
            clean_existing_id = str(existing_id).strip()
            existing_record = self.storage.load_feature(clean_existing_id)
            if not existing_record:
                return IntakeResult(
                    success=False,
                    feature_id=clean_existing_id,
                    is_existing=False,
                    record=None,
                    storage_path=None,
                    ready_for_azure=False,
                    blocker=(
                        f"Unknown feature ID '{clean_existing_id}' supplied for update. "
                        "Canonical records can only be updated if they already exist, and new identities must be issued by the allocator."
                    )
                )
            is_existing = True
            target_id = existing_record.feature_id
        else:
            # Check duplicate
            assert canonical_module is not None
            force_new = bool(raw_input.get("force_new"))
            if not force_new:
                dup = self.check_duplicate(title, problem, canonical_module)
                if dup:
                    dup_id, score, dup_title = dup
                    if raw_input.get("allow_update"):
                        # If moderate similarity (score < 0.85), require explicit confirmation
                        if score < 0.85 and not raw_input.get("confirmed_duplicate"):
                            return IntakeResult(
                                success=False,
                                feature_id=dup_id,
                                is_existing=True,
                                record=None,
                                storage_path=None,
                                ready_for_azure=False,
                                blocker=(
                                    f"Possible duplicate feature detected: '{dup_id}' ({dup_title}) with moderate similarity {score:.0%}. "
                                    "Manual review required to prevent accidental overwrite. "
                                    f"Specify 'confirmed_duplicate': True or pass 'feature_id': '{dup_id}' to update this record, "
                                    "or 'force_new': True to allocate a new distinct feature ID."
                                )
                            )
                        # Check module consistency on target record
                        target_rec = self.storage.load_feature(dup_id)
                        if target_rec and target_rec.module.lower() != canonical_module.lower():
                            return IntakeResult(
                                success=False,
                                feature_id=dup_id,
                                is_existing=True,
                                record=None,
                                storage_path=None,
                                ready_for_azure=False,
                                blocker=f"Cannot overwrite feature '{dup_id}' of module '{target_rec.module}' with request for module '{canonical_module}'."
                            )
                        is_existing = True
                        target_id = dup_id
                    else:
                        return IntakeResult(
                            success=False,
                            feature_id=dup_id,
                            is_existing=True,
                            record=None,
                            storage_path=None,
                            ready_for_azure=False,
                            blocker=(
                                f"Potential duplicate feature detected: '{dup_id}' ({dup_title}) with similarity {score:.0%}. "
                                "Specify 'allow_update': True (with confirmed_duplicate: True if moderate similarity) or provide feature_id to update, "
                                "or 'force_new': True to allocate a new distinct feature ID."
                            )
                        )

        if not target_id:
            assert canonical_module is not None
            target_id = self.allocate_next_id(canonical_module, is_test=is_test)

        slug = slugify(title)

        # Build FeatureRecord
        if is_existing and target_id:
            base_rec = self.storage.load_feature(target_id)
            if base_rec:
                record = base_rec
                record.title = title or record.title
                record.problem_opportunity = problem or record.problem_opportunity
                record.current_behavior = current_behavior or record.current_behavior
                record.proposed_behavior = proposed_behavior or record.proposed_behavior
                record.business_impact = business_impact or record.business_impact
                record.user_experience = user_experience or record.user_experience
                if criteria:
                    record.acceptance_criteria = criteria
                if implementation_guidance:
                    record.implementation_guidance = implementation_guidance
                if related_bugs:
                    record.related_bugs = list(set(record.related_bugs + related_bugs))
            else:
                assert canonical_module is not None
                record = FeatureRecord(
                    feature_id=target_id,
                    title=title,
                    module=canonical_module,
                    classification=classification,
                    problem_opportunity=problem,
                    current_behavior=current_behavior,
                    proposed_behavior=proposed_behavior,
                    business_impact=business_impact,
                    user_experience=user_experience,
                    acceptance_criteria=criteria,
                    implementation_guidance=implementation_guidance,
                    related_bugs=related_bugs,
                    slug=slug,
                )
        else:
            assert canonical_module is not None
            record = FeatureRecord(
                feature_id=target_id,
                title=title,
                module=canonical_module,
                classification=classification,
                problem_opportunity=problem,
                current_behavior=current_behavior,
                proposed_behavior=proposed_behavior,
                business_impact=business_impact,
                user_experience=user_experience,
                acceptance_criteria=criteria,
                implementation_guidance=implementation_guidance,
                related_bugs=related_bugs,
                slug=slug,
            )

        # Save feature to disk
        storage_path = self.storage.save_feature(record, source_evidence_files=evidence_files)

        # Check Azure readiness
        missing_fields = []
        if not (record.title and record.title.strip()):
            missing_fields.append("title")
        if not (record.module and record.module.strip()):
            missing_fields.append("module")
        if not (record.problem_opportunity and record.problem_opportunity.strip()):
            missing_fields.append("problem_opportunity")
        if not (record.proposed_behavior and record.proposed_behavior.strip()):
            missing_fields.append("proposed_behavior")
        if not record.acceptance_criteria or not any(str(c).strip() for c in record.acceptance_criteria):
            missing_fields.append("acceptance_criteria")

        ready_for_azure = (len(missing_fields) == 0)
        readiness_report = None
        if not ready_for_azure:
            readiness_report = f"Incomplete feature record for Azure synchronization. Missing required fields: {', '.join(missing_fields)}."

        # Defect warning advisory
        advisory = None
        lower_prob = (problem + " " + title).lower()
        if any(term in lower_prob for term in ["crash", "traceback", "nullpointer", "segfault", "500 internal server error"]):
            advisory = "Caution: Request contains severe defect terminology. Verify if this should be filed as a Bug instead."

        return IntakeResult(
            success=True,
            feature_id=record.feature_id,
            is_existing=is_existing,
            record=record,
            storage_path=storage_path,
            ready_for_azure=ready_for_azure,
            advisory=advisory,
            readiness_report=readiness_report
        )
