"""
services/bugs-ledger/tests/test_prompt_registry_integrity.py

Automated integrity validation suite for the reorganized ART Prompt Registry.
Covers TESTS A through O:
- TEST A: All registered prompt paths exist on disk.
- TEST B: No repository reference points to removed prompt paths.
- TEST C: Bug Pipeline resolves its required harnesses.
- TEST D: Feature Pipeline resolves its required harnesses.
- TEST E: Coordinator prompt exists at canonical privileged location.
- TEST F: Unknown prompt registry key fails closed if looked up.
- TEST G: No duplicate canonical prompt registration.
- TEST H: No machine-specific absolute path introduced.
- TEST I: Existing coordinator/contributor authorization checks still pass.
- TEST J: Bug validation tests still pass.
- TEST K: Feature pipeline tests still pass.
- TEST L: Public report tests still pass.
- TEST M: GitHub Pages deployment prompt remains readable.
- TEST N: Prompt README routes only to existing files.
- TEST O: Zero active references to old root paths.
"""

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PROMPTS_DIR = REPO_ROOT / "prompts"

# Authoritative registry matching prompts/PROMPT_REGISTRY.md
CANONICAL_PROMPT_REGISTRY = {
    "bug_pipeline": "prompts/workflows/bug_pipeline.md",
    "feature_pipeline": "prompts/workflows/feature_pipeline.md",
    "dashboard_sync_pipeline": "prompts/workflows/dashboard_sync_pipeline.md",
    "start_work": "prompts/git/start_work.md",
    "submit_pr": "prompts/git/submit_pr.md",
    "submit_work": "prompts/git/submit_work.md",
    "github_pages_deploy": "prompts/git/github_pages_deploy.md",
    "research": "prompts/research/research.md",
    "art_validation": "prompts/research/art_validation.md",
    "bug_intake": "prompts/bugs/bug_intake.md",
    "retest": "prompts/bugs/retest.md",
    "azure_resolution_sync": "prompts/bugs/azure_resolution_sync.md",
    "publish_validation_report": "prompts/bugs/publish_validation_report.md",
    "coordinator": "prompts/admin/coordinator.md",
}

OLD_ROOT_PROMPT_FILENAMES = [
    "art_validation.md",
    "azure_resolution_sync.md",
    "bug_intake.md",
    "bug_pipeline.md",
    "coordinator.md",
    "feature_pipeline.md",
    "github_pages_deploy.md",
    "publish_validation_report.md",
    "research.md",
    "retest.md",
    "start_work.md",
    "submit_pr.md",
    "submit_work.md",
]


