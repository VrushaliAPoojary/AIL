# ART Investigation Lab — Submit My Work for Review

Review my current repository work and prepare a complete GitHub Pull Request for coordinator review.

This is a reusable submission command. Do not restart the investigation, repeat completed ART tests, or generate new research. Report and submit the work that actually exists.

## 1. Identify my workspace

Read and follow:

- `START_HERE.md`
- `prompts/git/start_work.md` — applicable identity and safety rules only
- `prompts/git/submit_work.md`
- `research/procurement/OWNERSHIP.md`
- `research/procurement/RESEARCH_STANDARD.md`

Read `master_prompt.md` if present.

Verify:

- GitHub authenticated identity using `gh api user --jq .login`
- Active branch and upstream
- Assigned process and permitted directory
- Current working-tree status
- Existing commits and uncommitted changes
- Relevant open Pull Requests

Do not switch branches, pull, reset, stash, clean, or overwrite work without first establishing that the operation is safe.

If I am Chiranjeevi, apply coordinator permissions but do not assume that every file in my workspace belongs to the same submission.

If the active branch is `main`, a setup branch, or another non-assigned branch, do not submit directly. Identify the correct submission branch or stop for confirmation.

## 2. Inspect completed work

Examine actual repository changes since the appropriate merge base with the intended target branch.

Include relevant:

- Investigation updates
- Evidence and citations
- Workflow documentation
- ART agent/orchestrator validation records
- Successful and failed test executions
- Local bug records
- Bug pipeline references
- Screenshots, logs, and supporting evidence
- Outstanding blockers

Distinguish committed changes from uncommitted work.

Do not invent missing information.

Do not claim an ART workflow passed merely because documentation says it was planned.

## 3. Check submission scope

Determine whether the changes belong to my assigned process or explicitly authorized coordinator work.

Exclude:

- Other contributors' work
- Unrelated local modifications
- Temporary files
- Virtual environments
- Credentials and secrets
- Unapproved shared-code modifications
- Coordinator-only files when acting as a contributor

Never use `git add .` or `git add -A` indiscriminately.

Stage only explicitly reviewed, in-scope paths.

If the changes mix unrelated work, stop and propose a safe separation plan rather than combining them into one PR.

## 4. Validate before submission

Run the repository's required validation commands according to the existing instructions.

Check:

- Repository scope boundaries
- Markdown links
- Evidence references
- Secret exposure
- Execution records
- Bug references
- Test results

Record the exact commands, actual outcomes, and any failures.

Do not modify tests or shared code to conceal failures.

If required checks fail, stop and explain the failure unless repository policy explicitly permits submitting the work as a draft PR.

## 5. Generate a detailed PR description

Prepare the following report from verified repository content.

### Executive Summary

Explain what was completed and why it matters.

### Investigation Progress

Summarize new findings, evidence quality, and remaining organizational validation needs.

### ART Implementation

Describe actual agents, orchestrators, tools, governance rules, and integrations configured.

If no ART implementation occurred, state "Not performed."

### ART Validation Results

Provide a table with:

- Test ID
- Scenario
- Expected outcome
- Actual outcome
- PASS / FAIL / BLOCKED
- Evidence reference

Do not count planned tests as executed tests.

### Bugs and Retests

List:

- Local bug record
- Canonical/draft bug reference, if available
- Bug pipeline status
- Retest outcome
- Unresolved defects

### Files Changed

List relevant added, modified, and deleted files with their purpose.

### Repository Validation

Include actual commands, passed/failed checks, and known limitations.

### Risks and Blockers

Identify unresolved technical, operational, research, and governance issues.

### Next Actions

State what should happen after coordinator review.

### Coordinator Decisions Required

List only decisions genuinely requiring coordinator approval.

Use "None" when no decision is required.

## 6. Commit and submit

Follow `prompts/git/submit_work.md` and repository Git conventions.

If all required gates pass:

1. Stage only approved, in-scope files.
2. Create a descriptive, atomic commit.
3. Push the assigned submission branch to `origin`.
4. Create a GitHub Pull Request against the repository's authorized integration branch, normally `main`.
5. Use the detailed report as the PR description.
6. Capture the actual PR number and URL.

Before creating a PR, check whether an open PR already exists for the same head and base branches.

If one exists, update its description and push new commits to that branch as appropriate rather than creating a duplicate PR.

Do not merge the PR.

For Chiranjeevi's own submissions, follow the same reviewable PR process. Coordinator authority does not mean bypassing submission safety checks.

Never force-push or perform destructive Git operations.

If the GitHub identity, branch, target, permissions, or submission scope cannot be verified, stop and request clarification.

## 7. Final response

After submission, return:

**ART Investigation Lab — PR Submission Report**

- Contributor:
- Process / Workstream:
- Source Branch:
- Target Branch:
- Commit SHA:
- PR Number:
- PR URL:
- Files Changed:
- Research Status:
- ART Validation: Passed / Failed / Blocked / Not Executed
- Bug Records:
- Repository Tests:
- Outstanding Blockers:
- Coordinator Decisions:

If submission was blocked, clearly state:

- What was completed
- What prevented submission
- Which changes remain local
- The safest next action

**Success condition:** A real, accessible GitHub Pull Request exists with a complete, evidence-backed description of the work submitted.

Do not claim success without verifying the PR through GitHub.
