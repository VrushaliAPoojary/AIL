from typing import Dict, Any, List, Tuple, Optional
from compiler.validation.models import InvestigationBrief
from pydantic import ValidationError


def validate_candidate(data: Dict[str, Any]) -> Tuple[bool, List[Dict[str, str]], Optional[InvestigationBrief]]:
    errors: List[Dict[str, str]] = []

    try:
        brief = InvestigationBrief.model_validate(data)
    except ValidationError as e:
        for err in e.errors():
            loc = ".".join([str(l) for l in err["loc"]])
            errors.append({
                "stage": "VALIDATION",
                "error_code": "VALIDATION_SCHEMA_FAILED",
                "field_path": loc,
                "message": err["msg"]
            })
        return False, errors, None

    all_known_ids = set()

    def collect_ids(items, path_prefix=""):
        if not items:
            return
        for i, item in enumerate(items):
            if getattr(item, "id", None) in all_known_ids:
                errors.append({
                    "stage": "VALIDATION",
                    "error_code": "DUPLICATE_ID",
                    "object_id": item.id,
                    "field_path": f"{path_prefix}[{i}].id",
                    "message": "Duplicate ID found"
                })
            if getattr(item, "id", None):
                all_known_ids.add(item.id)

    collect_ids(brief.sources, "sources")
    collect_ids(brief.checkpoints, "checkpoints")
    collect_ids(brief.evidence, "evidence")
    collect_ids(brief.claims, "claims")
    collect_ids(brief.inferences, "inferences")
    collect_ids(brief.hypotheses, "hypotheses")
    collect_ids(brief.results, "results")
    collect_ids(brief.sections or [], "sections")
    collect_ids(brief.relationships or [], "relationships")
    collect_ids(brief.workflows or [], "workflows")
    collect_ids(brief.presentation.key_findings, "presentation.key_findings")
    collect_ids(brief.decision.reusable_intelligence, "decision.reusable_intelligence")
    for workflow in brief.workflows or []:
        collect_ids(workflow.steps, f"workflows[{workflow.id}].steps")

    if errors:
        return False, errors, None

    def check_refs(refs: List[str] | None, path: str, object_id: str):
        if refs is None:
            return
        for idx, ref in enumerate(refs):
            if ref not in all_known_ids:
                errors.append({
                    "stage": "VALIDATION",
                    "error_code": "VALIDATION_REFERENCE_FAILED",
                    "object_id": object_id,
                    "field_path": f"{path}[{idx}]",
                    "message": f"Referenced ID '{ref}' does not exist"
                })

    for i, kf in enumerate(brief.presentation.key_findings):
        check_refs(kf.source_refs, f"presentation.key_findings[{i}].source_refs", kf.id)

    for i, src in enumerate(brief.sources):
        check_refs(src.used_by, f"sources[{i}].used_by", src.id)

    for i, cp in enumerate(brief.checkpoints):
        check_refs(cp.evidence_refs, f"checkpoints[{i}].evidence_refs", cp.id)
        check_refs(cp.source_refs, f"checkpoints[{i}].source_refs", cp.id)

    for i, sec in enumerate(brief.sections or []):
        check_refs(sec.evidence_refs, f"sections[{i}].evidence_refs", sec.id)
        check_refs(sec.source_refs, f"sections[{i}].source_refs", sec.id)

    for i, wf in enumerate(brief.workflows or []):
        check_refs(wf.source_refs, f"workflows[{i}].source_refs", wf.id)
        for j, step in enumerate(wf.steps):
            check_refs(step.exception_refs, f"workflows[{i}].steps[{j}].exception_refs", step.id)
            check_refs(step.evidence_refs, f"workflows[{i}].steps[{j}].evidence_refs", step.id)
            check_refs(step.source_refs, f"workflows[{i}].steps[{j}].source_refs", step.id)

    for i, rel in enumerate(brief.relationships or []):
        if rel.source_id not in all_known_ids:
            errors.append({
                "stage": "VALIDATION",
                "error_code": "VALIDATION_REFERENCE_FAILED",
                "object_id": rel.id,
                "field_path": f"relationships[{i}].source_id",
                "message": f"Referenced ID '{rel.source_id}' does not exist"
            })
        if rel.target_id not in all_known_ids:
            errors.append({
                "stage": "VALIDATION",
                "error_code": "VALIDATION_REFERENCE_FAILED",
                "object_id": rel.id,
                "field_path": f"relationships[{i}].target_id",
                "message": f"Referenced ID '{rel.target_id}' does not exist"
            })

    for i, claim in enumerate(brief.claims):
        check_refs(claim.evidence_basis, f"claims[{i}].evidence_basis", claim.id)

    for i, inf in enumerate(brief.inferences):
        check_refs(inf.basis, f"inferences[{i}].basis", inf.id)

    for i, hyp in enumerate(brief.hypotheses):
        check_refs(hyp.supporting_basis, f"hypotheses[{i}].supporting_basis", hyp.id)
        check_refs(hyp.falsification_basis, f"hypotheses[{i}].falsification_basis", hyp.id)

    if brief.decision and brief.decision.reusable_intelligence:
        for i, intel in enumerate(brief.decision.reusable_intelligence):
            check_refs(intel.source_refs, f"decision.reusable_intelligence[{i}].source_refs", intel.id)

    if brief.falsification:
        for i, f in enumerate(brief.falsification):
            check_refs(f.basis, f"falsification[{i}].basis", f.statement)
            if f.targetRef:
                if f.targetRef not in all_known_ids:
                    errors.append({
                        "stage": "VALIDATION",
                        "error_code": "VALIDATION_REFERENCE_FAILED",
                        "object_id": f.statement,
                        "field_path": f"falsification[{i}].targetRef",
                        "message": f"Referenced ID '{f.targetRef}' does not exist"
                    })

    if errors:
        return False, errors, None

    return True, [], brief
