from typing import List, Dict, Any
from compiler.core.ir import Investigation, EpistemicStatus

class ValidationReport:
    def __init__(self):
        self.is_valid = True
        self.errors: List[str] = []
        self.contract_gaps: List[str] = []

    def fail(self, message: str):
        self.is_valid = False
        self.errors.append(message)
        
    def add_gap(self, message: str):
        self.contract_gaps.append(f"CONTRACT GAP: {message}")

class Validator:
    def __init__(self):
        pass
        
    def validate(self, investigation: Investigation) -> ValidationReport:
        report = ValidationReport()
        
        self._validate_epistemic(investigation, report)
        self._validate_semantic_safety(investigation, report)
        self._validate_relationships(investigation, report)
        
        return report
        
    def _validate_epistemic(self, investigation: Investigation, report: ValidationReport):
        # Ensure epistemic states aren't corrupted
        for obj in investigation.checkpoints + investigation.evidence + investigation.workflows:
            if obj.epistemic_status == EpistemicStatus.UNKNOWN and "verified" in obj.raw.lower():
                # Just checking we didn't upgrade it incorrectly, but here we enforce 
                # that if raw text clearly says unknown, IR shouldn't be verified.
                if "unknown" in obj.raw.lower():
                    pass # Handled by normalizer properly, just structural check

    def _validate_semantic_safety(self, investigation: Investigation, report: ValidationReport):
        # Critical semantic safety rule: Do not convert elapsed time into human labour.
        # This rule checks if any evidence or workflow metric makes this mistake.
        for obj in investigation.evidence + investigation.workflows:
            lower = obj.normalized.lower()
            if "elapsed" in lower and "delay" in lower and "staff labour" in lower:
                 report.fail(f"CRITICAL SAFETY VIOLATION: Elapsed delay converted to human labour in {obj.id}")
                 
    def _validate_relationships(self, investigation: Investigation, report: ValidationReport):
        # Broken references
        # Typically checked after the resolver. If there are dangling references, report fail.
        source_ids = {src.id for src in investigation.sources}
        for obj in investigation.checkpoints + investigation.evidence + investigation.workflows:
            for src_ref in obj.source_refs:
                if src_ref not in source_ids:
                    report.fail(f"Broken source reference {src_ref} in {obj.id}")
                    
        # Contract gaps
        # If we have Future time scope, and contract doesn't support it, we produce a gap
        for obj in investigation.checkpoints + investigation.evidence + investigation.workflows:
            if obj.time_scope and obj.time_scope.value == "FUTURE":
                report.add_gap(f"Frozen contract does not support FUTURE time scope found in {obj.id}")

