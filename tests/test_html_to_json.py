from bs4 import BeautifulSoup

from extract_rankings.html_to_json import extract_rank, extract_rankings


def test_extract_rank_parses_sss_from_image_alt():
    soup = BeautifulSoup(
        '<th><img alt="SSS Rating.png" title="unused" /></th>',
        "html.parser",
    )

    assert extract_rank(soup.th) == "SSS"


def test_extract_rank_preserves_ss_behavior():
    soup = BeautifulSoup(
        '<th><img alt="Genshin - SS Rank Icon" /></th>',
        "html.parser",
    )

    assert extract_rank(soup.th) == "SS"


def test_extract_rank_ignores_unknown_label():
    soup = BeautifulSoup(
        '<th><img alt="Legend Rank Icon" /></th>',
        "html.parser",
    )

    assert extract_rank(soup.th) is None


def test_extract_rankings_includes_sss_rows():
    html = """
    <html>
      <head><title>3.4A Rankings</title></head>
      <body>
        <table>
          <tr>
            <th></th>
            <th>DPS</th>
            <th>Sub-DPS</th>
            <th>Support</th>
          </tr>
          <tr>
            <th><img alt="SSS Rating.png" /></th>
            <td><a href="https://game8.co/games/Genshin-Impact/archives/111">x</a></td>
            <td></td>
            <td></td>
          </tr>
          <tr>
            <th><img alt="SS Rank Icon" /></th>
            <td><a href="https://game8.co/games/Genshin-Impact/archives/222">y</a></td>
            <td></td>
            <td></td>
          </tr>
        </table>
      </body>
    </html>
    """

    assert extract_rankings(html) == {
        "3.4A": {
            "Main DPS": {"SSS": ["111"], "SS": ["222"]},
            "Sub-DPS": {"SSS": [], "SS": []},
            "Support": {"SSS": [], "SS": []},
        }
    }
