from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_tooling.cdx import dedupe_captures, fetch_cdx_captures, load_cdx_cache, write_cdx_cache
from archive_tooling.manifest import (
    build_manifest,
    load_overrides,
    load_release_ticks,
    pick_candidates_for_version,
    write_manifest,
)
from archive_tooling.release_ticks import build_release_ticks_file
from archive_tooling.validation import validate_contract_bundle


def cmd_validate_contracts(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    failures = validate_contract_bundle(repo_root)
    if failures:
        print("Contract validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Contract validation passed.")
    return 0


def cmd_build_release_ticks(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    input_path = (repo_root / args.input_markdown).resolve()
    output_path = (repo_root / args.output_json).resolve()
    payload = build_release_ticks_file(input_path, output_path)
    print(f"Wrote {len(payload)} release ticks to {output_path}")
    return 0


def _load_or_fetch_cdx(cache_path: Path, target_url: str, refresh: bool) -> list[dict[str, str]]:
    cached = load_cdx_cache(cache_path)
    if cached and not refresh:
        return dedupe_captures(list(cached.get("captures", [])))

    captures = dedupe_captures(fetch_cdx_captures(target_url))
    write_cdx_cache(cache_path, target_url, captures)
    return captures


def cmd_build_snapshot_manifest(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    release_ticks_path = (repo_root / args.release_ticks).resolve()
    manifest_path = (repo_root / args.output_manifest).resolve()
    cdx_cache_path = (repo_root / args.cdx_cache).resolve()
    overrides_path = (repo_root / args.overrides).resolve()

    release_ticks = load_release_ticks(release_ticks_path)
    captures = _load_or_fetch_cdx(cdx_cache_path, args.target_url, args.refresh_cdx)
    overrides = load_overrides(overrides_path)

    manifest = build_manifest(release_ticks, captures, overrides)
    write_manifest(manifest_path, manifest)

    unresolved = sum(1 for row in manifest if row.get("unresolved_reason"))
    print(f"Wrote snapshot manifest with {len(manifest)} rows to {manifest_path}")
    print(f"Unresolved rows: {unresolved}")
    return 0


def cmd_inspect_snapshot_candidates(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    release_ticks_path = (repo_root / args.release_ticks).resolve()
    cdx_cache_path = (repo_root / args.cdx_cache).resolve()
    release_ticks = load_release_ticks(release_ticks_path)
    target_tick = next((row for row in release_ticks if str(row["version_id"]).upper() == args.version.upper()), None)
    if target_tick is None:
        print(f"Version not found in release ticks: {args.version}")
        return 1

    cached = load_cdx_cache(cdx_cache_path)
    if not cached:
        print(f"CDX cache not found at {cdx_cache_path}. Run build-snapshot-manifest first.")
        return 1

    captures = dedupe_captures(list(cached.get("captures", [])))
    before_or_equal, after = pick_candidates_for_version(captures, str(target_tick["version_end_date"]))

    print(json.dumps(
        {
            "version_id": target_tick["version_id"],
            "version_end_date": target_tick["version_end_date"],
            "candidate_count_before_or_equal": len(before_or_equal),
            "candidate_count_after": len(after),
            "latest_before_or_equal": before_or_equal[-1] if before_or_equal else None,
            "recent_before_or_equal": before_or_equal[-5:],
            "earliest_after": after[0] if after else None,
        },
        indent=2,
    ))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="genshin-archive",
        description="Wayback archive and manifest tooling.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser(
        "validate-contracts",
        help="Validate known artifact JSON files against schemas.",
    )
    validate.add_argument(
        "--repo-root",
        default=".",
        help="Repository root containing data/ and schemas/.",
    )
    validate.set_defaults(func=cmd_validate_contracts)

    release_ticks = subparsers.add_parser(
        "build-release-ticks",
        help="Parse releases markdown into release_ticks artifact.",
    )
    release_ticks.add_argument("--repo-root", default=".")
    release_ticks.add_argument("--input-markdown", default="releases_genshin.md")
    release_ticks.add_argument("--output-json", default="data/release_ticks.json")
    release_ticks.set_defaults(func=cmd_build_release_ticks)

    manifest = subparsers.add_parser(
        "build-snapshot-manifest",
        help="Build snapshot manifest from release ticks and CDX data.",
    )
    manifest.add_argument("--repo-root", default=".")
    manifest.add_argument("--release-ticks", default="data/release_ticks.json")
    manifest.add_argument("--output-manifest", default="data/snapshot_manifest.json")
    manifest.add_argument("--cdx-cache", default="data/cdx/game8_tierlist_cdx.json")
    manifest.add_argument("--overrides", default="data/snapshot_overrides.json")
    manifest.add_argument(
        "--target-url",
        default="https://game8.co/games/Genshin-Impact/archives/297465",
    )
    manifest.add_argument("--refresh-cdx", action="store_true")
    manifest.set_defaults(func=cmd_build_snapshot_manifest)

    inspect = subparsers.add_parser(
        "inspect-snapshot-candidates",
        help="Inspect candidate captures for a version (placeholder).",
    )
    inspect.add_argument("--version", required=True)
    inspect.add_argument("--repo-root", default=".")
    inspect.add_argument("--release-ticks", default="data/release_ticks.json")
    inspect.add_argument("--cdx-cache", default="data/cdx/game8_tierlist_cdx.json")
    inspect.set_defaults(func=cmd_inspect_snapshot_candidates)

    fetch = subparsers.add_parser(
        "fetch-canonical-html",
        help="Fetch canonical HTML for selected versions (placeholder).",
    )
    fetch.add_argument("--version")
    fetch.add_argument("--start-version")
    fetch.add_argument("--end-version")
    fetch.set_defaults(func=lambda _args: cmd_placeholder("fetch-canonical-html"))

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
