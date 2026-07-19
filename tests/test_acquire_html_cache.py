import json

from archive_tooling.acquire_html.cache import (
    find_missing_cached_versions,
    is_before_release,
    no_data_marker_path,
    select_manifest_rows,
    write_no_data_marker,
)


def _manifest_versions():
    return [
        {"version_id": "1.0A"},
        {"version_id": "1.0B"},
        {"version_id": "1.1A"},
        {"version_id": "1.1B"},
    ]


def test_select_manifest_rows_single_version():
    rows = select_manifest_rows(_manifest_versions(), version="1.1A", start_version=None, end_version=None)
    assert [r["version_id"] for r in rows] == ["1.1A"]


def test_select_manifest_rows_range_inclusive():
    rows = select_manifest_rows(_manifest_versions(), version=None, start_version="1.0B", end_version="1.1A")
    assert [r["version_id"] for r in rows] == ["1.0B", "1.1A"]


def test_select_manifest_rows_requires_both_range_bounds():
    try:
        select_manifest_rows(_manifest_versions(), version=None, start_version="1.0B", end_version=None)
    except ValueError as exc:
        assert "required together" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_is_before_release():
    assert is_before_release("20221103184314", "2022-11-18") is True
    assert is_before_release("20221118000000", "2022-11-18") is False


def test_no_data_marker_excludes_version_from_missing_report(tmp_path):
    cache_root = tmp_path / "html_cache"
    marker = write_no_data_marker(
        cache_root=cache_root,
        version_id="3.2B",
        reason="selected_snapshot_before_release_date",
        selected_timestamp="20221103184314",
        archive_url="https://web.archive.org/web/20221103184314/https://example.com",
        detail="release_date=2022-11-18",
    )
    assert marker == no_data_marker_path(cache_root, "3.2B")
    data = json.loads(marker.read_text(encoding="utf-8"))
    assert data["reason"] == "selected_snapshot_before_release_date"

    manifest = [
        {
            "version_id": "3.2B",
            "selected_timestamp": "20221103184314",
            "archive_url": "https://web.archive.org/web/20221103184314/https://example.com",
        }
    ]
    missing = find_missing_cached_versions(manifest, cache_root)
    assert missing == []
