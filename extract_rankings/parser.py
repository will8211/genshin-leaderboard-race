"""HTML parsing and table extraction utilities."""

from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup
from bs4.element import Tag


UNWANTED_ATTRIBUTES = {"width", "height", "class", "style"}

WAYBACK_PREFIX_PATTERN = re.compile(
    r"https://web\.archive\.org/web/\d+/"
)


def load_html_from_cache(html_path: Path) -> str:
    """Load HTML content from a cache file."""
    return html_path.read_text(encoding="utf-8", errors="replace")


def clean_table(element: Tag) -> None:
    """
    Clean an extracted table and all its descendants.

    Removes unwanted presentation attributes and strips timestamped
    Wayback Machine prefixes from attribute values such as href and src.
    """
    for tag in [element, *element.find_all(True)]:
        for attribute in UNWANTED_ATTRIBUTES:
            tag.attrs.pop(attribute, None)

        for attribute, value in list(tag.attrs.items()):
            if isinstance(value, str):
                tag.attrs[attribute] = WAYBACK_PREFIX_PATTERN.sub("", value)

            elif isinstance(value, list):
                tag.attrs[attribute] = [
                    WAYBACK_PREFIX_PATTERN.sub("", item)
                    if isinstance(item, str)
                    else item
                    for item in value
                ]


def extract_table_by_selector(
    html_content: str,
    selector: str,
) -> str | None:
    """
    Extract and clean a table element using a CSS selector.

    The selector format ``table:nth-of-type(N)`` is interpreted as selecting
    the Nth table in overall document order, using a 1-based index. This
    matches the behavior of archive_tooling's inspect-html-structure command.

    Other selector formats are handled as ordinary CSS selectors.

    Returns the full outer HTML of the cleaned table, or None if no matching
    table is found.
    """
    soup = BeautifulSoup(html_content, "lxml")

    if selector.startswith("table:nth-of-type(") and selector.endswith(")"):
        index_str = selector[len("table:nth-of-type(") : -1]

        try:
            table_index = int(index_str) - 1
        except ValueError:
            return None

        all_tables = soup.find_all("table")

        if table_index < 0 or table_index >= len(all_tables):
            return None

        table = all_tables[table_index]
    else:
        selected_element = soup.select_one(selector)

        if selected_element is None or selected_element.name != "table":
            return None

        table = selected_element

    clean_table(table)

    return str(table)


def extract_tables_by_selectors(
    html_content: str,
    selectors: list[str],
) -> list[str]:
    """
    Extract and clean multiple tables using CSS selectors.

    Returns table HTML strings in the same order as their selectors.
    Selectors that do not match a table are skipped.
    """
    tables: list[str] = []

    for selector in selectors:
        table_html = extract_table_by_selector(html_content, selector)

        if table_html is not None:
            tables.append(table_html)

    return tables