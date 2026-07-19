from archive_tooling.acquire_html.cache import select_manifest_rows


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
