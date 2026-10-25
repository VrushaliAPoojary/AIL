from typing import Optional
from compiler.core.parser import MarkdownParser
from compiler.core.normalizer import SemanticNormalizer
from compiler.core.resolver import RelationshipResolver
from compiler.core.firewall import ToolReferenceFirewall
from compiler.core.change_detection import ChangeDetector, ChangeReport
from compiler.core.validator import Validator, ValidationReport
from compiler.core.ir import Investigation

class CoreCompiler:
    def __init__(self):
        self.parser = MarkdownParser()
        self.normalizer = SemanticNormalizer()
        self.resolver = RelationshipResolver()
        self.firewall = ToolReferenceFirewall()
        self.validator = Validator()
        self.change_detector = ChangeDetector()
        
    def compile(self, markdown_text: str, file_path: str, previous_ir: Optional[Investigation] = None) -> tuple[Investigation, ValidationReport, Optional[ChangeReport]]:
        # 1. Parse Markdown
        parsed = self.parser.parse(markdown_text, file_path)
        
        # 2. Semantic Normalization to IR
        investigation = self.normalizer.normalize(parsed)
        
        # 3. Relationship / Provenance Resolution
        investigation = self.resolver.resolve(investigation)
        
        # 4. Tool-Reference Firewall
        investigation = self.firewall.apply_firewall(investigation)
        
        # 5. Validation
        validation_report = self.validator.validate(investigation)
        
        # 6. Change Detection (if previous IR exists)
        change_report = None
        if previous_ir:
            change_report = self.change_detector.detect_changes(previous_ir, investigation)
            
        return investigation, validation_report, change_report
