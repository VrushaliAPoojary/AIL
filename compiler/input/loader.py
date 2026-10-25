import os
import re
import hashlib
from typing import Tuple, List, Dict
from compiler.extraction.interface import ExtractionPackage, Document, ProvenanceIndexItem

def _get_role_and_checkpoint(filename: str):
    if filename == "opportunity.md": return "OPPORTUNITY", None, None
    if filename == "walkthrough.md": return "WALKTHROUGH", None, None
    if filename == "workflow.md": return "WORKFLOW", None, None
    match = re.match(r"^(OPP-\d+-\d+)\.md$", filename, re.IGNORECASE)
    if match:
        cp_id = match.group(1).upper()
        seq_match = re.search(r"-(\d+)$", cp_id)
        seq = int(seq_match.group(1)) if seq_match else 0
        return "CHECKPOINT", cp_id, seq
    return "SUPPORTING_RESEARCH", None, None

def load_investigation_package(directory_path: str) -> ExtractionPackage:
    directory_path = os.path.abspath(directory_path)
    dir_name = os.path.basename(directory_path)
    match = re.match(r"^opportunity(\d+)$", dir_name, re.IGNORECASE)
    opp_number = int(match.group(1)) if match else 0
    investigation_id = f"AOI-SNOW-OPP-{opp_number:03d}"
    
    opp_md = os.path.join(directory_path, "opportunity.md")
    walk_md = os.path.join(directory_path, "walkthrough.md")
    
    if not os.path.exists(opp_md) or not os.path.exists(walk_md):
        raise ValueError("PACKAGE_VALIDATION_ERROR: Missing required source 'opportunity.md' or 'walkthrough.md'.")
        
    all_files = os.listdir(directory_path)
    
    checkpoints = [f for f in all_files if re.match(r"^OPP-\d+-\d+\.md$", f, re.IGNORECASE)]
    
    def cp_sort_key(f):
        _, _, seq = _get_role_and_checkpoint(f)
        return seq or 0
    checkpoints.sort(key=cp_sort_key)
    
    if len(checkpoints) != len(set([c.lower() for c in checkpoints])):
        raise ValueError("PACKAGE_VALIDATION_ERROR: Duplicate checkpoint files detected.")
        
    ordered_filenames = ["opportunity.md", "walkthrough.md"] + checkpoints
    if "workflow.md" in all_files:
        ordered_filenames.append("workflow.md")
        
    remaining = [f for f in all_files if f.endswith(".md") and f not in ordered_filenames]
    remaining.sort()
    ordered_filenames.extend(remaining)
    
    documents = []
    provenance_index = []
    source_manifest = []
    
    for order_idx, filename in enumerate(ordered_filenames):
        path = os.path.join(directory_path, filename)
        with open(path, "rb") as f:
            raw_bytes = f.read()
        
        byte_hash = hashlib.sha256(raw_bytes).hexdigest()
        content = raw_bytes.decode("utf-8").replace("\r\n", "\n")
        lines = content.split('\n')
        line_count = len(lines)
        
        role, cp_id, seq = _get_role_and_checkpoint(filename)
        doc_id = filename.replace(".md", "")
        
        numbered_lines = []
        numbered_lines.append(f"===== BEGIN DOCUMENT =====")
        numbered_lines.append(f"DOCUMENT ID: {doc_id}")
        numbered_lines.append(f"ROLE: {role}")
        numbered_lines.append(f"SOURCE: {filename}")
        if cp_id:
            numbered_lines.append(f"CHECKPOINT: {cp_id}")
        numbered_lines.append(f"SHA256: {byte_hash}")
        numbered_lines.append(f"===== CONTENT =====")
        for i, line in enumerate(lines):
            numbered_lines.append(f"[{filename}:{i+1:03d}] {line}")
        numbered_lines.append(f"===== END DOCUMENT =====")
        
        numbered_content = "\n".join(numbered_lines)
        
        doc = Document(
            document_id=doc_id,
            filename=filename,
            relative_path=filename,
            role=role,
            checkpoint_id=cp_id,
            sha256=byte_hash,
            content=content,
            numbered_content=numbered_content,
            source_order=order_idx + 1
        )
        documents.append(doc)
        source_manifest.append(filename)
        
        pi = ProvenanceIndexItem(
            document_id=doc_id,
            path=filename,
            hash=byte_hash,
            line_count=line_count,
            checkpoint_id=cp_id,
            sequence=seq
        )
        provenance_index.append(pi)
        
    # Assume we run from repository root
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "extraction", "prompts", "investigation_brief_v1.txt")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            extraction_instructions = f.read()
    else:
        # fallback for tests running from different CWD
        fallback_path = "compiler/extraction/prompts/investigation_brief_v1.txt"
        if os.path.exists(fallback_path):
            with open(fallback_path, "r", encoding="utf-8") as f:
                extraction_instructions = f.read()
        else:
            extraction_instructions = "Fallback instructions"
            
    schema_version = "V1"
    compiler_version = "1.0"
    prompt_version = "INVESTIGATION-BRIEF-COMPILER-V1"
    
    hasher = hashlib.sha256()
    hasher.update(schema_version.encode())
    hasher.update(compiler_version.encode())
    hasher.update(prompt_version.encode())
    for d in documents:
        hasher.update(d.sha256.encode())
        
    package_hash = hasher.hexdigest()
    
    return ExtractionPackage(
        investigation_id=investigation_id,
        schema_version=schema_version,
        compiler_version=compiler_version,
        prompt_version=prompt_version,
        package_hash=package_hash,
        source_manifest=source_manifest,
        documents=documents,
        extraction_instructions=extraction_instructions,
        provenance_index=provenance_index
    )
