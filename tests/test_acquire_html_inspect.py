from archive_tooling.acquire_html.inspect import (
  diff_structures,
  select_tables_with_first_col_alt_substring,
  summarize_html_structure,
)


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
    assert summary["tables"][0]["name"] == "Genshin Tier List > Main DPS"
    assert summary["tables"][0]["rows"] == 3
    assert summary["tables"][0]["max_cols"] == 2


def test_diff_structures_reports_changes():
    left = summarize_html_structure(SAMPLE_HTML)
    right = summarize_html_structure(SAMPLE_HTML.replace("<h2>Main DPS</h2>", "<h2>Support</h2>"))
    diff = diff_structures("1.0A", "1.0B", left, right)
    assert diff["left_version"] == "1.0A"
    assert diff["right_version"] == "1.0B"
    assert diff["first_heading_changed"] is False
    assert len(diff["table_shape_changes"]) == 1
    assert diff["table_shape_changes"][0]["left"]["name"] == "Genshin Tier List > Main DPS"
    assert diff["table_shape_changes"][0]["right"]["name"] == "Genshin Tier List > Support"


def test_summarize_html_structure_captures_first_col_alts():
    html = """
    <html>
      <body>
        <h2>A Table</h2>
        <table>
          <tr><td><img alt="A Tier - Xiao"/></td><td>Xiao</td></tr>
          <tr><td><img alt="B Tier - Razor"/></td><td>Razor</td></tr>
        </table>
      </body>
    </html>
    """
    summary = summarize_html_structure(html)
    assert summary["table_count"] == 1
    assert summary["tables"][0]["first_col_alts"] == [["A Tier - Xiao"], ["B Tier - Razor"]]


def test_select_tables_with_first_col_alt_substring_filters_to_a_tier():
    html = """
    <html>
      <body>
        <h2>Main DPS</h2>
        <table>
          <tr><td><img alt="A Tier - Xiao"/></td><td>Xiao</td></tr>
          <tr><td><img alt="S Tier - Hu Tao"/></td><td>Hu Tao</td></tr>
        </table>
        <h2>Sub DPS</h2>
        <table>
          <tr><td><img alt="B Tier - Razor"/></td><td>Razor</td></tr>
        </table>
      </body>
    </html>
    """
    summary = summarize_html_structure(html)
    filtered = select_tables_with_first_col_alt_substring(summary, "A Tier")
    assert len(filtered) == 1
    assert filtered[0]["name"] == "Main DPS"


def test_table_name_includes_immediately_previous_parent_heading_level():
    html = """
    <html>
      <body>
        <h2>foo</h2>
        <h3>bar</h3>
        <table>
          <tr><td>x</td></tr>
        </table>
      </body>
    </html>
    """
    summary = summarize_html_structure(html)
    assert summary["tables"][0]["name"] == "foo > bar"


def test_table_name_does_not_include_non_immediate_parent_level_heading():
    html = """
    <html>
      <body>
        <h2>foo</h2>
        <h4>bar</h4>
        <table>
          <tr><td>x</td></tr>
        </table>
      </body>
    </html>
    """
    summary = summarize_html_structure(html)
    assert summary["tables"][0]["name"] == "bar"
