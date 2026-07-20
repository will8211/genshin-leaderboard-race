"""Table extraction and HTML generation."""

from __future__ import annotations

from pathlib import Path

import yaml
from bs4 import BeautifulSoup

from archive_tooling.acquire_html.cache import cache_paths
from extract_rankings.parser import extract_tables_by_selectors, load_html_from_cache


def load_table_selectors(yaml_path: Path) -> dict[str, dict[str, str | None]]:
    """
    Load table selectors from selected_tables.yaml.
    
    Returns a dict mapping version_id to a dict of table type -> selector.
    Example: {"1.0B": {"dps": "table:nth-of-type(11)", "sup": "table:nth-of-type(13)"}}
    """
    with yaml_path.open("r", encoding="utf-8") as f:
        raw_config = yaml.safe_load(f)
    
    # Transform the YAML structure from list of dicts to flat dict
    result = {}
    for version_id, entries in raw_config.items():
        if not entries or len(entries) == 0:
            result[version_id] = {}
            continue
        # Take the first item in the list (each version has one entry)
        result[version_id] = entries[0]
    
    return result


def generate_output_html(tables: list[str], version_id: str) -> str:
    """
    Generate a minimal HTML document containing the extracted tables.
    
    Each table is preserved with all its original HTML, attributes, and styling.
    """
    if not tables:
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{version_id} - No Data</title>
</head>
<body>
    <p>No ranking data available for this version.</p>
</body>
</html>
"""
    
    tables_html = "\n".join(tables)
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{version_id} Rankings</title>
</head>
<body>
{tables_html}
</body>
</html>
"""


def extract_tables_for_version(
    version_id: str,
    timestamp: str,
    table_config: dict[str, str | None],
    cache_root: Path,
) -> str:
    """
    Extract tables for a single version and generate output HTML.
    
    Args:
        version_id: Version identifier (e.g., "1.0B")
        timestamp: Timestamp string for the cached HTML file
        table_config: Dict mapping table type to CSS selector
        cache_root: Root directory of HTML cache
    
    Returns:
        Complete HTML document as a string
    """
    # Filter out null selectors and collect valid ones
    selectors = [
        selector
        for selector in table_config.values()
        if selector is not None
    ]
    
    if not selectors:
        # All selectors are null, generate no-data output without loading HTML
        return generate_output_html([], version_id)
    
    # Now we know we have valid selectors, load the cached HTML
    html_path, _meta_path = cache_paths(cache_root, version_id, timestamp)
    
    if not html_path.exists():
        raise FileNotFoundError(f"Cached HTML not found: {html_path}")
    
    html_content = load_html_from_cache(html_path)
    tables = extract_tables_by_selectors(html_content, selectors)
    
    return generate_output_html(tables, version_id)


def write_output_file(output_path: Path, content: str) -> None:
    """Write HTML content to output file, creating directories as needed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prettify the HTML for better readability
    soup = BeautifulSoup(content, "html.parser")
    formatted_content = soup.prettify()
    
    output_path.write_text(formatted_content, encoding="utf-8")
