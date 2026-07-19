from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from jsonschema import Draft202012Validator


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_against_schema(data: object, schema: object) -> list[str]:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    return [error.message for error in errors]


def validate_file(json_path: Path, schema_path: Path) -> list[str]:
    if not json_path.exists():
        return [f"missing file: {json_path}"]
    data = load_json(json_path)
    schema = load_json(schema_path)
    return validate_against_schema(data, schema)


def validate_contract_bundle(repo_root: Path) -> list[str]:
    checks: Iterable[tuple[Path, Path]] = [
        (
            repo_root / "data" / "release_ticks.json",
            repo_root / "schemas" / "release_ticks.schema.json",
        ),
        (
            repo_root / "data" / "snapshot_manifest.json",
            repo_root / "schemas" / "snapshot_manifest.schema.json",
        ),
    ]

    failures: list[str] = []
    for json_path, schema_path in checks:
        errors = validate_file(json_path, schema_path)
        failures.extend(f"{json_path.name}: {msg}" for msg in errors)
    return failures
