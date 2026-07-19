from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen


def load_manifest(path: Path) -> list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))


def select_manifest_rows(
    manifest: list[dict[str, object]],
    version: str | None,
    start_version: str | None,
    end_version: str | None,
) -> list[dict[str, object]]:
    ordered_versions = [str(row["version_id"]) for row in manifest]
    index_by_version = {v.upper(): i for i, v in enumerate(ordered_versions)}

    if version:
        idx = index_by_version.get(version.upper())
        if idx is None:
            raise ValueError(f"Unknown version: {version}")
        return [manifest[idx]]

    if start_version or end_version:
        if not start_version or not end_version:
            raise ValueError("Both --start-version and --end-version are required together")
        start_idx = index_by_version.get(start_version.upper())
        end_idx = index_by_version.get(end_version.upper())
        if start_idx is None:
            raise ValueError(f"Unknown start version: {start_version}")
        if end_idx is None:
            raise ValueError(f"Unknown end version: {end_version}")
        if start_idx > end_idx:
            raise ValueError("start version must be earlier than or equal to end version")
        return manifest[start_idx : end_idx + 1]

    return manifest


def cache_paths(cache_root: Path, version_id: str, timestamp: str) -> tuple[Path, Path]:
    version_dir = cache_root / version_id
    html_path = version_dir / f"{timestamp}.html"
    meta_path = version_dir / f"{timestamp}.meta.json"
    return html_path, meta_path


def version_dir_path(cache_root: Path, version_id: str) -> Path:
    return cache_root / version_id


def no_data_marker_path(cache_root: Path, version_id: str) -> Path:
    return version_dir_path(cache_root, version_id) / ".no-data"


def fetch_bytes(url: str) -> bytes:
    with urlopen(url) as response:
        return response.read()


def write_cached_html(
    cache_root: Path,
    version_id: str,
    timestamp: str,
    archive_url: str,
    content: bytes,
) -> tuple[Path, Path]:
    html_path, meta_path = cache_paths(cache_root, version_id, timestamp)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_bytes(content)

    checksum = hashlib.sha256(content).hexdigest()
    metadata = {
        "version_id": version_id,
        "selected_timestamp": timestamp,
        "archive_url": archive_url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "size_bytes": len(content),
        "sha256": checksum,
    }
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return html_path, meta_path


def write_no_data_marker(
    cache_root: Path,
    version_id: str,
    reason: str,
    selected_timestamp: str | None = None,
    archive_url: str | None = None,
    detail: str | None = None,
) -> Path:
    version_dir = version_dir_path(cache_root, version_id)
    if version_dir.exists():
        shutil.rmtree(version_dir)
    version_dir.mkdir(parents=True, exist_ok=True)

    marker_path = no_data_marker_path(cache_root, version_id)
    payload = {
        "version_id": version_id,
        "reason": reason,
        "selected_timestamp": selected_timestamp,
        "archive_url": archive_url,
        "detail": detail,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    marker_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return marker_path


def is_before_release(selected_timestamp: str, release_date_iso: str) -> bool:
    release_floor = release_date_iso.replace("-", "") + "000000"
    return selected_timestamp < release_floor


def find_missing_cached_versions(manifest: list[dict[str, object]], cache_root: Path) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    for row in manifest:
        version_id = str(row["version_id"])
        timestamp = row.get("selected_timestamp")
        archive_url = row.get("archive_url")
        if not timestamp or not archive_url:
            continue
        marker_path = no_data_marker_path(cache_root, version_id)
        if marker_path.exists():
            continue
        html_path, _meta_path = cache_paths(cache_root, version_id, str(timestamp))
        if not html_path.exists():
            missing.append(
                {
                    "version_id": version_id,
                    "selected_timestamp": str(timestamp),
                    "archive_url": str(archive_url),
                    "expected_html_path": str(html_path),
                }
            )
    return missing
