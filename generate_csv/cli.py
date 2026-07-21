"""Command-line interface for CSV generation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate leaderboard CSV outputs"
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=".",
        help="Path to repository root (default: current directory)",
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/extracted_rankings/json_names",
        help="Directory containing ranking JSON-by-name files",
    )
    parser.add_argument(
        "--template",
        type=str,
        default="data/extracted_rankings/csv/template.csv",
        help="CSV template path",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/leaderboard.csv",
        help="Generated CSV output path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    repo_root = Path(args.repo_root).resolve()
    input_dir = (repo_root / args.input_dir).resolve()
    template_path = (repo_root / args.template).resolve()
    output_path = (repo_root / args.output).resolve()

    result = {
        "status": "scaffold",
        "message": "generate_csv module created and ready for implementation",
        "input_dir": str(input_dir),
        "template": str(template_path),
        "output": str(output_path),
    }

    if not input_dir.exists():
        result["warning"] = f"Input directory not found: {input_dir}"

    if not template_path.exists():
        result["warning"] = f"Template not found: {template_path}"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
