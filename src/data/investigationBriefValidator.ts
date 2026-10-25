import type { InvestigationBrief } from '../types/investigationBrief';

const VALID_STATUSES = new Set(['UNKNOWN', 'UNVERIFIED', 'PENDING', 'ACTIVE', 'PASSED', 'FAILED', 'BLOCKED', 'SURVIVED', 'KILLED']);
const VALID_WORKFLOW_TYPES = new Set(['OBSERVED', 'RECONSTRUCTED', 'PROPOSED_ART']);
const VALID_RELATIONSHIP_TYPES = new Set(['CONTRADICTS', 'SUPPORTS', 'DEPENDS_ON']);
const VALID_INTELLIGENCE_TYPES = new Set([
  'WORKFLOW_PATTERN', 'STRATEGY_PATTERN', 'DECISION_PATTERN', 'IMPLEMENTATION_PATTERN',
  'ARCHITECTURE_PATTERN', 'GUARDRAIL', 'METRIC_PATTERN', 'RESEARCH_METHOD',
  'DESIGN_PRINCIPLE', 'NEGATIVE_INTELLIGENCE', 'ART_IMPROVEMENT'
]);
const VALID_EVIDENCE_STATUSES = new Set(['VERIFIED', 'PARTIAL', 'HYPOTHESIS', 'UNKNOWN', 'REJECTED']);
const VALID_LIFECYCLE_STATUSES = new Set(['ACTIVE', 'EXPERIMENTAL', 'RETIRED']);
const VALID_CONFIDENCE_LEVELS = new Set(['HIGH', 'MEDIUM', 'LOW']);
const VALID_REUSE_POTENTIALS = new Set(['HIGH', 'MEDIUM', 'LOW']);
const VALID_EPISTEMIC_CLASSIFICATIONS = new Set(['EVIDENCE', 'CLAIM', 'INFERENCE', 'HYPOTHESIS', 'FALSIFICATION', 'RESULT', 'DECISION']);
const VALID_FALSIFICATION_OUTCOMES = new Set(['KILLED', 'WEAKENED', 'UNRESOLVED', 'SURVIVED']);

export interface ValidationError {
  field: string;
  message: string;
}

