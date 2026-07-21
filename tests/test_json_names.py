import json

from extract_rankings.json_names import convert_json_directory


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_convert_json_directory_replaces_ids_with_character_keys(tmp_path):
    characters = {
        "Diluc": {"game8id": "297518"},
        "Klee": {"game8id": "297521"},
        "Bennett": {"game8id": "Bennett-Best-Builds"},
    }
    payload = {
        "1.0B": {
            "Main DPS": {
                "SS": ["297518", "297521"],
                "S": ["Bennett-Best-Builds"],
            }
        }
    }

    characters_path = tmp_path / "characters.json"
    input_dir = tmp_path / "json"
    output_dir = tmp_path / "json_names"

    _write_json(characters_path, characters)
    _write_json(input_dir / "1.0B.json", payload)

    total, converted_count, failures = convert_json_directory(
        input_dir=input_dir,
        output_dir=output_dir,
        characters_path=characters_path,
    )

    assert total == 1
    assert converted_count == 1
    assert failures == []

    converted = json.loads((output_dir / "1.0B.json").read_text(encoding="utf-8"))
    assert converted["1.0B"]["Main DPS"]["SS"] == ["Diluc", "Klee"]
    assert converted["1.0B"]["Main DPS"]["S"] == ["Bennett"]


def test_convert_json_directory_fails_file_when_unmapped_ids_exist(tmp_path):
    characters = {
        "Diluc": {"game8id": "297518"},
    }
    payload = {
        "1.0B": {
            "Main DPS": {
                "SS": ["297518", "999999"],
            }
        }
    }

    characters_path = tmp_path / "characters.json"
    input_dir = tmp_path / "json"
    output_dir = tmp_path / "json_names"

    _write_json(characters_path, characters)
    _write_json(input_dir / "1.0B.json", payload)

    total, converted_count, failures = convert_json_directory(
        input_dir=input_dir,
        output_dir=output_dir,
        characters_path=characters_path,
    )

    assert total == 1
    assert converted_count == 0
    assert len(failures) == 1
    assert failures[0].file == "1.0B.json"
    assert failures[0].version_id == "1.0B"
    assert failures[0].unmapped_ids == ["999999"]
    assert not (output_dir / "1.0B.json").exists()


def test_convert_json_directory_supports_legacy_tokens(tmp_path):
    characters = {
        "Lisa": {"game8id": "Lisa-Best-Builds"},
        "Venti": {"game8id": "Venti-Best-Builds"},
        "Nahida": {"game8id": "Nahida-Best-Builds"},
        "Gaming": {"game8id": "437446"},
    }
    payload = {
        "3.2A": {
            "Main DPS": {
                "S": ["297520", "Gaming-Best-Builds"],
                "A": ["383713", "297515", "999999"],
            }
        }
    }

    characters_path = tmp_path / "characters.json"
    input_dir = tmp_path / "json"
    output_dir = tmp_path / "json_names"

    _write_json(characters_path, characters)
    _write_json(input_dir / "3.2A.json", payload)

    total, converted_count, failures = convert_json_directory(
        input_dir=input_dir,
        output_dir=output_dir,
        characters_path=characters_path,
    )

    assert total == 1
    assert converted_count == 0
    assert len(failures) == 1
    assert failures[0].unmapped_ids == ["999999"]

    payload["3.2A"]["Main DPS"]["A"] = ["383713", "297515"]
    _write_json(input_dir / "3.2A.json", payload)

    total, converted_count, failures = convert_json_directory(
        input_dir=input_dir,
        output_dir=output_dir,
        characters_path=characters_path,
    )

    assert total == 1
    assert converted_count == 1
    assert failures == []

    converted = json.loads((output_dir / "3.2A.json").read_text(encoding="utf-8"))
    assert converted["3.2A"]["Main DPS"]["S"] == ["Venti", "Gaming"]
    assert converted["3.2A"]["Main DPS"]["A"] == ["Nahida", "Lisa"]
