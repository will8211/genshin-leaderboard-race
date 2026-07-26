# TO_DO

We currently have three invocation styles in one pipeline:

```sh
uv run extract-rankings ...
uv run python extract_rankings/html_to_json.py ...
uv run python -m generate_csv.cli ...
```

The clean endpoint would be four consistent console scripts:
```sh
uv run extract-rankings --all --force
uv run extract-rankings-json
uv run extract-rankings-json-names
uv run generate-rankings-csv
```

The exact pyproject.toml goal:

```toml
[project.scripts]
extract-rankings = "extract_rankings.cli:main"
extract-rankings-json = "extract_rankings.html_to_json:main"
extract-rankings-json-names = "..."
generate-rankings-csv = "generate_csv.cli:main"
```
