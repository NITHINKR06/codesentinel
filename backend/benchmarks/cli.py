import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmarks.runner import BenchmarkRunner


def _format_table(result: dict) -> str:
    summary = result["summary"]
    lines = []
    lines.append("Benchmark Summary")
    lines.append("=" * len(lines[0]))
    lines.append(f"Root: {result['root_dir']}")
    lines.append(f"Cases: {summary['cases']}")
    lines.append(f"Expected: {summary['expected']}  Predicted: {summary['predicted']}")
    lines.append(
        f"TP: {summary['true_positives']}  FP: {summary['false_positives']}  FN: {summary['false_negatives']}"
    )
    lines.append(
        f"Precision: {summary['precision']:.4f}  Recall: {summary['recall']:.4f}  F1: {summary['f1']:.4f}"
    )
    lines.append("")
    lines.append("Per Case")
    lines.append("--------")
    for case in result["cases"]:
        lines.append(
            f"{case['case_name']}: P={case['precision']:.4f} R={case['recall']:.4f} F1={case['f1']:.4f} "
            f"(TP={case['true_positives']}, FP={case['false_positives']}, FN={case['false_negatives']})"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CodeSentinel benchmark evaluation")
    parser.add_argument("root", help="Benchmark root directory")
    parser.add_argument("--line-tolerance", type=int, default=2, help="Allowed line delta when matching findings")
    parser.add_argument("--output", choices=("table", "json"), default="table", help="Output format")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    runner = BenchmarkRunner(args.root, line_tolerance=args.line_tolerance)
    result = runner.run()

    if args.output == "json":
        indent = 2 if args.pretty else None
        print(json.dumps(result, indent=indent, sort_keys=args.pretty))
    else:
        print(_format_table(result))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())