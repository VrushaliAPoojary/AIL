"""Project an existing AOI Phase 1 normalized snapshot for the ART Lab UI.

This script does not parse Markdown or perform research. It copies only fields
already present in normalized AOI semantic objects and writes a deterministic
UI snapshot plus a generation manifest containing source hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "src" / "data" / "aoi" / "normalizedOpportunities.json"
MANIFEST = ROOT / "src" / "data" / "aoi" / "normalizedOpportunities.manifest.json"
PROJECTION_VERSION = "AOI-UI-PROJECTION-1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def pick(mapping: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    return {field: mapping.get(field) for field in fields if field in mapping}


def project(opportunity: dict[str, Any]) -> dict[str, Any]:
    return {
        "metadata": opportunity.get("metadata", {}),
        "checkpoints": [
            pick(item, [
                "id", "sequence", "title", "company", "opportunity", "status",
                "investigation_type", "metadata", "conflicts", "evidence_ids",
                "hypothesis_ids", "decision_ids", "source_ids", "sha256",
            ])
            for item in opportunity.get("checkpoints", [])
        ],
        "evidence": [
            pick(item, [
                "id", "checkpoint_id", "classification", "statement", "section",
                "source_ids",
            ])
            for item in opportunity.get("evidence", [])
        ],
        "hypotheses": [
            pick(item, [
                "id", "checkpoint_id", "statement", "classification", "status",
                "section", "source_ids",
            ])
            for item in opportunity.get("hypotheses", [])
        ],
        "decisions": [
            pick(item, [
                "id", "checkpoint_id", "value", "statement", "section",
                "source_ids", "raw_value",
            ])
            for item in opportunity.get("decisions", [])
        ],
        "workflows": [
            pick(item, [
                "id", "title", "source_file", "classification", "status",
                "checkpoint_ids", "source_ids",
            ])
            for item in opportunity.get("workflows", [])
        ],
        "intelligence": [
            pick(item, [
                "id", "name", "category", "source_file", "problem", "workflow",
                "implementation_mechanism", "classification", "applicability",
                "limitations", "checkpoint_ids", "source_ids",
            ])
            for item in opportunity.get("intelligence", [])
        ],
        "sources": [
            pick(item, ["id", "name", "url", "references"])
            for item in opportunity.get("sources", [])
        ],
        "ingestion_errors": opportunity.get("ingestion_errors", []),
        "ingestion_warnings": opportunity.get("ingestion_warnings", []),
    }


def build_payload(source: Path, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": data.get("schemaVersion", "AOI-PHASE-1"),
        "generatedFrom": str(source),
        "opportunities": [project(item) for item in data.get("opportunities", [])],
        "ingestion": data.get("ingestion", {}),
    }


def find_canonical_root(source: Path, relative_path: str) -> Path | None:
    for candidate in [source.parent, *source.parents]:
        if (candidate / relative_path).exists():
            return candidate
    return None


def canonical_files(source: Path, data: dict[str, Any]) -> tuple[Path | None, list[dict[str, Any]]]:
    files: dict[str, dict[str, Any]] = {}
    for opportunity in data.get("opportunities", []):
        metadata = opportunity.get("metadata", {})
        directory = metadata.get("directory")
        if not directory:
            continue
        relative_paths = list(metadata.get("source_files", {}).values())
        relative_paths.extend(
            f"{directory}/{checkpoint.get('id')}.md"
            for checkpoint in opportunity.get("checkpoints", [])
            if checkpoint.get("id")
        )
        root = find_canonical_root(source, relative_paths[0]) if relative_paths else None
        if root is None:
            continue
        for relative_path in relative_paths:
            path = root / relative_path
            files[str(path)] = {
                "path": relative_path,
                "sha256": sha256(path) if path.exists() else None,
                "exists": path.exists(),
            }
    root = None
    for opportunity in data.get("opportunities", []):
        metadata = opportunity.get("metadata", {})
        values = list(metadata.get("source_files", {}).values())
        if values:
            root = find_canonical_root(source, values[0])
            if root:
                break
    return root, sorted(files.values(), key=lambda item: item["path"])


def build_manifest(source: Path, data: dict[str, Any], snapshot_hash: str) -> dict[str, Any]:
    root, files = canonical_files(source, data)
    return {
        "manifestVersion": "AOI-INTEGRITY-1",
        "projectionVersion": PROJECTION_VERSION,
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "compilerVersion": data.get("schemaVersion", "UNKNOWN"),
        "source": {
            "path": str(source),
            "sha256": sha256(source),
            "canonicalRoot": str(root) if root else None,
        },
        "snapshot": {
            "path": str(OUTPUT.relative_to(ROOT)),
            "sha256": snapshot_hash,
        },
        "canonicalFiles": files,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="AOI Phase 1 normalized JSON")
    parser.add_argument("--check", action="store_true", help="Do not write; fail if the snapshot differs")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    data = json.loads(source.read_text(encoding="utf-8"))
    payload_text = json.dumps(build_payload(source, data), indent=2, ensure_ascii=False) + "\n"
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != payload_text:
            print("STALE: normalized snapshot content differs from the AOI Phase 1 source")
            return 1
        print("CURRENT: normalized snapshot content matches the AOI Phase 1 source")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(payload_text, encoding="utf-8")
    manifest = build_manifest(source, data, sha256(OUTPUT))
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT}")
    print(f"wrote {MANIFEST}")
    print(f"opportunities={len(payload_text.split('\"opportunity_id\"')) - 1}")
    print(f"intelligence={sum(len(item['intelligence']) for item in build_payload(source, data)['opportunities'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
