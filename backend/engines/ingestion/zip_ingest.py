import os
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict
import structlog

log = structlog.get_logger()

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".php",
    ".go", ".java", ".rb", ".env", ".yml", ".yaml",
    ".json", ".toml", ".sh", ".html", ".sql",
}

LANGUAGE_BY_EXTENSION = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".php": "php",
    ".go": "go",
    ".java": "java",
    ".rb": "ruby",
    ".sh": "shell",
    ".html": "html",
    ".sql": "sql",
    ".json": "json",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".toml": "toml",
}


def detect_language(path: str, content: str) -> str:
    ext = Path(path).suffix.lower()
    if ext in LANGUAGE_BY_EXTENSION:
        return LANGUAGE_BY_EXTENSION[ext]
    if content.startswith("#!") and "python" in content.splitlines()[0].lower():
        return "python"
    return "unknown"
SKIP_DIRS = {"node_modules", "__pycache__", ".git", "dist", "build", "vendor"}


class ZipIngestion:
    def __init__(self, zip_path: str):
        self.zip_path = zip_path
        self.tmp_dir = None
        self.extract_path = None

    def extract(self) -> str:
        self.tmp_dir = tempfile.mkdtemp(prefix="sentinel_zip_")
        self.extract_path = os.path.join(self.tmp_dir, "repo")
        with zipfile.ZipFile(self.zip_path, "r") as z:
            z.extractall(self.extract_path)
        log.info("Extracted ZIP", path=self.extract_path)
        return self.extract_path

    def get_files(self) -> List[Dict]:
        if not self.extract_path:
            raise RuntimeError("Call extract() first")
        files = []
        for root, dirs, filenames in os.walk(self.extract_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in filenames:
                ext = Path(fname).suffix.lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    continue
                full_path = os.path.join(root, fname)
                rel_path = os.path.relpath(full_path, self.extract_path)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    files.append({
                        "path": rel_path,
                        "full_path": full_path,
                        "extension": ext,
                        "language": detect_language(rel_path, content),
                        "content": content,
                        "size": len(content),
                    })
                except Exception:
                    pass
        return files

    def cleanup(self):
        if self.tmp_dir and os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir, ignore_errors=True)
