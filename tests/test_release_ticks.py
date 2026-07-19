from datetime import date

from archive_tooling.release_ticks import parse_release_markdown, to_release_ticks_payload


def test_parse_release_markdown_and_payload(tmp_path):
    markdown = """# 1.0a
## September 28, 2020

Diluc
Jean

# 1.0b
## October 20, 2020

Klee
"""
    path = tmp_path / "releases.md"
    path.write_text(markdown, encoding="utf-8")

    ticks = parse_release_markdown(path)
    assert [t.version_id for t in ticks] == ["1.0A", "1.0B"]
    assert ticks[0].release_date == date(2020, 9, 28)
    assert ticks[0].introduced_characters == ["Diluc", "Jean"]

    payload = to_release_ticks_payload(ticks)
    assert payload[0]["next_release_date"] == "2020-10-20"
    assert payload[0]["version_end_date"] == "2020-10-19"
    assert payload[1]["next_release_date"] is None
    assert payload[1]["version_end_date"] == "2020-10-20"
