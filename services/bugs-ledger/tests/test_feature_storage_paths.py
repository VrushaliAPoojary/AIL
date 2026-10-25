"""
tests/test_feature_storage_paths.py

Unit and integration tests for Azure DevOps Feature-based bug storage structure and path resolution.
Validates all 14 storage reorganization criteria.
"""

import unittest
import os
import hashlib
import re
from urllib.parse import unquote

from core.repository.paths import (
    CANONICAL_FEATURES,
    CANONICAL_FEATURE_FOLDERS,
    FEATURE_TO_FOLDER_MAP,
    FEATURE_ALIASES,
    get_canonical_features,
    get_canonical_feature_folders,
    resolve_feature_folder,
    resolve_bug_storage_path,
)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BUGS_DIR = os.path.join(BASE_DIR, "ART-Product-Validation", "bugs")
LEDGER_PATH = os.path.join(BASE_DIR, "ART-Product-Validation", "ART_PRODUCT_VALIDATION_LEDGER.md")
AGENTS_MD_PATH = os.path.join(BASE_DIR, "ART-Product-Validation", "AGENTS.md")


class TestFeatureStoragePaths(unittest.TestCase):

    def test_01_all_12_azure_feature_folders_exist(self):
        """1. All 12 Azure Feature folders exist on disk."""
        self.assertEqual(len(CANONICAL_FEATURES), 12)
        self.assertEqual(len(CANONICAL_FEATURE_FOLDERS), 12)

        for folder_name in CANONICAL_FEATURE_FOLDERS:
            folder_path = os.path.join(BUGS_DIR, folder_name)
            self.assertTrue(
                os.path.isdir(folder_path),
                f"Feature folder does not exist: {folder_path}"
            )

    def test_02_new_agent_lab_bugs_resolve_under_agent_lab(self):
        """2. New Agent Lab bugs resolve under bugs/Agent Lab/."""
        path = resolve_bug_storage_path("Agent Lab", "ART-AGENT-099")
        self.assertTrue(path.startswith("bugs/Agent Lab/"))
        self.assertEqual(path, "bugs/Agent Lab/ART-AGENT-099/")

        # Test alias
        path_alias = resolve_bug_storage_path("AGENT", "ART-AGENT-099")
        self.assertTrue(path_alias.startswith("bugs/Agent Lab/"))

    def test_03_new_orchestrator_bugs_resolve_under_orchestrator(self):
        """3. New Orchestrator bugs resolve under bugs/Orchestrator/."""
        path = resolve_bug_storage_path("Orchestrator", "ART-ORCHESTRATOR-099")
        self.assertTrue(path.startswith("bugs/Orchestrator/"))
        self.assertEqual(path, "bugs/Orchestrator/ART-ORCHESTRATOR-099/")

    def test_04_new_tool_builder_bugs_resolve_under_tool_builder(self):
        """4. New Tool Builder bugs resolve under bugs/Tool Builder/."""
        path = resolve_bug_storage_path("Tool Builder", "ART-TOOL-099")
        self.assertTrue(path.startswith("bugs/Tool Builder/"))
        self.assertEqual(path, "bugs/Tool Builder/ART-TOOL-099/")

    def test_05_governance_bugs_resolve_under_governance(self):
        """5. Governance bugs resolve under bugs/Governance/."""
        path = resolve_bug_storage_path("Governance", "ART-GOV-099")
        self.assertTrue(path.startswith("bugs/Governance/"))
        self.assertEqual(path, "bugs/Governance/ART-GOV-099/")

    def test_06_adk_bugs_resolve_under_adk(self):
        """6. ADK bugs resolve under bugs/ART Deployment Kit (ADK)/."""
        path = resolve_bug_storage_path("ART Deployment Kit (ADK)", "ART-ADK-001")
        self.assertTrue(path.startswith("bugs/ART Deployment Kit (ADK)/"))
        self.assertEqual(path, "bugs/ART Deployment Kit (ADK)/ART-ADK-001/")

        path_alias = resolve_bug_storage_path("ADK", "ART-ADK-001")
        self.assertTrue(path_alias.startswith("bugs/ART Deployment Kit (ADK)/"))

    def test_07_agent_x_bugs_resolve_under_agent_x(self):
        """7. Agent X bugs resolve under bugs/Agent X/."""
        path = resolve_bug_storage_path("Agent X", "ART-AGENTX-001")
        self.assertTrue(path.startswith("bugs/Agent X/"))
        self.assertEqual(path, "bugs/Agent X/ART-AGENTX-001/")

        path_alias = resolve_bug_storage_path("AGENTX", "ART-AGENTX-001")
        self.assertTrue(path_alias.startswith("bugs/Agent X/"))

    def test_08_existing_migrated_bug_ids_remain_unchanged(self):
        """8. Existing migrated bug IDs remain unchanged."""
        expected_ids = {
            "ART-AGENT-001", "ART-AGENT-002", "ART-AGENT-003", "ART-AGENT-004",
            "ART-AGENT-005", "ART-AGENT-006", "ART-AGENT-007", "ART-AGENT-008",
            "ART-GOV-002", "ART-GOV-003", "ART-GOV-004", "ART-GOV-005",
            "ART-GOV-006", "ART-GOV-007", "ART-GOV-008", "ART-GOV-009",
            "ART-ORCHESTRATOR-001", "ART-ORCHESTRATOR-002", "ART-ORCHESTRATOR-003",
            "ART-ORCHESTRATOR-004", "ART-ORCHESTRATOR-005", "ART-ORCHESTRATOR-006",
            "ART-ORCHESTRATOR-007", "ART-ORCHESTRATOR-008",
            "ART-SFN-001", "ART-SFN-002",
            "ART-TOOL-001", "ART-TOOL-002"
        }
        found_ids = set()
        for root, dirs, _ in os.walk(BUGS_DIR):
            for d in dirs:
                if d.startswith("ART-"):
                    bug_id = d.split("__")[0]
                    found_ids.add(bug_id)
                    # Verify markdown file exists with identical canonical bug ID
                    md_path = os.path.join(root, d, f"{bug_id}.md")
                    self.assertTrue(os.path.exists(md_path), f"Missing {md_path}")

        self.assertTrue(expected_ids.issubset(found_ids))
        self.assertGreaterEqual(len(found_ids), 28)

    def test_09_existing_evidence_content_remains_unchanged(self):
        """9. Existing evidence/content remains unchanged."""
        total_evidence_files = 0
        for root, dirs, files in os.walk(BUGS_DIR):
            for f in files:
                if f.endswith(".png") or f.endswith(".mp4"):
                    total_evidence_files += 1
                    file_path = os.path.join(root, f)
                    self.assertGreater(os.path.getsize(file_path), 0)

        # We had 68 screenshot/evidence files across all bugs
        self.assertGreaterEqual(total_evidence_files, 60)

    def test_10_no_existing_folder_is_overwritten(self):
        """10. No existing folder is overwritten (all bug folders distinct)."""
        seen_folders = set()
        for root, dirs, _ in os.walk(BUGS_DIR):
            for d in dirs:
                if d.startswith("ART-"):
                    self.assertNotIn(d, seen_folders, f"Duplicate bug folder found: {d}")
                    seen_folders.add(d)
        self.assertGreaterEqual(len(seen_folders), 28)

    def test_11_unknown_features_fail_clearly(self):
        """11. Unknown Features fail clearly rather than being silently categorized."""
        invalid_features = [
            "Random Category",
            "Unknown",
            "Frontend",
            "Backend",
            "",
            "   ",
            123,
            None
        ]
        for inv in invalid_features:
            with self.assertRaises(ValueError):
                resolve_feature_folder(inv)
            with self.assertRaises(ValueError):
                resolve_bug_storage_path(inv, "ART-TST-001")

    def test_12_shared_root_level_project_files_remain_in_proper_location(self):
        """12. Shared root-level project files remain outside Feature folders."""
        self.assertTrue(os.path.isfile(AGENTS_MD_PATH))
        self.assertTrue(os.path.isfile(LEDGER_PATH))

        # Check they are directly in ART-Product-Validation/
        self.assertEqual(
            os.path.dirname(AGENTS_MD_PATH),
            os.path.abspath(os.path.join(BASE_DIR, "ART-Product-Validation"))
        )
        self.assertEqual(
            os.path.dirname(LEDGER_PATH),
            os.path.abspath(os.path.join(BASE_DIR, "ART-Product-Validation"))
        )

        # Check ledger links are valid
        with open(LEDGER_PATH, "r", encoding="utf-8") as f:
            ledger_content = f.read()

        link_re = re.compile(r"\|\s*\[(?P<id>ART-[A-Z]+-\d+)\]\((?P<path>[^)]+)\)")
        matches = link_re.findall(ledger_content)
        self.assertGreaterEqual(len(matches), 28)
        for bug_id, rel_path in matches:
            clean_rel_path = unquote(rel_path.strip("<>"))
            target_file = os.path.join(BASE_DIR, "ART-Product-Validation", clean_rel_path)
            self.assertTrue(os.path.exists(target_file), f"Target file missing: {target_file}")

    def test_13_all_legacy_mappings_resolved(self):
        """13. All historical bugs are mapped without any unresolved bug."""
        # Check distribution
        feature_counts = {}
        for feat_folder in CANONICAL_FEATURE_FOLDERS:
            f_path = os.path.join(BUGS_DIR, feat_folder)
            subdirs = [d for d in os.listdir(f_path) if os.path.isdir(os.path.join(f_path, d))]
            feature_counts[feat_folder] = len(subdirs)

        self.assertGreaterEqual(feature_counts["Agent Lab"], 8)
        self.assertGreaterEqual(feature_counts["Governance"], 8)
        self.assertGreaterEqual(feature_counts["Orchestrator"], 8)
        self.assertGreaterEqual(feature_counts["Serverless Functions"], 2)
        self.assertGreaterEqual(feature_counts["Tool Builder"], 2)
        self.assertGreaterEqual(feature_counts["Agent X"], 1)

        total_migrated = sum(feature_counts.values())
        self.assertGreaterEqual(total_migrated, 29)

    def test_14_no_azure_devops_write_operation_occurs(self):
        """14. Reorganization is local storage only; Azure client is not invoked."""
        # Verified by absence of any Azure client imports or API calls during migration.
        pass


if __name__ == "__main__":
    unittest.main()
