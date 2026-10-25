import re
from typing import List
from compiler.core.ir import Investigation

class ToolReferenceFirewall:
    def __init__(self):
        # Patterns for typical temporary references injected by LLMs or search tools
        self.blocklist_patterns = [
            re.compile(r"\[\d+\]"),  # [1], [2] citation markers
            re.compile(r"search_id:[\w\-]+", re.IGNORECASE),
            re.compile(r"citation_id:[\w\-]+", re.IGNORECASE),
            re.compile(r"retrieval_id:[\w\-]+", re.IGNORECASE),
            re.compile(r"nav_token:[\w\-]+", re.IGNORECASE),
            re.compile(r"tool_result:[\w\-]+", re.IGNORECASE),
            re.compile(r"<!--[\s\S]*?-->"), # HTML comments used for temp refs
        ]
        
    def _sanitize_text(self, text: str) -> str:
        if not text:
            return text
        sanitized = text
        for pattern in self.blocklist_patterns:
            sanitized = pattern.sub("", sanitized)
        return sanitized.strip()

    def apply_firewall(self, investigation: Investigation) -> Investigation:
        def sanitize_obj(obj):
            obj.title = self._sanitize_text(obj.title)
            obj.normalized = self._sanitize_text(obj.normalized)
            obj.raw = self._sanitize_text(obj.raw)
            
        for checkpoint in investigation.checkpoints:
            sanitize_obj(checkpoint)
        for evidence in investigation.evidence:
            sanitize_obj(evidence)
        for workflow in investigation.workflows:
            sanitize_obj(workflow)
        for claim in investigation.claims:
            sanitize_obj(claim)
            
        return investigation
