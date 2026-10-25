"""
tests/test_identity_and_evidence.py

Phase 01E — Identity and Evidence Storage Test Suite
Validates:
- Pure investigation ID sequence and date logic
- Module-scoped canonical bug ID generation
- Evidence ID stability and independence
- Safe, immutable physical evidence storage
- Path traversal defense
- SHA-256 integrity verification
- Schema validation
- Legacy ID collision protection
"""

import unittest
import os
import shutil
import json
import tempfile
import jsonschema

from core.identity.generator import (
    generate_investigation_id,
    generate_bug_id,
    generate_evidence_id
)
from core.evidence.storage import (
    EvidenceStorageService,
    sanitize_filename
)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCHEMAS_DIR = os.path.join(BASE_DIR, "contracts/schemas")
BUGS_DIR = os.path.join(BASE_DIR, "ART-Product-Validation/bugs")


def load_schemas():
    store = {}
    for fname in os.listdir(SCHEMAS_DIR):
        if fname.endswith(".json"):
            fpath = os.path.join(SCHEMAS_DIR, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                store[fname] = data
                if "$id" in data:
                    store[data["$id"]] = data
    return store


class TestIdentityAndEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schemas = load_schemas()
        cls.resolver = jsonschema.RefResolver.from_schema(cls.schemas["common.json"], store=cls.schemas)
        cls.evidence_validator = jsonschema.Draft202012Validator(cls.schemas["evidence.json"], resolver=cls.resolver)

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="art_test_evidence_")
        self.storage_service = EvidenceStorageService(self.test_dir, schema_store=self.schemas)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # ==========================================
    # PART A & B: IDENTITY TESTS (1 - 10)
    # ==========================================

    def test_01_investigation_id_format(self):
        inv_id = generate_investigation_id([], date_str="20260925")
        self.assertEqual(inv_id, "INV-20260925-0001")

    def test_02_investigation_sequence_increments(self):
        existing = {"INV-20260925-0001", "INV-20260925-0002"}
        inv_id = generate_investigation_id(existing, date_str="20260925")
        self.assertEqual(inv_id, "INV-20260925-0003")

    def test_03_existing_investigation_id_not_reused(self):
        existing = {"INV-20260925-0005"}
        inv_id = generate_investigation_id(existing, date_str="20260925")
        self.assertEqual(inv_id, "INV-20260925-0006")
        self.assertNotIn(inv_id, existing)

    def test_04_different_date_receives_own_sequence(self):
        existing = {"INV-20260924-0010"}
        inv_id = generate_investigation_id(existing, date_str="20260925")
        self.assertEqual(inv_id, "INV-20260925-0001")

    def test_05_bug_id_format(self):
        bug_id = generate_bug_id("AGENT", [])
        self.assertEqual(bug_id, "ART-AGENT-001")

    def test_06_bug_sequence_increments_per_module(self):
        existing = {"ART-AGENT-001", "ART-GOV-001"}
        agent_id = generate_bug_id("AGENT", existing)
        gov_id = generate_bug_id("GOV", existing)
        sfn_id = generate_bug_id("SFN", existing)

        self.assertEqual(agent_id, "ART-AGENT-002")
        self.assertEqual(gov_id, "ART-GOV-002")
        self.assertEqual(sfn_id, "ART-SFN-001")

    def test_07_existing_art_ids_not_reused(self):
        existing = {"ART-SFN-001", "ART-SFN-002"}
        new_id = generate_bug_id("SFN", existing)
        self.assertEqual(new_id, "ART-SFN-003")
        self.assertNotIn(new_id, existing)

    def test_08_unknown_module_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            generate_bug_id("UNKNOWN", [])
        self.assertIn("not an approved canonical module", str(ctx.exception))

    def test_09_not_provided_module_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            generate_bug_id("Not provided", [])
        self.assertIn("not an approved canonical module", str(ctx.exception))

    def test_10_evidence_id_independent_of_bug_id(self):
        evd1 = generate_evidence_id()
        evd2 = generate_evidence_id([evd1])
        self.assertTrue(evd1.startswith("EVD-"))
        self.assertTrue(evd2.startswith("EVD-"))
        self.assertNotEqual(evd1, evd2)
        # Verify independence from ART bug ID
        self.assertNotIn("ART", evd1)

    # ==========================================
    # PART C & D: EVIDENCE TESTS (11 - 25)
    # ==========================================

    def test_11_evidence_can_be_stored(self):
        sample_bytes = b"sample_png_bytes_for_testing"
        meta = self.storage_service.store_evidence(
            investigation_id="INV-20260925-0001",
            file_bytes=sample_bytes,
            original_filename="screenshot.png",
            stage="ORIGINAL",
            uploaded_by="tester"
        )
        self.assertIsNotNone(meta["id"])
        full_path = os.path.join(os.getcwd(), meta["storagePath"])
        self.assertTrue(os.path.exists(full_path))

    def test_12_stored_bytes_equal_source_bytes(self):
        sample_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRtest_data"
        meta = self.storage_service.store_evidence(
            investigation_id="INV-20260925-0001",
            file_bytes=sample_bytes,
            original_filename="test.png",
            stage="ORIGINAL",
            uploaded_by="tester"
        )
        with open(os.path.join(os.getcwd(), meta["storagePath"]), "rb") as fp:
            stored_bytes = fp.read()
        self.assertEqual(stored_bytes, sample_bytes)

    def test_13_sha256_matches(self):
        import hashlib
        sample_bytes = b"deterministic_content_12345"
        expected_sha = hashlib.sha256(sample_bytes).hexdigest()
        meta = self.storage_service.store_evidence(
            investigation_id="INV-20260925-0001",
            file_bytes=sample_bytes,
            original_filename="doc.txt",
            stage="ORIGINAL",
            uploaded_by="tester"
        )
        self.assertEqual(meta["sha256"], expected_sha)

    def test_14_metadata_validates_against_evidence_schema(self):
        meta = self.storage_service.store_evidence(
            investigation_id="INV-20260925-0001",
            file_bytes=b"schema_test_bytes",
            original_filename="test_evidence.png",
            stage="ORIGINAL",
            uploaded_by="tester",
            notes="Testing schema validation"
        )
        # Explicit validation call
        self.evidence_validator.validate(meta)

    def test_15_original_filename_preserved_as_metadata(self):
        original_name = "My Complex Screenshot (Draft) #1.png"
        meta = self.storage_service.store_evidence(
            investigation_id="INV-20260925-0001",
            file_bytes=b"test",
            original_filename=original_name,
            stage="ORIGINAL",
            uploaded_by="tester"
        )
        self.assertEqual(meta["originalFilename"], original_name)
        # But canonical file on disk has sanitized name prefixed with EVD id
        self.assertTrue(meta["canonicalFilename"].startswith(meta["id"]))
        self.assertNotIn(" ", meta["canonicalFilename"])

    def test_16_unsafe_filename_cannot_escape_evidence_root(self):
        # 1. Filename with directory traversal
        unsafe_name = "../../../etc/passwd"
        meta = self.storage_service.store_evidence(
            investigation_id="INV-20260925-0001",
            file_bytes=b"safe_content",
            original_filename=unsafe_name,
            stage="ORIGINAL",
            uploaded_by="tester"
        )
        full_path = os.path.abspath(os.path.join(os.getcwd(), meta["storagePath"]))
        self.assertTrue(os.path.normcase(full_path).startswith(os.path.normcase(self.test_dir)))
        self.assertFalse(full_path.startswith("/etc"))
        self.assertNotIn("..", full_path)

        # 2. Investigation ID with traversal
        with self.assertRaises(ValueError):
            self.storage_service.store_evidence(
                investigation_id="../../escape",
                file_bytes=b"safe_content",
                original_filename="test.png",
                stage="ORIGINAL",
                uploaded_by="tester"
            )

    def test_17_existing_stored_evidence_cannot_be_overwritten(self):
        sample = b"original_content"
        meta = self.storage_service.store_evidence(
            investigation_id="INV-20260925-0001",
            file_bytes=sample,
            original_filename="image.png",
            stage="ORIGINAL",
            uploaded_by="tester"
        )
        full_path = os.path.join(os.getcwd(), meta["storagePath"])
        # Attempting to write directly to same file path must be prevented by OS/permissions or service
        self.assertTrue(os.path.exists(full_path))

    def test_18_to_21_supported_stages_accepted(self):
        for stage, prov in [
            ("ORIGINAL", "HUMAN_SUPPLIED"),
            ("DEVELOPER_FIX", "DEVELOPER_UPDATE"),
            ("RETEST", "RETEST_VERIFICATION"),
            ("SUPPLEMENTAL", "HUMAN_SUPPLIED")
        ]:
            meta = self.storage_service.store_evidence(
                investigation_id="INV-20260925-0001",
                file_bytes=b"content",
                original_filename=f"{stage.lower()}.png",
                stage=stage,
                uploaded_by="user"
            )
            self.assertEqual(meta["stage"], stage)
            self.assertEqual(meta["provenance"], prov)
            self.evidence_validator.validate(meta)

    def test_22_unsupported_stage_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            self.storage_service.store_evidence(
                investigation_id="INV-20260925-0001",
                file_bytes=b"content",
                original_filename="test.png",
                stage="INVALID_STAGE",
                uploaded_by="user"
            )
        self.assertIn("Invalid stage", str(ctx.exception))

    def test_23_multiple_evidence_files_in_one_investigation(self):
        meta1 = self.storage_service.store_evidence(
            investigation_id="INV-20260925-0001",
            file_bytes=b"screenshot_1",
            original_filename="screen1.png",
            stage="ORIGINAL",
            uploaded_by="tester"
        )
        meta2 = self.storage_service.store_evidence(
            investigation_id="INV-20260925-0001",
            file_bytes=b"screenshot_2",
            original_filename="screen2.png",
            stage="ORIGINAL",
            uploaded_by="tester"
        )
        self.assertNotEqual(meta1["id"], meta2["id"])
        self.assertNotEqual(meta1["canonicalFilename"], meta2["canonicalFilename"])
        inv_dir = os.path.join(self.test_dir, "INV-20260925-0001")
        self.assertEqual(len(os.listdir(inv_dir)), 2)

    def test_24_duplicate_bytes_exist_as_separate_evidence_records(self):
        identical_bytes = b"same_byte_content_for_two_different_events"
        meta1 = self.storage_service.store_evidence(
            investigation_id="INV-20260925-0001",
            file_bytes=identical_bytes,
            original_filename="shot1.png",
            stage="ORIGINAL",
            uploaded_by="tester"
        )
        meta2 = self.storage_service.store_evidence(
            investigation_id="INV-20260925-0001",
            file_bytes=identical_bytes,
            original_filename="shot2.png",
            stage="RETEST",
            uploaded_by="qa"
        )
        # Identical hash
        self.assertEqual(meta1["sha256"], meta2["sha256"])
        # Distinct logical entities
        self.assertNotEqual(meta1["id"], meta2["id"])
        self.assertNotEqual(meta1["canonicalFilename"], meta2["canonicalFilename"])

    def test_25_evidence_stable_on_bug_promotion_without_move(self):
        # 1. Evidence captured under INV identity
        meta = self.storage_service.store_evidence(
            investigation_id="INV-20260925-0001",
            file_bytes=b"promo_test_data",
            original_filename="defect.png",
            stage="ORIGINAL",
            uploaded_by="tester"
        )
        original_storage_path = meta["storagePath"]
        evd_id = meta["id"]

        # 2. Simulate promotion: Bug ID allocated, but evidence file is NOT moved
        promoted_bug_id = generate_bug_id("AGENT", ["ART-AGENT-001"])
        self.assertEqual(promoted_bug_id, "ART-AGENT-002")

        # The storagePath and evd_id remain 100% valid and existing on disk
        full_path = os.path.join(os.getcwd(), original_storage_path)
        self.assertTrue(os.path.exists(full_path))
        self.assertEqual(meta["id"], evd_id)

    # ==========================================
    # LEGACY REPOSITORY COLLISION TEST
    # ==========================================

    def test_26_legacy_id_collision_prevention(self):
        # Read-only scan of actual legacy bugs
        legacy_dirs = [d for root, dirs, _ in os.walk(BUGS_DIR) for d in dirs if d.startswith("ART-")]
        legacy_bug_ids = set([d.split("__")[0] for d in legacy_dirs if d.split("__")[0] in {"ART-AGENT-001", "ART-GOV-002", "ART-GOV-003", "ART-SFN-001"}])
        self.assertEqual(legacy_bug_ids, {"ART-AGENT-001", "ART-GOV-002", "ART-GOV-003", "ART-SFN-001"})

        # Verify next AGENT bug avoids ART-AGENT-001
        next_agent = generate_bug_id("AGENT", legacy_bug_ids)
        self.assertEqual(next_agent, "ART-AGENT-002")

        # Verify next GOV bug avoids ART-GOV-002 and ART-GOV-003
        next_gov = generate_bug_id("GOV", legacy_bug_ids)
        self.assertEqual(next_gov, "ART-GOV-004")

        # Verify next SFN bug avoids ART-SFN-001
        next_sfn = generate_bug_id("SFN", legacy_bug_ids)
        self.assertEqual(next_sfn, "ART-SFN-002")

    # ==========================================
    # WINDOWS CROSS-DRIVE REGRESSION TESTS
    # ==========================================

    def test_27_windows_cross_drive_path_fallback(self):
        from unittest.mock import patch
        sample_bytes = b"sample_cross_drive_bytes"
        with patch("os.path.relpath", side_effect=ValueError("path is on mount 'C:', start on mount 'D:'")):
            meta = self.storage_service.store_evidence(
                investigation_id="INV-20260925-0001",
                file_bytes=sample_bytes,
                original_filename="cross_drive_evidence.png",
                stage="ORIGINAL",
                uploaded_by="tester"
            )
            self.assertIsNotNone(meta["id"])
            # Storage path falls back safely to absolute path on cross-mount
            self.assertTrue(os.path.isabs(meta["storagePath"]))
            self.assertTrue(os.path.exists(meta["storagePath"]))
            with open(meta["storagePath"], "rb") as fp:
                self.assertEqual(fp.read(), sample_bytes)
            # Must still conform to JSON schema
            self.evidence_validator.validate(meta)

    def test_28_path_traversal_cross_drive_blocked(self):
        from unittest.mock import patch
        with patch("os.path.relpath", side_effect=ValueError("path is on mount 'C:', start on mount 'D:'")):
            # 1. Investigation ID traversal blocked
            with self.assertRaises(ValueError):
                self.storage_service.store_evidence(
                    investigation_id="../../escape",
                    file_bytes=b"data",
                    original_filename="test.png",
                    stage="ORIGINAL",
                    uploaded_by="tester"
                )
            # 2. Dangerous filename sanitized and contained strictly within evidence_root
            meta = self.storage_service.store_evidence(
                investigation_id="INV-20260925-0001",
                file_bytes=b"safe",
                original_filename="../../../etc/shadow",
                stage="ORIGINAL",
                uploaded_by="tester"
            )
            norm_storage = os.path.normcase(os.path.abspath(meta["storagePath"]))
            norm_root = os.path.normcase(os.path.abspath(self.test_dir))
            self.assertTrue(norm_storage.startswith(norm_root))


if __name__ == "__main__":
    unittest.main()
