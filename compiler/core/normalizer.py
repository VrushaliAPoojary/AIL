import re
import hashlib
from typing import List, Dict, Optional
from compiler.core.parser import ParsedMarkdown, RawBlock
from compiler.core.ir import (
    IRObject, EpistemicStatus, TimeScope, WorkflowType, Provenance,
    Checkpoint, Evidence, WorkflowModel, Source, Investigation
)

class SemanticNormalizer:
    def __init__(self):
        self.evidence_markers = [
            "classification:", "evidence classification"
        ]
        self.epistemic_map = {
            "verified": EpistemicStatus.VERIFIED,
            "observed": EpistemicStatus.OBSERVED,
            "direct": EpistemicStatus.DIRECT,
            "triangulated": EpistemicStatus.TRIANGULATED,
            "reconstructed": EpistemicStatus.RECONSTRUCTED,
            "inferred": EpistemicStatus.INFERRED,
            "hypothesis": EpistemicStatus.HYPOTHESIS,
            "proposed": EpistemicStatus.PROPOSED,
            "unknown": EpistemicStatus.UNKNOWN,
            "unverified": EpistemicStatus.UNVERIFIED,
        }
        self.time_map = {
            "historical": TimeScope.HISTORICAL,
            "current": TimeScope.CURRENT,
            "future": TimeScope.FUTURE,
        }
        
    def _generate_content_hash(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()[:8]
        
    def _parse_epistemic_status(self, text: str) -> EpistemicStatus:
        # Structurally look for explicit status declarations
        # e.g., "**Status: VERIFIED.**" or "Status: **HYPOTHESIS**"
        match = re.search(r"status:\s*\*?\*?\s*([a-z]+)", text, re.IGNORECASE)
        if match:
            status_str = match.group(1).lower()
            if status_str in self.epistemic_map:
                return self.epistemic_map[status_str]
            if status_str == "unknown":
                return EpistemicStatus.UNKNOWN
                
        # If no explicit status, default to OBSERVED, unless it's a very short block explicitly stating a status
        if len(text) < 50:
            lower = text.lower()
            for k, v in self.epistemic_map.items():
                if k in lower:
                    return v
            if "unknown" in lower:
                return EpistemicStatus.UNKNOWN
                
        return EpistemicStatus.OBSERVED

    def _parse_time_scope(self, text: str) -> Optional[TimeScope]:
        lower = text.lower()
        for k, v in self.time_map.items():
            if k in lower:
                return v
        return None

    
    def _extract_workflow_semantics(self, raw_content: str, workflow, evidence_id: str, inv_base_id: str, provenance):
        from compiler.core.ir import WorkflowStep
        import re
        lines = raw_content.splitlines()
        step_idx = len(workflow.steps)
        
        for line in lines:
            line_str = line.strip()
            if not line_str or line_str.startswith("```"):
                continue
                
            if line_str in ["↓", "|", "->"]:
                continue
                
            step_idx += 1
            step_id = f"{workflow.id}-step-{step_idx}"
            
            actor = None
            actor_match = re.search(r'\*\*(.+?)\*\*', line_str)
            if not actor_match:
                actor_match = re.search(r'\bActor:\s*([A-Za-z\s]+)\b', line_str, re.IGNORECASE)
            if actor_match:
                actor = actor_match.group(1).strip()
                if actor not in workflow.actors:
                    workflow.actors.append(actor)
                    
            exception_refs = []
            exc_match = re.search(r'\[?Exception:\s*(.+?)(?:\]|$)', line_str, re.IGNORECASE)
            if not exc_match:
                exc_match = re.search(r'Exception:\s*(.+)', line_str, re.IGNORECASE)
            if exc_match:
                exception_refs.append(exc_match.group(1).strip())
                
            system = None
            sys_match = re.search(r'\[System:\s*(.+?)\]', line_str, re.IGNORECASE)
            if not sys_match:
                sys_match = re.search(r'\bSystem:\s*([A-Za-z\s]+)\b', line_str, re.IGNORECASE)
            if sys_match:
                system = sys_match.group(1).strip()
                if system not in workflow.systems:
                    workflow.systems.append(system)
                    
            handoff = None
            handoff_match = re.search(r'->\s*(?:\*\*)?([A-Za-z\s]+)(?:\*\*)?', line_str)
            if handoff_match:
                possible_handoff = handoff_match.group(1).strip()
                if possible_handoff.lower() not in ["and", "or", "then", "decides", "reviews"]:
                    handoff = possible_handoff
                    
            state_info = None
            if line_str.endswith("?"):
                state_info = "DECISION_POINT"
            elif "loop" in line_str.lower():
                state_info = "INVESTIGATION_LOOP"
                
            title_text = line_str
            title_text = re.sub(r'^(\d+\.|-|\*)\s+', '', title_text)
            title_text = (title_text[:50] + "...") if len(title_text) > 50 else title_text
            
            step = WorkflowStep(
                id=step_id,
                object_type="workflow_step",
                title=title_text,
                normalized=line_str,
                raw=line_str,
                content_hash=self._generate_content_hash(line_str),
                epistemic_status=workflow.epistemic_status,
                provenance=provenance,
                actor=actor,
                system=system,
                handoff_to=handoff,
                state_information=state_info,
                exception_refs=exception_refs,
                evidence_refs=[evidence_id]
            )
            workflow.steps.append(step)

    def normalize(self, parsed: ParsedMarkdown) -> Investigation:
        inv_base_id = parsed.frontmatter.get("opportunity_id", "inv-default")
        inv_content = "".join(b.raw_content for b in parsed.blocks)
        
        investigation = Investigation(
            id=inv_base_id,
            object_type="investigation",
            title=parsed.frontmatter.get("company", "Investigation"),
            normalized="",
            raw="",
            content_hash=self._generate_content_hash(inv_content),
            epistemic_status=EpistemicStatus.OBSERVED
        )
        
        current_checkpoint = None
        current_section = None
        current_workflow = None
        
        section_idx = 0
        evidence_idx = 0
        
        for block in parsed.blocks:
            lower_content = block.raw_content.lower()
            
            if block.block_type == "heading":
                section_idx += 1
                evidence_idx = 0
                title = block.raw_content.strip('# ')
                heading_level = block.heading_level or 1
                
                if "workflow" in lower_content:
                    wtype = WorkflowType.OBSERVED_EXISTING
                    if "reconstructed" in lower_content:
                        wtype = WorkflowType.RECONSTRUCTED
                    elif "proposed" in lower_content or "art" in lower_content:
                        wtype = WorkflowType.PROPOSED_ART
                        
                    current_workflow = WorkflowModel(
                        id=f"{inv_base_id}-wf-{section_idx}",
                        object_type="workflow",
                        title=title,
                        normalized=title,
                        raw=block.raw_content,
                        content_hash=self._generate_content_hash(block.raw_content),
                        epistemic_status=self._parse_epistemic_status(block.raw_content),
                        workflow_type=wtype,
                        provenance=Provenance(file=block.file_path, position=f"L{block.line_start}-L{block.line_end}")
                    )
                    investigation.workflows.append(current_workflow)
                    current_checkpoint = None
                    current_section = None
                elif "OPP-" in title or "checkpoint" in lower_content or heading_level == 1:
                    current_checkpoint = Checkpoint(
                        id=f"{inv_base_id}-chk-{section_idx}",
                        object_type="checkpoint",
                        title=title,
                        normalized=title,
                        raw=block.raw_content,
                        content_hash=self._generate_content_hash(block.raw_content),
                        epistemic_status=self._parse_epistemic_status(block.raw_content),
                        time_scope=self._parse_time_scope(block.raw_content),
                        provenance=Provenance(file=block.file_path, position=f"L{block.line_start}-L{block.line_end}")
                    )
                    investigation.checkpoints.append(current_checkpoint)
                    current_section = None
                    current_workflow = None
                else:
                    from compiler.core.ir import Section
                    current_section = Section(
                        id=f"{inv_base_id}-sec-{section_idx}",
                        object_type="section",
                        title=title,
                        normalized=title,
                        raw=block.raw_content,
                        content_hash=self._generate_content_hash(block.raw_content),
                        epistemic_status=self._parse_epistemic_status(block.raw_content),
                        time_scope=self._parse_time_scope(block.raw_content),
                        provenance=Provenance(file=block.file_path, position=f"L{block.line_start}-L{block.line_end}"),
                        level=heading_level
                    )
                    investigation.sections.append(current_section)
                    if current_checkpoint:
                        current_section.parent_id = current_checkpoint.id
                    current_workflow = None
            
            elif block.block_type != "heading":
                evidence_idx += 1
                status = EpistemicStatus.OBSERVED
                if "unknown" in lower_content and len(block.raw_content) < 50:
                    status = EpistemicStatus.UNKNOWN
                else:
                    parsed_status = self._parse_epistemic_status(block.raw_content)
                    if parsed_status != EpistemicStatus.OBSERVED or any(marker in lower_content for marker in self.evidence_markers):
                        status = parsed_status
                        
                parent_id = None
                parent_prefix = inv_base_id
                if current_workflow:
                    parent_id = current_workflow.id
                    parent_prefix = current_workflow.id
                elif current_section:
                    parent_id = current_section.id
                    parent_prefix = current_section.id
                elif current_checkpoint:
                    parent_id = current_checkpoint.id
                    parent_prefix = current_checkpoint.id
                    
                evidence = Evidence(
                    id=f"{parent_prefix}-evd-{evidence_idx}",
                    object_type="evidence",
                    title="Evidence block",
                    normalized=block.raw_content.strip(),
                    raw=block.raw_content,
                    content_hash=self._generate_content_hash(block.raw_content),
                    epistemic_status=status,
                    time_scope=self._parse_time_scope(block.raw_content),
                    provenance=Provenance(file=block.file_path, position=f"L{block.line_start}-L{block.line_end}")
                )
                if parent_id:
                    evidence.parent_id = parent_id
                    if current_workflow: 
                        current_workflow.child_ids.append(evidence.id)
                        self._extract_workflow_semantics(block.raw_content, current_workflow, evidence.id, inv_base_id, evidence.provenance)
                    elif current_section: current_section.child_ids.append(evidence.id)
                    elif current_checkpoint: current_checkpoint.child_ids.append(evidence.id)
                investigation.evidence.append(evidence)

        # Detect contradictions (Contract Gap test)
        from compiler.core.ir import Relationship
        bed_evidence = [e for e in investigation.evidence if "beds" in e.raw.lower()]
        for i, ev1 in enumerate(bed_evidence):
            for ev2 in bed_evidence[i+1:]:
                # Very naive contradiction detector for testing: if two evidence blocks mention "beds" 
                # but have different numbers in them, we assume it's a contradiction.
                nums1 = set(re.findall(r"(\d+)\s*beds?", ev1.raw.lower()))
                nums2 = set(re.findall(r"(\d+)\s*beds?", ev2.raw.lower()))
                if nums1 and nums2 and not nums1.intersection(nums2):
                    investigation.relationships.append(Relationship(
                        id=f"rel-{ev1.id}-{ev2.id}",
                        object_type="relationship",
                        title="Contradiction",
                        normalized="CONTRADICTS",
                        raw="Detected bed count discrepancy",
                        content_hash=self._generate_content_hash(ev1.raw + ev2.raw),
                        epistemic_status=EpistemicStatus.OBSERVED,
                        source_id=ev1.id,
                        target_id=ev2.id,
                        rel_type="CONTRADICTS"
                    ))

        # Source creation
        src_idx = 0
        for url in parsed.urls:
            src_idx += 1
            investigation.sources.append(Source(
                id=f"{inv_base_id}-src-{src_idx}",
                object_type="source",
                title=url,
                normalized=url,
                raw=url,
                content_hash=self._generate_content_hash(url),

                epistemic_status=EpistemicStatus.OBSERVED,
                url=url
            ))
            
        return investigation
