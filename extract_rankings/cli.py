"""Command-line interface for table extraction."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from archive_tooling.acquire_html.cache import load_manifest, select_manifest_rows
from extract_rankings.extractor import (
    extract_tables_for_version,
    load_table_selectors,
    write_output_file,
)


def main() -> int:
    """Main entry point for extract-rankings CLI."""
    parser = argparse.ArgumentParser(
        description="Extract tier list tables from cached HTML snapshots"
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=".",
        help="Path to repository root (default: current directory)",
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default="data/snapshot_manifest.json",
        help="Path to snapshot manifest (default: data/snapshot_manifest.json)",
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default="data/html_cache",
        help="Path to HTML cache directory (default: data/html_cache)",
    )
    parser.add_argument(
        "--selectors",
        type=str,
        default="selected_tables.yaml",
        help="Path to table selectors YAML (default: selected_tables.yaml)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/extracted_rankings/relevant_tables",
        help="Output directory for extracted tables (default: data/extracted_rankings/relevant_tables)",
    )
    parser.add_argument(
        "--version",
        type=str,
        help="Extract tables for a specific version (e.g., 1.0B)",
    )
    parser.add_argument(
        "--start-version",
        type=str,
        help="Start of version range (requires --end-version)",
    )
    parser.add_argument(
        "--end-version",
        type=str,
        help="End of version range (requires --start-version)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Extract tables for all versions in selectors config",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing output files",
    )
    
    args = parser.parse_args()
    
    repo_root = Path(args.repo_root).resolve()
    manifest_path = (repo_root / args.manifest).resolve()
    cache_root = (repo_root / args.cache_dir).resolve()
    selectors_path = (repo_root / args.selectors).resolve()
    output_root = (repo_root / args.output_dir).resolve()
    
    # Load manifest and selectors
    try:
        manifest = load_manifest(manifest_path)
        table_selectors = load_table_selectors(selectors_path)
    except Exception as exc:
        print(f"Error loading configuration: {exc}", file=sys.stderr)
        return 1
    
    # Select versions to process
    if args.all:
        # Process all versions from the YAML config
        versions_to_process = list(table_selectors.keys())
        # Build manifest-like rows for compatibility
        rows = []
        manifest_by_id = {str(row["version_id"]): row for row in manifest}
        for version_id in versions_to_process:
            if version_id in manifest_by_id:
                rows.append(manifest_by_id[version_id])
            else:
                # Version in config but not in manifest - add dummy row
                rows.append({"version_id": version_id, "selected_timestamp": None})
    else:
        try:
            rows = select_manifest_rows(
                manifest,
                args.version,
                args.start_version,
                args.end_version,
            )
        except ValueError as exc:
            print(f"Error selecting versions: {exc}", file=sys.stderr)
            return 1
    
    extracted = []
    skipped = []
    failures = []
    
    for row in rows:
        version_id = str(row["version_id"])
        timestamp = row.get("selected_timestamp")
        
        if not timestamp:
            skipped.append({
                "version_id": version_id,
                "reason": "no_selected_timestamp",
            })
            continue
        
        output_path = output_root / f"{version_id}.html"
        
        if output_path.exists() and not args.force:
            skipped.append({
                "version_id": version_id,
                "reason": "already_exists",
                "output_path": str(output_path),
            })
            continue
        
        # Get table config for this version
        table_config = table_selectors.get(version_id, {})
        
        try:
            html_content = extract_tables_for_version(
                version_id,
                str(timestamp),
                table_config,
                cache_root,
            )
            write_output_file(output_path, html_content)
            
            extracted.append({
                "version_id": version_id,
                "selected_timestamp": str(timestamp),
                "output_path": str(output_path),
                "table_types": list(table_config.keys()),
            })
        except Exception as exc:
            failures.append({
                "version_id": version_id,
                "selected_timestamp": str(timestamp),
                "error": str(exc),
            })
    
    result = {
        "requested_rows": len(rows),
        "extracted_count": len(extracted),
        "skipped_count": len(skipped),
        "failure_count": len(failures),
        "extracted": extracted,
        "skipped": skipped,
        "failures": failures,
    }
    
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
