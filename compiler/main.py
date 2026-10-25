import os
import sys
import json
import datetime
import uuid
import argparse
import hashlib
from compiler.input.loader import load_investigation_package
# pyrefly: ignore [missing-import]
from compiler.extraction.registry import get_provider, ProviderNotFoundError
from compiler.validation.validator import validate_candidate
from compiler.output.writer import save_investigation_brief, save_failure_record, atomic_write

def run_dry_run(opp_dir, provider_name):
    print("Running in DRY-RUN mode.")
    try:
        extraction_input = load_investigation_package(opp_dir)
        print("Package validation: PASS")
        print(f"Investigation ID: {extraction_input.investigation_id}")
        print(f"Package Hash: {extraction_input.package_hash}")
        print("Source files ordered:")
        for doc in extraction_input.documents:
            print(f" - {doc.source_order}: {doc.relative_path} ({doc.role}, {doc.sha256})")
            
        try:
            _ = get_provider(provider_name)
            print(f"Provider configuration: {provider_name}")
        except ProviderNotFoundError:
            print(f"Provider '{provider_name}' NOT FOUND.")
            sys.exit(1)
            
        print("Dry run completed safely.")
        sys.exit(0)
    except Exception as e:
        print(f"Package validation FAILED: {e}")
        sys.exit(1)

def run_validate_only(json_path):
    print(f"Running in VALIDATE-ONLY mode for {json_path}")
    if not os.path.exists(json_path):
        print("File not found.")
        sys.exit(1)
    
    with open(json_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"INVALID_JSON: {e}")
            sys.exit(1)
            
    is_valid, errors, brief = validate_candidate(data)
    if not is_valid:
        print("Validation FAILED.")
        for err in errors:
            print(json.dumps(err))
        sys.exit(1)
        
    print("Validation SUCCESS.")
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Investigation Brief Compiler")
    parser.add_argument("path", help="Path to opportunity directory or JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Run without extraction/output")
    parser.add_argument("--validate-only", action="store_true", help="Validate existing JSON")
    parser.add_argument("--provider", type=str, default="gemini", help="Provider to use for extraction")
    
    args = parser.parse_args()
    
    if args.dry_run:
        run_dry_run(args.path, args.provider)
        
    if args.validate_only:
        run_validate_only(args.path)

    opp_dir = args.path
    
    try:
        extraction_input = load_investigation_package(opp_dir)
    except Exception as e:
        print(f"FAILED to load input: {e}")
        sys.exit(1)
        
    execution_id = uuid.uuid4().hex
    
    snapshot_path = os.path.join("artifacts", "extraction-inputs", f"{execution_id}.json")
    os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
    snapshot = {
        "investigation_id": extraction_input.investigation_id,
        "prompt_version": extraction_input.prompt_version,
        "schema_version": extraction_input.schema_version,
        "source_hashes": {d.relative_path: d.sha256 for d in extraction_input.documents},
        "ordered_documents": extraction_input.source_manifest,
        "content_hashes": {d.relative_path: hashlib.sha256(d.content.encode()).hexdigest() for d in extraction_input.documents},
        "package_hash": extraction_input.package_hash
    }
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)

    try:
        provider = get_provider(args.provider)
    except ProviderNotFoundError:
        print("PROVIDER_NOT_FOUND")
        save_failure_record({
            "investigation_id": extraction_input.investigation_id,
            "execution_id": execution_id,
            "status": "PROVIDER_NOT_FOUND"
        }, execution_id)
        sys.exit(1)
        
    manifest_path = os.path.join("compiled", f"{extraction_input.investigation_id}_MANIFEST.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            prev_manifest = json.load(f)
        
        current_hashes = {d.relative_path: d.sha256 for d in extraction_input.documents}
        prev_hashes = {f["relative_path"]: f["sha256"] for f in prev_manifest.get("source_files", [])} if "source_files" in prev_manifest else {}
        
        if (current_hashes == prev_hashes and 
            prev_manifest.get("schema_version") == extraction_input.schema_version and 
            prev_manifest.get("provider") == args.provider and 
            prev_manifest.get("status") == "SUCCESS"):
            
            if os.path.exists(os.path.join("compiled", f"{extraction_input.investigation_id}.json")):
                print("SKIPPED_UNCHANGED")
                sys.exit(0)
    
    response = provider.extract(extraction_input)
    
    compilation_result = {
        "investigation_id": extraction_input.investigation_id,
        "execution_id": response.execution_id,
        "started_at": response.executed_at,
        "completed_at": datetime.datetime.utcnow().isoformat(),
        "status": response.status,
        "provider": response.provider,
        "model": response.model,
        "prompt_version": extraction_input.prompt_version,
        "source_files": [d.model_dump() for d in extraction_input.documents],
        "schema_version": extraction_input.schema_version,
        "package_hash": extraction_input.package_hash,
        "validation_status": "PENDING",
        "output_path": None,
        "errors": [],
        "warnings": response.warnings,
        "result_hash": None,
        "failure_code": None
    }
    
    if response.status != "SUCCESS":
        compilation_result["failure_code"] = response.status
        save_failure_record(compilation_result, response.execution_id)
        print(response.status)
        sys.exit(1)
        
    if not response.raw_response:
        compilation_result["status"] = "INVALID_PROVIDER_RESPONSE"
        compilation_result["failure_code"] = "INVALID_PROVIDER_RESPONSE"
        save_failure_record(compilation_result, response.execution_id)
        print("INVALID_PROVIDER_RESPONSE")
        sys.exit(1)
        
    try:
        candidate_json = json.loads(response.raw_response)
    except json.JSONDecodeError as e:
        compilation_result["status"] = "INVALID_JSON_RESPONSE"
        compilation_result["failure_code"] = "INVALID_JSON_RESPONSE"
        compilation_result["errors"].append({"message": str(e)})
        save_failure_record(compilation_result, response.execution_id)
        print("INVALID_JSON_RESPONSE")
        sys.exit(1)
        
    compilation_result["result_hash"] = hashlib.sha256(response.raw_response.encode()).hexdigest()
        
    is_valid, errors, brief = validate_candidate(candidate_json)
    
    if not is_valid:
        compilation_result["status"] = "VALIDATION_FAILED"
        compilation_result["failure_code"] = "VALIDATION_FAILED"
        compilation_result["validation_status"] = "FAILED"
        compilation_result["errors"] = errors
        save_failure_record(compilation_result, response.execution_id)
        print("VALIDATION_FAILED")
        sys.exit(1)
        
    compilation_result["status"] = "SUCCESS"
    compilation_result["validation_status"] = "SUCCESS"
    compilation_result["completed_at"] = datetime.datetime.utcnow().isoformat()
    
    output_path = save_investigation_brief(brief.model_dump(), extraction_input.investigation_id, "compiled")
    compilation_result["output_path"] = output_path
    
    atomic_write(manifest_path, compilation_result)
    
    print("SUCCESS")

if __name__ == "__main__":
    main()
