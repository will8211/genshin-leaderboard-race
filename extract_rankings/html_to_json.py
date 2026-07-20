import json
import re
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag


ROLE_NAME_MAP = {
    "DPS": "Main DPS",
    "Main DPS": "Main DPS",
    "Sub DPS": "Sub-DPS",
    "Sub-DPS": "Sub-DPS",
    "Support": "Support",
}


def extract_source_key(href: str) -> str | None:
    """
    Extract the final path segment from a Game8 URL.

    The source key is treated as an opaque string. It may be numeric or textual.

    Examples:
        https://game8.co/games/Genshin-Impact/archives/297518
        -> "297518"

        https://game8.co/games/Genshin-Impact/archives/Furina-Best-Builds
        -> "Furina-Best-Builds"
    """
    path = urlparse(href).path.rstrip("/")

    if not path:
        return None

    source_key = path.rsplit("/", maxsplit=1)[-1]
    return source_key or None


def extract_rank(th: Tag) -> str | None:
    """
    Extract a rank such as SS, S, A, B, C, or D from a row header.

    Handles labels such as:
        "Genshin - SS Rank Icon"
        "S Rank Icon"
        "SS Tier"
        "D Tier"
    """
    image = th.find("img")

    candidates = [
        th.get_text(" ", strip=True),
        image.get("alt", "") if image else "",
        image.get("title", "") if image else "",
    ]

    for candidate in candidates:
        match = re.search(
            r"\b(SS|S|A|B|C|D|E|F)\b",
            candidate,
            re.IGNORECASE,
        )

        if match:
            return match.group(1).upper()

    return None


def extract_version_id(soup: BeautifulSoup) -> str:
    """
    Extract the version ID from a title such as:
        "1.2A Rankings"
        "6.7A Rankings"
    """
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
    """
    Normalize role names across historical table formats.
    """
    normalized = " ".join(name.split())
    return ROLE_NAME_MAP.get(normalized, normalized)


def extract_rankings(
    html: str,
) -> dict[str, dict[str, dict[str, list[str]]]]:
    soup = BeautifulSoup(html, "html.parser")
    version_id = extract_version_id(soup)

    table = soup.find("table")
    if table is None:
        raise ValueError("No rankings table found")

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

    rankings: dict[str, dict[str, list[str]]] = {
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
            source_keys: list[str] = []

            for link in cell.find_all("a", href=True):
                source_key = extract_source_key(link["href"])

                if source_key is not None:
                    source_keys.append(source_key)

            rankings[role][rank] = source_keys

    return {
        version_id: rankings,
    }


def convert_file(
    input_path: Path,
    output_path: Path | None = None,
) -> Path:
    """
    Convert one extracted rankings HTML file to JSON.

    If no output path is supplied, the JSON file is written beside the HTML
    file using the same filename stem.
    """
    html = input_path.read_text(encoding="utf-8")
    data = extract_rankings(html)

    if output_path is None:
        output_path = input_path.with_suffix(".json")

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


if __name__ == "__main__":
    input_path = Path("1.2A.html")
    output_path = convert_file(input_path)

    print(f"Wrote {output_path}")