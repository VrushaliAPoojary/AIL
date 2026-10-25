import tempfile
import unittest
from pathlib import Path
from compiler.core.compiler_main import CoreCompiler
from compiler.core.ir import EpistemicStatus

class TestIntegration(unittest.TestCase):
    def test_fixture_compilation(self):
        compiler = CoreCompiler()
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = Path(tmpdir) / 'opportunity.md'
            md = """---
opportunity_id: OPP-001
company: TestCorp
---
# Checkpoint 1

## Proposed ART Workflow

Status: VERIFIED
We will automate this with https://example.com/reference
"""
            fixture_path.write_text(md, encoding='utf-8')

            inv, report, change_report = compiler.compile(md, str(fixture_path))

            self.assertTrue(report.is_valid)
            self.assertEqual(len(inv.checkpoints), 1)
            self.assertEqual(len(inv.evidence), 1)
            self.assertEqual(inv.evidence[0].epistemic_status, EpistemicStatus.VERIFIED)
            self.assertEqual(len(inv.workflows), 1)
            self.assertEqual(inv.workflows[0].workflow_type.value, 'PROPOSED_ART')
            self.assertEqual(len(inv.sources), 1)
            self.assertEqual(inv.sources[0].url, 'https://example.com/reference')

            inv2, report2, change_report = compiler.compile(md, str(fixture_path), previous_ir=inv)
            self.assertTrue(report2.is_valid)
            self.assertEqual(len(change_report.modified), 0)
            self.assertEqual(len(change_report.added), 0)

if __name__ == '__main__':
    unittest.main()
