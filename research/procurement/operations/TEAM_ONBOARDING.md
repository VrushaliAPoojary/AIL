# Procurement Research Team Onboarding Guide

> **Audience:** Research Contributors (Chiranjeevi, Vrushali, Bhushan, Ashwin)  
> **Repository:** `ART-Automation-Lab/art-investigation-lab`  
> **Scope:** Markdown research in [`../processes/`](../processes/)  
> **Prerequisites:** Git CLI, GitHub account, Antigravity IDE (No Node.js or application dependencies required)

---

## 1. Quick Start: Minimum Setup for Research

As a research contributor, you are authoring structured Markdown investigations, evidence registries, and process workflow maps. **You do NOT need to install or build the full Next.js application, install Node dependencies, or configure backend services.**

### Step 1: GitHub Access & Membership
1. Ensure your GitHub account has been invited as a member/collaborator to the [`ART-Automation-Lab`](https://github.com/ART-Automation-Lab) organization with read/write access to `art-investigation-lab`.
2. Confirm two-factor authentication (2FA) is enabled on your GitHub account.

### Step 2: Git Setup & Authentication
Install Git on your workstation if not already available:
- **Ubuntu/Debian:** `sudo apt update && sudo apt install git gh -y`
- **macOS:** `brew install git gh`
- **Windows:** Install Git for Windows and GitHub CLI (`winget install GitHub.cli`)

Authenticate securely via GitHub CLI using the browser (never share or hardcode tokens):
```bash
gh auth login
# Select: GitHub.com -> HTTPS -> Authenticate Git with GitHub credentials (Y) -> Login with a web browser
```
Verify your identity:
```bash
gh auth status
```

### Step 3: Create Workspace & Clone Repository
Create a dedicated folder for your ART work and clone the repository:
```bash
mkdir -p ~/ART
cd ~/ART
git clone https://github.com/ART-Automation-Lab/art-investigation-lab.git
cd art-investigation-lab
```

### Step 4: Open in Antigravity
Open the cloned repository folder directly in **Antigravity IDE**:
```bash
agy .
```
Verify that the workspace root is `/path/to/art-investigation-lab`.

---

## 2. Daily Research Workflow

All research follows a lightweight, short-lived branch model.

### 1. Synchronize with Latest `main`
Always start your work session from the most recent, approved `main` branch:
```bash
git checkout main
git pull origin main
```

### 2. Switch to Your Assigned Research Branch
Switch to your assigned research branch (safe checkout automatically tracks `origin` if present and never overwrites existing local work):
```bash
git checkout research/vrushali       # for P02 (VrushaliAPoojary)
git checkout research/bhushan        # for P03 (BhushanShenoy07)
git checkout research/ashwin         # for P04 (ashwinash19)
git checkout research/chiranjeevi    # for P01 (Chiranjeevi005)
```

### 3. Edit Assigned Markdown Files
Modify **only** files within your assigned process directory under [`../processes/`](../processes/):
- **P01:** [`../processes/P01-RFP/`](../processes/P01-RFP/) (Chiranjeevi)
- **P02:** [`../processes/P02-SUPPLIER-DELIVERY/`](../processes/P02-SUPPLIER-DELIVERY/) (Vrushali)
- **P03:** [`../processes/P03-REPLENISHMENT/`](../processes/P03-REPLENISHMENT/) (Bhushan)
- **P04:** [`../processes/P04-INVOICE-EXCEPTIONS/`](../processes/P04-INVOICE-EXCEPTIONS/) (Ashwin)

Never modify files in `src/`, `contracts/`, or another member's process folder.

### 4. Run Local Pre-Flight Check
Before committing, run the procurement workspace validator script:
```bash
python3 scripts/procurement/validate-procurement-workspace.py
```
Ensure 0 broken links, correct process assignments, and valid evidence schemas.

### 5. Commit and Push
Stage and commit your specific research changes with clear commit messages:
```bash
git status
git add research/procurement/processes/P0x-.../
git commit -m "docs(p0x): add verified supplier acknowledgment evidence"
git push -u origin <your-branch-name>
```

### 6. Open a Pull Request
Create a PR targeting `main` on GitHub:
```bash
gh pr create --base main --fill
```
Fill out all fields in the standard Pull Request template.

### 7. Incorporate Feedback
If Coordinator Chiranjeevi requests changes, make your edits on the **same branch**, commit, and push:
```bash
git add research/procurement/processes/P0x-.../
git commit -m "docs(p0x): resolve citation ambiguity AMB-P0x-002"
git push origin <your-branch-name>
```
Once approved, Chiranjeevi will merge the PR.

---

## 3. Updating Your Branch After `main` Changes

If other teammates' PRs have merged into `main` while you are working:
```bash
git fetch origin
git rebase origin/main
git push origin <your-branch-name>
```
Because each researcher works strictly inside their own process directory, rebasing should never produce file conflicts.

---

## 4. Recovering Safely from Common Git Mistakes

### Mistake 1: Accidental Edits Outside Assigned Folder
If you accidentally edited files outside `research/procurement/`:
```bash
# Check what was touched
git status

# Discard changes to an unintended file (e.g. in src/ or contracts/)
git restore path/to/unintended-file
```

### Mistake 2: Accidentally Committed to `main` Locally
If you made a commit on `main` instead of creating a branch:
```bash
# Stash any uncommitted work first to prevent data loss:
git stash

# Create a new branch carrying your commit
git branch research/<your-name>-work

# Safely reset your local main to match remote origin/main without destroying uncommitted work:
git checkout main
git reset --keep origin/main

# Switch back to your working branch and restore stashed work:
git checkout research/<your-name>-work
git stash pop
```

### Mistake 3: "Detached HEAD" State
If Git indicates `HEAD detached at ...`:
```bash
git checkout <your-branch-name>
```

---

## 5. Security & Help Protocol

- **Zero Credential Sharing:** Never share personal passwords, tokens, API keys, or private SSH keys with teammates or in chat.
- **Reporting Issues:** If you encounter permission errors, open an issue or message Coordinator Chiranjeevi with:
  1. The exact command you ran
  2. The sanitized terminal error message
  3. Your current branch name (`git branch --show-current`)
