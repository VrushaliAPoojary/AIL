from typing import Dict, Tuple, List
from compiler.core.ir import Investigation, IRObject

class ChangeReport:
    def __init__(self):
        self.added: List[str] = []
        self.modified: List[str] = []
        self.removed: List[str] = []
        self.unchanged: List[str] = []

class ChangeDetector:
    def _build_id_map(self, inv: Investigation) -> Dict[str, IRObject]:
        mapping = {}
        for obj in inv.checkpoints + inv.evidence + inv.workflows + inv.claims + inv.sources + inv.sections + inv.relationships:
            mapping[obj.id] = obj
        return mapping

    def detect_changes(self, old_inv: Investigation, new_inv: Investigation) -> ChangeReport:
        report = ChangeReport()
        old_map = self._build_id_map(old_inv)
        new_map = self._build_id_map(new_inv)
        
        for obj_id, new_obj in new_map.items():
            if obj_id not in old_map:
                report.added.append(obj_id)
            else:
                old_obj = old_map[obj_id]
                # Compare content_hash and epistemic status
                if old_obj.content_hash != new_obj.content_hash or old_obj.epistemic_status != new_obj.epistemic_status:
                    report.modified.append(obj_id)
                else:
                    report.unchanged.append(obj_id)
                    
        for obj_id in old_map.keys():
            if obj_id not in new_map:
                report.removed.append(obj_id)
                
        return report
