from archive_tooling.manifest import build_manifest, pick_candidates_for_version


def test_pick_candidates_for_version_split_before_and_after_cutoff():
    captures = [
        {"timestamp": "20201019120000", "original": "https://example.com"},
        {"timestamp": "20201019235959", "original": "https://example.com"},
        {"timestamp": "20201020000000", "original": "https://example.com"},
    ]
    before, after = pick_candidates_for_version(captures, "2020-10-19")

    assert [c["timestamp"] for c in before] == ["20201019120000", "20201019235959"]
    assert [c["timestamp"] for c in after] == ["20201020000000"]


def test_build_manifest_selects_latest_before_end_date():
    ticks = [
        {"version_id": "1.0A", "version_end_date": "2020-10-19"},
        {"version_id": "1.0B", "version_end_date": "2020-11-10"},
    ]
    captures = [
        {
            "timestamp": "20201019100000",
            "original": "https://game8.co/games/Genshin-Impact/archives/297465",
        },
        {
            "timestamp": "20201019230000",
            "original": "https://game8.co/games/Genshin-Impact/archives/297465",
        },
        {
            "timestamp": "20201101014348",
            "original": "https://game8.co/games/Genshin-Impact/archives/297465",
        },
    ]

    manifest = build_manifest(ticks, captures, overrides={})

    assert manifest[0]["selected_timestamp"] == "20201019230000"
    assert manifest[0]["selection_reason"] == "latest_leq_end_date"
    assert manifest[1]["selected_timestamp"] == "20201101014348"


def test_build_manifest_honors_override():
    ticks = [{"version_id": "1.0A", "version_end_date": "2020-10-19"}]
    captures = []
    overrides = {
        "1.0A": {
            "selected_timestamp": "20201024083644",
            "original_url": "https://game8.co/games/Genshin-Impact/archives/297465",
            "note": "manual fallback",
        }
    }

    manifest = build_manifest(ticks, captures, overrides=overrides)

    assert manifest[0]["selection_reason"] == "manual_override"
    assert manifest[0]["selected_timestamp"] == "20201024083644"
    assert "20201024083644" in manifest[0]["archive_url"]
    assert manifest[0]["override"]["note"] == "manual fallback"
