import json
import tempfile
import unittest
from pathlib import Path
from jsonschema import validate, ValidationError
from compiler.core.compiler_main import CoreCompiler

class TestV1_2Schema(unittest.TestCase):
    def setUp(self):
        self.compiler = CoreCompiler()
        self.schema_path = Path('contracts/AIL-INVESTIGATION-BRIEF-JSON-SCHEMA-V1.json')
        with self.schema_path.open('r', encoding='utf-8') as f:
            self.schema = json.load(f)

    def test_schema_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = Path(tmpdir) / 'opportunity.md'
            md = """---
opportunity_id: OPP-001
company: TestCorp
---
## Section Alpha

The official site reports 490 beds.

## Proposed ART Workflow

Status: VERIFIED
The regulatory filing reports 600 beds. https://example.com/reference

# Checkpoint 1
"""
            fixture_path.write_text(md, encoding='utf-8')

            inv, report, _ = self.compiler.compile(md, str(fixture_path))
            self.assertTrue(report.is_valid)
            self.assertEqual(len(inv.checkpoints), 1)

            from compiler.core.mapper import ContractMapper
            json_out, gaps = ContractMapper().map_investigation(inv)

            self.assertEqual(len(gaps), 0, f'Expected 0 gaps in v1.2, got: {gaps}')

            try:
                validate(instance=json_out, schema=self.schema)
            except ValidationError as e:
                self.fail(f'JSON Output failed schema validation: {e.message}')

            self.assertIn('workflows', json_out)
            self.assertTrue(len(json_out['workflows']) > 0)
            wf = json_out['workflows'][0]
            self.assertIn('workflow_type', wf)
            self.assertIn(wf['workflow_type'], ['OBSERVED', 'RECONSTRUCTED', 'PROPOSED_ART'])

            self.assertIn('sections', json_out)
            self.assertTrue(len(json_out['sections']) > 0)
            sec = json_out['sections'][0]
            self.assertIn('id', sec)

    def test_contradiction_relationship_preservation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = Path(tmpdir) / 'opportunity.md'
            content = """---
opportunity_id: OPP-001
company: TestCorp
---
## Section Alpha

The official site reports 490 beds.

## Proposed ART Workflow

Status: VERIFIED
The regulatory filing reports 600 beds. https://example.com/reference

# Checkpoint 1
"""
            fixture_path.write_text(content, encoding='utf-8')

            inv, report, _ = self.compiler.compile(content, str(fixture_path))
            self.assertTrue(report.is_valid)

            from compiler.core.mapper import ContractMapper
            json_out, gaps = ContractMapper().map_investigation(inv)

            self.assertIn('relationships', json_out)
            contradictions = [r for r in json_out['relationships'] if r['relationship_type'] == 'CONTRADICTS']
            self.assertGreater(len(contradictions), 0, 'Contradiction relationship not preserved in JSON')

            try:
                validate(instance=json_out, schema=self.schema)
            except ValidationError as e:
                self.fail(f'JSON with contradiction failed validation: {e.message}')

if __name__ == '__main__':
    unittest.main()
