"""
Surgical Patch Applier
Replaces ONLY the vulnerable lines in a file.
Preserves everything else — indentation, comments, surrounding code.
"""
import re
from typing import Optional, Tuple


def apply_surgical_patch(
    original_content: str,
    vulnerable_code: str,
    patched_code: str,
    line_number: Optional[int] = None,
) -> Tuple[str, bool, str]:
    """
    Apply a patch surgically — only replace the vulnerable lines.

    Returns:
        (patched_file_content, success, description)
    """
    if not original_content or not vulnerable_code or not patched_code:
        return original_content, False, "Missing required parameters"

    lines = original_content.split("\n")

    # Strategy 1: Exact line match at known line number
    if line_number and 1 <= line_number <= len(lines):
        target_line = lines[line_number - 1]
        vuln_stripped = vulnerable_code.strip()

        if vuln_stripped in target_line or target_line.strip() == vuln_stripped:
            # Preserve original indentation
            indent = len(target_line) - len(target_line.lstrip())
            indent_str = target_line[:indent]

            # Apply indentation to each line of the patch
            patched_lines = patched_code.strip().split("\n")
            indented_patch = "\n".join(
                indent_str + pl if pl.strip() else pl
                for pl in patched_lines
            )

            lines[line_number - 1] = indented_patch
            result = "\n".join(lines)
            return result, True, f"Patched line {line_number} (exact match)"

    # Strategy 2: Search entire file for the vulnerable snippet
    vuln_stripped = vulnerable_code.strip()
    for i, line in enumerate(lines):
        if vuln_stripped in line or line.strip() == vuln_stripped:
            indent = len(line) - len(line.lstrip())
            indent_str = line[:indent]

            patched_lines = patched_code.strip().split("\n")
            indented_patch = "\n".join(
                indent_str + pl if pl.strip() else pl
                for pl in patched_lines
            )

            lines[i] = indented_patch
            result = "\n".join(lines)
            return result, True, f"Patched line {i+1} (content search)"

    # Strategy 3: Multi-line block replacement
    vuln_block = vulnerable_code.strip()
    content_stripped = original_content
    if vuln_block in content_stripped:
        # Find indentation of first line of the block
        block_start_idx = content_stripped.find(vuln_block)
        line_start = content_stripped.rfind("\n", 0, block_start_idx) + 1
        indent = 0
        for ch in content_stripped[line_start:]:
            if ch in (" ", "\t"):
                indent += 1
            else:
                break
        indent_str = content_stripped[line_start:line_start + indent]

        patched_lines = patched_code.strip().split("\n")
        indented_patch = "\n".join(
            indent_str + pl if pl.strip() else pl
            for pl in patched_lines
        )

        result = content_stripped.replace(vuln_block, indented_patch, 1)
        return result, True, "Patched block (multi-line match)"

    # Strategy 4: Fuzzy match — find closest line
    vuln_words = set(vuln_stripped.lower().split())
    best_match_idx = -1
    best_score = 0

    for i, line in enumerate(lines):
        line_words = set(line.strip().lower().split())
        if not line_words:
            continue
        overlap = len(vuln_words & line_words)
        score = overlap / max(len(vuln_words), len(line_words))
        if score > best_score and score > 0.7:
            best_score = score
            best_match_idx = i

    if best_match_idx >= 0:
        line = lines[best_match_idx]
        indent = len(line) - len(line.lstrip())
        indent_str = line[:indent]

        patched_lines = patched_code.strip().split("\n")
        indented_patch = "\n".join(
            indent_str + pl if pl.strip() else pl
            for pl in patched_lines
        )

        lines[best_match_idx] = indented_patch
        result = "\n".join(lines)
        return result, True, f"Patched line {best_match_idx+1} (fuzzy match {best_score:.0%})"

    return original_content, False, "Could not locate vulnerable code in file — manual review needed"


def build_pr_body(scan, findings_data, chains_data, patches_applied, simulation_results=None):
    """Build a detailed PR description with the full security report."""

    sev_counts = {
        "critical": sum(1 for f in findings_data if f.get("severity") == "critical"),
        "high": sum(1 for f in findings_data if f.get("severity") == "high"),
        "medium": sum(1 for f in findings_data if f.get("severity") == "medium"),
        "low": sum(1 for f in findings_data if f.get("severity") == "low"),
    }

    findings_table = "\n".join(
        f"| `{f.get('file_path','')}:{f.get('line_number','')}` "
        f"| {f.get('severity','').upper()} "
        f"| {f.get('title','')} "
        f"| {f.get('plain_impact','')[:60]} |"
        for f in findings_data[:20]
    )

    patches_list = "\n".join(
        f"- ✅ `{p['file_path']}` — {p.get('vuln_type','')} "
        f"({'verified' if p.get('validated') else 'applied'})"
        for p in patches_applied
    )

    sim_section = ""
    if simulation_results:
        confirmed = [s for s in simulation_results if s.get("confirmed")]
        sim_section = f"""
### 🔴 Live Attack Simulation Results
{len(confirmed)}/{len(simulation_results)} exploits confirmed exploitable before patching.

"""
        for s in confirmed[:5]:
            sim_section += f"- **{s.get('vuln_type')}**: {s.get('confirmation_message','')}\n"

    return f"""## 🛡️ CodeSentinel — Automated Security Report

> This PR was automatically generated by [CodeSentinel](https://github.com/NITHINKR06/codesentinel).
> All patches are **surgical** — only vulnerable lines were modified. Surrounding code is untouched.

---

### 📊 Security Score
| Before | After | Improvement |
|--------|-------|-------------|
| **{scan.score_before or '?'}** / 100 | **{scan.score_after or '?'}** / 100 | +{(scan.score_after or 0) - (scan.score_before or 0)} points |

### 🔍 Findings Summary
| Severity | Count |
|----------|-------|
| 🔴 Critical | {sev_counts['critical']} |
| 🟠 High | {sev_counts['high']} |
| 🟡 Medium | {sev_counts['medium']} |
| 🟢 Low | {sev_counts['low']} |

### 📁 Vulnerabilities Found
| File | Severity | Type | Impact |
|------|----------|------|--------|
{findings_table}

### 🔧 Patches Applied ({len(patches_applied)} files)
{patches_list}
{sim_section}
### ⚠️ What to do
1. **Review each patch** — confirm the fix makes sense in context
2. **Run your test suite** — patches preserve logic but verify behaviour
3. **Merge when satisfied** — or request changes if anything looks off

---
*Generated by CodeSentinel · Surgical patching — only vulnerable lines modified*
"""
