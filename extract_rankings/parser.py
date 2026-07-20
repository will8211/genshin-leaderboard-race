"""HTML parsing and table extraction utilities."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup


def load_html_from_cache(html_path: Path) -> str:
    """Load HTML content from a cache file."""
    return html_path.read_text(encoding="utf-8", errors="replace")


def extract_table_by_selector(html_content: str, selector: str) -> str | None:
    """
    Extract a table element from HTML using a CSS selector.
    
    The selector format "table:nth-of-type(N)" is interpreted as selecting
    the Nth table in document order (1-based), matching the behavior of
    archive_tooling's inspect-html-structure command.
    
    Returns the full outer HTML of the table element, or None if not found.
    Preserves all attributes, classes, and nested structure.
    """
    soup = BeautifulSoup(html_content, "lxml")
    
    # Parse the selector to extract the table index
    # Format: "table:nth-of-type(N)" where N is 1-based
    if selector.startswith("table:nth-of-type(") and selector.endswith(")"):
        index_str = selector[len("table:nth-of-type("):-1]
        try:
            # Convert from 1-based CSS selector to 0-based Python index
            table_index = int(index_str) - 1
        except ValueError:
            return None
        
        # Find all tables in document order
        all_tables = soup.find_all("table")
        
        if table_index < 0 or table_index >= len(all_tables):
            return None
        
        # Return the full table HTML including all attributes
        return str(all_tables[table_index])
    else:
        # Fall back to CSS selector for other formats
        table = soup.select_one(selector)
        if table is None:
            return None
        return str(table)


def extract_tables_by_selectors(html_content: str, selectors: list[str]) -> list[str]:
    """
    Extract multiple tables from HTML using CSS selectors.
    
    Returns a list of table HTML strings in the same order as selectors.
    Skips any tables that are not found.
    """
    tables = []
    for selector in selectors:
        table_html = extract_table_by_selector(html_content, selector)
        if table_html:
            tables.append(table_html)
    return tables
