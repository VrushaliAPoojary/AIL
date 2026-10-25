import json
import os
import uuid

def atomic_write(filepath: str, data: dict):
    tmp_path = filepath + f".tmp.{uuid.uuid4().hex}"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    # validate file written
    with open(tmp_path, "r", encoding="utf-8") as f:
        json.load(f)
    os.replace(tmp_path, filepath)

def save_investigation_brief(brief: dict, investigation_id: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{investigation_id}.json")
    atomic_write(file_path, brief)
    return file_path
    
def save_failure_record(record: dict, execution_id: str):
    output_dir = "artifacts/compiler-runs"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{execution_id}.json")
    atomic_write(file_path, record)
    return file_path
