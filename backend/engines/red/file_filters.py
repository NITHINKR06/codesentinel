from __future__ import annotations

from pathlib import Path
from typing import Any

# Files that are typically generated, extremely noisy for secret/entropy heuristics,
# and not meaningful to patch or generate PoCs for.
SKIP_BASENAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "pnpm-lock.yml",
    "bun.lockb",
    "composer.lock",
    "poetry.lock",
    "go.sum",
    "cargo.lock",
}


def should_skip_path(path: str | None) -> bool:
    if not path:
        return False

    base_name = Path(path).name.lower()

    if base_name in SKIP_BASENAMES:
        return True

    # Other generated/minified artifacts that are commonly very noisy.
    if base_name.endswith(".lock"):
        return True
    if base_name.endswith(".min.js") or base_name.endswith(".min.css"):
        return True

    return False


def should_skip_file_info(file_info: dict[str, Any]) -> bool:
    return should_skip_path(str(file_info.get("path", "")))


def filter_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove findings for paths we never want to spend LLM budget on."""
    kept: list[dict[str, Any]] = []
    for finding in findings:
        if should_skip_path(str(finding.get("file_path", ""))):
            continue
        kept.append(finding)
    return kept
