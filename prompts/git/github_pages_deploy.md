
# GITHUB PAGES DEPLOYMENT HARNESS

## REUSABLE STATIC ARTIFACT PUBLISHER

## PURPOSE

Safely deploy an approved static website/report to GitHub Pages using the
authenticated GitHub CLI without requiring manual GitHub UI deployment.

This harness owns:

STATIC ARTIFACT
→ ISOLATED PUBLISHING REPOSITORY
→ GITHUB PAGES
→ VERIFIED PUBLIC URL

This harness does NOT own generation of the source artifact.

It must never expose the source/private repository merely to enable Pages.

==================================================

1. REQUIRED INPUT
   ==================================================

Provide:

SOURCE_ARTIFACT:
<path to approved index.html or static-site directory></path>

TARGET_OWNER:
<GitHub organization or username></github>

TARGET_REPOSITORY:
<dedicated publishing repository name></dedicated>

TARGET_VISIBILITY:
PUBLIC / PRIVATE

PAGES_BRANCH:
main

PAGES_PATH:
/

Optional:

NOJEKYLL:
YES

Example:

SOURCE_ARTIFACT: docs/index.html
TARGET_OWNER: ART-Automation-Lab
TARGET_REPOSITORY: art-validation-report
TARGET_VISIBILITY: PUBLIC
PAGES_BRANCH: main
PAGES_PATH: /
NOJEKYLL: YES

Do not infer a different target repository if one is explicitly supplied.

==================================================
2. CORE SAFETY RULE
===================

Never enable public GitHub Pages directly from an internal/source repository
unless the user explicitly identifies that repository as the approved
publishing repository.

Default architecture:

SOURCE REPOSITORY
      ↓
approved static artifact
      ↓
ISOLATED PUBLISHING DIRECTORY
      ↓
DEDICATED GITHUB REPOSITORY
      ↓
GitHub Pages

The publishing repository must contain only files intentionally approved for
public deployment.

==================================================
3. PREFLIGHT
============

Before making external changes, inspect:

- git status
- current branch
- git remotes
- authenticated GitHub CLI identity
- target owner access
- target repository existence
- target repository visibility if it exists
- existing GitHub Pages configuration if it exists
- source artifact existence
- source artifact structure

Use GitHub CLI/API where appropriate.

Do not modify anything during preflight.

==================================================
4. AUTHENTICATION
=================

Verify authenticated GitHub CLI access.

Example capability:

gh auth status

If authentication is unavailable:

DEPLOYMENT: BLOCKED
BLOCKER: GITHUB CLI AUTHENTICATION REQUIRED

STOP.

Do not request or print tokens.

==================================================
5. SOURCE ARTIFACT VALIDATION
=============================

Verify SOURCE_ARTIFACT exists.

For a single HTML report:

verify:

index.html or supplied HTML file exists
HTML is structurally valid enough for static publication
required local assets resolve correctly

For a static-site directory:

identify exactly which files are required by the site.

Do not blindly copy the source repository.

==================================================
6. PUBLICATION SECURITY SCAN
============================

Before deployment, inspect all files that would be published.

Check for accidental exposure of:

- credentials
- API keys
- access tokens
- PATs
- passwords
- `.env`
- private keys
- database files
- SQLite files
- internal filesystem paths
- internal-only URLs
- source repository paths
- private evidence
- internal configuration
- hidden development artifacts
- unapproved personal information

Also inspect HTML/JS for unintended executable injection originating from
untrusted source content.

If prohibited content is found:

DEPLOYMENT: BLOCKED
SECURITY SCAN: FAIL

Report the category of exposure without printing the secret.

STOP.

==================================================
7. ISOLATED PUBLISHING DIRECTORY
================================

Create a temporary/isolated publishing directory outside the source
repository's tracked working tree.

Copy ONLY approved static-site artifacts.

For a single generated report:

SOURCE_ARTIFACT
→ isolated/index.html

If NOJEKYLL = YES:

create:

.nojekyll

Do not copy:

.git
.gitignore from source unless intentionally required
.env
databases
source code
tests
logs
evidence
internal Markdown
configuration
credentials
repository history

==================================================
8. VERIFY ISOLATION
===================

