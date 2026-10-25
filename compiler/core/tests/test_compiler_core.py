import unittest
from compiler.core.compiler_main import CoreCompiler
from compiler.core.ir import EpistemicStatus

class TestCoreCompiler(unittest.TestCase):
    def setUp(self):
        self.compiler = CoreCompiler()

    def test_parser_and_normalizer(self):
        md = """---
opportunity id: OPP-123
company: TestCorp
---
# Exception + Human Investigation Reconstruction

Status: VERIFIED
The problem is significant.

# Proposed ART Workflow

We will automate this.
"""
        inv, report, _ = self.compiler.compile(md, "test.md")
        self.assertTrue(report.is_valid)
        self.assertEqual(len(inv.checkpoints), 1)
        self.assertEqual(inv.evidence[0].epistemic_status, EpistemicStatus.VERIFIED)

        self.assertEqual(len(inv.workflows), 1)
        self.assertEqual(inv.workflows[0].workflow_type.value, "PROPOSED_ART")

    def test_epistemic_unknown(self):
        md = """# Some Unknown Fact
Status: UNKNOWN
We don't know the exact count.
"""
        inv, report, _ = self.compiler.compile(md, "test.md")
        self.assertTrue(report.is_valid)
        self.assertEqual(inv.evidence[0].epistemic_status, EpistemicStatus.UNKNOWN)

    def test_semantic_safety_rule(self):
        md = """# Evidence
classification: OBSERVED
Sample transport contributed 34 minutes of elapsed delay which equals 34 minutes of staff labour.
"""
        inv, report, _ = self.compiler.compile(md, "test.md")
        self.assertFalse(report.is_valid)
        self.assertTrue(any("CRITICAL SAFETY VIOLATION" in err for err in report.errors))

    def test_tool_reference_firewall(self):
        md = """# Evidence
classification: OBSERVED
This is an observation [1] and this is a search_id:12345 tool_result:abc.
"""
        inv, report, _ = self.compiler.compile(md, "test.md")
        self.assertTrue(report.is_valid)
        evidence = inv.evidence[0]
        self.assertNotIn("[1]", evidence.raw)
        self.assertNotIn("search_id", evidence.raw)
        self.assertNotIn("tool_result", evidence.raw)

if __name__ == '__main__':
    unittest.main()
