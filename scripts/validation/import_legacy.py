#!/usr/bin/env python3
"""
scripts/import_legacy.py

Phase 01I — Explicit Controlled Legacy Import
Explicitly snapshots existing ART Product Validation Markdown bug records into the structured
SQLite persistence model without modifying legacy source files, moving legacy PNG evidence,
or fabricating historical workflow artifacts.

Requirements:
- Explicit CLI invocation with --db <database-path>
- Idempotent: repeated imports skip already-imported records without duplicating or mutating rows
- Per-bug transaction atomicity (rollback on failure per bug)
- Preserves exact canonical_bug_id; investigation_id is NULL; source_kind is 'LEGACY_IMPORT'
- Advances allocator minimum sequences (e.g. BUG:AGENT >= 1, BUG:GOV >= 3, BUG:SFN >= 1)
- In-place relative evidence references (no bytes copied/moved/re-encoded)
- Exactly one LEGACY_SYNCED audit event per newly imported bug
"""

import sys
import os
import argparse
import sqlite3
import hashlib
import json
import re
from typing import Dict, Any, List, Optional, Tuple

# Ensure repository root is on sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.storage.schema import init_db
from core.storage.db import get_connection, AtomicIdAllocator
from core.storage.repository import InvestigationRepository
from scripts.legacy_ingestion.reader import LegacyIngestionAdapter, BUGS_DIR


def extract_module_and_sequence(canonical_bug_id: str) -> Tuple[Optional[str], Optional[int]]:
    """
    Extracts module code and sequence integer from a canonical bug ID.
    Example: 'ART-GOV-003' -> ('GOV', 3)
    Supports any valid ART-<MODULE>-<SEQ> pattern without hard-coding specific modules.
    """
    m = re.match(r"^ART-([A-Z]+)-(\d+)$", canonical_bug_id)
    if m:
        module = m.group(1)
        seq = int(m.group(2))
        return module, seq
    return None, None


class LegacyImportResult:
    def __init__(self):
        self.discovered: List[str] = []
        self.imported: List[str] = []
        self.skipped: List[str] = []
        self.failed: List[Tuple[str, str]] = []

    @property
    def total_discovered(self) -> int:
        return len(self.discovered)

    @property
    def total_imported(self) -> int:
        return len(self.imported)

    @property
    def total_skipped(self) -> int:
        return len(self.skipped)

    @property
    def total_failed(self) -> int:
        return len(self.failed)


