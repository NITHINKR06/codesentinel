from typing import List, Dict

SEVERITY_DEDUCTIONS = {
    "critical": 25,
    "high": 12,
    "medium": 6,
    "low": 2,
}

CHAIN_DEDUCTION = 15
GHOST_COMMIT_DEDUCTION = 10
MAX_SCORE = 100


def calculate_score(
    findings: List[Dict],
    chains: List[Dict],
    ghost_commits: List[Dict],
    total_files: int = 1,
) -> int:
    score = MAX_SCORE

    # Deduct per finding
    for f in findings:
        deduction = SEVERITY_DEDUCTIONS.get(f.get("severity", "low"), 2)
        # Scale down for larger codebases (more files = proportionally less per finding)
        scale = max(0.5, 1.0 - (total_files / 500) * 0.3)
        score -= deduction * scale

    # Deduct per chain (chains are worse than individual findings)
    for chain in chains:
        chain_sev = chain.get("escalated_severity", "medium")
        base = SEVERITY_DEDUCTIONS.get(chain_sev, 6)
        score -= base * 1.5

    # Deduct for ghost commits
    for gc in ghost_commits:
        if gc.get("still_present"):
            score -= GHOST_COMMIT_DEDUCTION
        else:
            score -= GHOST_COMMIT_DEDUCTION / 2

    return max(0, min(100, round(score)))


def calculate_score_after_patches(
    before_score: int,
    patches: List[Dict],
    findings: List[Dict],
) -> int:
    validated_patches = [p for p in patches if p.get("validated")]
    if not validated_patches:
        return before_score

    patched_finding_ids = {p.get("finding_id") for p in validated_patches}
    remaining_findings = [f for f in findings if f.get("id") not in patched_finding_ids]

    improvement = len(validated_patches) * 8
    return min(100, before_score + improvement)


def score_summary(score: int) -> Dict:
    if score >= 80:
        grade, label, color = "A", "Secured", "#1D9E75"
    elif score >= 65:
        grade, label, color = "B", "Good", "#3B6D11"
    elif score >= 50:
        grade, label, color = "C", "Needs work", "#BA7517"
    elif score >= 30:
        grade, label, color = "D", "At risk", "#E24B4A"
    else:
        grade, label, color = "F", "Critical risk", "#A32D2D"

    return {
        "score": score,
        "grade": grade,
        "label": label,
        "color": color,
    }
