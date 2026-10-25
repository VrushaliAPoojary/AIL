import unittest
import os
from compiler.core.parser import MarkdownParser
from compiler.core.normalizer import SemanticNormalizer
from compiler.core.change_detection import ChangeDetector


class TestRealCorpusStress(unittest.TestCase):
    def setUp(self):
        self.parser = MarkdownParser()
        self.normalizer = SemanticNormalizer()
        self.detector = ChangeDetector()

        self.files = [
            "/home/chiranjeevi/Documents/art-investigation-lab(AIL)/research/imported/Healthcare_and_Pharmaceuticals/Baby_Memorial_Hospital_Kozhikode/opportunity - 01/OPP-001-01.md",
            "/home/chiranjeevi/Documents/art-investigation-lab(AIL)/research/imported/IT_and_Business_Services/servicenow/opportunity06/opportunity.md",
            "/home/chiranjeevi/Documents/art-investigation-lab(AIL)/research/imported/IT_and_Business_Services/servicenow/opportunity08/opportunity.md",
        ]

    def test_semantic_adaptation(self):
        for fpath in self.files:
            with open(fpath, "r", encoding="utf-8") as f:
                parsed = self.parser.parse(f.read(), fpath)
            inv = self.normalizer.normalize(parsed)

            # Headings are correctly separated into workflows, checkpoints, and sections
            self.assertTrue(len(inv.checkpoints) > 0 or len(inv.sections) > 0)

            # Evidence blocks are mapped
            self.assertGreater(len(inv.evidence), 5)

            # Stable IDs are separated from content hashes
            for e in inv.evidence:
                self.assertIsNotNone(e.id)
                self.assertIsNotNone(e.content_hash)
                self.assertNotEqual(e.id, e.content_hash)

    def test_markdown_mutation(self):
        fpath = self.files[0]
        with open(fpath, "r", encoding="utf-8") as f:
            corpus_text = f.read()

        parsed1 = self.parser.parse(corpus_text, fpath)
        inv1 = self.normalizer.normalize(parsed1)

        # Mutation operations
        # 1. Modify a finding
        modified_text = corpus_text.replace("41 minutes", "42 minutes")
        # 2. Add an evidence item
        modified_text += "\n\nNew verified evidence here.\n"

        parsed2 = self.parser.parse(modified_text, fpath)
        inv2 = self.normalizer.normalize(parsed2)

        diff = self.detector.detect_changes(inv1, inv2)

        # The modified evidence block should be tracked via stable ID and show as 'modified'
        # because its content hash changed.
        self.assertTrue(len(diff.added) > 0, "New evidence must be detected as added")
        self.assertTrue(len(diff.modified) > 0, "Modified text must be detected as modified")

    def test_epistemic_integrity(self):
        fpath = self.files[0]
        with open(fpath, "r", encoding="utf-8") as f:
            parsed = self.parser.parse(f.read(), fpath)

        inv = self.normalizer.normalize(parsed)
        for e in inv.evidence:
            if "status: unknown" in e.raw.lower():
                self.assertEqual(e.epistemic_status.name, "UNKNOWN")
            if "status: inferred" in e.raw.lower():
                self.assertEqual(e.epistemic_status.name, "INFERRED")

    def test_contract_gap_contradictions(self):
        # We manually inject a contradiction about bed counts
        fpath = self.files[0]
        with open(fpath, "r", encoding="utf-8") as f:
            corpus_text = f.read()

        corpus_text += "\n\nThe official site reports 490 beds.\n\nHowever, regulatory filing claims 600 beds.\n"

        parsed = self.parser.parse(corpus_text, fpath)
        inv = self.normalizer.normalize(parsed)

        # The relationship should be established in IR, even if the JSON contract doesn't allow it.
        self.assertGreater(len(inv.relationships), 0, "Contradiction relationship must be captured in IR")

    def test_determinism(self):
        fpath = self.files[0]
        with open(fpath, "r", encoding="utf-8") as f:
            corpus_text = f.read()

        parsed1 = self.parser.parse(corpus_text, fpath)
        inv1 = self.normalizer.normalize(parsed1)

        parsed2 = self.parser.parse(corpus_text, fpath)
        inv2 = self.normalizer.normalize(parsed2)

        diff = self.detector.detect_changes(inv1, inv2)
        self.assertEqual(len(diff.added), 0)
        self.assertEqual(len(diff.removed), 0)
        self.assertEqual(len(diff.modified), 0)


if __name__ == '__main__':
    unittest.main()
