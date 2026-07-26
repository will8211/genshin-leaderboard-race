"""Convert extracted ranking-table HTML files to JSON."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Comment, Tag


ROLE_NAME_MAP = {
    "DPS": "Main DPS",
    "Main DPS": "Main DPS",
    "Sub DPS": "Sub-DPS",
    "Sub-DPS": "Sub-DPS",
    "Support": "Support",
    "Exploration": "Exploration",
}


RankingsByRole = dict[str, dict[str, list[str]]]
VersionRankings = dict[str, RankingsByRole]


def extract_source_key(href: str) -> str | None:
    """Extract the final path component from a Game8 URL."""
    path = urlparse(href).path.rstrip("/")

    if not path:
        return None

    source_key = path.rsplit("/", maxsplit=1)[-1]
    return source_key or None


def extract_source_keys(cell: Tag) -> list[str]:
    """Extract character source keys from all links in a table cell."""
    return [
        source_key
        for link in cell.find_all("a", href=True)
        if (
            source_key := extract_source_key(str(link["href"]))
        ) is not None
    ]


def extract_rank(cell: Tag) -> str | None:
    """Extract a tier rank such as SS, S, A, B, or C from a cell."""
    image = cell.find("img")

    candidates = [
        cell.get_text(" ", strip=True),
        str(image.get("alt", "")) if image else "",
        str(image.get("title", "")) if image else "",
    ]

    for candidate in candidates:
        match = re.search(
            r"\b(SSS|SS|S|A|B|C|D|E|F)\b",
            candidate,
            re.IGNORECASE,
        )

        if match:
            return match.group(1).upper()

    return None


def extract_version_id(soup: BeautifulSoup) -> str:
    """Extract the version ID from an HTML title such as '1.2A Rankings'."""
    title = soup.title.get_text(" ", strip=True) if soup.title else ""

    match = re.match(
        r"(.+?)\s+Rankings$",
        title,
        re.IGNORECASE,
    )

    if not match:
        raise ValueError(
            f"Could not extract version ID from title: {title!r}"
        )

    return match.group(1).strip()


def normalize_role_name(name: str) -> str:
    """Normalize whitespace and known role-name variants."""
    normalized = " ".join(name.split())
    return ROLE_NAME_MAP.get(normalized, normalized)


def extract_table_label(table: Tag) -> str | None:
    """
    Read the HTML comment immediately preceding a table.

    Whitespace text nodes between the comment and table are ignored. A previous
    HTML element stops the search so that an unrelated earlier comment is not
    accidentally used.
    """
    node = table.previous_sibling

    while node is not None:
        if isinstance(node, Comment):
            label = node.strip()
            return label or None

        if isinstance(node, Tag):
            return None

        node = node.previous_sibling

    return None


def table_starts_with_rank_row(table: Tag) -> bool:
    """
    Determine whether the first row is ranking data rather than a role header.

    Separate role tables begin immediately with a rank such as SS. Combined
    tables begin with a header row containing role names.
    """
    first_row = table.find("tr", recursive=False)

    if first_row is None:
        return False

    first_cell = first_row.find(
        ["th", "td"],
        recursive=False,
    )

    if first_cell is None:
        return False

    return extract_rank(first_cell) is not None


def extract_single_role_table(
    table: Tag,
    role_name: str,
) -> RankingsByRole:
    """
    Extract a table representing one role.

    Expected shape:

        rank | characters
    """
    normalized_role = normalize_role_name(role_name)
    rankings: dict[str, list[str]] = {}

    for row in table.find_all("tr", recursive=False):
        cells = row.find_all(
            ["th", "td"],
            recursive=False,
        )

        if len(cells) < 2:
            continue

        rank = extract_rank(cells[0])

        if rank is None:
            continue

        rankings[rank] = extract_source_keys(cells[1])

    if not rankings:
        raise ValueError(
            f"No ranking rows found for role {normalized_role!r}"
        )

    return {
        normalized_role: rankings,
    }


def extract_combined_role_table(table: Tag) -> RankingsByRole:
    """
    Extract a table whose columns represent multiple roles.

    Expected shape:

        rank | Main DPS | Sub-DPS | Support
    """
    rows = table.find_all("tr", recursive=False)

    if not rows:
        raise ValueError("Rankings table is empty")

    header_cells = rows[0].find_all(
        ["th", "td"],
        recursive=False,
    )

    role_names = [
        normalize_role_name(cell.get_text(" ", strip=True))
        for cell in header_cells[1:]
    ]

    role_names = [
        role
        for role in role_names
        if role
    ]

    if not role_names:
        raise ValueError("No role columns found")

    rankings: RankingsByRole = {
        role: {}
        for role in role_names
    }

    for row in rows[1:]:
        cells = row.find_all(
            ["th", "td"],
            recursive=False,
        )

        if len(cells) < 2:
            continue

        rank = extract_rank(cells[0])

        if rank is None:
            continue

        for role, cell in zip(
            role_names,
            cells[1:],
            strict=False,
        ):
            rankings[role][rank] = extract_source_keys(cell)

    return rankings


def merge_rankings(
    destination: RankingsByRole,
    incoming: RankingsByRole,
) -> None:
    """Merge parsed role rankings without silently replacing duplicate roles."""
    duplicate_roles = destination.keys() & incoming.keys()

    if duplicate_roles:
        formatted_roles = ", ".join(sorted(duplicate_roles))
        raise ValueError(
            f"Duplicate ranking roles found: {formatted_roles}"
        )

    destination.update(incoming)


def extract_rankings(html: str) -> VersionRankings:
    """
    Extract rankings from all tables in an HTML document.

    Two table layouts are supported:

    1. Separate role tables identified by preceding HTML comments:
       <!-- Main DPS -->
       <!-- Support -->
       <!-- Exploration -->

    2. A combined table whose first row contains role names.
    """
    soup = BeautifulSoup(html, "html.parser")
    version_id = extract_version_id(soup)

    tables = soup.find_all("table")

    if not tables:
        raise ValueError("No rankings tables found")

    rankings: RankingsByRole = {}

    for table in tables:
        if not isinstance(table, Tag):
            continue

        if table_starts_with_rank_row(table):
            label = extract_table_label(table)

            if label is None:
                raise ValueError(
                    "Single-role rankings table has no preceding label comment"
                )

            parsed_rankings = extract_single_role_table(
                table,
                label,
            )
        else:
            parsed_rankings = extract_combined_role_table(table)

        merge_rankings(
            rankings,
            parsed_rankings,
        )

    if not rankings:
        raise ValueError("No ranking data found")

    return {
        version_id: rankings,
    }


def convert_file(
    input_path: Path,
    output_path: Path,
) -> Path:
    """Convert one extracted HTML file to JSON."""
    html = input_path.read_text(encoding="utf-8")
    data = extract_rankings(html)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    return output_path


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert an extracted rankings HTML file to JSON."
    )

    parser.add_argument(
        "--version",
        required=True,
        help="Genshin version ID, for example 1.2B.",
    )

    return parser.parse_args()


def main() -> int:
    """Run the HTML-to-JSON conversion."""
    args = parse_args()
    version = args.version

    input_path = Path(
        f"data/extracted_rankings/relevant_tables/{version}.html"
    )
    output_path = Path(
        f"data/extracted_rankings/json/{version}.json"
    )

    written_path = convert_file(
        input_path=input_path,
        output_path=output_path,
    )

    print(f"Wrote {written_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())