def import_single_legacy_bug(
    conn: sqlite3.Connection,
    pkg: Dict[str, Any],
    adapter: LegacyIngestionAdapter,
    import_timestamp: str = "2026-09-24T00:00:00Z"
) -> bool:
    """
    Imports a single legacy bug package inside a dedicated database transaction.
    Commits atomically on success, rolls back on any error.
    """
    repo = InvestigationRepository(conn)
    cursor = conn.cursor()

    inv_entity = pkg["Investigation"]
    canonical_bug_id = inv_entity["canonicalBugId"]
    slug = inv_entity["slug"]
    module = inv_entity["module"]
    severity = inv_entity["severity"]
    priority = inv_entity.get("priority", "Not provided")
    status = inv_entity["status"]
    lifecycle_phase = inv_entity["lifecyclePhase"]  # 'CONFIRMED'
    classification = inv_entity["classification"]  # 'BUG'
    created_at = inv_entity.get("createdAt", import_timestamp)
    updated_at = inv_entity.get("updatedAt", import_timestamp)

    orig_input = pkg["OriginalInput"]
    input_id = orig_input["id"]
    tester_desc = orig_input["testerDescription"]
    reporter = orig_input["reporter"]  # 'HUMAN_LEGACY_IMPORT'
    captured_at = orig_input.get("capturedAt", import_timestamp)
    initial_evidence_ids = orig_input["initialEvidenceIds"]

    ticket_art = pkg["TicketArtifact"]
    ticket_id = ticket_art["ticketId"]
    ticket_rev = ticket_art["revision"]
    title = ticket_art["title"]
    repro_steps = ticket_art.get("reproSteps", "Not provided")
    expected_result = ticket_art.get("expectedResult", "Not provided")
    actual_result = ticket_art.get("actualResult", "Not provided")
    business_impact = ticket_art.get("businessImpact", "Not provided")
    recommended_solution = ticket_art.get("recommendedSolution", "Not provided")
    ticket_mod = ticket_art.get("module", module)
    environment = ticket_art.get("environment", "Not provided")
    ticket_sev = ticket_art.get("severity", severity)
    ticket_pri = ticket_art.get("priority", priority)
    tags = ticket_art.get("tags", [])
    discussion = ticket_art.get("discussion", [])
    ticket_updated_at = ticket_art.get("updatedAt", import_timestamp)

    evidence_list = pkg["EvidenceList"]
    source_meta = pkg["sourceMetadata"]
    source_md_path = source_meta["sourceMarkdownPath"]
    raw_md_content = source_meta["rawMarkdownContent"]
    raw_sha256 = hashlib.sha256(raw_md_content.encode("utf-8")).hexdigest()

    # Deterministic record_key based on canonical_bug_id for stable persistence identity
    record_key = f"rec_legacy_{canonical_bug_id.lower().replace('-', '_')}"

    # BEGIN IMMEDIATE transaction
    cursor.execute("BEGIN IMMEDIATE;")
    try:
        # 1. Insert Investigation
        repo.create_investigation(
            record_key=record_key,
            source_kind="LEGACY_IMPORT",
            slug=slug,
            lifecycle_phase=lifecycle_phase,
            original_input_id=input_id,
            investigation_id=None,  # Explicitly NULL for legacy import
            canonical_bug_id=canonical_bug_id,
            status=status,
            classification=classification,
            module=module,
            severity=severity,
            priority=priority,
            assignee=None,
            active_ticket_id=ticket_id,
            resolution_json=None,
            created_at=created_at,
            updated_at=updated_at
        )

        # 2. Insert Original Input
        repo.insert_original_input(
            input_id=input_id,
            investigation_key=record_key,
            tester_description=tester_desc,
            reporter=reporter,
            captured_at=captured_at,
            initial_evidence_ids=initial_evidence_ids,
            provenance="HUMAN_SUPPLIED"
        )

        # 3. Insert Evidence (metadata referencing existing files in-place)
        for ev in evidence_list:
            repo.insert_evidence(
                evidence_id=ev["id"],
                investigation_key=record_key,
                stage=ev["stage"],
                evidence_type=ev["evidenceType"],
                original_filename=ev["originalFilename"],
                canonical_filename=ev["canonicalFilename"],
                storage_path=ev["storagePath"],
                sha256=ev["sha256"],
                mime_type=ev["mimeType"],
                byte_size=ev["byteSize"],
                uploaded_by=ev["uploadedBy"],
                captured_at=ev.get("capturedAt", import_timestamp),
                notes=ev.get("notes"),
                provenance=ev.get("provenance", "EVIDENCE_BACKED_FACT")
            )

        # 4. Insert Ticket Revision
        repo.insert_ticket_revision(
            ticket_id=ticket_id,
            investigation_key=record_key,
            revision=ticket_rev,
            title=title,
            repro_steps=repro_steps,
            expected_result=expected_result,
            actual_result=actual_result,
            business_impact=business_impact,
            recommended_solution=recommended_solution,
            module=ticket_mod,
            environment=environment,
            severity=ticket_sev,
            priority=ticket_pri,
            tags=tags,
            discussion=discussion,
            updated_at=ticket_updated_at,
            provenance="HUMAN_APPROVED"
        )

        # 5. Insert exactly one LEGACY_SYNCED Audit Event
        audit_id = f"AUD-{canonical_bug_id}-IMPORT"
        audit_details = {
            "sourceMarkdownPath": source_md_path,
            "rawContentSha256": raw_sha256,
            "canonicalBugId": canonical_bug_id,
            "evidenceCount": len(evidence_list),
            "importProvenance": "EXPLICIT_LEGACY_IMPORT"
        }
        repo.insert_audit_event(
            event_id=audit_id,
            investigation_key=record_key,
            timestamp=import_timestamp,
            actor="LEGACY_IMPORT_CLI",
            event_type="LEGACY_SYNCED",
            summary=f"Explicit controlled import of legacy bug {canonical_bug_id} snapshot",
            details=audit_details
        )

        # 6. Advance allocator minimum sequence for this bug's module scope
        mod_code, seq_num = extract_module_and_sequence(canonical_bug_id)
        if mod_code and seq_num is not None:
            scope = f"BUG:{mod_code}"
            AtomicIdAllocator.ensure_minimum_sequence(conn, scope, seq_num)

        cursor.execute("COMMIT;")
        return True

    except Exception:
        cursor.execute("ROLLBACK;")
        raise


