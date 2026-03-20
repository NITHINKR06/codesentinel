from typing import List, Dict

# Deduction per finding — capped so large repos don't hit 0 unfairly
SEVERITY_DEDUCTIONS = {
    "critical": 15,
    "high": 8,
    "medium": 4,
    "low": 1,
}

CHAIN_DEDUCTION = 10       # per chain
GHOST_COMMIT_DEDUCTION = 8  # per active secret in history
MAX_SCORE = 100
MIN_SCORE = 5              # never show 0 — always some residual risk shown


def calculate_score(
    findings: List[Dict],
    chains: List[Dict],
    ghost_commits: List[Dict],
    total_files: int = 1,
) -> int:
    score = MAX_SCORE

    if not findings and not chains and not ghost_commits:
        return 95  # clean scan — not perfect, could have runtime issues

    # Deduct per finding with diminishing returns
    # First 3 of each severity hit full — rest are halved
    sev_counts: Dict[str, int] = {}
    for f in findings:
        sev = f.get("severity", "low")
        sev_counts[sev] = sev_counts.get(sev, 0) + 1
        count = sev_counts[sev]
        deduction = SEVERITY_DEDUCTIONS.get(sev, 1)
        # Diminishing returns after 3rd finding of same severity
        if count > 3:
            deduction = deduction * 0.4
        score -= deduction

    # Deduct per chain (escalated severity)
    for chain in chains:
        chain_sev = chain.get("escalated_severity", "medium")
        base = SEVERITY_DEDUCTIONS.get(chain_sev, 4)
        score -= base * 1.2  # chains are worse than individual findings

    # Deduct for ghost commits
    for gc in ghost_commits:
        if gc.get("still_present"):
            score -= GHOST_COMMIT_DEDUCTION
        else:
            score -= GHOST_COMMIT_DEDUCTION * 0.4  # deleted but still in history

    return max(MIN_SCORE, min(MAX_SCORE, round(score)))


def calculate_score_after_patches(
    before_score: int,
    patches: List[Dict],
    findings: List[Dict],
) -> int:
    validated_patches = [p for p in patches if p.get("validated")]

    if not validated_patches:
        return before_score  # no verified patches = no improvement

    # Each validated patch improves score by fixing its finding's deduction
    improvement = 0
    patched_vuln_types = set()

    for patch in validated_patches:
        vuln_type = patch.get("vuln_type", "")
        file_path = patch.get("file_path", "")

        # Find the original finding this patch fixes
        original_finding = next(
            (f for f in findings
             if f.get("file_path") == file_path
             and f.get("vuln_type") == vuln_type),
            None
        )

        if original_finding:
            sev = original_finding.get("severity", "low")
            base = SEVERITY_DEDUCTIONS.get(sev, 1)
            # Recover 80% of the deduction (20% residual — patch may not be perfect)
            improvement += base * 0.8
        else:
            improvement += 3  # unknown finding — small improvement

    new_score = before_score + improvement
    # Cap improvement — can't exceed 95 (nothing is perfectly secure)
    return max(before_score, min(95, round(new_score)))


def score_summary(score: int) -> Dict:
    if score >= 85:
        grade, label, color = "A", "Secured", "#1D9E75"
    elif score >= 70:
        grade, label, color = "B", "Good", "#3B6D11"
    elif score >= 55:
        grade, label, color = "C", "Needs work", "#BA7517"
    elif score >= 35:
        grade, label, color = "D", "At risk", "#E24B4A"
    else:
        grade, label, color = "F", "Critical risk", "#A32D2D"

    return {
        "score": score,
        "grade": grade,
        "label": label,
        "color": color,
    }