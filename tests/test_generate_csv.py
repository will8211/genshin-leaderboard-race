import csv
import json

from generate_csv.cli import (
    build_role_version_ranks,
    flatten_tiers_to_ranks,
    load_template,
    write_role_csvs,
)


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_template(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "Character,Images,1.0A,1.0B,1.1A,1.1B\n"
        "Diluc,https://example.com/diluc.png,,,,\n"
        "Klee,https://example.com/klee.png,,,,\n"
        "Venti,https://example.com/venti.png,,,,\n",
        encoding="utf-8",
    )


def _read_csv_rows(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_generate_role_csvs_prefers_mine_and_carries_forward(tmp_path):
    input_dir = tmp_path / "json_names"
    template_path = tmp_path / "template.csv"
    output_dir = tmp_path / "out"

    _write_template(template_path)

    _write_json(
        input_dir / "1.0B.json",
        {
            "1.0B": {
                "Main DPS": {"SS": ["Diluc", "Klee"]},
                "Sub-DPS": {"SS": ["Diluc", "Venti"]},
                "Support": {"SS": ["Venti", "Klee"]},
            }
        },
    )
    _write_json(
        input_dir / "1.0B_mine.json",
        {
            "1.0B": {
                "Main DPS": {"SS": ["Klee", "Diluc"]},
                "Sub-DPS": {"SS": ["Venti"], "S": ["Diluc"]},
                "Support": {"SS": ["Klee"], "A": ["Venti"]},
            }
        },
    )
    _write_json(
        input_dir / "1.1B.json",
        {
            "1.1B": {
                "Main DPS": {"SS": ["Diluc"], "S": ["Klee"]},
                "Sub-DPS": {"SS": ["Diluc"], "A": ["Venti"]},
                "Support": {"SS": ["Diluc"]},
            }
        },
    )

    fieldnames, template_rows, versions = load_template(template_path)
    role_version_ranks, role_stats = build_role_version_ranks(
        versions=versions,
        input_dir=input_dir,
    )
    written = write_role_csvs(
        fieldnames=fieldnames,
        template_rows=template_rows,
        versions=versions,
        role_version_ranks=role_version_ranks,
        output_dir=output_dir,
    )

    assert {p.name for p in written} == {"main_dps.csv", "sub_dps.csv", "support.csv"}

    main_rows = {row["Character"]: row for row in _read_csv_rows(output_dir / "main_dps.csv")}
    assert main_rows["Diluc"]["1.0A"] == ""
    assert main_rows["Diluc"]["1.0B"] == "2"
    assert main_rows["Diluc"]["1.1A"] == "2"
    assert main_rows["Diluc"]["1.1B"] == "1"
    assert main_rows["Klee"]["1.0B"] == "1"

    sub_rows = {row["Character"]: row for row in _read_csv_rows(output_dir / "sub_dps.csv")}
    assert sub_rows["Venti"]["1.0B"] == "1"
    assert sub_rows["Venti"]["1.1A"] == "1"
    assert sub_rows["Venti"]["1.1B"] == "2"

    support_rows = {row["Character"]: row for row in _read_csv_rows(output_dir / "support.csv")}
    assert support_rows["Klee"]["1.0B"] == "1"
    assert support_rows["Venti"]["1.0B"] == "2"
    assert support_rows["Klee"]["1.1B"] == ""

    assert role_stats["Main DPS"] == {"direct": 2, "carry_forward": 1, "blank": 1}


def test_flatten_tiers_to_ranks_uses_ss_to_c_then_extra_tiers():
    tiers = {
        "A": ["A1"],
        "SS": ["S1", "S2"],
        "C": ["C1"],
        "Z": ["Z1"],
    }

    ranks = flatten_tiers_to_ranks(tiers)

    assert ranks == {
        "S1": "1",
        "S2": "2",
        "A1": "3",
        "C1": "4",
        "Z1": "5",
    }


def test_flatten_tiers_to_ranks_places_sss_above_ss():
    tiers = {
        "SS": ["SS1"],
        "SSS": ["SSS1", "SSS2"],
        "S": ["S1"],
    }

    ranks = flatten_tiers_to_ranks(tiers)

    assert ranks == {
        "SSS1": "1",
        "SSS2": "2",
        "SS1": "3",
        "S1": "4",
    }