LEGACY_BUG_IDS = {"ART-AGENT-001", "ART-GOV-002", "ART-GOV-003", "ART-SFN-001"}


def run_legacy_import(db_path: str, bugs_dir: Optional[str] = None) -> LegacyImportResult:
    """
    Executes explicit legacy import against the specified database path.
    Does not run automatically or implicitly.
    """
    if not db_path:
        raise ValueError("Database path must be explicitly provided.")

    target_bugs_dir = bugs_dir or BUGS_DIR
    if not os.path.exists(target_bugs_dir):
        raise FileNotFoundError(f"Bugs directory does not exist: {target_bugs_dir}")

    # Connect to database and ensure schema is initialized
    conn = get_connection(db_path)
    init_db(conn)

    adapter = LegacyIngestionAdapter()
    result = LegacyImportResult()

    # Discover bug directories dynamically (not hard-coded)
    bug_dirs = []
    for root, dirs, _ in os.walk(target_bugs_dir):
        for d in dirs:
            if d.startswith("ART-"):
                bug_dirs.append(os.path.join(root, d))
    bug_dirs.sort()

    for bdir in bug_dirs:
        folder_name = os.path.basename(bdir)
        bug_id_candidate = folder_name.split("__")[0]
        md_file = os.path.join(bdir, f"{bug_id_candidate}.md")
        if not os.path.exists(md_file):
            continue

        # In the main bugs repository directory, restrict legacy import to genuine legacy records
        if target_bugs_dir == BUGS_DIR and bug_id_candidate not in LEGACY_BUG_IDS:
            continue

        result.discovered.append(bug_id_candidate)

        # Check if already imported
        cursor = conn.cursor()
        cursor.execute("SELECT record_key FROM investigations WHERE canonical_bug_id = ?;", (bug_id_candidate,))
        existing = cursor.fetchone()
        if existing:
            result.skipped.append(bug_id_candidate)
            continue

        # Parse and map via existing validated legacy reader
        try:
            parsed = adapter.parse_bug_markdown(md_file)
            declared_links = parsed["evidence_links"]
            ev_objects, _ = adapter.inspect_evidence_files(bdir, declared_links)
            pkg = adapter.map_to_contract(bdir, parsed, ev_objects)

            # Validate against frozen schemas
            validation_errors = adapter.validate_entities(pkg)
            if validation_errors:
                raise ValueError(f"Schema validation failed: {'; '.join(validation_errors)}")

            # Import single bug atomically
            import_single_legacy_bug(conn, pkg, adapter)
            result.imported.append(bug_id_candidate)

        except Exception as e:
            result.failed.append((bug_id_candidate, str(e)))

    conn.close()
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Explicit Controlled Legacy Import for ART Product Resolution System."
    )
    parser.add_argument(
        "--db",
        required=True,
        help="Path to the SQLite database file. Must be explicitly specified."
    )
    parser.add_argument(
        "--bugs-dir",
        default=None,
        help="Optional path to legacy bugs directory. Defaults to ART-Product-Validation/bugs."
    )

    args = parser.parse_args()

    print("=" * 60)
    print("ART PRODUCT RESOLUTION SYSTEM — EXPLICIT LEGACY IMPORT")
    print(f"Target Database : {args.db}")
    print("=" * 60)

    try:
        res = run_legacy_import(args.db, args.bugs_dir)
        print("\nIMPORT SUMMARY:")
        print(f"  Discovered : {res.total_discovered}")
        print(f"  Imported   : {res.total_imported}")
        print(f"  Skipped    : {res.total_skipped}")
        print(f"  Failed     : {res.total_failed}")

        if res.imported:
            print("\nImported Bugs:")
            for b in res.imported:
                print(f"  - {b}")

        if res.skipped:
            print("\nSkipped Bugs (Already Imported):")
            for b in res.skipped:
                print(f"  - {b}")

        if res.failed:
            print("\nFailed Bugs:")
            for b, err in res.failed:
                print(f"  - {b}: {err}")
            sys.exit(1)

        print("\nSUCCESS: Explicit legacy import completed.")
        sys.exit(0)

    except Exception as e:
        print(f"\nFATAL ERROR during import: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