export function validateInvestigationBrief(data: any): { valid: boolean; errors: ValidationError[]; brief?: InvestigationBrief } {
  const errors: ValidationError[] = [];

  const checkRequired = (obj: any, fields: string[], path: string) => {
    if (!obj) {
      errors.push({ field: path, message: 'Object is null or undefined' });
      return false;
    }
    for (const field of fields) {
      if (!(field in obj)) {
        errors.push({ field: `${path}.${field}`, message: 'Missing required field' });
      }
    }
    return true;
  };

  const checkStatus = (status: any, path: string) => {
    if (!VALID_STATUSES.has(status)) {
      errors.push({ field: path, message: `Invalid status: ${status}` });
    }
  };

  const checkProvenance = (prov: any, path: string) => {
    if (checkRequired(prov, ['source_file', 'section', 'line_start', 'line_end'], path)) {
      if (typeof prov.source_file !== 'string') errors.push({ field: `${path}.source_file`, message: 'Must be a string' });
      if (prov.section !== null && typeof prov.section !== 'string') errors.push({ field: `${path}.section`, message: 'Must be a string or null' });
      if (prov.line_start !== null && typeof prov.line_start !== 'number') errors.push({ field: `${path}.line_start`, message: 'Must be a number or null' });
      if (prov.line_end !== null && typeof prov.line_end !== 'number') errors.push({ field: `${path}.line_end`, message: 'Must be a number or null' });
      if (prov.url !== undefined && prov.url !== null && typeof prov.url !== 'string') errors.push({ field: `${path}.url`, message: 'Must be a string, null, or omitted' });
    }
  };

  if (typeof data !== 'object' || data === null) {
    return { valid: false, errors: [{ field: 'root', message: 'Data must be an object' }] };
  }

  const rootFields = [
    'investigation_id', 'company', 'industry', 'opportunity', 'investigation_type', 'research_status',
    'presentation', 'decision', 'primary_question',
    'sources', 'checkpoints', 'evidence', 'claims', 'inferences', 'hypotheses', 'results',
    'traceability'
  ];

  if (!checkRequired(data, rootFields, 'root')) {
    return { valid: false, errors };
  }

  checkStatus(data.research_status, 'root.research_status');

  const allKnownIds = new Set<string>();
  const collectIds = (arr: any[]) => {
    if (Array.isArray(arr)) {
      arr.forEach(item => {
        if (item && item.id) allKnownIds.add(item.id);
      });
    }
  };

  collectIds(data.sources);
  collectIds(data.checkpoints);
  collectIds(data.evidence);
  collectIds(data.claims);
  collectIds(data.inferences);
  collectIds(data.hypotheses);
  collectIds(data.results);
  collectIds(data.presentation?.key_findings);
  collectIds(data.decision?.reusable_intelligence);

  if (Array.isArray(data.sections)) {
    collectIds(data.sections);
  }
  if (Array.isArray(data.relationships)) {
    collectIds(data.relationships);
  }
  if (Array.isArray(data.workflows)) {
    collectIds(data.workflows);
    data.workflows.forEach((workflow: any) => collectIds(workflow.steps));
  }

  const checkRefs = (refs: any, path: string) => {
    if (refs == null) return;
    if (Array.isArray(refs)) {
      refs.forEach((ref, idx) => {
        if (!allKnownIds.has(ref)) {
          errors.push({ field: `${path}[${idx}]`, message: `UNKNOWN ID: ${ref}` });
        }
      });
      return;
    }
    errors.push({ field: path, message: 'Must be an array when present' });
  };

  if (checkRequired(data.presentation, ['investigation_summary', 'key_findings'], 'presentation')) {
    if (Array.isArray(data.presentation.key_findings)) {
      data.presentation.key_findings.forEach((kf: any, i: number) => {
        if (checkRequired(kf, ['id', 'statement', 'classification', 'source_refs'], `presentation.key_findings[${i}]`)) {
          if (!VALID_EPISTEMIC_CLASSIFICATIONS.has(kf.classification)) {
            errors.push({ field: `presentation.key_findings[${i}].classification`, message: `Invalid epistemic classification: ${kf.classification}` });
          }
          checkRefs(kf.source_refs, `presentation.key_findings[${i}].source_refs`);
        }
      });
    } else {
      errors.push({ field: 'presentation.key_findings', message: 'Must be an array' });
    }
  }

  if (checkRequired(data.decision, ['decision', 'reason', 'reusable_intelligence', 'provenance'], 'decision')) {
    checkProvenance(data.decision.provenance, 'decision.provenance');
    if (Array.isArray(data.decision.reusable_intelligence)) {
      data.decision.reusable_intelligence.forEach((intel: any, i: number) => {
        const path = `decision.reusable_intelligence[${i}]`;
        if (checkRequired(intel, [
          'id', 'type', 'title', 'domain', 'description',
          'evidence_status', 'status', 'confidence', 'reuse_potential',
          'applications', 'source_refs', 'tags', 'provenance'
        ], path)) {
          if (!VALID_INTELLIGENCE_TYPES.has(intel.type)) {
            errors.push({ field: `${path}.type`, message: `Invalid intelligence type: ${intel.type}` });
          }
          if (!VALID_EVIDENCE_STATUSES.has(intel.evidence_status)) {
            errors.push({ field: `${path}.evidence_status`, message: `Invalid evidence status: ${intel.evidence_status}` });
          }
          if (!VALID_LIFECYCLE_STATUSES.has(intel.status)) {
            errors.push({ field: `${path}.status`, message: `Invalid lifecycle status: ${intel.status}` });
          }
          if (!VALID_CONFIDENCE_LEVELS.has(intel.confidence)) {
            errors.push({ field: `${path}.confidence`, message: `Invalid confidence level: ${intel.confidence}` });
          }
          if (!VALID_REUSE_POTENTIALS.has(intel.reuse_potential)) {
            errors.push({ field: `${path}.reuse_potential`, message: `Invalid reuse potential: ${intel.reuse_potential}` });
          }
          checkProvenance(intel.provenance, `${path}.provenance`);
          checkRefs(intel.source_refs, `${path}.source_refs`);
        }
      });
    } else {
      errors.push({ field: 'decision.reusable_intelligence', message: 'Must be an array of intelligence objects' });
    }
  }

  if (Array.isArray(data.sources)) {
    data.sources.forEach((src: any, i: number) => {
      if (checkRequired(src, ['id', 'title', 'url', 'source_type', 'used_by'], `sources[${i}]`)) {
        checkRefs(src.used_by, `sources[${i}].used_by`);
      }
    });
  } else {
    errors.push({ field: 'sources', message: 'Must be an array' });
  }

  if (Array.isArray(data.checkpoints)) {
    data.checkpoints.forEach((cp: any, i: number) => {
      if (checkRequired(cp, ['id', 'title', 'what_changed', 'provenance'], `checkpoints[${i}]`)) {
        checkProvenance(cp.provenance, `checkpoints[${i}].provenance`);
        if (cp.status !== undefined && cp.status !== null && typeof cp.status !== 'string') {
          errors.push({ field: `checkpoints[${i}].status`, message: 'Must be a string or null' });
        }
        if (cp.investigation_question !== undefined && cp.investigation_question !== null && typeof cp.investigation_question !== 'string') {
          errors.push({ field: `checkpoints[${i}].investigation_question`, message: 'Must be a string or null' });
        }
        if (cp.tested !== undefined && cp.tested !== null && typeof cp.tested !== 'string') {
          errors.push({ field: `checkpoints[${i}].tested`, message: 'Must be a string or null' });
        }
        if (cp.found !== undefined && cp.found !== null && typeof cp.found !== 'string') {
          errors.push({ field: `checkpoints[${i}].found`, message: 'Must be a string or null' });
        }
        if (cp.resulting_state !== undefined && cp.resulting_state !== null && typeof cp.resulting_state !== 'string') {
          errors.push({ field: `checkpoints[${i}].resulting_state`, message: 'Must be a string or null' });
        }
        checkRefs(cp.evidence_refs, `checkpoints[${i}].evidence_refs`);
        checkRefs(cp.source_refs, `checkpoints[${i}].source_refs`);
      }
    });
  } else {
    errors.push({ field: 'checkpoints', message: 'Must be an array' });
  }

  if (Array.isArray(data.workflows)) {
    data.workflows.forEach((wf: any, i: number) => {
      if (checkRequired(wf, ['id', 'title', 'workflow_type', 'steps', 'provenance'], `workflows[${i}]`)) {
        if (!VALID_WORKFLOW_TYPES.has(wf.workflow_type)) {
          errors.push({ field: `workflows[${i}].workflow_type`, message: `Invalid workflow type: ${wf.workflow_type}` });
        }
        checkProvenance(wf.provenance, `workflows[${i}].provenance`);
        checkRefs(wf.source_refs, `workflows[${i}].source_refs`);
        if (Array.isArray(wf.steps)) {
          wf.steps.forEach((step: any, j: number) => {
            const path = `workflows[${i}].steps[${j}]`;
            if (checkRequired(step, ['id', 'title', 'description', 'provenance'], path)) {
              checkProvenance(step.provenance, `${path}.provenance`);
              checkRefs(step.exception_refs, `${path}.exception_refs`);
              checkRefs(step.evidence_refs, `${path}.evidence_refs`);
              checkRefs(step.source_refs, `${path}.source_refs`);
            }
          });
        } else {
          errors.push({ field: `workflows[${i}].steps`, message: 'Must be an array' });
        }
      }
    });
  }

  if (Array.isArray(data.sections)) {
    data.sections.forEach((section: any, i: number) => {
      if (checkRequired(section, ['id', 'title', 'provenance'], `sections[${i}]`)) {
        checkProvenance(section.provenance, `sections[${i}].provenance`);
        checkRefs(section.evidence_refs, `sections[${i}].evidence_refs`);
        checkRefs(section.source_refs, `sections[${i}].source_refs`);
      }
    });
  }

  if (Array.isArray(data.relationships)) {
    data.relationships.forEach((rel: any, i: number) => {
      if (checkRequired(rel, ['id', 'source_id', 'target_id', 'relationship_type', 'provenance'], `relationships[${i}]`)) {
        if (!VALID_RELATIONSHIP_TYPES.has(rel.relationship_type)) {
          errors.push({ field: `relationships[${i}].relationship_type`, message: `Invalid relationship type: ${rel.relationship_type}` });
        }
        checkProvenance(rel.provenance, `relationships[${i}].provenance`);
        if (!allKnownIds.has(rel.source_id)) {
          errors.push({ field: `relationships[${i}].source_id`, message: `UNKNOWN ID: ${rel.source_id}` });
        }
        if (!allKnownIds.has(rel.target_id)) {
          errors.push({ field: `relationships[${i}].target_id`, message: `UNKNOWN ID: ${rel.target_id}` });
        }
      }
    });
  }

  if (Array.isArray(data.evidence)) {
    data.evidence.forEach((ev: any, i: number) => {
      if (checkRequired(ev, ['id', 'statement', 'classification', 'source', 'provenance'], `evidence[${i}]`)) {
        checkProvenance(ev.provenance, `evidence[${i}].provenance`);
      }
    });
  } else {
    errors.push({ field: 'evidence', message: 'Must be an array' });
  }

  if (Array.isArray(data.claims)) {
    data.claims.forEach((claim: any, i: number) => {
      if (checkRequired(claim, ['id', 'statement', 'evidence_basis', 'provenance'], `claims[${i}]`)) {
        checkProvenance(claim.provenance, `claims[${i}].provenance`);
        checkRefs(claim.evidence_basis, `claims[${i}].evidence_basis`);
      }
    });
  } else {
    errors.push({ field: 'claims', message: 'Must be an array' });
  }

  if (Array.isArray(data.inferences)) {
    data.inferences.forEach((inf: any, i: number) => {
      if (checkRequired(inf, ['id', 'statement', 'basis', 'implication', 'provenance'], `inferences[${i}]`)) {
        checkProvenance(inf.provenance, `inferences[${i}].provenance`);
        checkRefs(inf.basis, `inferences[${i}].basis`);
      }
    });
  } else {
    errors.push({ field: 'inferences', message: 'Must be an array' });
  }

  if (Array.isArray(data.hypotheses)) {
    data.hypotheses.forEach((hyp: any, i: number) => {
      if (checkRequired(hyp, ['id', 'statement', 'status', 'supporting_basis', 'falsification_basis', 'provenance'], `hypotheses[${i}]`)) {
        checkStatus(hyp.status, `hypotheses[${i}].status`);
        checkProvenance(hyp.provenance, `hypotheses[${i}].provenance`);
        checkRefs(hyp.supporting_basis, `hypotheses[${i}].supporting_basis`);
        checkRefs(hyp.falsification_basis, `hypotheses[${i}].falsification_basis`);
      }
    });
  } else {
    errors.push({ field: 'hypotheses', message: 'Must be an array' });
  }

  if (Array.isArray(data.results)) {
    data.results.forEach((res: any, i: number) => {
      if (checkRequired(res, ['id', 'statement', 'status', 'provenance'], `results[${i}]`)) {
        checkStatus(res.status, `results[${i}].status`);
        checkProvenance(res.provenance, `results[${i}].provenance`);
      }
    });
  } else {
    errors.push({ field: 'results', message: 'Must be an array' });
  }

  if (data.falsification) {
    if (Array.isArray(data.falsification)) {
      data.falsification.forEach((f: any, i: number) => {
        if (checkRequired(f, ['statement', 'outcome', 'basis', 'provenance'], `falsification[${i}]`)) {
          if (!VALID_FALSIFICATION_OUTCOMES.has(f.outcome)) {
            errors.push({ field: `falsification[${i}].outcome`, message: `Invalid falsification outcome: ${f.outcome}` });
          }
          if (f.targetRef !== undefined && f.targetRef !== null && typeof f.targetRef !== 'string') {
            errors.push({ field: `falsification[${i}].targetRef`, message: 'Must be a string or null' });
          }
          if (f.whatWasTested !== undefined && f.whatWasTested !== null && typeof f.whatWasTested !== 'string') {
            errors.push({ field: `falsification[${i}].whatWasTested`, message: 'Must be a string or null' });
          }
          if (f.evidence !== undefined && f.evidence !== null && typeof f.evidence !== 'string') {
            errors.push({ field: `falsification[${i}].evidence`, message: 'Must be a string or null' });
          }
          if (f.reason !== undefined && f.reason !== null && typeof f.reason !== 'string') {
            errors.push({ field: `falsification[${i}].reason`, message: 'Must be a string or null' });
          }
          checkRefs(f.basis, `falsification[${i}].basis`);
          checkProvenance(f.provenance, `falsification[${i}].provenance`);
        }
      });
    } else {
      errors.push({ field: 'falsification', message: 'Must be an array if present' });
    }
  }

  if (Array.isArray(data.traceability)) {
    data.traceability.forEach((tr: any, i: number) => {
      if (checkRequired(tr, ['statement', 'research_location', 'source_urls', 'provenance'], `traceability[${i}]`)) {
        checkProvenance(tr.provenance, `traceability[${i}].provenance`);
        if (!Array.isArray(tr.source_urls)) {
          errors.push({ field: `traceability[${i}].source_urls`, message: 'Must be an array' });
        } else {
          tr.source_urls.forEach((url: any, j: number) => {
            if (typeof url !== 'string') {
              errors.push({ field: `traceability[${i}].source_urls[${j}]`, message: 'Must be a string' });
            }
          });
        }
      }
    });
  } else {
    errors.push({ field: 'traceability', message: 'Must be an array' });
  }

  return {
    valid: errors.length === 0,
    errors,
    brief: errors.length === 0 ? data as InvestigationBrief : undefined
  };
}
