import re
from typing import List
from compiler.core.ir import Investigation, IRObject

class RelationshipResolver:
    def __init__(self):
        self.broken_references: List[str] = []
        
    def _extract_urls(self, text: str) -> List[str]:
        url_re = re.compile(r"https?://[^\s)\]>]+")
        return [match.group(0).rstrip(".,;:)") for match in url_re.finditer(text)]

    def resolve(self, investigation: Investigation) -> Investigation:
        self.broken_references = []
        
        # Build URL to Source ID map
        url_to_source = {src.url: src.id for src in investigation.sources}
        
        # Link elements to sources
        def link_sources(obj: IRObject):
            urls = self._extract_urls(obj.raw)
            for url in urls:
                if url in url_to_source:
                    src_id = url_to_source[url]
                    if src_id not in obj.source_refs:
                        obj.source_refs.append(src_id)
                else:
                    self.broken_references.append(f"Broken URL ref in {obj.id}: {url}")
                    
        for checkpoint in investigation.checkpoints:
            link_sources(checkpoint)
        for evidence in investigation.evidence:
            link_sources(evidence)
        for workflow in investigation.workflows:
            link_sources(workflow)
        for claim in investigation.claims:
            link_sources(claim)
            
        return investigation
