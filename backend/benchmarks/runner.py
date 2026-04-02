import json
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.red.ast_scanner import scan_files


SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".php",
    ".go",
    ".java",
    ".rb",
    ".cs",
    ".sh",
    ".bash",
    ".html",
    ".sql",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
}

DEFAULT_SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".next",
    "node_modules",
    "dist",
    "build",
    "vendor",
    "coverage",
    ".pytest_cache",
    ".venv",
    "venv",
}


@dataclass
class BenchmarkFinding:
    vuln_type: str
    file_path: str
    line_number: int
    severity: Optional[str] = None

    @classmethod
    def from_dict(cls, payload: Dict) -> "BenchmarkFinding":
        return cls(
            vuln_type=payload["vuln_type"],
            file_path=payload["file_path"],
            line_number=int(payload.get("line_number", 0) or 0),
            severity=payload.get("severity"),
        )


@dataclass
class CaseResult:
    case_name: str
    case_path: str
    expected: int
    predicted: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1: float
    matched: List[Dict]
    missed: List[Dict]
    extra: List[Dict]

    def to_dict(self) -> Dict:
        return asdict(self)


class BenchmarkRunner:
    def __init__(self, root_dir: str, line_tolerance: int = 2):
        self.root_dir = Path(root_dir).resolve()
        self.line_tolerance = max(0, line_tolerance)

    def run(self) -> Dict:
        case_dirs = self._discover_case_dirs()
        results = [self.run_case(case_dir) for case_dir in case_dirs]
        return self._summarize(results)

    def run_case(self, case_dir: Path) -> CaseResult:
        manifest = self._load_manifest(case_dir)
        expected_findings = [BenchmarkFinding.from_dict(item) for item in manifest.get("expected_findings", [])]
        files = self._collect_files(case_dir)
        predicted_findings = scan_files(files)

        matches, missed, extra = self._match_findings(expected_findings, predicted_findings)

        true_positives = len(matches)
        false_positives = len(extra)
        false_negatives = len(missed)
        precision = self._safe_div(true_positives, true_positives + false_positives)
        recall = self._safe_div(true_positives, true_positives + false_negatives)
        f1 = self._safe_div(2 * precision * recall, precision + recall)

        return CaseResult(
            case_name=manifest.get("name") or case_dir.name,
            case_path=str(case_dir),
            expected=len(expected_findings),
            predicted=len(predicted_findings),
            true_positives=true_positives,
            false_positives=false_positives,
            false_negatives=false_negatives,
            precision=precision,
            recall=recall,
            f1=f1,
            matched=matches,
            missed=[asdict(item) for item in missed],
            extra=[item for item in extra],
        )

    def _discover_case_dirs(self) -> List[Path]:
        manifest = self.root_dir / "benchmark.json"
        if manifest.exists():
            return [self.root_dir]

        case_dirs = [path for path in sorted(self.root_dir.iterdir()) if path.is_dir()]
        if not case_dirs:
            return [self.root_dir]
        return case_dirs

    def _load_manifest(self, case_dir: Path) -> Dict:
        manifest_path = case_dir / "benchmark.json"
        if manifest_path.exists():
            return json.loads(manifest_path.read_text(encoding="utf-8"))

        return {
            "name": case_dir.name,
            "expected_findings": [],
            "notes": "No benchmark.json manifest found.",
        }

    def _collect_files(self, case_dir: Path) -> List[Dict]:
        files: List[Dict] = []
        for root, dirs, filenames in os.walk(case_dir):
            dirs[:] = [directory for directory in dirs if directory not in DEFAULT_SKIP_DIRS]
            for filename in filenames:
                if filename == "benchmark.json":
                    continue
                path = Path(root) / filename
                extension = path.suffix.lower()
                if extension not in SUPPORTED_EXTENSIONS:
                    continue
                try:
                    content = path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                files.append(
                    {
                        "path": str(path.relative_to(case_dir)).replace(os.sep, "/"),
                        "full_path": str(path),
                        "extension": extension,
                        "language": self._detect_language(path, content),
                        "content": content,
                        "size": len(content),
                    }
                )
        return files

    def _detect_language(self, path: Path, content: str) -> str:
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".php": "php",
            ".go": "go",
            ".java": "java",
            ".rb": "ruby",
            ".cs": "csharp",
            ".sh": "shell",
            ".bash": "shell",
            ".html": "html",
            ".sql": "sql",
            ".json": "json",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".toml": "toml",
        }
        ext = path.suffix.lower()
        if ext in extension_map:
            return extension_map[ext]
        if content.startswith("#!") and content.splitlines():
            first_line = content.splitlines()[0].lower()
            if "python" in first_line:
                return "python"
        return "unknown"

    def _match_findings(
        self,
        expected: Sequence[BenchmarkFinding],
        predicted: Sequence[Dict],
    ) -> Tuple[List[Dict], List[BenchmarkFinding], List[Dict]]:
        unmatched_predictions = [dict(item) for item in predicted]
        matched: List[Dict] = []
        missed: List[BenchmarkFinding] = []

        for expected_finding in expected:
            match_index = self._find_best_prediction(expected_finding, unmatched_predictions)
            if match_index is None:
                missed.append(expected_finding)
                continue

            prediction = unmatched_predictions.pop(match_index)
            matched.append(
                {
                    "expected": asdict(expected_finding),
                    "predicted": prediction,
                }
            )

        extra = unmatched_predictions
        return matched, missed, extra

    def _find_best_prediction(self, expected: BenchmarkFinding, predictions: List[Dict]) -> Optional[int]:
        best_index = None
        best_score = None
        expected_path = self._normalize_path(expected.file_path)

        for index, prediction in enumerate(predictions):
            if prediction.get("vuln_type") != expected.vuln_type:
                continue

            predicted_path = self._normalize_path(prediction.get("file_path", ""))
            if predicted_path != expected_path:
                continue

            predicted_line = int(prediction.get("line_number", 0) or 0)
            line_distance = abs(predicted_line - expected.line_number)
            if line_distance > self.line_tolerance:
                continue

            score = (line_distance, 0 if prediction.get("severity") == expected.severity else 1)
            if best_score is None or score < best_score:
                best_score = score
                best_index = index

        return best_index

    def _normalize_path(self, value: str) -> str:
        return value.replace("\\", "/").lstrip("./")

    def _safe_div(self, numerator: float, denominator: float) -> float:
        if denominator == 0:
            return 0.0
        return round(numerator / denominator, 4)

    def _summarize(self, results: List[CaseResult]) -> Dict:
        total_expected = sum(result.expected for result in results)
        total_predicted = sum(result.predicted for result in results)
        total_tp = sum(result.true_positives for result in results)
        total_fp = sum(result.false_positives for result in results)
        total_fn = sum(result.false_negatives for result in results)

        precision = self._safe_div(total_tp, total_tp + total_fp)
        recall = self._safe_div(total_tp, total_tp + total_fn)
        f1 = self._safe_div(2 * precision * recall, precision + recall)

        by_case = [result.to_dict() for result in results]
        return {
            "root_dir": str(self.root_dir),
            "line_tolerance": self.line_tolerance,
            "cases": by_case,
            "summary": {
                "cases": len(results),
                "expected": total_expected,
                "predicted": total_predicted,
                "true_positives": total_tp,
                "false_positives": total_fp,
                "false_negatives": total_fn,
                "precision": precision,
                "recall": recall,
                "f1": f1,
            },
        }
