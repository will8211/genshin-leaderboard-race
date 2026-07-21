from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path


# Historical ranking exports include several retired numeric IDs and slug forms.
# Map those legacy tokens to canonical character keys used in characters.json.
LEGACY_TOKEN_TO_CHARACTER_KEY: dict[str, str] = {
    "297515": "Lisa",
    "297520": "Venti",
    "297522": "Bennett",
    "297526": "Mona",
    "297534": "Keqing",
    "383713": "Nahida",
    "383716": "Dehya",
    "386489": "Kaveh",
    "393054": "Neuvillette",
    "417191": "Wriothesley",
    "Gaming-Best-Builds": "Gaming",
}


@dataclass(frozen=True)
class FileFailure:
    file: str
    version_id: str | None
    unmapped_ids: list[str]


def build_game8id_map(characters_path: Path) -> dict[str, str]:
    """Build reverse map from game8id to character key."""
    raw = json.loads(characters_path.read_text(encoding="utf-8"))

    game8id_to_key: dict[str, str] = {}
    duplicates: dict[str, list[str]] = {}

    for character_key, details in raw.items():
        game8id = details.get("game8id")
        if not game8id:
            continue

        existing = game8id_to_key.get(game8id)
        if existing is not None:
            duplicates.setdefault(game8id, [existing]).append(character_key)
            continue

        game8id_to_key[game8id] = character_key

    if duplicates:
        lines = []
        for game8id, keys in sorted(duplicates.items()):
            lines.append(f"{game8id}: {', '.join(sorted(set(keys)))}")
        raise ValueError(
            "Duplicate game8id values found in characters.json:\n"
            + "\n".join(lines)
        )

    for token, character_key in LEGACY_TOKEN_TO_CHARACTER_KEY.items():
        if character_key not in raw:
            # Allow partial character fixtures in tests and optional datasets.
            continue

        existing = game8id_to_key.get(token)
        if existing is not None and existing != character_key:
            raise ValueError(
                "Legacy token conflicts with game8id mapping: "
                f"{token} -> {existing} (expected {character_key})"
            )

        game8id_to_key[token] = character_key

    return game8id_to_key


def convert_payload_ids_to_names(
    payload: dict[str, dict[str, dict[str, list[str]]]],
    game8id_to_key: dict[str, str],
) -> tuple[dict[str, dict[str, dict[str, list[str]]]], list[str], str | None]:
    """Convert ranking IDs in a single payload to character keys."""
    converted: dict[str, dict[str, dict[str, list[str]]]] = {}
    unmapped: set[str] = set()
    version_id: str | None = None

    for current_version_id, roles in payload.items():
        version_id = current_version_id
        converted_roles: dict[str, dict[str, list[str]]] = {}

        for role_name, tiers in roles.items():
            converted_tiers: dict[str, list[str]] = {}

            for tier_name, ranking_ids in tiers.items():
                converted_ids: list[str] = []

                for ranking_id in ranking_ids:
                    character_key = game8id_to_key.get(ranking_id)
                    if character_key is None:
                        unmapped.add(ranking_id)
                        continue
                    converted_ids.append(character_key)

                converted_tiers[tier_name] = converted_ids

            converted_roles[role_name] = converted_tiers

        converted[current_version_id] = converted_roles

    return converted, sorted(unmapped), version_id


def convert_json_directory(
    input_dir: Path,
    output_dir: Path,
    characters_path: Path,
) -> tuple[int, int, list[FileFailure]]:
    """Convert every JSON ranking file in input_dir into output_dir."""
    game8id_to_key = build_game8id_map(characters_path)

    total = 0
    converted_count = 0
    failures: list[FileFailure] = []

    for input_path in sorted(input_dir.glob("*.json")):
        total += 1
        payload = json.loads(input_path.read_text(encoding="utf-8"))

        converted_payload, unmapped_ids, version_id = convert_payload_ids_to_names(
            payload,
            game8id_to_key,
        )

        if unmapped_ids:
            failures.append(
                FileFailure(
                    file=input_path.name,
                    version_id=version_id,
                    unmapped_ids=unmapped_ids,
                )
            )
            continue

        output_path = output_dir / input_path.name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(converted_payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        converted_count += 1

    return total, converted_count, failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert ranking JSON files from game8 IDs to character keys "
            "using data/characters.json."
        )
    )
    parser.add_argument(
        "--input-dir",
        default="data/extracted_rankings/json",
        help="Input directory of ranking JSON files.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/extracted_rankings/json_names",
        help="Output directory for converted ranking JSON files.",
    )
    parser.add_argument(
        "--characters",
        default="data/characters.json",
        help="Path to characters.json containing game8id values.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    characters_path = Path(args.characters)

    if not input_dir.exists():
        print(f"Input directory not found: {input_dir}", file=sys.stderr)
        return 1

    if not characters_path.exists():
        print(f"Characters file not found: {characters_path}", file=sys.stderr)
        return 1

    total, converted_count, failures = convert_json_directory(
        input_dir=input_dir,
        output_dir=output_dir,
        characters_path=characters_path,
    )

    report = {
        "input_count": total,
        "converted_count": converted_count,
        "failure_count": len(failures),
        "failures": [
            {
                "file": failure.file,
                "version_id": failure.version_id,
                "unmapped_ids": failure.unmapped_ids,
            }
            for failure in failures
        ],
    }
    print(json.dumps(report, indent=2))

    if failures:
        unique_unmapped_ids = sorted(
            {
                unmapped_id
                for failure in failures
                for unmapped_id in failure.unmapped_ids
            }
        )
        print(
            "PING ME: missing IDs detected "
            f"({len(unique_unmapped_ids)} unique, {len(failures)} file failures).",
            file=sys.stderr,
        )

    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
