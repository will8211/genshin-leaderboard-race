"""Command-line interface for CSV generation."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROLE_TO_OUTPUT = {
    "Main DPS": "main_dps.csv",
    "Sub-DPS": "sub_dps.csv",
    "Support": "support.csv",
}
TIER_ORDER = ("SS", "S", "A", "B", "C")


def load_template(template_path: Path) -> tuple[list[str], list[dict[str, str]], list[str]]:
    with template_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("Template CSV has no header row")
        fieldnames = reader.fieldnames
        rows = [dict(row) for row in reader]

    if len(fieldnames) < 4:
        raise ValueError(
            "Template CSV must include Character, Image, Color, and version columns"
        )

    versions = fieldnames[3:]
    return fieldnames, rows, versions


def select_version_payload(input_dir: Path, version: str) -> tuple[dict[str, dict[str, list[str]]] | None, str | None]:
    mine_path = input_dir / f"{version}_mine.json"
    base_path = input_dir / f"{version}.json"

    selected_path: Path | None = None
    if mine_path.exists():
        selected_path = mine_path
    elif base_path.exists():
        selected_path = base_path

    if selected_path is None:
        return None, None

    payload = json.loads(selected_path.read_text(encoding="utf-8"))
    roles = payload.get(version)
    if roles is None and len(payload) == 1:
        roles = next(iter(payload.values()))
    if not isinstance(roles, dict):
        raise ValueError(f"Invalid payload format in {selected_path}")

    return roles, selected_path.name


def flatten_tiers_to_ranks(tiers: dict[str, list[str]]) -> dict[str, str]:
    ordered_tiers: list[str] = [tier for tier in TIER_ORDER if tier in tiers]
    ordered_tiers.extend(tier for tier in tiers if tier not in TIER_ORDER)

    ranks: dict[str, str] = {}
    rank = 1
    for tier in ordered_tiers:
        for character_name in tiers.get(tier, []):
            ranks[character_name] = str(rank)
            rank += 1
    return ranks


def build_role_version_ranks(
    versions: list[str],
    input_dir: Path,
) -> tuple[dict[str, dict[str, dict[str, str]]], dict[str, dict[str, int]]]:
    role_version_ranks: dict[str, dict[str, dict[str, str]]] = {
        role_name: {} for role_name in ROLE_TO_OUTPUT
    }
    role_stats: dict[str, dict[str, int]] = {
        role_name: {"direct": 0, "carry_forward": 0, "blank": 0}
        for role_name in ROLE_TO_OUTPUT
    }

    selected_payloads: dict[str, dict[str, dict[str, list[str]]] | None] = {}
    for version in versions:
        roles, _ = select_version_payload(input_dir, version)
        selected_payloads[version] = roles

    for role_name in ROLE_TO_OUTPUT:
        previous_ranks: dict[str, str] | None = None

        for version in versions:
            roles = selected_payloads[version]
            if roles is None:
                if previous_ranks is None:
                    current_ranks: dict[str, str] = {}
                    role_stats[role_name]["blank"] += 1
                else:
                    current_ranks = dict(previous_ranks)
                    role_stats[role_name]["carry_forward"] += 1
            else:
                role_tiers = roles.get(role_name)
                if role_tiers is None:
                    current_ranks = {}
                    role_stats[role_name]["blank"] += 1
                else:
                    current_ranks = flatten_tiers_to_ranks(role_tiers)
                    role_stats[role_name]["direct"] += 1

            role_version_ranks[role_name][version] = current_ranks
            previous_ranks = current_ranks

    return role_version_ranks, role_stats


def write_role_csvs(
    fieldnames: list[str],
    template_rows: list[dict[str, str]],
    versions: list[str],
    role_version_ranks: dict[str, dict[str, dict[str, str]]],
    output_dir: Path,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written_files: list[Path] = []

    for role_name, output_filename in ROLE_TO_OUTPUT.items():
        output_path = output_dir / output_filename
        written_files.append(output_path)

        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()

            for template_row in template_rows:
                row = dict(template_row)
                character_name = row.get("Character", "")

                for version in versions:
                    row[version] = role_version_ranks[role_name][version].get(
                        character_name,
                        "",
                    )

                writer.writerow(row)

    return written_files


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
        default="data/csv/template.csv",
        help="CSV template path",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/csv",
        help="Output directory for generated role CSV files",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    repo_root = Path(args.repo_root).resolve()
    input_dir = (repo_root / args.input_dir).resolve()
    template_path = (repo_root / args.template).resolve()
    output_dir = (repo_root / args.output_dir).resolve()

    if not input_dir.exists():
        print(f"Input directory not found: {input_dir}", file=sys.stderr)
        return 1

    if not template_path.exists():
        print(f"Template not found: {template_path}", file=sys.stderr)
        return 1

    fieldnames, template_rows, versions = load_template(template_path)
    role_version_ranks, role_stats = build_role_version_ranks(
        versions=versions,
        input_dir=input_dir,
    )

    written_files = write_role_csvs(
        fieldnames=fieldnames,
        template_rows=template_rows,
        versions=versions,
        role_version_ranks=role_version_ranks,
        output_dir=output_dir,
    )

    result = {
        "status": "ok",
        "template": str(template_path),
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "written_files": [str(path) for path in written_files],
        "role_stats": role_stats,
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
