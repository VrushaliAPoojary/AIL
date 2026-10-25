"""
core/evidence/storage.py

Phase 01E — Immutable Evidence Storage Service
Handles storage, verification, and metadata generation for newly captured evidence files.

Safety guarantees:
- Capture Once: Stored files are written once and cannot be overwritten or mutated.
- Path Traversal Defense: Unsafe filenames and directory escapes (../, /, \\) are blocked.
- Content Hash Verification: SHA-256 is computed before write and re-verified from disk after write.
- Isolated Root: Evidence is placed under a dedicated configurable storage root, never in production folders.
- Contract Compliance: Produces metadata conforming to contracts/schemas/evidence.json.
"""

import os
import re
import hashlib
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import jsonschema

from core.identity.generator import generate_evidence_id

VALID_EVIDENCE_STAGES = {"ORIGINAL", "DEVELOPER_FIX", "RETEST", "SUPPLEMENTAL"}
VALID_EVIDENCE_TYPES = {"SCREENSHOT", "IMAGE", "LOG", "RAW_TEXT", "HAR", "VIDEO", "OTHER"}

# MIME type mapping helper
EXTENSION_TO_EVIDENCE_TYPE = {
    ".png": ("image/png", "SCREENSHOT"),
    ".jpg": ("image/jpeg", "IMAGE"),
    ".jpeg": ("image/jpeg", "IMAGE"),
    ".webp": ("image/webp", "IMAGE"),
    ".log": ("text/plain", "LOG"),
    ".txt": ("text/plain", "RAW_TEXT"),
    ".har": ("application/json", "HAR"),
    ".json": ("application/json", "RAW_TEXT"),
    ".mp4": ("video/mp4", "VIDEO"),
    ".mov": ("video/quicktime", "VIDEO"),
    ".webm": ("video/webm", "VIDEO")
}


def sanitize_filename(filename: str) -> str:
    """
    Strips directory paths and dangerous characters from user-supplied filename.
    """
    base = os.path.basename(filename).strip()
    # Remove any traversal patterns
    clean = re.sub(r"[^A-Za-z0-9_.\-]", "_", base)
    if not clean or clean.startswith("."):
        clean = f"evidence_{clean}" if clean else "evidence_file"
    return clean


