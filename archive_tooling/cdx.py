from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


CDX_FIELDS = ["timestamp", "original", "statuscode", "mimetype", "digest", "length"]


def _cdx_url(target_url: str) -> str:
    query = urlencode(
        {
            "url": target_url,
            "output": "json",
            "fl": ",".join(CDX_FIELDS),
            "filter": "statuscode:200",
        }
    )
    return f"https://web.archive.org/cdx/search/cdx?{query}"


def fetch_cdx_captures(target_url: str) -> list[dict[str, str]]:
    url = _cdx_url(target_url)
    with urlopen(url) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if not payload:
        return []

    headers = payload[0]
    rows = payload[1:]
    captures: list[dict[str, str]] = []
    for row in rows:
        item = dict(zip(headers, row))
        captures.append(item)
    return captures


def dedupe_captures(captures: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, str]] = []
    for capture in captures:
        key = (capture.get("timestamp", ""), capture.get("digest", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(capture)
    return deduped


def write_cdx_cache(cache_path: Path, target_url: str, captures: list[dict[str, str]]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "target_url": target_url,
        "captures": captures,
    }
    cache_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def load_cdx_cache(cache_path: Path) -> dict[str, object] | None:
    if not cache_path.exists():
        return None
    return json.loads(cache_path.read_text(encoding="utf-8"))
