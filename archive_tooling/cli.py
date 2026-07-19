from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_tooling.acquire_html.cache import (
    cache_paths,
    fetch_bytes,
    find_missing_cached_versions,
    is_before_release,
    load_manifest,
    select_manifest_rows,
    write_no_data_marker,
    write_cached_html,
)
from archive_tooling.acquire_html.inspect import diff_structures, summarize_html_structure
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


def _find_manifest_row(manifest: list[dict[str, object]], version: str) -> dict[str, object] | None:
    version_upper = version.upper()
    return next((row for row in manifest if str(row["version_id"]).upper() == version_upper), None)


def cmd_fetch_canonical_html(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    manifest_path = (repo_root / args.manifest).resolve()
    release_ticks_path = (repo_root / args.release_ticks).resolve()
    cache_root = (repo_root / args.cache_dir).resolve()
    manifest = load_manifest(manifest_path)
    release_ticks = load_release_ticks(release_ticks_path)
    release_by_version = {str(row["version_id"]).upper(): str(row["release_date"]) for row in release_ticks}
    try:
        rows = select_manifest_rows(manifest, args.version, args.start_version, args.end_version)
    except ValueError as exc:
        print(str(exc))
        return 1

    fetched: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    placeholders: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []

    for row in rows:
        version_id = str(row["version_id"])
        timestamp = row.get("selected_timestamp")
        archive_url = row.get("archive_url")
        unresolved_reason = row.get("unresolved_reason")
        release_date = release_by_version.get(version_id.upper())

        if not timestamp or not archive_url:
            marker_path = write_no_data_marker(
                cache_root=cache_root,
                version_id=version_id,
                reason="no_data_for_version",
                selected_timestamp=str(timestamp) if timestamp else None,
                archive_url=str(archive_url) if archive_url else None,
                detail=str(unresolved_reason or "missing_timestamp_or_url"),
            )
            placeholders.append(
                {
                    "version_id": version_id,
                    "reason": str(unresolved_reason or "missing_timestamp_or_url"),
                    "marker_path": str(marker_path),
                }
            )
            continue

        if release_date and is_before_release(str(timestamp), release_date):
            marker_path = write_no_data_marker(
                cache_root=cache_root,
                version_id=version_id,
                reason="selected_snapshot_before_release_date",
                selected_timestamp=str(timestamp),
                archive_url=str(archive_url),
                detail=f"release_date={release_date}",
            )
            placeholders.append(
                {
                    "version_id": version_id,
                    "reason": "selected_snapshot_before_release_date",
                    "selected_timestamp": str(timestamp),
                    "release_date": release_date,
                    "marker_path": str(marker_path),
                }
            )
            continue

        html_path, _meta_path = cache_paths(cache_root, version_id, str(timestamp))
        if html_path.exists() and not args.force:
            skipped.append(
                {
                    "version_id": version_id,
                    "reason": "already_cached",
                    "html_path": str(html_path),
                }
            )
            continue

        try:
            content = fetch_bytes(str(archive_url))
            written_html, written_meta = write_cached_html(
                cache_root=cache_root,
                version_id=version_id,
                timestamp=str(timestamp),
                archive_url=str(archive_url),
                content=content,
            )
            fetched.append(
                {
                    "version_id": version_id,
                    "selected_timestamp": str(timestamp),
                    "html_path": str(written_html),
                    "meta_path": str(written_meta),
                }
            )
        except Exception as exc:
            failures.append(
                {
                    "version_id": version_id,
                    "selected_timestamp": str(timestamp),
                    "archive_url": str(archive_url),
                    "error": str(exc),
                }
            )

    print(
        json.dumps(
            {
                "requested_rows": len(rows),
                "fetched_count": len(fetched),
                "placeholder_count": len(placeholders),
                "skipped_count": len(skipped),
                "failure_count": len(failures),
                "fetched": fetched,
                "placeholders": placeholders,
                "skipped": skipped,
                "failures": failures,
            },
            indent=2,
        )
    )
    return 1 if failures else 0


def cmd_list_missing_canonical_html(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    manifest_path = (repo_root / args.manifest).resolve()
    cache_root = (repo_root / args.cache_dir).resolve()
    manifest = load_manifest(manifest_path)
    missing = find_missing_cached_versions(manifest, cache_root)
    print(json.dumps({"missing_count": len(missing), "missing": missing}, indent=2))
    return 0


def _load_cached_html_for_version(
    manifest: list[dict[str, object]],
    cache_root: Path,
    version: str,
) -> tuple[dict[str, object], str] | tuple[None, None]:
    row = _find_manifest_row(manifest, version)
    if row is None:
        return None, None
    timestamp = row.get("selected_timestamp")
    if not timestamp:
        return row, None
    html_path, _meta_path = cache_paths(cache_root, str(row["version_id"]), str(timestamp))
    if not html_path.exists():
        return row, None
    return row, html_path.read_text(encoding="utf-8", errors="replace")


def cmd_inspect_html_structure(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    manifest_path = (repo_root / args.manifest).resolve()
    cache_root = (repo_root / args.cache_dir).resolve()
    manifest = load_manifest(manifest_path)

    row, html_text = _load_cached_html_for_version(manifest, cache_root, args.version)
    if row is None:
        print(f"Version not found in manifest: {args.version}")
        return 1
    if html_text is None:
        print(f"Cached HTML not found for version {row['version_id']}; run fetch-canonical-html first.")
        return 1

    summary = summarize_html_structure(html_text)
    payload = {
        "version_id": row["version_id"],
        "selected_timestamp": row["selected_timestamp"],
        **summary,
    }
    print(json.dumps(payload, indent=2))
    return 0


def cmd_diff_html_structure(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    manifest_path = (repo_root / args.manifest).resolve()
    cache_root = (repo_root / args.cache_dir).resolve()
    manifest = load_manifest(manifest_path)

    left_row, left_html = _load_cached_html_for_version(manifest, cache_root, args.left_version)
    right_row, right_html = _load_cached_html_for_version(manifest, cache_root, args.right_version)

    if left_row is None:
        print(f"Version not found in manifest: {args.left_version}")
        return 1
    if right_row is None:
        print(f"Version not found in manifest: {args.right_version}")
        return 1
    if left_html is None:
        print(f"Cached HTML not found for version {left_row['version_id']}; run fetch-canonical-html first.")
        return 1
    if right_html is None:
        print(f"Cached HTML not found for version {right_row['version_id']}; run fetch-canonical-html first.")
        return 1

    left_summary = summarize_html_structure(left_html)
    right_summary = summarize_html_structure(right_html)
    diff = diff_structures(str(left_row["version_id"]), str(right_row["version_id"]), left_summary, right_summary)
    print(json.dumps(diff, indent=2))
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
        help="Inspect candidate captures for a version.",
    )
    inspect.add_argument("--version", required=True)
    inspect.add_argument("--repo-root", default=".")
    inspect.add_argument("--release-ticks", default="data/release_ticks.json")
    inspect.add_argument("--cdx-cache", default="data/cdx/game8_tierlist_cdx.json")
    inspect.set_defaults(func=cmd_inspect_snapshot_candidates)

    fetch = subparsers.add_parser(
        "fetch-canonical-html",
        help="Fetch canonical HTML for selected versions.",
    )
    fetch.add_argument("--repo-root", default=".")
    fetch.add_argument("--manifest", default="data/snapshot_manifest.json")
    fetch.add_argument("--release-ticks", default="data/release_ticks.json")
    fetch.add_argument("--cache-dir", default="data/html_cache")
    fetch.add_argument("--version")
    fetch.add_argument("--start-version")
    fetch.add_argument("--end-version")
    fetch.add_argument("--force", action="store_true")
    fetch.set_defaults(func=cmd_fetch_canonical_html)

    inspect_html = subparsers.add_parser(
        "inspect-html-structure",
        help="Summarize headings and tables for a cached version HTML.",
    )
    inspect_html.add_argument("--repo-root", default=".")
    inspect_html.add_argument("--manifest", default="data/snapshot_manifest.json")
    inspect_html.add_argument("--cache-dir", default="data/html_cache")
    inspect_html.add_argument("--version", required=True)
    inspect_html.set_defaults(func=cmd_inspect_html_structure)

    diff_html = subparsers.add_parser(
        "diff-html-structure",
        help="Compare cached HTML structure between two versions.",
    )
    diff_html.add_argument("--repo-root", default=".")
    diff_html.add_argument("--manifest", default="data/snapshot_manifest.json")
    diff_html.add_argument("--cache-dir", default="data/html_cache")
    diff_html.add_argument("--left-version", required=True)
    diff_html.add_argument("--right-version", required=True)
    diff_html.set_defaults(func=cmd_diff_html_structure)

    missing_html = subparsers.add_parser(
        "list-missing-canonical-html",
        help="List manifest versions whose canonical HTML is not cached locally.",
    )
    missing_html.add_argument("--repo-root", default=".")
    missing_html.add_argument("--manifest", default="data/snapshot_manifest.json")
    missing_html.add_argument("--cache-dir", default="data/html_cache")
    missing_html.set_defaults(func=cmd_list_missing_canonical_html)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
