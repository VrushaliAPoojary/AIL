from typing import Protocol, Dict, Any, List, Optional
from pydantic import BaseModel
import datetime

class ProvenanceIndexItem(BaseModel):
    document_id: str
    path: str
    hash: str
    line_count: int
    checkpoint_id: Optional[str] = None
    sequence: Optional[int] = None

class Document(BaseModel):
    document_id: str
    filename: str
    relative_path: str
    role: str
    checkpoint_id: Optional[str] = None
    sha256: str
    content: str
    numbered_content: str
    source_order: int

class ExtractionPackage(BaseModel):
    investigation_id: str
    schema_version: str
    compiler_version: str
    prompt_version: str
    package_hash: str
    source_manifest: List[str]
    documents: List[Document]
    extraction_instructions: str
    provenance_index: List[ProvenanceIndexItem]

class ProviderResponse(BaseModel):
    provider: str
    model: str
    execution_id: str
    raw_response: Optional[str] = None
    executed_at: str
    status: str
    warnings: List[str] = []

class ExtractionProvider(Protocol):
    def extract(self, extraction_input: ExtractionPackage) -> ProviderResponse:
        ...
