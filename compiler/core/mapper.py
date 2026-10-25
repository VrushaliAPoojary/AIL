from typing import Dict, Any, List, Tuple
from compiler.core.ir import Investigation, IRObject, EpistemicStatus, WorkflowModel, Checkpoint

class ContractMapper:
    def __init__(self):
        self.gaps = []
        self.omissions = []
        self.transformed = []
        self.preserved = []

    def _map_provenance(self, obj: IRObject) -> Dict[str, Any]:
        if not obj.provenance:
            result = {
                "source_file": "UNKNOWN",
                "section": "UNKNOWN",
                "line_start": None,
                "line_end": None
            }
            obj_url = getattr(obj, "url", None)
            if obj_url:
                result["url"] = obj_url
            return result
        
        # Try to parse "L10-L15"
        l_start = None
        l_end = None
        if obj.provenance.position and obj.provenance.position.startswith("L"):
            parts = obj.provenance.position.replace("L", "").split("-")
            try:
                l_start = int(parts[0])
                if len(parts) > 1:
                    l_end = int(parts[1])
            except ValueError:
                pass

        result = {
            "source_file": obj.provenance.file or "UNKNOWN",
            "section": obj.provenance.section or "UNKNOWN",
            "line_start": l_start,
            "line_end": l_end
        }
        if getattr(obj.provenance, "url", None):
            result["url"] = obj.provenance.url
        obj_url = getattr(obj, "url", None)
        if obj_url:
            result["url"] = obj_url
        return result

    def _map_epistemic(self, status: EpistemicStatus) -> str:
        # Schema only supports certain epistemic classifications, but the prompt says 
        # "Never convert... inferred -> observed, etc"
        # Wait, the contract for EpistemicClassification is:
        # ["EVIDENCE", "CLAIM", "INFERENCE", "HYPOTHESIS", "FALSIFICATION", "RESULT", "DECISION"]
        # But for 'IntelligenceEvidenceStatus': ["VERIFIED", "PARTIAL", "HYPOTHESIS", "UNKNOWN", "REJECTED"]
        # For evidence blocks, the schema field is 'classification': type string (not enum restricted!)
        return status.value

    def map_investigation(self, inv: Investigation) -> Tuple[Dict[str, Any], List[str]]:
        self.gaps = []
        self.omissions = []
        self.transformed = []
        self.preserved = []

        # Start building the InvestigationBrief.json
        output = {
            "investigation_id": inv.id,
            "company": inv.title,
            "industry": "UNKNOWN", # Need to extract from frontmatter if possible
            "opportunity": inv.id.split('-')[1] if '-' in inv.id else "UNKNOWN",
            "investigation_type": "Specific Hospital + Workflow Discovery",
            "research_status": "UNKNOWN",
            "primary_question": "UNKNOWN",
            "presentation": {
                "investigation_summary": "Auto-generated summary from compiler.",
                "key_findings": []
            },
            "decision": {
                "decision": "UNKNOWN",
                "reason": "UNKNOWN",
                "reusable_intelligence": [],
                "provenance": {
                    "source_file": "UNKNOWN",
                    "section": "UNKNOWN",
                    "line_start": None,
                    "line_end": None
                }
            },
            "sources": [],
            "checkpoints": [],
            "evidence": [],
            "claims": [],
            "inferences": [],
            "hypotheses": [],
            "results": [],
            "traceability": [],
            "workflows": [],
            "sections": [],
            "relationships": []
        }

        # Map Workflows
        if inv.workflows:
            for wf in inv.workflows:
                self.preserved.append(f"Workflow '{wf.id}' mapped.")
                w_type = wf.workflow_type.name
                if w_type == "OBSERVED_EXISTING":
                    w_type = "OBSERVED"
                
                steps = [
                    {k: v for k, v in {
                        "id": s.id,
                        "title": s.title,
                        "description": s.raw,
                        "actor": s.actor,
                        "system": s.system,
                        "handoff_to": s.handoff_to,
                        "state_information": s.state_information,
                        "exception_refs": s.exception_refs,
                        "evidence_refs": s.evidence_refs,
                        "source_refs": getattr(s, 'source_refs', []),
                        "provenance": self._map_provenance(s)
                    }.items() if v is not None} for s in getattr(wf, 'steps', [])
                ]
                output["workflows"].append({
                    "id": wf.id,
                    "title": wf.title,
                    "workflow_type": w_type,
                    "summary": "UNKNOWN",
                    "steps": steps,
                    "nodes": steps,
                    "actors": getattr(wf, 'actors', []),
                    "systems": getattr(wf, 'systems', []),
                    "safety_boundaries": getattr(wf, 'safety_boundaries', []),
                    "source_refs": getattr(wf, 'source_refs', []),
                    "provenance": self._map_provenance(wf)
                })

        # Map Sections
        if getattr(inv, "sections", None):
            for sec in inv.sections:
                self.preserved.append(f"Section '{sec.id}' mapped.")
                output["sections"].append({
                    "id": sec.id,
                    "title": sec.title,
                    "summary": "UNKNOWN",
                    "evidence_refs": sec.child_ids,
                    "source_refs": getattr(sec, 'source_refs', []),
                    "provenance": self._map_provenance(sec)
                })

        # Map Relationships
        if getattr(inv, "relationships", None):
            for rel in inv.relationships:
                self.preserved.append(f"Relationship '{rel.id}' mapped.")
                output["relationships"].append({
                    "id": rel.id,
                    "source_id": rel.source_id,
                    "target_id": rel.target_id,
                    "relationship_type": rel.rel_type,
                    "source_refs": getattr(rel, 'source_refs', []),
                    "provenance": self._map_provenance(rel)
                })

        # Map Checkpoints
        for chk in inv.checkpoints:
            self.preserved.append(f"Checkpoint '{chk.id}' mapped.")
            output["checkpoints"].append({
                "id": chk.id,
                "title": chk.title,
                "status": "UNKNOWN",
                "investigation_question": chk.question or "UNKNOWN",
                "tested": "UNKNOWN",
                "found": chk.discovered or "UNKNOWN",
                "what_changed": chk.state_changed or "UNKNOWN",
                "resulting_state": "UNKNOWN",
                "evidence_refs": chk.child_ids,
                "source_refs": getattr(chk, 'source_refs', []),
                "provenance": self._map_provenance(chk)
            })

        # Map Sources
        for src in inv.sources:
            self.preserved.append(f"Source '{src.id}' mapped.")
            output["sources"].append({
                "id": src.id,
                "title": src.title,
                "url": src.url,
                "source_type": src.source_type or "URL",
                "used_by": []
            })
            
        # Map Evidence
        for evd in inv.evidence:
            self.preserved.append(f"Evidence '{evd.id}' mapped.")
            output["evidence"].append({
                "id": evd.id,
                "statement": evd.raw,
                "classification": self._map_epistemic(evd.epistemic_status),
                "source": "UNKNOWN",
                "provenance": self._map_provenance(evd)
            })

        return output, self.gaps
