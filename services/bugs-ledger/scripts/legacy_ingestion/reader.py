#!/usr/bin/env python3
"""
scripts/legacy_ingestion/reader.py

Phase 01C — Read-Only Legacy Ingestion Proof
Reads all existing bug records from ART-Product-Validation/bugs/, parses their Markdown,
verifies against evidence files and master ledger, maps them into canonical contract
schemas, and validates using jsonschema Draft202012Validator.

Safety guarantee: Read-only. Does not mutate anything under ART-Product-Validation/.
"""

import os
import re
import json
import hashlib
import mimetypes
from typing import Dict, Any, List, Tuple
import jsonschema

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
BUGS_DIR = os.path.join(BASE_DIR, "ART-Product-Validation/bugs")
LEDGER_PATH = os.path.join(BASE_DIR, "ART-Product-Validation/ART_PRODUCT_VALIDATION_LEDGER.md")
SCHEMAS_DIR = os.path.join(BASE_DIR, "contracts/schemas")
OUTPUT_DIR = os.path.join(BASE_DIR, "contracts/test-output")

class LegacyIngestionAdapter:
    def __init__(self):
        self.schemas = self._load_schemas()
        self.resolver = jsonschema.RefResolver.from_schema(self.schemas["common.json"], store=self.schemas)
        self.ledger_data = self._parse_ledger(LEDGER_PATH)

    def _load_schemas(self) -> Dict[str, Any]:
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

    def _parse_ledger(self, ledger_path: str) -> Dict[str, Dict[str, str]]:
        ledger = {}
        with open(ledger_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Look for rows: | [ART-SFN-001](...) | Name | Severity | Status | Dev | Retest |
        row_re = re.compile(r"^\|\s*\[(?P<id>ART-[A-Z]+-\d+)\]\((?P<path>[^)]+)\)\s*\|\s*(?P<name>[^|]+)\|\s*(?P<severity>[^|]+)\|\s*(?P<status>[^|]+)\|\s*(?P<dev>[^|]*)\|\s*(?P<retest>[^|]*)\|")
        for line in lines:
            m = row_re.match(line.strip())
            if m:
                d = m.groupdict()
                bug_id = d["id"].strip()
                ledger[bug_id] = {
                    "bug_id": bug_id,
                    "rel_path": d["path"].strip(),
                    "name": d["name"].strip(),
                    "severity": d["severity"].strip(),
                    "status": d["status"].strip(),
                    "dev_update": d["dev"].strip(),
                    "retest": d["retest"].strip(),
                }
        return ledger

    def parse_bug_markdown(self, md_path: str) -> Dict[str, Any]:
        with open(md_path, "r", encoding="utf-8") as f:
            raw_content = f.read()

        parsed = {
            "raw_content": raw_content,
            "title": "",
            "bug_id": "",
            "severity": "Not provided",
            "status": "OPEN",
            "bug": "",
            "expected": "",
            "actual": "",
            "evidence_links": [],
            "fix_proposal": "",
            "developer_update": "",
            "retest": ""
        }

        # Parse title: # ART-AGENT-001 — Structured output...
        title_match = re.search(r"^#\s+(ART-[A-Z]+-\d+)\s+—\s+(.+)$", raw_content, re.MULTILINE)
        if title_match:
            parsed["bug_id"] = title_match.group(1).strip()
            parsed["title"] = title_match.group(2).strip()

        # Parse header metadata bullets
        canon_id_match = re.search(r"-\s+\*\*Canonical Bug ID:\*\*\s*([A-Za-z0-9\-]+)", raw_content)
        if canon_id_match and not parsed["bug_id"]:
            parsed["bug_id"] = canon_id_match.group(1).strip()

        title_field_match = re.search(r"-\s+\*\*Title:\*\*\s*(.+)$", raw_content, re.MULTILINE)
        if title_field_match and not parsed["title"]:
            parsed["title"] = title_field_match.group(1).strip()

        sev_match = re.search(r"-\s+\*\*Severity:\*\*\s*([A-Za-z0-9]+)", raw_content)
        if sev_match:
            parsed["severity"] = sev_match.group(1).strip()

        status_match = re.search(r"-\s+\*\*Status:\*\*\s*([A-Za-z]+)", raw_content)
        if status_match:
            parsed["status"] = status_match.group(1).strip()

        pri_match = re.search(r"-\s+\*\*Priority:\*\*\s*([A-Za-z0-9]+)", raw_content)
        if pri_match:
            parsed["priority"] = pri_match.group(1).strip()

        env_match = re.search(r"-\s+\*\*Environment:\*\*\s*([^\r\n]+)", raw_content)
        if env_match:
            parsed["environment"] = env_match.group(1).strip()

        # Dynamically extract all ## sections
        header_matches = list(re.finditer(r"^##\s+(.+)$", raw_content, re.MULTILINE))
        for idx, hm in enumerate(header_matches):
            h_name = hm.group(1).strip()
            content_start = hm.end()
            content_end = header_matches[idx + 1].start() if idx + 1 < len(header_matches) else len(raw_content)
            body = raw_content[content_start:content_end].strip()
            norm_key = h_name.lower().replace(" ", "_").replace("-", "_")
            parsed[norm_key] = body

            # Map canonical section names to legacy keys
            if norm_key in ("problem", "bug") and not parsed.get("bug"):
                parsed["bug"] = body
            elif norm_key in ("observed_behavior", "actual", "actual_result") and not parsed.get("actual"):
                parsed["actual"] = body
            elif norm_key in ("expected_behavior", "expected", "expected_result") and not parsed.get("expected"):
                parsed["expected"] = body
            elif norm_key in ("recommended_solution", "production_grade_fix_proposal", "fix_proposal") and not parsed.get("fix_proposal"):
                parsed["fix_proposal"] = body
            elif norm_key == "evidence":
                links = re.findall(r"-\s+\[?([^\]\r\n]+\.(?:png|jpg|jpeg|webp|mp4|mov|webm))\]?(?:\(([^)\r\n]+)\))?", body, re.IGNORECASE)
                found_ev = []
                for fname, fpath in links:
                    target = fpath if fpath else fname
                    found_ev.append(os.path.basename(target))
                parsed["evidence_links"] = found_ev

        return parsed

    def inspect_evidence_files(self, bug_dir: str, declared_links: List[str]) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        supported_exts = (".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mov", ".webm")
        actual_files = [f for f in os.listdir(bug_dir) if any(f.lower().endswith(ext) for ext in supported_exts)]
        status_map = {}
        evidence_objects = []

        for fname in actual_files:
            full_path = os.path.join(bug_dir, fname)
            try:
                rel_path = os.path.relpath(full_path, BASE_DIR)
            except ValueError:
                # Cross-drive fallback on Windows
                rel_path = os.path.abspath(full_path)
            size = os.path.getsize(full_path)
            with open(full_path, "rb") as fp:
                sha256 = hashlib.sha256(fp.read()).hexdigest()
            
            ext = os.path.splitext(fname)[1].lower()
            if ext in (".mp4", ".mov", ".webm"):
                ev_type = "VIDEO"
            elif ext == ".png":
                ev_type = "SCREENSHOT"
            elif ext in (".jpg", ".jpeg", ".webp"):
                ev_type = "IMAGE"
            else:
                ev_type = "OTHER"

            mime, _ = mimetypes.guess_type(full_path)
            if not mime:
                if ext == ".png":
                    mime = "image/png"
                elif ext in (".jpg", ".jpeg"):
                    mime = "image/jpeg"
                elif ext == ".webp":
                    mime = "image/webp"
                elif ext == ".mp4":
                    mime = "video/mp4"
                elif ext == ".mov":
                    mime = "video/quicktime"
                elif ext == ".webm":
                    mime = "video/webm"
                else:
                    mime = "application/octet-stream"

            if fname in declared_links:
                status_map[fname] = "MATCHED"
            else:
                status_map[fname] = "UNREFERENCED"

            evidence_objects.append({
                "filename": fname,
                "rel_path": rel_path,
                "byte_size": size,
                "sha256": sha256,
                "mime": mime,
                "evidence_type": ev_type
            })

        for decl in declared_links:
            if decl not in actual_files:
                status_map[decl] = "MISSING"

        return evidence_objects, status_map

    def map_to_contract(self, bug_dir: str, parsed: Dict[str, Any], evidence_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        bug_id = parsed["bug_id"]
        dir_name = os.path.basename(bug_dir)
        slug = dir_name.replace(f"{bug_id}__", "") if f"{bug_id}__" in dir_name else dir_name
        
        # Module code extracted from bug ID (e.g. ART-AGENT-001 -> AGENT)
        m = re.match(r"^ART-([A-Z]+)-\d+$", bug_id)
        module_code = m.group(1) if m else "Not provided"

        # Evidence entities
        evidence_entities = []
        evidence_ids = []
        for i, ev in enumerate(evidence_files):
            ev_id = f"EVD-{bug_id}-{i+1:02d}"
            evidence_ids.append(ev_id)
            evidence_entities.append({
                "id": ev_id,
                "investigationId": bug_id,
                "stage": "ORIGINAL",
                "evidenceType": ev.get("evidence_type", "SCREENSHOT"),
                "originalFilename": ev["filename"],
                "canonicalFilename": ev["filename"],
                "storagePath": ev["rel_path"],
                "sha256": ev["sha256"],
                "mimeType": ev["mime"],
                "byteSize": ev["byte_size"],
                "uploadedBy": "HUMAN_LEGACY_IMPORT",
                "capturedAt": "2026-09-24T00:00:00Z",
                "notes": None,
                "provenance": "EVIDENCE_BACKED_FACT"
            })

        # Original input entity
        inp_id = f"INP-{bug_id}"
        original_input = {
            "id": inp_id,
            "investigationId": bug_id,
            "testerDescription": parsed["bug"],
            "reporter": "HUMAN_LEGACY_IMPORT",
            "capturedAt": "2026-09-24T00:00:00Z",
            "initialEvidenceIds": evidence_ids,
            "provenance": "HUMAN_SUPPLIED"
        }

        # Ticket Artifact entity
        tck_id = f"TCK-{bug_id}-01"
        ticket_artifact = {
            "ticketId": tck_id,
            "investigationId": bug_id,
            "revision": 1,
            "title": parsed["title"],
            "reproSteps": "Not provided",
            "expectedResult": parsed["expected"] if parsed["expected"] else "Not provided",
            "actualResult": parsed["actual"] if parsed["actual"] else "Not provided",
            "businessImpact": "Not provided",
            "recommendedSolution": parsed["fix_proposal"] if parsed["fix_proposal"] else "Not provided",
            "module": module_code,
            "environment": "Not provided",
            "severity": parsed["severity"] if parsed["severity"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"] else "Not provided",
            "priority": "Not provided",
            "tags": [module_code.lower()] if module_code != "Not provided" else [],
            "discussion": [],
            "provenance": "HUMAN_APPROVED",
            "updatedAt": "2026-09-24T00:00:00Z"
        }

        # Audit Event entity
        aud_id = f"AUD-{bug_id}-01"
        audit_event = {
            "id": aud_id,
            "investigationId": bug_id,
            "timestamp": "2026-09-24T00:00:00Z",
            "actor": "LEGACY_IMPORT_ADAPTER",
            "eventType": "INVESTIGATION_CAPTURED",
            "summary": f"Imported legacy bug record {bug_id} from ART-Product-Validation/bugs",
            "details": {
                "sourceMarkdownPath": (
                    os.path.relpath(os.path.join(bug_dir, f"{bug_id}.md"), BASE_DIR)
                    if not (hasattr(os.path, "splitdrive") and os.path.splitdrive(bug_dir)[0].lower() != os.path.splitdrive(BASE_DIR)[0].lower())
                    else os.path.abspath(os.path.join(bug_dir, f"{bug_id}.md"))
                ),
                "rawContentSha256": hashlib.sha256(parsed["raw_content"].encode("utf-8")).hexdigest()
            }
        }

        # Root Investigation entity
        investigation = {
            "id": bug_id,  # Preserve exact legacy Bug ID
            "canonicalBugId": bug_id,
            "slug": slug,
            "lifecyclePhase": "CONFIRMED",
            "status": parsed["status"],
            "classification": "BUG",
            "module": module_code,
            "severity": ticket_artifact["severity"],
            "priority": "Not provided",
            "assignee": None,
            "originalInputId": inp_id,
            "evidenceIds": evidence_ids,
            "aiAnalysisIds": [],
            "researchIds": [],
            "ticketRevisionIds": [tck_id],
            "activeTicketRevisionId": tck_id,
            "developerUpdateIds": [],
            "retestIds": [],
            "auditEventIds": [aud_id],
            "createdAt": "2026-09-24T00:00:00Z",
            "updatedAt": "2026-09-24T00:00:00Z"
        }

        source_md_full = os.path.join(bug_dir, f"{bug_id}.md")
        try:
            source_md_rel = os.path.relpath(source_md_full, BASE_DIR)
        except ValueError:
            source_md_rel = os.path.abspath(source_md_full)

        return {
            "Investigation": investigation,
            "OriginalInput": original_input,
            "EvidenceList": evidence_entities,
            "TicketArtifact": ticket_artifact,
            "AuditEvent": audit_event,
            "sourceMetadata": {
                "sourceMarkdownPath": source_md_rel,
                "rawMarkdownContent": parsed["raw_content"],
                "ledgerRow": self.ledger_data.get(bug_id)
            }
        }

    def validate_entities(self, contract_package: Dict[str, Any]) -> List[str]:
        errors = []
        checks = [
            ("Investigation", "investigation.json", contract_package["Investigation"]),
            ("OriginalInput", "original_input.json", contract_package["OriginalInput"]),
            ("TicketArtifact", "ticket_artifact.json", contract_package["TicketArtifact"]),
            ("AuditEvent", "audit_event.json", contract_package["AuditEvent"])
        ]
        for name, schema_name, instance in checks:
            schema = self.schemas[schema_name]
            validator = jsonschema.Draft202012Validator(schema, resolver=self.resolver)
            for err in validator.iter_errors(instance):
                errors.append(f"[{name}] {err.message} at path: {'/'.join(str(p) for p in err.path)}")

        ev_schema = self.schemas["evidence.json"]
        ev_validator = jsonschema.Draft202012Validator(ev_schema, resolver=self.resolver)
        for ev in contract_package["EvidenceList"]:
            for err in ev_validator.iter_errors(ev):
                errors.append(f"[Evidence {ev['id']}] {err.message} at path: {'/'.join(str(p) for p in err.path)}")

        return errors

def main():
    adapter = LegacyIngestionAdapter()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    bug_dirs = []
    for root, dirs, _ in os.walk(BUGS_DIR):
        for d in dirs:
            if d.startswith("ART-"):
                bug_dirs.append(os.path.join(root, d))
    bug_dirs.sort()

    results = []
    print("="*60)
    print("PHASE 01C — READ-ONLY LEGACY INGESTION PROOF EXECUTION")
    print("="*60)

    for bdir in bug_dirs:
        folder_name = os.path.basename(bdir)
        bug_id = folder_name.split("__")[0]
        md_file = os.path.join(bdir, f"{bug_id}.md")
        
        parse_status = "FAIL"
        evidence_status = "FAIL"
        ledger_status = "FAIL"
        schema_status = "FAIL"
        err_details = []

        if not os.path.exists(md_file):
            err_details.append(f"Missing Markdown file: {md_file}")
            results.append({
                "id": bug_id, "parse": parse_status, "evidence": evidence_status,
                "ledger": ledger_status, "schema": schema_status, "overall": "FAIL", "errors": err_details
            })
            continue

        try:
            parsed = adapter.parse_bug_markdown(md_file)
            parse_status = "PASS" if parsed["bug_id"] == bug_id and parsed["title"] else "FAIL"
        except Exception as e:
            err_details.append(f"Parse error: {e}")

        try:
            ev_files, ev_status_map = adapter.inspect_evidence_files(bdir, parsed["evidence_links"])
            all_matched = all(st == "MATCHED" for st in ev_status_map.values())
            evidence_status = "PASS" if all_matched and len(ev_files) > 0 else "FAIL"
            if not all_matched:
                err_details.append(f"Evidence mismatch: {ev_status_map}")
        except Exception as e:
            err_details.append(f"Evidence inspection error: {e}")

        # Ledger comparison
        ledger_entry = adapter.ledger_data.get(bug_id)
        if ledger_entry:
            sev_match = (ledger_entry["severity"] == parsed["severity"])
            st_match = (ledger_entry["status"] == parsed["status"])
            ledger_status = "PASS" if (sev_match and st_match) else "FAIL"
            if not (sev_match and st_match):
                err_details.append(f"Ledger mismatch: sev({ledger_entry['severity']} vs {parsed['severity']}), st({ledger_entry['status']} vs {parsed['status']})")
        else:
            err_details.append(f"Bug ID {bug_id} not found in master ledger")

        # Map to contract and validate against schema
        contract_pkg = adapter.map_to_contract(bdir, parsed, ev_files)
        val_errors = adapter.validate_entities(contract_pkg)
        if not val_errors:
            schema_status = "PASS"
        else:
            err_details.extend(val_errors)

        # Save test output outside ART-Product-Validation
        out_path = os.path.join(OUTPUT_DIR, f"{bug_id}_contract.json")
        with open(out_path, "w", encoding="utf-8") as out_fp:
            json.dump(contract_pkg, out_fp, indent=2)

        overall = "PASS" if (parse_status == "PASS" and evidence_status == "PASS" and ledger_status == "PASS" and schema_status == "PASS") else "FAIL"
        results.append({
            "id": bug_id,
            "parse": parse_status,
            "evidence": evidence_status,
            "ledger": ledger_status,
            "schema": schema_status,
            "overall": overall,
            # pyrefly: ignore [bad-assignment]
            "evidence_status_map": ev_status_map,
            "errors": err_details
        })

    # Print summary
    print("\nINGESTION RESULTS MATRIX:")
    print(f"{'Bug ID':<16} | {'Parse':<6} | {'Evidence':<8} | {'Ledger':<6} | {'Schema':<6} | {'Result':<6}")
    print("-" * 62)
    for r in results:
        print(f"{r['id']:<16} | {r['parse']:<6} | {r['evidence']:<8} | {r['ledger']:<6} | {r['schema']:<6} | {r['overall']:<6}")

    all_pass = all(r["overall"] == "PASS" for r in results)
    print("\nOVERALL TEST RESULT:", "PASS" if all_pass else "FAIL")
    if not all_pass:
        print("\nErrors encountered:")
        for r in results:
            if r["errors"]:
                print(f"  {r['id']}: {r['errors']}")

if __name__ == "__main__":
    main()
