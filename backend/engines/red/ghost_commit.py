import re
import math
from typing import List, Dict
import structlog
import git

log = structlog.get_logger()

SECRET_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"['\"]?aws_secret['\"]?\s*[:=]\s*['\"]([^'\"]{20,})['\"]", "AWS Secret Key"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"ghs_[a-zA-Z0-9]{36}", "GitHub App Token"),
    (r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----", "Private Key"),
    (r"(password|passwd|pwd)\s*=\s*['\"][^'\"]{6,}['\"]", "Hardcoded Password"),
    (r"(api_key|apikey|api_secret)\s*=\s*['\"][^'\"]{10,}['\"]", "API Key"),
    (r"(secret_key|secretkey)\s*=\s*['\"][^'\"]{10,}['\"]", "Secret Key"),
    (r"mongodb(\+srv)?://[^@]+:[^@]+@", "MongoDB Connection String with Credentials"),
    (r"postgresql://[^@]+:[^@]+@", "PostgreSQL Connection String with Credentials"),
    (r"redis://:[^@]+@", "Redis Connection String with Password"),
    (r"(Authorization|Bearer)\s*:\s*['\"]?[A-Za-z0-9\-_\.]{20,}", "Authorization Header Value"),
    (r"sk-[a-zA-Z0-9]{32,}", "OpenAI API Key"),
    (r"xox[baprs]-[0-9A-Za-z\-]{10,}", "Slack Token"),
    (r"AIza[0-9A-Za-z\-_]{35}", "Google API Key"),
]


def _entropy(s: str) -> float:
    if not s:
        return 0.0
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    return -sum((f / len(s)) * math.log2(f / len(s)) for f in freq.values())


def _scan_content_for_secrets(content: str) -> List[Dict]:
    hits = []
    for pattern, label in SECRET_PATTERNS:
        for m in re.finditer(pattern, content, re.IGNORECASE):
            hits.append({
                "pattern_label": label,
                "match": m.group(0)[:80],  # truncate for safety
                "char_offset": m.start(),
            })

    # High-entropy string scan
    for m in re.finditer(r"['\"]([A-Za-z0-9+/=_\-]{20,})['\"]", content):
        val = m.group(1)
        if _entropy(val) > 4.5:
            hits.append({
                "pattern_label": "High-entropy string (possible secret)",
                "match": val[:40] + "...",
                "char_offset": m.start(),
            })
    return hits


def scan_git_history(repo_path: str) -> List[Dict]:
    """
    Walk every commit in history, diff each one, and flag secrets that were
    added (and possibly later deleted). Deleted secrets are still in the history.
    """
    findings = []
    try:
        repo = git.Repo(repo_path)
    except Exception as e:
        log.error("Could not open repo for ghost commit scan", error=str(e))
        return findings

    commits = list(repo.iter_commits("HEAD", max_count=200))
    log.info("Scanning git history", commits=len(commits))

    seen_hashes = set()

    for commit in commits:
        if not commit.parents:
            continue
        try:
            diffs = commit.parents[0].diff(commit, create_patch=True)
        except Exception:
            continue

        for diff in diffs:
            try:
                patch_text = diff.diff.decode("utf-8", errors="ignore")
            except Exception:
                continue

            added_lines = "\n".join(
                line[1:] for line in patch_text.split("\n") if line.startswith("+") and not line.startswith("+++")
            )
            if not added_lines:
                continue

            hits = _scan_content_for_secrets(added_lines)
            for hit in hits:
                fingerprint = f"{commit.hexsha[:8]}_{hit['pattern_label']}_{hit['match'][:20]}"
                if fingerprint in seen_hashes:
                    continue
                seen_hashes.add(fingerprint)

                # Check if this secret still exists in HEAD
                still_present = _secret_in_head(repo, hit["match"][:30])

                findings.append({
                    "commit_sha": commit.hexsha[:8],
                    "commit_message": commit.message.strip()[:100],
                    "author": str(commit.author),
                    "committed_at": commit.committed_datetime.isoformat(),
                    "file": diff.b_path or diff.a_path,
                    "secret_type": hit["pattern_label"],
                    "secret_preview": hit["match"],
                    "still_present": still_present,
                    "severity": "critical" if still_present else "high",
                    "title": f"{'Active' if still_present else 'Deleted'} secret in git history: {hit['pattern_label']}",
                    "plain_impact": (
                        "This secret is STILL in the codebase and is immediately usable."
                        if still_present else
                        "This secret was committed and is permanently in git history. Anyone who clones this repo can recover it."
                    ),
                })

    log.info("Ghost commit scan complete", findings=len(findings))
    return findings


def _secret_in_head(repo: git.Repo, secret_preview: str) -> bool:
    """Check if a secret snippet still exists in the current HEAD tree."""
    try:
        for blob in repo.head.commit.tree.traverse():
            if blob.type == "blob":
                try:
                    content = blob.data_stream.read().decode("utf-8", errors="ignore")
                    if secret_preview in content:
                        return True
                except Exception:
                    pass
    except Exception:
        pass
    return False
