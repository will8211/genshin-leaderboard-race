from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def _end_of_day_timestamp(version_end_date: str) -> str:
    return datetime.strptime(version_end_date, "%Y-%m-%d").strftime("%Y%m%d") + "235959"


def _to_archive_url(timestamp: str, original_url: str) -> str:
    return f"https://web.archive.org/web/{timestamp}/{original_url}"


def load_release_ticks(path: Path) -> list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_overrides(path: Path) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("snapshot overrides file must be an object keyed by version_id")
    return data


def pick_candidates_for_version(
    captures: list[dict[str, str]],
    version_end_date: str,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    cutoff = _end_of_day_timestamp(version_end_date)
    before_or_equal = [c for c in captures if c.get("timestamp", "") <= cutoff]
    after = [c for c in captures if c.get("timestamp", "") > cutoff]
    before_or_equal.sort(key=lambda c: c.get("timestamp", ""))
    after.sort(key=lambda c: c.get("timestamp", ""))
    return before_or_equal, after


def build_manifest(
    release_ticks: list[dict[str, object]],
    captures: list[dict[str, str]],
    overrides: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    manifest: list[dict[str, object]] = []

    for tick in release_ticks:
        version_id = str(tick["version_id"])
        target_end = str(tick["version_end_date"])

        override = overrides.get(version_id)
        if override:
            timestamp = str(override.get("selected_timestamp")) if override.get("selected_timestamp") else None
            original_url = str(override.get("original_url") or "")
            archive_url = _to_archive_url(timestamp, original_url) if timestamp and original_url else None
            manifest.append(
                {
                    "version_id": version_id,
                    "target_end_date": target_end,
                    "selected_timestamp": timestamp,
                    "archive_url": archive_url,
                    "selection_reason": "manual_override",
                    "quality_flags": ["override"],
                    "override": override,
                    "unresolved_reason": None if timestamp else "override_missing_timestamp",
                }
            )
            continue

        before_or_equal, _after = pick_candidates_for_version(captures, target_end)
        if not before_or_equal:
            manifest.append(
                {
                    "version_id": version_id,
                    "target_end_date": target_end,
                    "selected_timestamp": None,
                    "archive_url": None,
                    "selection_reason": "none_found_before_end_date",
                    "quality_flags": ["unresolved"],
                    "override": None,
                    "unresolved_reason": "no_capture_leq_version_end",
                }
            )
            continue

        selected = before_or_equal[-1]
        manifest.append(
            {
                "version_id": version_id,
                "target_end_date": target_end,
                "selected_timestamp": selected["timestamp"],
                "archive_url": _to_archive_url(selected["timestamp"], selected["original"]),
                "selection_reason": "latest_leq_end_date",
                "quality_flags": [],
                "override": None,
                "unresolved_reason": None,
            }
        )

    return manifest


def write_manifest(path: Path, manifest: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
