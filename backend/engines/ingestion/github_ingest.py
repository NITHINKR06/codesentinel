import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict
import structlog

import git

log = structlog.get_logger()

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".php", ".go", ".java", ".rb", ".cs",
    ".env", ".yml", ".yaml", ".json", ".toml",
    ".sh", ".bash", ".html", ".sql",
}

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".next",
    "dist", "build", "vendor", ".venv", "venv",
    "coverage", ".pytest_cache",
}


class RepoIngestion:
    def __init__(self, github_url: str):
        self.github_url = github_url
        self.tmp_dir = None
        self.repo_path = None

    def clone(self) -> str:
        self.tmp_dir = tempfile.mkdtemp(prefix="sentinel_")
        self.repo_path = os.path.join(self.tmp_dir, "repo")
        log.info("Cloning repo", url=self.github_url)
        git.Repo.clone_from(self.github_url, self.repo_path, depth=50)
        return self.repo_path

    def get_files(self) -> List[Dict]:
        if not self.repo_path:
            raise RuntimeError("Call clone() first")

        files = []
        for root, dirs, filenames in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in filenames:
                ext = Path(fname).suffix.lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    continue
                full_path = os.path.join(root, fname)
                rel_path = os.path.relpath(full_path, self.repo_path)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    files.append({
                        "path": rel_path,
                        "full_path": full_path,
                        "extension": ext,
                        "content": content,
                        "size": len(content),
                    })
                except Exception as e:
                    log.warning("Could not read file", path=rel_path, error=str(e))

        log.info("Ingested files", count=len(files))
        return files

    def get_repo_name(self) -> str:
        parts = self.github_url.rstrip("/").split("/")
        return f"{parts[-2]}/{parts[-1]}" if len(parts) >= 2 else parts[-1]

    def cleanup(self):
        if self.tmp_dir and os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir, ignore_errors=True)
