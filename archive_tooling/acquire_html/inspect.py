from __future__ import annotations

from html.parser import HTMLParser


class _StructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._current_heading_tag: str | None = None
        self._heading_buffer: list[str] = []
        self.headings: list[dict[str, str]] = []

        self._in_row_stack: list[bool] = []
        self._cell_count_stack: list[int] = []
        self._table_stack: list[dict[str, object]] = []
        self.tables: list[dict[str, object]] = []

        self._in_first_col_stack: list[bool] = []
        self._current_cell_alts_stack: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lower = tag.lower()
        if lower in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._current_heading_tag = lower
            self._heading_buffer = []
            return

        if lower == "table":
            last_heading = self._current_table_heading_name()
            self._table_stack.append({"name": last_heading, "rows": 0, "max_cols": 0, "first_col_alts": []})
            self._in_row_stack.append(False)
            self._cell_count_stack.append(0)
            self._in_first_col_stack.append(False)
            self._current_cell_alts_stack.append([])
            return

        if lower == "tr" and self._table_stack:
            self._in_row_stack[-1] = True
            self._cell_count_stack[-1] = 0
            return

        if lower in {"td", "th"} and self._table_stack and self._in_row_stack[-1]:
            if self._cell_count_stack[-1] == 0:
                self._in_first_col_stack[-1] = True
                self._current_cell_alts_stack[-1] = []
            self._cell_count_stack[-1] += 1
            return

        if lower == "img" and self._table_stack and self._in_first_col_stack[-1]:
            alt = dict(attrs).get("alt")
            if alt:
                self._current_cell_alts_stack[-1].append(alt)

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if self._current_heading_tag and lower == self._current_heading_tag:
            text = " ".join("".join(self._heading_buffer).split())
            if text:
                self.headings.append({"level": self._current_heading_tag, "text": text})
            self._current_heading_tag = None
            self._heading_buffer = []
            return

        if lower in {"td", "th"} and self._table_stack and self._in_first_col_stack[-1]:
            if self._current_cell_alts_stack[-1]:
                table = self._table_stack[-1]
                first_col_alts = table["first_col_alts"]
                assert isinstance(first_col_alts, list)
                first_col_alts.append(list(self._current_cell_alts_stack[-1]))
            self._in_first_col_stack[-1] = False
            return

        if lower == "tr" and self._table_stack and self._in_row_stack[-1]:
            table = self._table_stack[-1]
            table["rows"] = int(table["rows"]) + 1
            table["max_cols"] = max(int(table["max_cols"]), self._cell_count_stack[-1])
            self._in_row_stack[-1] = False
            return

        if lower == "table" and self._table_stack:
            table = self._table_stack.pop()
            self._in_row_stack.pop()
            self._cell_count_stack.pop()
            self._in_first_col_stack.pop()
            self._current_cell_alts_stack.pop()
            self.tables.append(table)

    def handle_data(self, data: str) -> None:
        if self._current_heading_tag:
            self._heading_buffer.append(data)

    def _current_table_heading_name(self) -> str | None:
        if not self.headings:
            return None

        current_heading = self.headings[-1]
        current_level = _heading_level(current_heading["level"])
        if current_level is None or len(self.headings) < 2:
            return current_heading["text"]

        previous_heading = self.headings[-2]
        previous_level = _heading_level(previous_heading["level"])
        if previous_level == current_level - 1:
            return f"{previous_heading['text']} > {current_heading['text']}"

        return current_heading["text"]


def _heading_level(level_tag: str) -> int | None:
    if len(level_tag) == 2 and level_tag.startswith("h") and level_tag[1].isdigit():
        return int(level_tag[1])
    return None


def summarize_html_structure(html_text: str) -> dict[str, object]:
    parser = _StructureParser()
    parser.feed(html_text)
    return {
        "heading_count": len(parser.headings),
        "headings": parser.headings,
        "table_count": len(parser.tables),
        "tables": [
            {
                "index": idx,
                "name": table["name"],
                "rows": table["rows"],
                "max_cols": table["max_cols"],
                "first_col_alts": table["first_col_alts"],
                "selector": f"table:nth-of-type({idx + 1})",
            }
            for idx, table in enumerate(parser.tables)
        ],
    }


def select_tables_with_first_col_alt_substring(
    summary: dict[str, object],
    substring: str,
) -> list[dict[str, object]]:
    return select_tables_with_first_col_alt_substrings(summary, [substring])


def select_tables_with_first_col_alt_substrings(
    summary: dict[str, object],
    substrings: list[str],
) -> list[dict[str, object]]:
    tables = summary.get("tables", [])
    if not isinstance(tables, list):
        return []

    needles = [needle for needle in substrings if needle]
    if not needles:
        return []

    matching_tables: list[dict[str, object]] = []
    for table in tables:
        if not isinstance(table, dict):
            continue
        first_col_alts = table.get("first_col_alts", [])
        if not isinstance(first_col_alts, list):
            continue

        if any(
            isinstance(row_alts, list)
            and any(
                isinstance(alt, str) and any(needle in alt for needle in needles)
                for alt in row_alts
            )
            for row_alts in first_col_alts
        ):
            matching_tables.append(table)

    return matching_tables


def diff_structures(
    left_version: str,
    right_version: str,
    left_summary: dict[str, object],
    right_summary: dict[str, object],
) -> dict[str, object]:
    left_tables = left_summary.get("tables", [])
    right_tables = right_summary.get("tables", [])

    max_len = max(len(left_tables), len(right_tables))
    changed: list[dict[str, object]] = []
    for idx in range(max_len):
        left_table = left_tables[idx] if idx < len(left_tables) else None
        right_table = right_tables[idx] if idx < len(right_tables) else None
        if left_table != right_table:
            changed.append(
                {
                    "index": idx,
                    "left": left_table,
                    "right": right_table,
                }
            )

    left_first = (left_summary.get("headings", []) or [None])[0]
    right_first = (right_summary.get("headings", []) or [None])[0]
    return {
        "left_version": left_version,
        "right_version": right_version,
        "left_heading_count": left_summary.get("heading_count", 0),
        "right_heading_count": right_summary.get("heading_count", 0),
        "left_table_count": left_summary.get("table_count", 0),
        "right_table_count": right_summary.get("table_count", 0),
        "first_heading_changed": left_first != right_first,
        "table_shape_changes": changed,
    }
