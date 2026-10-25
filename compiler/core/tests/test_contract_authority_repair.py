import json
import unittest
from jsonschema import validate
from compiler.core.ir import (
    Evidence,
    EpistemicStatus,
    Investigation,
    Provenance,
    Relationship,
    Source,
    WorkflowModel,
    WorkflowStep,
    Checkpoint,
    Section,
    WorkflowType,
)
from compiler.core.mapper import ContractMapper

class TestContractAuthorityRepair(unittest.TestCase):
    def test_mapper_output_accepts_repaired_ail_contract(self):
        provenance = Provenance(file='research.md', section='Identity', position='L1-L3')
        source = Source(
            id='src-1',
            object_type='source',
            title='Source 1',
            normalized='source-1',
            raw='Source 1 raw',
            epistemic_status=EpistemicStatus.VERIFIED,
            provenance=provenance,
            url='https://example.com/source-1',
            source_type='article',
        )
        evidence = Evidence(
            id='ev-1',
            object_type='evidence',
            title='Evidence 1',
            normalized='evidence-1',
            raw='Evidence 1 raw',
            epistemic_status=EpistemicStatus.OBSERVED,
            provenance=provenance,
            source_refs=['src-1'],
        )
        section = Section(
            id='sec-1',
            object_type='section',
            title='Section 1',
            normalized='section-1',
            raw='Section 1 raw',
            epistemic_status=EpistemicStatus.RECONSTRUCTED,
            provenance=provenance,
            child_ids=['ev-1'],
        )
        step = WorkflowStep(
            id='step-1',
            object_type='workflow_step',
            title='Step 1',
            normalized='step-1',
            raw='Step 1 raw',
            epistemic_status=EpistemicStatus.OBSERVED,
            provenance=provenance,
            actor='analyst',
            system='AIL',
            handoff_to='review',
            state_information='state',
            exception_refs=['ev-1'],
            evidence_refs=['ev-1'],
            source_refs=['src-1'],
        )
        workflow = WorkflowModel(
            id='wf-1',
            object_type='workflow',
            title='Workflow 1',
            normalized='workflow-1',
            raw='Workflow 1 raw',
            epistemic_status=EpistemicStatus.RECONSTRUCTED,
            provenance=provenance,
            workflow_type=WorkflowType.PROPOSED_ART,
            steps=[step],
            actors=['analyst'],
            systems=['AIL'],
            safety_boundaries=['none'],
            source_refs=['src-1'],
            child_ids=['ev-1'],
        )
        checkpoint = Checkpoint(
            id='chk-1',
            object_type='checkpoint',
            title='Checkpoint 1',
            normalized='checkpoint-1',
            raw='Checkpoint 1 raw',
            epistemic_status=EpistemicStatus.OBSERVED,
            provenance=provenance,
            question='What changed?',
            discovered='A change was observed',
            state_changed='State updated',
            child_ids=['ev-1'],
            source_refs=['src-1'],
        )
        relationship = Relationship(
            id='rel-1',
            object_type='relationship',
            title='Relationship 1',
            normalized='relationship-1',
            raw='Relationship 1 raw',
            epistemic_status=EpistemicStatus.UNKNOWN,
            provenance=provenance,
            source_id='ev-1',
            target_id='sec-1',
            rel_type='SUPPORTS',
            source_refs=['src-1'],
        )
        investigation = Investigation(
            id='INV-1',
            object_type='investigation',
            title='Acme Opportunity',
            normalized='investigation-1',
            raw='Investigation raw',
            epistemic_status=EpistemicStatus.UNKNOWN,
            provenance=provenance,
            checkpoints=[checkpoint],
            sections=[section],
            workflows=[workflow],
            sources=[source],
            evidence=[evidence],
            relationships=[relationship],
        )

        mapped, gaps = ContractMapper().map_investigation(investigation)
        self.assertEqual(gaps, [])
        self.assertEqual(mapped['research_status'], 'UNKNOWN')
        self.assertEqual(mapped['workflows'][0]['workflow_type'], 'PROPOSED_ART')
        self.assertEqual(mapped['checkpoints'][0]['provenance']['source_file'], 'research.md')
        self.assertEqual(mapped['sections'][0]['provenance']['section'], 'Identity')

        mapped['decision']['reusable_intelligence'] = [{
            'id': 'intel-1',
            'type': 'WORKFLOW_PATTERN',
            'title': 'Reusable workflow pattern',
            'domain': 'compiler',
            'description': 'Structured reusable intelligence used for contract validation.',
            'evidence_status': 'VERIFIED',
            'status': 'ACTIVE',
            'confidence': 'HIGH',
            'reuse_potential': 'HIGH',
            'applications': ['contract validation'],
            'source_refs': ['src-1'],
            'tags': ['migration'],
            'provenance': {
                'source_file': 'research.md',
                'section': 'Identity',
                'line_start': 1,
                'line_end': 3,
                'url': 'https://example.com/source-1',
            },
        }]

        with open('contracts/AIL-INVESTIGATION-BRIEF-JSON-SCHEMA-V1.json', 'r', encoding='utf-8') as f:
            schema = json.load(f)

        validate(instance=mapped, schema=schema)
        self.assertEqual(mapped['decision']['reusable_intelligence'][0]['type'], 'WORKFLOW_PATTERN')
        self.assertEqual(mapped['decision']['reusable_intelligence'][0]['provenance']['url'], 'https://example.com/source-1')

if __name__ == '__main__':
    unittest.main()
