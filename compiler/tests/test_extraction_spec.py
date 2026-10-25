import os
import re

def get_schema_fields():
    from compiler.validation.models import InvestigationBrief
    schema = InvestigationBrief.model_json_schema()

    def extract_fields(schema_def, prefix=''):
        f_list = []
        if 'properties' in schema_def:
            for k, v in schema_def['properties'].items():
                full_k = f'{prefix}{k}'
                f_list.append(full_k)
                if '$ref' in v:
                    ref_name = v['$ref'].split('/')[-1]
                    if '$defs' in schema:
                        ref_schema = schema['$defs'][ref_name]
                        f_list.extend(extract_fields(ref_schema, f'{full_k}.'))
                elif v.get('type') == 'array' and '$ref' in v.get('items', {}):
                    ref_name = v['items']['$ref'].split('/')[-1]
                    if '$defs' in schema:
                        ref_schema = schema['$defs'][ref_name]
                        f_list.extend(extract_fields(ref_schema, f'{full_k}[i].'))
        return f_list

    return extract_fields(schema)

def test_spec_coverage():
    spec_path = 'artifacts/investigation-brief-extraction-spec-v1.md'
    assert os.path.exists(spec_path)

    with open(spec_path, 'r', encoding='utf-8') as f:
        spec_content = f.read()

    fields = get_schema_fields()

    for field in fields:
        if field.endswith('.provenance.source_file'):
            assert '### provenance.source_file' in spec_content
        elif field.endswith('.provenance.section'):
            assert '### provenance.section' in spec_content
        elif field.endswith('.provenance.line_start'):
            assert '### provenance.line_start' in spec_content
        elif field.endswith('.provenance.line_end'):
            assert '### provenance.line_end' in spec_content
        else:
            assert f'### {field}' in spec_content or f'`{field}`' in spec_content, f'Missing {field} in spec'

def test_enums_represented():
    spec_path = 'artifacts/investigation-brief-extraction-spec-v1.md'
    with open(spec_path, 'r', encoding='utf-8') as f:
        spec_content = f.read()

    assert 'UNKNOWN' in spec_content
    assert 'UNVERIFIED' in spec_content
    assert 'PASSED' in spec_content
    assert 'FAILED' in spec_content

def test_reference_rule():
    prompt_path = 'compiler/extraction/prompts/investigation_brief_v1.txt'
    assert os.path.exists(prompt_path)
    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompt_content = f.read()

    assert 'Every reference' in prompt_content
    assert 'must point to an actual, generated ID' in prompt_content

def test_provenance_rule():
    prompt_path = 'compiler/extraction/prompts/investigation_brief_v1.txt'
    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompt_content = f.read()

    assert 'Every object with a `provenance` field must have' in prompt_content
    assert 'line_start' in prompt_content
    assert 'source_file' in prompt_content

def test_prompt_version():
    assert os.path.exists('compiler/extraction/prompts/investigation_brief_v1.txt')