Before Git initialization, list the complete publishing directory.

Every file must be explainable as a required public artifact.

If unexpected files exist:

STOP.

Do not publish.

==================================================
9. TARGET REPOSITORY
====================

Check:

TARGET_OWNER/TARGET_REPOSITORY

If repository exists:

verify:

- ownership
- visibility
- purpose
- current contents
- default branch
- Pages configuration

Do NOT overwrite unrelated repositories.

If repository does not exist:

create it using GitHub CLI with the requested visibility.

Example conceptual operation:

gh repo create TARGET_OWNER/TARGET_REPOSITORY ...

Repository creation must happen only when the current execution has explicit
authorization to deploy.

Never change an existing repository's visibility unless explicitly requested.

==================================================
10. GIT ISOLATION
=================

Initialize the isolated publishing directory as its OWN Git repository.

Do NOT reuse source repository Git history.

Do NOT add the publishing repository as a remote of the source repository.

Expected:

isolated-site/
    .git/
    index.html
    .nojekyll

Branch:

PAGES_BRANCH

Default:

main

==================================================
11. COMMIT
==========

Stage only approved public files.

Before commit:

inspect:

git status
git diff --cached

Verify no unexpected file is staged.

Commit using a deployment-specific message.

Example:

Publish static site

or:

Update static site

==================================================
12. PUSH
========

Push the isolated publishing repository to:

TARGET_OWNER/TARGET_REPOSITORY

Branch:

PAGES_BRANCH

Default:

main

Do not force push unless explicitly authorized and necessary.

If the remote repository already contains deployment history, preserve normal
history and update it safely.

==================================================
13. GITHUB PAGES CONFIGURATION
==============================

Configure GitHub Pages programmatically using GitHub CLI/API.

Publishing method:

Deploy from a branch

Source branch:

PAGES_BRANCH

Source directory:

PAGES_PATH

Default:

main / (root)

Equivalent configuration:

branch: main
path: /

Do not require the user to configure Pages manually if authenticated GitHub
permissions permit programmatic configuration.

If Pages is already configured correctly:

leave it unchanged.

==================================================
14. PAGES CONFIGURATION SAFETY
==============================

Do NOT:

- enable Pages on the source repository
- change source repository visibility
- alter organization security policy
- alter unrelated repository settings
- enable unrelated GitHub Actions
- create deployment secrets unnecessarily

If organization policy prevents Pages:

DEPLOYMENT: BLOCKED

Return the exact non-sensitive GitHub error/restriction.

STOP.

==================================================
15. WAIT FOR ACTUAL DEPLOYMENT
==============================

A successful Git push is NOT sufficient evidence of deployment.

After Pages configuration:

check GitHub Pages deployment/build status.

Wait/recheck until:

SUCCESS

or a definitive failure is returned.

Do not report PASS while deployment remains pending.

==================================================
16. DISCOVER PUBLIC URL
=======================

Retrieve the Pages URL from GitHub configuration/API.

Never construct or guess the URL when GitHub can provide the authoritative
value.

Store:

PUBLIC_URL

==================================================
17. PUBLIC SITE VERIFICATION
============================

Request/open PUBLIC_URL.

Verify:

- successful HTTP response
- expected page loads
- expected page title/content exists
- required static assets load
- JavaScript required by the page is present
- no obvious deployment error page is returned

For interactive static reports, verify that required client-side controls are
present.

Do not claim browser-level behavior that was not actually tested.

==================================================
18. PUBLIC EXPOSURE VERIFICATION
================================

After deployment, verify the publishing repository contains only approved
public artifacts.

Check again for:

- secrets
- internal paths
- database files
- private configuration
- source files not intended for publication
- accidental repository history from source project

PRIVATE FILE EXPOSURE must be:

NONE

before PASS.

==================================================
19. SOURCE REPOSITORY IMMUTABILITY
==================================

Verify deployment did not modify the source repository unless the deployment
task explicitly required updating the generated artifact itself.

At minimum verify:

- no publishing remote added
- no Pages configuration added to source repository
- no visibility change
- no deployment commit accidentally created there

==================================================
20. UPDATE EXISTING DEPLOYMENT
==============================

