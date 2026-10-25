#!/usr/bin/env python3
"""
Procurement Workspace Validator
Validates structural integrity, link resolution, process file inventory,
epistemic schema compliance, duplicate ID avoidance, and scope boundaries
for ART Procurement Research.

Standard Library only; zero external dependencies.
"""

import os
import sys
import re
import argparse
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Permitted paths for procurement research
PERMITTED_PREFIXES = (
    "research/procurement/",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/CODEOWNERS",
    ".github/workflows/procurement-pr-check.yml",
    "scripts/procurement/",
)

REQUIRED_PROCESSES = {
    "P01-RFP": "Chiranjeevi",
    "P02-SUPPLIER-DELIVERY": "Vrushali",
    "P03-REPLENISHMENT": "Bhushan",
    "P04-INVOICE-EXCEPTIONS": "Ashwin",
}

REQUIRED_PROCESS_FILES = (
    "investigation.md",
    "evidence.md",
    "workflow.md",
    "art-validation.md",
)

REQUIRED_GOVERNANCE_FILES = (
    "README.md",
    "MASTER_PROMPT.md",
    "RESEARCH_STANDARD.md",
    "OWNERSHIP.md",
    "EVIDENCE_REGISTER.md",
    "AMBIGUITIES.md",
    "DECISIONS.md",
)

SUSPICIOUS_PATTERNS = [
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), "Private key block detected"),
    (re.compile(r"(?:ghp_|gho_|ghu_|ghs_|ghr_)[A-Za-z0-9_]{30,}"), "GitHub token pattern detected"),
    (re.compile(r"(?:api[_-]?key|secret[_-]?key)\s*[:=]\s*['\"][A-Za-z0-9_-]{16,}['\"]", re.IGNORECASE), "Likely API key / secret assignment"),
]


def check_utf8_and_credentials(repo_root):
    errors = []
    warnings = []
    base_dir = repo_root / "research" / "procurement"
    for path in base_dir.rglob("*.md"):
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"Non-UTF8 file: {path.relative_to(repo_root)}: {exc}")
            continue

        for pattern, label in SUSPICIOUS_PATTERNS:
            if pattern.search(content):
                errors.append(f"Potential credential in {path.relative_to(repo_root)}: {label}")
    return errors, warnings


def check_required_files(repo_root):
    errors = []
    proc_root = repo_root / "research" / "procurement"

    for gov_file in REQUIRED_GOVERNANCE_FILES:
        target = proc_root / gov_file
        if not target.is_file():
            errors.append(f"Missing required governance file: research/procurement/{gov_file}")

    for proc_id in REQUIRED_PROCESSES:
        proc_dir = proc_root / "processes" / proc_id
        if not proc_dir.is_dir():
            errors.append(f"Missing required process directory: research/procurement/processes/{proc_id}")
            continue
        for req_file in REQUIRED_PROCESS_FILES:
            target = proc_dir / req_file
            if not target.is_file():
                errors.append(f"Missing required process file: research/procurement/processes/{proc_id}/{req_file}")

    return errors


def check_markdown_links(repo_root):
    errors = []
    warnings = []
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    base_dir = repo_root / "research" / "procurement"

    for path in base_dir.rglob("*.md"):
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue

        for text, target in link_pattern.findall(content):
            target = target.strip()
            # Ignore absolute web URLs, mailto, etc.
            if target.startswith(("http://", "https://", "mailto:", "ftp://")):
                continue

            parts = target.split("#", 1)
            target_path = parts[0]
            anchor = parts[1] if len(parts) > 1 else None

            if not target_path:
                resolved_file = path
            else:
                resolved_file = (path.parent / target_path).resolve()

            if not resolved_file.exists():
                errors.append(
                    f"Broken link in {path.relative_to(repo_root)}: [{text}]({target}) -> {target_path} not found"
                )
                continue

            if anchor and resolved_file.is_file():
                try:
                    target_content = resolved_file.read_text(encoding="utf-8")
                    slugs = []
                    for line in target_content.splitlines():
                        if line.strip().startswith("#"):
                            heading = line.strip("# ").strip().lower()
                            slug = re.sub(r"[^\w\s-]", "", heading).strip().replace(" ", "-")
                            slug = re.sub(r"-+", "-", slug)
                            slugs.append(slug)
                    if anchor.lower() not in [s.lower() for s in slugs]:
                        warnings.append(
                            f"Anchor warning in {path.relative_to(repo_root)}: #{anchor} in [{text}]({target})"
                        )
                except Exception:
                    pass

    return errors, warnings


