"""HTML parsing and table extraction utilities."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup
from bs4.element import Tag


UNWANTED_ATTRIBUTES = {"width", "height", "class", "style"}


def load_html_from_cache(html_path: Path) -> str:
    """Load HTML content from a cache file."""
    return html_path.read_text(encoding="utf-8", errors="replace")


def remove_unwanted_attributes(
    element: Tag,
    attributes: set[str] = UNWANTED_ATTRIBUTES,
) -> None:
    """Remove unwanted attributes from an element and its descendants."""
    for tag in [element, *element.find_all(True)]:
        for attribute in attributes:
            tag.attrs.pop(attribute, None)


def extract_table_by_selector(html_content: str, selector: str) -> str | None:
    """
    Extract a table element from HTML using a CSS selector.

    The selector format "table:nth-of-type(N)" is interpreted as selecting
    the Nth table in document order, using a 1-based index.

    Removes unwanted presentation attributes from the table and all
    descendant elements.
    """
    soup = BeautifulSoup(html_content, "lxml")

    if selector.startswith("table:nth-of-type(") and selector.endswith(")"):
        index_str = selector[len("table:nth-of-type("):-1]

        try:
            table_index = int(index_str) - 1
        except ValueError:
            return None

        all_tables = soup.find_all("table")

        if table_index < 0 or table_index >= len(all_tables):
            return None

        table = all_tables[table_index]
    else:
        table = soup.select_one(selector)

        if table is None:
            return None

    remove_unwanted_attributes(table)

    return str(table)


def extract_tables_by_selectors(
    html_content: str,
    selectors: list[str],
) -> list[str]:
    """
    Extract multiple tables from HTML using CSS selectors.

    Returns table HTML strings in the same order as the selectors.
    Tables that cannot be found are skipped.
    """
    tables = []

    for selector in selectors:
        table_html = extract_table_by_selector(html_content, selector)

        if table_html:
            tables.append(table_html)

    return tables