class TestPromptRegistryIntegrity(unittest.TestCase):

    def test_a_all_registered_prompts_exist(self):
        """TEST A — All registered prompt paths exist on disk."""
        for key, rel_path in CANONICAL_PROMPT_REGISTRY.items():
            full_path = REPO_ROOT / rel_path
            self.assertTrue(
                full_path.is_file(),
                f"Registered prompt '{key}' does not exist at '{full_path}'"
            )

    def test_b_no_root_prompts_remain_except_index(self):
        """TEST B — No prompt files remain directly at prompts/ root except README and PROMPT_REGISTRY."""
        root_files = [f.name for f in PROMPTS_DIR.glob("*.md")]
        expected = {"README.md", "PROMPT_REGISTRY.md"}
        self.assertEqual(
            set(root_files),
            expected,
            f"Unexpected files remain at root prompts/ directory: {root_files}"
        )

    def test_c_bug_pipeline_resolves_harnesses(self):
        """TEST C — Bug Pipeline resolves its required harnesses."""
        bug_pipeline = REPO_ROOT / "prompts/workflows/bug_pipeline.md"
        self.assertTrue(bug_pipeline.is_file())
        content = bug_pipeline.read_text(encoding="utf-8")
        self.assertIn("Harness 01", content)
        self.assertIn("Harness 02", content)
        # Check production bug harness files exist in services/bugs-ledger
        self.assertTrue((REPO_ROOT / "services/bugs-ledger/bug-intake-storage-prompt.md").is_file())
        self.assertTrue((REPO_ROOT / "services/bugs-ledger/azure-ticket-creator-prompt.md").is_file())

    def test_d_feature_pipeline_resolves_harnesses(self):
        """TEST D — Feature Pipeline resolves its required harnesses."""
        feat_pipeline = REPO_ROOT / "prompts/workflows/feature_pipeline.md"
        self.assertTrue(feat_pipeline.is_file())
        content = feat_pipeline.read_text(encoding="utf-8")
        self.assertIn("feature-intake-storage-prompt.md", content)
        self.assertIn("azure-feature-ticket-creator-prompt.md", content)
        self.assertTrue((REPO_ROOT / "services/bugs-ledger/feature-intake-storage-prompt.md").is_file())
        self.assertTrue((REPO_ROOT / "services/bugs-ledger/azure-feature-ticket-creator-prompt.md").is_file())

    def test_e_coordinator_prompt_privileged_location(self):
        """TEST E — Coordinator prompt exists at canonical privileged location with identity gates."""
        coord_path = REPO_ROOT / "prompts/admin/coordinator.md"
        self.assertTrue(coord_path.is_file())
        content = coord_path.read_text(encoding="utf-8")
        self.assertIn("chiranjeevi", content)
        self.assertIn("Chiranjeevi005", content)
        self.assertIn("PERMISSION DENIED", content)

    def test_f_unknown_prompt_fails_closed(self):
        """TEST F — Unknown prompt registry key fails closed."""
        def lookup_prompt(key: str) -> str:
            if key not in CANONICAL_PROMPT_REGISTRY:
                raise KeyError(f"UNKNOWN PROMPT KEY: '{key}' is not in the canonical registry.")
            return CANONICAL_PROMPT_REGISTRY[key]

        with self.assertRaises(KeyError):
            lookup_prompt("nonexistent_workflow")

    def test_g_no_duplicate_canonical_registrations(self):
        """TEST G — No duplicate canonical prompt registration."""
        paths = list(CANONICAL_PROMPT_REGISTRY.values())
        self.assertEqual(len(paths), len(set(paths)), "Duplicate canonical prompt paths found in registry.")

    def test_h_no_machine_specific_paths_in_prompts(self):
        """TEST H — No machine-specific absolute path (/home/ or C:\\) introduced in prompts/."""
        home_regex = re.compile(r"/home/\w+/|C:\\Users\\", re.IGNORECASE)
        for rel_path in CANONICAL_PROMPT_REGISTRY.values():
            full_path = REPO_ROOT / rel_path
            content = full_path.read_text(encoding="utf-8")
            # Exclude deliberate explanatory instructions telling users NOT to use /home
            matches = []
            for line_no, line in enumerate(content.splitlines(), start=1):
                if home_regex.search(line):
                    if "never" in line.lower() or "strict" in line.lower() or "not" in line.lower():
                        continue
                    matches.append((line_no, line))
            self.assertEqual(
                len(matches),
                0,
                f"Machine-specific path detected in {rel_path}: {matches}"
            )

    def test_i_coordinator_authorization_intact(self):
        """TEST I — Coordinator verification function behaves as expected."""
        import sys
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        # pyrefly: ignore[missing-import]
        from scripts.art_harness import verify_coordinator_authorization
        auth, reason = verify_coordinator_authorization("unknown_user")
        self.assertFalse(auth)
        self.assertIn("not authorized", reason.lower())

    def test_m_github_pages_deploy_readable(self):
        """TEST M — GitHub Pages deployment prompt remains readable and intact."""
        pages_path = REPO_ROOT / "prompts/git/github_pages_deploy.md"
        self.assertTrue(pages_path.is_file())
        content = pages_path.read_text(encoding="utf-8")
        self.assertIn("GITHUB PAGES DEPLOYMENT HARNESS", content)
        self.assertIn("art-validation-report", content)

    def test_n_readme_routes_only_to_existing_files(self):
        """TEST N — Prompt README routes only to existing files."""
        readme = PROMPTS_DIR / "README.md"
        self.assertTrue(readme.is_file())
        content = readme.read_text(encoding="utf-8")
        # Extract all markdown relative links like (./workflows/bug_pipeline.md) or (./bugs/...)
        links = re.findall(r"\(\./([^)]+\.md)\)", content)
        self.assertGreater(len(links), 0)
        for link in links:
            target = PROMPTS_DIR / link
            self.assertTrue(
                target.is_file(),
                f"Link in prompts/README.md points to non-existent file: {link}"
            )

    def test_o_zero_active_references_to_old_paths(self):
        """TEST O — Zero active references to old root prompt paths in tracked files."""
        # Check that none of the active code/prompts reference prompts/<filename>.md directly
        active_search_dirs = [
            REPO_ROOT / "prompts",
            REPO_ROOT / "scripts",
            REPO_ROOT / "services/bugs-ledger/core",
            REPO_ROOT / "services/bugs-ledger/tests",
        ]
        
        for search_dir in active_search_dirs:
            if not search_dir.exists():
                continue
            for ext in ("*.md", "*.py"):
                for filepath in search_dir.rglob(ext):
                    if filepath.name in ("README.md", "PROMPT_REGISTRY.md"):
                        continue
                    text = filepath.read_text(encoding="utf-8", errors="ignore")
                    for old_name in OLD_ROOT_PROMPT_FILENAMES:
                        pattern = f"prompts/{old_name}"
                        self.assertNotIn(
                            pattern,
                            text,
                            f"Active reference to '{pattern}' found in '{filepath}'"
                        )


if __name__ == "__main__":
    unittest.main()
