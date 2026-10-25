import datetime
import json
import uuid
from pathlib import Path
import tempfile

import pytest

from compiler.input.loader import load_investigation_package
from compiler.extraction.interface import ExtractionProvider, ExtractionPackage, ProviderResponse
from compiler.validation.validator import validate_candidate

class MockProvider(ExtractionProvider):
    def __init__(self, status='SUCCESS', raw_response=None):
        self.status = status
        self.raw_response = raw_response

    def extract(self, extraction_input: ExtractionPackage) -> ProviderResponse:
        return ProviderResponse(
            provider='mock',
            model='mock-v1',
            execution_id=uuid.uuid4().hex,
            executed_at=datetime.datetime.utcnow().isoformat(),
            status=self.status,
            raw_response=self.raw_response,
        )

def write_package(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    (root / 'opportunity.md').write_text('opportunity', encoding='utf-8')
    (root / 'walkthrough.md').write_text('walkthrough', encoding='utf-8')
    (root / 'OPP-002-01.md').write_text('checkpoint one', encoding='utf-8')
    return root

def test_package_hash_deterministic(tmp_path):
    pkg_dir = write_package(tmp_path / 'opportunity02')
    pkg1 = load_investigation_package(str(pkg_dir))
    pkg2 = load_investigation_package(str(pkg_dir))
    assert pkg1.package_hash == pkg2.package_hash

def test_source_boundaries_and_numbering(tmp_path):
    pkg_dir = write_package(tmp_path / 'opportunity02')
    pkg = load_investigation_package(str(pkg_dir))
    for doc in pkg.documents:
        assert '===== BEGIN DOCUMENT =====' in doc.numbered_content
        assert f'DOCUMENT ID: {doc.document_id}' in doc.numbered_content
        assert f'ROLE: {doc.role}' in doc.numbered_content
        assert f'[{doc.filename}:001]' in doc.numbered_content
        assert '===== END DOCUMENT =====' in doc.numbered_content

def test_provenance_index(tmp_path):
    pkg_dir = write_package(tmp_path / 'opportunity02')
    pkg = load_investigation_package(str(pkg_dir))
    assert len(pkg.provenance_index) == len(pkg.documents)
    walkthrough = next(p for p in pkg.provenance_index if 'walkthrough' in p.path)
    assert walkthrough.document_id == 'walkthrough'

def test_discovery_and_loader_input(tmp_path):
    pkg_dir = write_package(tmp_path / 'opportunity02')
    extraction_input = load_investigation_package(str(pkg_dir))
    assert extraction_input.investigation_id == 'AOI-SNOW-OPP-002'
    filenames = [sf.relative_path for sf in extraction_input.documents]
    assert 'opportunity.md' in filenames
    assert 'walkthrough.md' in filenames

    assert filenames[0] == 'opportunity.md'
    assert filenames[1] == 'walkthrough.md'
    checkpoints = [f for f in filenames if 'OPP-002' in f]
    assert checkpoints == sorted(checkpoints)

    for sf in extraction_input.documents:
        assert sf.sha256 is not None
        assert len(sf.sha256) == 64

def test_missing_opportunity_md(tmp_path):
    pkg_dir = tmp_path / 'opportunity02'
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / 'walkthrough.md').write_text('test', encoding='utf-8')
    with pytest.raises(ValueError, match='PACKAGE_VALIDATION_ERROR'):
        load_investigation_package(str(pkg_dir))

def test_duplicate_checkpoint(tmp_path):
    pkg_dir = tmp_path / 'opportunity02'
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / 'opportunity.md').write_text('test', encoding='utf-8')
    (pkg_dir / 'walkthrough.md').write_text('test', encoding='utf-8')
    (pkg_dir / 'OPP-002-01.md').write_text('test', encoding='utf-8')
    (pkg_dir / 'opp-002-01.md').write_text('test2', encoding='utf-8')
    if len(list(pkg_dir.iterdir())) == 4:
        with pytest.raises(ValueError, match='Duplicate checkpoint files'):
            load_investigation_package(str(pkg_dir))

def test_mock_provider_failed(tmp_path):
    pkg_dir = write_package(tmp_path / 'opportunity02')
    extraction_input = load_investigation_package(str(pkg_dir))
    provider = MockProvider(status='PROVIDER_EXECUTION_FAILED')
    result = provider.extract(extraction_input)
    assert result.status == 'PROVIDER_EXECUTION_FAILED'

def test_invalid_schema_rejection():
    invalid_data = {
        'investigation_id': '1', 'company': 'a', 'opportunity': 'a',
        'investigation_type': 'type', 'research_status': 'INVALID_STATUS',
        'presentation': {'investigation_summary': 'sum', 'key_findings': []},
        'decision': {'decision': 'd', 'reason': 'r', 'reusable_intelligence': [], 'provenance': {'source_file': 'a', 'section': 'b', 'line_start': 1, 'line_end': 2}},
        'primary_question': 'q', 'sources': [], 'checkpoints': [], 'evidence': [],
        'claims': [], 'inferences': [], 'hypotheses': [], 'results': [], 'traceability': []
    }
    is_valid, errors, _ = validate_candidate(invalid_data)
    assert not is_valid
    assert any(err['error_code'] == 'VALIDATION_SCHEMA_FAILED' for err in errors)

def test_valid_json_success():
    repo_root = Path(__file__).resolve().parents[2]
    valid_json_path = repo_root / 'src/data/investigations/industries/Healthcare/aiims_bhopal/OPP-014.json'
    with valid_json_path.open('r', encoding='utf-8') as f:
        valid_json = json.load(f)

    provider = MockProvider(status='SUCCESS', raw_response=json.dumps(valid_json))
    pkg_dir = write_package(Path(tempfile.mkdtemp()) / 'opportunity02')
    extraction_input = load_investigation_package(str(pkg_dir))
    result = provider.extract(extraction_input)
    assert result.status == 'SUCCESS'

    parsed = json.loads(result.raw_response)
    is_valid, errors, _ = validate_candidate(parsed)
    assert is_valid
    assert not errors
