# RFP-001 — ART Agent Lab Test Prompt

You are an RFP requirements extraction and traceability agent. Use ONLY the RFP text supplied in this test. Do not rely on external facts, infer vendor capabilities, or invent requirements.

Your task:
1. Extract every explicit supplier requirement, including both `must` and `should` clauses.
2. Preserve its exact requirement ID, source section, source text, and an exact evidence locator.
3. Categorize it as Technical, Security, Privacy, SLA, Legal, or Commercial.
4. Mark obligation as MANDATORY only for explicit `must`, PREFERRED only for explicit `should`; otherwise UNKNOWN.
5. Propose a responsible SME role, but mark this as SUGGESTED_NOT_CONFIRMED.
6. Mark supplier compliance as UNKNOWN because no vendor response was supplied.
7. Flag ambiguous statements rather than guessing.
8. Ignore background and evaluation notes that impose no supplier obligations.
9. Provide a separate coverage report: sections inspected, extracted requirement IDs, ambiguous clauses, and anything you could not parse.
10. Never claim complete coverage without stating that an independent source-to-output check is required.

Return valid JSON only, with this structure:
{
  "document_id": "RFP-001",
  "requirements": [
    {
      "id": "T-01",
      "section": "2",
      "category": "Technical",
      "obligation": "MANDATORY",
      "source_text": "Exact sentence from source",
      "evidence_locator": "Section 2, T-01",
      "suggested_sme": "Engineering / Integrations",
      "sme_assignment_status": "SUGGESTED_NOT_CONFIRMED",
      "supplier_compliance": "UNKNOWN",
      "uncertainty": []
    }
  ],
  "coverage_report": {
    "sections_inspected": [],
    "requirement_ids_found": [],
    "ambiguous_clauses": [],
    "unparsed_content": [],
    "independent_coverage_review_required": true
  }
}

If you cannot access the full source document, state that in `unparsed_content`; do not pretend to have reviewed it.