def check_ids_and_evidence(repo_root):
    errors = []
    warnings = []
    seen_ids = {}

    id_patterns = [
        ("evidence", re.compile(r"\b(EVD-P0[1-4]-\d{3})\b")),
        ("ambiguity", re.compile(r"\b(AMB-P0[1-4]-\d{3})\b")),
    ]

    proc_root = repo_root / "research" / "procurement"
    for path in proc_root.rglob("*.md"):
        # Skip validation kit benchmarks and templates from duplicate check
        if "validation/RFP-001" in str(path) or "SESSION_HANDOFF" in str(path):
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue

        for kind, pat in id_patterns:
            matches = pat.findall(content)
            for item in matches:
                if item not in seen_ids:
                    seen_ids[item] = []
                seen_ids[item].append(str(path.relative_to(repo_root)))

    # Detect duplicate definitions across files
    for item_id, file_list in seen_ids.items():
        distinct_files = sorted(set(file_list))
        # An ID being referenced across registers or in its own process file is expected,
        # but multiple definitions in different process folders is a violation.
        process_origins = set()
        for f in distinct_files:
            m = re.search(r"processes/(P0[1-4]-[A-Z0-9-]+)", f)
            if m:
                process_origins.add(m.group(1))
        if len(process_origins) > 1:
            errors.append(f"Cross-process ID collision for {item_id}: found across {sorted(process_origins)}")

    # Check art-validation.md has explicit execution status
    for proc_id in REQUIRED_PROCESSES:
        val_file = proc_root / "processes" / proc_id / "art-validation.md"
        if val_file.is_file():
            content = val_file.read_text(encoding="utf-8")
            if "CURRENTLY NOT TESTED" not in content and "STATUS: EXECUTED" not in content and "Execution Status:" not in content:
                warnings.append(f"{proc_id}/art-validation.md lacks explicit Execution Status declaration")

    return errors, warnings


def check_scope_boundaries(repo_root, changed_files):
    errors = []
    if not changed_files:
        return errors

    for f in changed_files:
        f = f.strip()
        if not f:
            continue
        if not any(f.startswith(prefix) for prefix in PERMITTED_PREFIXES):
            errors.append(f"File outside permitted procurement scope modified: {f}")
    return errors


def generate_markdown_summary(errors, warnings, changed_files=None):
    lines = []
    lines.append("## ART Procurement PR Validation Summary\n")
    if not errors:
        lines.append("**:white_check_mark: All procurement workspace checks passed.**\n")
    else:
        lines.append(f"**:x: Validation failed with {len(errors)} error(s).**\n")

    lines.append("| Check Category | Status | Details |")
    lines.append("|---|---|---|")

    # Scope
    scope_errs = [e for e in errors if "outside permitted" in e]
    if scope_errs:
        lines.append(f"| Scope Boundary | :x: Failed | {len(scope_errs)} file(s) outside permitted paths |")
    else:
        lines.append("| Scope Boundary | :white_check_mark: Passed | Changes restricted to procurement workspace |")

    # Required files
    file_errs = [e for e in errors if "Missing required" in e]
    if file_errs:
        lines.append(f"| File Inventory | :x: Failed | {len(file_errs)} required file(s) missing |")
    else:
        lines.append("| File Inventory | :white_check_mark: Passed | All 4 process packages and governance files present |")

    # Links
    link_errs = [e for e in errors if "Broken link" in e]
    if link_errs:
        lines.append(f"| Relative Links | :x: Failed | {len(link_errs)} broken relative link(s) |")
    else:
        lines.append("| Relative Links | :white_check_mark: Passed | 100% relative Markdown links resolve cleanly |")

    # Credentials
    cred_errs = [e for e in errors if "credential" in e]
    if cred_errs:
        lines.append(f"| Security / Secret Scan | :x: Failed | {len(cred_errs)} suspicious credential pattern(s) |")
    else:
        lines.append("| Security / Secret Scan | :white_check_mark: Passed | Zero credential patterns detected |")

    # IDs & Evidence
    id_errs = [e for e in errors if "ID collision" in e]
    if id_errs:
        lines.append(f"| ID Integrity | :x: Failed | {len(id_errs)} cross-process ID collision(s) |")
    else:
        lines.append("| ID Integrity | :white_check_mark: Passed | Zero cross-process ID collisions |")

    if errors:
        lines.append("\n### Detailed Failure Log")
        for err in errors:
            lines.append(f"- :heavy_exclamation_mark: `{err}`")

    if warnings:
        lines.append("\n### Advisory Notices")
        for warn in warnings:
            lines.append(f"- :warning: `{warn}`")

    lines.append("\n*Note: Automated structural validation passing does not substitute for Coordinator Chiranjeevi's peer evidence review.*")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Validate ART procurement workspace.")
    parser.add_argument("--repo-root", default=".", help="Path to repository root")
    parser.add_argument("--changed-files", nargs="*", help="List of changed files in PR")
    parser.add_argument("--summary-file", help="Path to write GitHub step summary markdown")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    all_errors = []
    all_warnings = []

    # 1. UTF-8 & Credentials
    errs, warns = check_utf8_and_credentials(repo_root)
    all_errors.extend(errs)
    all_warnings.extend(warns)

    # 2. Required files
    errs = check_required_files(repo_root)
    all_errors.extend(errs)

    # 3. Links
    errs, warns = check_markdown_links(repo_root)
    all_errors.extend(errs)
    all_warnings.extend(warns)

    # 4. IDs & Evidence
    errs, warns = check_ids_and_evidence(repo_root)
    all_errors.extend(errs)
    all_warnings.extend(warns)

    # 5. Scope boundaries (if changed files provided)
    if args.changed_files:
        errs = check_scope_boundaries(repo_root, args.changed_files)
        all_errors.extend(errs)

    summary = generate_markdown_summary(all_errors, all_warnings, args.changed_files)

    if args.summary_file:
        Path(args.summary_file).write_text(summary + "\n", encoding="utf-8")

    github_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if github_summary_path:
        with open(github_summary_path, "a", encoding="utf-8") as fh:
            fh.write(summary + "\n")

    print(summary)
    sys.exit(1 if all_errors else 0)


if __name__ == "__main__":
    main()
