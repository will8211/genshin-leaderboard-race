from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path


@dataclass(frozen=True)
class ReleaseTick:
    version_id: str
    release_date: date
    introduced_characters: list[str]


def _normalize_version(raw: str) -> str:
    return raw.strip().upper()


def _parse_date(raw: str) -> date:
    return datetime.strptime(raw.strip(), "%B %d, %Y").date()


def parse_release_markdown(path: Path) -> list[ReleaseTick]:
    lines = path.read_text(encoding="utf-8").splitlines()

    ticks: list[ReleaseTick] = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line.startswith("# "):
            i += 1
            continue

        version = _normalize_version(line[2:])
        i += 1

        while i < len(lines) and not lines[i].strip():
            i += 1

        if i >= len(lines) or not lines[i].strip().startswith("## "):
            raise ValueError(f"Missing release date heading after version {version}")

        release = _parse_date(lines[i].strip()[3:])
        i += 1

        chars: list[str] = []
        while i < len(lines):
            current = lines[i].strip()
            if not current:
                i += 1
                continue
            if current.startswith("# "):
                break
            if current.startswith("## "):
                raise ValueError(f"Unexpected date heading in character section for {version}")
            chars.append(current)
            i += 1

        ticks.append(
            ReleaseTick(
                version_id=version,
                release_date=release,
                introduced_characters=chars,
            )
        )

    return ticks


def to_release_ticks_payload(ticks: list[ReleaseTick]) -> list[dict[str, object]]:
    payload: list[dict[str, object]] = []
    for idx, tick in enumerate(ticks):
        next_release = ticks[idx + 1].release_date if idx + 1 < len(ticks) else None
        version_end = (next_release - timedelta(days=1)) if next_release else tick.release_date

        payload.append(
            {
                "version_id": tick.version_id,
                "release_date": tick.release_date.isoformat(),
                "next_release_date": next_release.isoformat() if next_release else None,
                "version_end_date": version_end.isoformat(),
                "introduced_characters": tick.introduced_characters,
            }
        )
    return payload


def build_release_ticks_file(input_path: Path, output_path: Path) -> list[dict[str, object]]:
    ticks = parse_release_markdown(input_path)
    payload = to_release_ticks_payload(ticks)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload
