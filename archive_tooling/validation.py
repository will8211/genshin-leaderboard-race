from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable

from jsonschema import Draft202012Validator

from archive_tooling.acquire_html.cache import cache_paths, no_data_marker_path


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


def _parse_iso_date(value: str) -> datetime.date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _parse_timestamp_date(value: str) -> datetime.date:
    return datetime.strptime(value[:8], "%Y%m%d").date()


def _load_release_ticks(repo_root: Path) -> list[dict[str, object]]:
    path = repo_root / "data" / "release_ticks.json"
    data = load_json(path)
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict)]


def _load_manifest(repo_root: Path) -> list[dict[str, object]]:
    path = repo_root / "data" / "snapshot_manifest.json"
    data = load_json(path)
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict)]


def validate_completed_work_bundle(repo_root: Path) -> list[str]:
    failures = validate_contract_bundle(repo_root)
    if failures:
        return failures

    release_ticks = _load_release_ticks(repo_root)
    manifest = _load_manifest(repo_root)
    cache_root = repo_root / "data" / "html_cache"

    tick_versions = [str(row.get("version_id")) for row in release_ticks]
    manifest_versions = [str(row.get("version_id")) for row in manifest]
    if tick_versions != manifest_versions:
        failures.append("version order mismatch between release_ticks and snapshot_manifest")

    for i in range(1, len(release_ticks)):
        prev_date = _parse_iso_date(str(release_ticks[i - 1]["release_date"]))
        curr_date = _parse_iso_date(str(release_ticks[i]["release_date"]))
        if curr_date <= prev_date:
            failures.append(f"release_ticks not strictly increasing at {release_ticks[i]['version_id']}")

    for row in manifest:
        version_id = str(row.get("version_id"))
        timestamp = row.get("selected_timestamp")
        archive_url = row.get("archive_url")
        unresolved_reason = row.get("unresolved_reason")
        target_end_date = str(row.get("target_end_date"))

        has_selection = bool(timestamp and archive_url)
        if unresolved_reason and has_selection:
            failures.append(f"{version_id}: unresolved_reason present alongside selected snapshot")
            continue
        if not unresolved_reason and not has_selection:
            failures.append(f"{version_id}: missing selected snapshot without unresolved_reason")
            continue
        if not has_selection:
            continue

        selected_date = _parse_timestamp_date(str(timestamp))
        end_date = _parse_iso_date(target_end_date)
        if selected_date > end_date:
            failures.append(f"{version_id}: selected timestamp exceeds target_end_date")

        marker_path = no_data_marker_path(cache_root, version_id)
        html_path, meta_path = cache_paths(cache_root, version_id, str(timestamp))
        if marker_path.exists():
            if html_path.exists() or meta_path.exists():
                failures.append(f"{version_id}: .no-data marker should not coexist with cached html/meta")
            continue

        if not html_path.exists():
            failures.append(f"{version_id}: missing cached html for selected snapshot")
            continue
        if not meta_path.exists():
            failures.append(f"{version_id}: missing metadata json for selected cached html")

    return failures


def build_completed_work_summary(repo_root: Path) -> dict[str, object]:
    release_ticks = _load_release_ticks(repo_root)
    manifest = _load_manifest(repo_root)
    cache_root = repo_root / "data" / "html_cache"

    unresolved_counter = Counter(
        str(row.get("unresolved_reason"))
        for row in manifest
        if row.get("unresolved_reason")
    )

    resolvable_rows = [row for row in manifest if row.get("selected_timestamp") and row.get("archive_url")]
    marker_count = 0
    cached_complete_count = 0
    missing_cache_count = 0

    for row in resolvable_rows:
        version_id = str(row["version_id"])
        timestamp = str(row["selected_timestamp"])
        marker_path = no_data_marker_path(cache_root, version_id)
        html_path, meta_path = cache_paths(cache_root, version_id, timestamp)

        if marker_path.exists():
            marker_count += 1
        elif html_path.exists() and meta_path.exists():
            cached_complete_count += 1
        else:
            missing_cache_count += 1

    return {
        "release_tick_count": len(release_ticks),
        "manifest_row_count": len(manifest),
        "version_alignment_ok": [str(row.get("version_id")) for row in release_ticks]
        == [str(row.get("version_id")) for row in manifest],
        "manifest": {
            "resolvable_count": len(resolvable_rows),
            "unresolved_count": sum(unresolved_counter.values()),
            "unresolved_by_reason": dict(unresolved_counter),
        },
        "cache": {
            "cached_complete_count": cached_complete_count,
            "no_data_marker_count": marker_count,
            "missing_cache_count": missing_cache_count,
            "coverage_count": cached_complete_count + marker_count,
            "coverage_rate": (
                (cached_complete_count + marker_count) / len(resolvable_rows)
                if resolvable_rows
                else 1.0
            ),
        },
    }