For subsequent executions where TARGET_REPOSITORY already exists:

DO NOT create another repository.

Instead:

1. validate new source artifact
2. run security scan
3. prepare isolated publishing checkout/directory
4. synchronize approved public files
5. inspect diff
6. commit only if content changed
7. push main
8. wait for Pages deployment
9. verify public URL

If there are no content changes:

do not create an empty commit.

Return:

DEPLOYMENT: NO_CHANGE

Verify the existing public site remains accessible.

==================================================
21. REMOVED FILE HANDLING
=========================

When updating an existing static site, remove public files that were part of
the previous deployment but are no longer part of the approved current
artifact.

Do not allow stale public files to remain indefinitely.

However, never delete unexpected remote content automatically if repository
ownership/purpose is ambiguous.

In that case:

STOP.

==================================================
22. IDEMPOTENCY
===============

Running this harness repeatedly with the same source artifact must not:

- create duplicate repositories
- create duplicate Pages configurations
- create empty commits
- change visibility
- alter source repository
- duplicate files

Expected repeated result:

NO_CHANGE

or a normal single update when the artifact changed.

==================================================
23. FAILURE RECOVERY
====================

If repository push succeeds but Pages configuration fails:

report:

PUSH: PASS
PAGES CONFIGURATION: FAIL

Do not pretend the deployment succeeded.

If Pages configuration succeeds but site verification fails:

report:

PAGES DEPLOYMENT: PASS
PUBLIC SITE VERIFICATION: FAIL

Preserve enough non-sensitive diagnostic information for investigation.

==================================================
24. PROHIBITED OPERATIONS
=========================

Unless separately requested, do NOT:

- modify application source
- regenerate source data
- modify databases
- modify Azure DevOps
- modify lifecycle state
- modify canonical records
- change organization settings
- change repository visibility
- delete source repositories
- configure custom domains
- configure DNS
- add analytics
- add telemetry

This harness is deployment only.

==================================================
25. DEPLOYMENT RECORD
=====================

Capture:

- target repository
- deployed commit SHA
- Pages branch
- Pages path
- deployment status
- verified public URL
- deployment timestamp

Do not store credentials.

==================================================
26. REQUIRED COMPLETION OUTPUT
==============================

Return only:

DEPLOYMENT: PASS / NO_CHANGE / BLOCKED / FAILED

SOURCE ARTIFACT:
<path></path>

SOURCE REPOSITORY:
<repository or NOT_APPLICABLE></repository>

SOURCE REPOSITORY MODIFIED:
YES / NO

PUBLISHING REPOSITORY:
<owner/repository>

REPOSITORY CREATED:
YES / NO

REPOSITORY VISIBILITY:
PUBLIC / PRIVATE / UNKNOWN

SECURITY SCAN:
PASS / FAIL

FILES PUBLISHED:
<exact list></exact>

UNEXPECTED FILES:
NONE / <list></list>

COMMIT:
<SHA / NO_CHANGE / NOT_CREATED>

PUSH:
PASS / NO_CHANGE / FAIL

PAGES CONFIGURATION:
PASS / FAIL

PAGES SOURCE:
<branch></branch> / <path></path>

PAGES DEPLOYMENT:
PASS / FAIL / NOT_RUN

PUBLIC URL:
<GitHub-returned URL / NOT_AVAILABLE>

PUBLIC SITE HTTP CHECK:
PASS / FAIL / NOT_RUN

PUBLIC SITE CONTENT CHECK:
PASS / FAIL / NOT_RUN

PRIVATE FILE EXPOSURE:
NONE / DETECTED / NOT_CHECKED

SOURCE HISTORY EXPOSED:
NO / YES / NOT_CHECKED

BLOCKER:
<reason or NONE></reason>

STOP.

==================================================
27. CORE RULE
=============

Deploy the approved artifact.

Never deploy the source repository merely because the artifact lives inside
that repository.

SOURCE
→ SANITIZE
→ ISOLATE
→ COMMIT
→ PUSH
→ CONFIGURE PAGES
→ WAIT
→ VERIFY

A successful push is not a successful deployment.

A successful Pages build is not sufficient until the public URL has also been
verified.
