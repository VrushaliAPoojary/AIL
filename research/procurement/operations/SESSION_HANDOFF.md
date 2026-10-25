# Research Session Handoff Template

> **Purpose:** Standardized context transfer between research sessions (ChatGPT, Antigravity, or human shifts).  
> **Target:** Copy and paste into the first turn of a new AI conversation to resume work seamlessly without conversational loss.

---

## Instructions for Researchers

Whenever you conclude an investigation sprint or reach context limits in an AI conversation, ask the AI to generate a completed handoff summary matching the template below. Save it in your personal scratch notes or commit it to your research branch if handing off to a collaborator.

When starting a new conversation:
1. Provide [`../MASTER_PROMPT.md`](../MASTER_PROMPT.md) and [`../RESEARCH_STANDARD.md`](../RESEARCH_STANDARD.md).
2. Paste this filled handoff template.
3. State your immediate next objective.

---

## Handoff Document Template

```markdown
# Session Handoff: [Process ID] — [Sprint / Date]

### 1. Session Metadata
- **Contributor / Owner:** [Chiranjeevi | Vrushali | Bhushan | Ashwin]
- **Assigned Process:** [P01-RFP | P02-SUPPLIER-DELIVERY | P03-REPLENISHMENT | P04-INVOICE-EXCEPTIONS]
- **Active Git Branch:** [e.g., research/vrushali-delivery-001]
- **Latest Commit Hash:** [e.g., a1b2c3d]
- **Investigation Objective:** [1-2 sentences on what this session was investigating]

### 2. Verified Findings & Evidence Added
- **[CLM-P0x-xxx]:** [Description of finding]
  - *Evidence ID:* [EVD-P0x-xxx]
  - *Evidence Level:* [E1 | E2 | E3 | E4]
  - *Verbatim Source Quote:* "[Exact quotation]"
  - *Source URL / Reference:* [Canonical URL]

### 3. Hypotheses Under Evaluation (E0)
- **[CLM-P0x-yyy]:** [Unvalidated hypothesis currently being researched]
  - *Current Status:* Pending empirical documentation or practitioner interview.

### 4. Open Ambiguities & Contradictions
- **[AMB-P0x-zzz] (Level A1-A4):** [Description of gap or conflicting evidence]
  - *Required Evidence:* [What specific fact is needed to close this]
  - *Current Blockers:* [Is this blocking downstream work?]

### 5. Incumbent Software Audited
- **Vendors / Systems Evaluated:** [e.g., SAP S/4HANA MM, Coupa BSM]
- **Verified Capabilities:** [What they already solve out of the box]
- **Documented Automation Deficit:** [Why humans still intervene]

### 6. Files Changed in Working Tree
- `research/procurement/processes/P0x-.../investigation.md`
- `research/procurement/processes/P0x-.../evidence.md`
- `research/procurement/processes/P0x-.../workflow.md`
- `research/procurement/processes/P0x-.../art-validation.md`

### 7. Validation Checks Executed Locally
- Workspace Link & Schema Validator: [PASSED | FAILED]
- Link Validation Result: [0 broken links]
- Contributor Directory Boundary Check: [PASSED - 100% within assigned folder]

### 8. Pending Decisions & Escalations
- [Any architectural questions or cross-process dependencies requiring Coordinator Chiranjeevi's input]

### 9. Exact Next Action for Incoming Session
- [Specific step to perform immediately upon opening the new conversation, e.g.: "Investigate Coupa ASN discrepancy handling documentation at <URL>."]
```