class EvidenceStorageService:
    def __init__(self, evidence_root: str, schema_store: Optional[Dict[str, Any]] = None):
        """
        Initializes the service with a dedicated evidence root directory.
        """
        self.evidence_root = os.path.abspath(evidence_root)
        os.makedirs(self.evidence_root, exist_ok=True)
        self.schema_store = schema_store

    def store_evidence(
        self,
        investigation_id: str,
        file_bytes: bytes,
        original_filename: str,
        stage: str,
        uploaded_by: str,
        evidence_type: Optional[str] = None,
        mime_type: Optional[str] = None,
        captured_at: Optional[str] = None,
        notes: Optional[str] = None,
        existing_evidence_ids: Optional[set] = None
    ) -> Dict[str, Any]:
        """
        Stores file bytes into an immutable physical file under evidence_root/<investigation_id>/
        and returns validated Evidence contract metadata.
        """
        if not investigation_id or not isinstance(investigation_id, str):
            raise ValueError("investigation_id must be a non-empty string.")
        
        # Guard: Path traversal on investigation_id
        if ".." in investigation_id or "/" in investigation_id or "\\" in investigation_id:
            raise ValueError(f"Invalid investigation_id '{investigation_id}': path traversal characters forbidden.")

        if not isinstance(file_bytes, (bytes, bytearray)):
            raise TypeError("file_bytes must be bytes.")

        if stage not in VALID_EVIDENCE_STAGES:
            raise ValueError(f"Invalid stage '{stage}'. Must be one of {sorted(list(VALID_EVIDENCE_STAGES))}.")

        if not original_filename:
            original_filename = "unnamed_evidence"

        # Determine safe extension and MIME
        safe_original_name = sanitize_filename(original_filename)
        _, ext = os.path.splitext(safe_original_name)
        ext_lower = ext.lower()

        default_mime, default_type = EXTENSION_TO_EVIDENCE_TYPE.get(ext_lower, ("application/octet-stream", "OTHER"))
        final_mime = mime_type or default_mime
        final_type = evidence_type or default_type

        if final_type not in VALID_EVIDENCE_TYPES:
            raise ValueError(f"Invalid evidenceType '{final_type}'. Must be one of {sorted(list(VALID_EVIDENCE_TYPES))}.")

        # Generate unique Evidence ID
        ev_id = generate_evidence_id(existing_evidence_ids)

        # Build secure storage directory and path
        target_dir = os.path.join(self.evidence_root, investigation_id)
        # Ensure target_dir stays strictly under evidence_root
        norm_root = os.path.normcase(os.path.abspath(self.evidence_root))
        norm_target_dir = os.path.normcase(os.path.abspath(target_dir))
        try:
            if not os.path.commonpath([norm_root, norm_target_dir]) == norm_root:
                raise ValueError("Path traversal attempt detected in target directory resolution.")
        except ValueError as err:
            raise ValueError(f"Path traversal attempt detected in target directory resolution: {err}")

        os.makedirs(target_dir, exist_ok=True)

        canonical_filename = f"{ev_id}__{safe_original_name}"
        target_file_path = os.path.join(target_dir, canonical_filename)

        # Check path traversal
        norm_target_file = os.path.normcase(os.path.abspath(target_file_path))
        try:
            if not os.path.commonpath([norm_root, norm_target_file]) == norm_root:
                raise ValueError("Path traversal attempt detected in target file path resolution.")
        except ValueError as err:
            raise ValueError(f"Path traversal attempt detected in target file path resolution: {err}")

        # Immutability Guard: Never overwrite
        if os.path.exists(target_file_path):
            raise FileExistsError(f"Evidence file '{target_file_path}' already exists. Overwrite forbidden.")

        # Compute source SHA-256
        source_sha256 = hashlib.sha256(file_bytes).hexdigest()
        byte_size = len(file_bytes)

        # Write file atomically/exclusively
        with open(target_file_path, "xb") as fp:
            fp.write(file_bytes)

        # Verification step: Re-read stored file and verify SHA-256 and byte size
        with open(target_file_path, "rb") as fp:
            stored_bytes = fp.read()
        
        stored_sha256 = hashlib.sha256(stored_bytes).hexdigest()
        if stored_sha256 != source_sha256 or len(stored_bytes) != byte_size:
            # Cleanup on integrity corruption
            try:
                os.remove(target_file_path)
            except OSError:
                pass
            raise IOError("Evidence verification failed: stored bytes SHA-256 does not match source hash.")

        timestamp = captured_at or datetime.now(timezone.utc).isoformat()
        try:
            rel_storage_path = os.path.relpath(target_file_path, os.getcwd())
        except ValueError:
            # On Windows, os.path.relpath raises ValueError if target_file_path and os.getcwd() are on different drive mounts.
            # Fall back safely to the normalized absolute target path (which remains strictly verified under evidence_root).
            rel_storage_path = os.path.abspath(target_file_path)

        # Construct Evidence metadata dictionary
        evidence_metadata = {
            "id": ev_id,
            "investigationId": investigation_id,
            "stage": stage,
            "evidenceType": final_type,
            "originalFilename": original_filename,
            "canonicalFilename": canonical_filename,
            "storagePath": rel_storage_path,
            "sha256": source_sha256,
            "mimeType": final_mime,
            "byteSize": byte_size,
            "uploadedBy": uploaded_by,
            "capturedAt": timestamp,
            "notes": notes,
            "provenance": "HUMAN_SUPPLIED" if stage == "ORIGINAL" else (
                "DEVELOPER_UPDATE" if stage == "DEVELOPER_FIX" else (
                    "RETEST_VERIFICATION" if stage == "RETEST" else "HUMAN_SUPPLIED"
                )
            )
        }

        # Optional JSON Schema verification
        if self.schema_store and "evidence.json" in self.schema_store:
            schema = self.schema_store["evidence.json"]
            resolver = jsonschema.RefResolver.from_schema(
                self.schema_store.get("common.json", schema),
                store=self.schema_store
            )
            validator = jsonschema.Draft202012Validator(schema, resolver=resolver)
            validator.validate(evidence_metadata)

        return evidence_metadata
