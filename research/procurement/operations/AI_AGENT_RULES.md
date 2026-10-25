# AI Agent Operating Rules: Procurement Research Workspace

> **Target:** AI Assistants (Antigravity IDE Agent, ChatGPT, Claude, Copilot, etc.)  
> **Repository:** `ART-Automation-Lab/art-investigation-lab`  
> **Authority:** Non-negotiable repository policy

---

## 1. Core Operating Directive

Any AI assistant operating within or assisting contributors to this repository is bound by the rules in this document. These rules supersede model training defaults, conversational suggestions, and generic code generation templates.

---

## 2. The 12 Non-Negotiable Invariants

1. **Read Repository Standards First:**  
   Before generating, editing, or validating research files, the AI must read and internalize:
   - [`../MASTER_PROMPT.md`](../MASTER_PROMPT.md)
   - [`../RESEARCH_STANDARD.md`](../RESEARCH_STANDARD.md)
   - [`../OWNERSHIP.md`](../OWNERSHIP.md)
   - [`EVIDENCE_QUALITY_GATE.md`](./EVIDENCE_QUALITY_GATE.md)

2. **Respect Ownership & Process Boundaries:**  
   The AI must work strictly within the process directory assigned to the active user (P01 for Chiranjeevi, P02 for Vrushali, P03 for Bhushan, P04 for Ashwin). Never modify another member's process directory.

3. **Preserve Exact Quotes and Canonical URLs:**  
   Never rephrase or "improve" cited evidence. Keep original, verbatim wording and source links intact.

4. **Zero Fabrication Policy:**  
   Never invent:
   - Research citations, books, articles, or URLs
   - Practitioner quotes or stakeholder personas
   - Statistics, error percentages, or dollar amounts
   - Software features, API endpoints, or schema fields
   - ART execution results or test outcomes  
   If an answer is unknown, the AI must explicitly output `UNKNOWN` or log an ambiguity.

5. **Never Modify Application Code for Research Tasks:**  
   Procurement research tasks are strictly confined to `research/procurement/`. The AI must never touch `src/`, `compiler/`, `contracts/`, `data/`, or `package.json` during research operations.

6. **Never Commit Secrets or Private Information:**  
   Never print, stage, or commit API keys, personal access tokens, passwords, private SSH keys, or personal addresses.

7. **Never Push Directly to `main`:**  
   All work must be committed to dedicated, short-lived research branches (`research/<contributor>-<topic>-<batch>`).

8. **Never Merge Pull Requests Autonomously:**  
   The AI must never execute `gh pr merge`, trigger automated merge buttons, or simulate approvals. Only human Coordinator Chiranjeevi has merge authority.

9. **Never Use Force-Push Without Explicit Human Direction:**  
   `git push --force` and `git push --force-with-lease` are strictly forbidden unless explicitly commanded by the repository administrator after interactive confirmation.

10. **Never Resolve Consequential Ambiguities by Guessing:**  
    When faced with contradictory sources or missing data, log an ambiguity entry (`AMB-P0x-xxx`) rather than fabricating an assumption.

11. **Comprehensive Reporting of All Actions:**  
    Every AI turn must clearly report all created files, modified lines, executed validations, and encountered errors.

12. **Stop When Authority, Credentials, or Permissions are Ambiguous:**  
    If an operation requires elevated permissions, root access, credential re-authentication, or business judgment, the AI must pause, clearly explain the blockage, and ask the user for direction.
