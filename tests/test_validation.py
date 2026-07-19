import json

from archive_tooling.validation import build_completed_work_summary, validate_completed_work_bundle


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_validate_completed_work_bundle_passes_with_no_data_marker(monkeypatch, tmp_path):
    monkeypatch.setattr("archive_tooling.validation.validate_contract_bundle", lambda _repo_root: [])

    _write_json(
        tmp_path / "data" / "release_ticks.json",
        [
            {
                "version_id": "1.0A",
                "release_date": "2020-09-28",
                "next_release_date": None,
                "version_end_date": "2020-10-19",
                "introduced_characters": [],
            }
        ],
    )
    _write_json(
        tmp_path / "data" / "snapshot_manifest.json",
        [
            {
                "version_id": "1.0A",
                "target_end_date": "2020-10-19",
                "selected_timestamp": "20201019230000",
                "archive_url": "https://web.archive.org/web/20201019230000/https://example.com",
                "selection_reason": "latest_leq_end_date",
                "quality_flags": [],
                "override": None,
                "unresolved_reason": None,
            }
        ],
    )

    marker = tmp_path / "data" / "html_cache" / "1.0A" / ".no-data"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text('{"reason": "selected_snapshot_before_release_date"}\n', encoding="utf-8")

    assert validate_completed_work_bundle(tmp_path) == []


def test_validate_completed_work_bundle_flags_timestamp_after_end_date(monkeypatch, tmp_path):
    monkeypatch.setattr("archive_tooling.validation.validate_contract_bundle", lambda _repo_root: [])

    _write_json(
        tmp_path / "data" / "release_ticks.json",
        [
            {
                "version_id": "1.0A",
                "release_date": "2020-09-28",
                "next_release_date": None,
                "version_end_date": "2020-10-19",
                "introduced_characters": [],
            }
        ],
    )
    _write_json(
        tmp_path / "data" / "snapshot_manifest.json",
        [
            {
                "version_id": "1.0A",
                "target_end_date": "2020-10-19",
                "selected_timestamp": "20201020000000",
                "archive_url": "https://web.archive.org/web/20201020000000/https://example.com",
                "selection_reason": "latest_leq_end_date",
                "quality_flags": [],
                "override": None,
                "unresolved_reason": None,
            }
        ],
    )

    html_dir = tmp_path / "data" / "html_cache" / "1.0A"
    html_dir.mkdir(parents=True, exist_ok=True)
    (html_dir / "20201020000000.html").write_text("<html></html>", encoding="utf-8")
    (html_dir / "20201020000000.meta.json").write_text("{}\n", encoding="utf-8")

    failures = validate_completed_work_bundle(tmp_path)
    assert any("selected timestamp exceeds target_end_date" in item for item in failures)


def test_build_completed_work_summary_counts_cache_coverage(tmp_path):
    _write_json(
        tmp_path / "data" / "release_ticks.json",
        [
            {
                "version_id": "1.0A",
                "release_date": "2020-09-28",
                "next_release_date": "2020-11-11",
                "version_end_date": "2020-11-10",
                "introduced_characters": [],
            },
            {
                "version_id": "1.1A",
                "release_date": "2020-11-11",
                "next_release_date": None,
                "version_end_date": "2020-12-22",
                "introduced_characters": [],
            },
        ],
    )
    _write_json(
        tmp_path / "data" / "snapshot_manifest.json",
        [
            {
                "version_id": "1.0A",
                "target_end_date": "2020-11-10",
                "selected_timestamp": "20201101014348",
                "archive_url": "https://web.archive.org/web/20201101014348/https://example.com",
                "selection_reason": "latest_leq_end_date",
                "quality_flags": [],
                "override": None,
                "unresolved_reason": None,
            },
            {
                "version_id": "1.1A",
                "target_end_date": "2020-12-22",
                "selected_timestamp": None,
                "archive_url": None,
                "selection_reason": "unresolved",
                "quality_flags": [],
                "override": None,
                "unresolved_reason": "no_capture_leq_version_end",
            },
        ],
    )

    html_dir = tmp_path / "data" / "html_cache" / "1.0A"
    html_dir.mkdir(parents=True, exist_ok=True)
    (html_dir / ".no-data").write_text('{"reason":"selected_snapshot_before_release_date"}\n', encoding="utf-8")

    summary = build_completed_work_summary(tmp_path)
    assert summary["release_tick_count"] == 2
    assert summary["manifest"]["resolvable_count"] == 1
    assert summary["manifest"]["unresolved_count"] == 1
    assert summary["cache"]["no_data_marker_count"] == 1
    assert summary["cache"]["coverage_count"] == 1
