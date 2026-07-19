from archive_tooling.acquire_html.inspect import diff_structures, summarize_html_structure


SAMPLE_HTML = """
<html>
  <body>
    <h1>Genshin Tier List</h1>
    <h2>Main DPS</h2>
    <table>
      <tr><th>Tier</th><th>Character</th></tr>
      <tr><td>SS</td><td>Diluc</td></tr>
      <tr><td>S</td><td>Keqing</td></tr>
    </table>
  </body>
</html>
"""


def test_summarize_html_structure_counts_headings_and_tables():
    summary = summarize_html_structure(SAMPLE_HTML)
    assert summary["heading_count"] == 2
    assert summary["table_count"] == 1
    assert summary["tables"][0]["rows"] == 3
    assert summary["tables"][0]["max_cols"] == 2


def test_diff_structures_reports_changes():
    left = summarize_html_structure(SAMPLE_HTML)
    right = summarize_html_structure(SAMPLE_HTML.replace("<h2>Main DPS</h2>", "<h2>Support</h2>"))
    diff = diff_structures("1.0A", "1.0B", left, right)
    assert diff["left_version"] == "1.0A"
    assert diff["right_version"] == "1.0B"
    assert diff["first_heading_changed"] is False
