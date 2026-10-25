"""Validate the AOI Phase 1 source, generated UI snapshot, and integrity manifest.

This is a read-only check. It never regenerates representations and never edits
canonical research Markdown.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from import_aoi_normalized_snapshot import (  # noqa: E402
    MANIFEST,
    OUTPUT,
    build_payload,
    canonical_files,
    sha256,
)


EXPECTED_CLASSIFICATIONS = {
    "DIRECT EVIDENCE",
    "VERIFIED EXTERNAL EVIDENCE",
    "CLAIM",
    "INFERENCE",
    "HYPOTHESIS",
    "UNKNOWN",
    "UNVALIDATED",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def checkpoint_number(checkpoint: dict[str, Any]) -> int:
    value = checkpoint.get("sequence")
    if isinstance(value, int):
        return value
    checkpoint_id = str(checkpoint.get("id", ""))
    try:
        return int(checkpoint_id.rsplit("-", 1)[1])
    except (IndexError, ValueError):
        return 0


def source_urls(opportunity: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        (str(source.get("name") or ""), str(source.get("url") or ""))
        for source in opportunity.get("sources", [])
        if source.get("url")
    }


def projected_opportunity(source: dict[str, Any]) -> dict[str, Any]:
    return build_payload(Path(source.get("generatedFrom", "")), {"opportunities": [source]})[
        "opportunities"
    ][0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source",
        type=Path,
        help="AOI Phase 1 normalized JSON used to create the snapshot",
    )
    args = parser.parse_args()
    source_path = args.source.expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []

    if not source_path.exists():
        print(f"BLOCKED: source does not exist: {source_path}")
        return 2
    if not OUTPUT.exists() or not MANIFEST.exists():
        print("BLOCKED: snapshot or integrity manifest is missing")
        return 2

    source_data = load_json(source_path)
    snapshot_data = load_json(OUTPUT)
    manifest = load_json(MANIFEST)

    expected_payload = build_payload(source_path, source_data)
    expected_text = json.dumps(expected_payload, indent=2, ensure_ascii=False) + "\n"
    actual_text = OUTPUT.read_text(encoding="utf-8")
    if actual_text != expected_text:
        errors.append("snapshot content differs from deterministic projection")
    if manifest.get("source", {}).get("sha256") != sha256(source_path):
        errors.append("source JSON hash differs from manifest")
    if manifest.get("snapshot", {}).get("sha256") != sha256(OUTPUT):
        errors.append("snapshot hash differs from manifest")

    source_opportunities = source_data.get("opportunities", [])
    snapshot_opportunities = snapshot_data.get("opportunities", [])
    source_ids = [item.get("metadata", {}).get("opportunity_id") for item in source_opportunities]
    snapshot_ids = [item.get("metadata", {}).get("opportunity_id") for item in snapshot_opportunities]
    if source_ids != snapshot_ids:
        errors.append("opportunity IDs/order differ between source and snapshot")

    all_classifications: set[str] = set()
    source_url_pairs: set[tuple[str, str]] = set()
    total_checkpoints = 0
    total_intelligence = 0
    all_decisions: list[str] = []
    all_ail_statuses: list[str] = []
    print("AOI INTEGRITY VALIDATION")
    print(f"Source: {source_path}")
    print(f"Snapshot: {OUTPUT}")
    print(f"Manifest: {MANIFEST}")
    print("")

    for source_opportunity in source_opportunities:
        metadata = source_opportunity.get("metadata", {})
        opportunity_id = metadata.get("opportunity_id", "UNKNOWN")
        snapshot_opportunity = next(
            (
                item
                for item in snapshot_opportunities
                if item.get("metadata", {}).get("opportunity_id") == opportunity_id
            ),
            None,
        )
        if snapshot_opportunity is None:
            errors.append(f"{opportunity_id}: missing from snapshot")
            continue

        checkpoints = source_opportunity.get("checkpoints", [])
        ordered = sorted(checkpoints, key=checkpoint_number)
        sequences = [checkpoint_number(item) for item in checkpoints]
        ordered_sequences = [checkpoint_number(item) for item in ordered]
        if sequences != ordered_sequences:
            errors.append(f"{opportunity_id}: checkpoints are not numerically ordered")
        if metadata.get("checkpoint_ids") != [item.get("id") for item in ordered]:
            warnings.append(f"{opportunity_id}: metadata checkpoint sequence differs from parsed order")

        missing = metadata.get("missing_checkpoints", [])
        conflicts = list(metadata.get("conflicts", []))
        for checkpoint in checkpoints:
            conflicts.extend(checkpoint.get("conflicts", []))
        if missing:
            warnings.append(f"{opportunity_id}: missing checkpoints: {', '.join(map(str, missing))}")
        if conflicts:
            warnings.append(f"{opportunity_id}: data-quality conflicts: {' | '.join(map(str, conflicts))}")

        source_files = metadata.get("source_files", {})
        for required in ("opportunity.md", "walkthrough.md", "workflow.md"):
            relative_path = source_files.get(required)
            if not relative_path:
                errors.append(f"{opportunity_id}: missing {required} source reference")
            else:
                root = next(
                    (
                        candidate
                        for candidate in [source_path.parent, *source_path.parents]
                        if (candidate / relative_path).exists()
                    ),
                    None,
                )
                if root is None:
                    errors.append(f"{opportunity_id}: canonical file not found: {relative_path}")

        total_checkpoints += len(checkpoints)
        total_intelligence += len(source_opportunity.get("intelligence", []))
        all_decisions.extend(
            str(item.get("value"))
            for item in source_opportunity.get("decisions", [])
            if item.get("value") is not None
        )
        all_ail_statuses.append(str(metadata.get("ail_status")))
        source_url_pairs |= source_urls(source_opportunity)

        for evidence in source_opportunity.get("evidence", []):
            classification = evidence.get("classification")
            if classification:
                all_classifications.add(str(classification))
        if projected_opportunity(source_opportunity) != snapshot_opportunity:
            errors.append(f"{opportunity_id}: projected semantic object differs from snapshot")

    if not all_classifications.issubset(EXPECTED_CLASSIFICATIONS):
        unknown = sorted(all_classifications - EXPECTED_CLASSIFICATIONS)
        warnings.append(f"unregistered evidence classifications preserved: {', '.join(unknown)}")

    snapshot_url_pairs = {
        (str(source.get("name") or ""), str(source.get("url") or ""))
        for opportunity in snapshot_opportunities
        for source in opportunity.get("sources", [])
        if source.get("url")
    }
    if source_url_pairs != snapshot_url_pairs:
        errors.append("source names/URLs differ between source and snapshot")

    root, current_files = canonical_files(source_path, source_data)
    manifest_files = {
        item.get("path"): item for item in manifest.get("canonicalFiles", [])
    }
    current_paths = {item.get("path") for item in current_files}
    for current in current_files:
        recorded = manifest_files.get(current.get("path"))
        if recorded is None:
            errors.append(f"canonical file is not recorded in manifest: {current.get('path')}")
        elif recorded.get("exists") != current.get("exists") or recorded.get("sha256") != current.get("sha256"):
            errors.append(f"canonical file hash changed: {current.get('path')}")
    for recorded_path in manifest_files:
        if recorded_path not in current_paths:
            errors.append(f"manifest file is no longer present in current source set: {recorded_path}")

    status = "CURRENT" if not errors else "STALE"
    print(f"STATUS: {status}")
    print(f"Opportunities: {len(source_opportunities)}")
    print(f"Checkpoints: {total_checkpoints}")
    print(f"Intelligence records: {total_intelligence}")
    print(f"Source URLs: {len(source_url_pairs)}")
    print(f"Evidence classifications: {', '.join(sorted(all_classifications)) or 'NONE'}")
    print(f"AOI decisions observed: {', '.join(sorted(set(all_decisions))) or 'NONE'}")
    print(f"AIL statuses observed: {', '.join(sorted(set(all_ail_statuses)) or ['NONE'])}")
    print(f"Canonical root: {root or 'UNKNOWN'}")
    print("")
    print("WARNINGS")
    for warning in warnings:
        print(f"- {warning}")
    if not warnings:
        print("- none")
    print("")
    print("ERRORS")
    for error in errors:
        print(f"- {error}")
    if not errors:
        print("- none")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
