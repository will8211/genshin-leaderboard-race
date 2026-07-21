import argparse
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
    path = urlparse(href).path.rstrip("/")

    if not path:
        return None

    source_key = path.rsplit("/", maxsplit=1)[-1]
    return source_key or None


def extract_rank(th: Tag) -> str | None:
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
            source_keys = [
                source_key
                for link in cell.find_all("a", href=True)
                if (
                    source_key := extract_source_key(link["href"])
                ) is not None
            ]

            rankings[role][rank] = source_keys

    return {
        version_id: rankings,
    }


def convert_file(
    input_path: Path,
    output_path: Path,
) -> Path:
    html = input_path.read_text(encoding="utf-8")
    data = extract_rankings(html)

    output_path.parent.mkdir(parents=True, exist_ok=True)

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
    parser = argparse.ArgumentParser(
        description="Convert an extracted rankings HTML file to JSON."
    )

    parser.add_argument(
        "--verision",
        required=True,
        help="Genshin version ID, for example 1.2B.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    version = args.verision

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