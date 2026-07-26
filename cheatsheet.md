# HTML → CSV Cheat Sheet

Run all commands from the repository root.

## 1. Extract relevant tables from cached HTML

Uses `selected_tables.yaml` and regenerates every configured version.

```bash
uv run extract-rankings --all --force
```

Output:

```text
data/extracted_rankings/relevant_tables/*.html
```

Optional compact result check:

```bash
uv run extract-rankings --all --force |
  jq '{
    extracted_count,
    skipped_count,
    failure_count,
    failures
  }'
```

## 2. Convert extracted HTML to archive-ID JSON

```bash
for f in data/extracted_rankings/relevant_tables/*.html; do
  uv run python extract_rankings/html_to_json.py \
    --version "$(basename "$f" .html)"
done
```

Output:

```text
data/extracted_rankings/json/*.json
```

Do not run Prettier. Let `html_to_json.py` use its normal `json.dumps(..., indent=2)` formatting.

## 3. Convert archive IDs to character names

```bash
uv run extract-rankings-json-names \
  --input-dir data/extracted_rankings/json \
  --output-dir data/extracted_rankings/json_names
```

Input:

```text
data/extracted_rankings/json/*.json
```

Output:

```text
data/extracted_rankings/json_names/*.json
```

A file named `{version}_mine.json` overrides `{version}.json` when generating CSVs.

## 4. Generate all role CSVs

```bash
uv run python -m generate_csv.cli \
  --repo-root . \
  --input-dir data/extracted_rankings/json_names \
  --template data/csv/template.csv \
  --output-dir data/csv
```

Expected outputs:

```text
data/csv/main_dps.csv
data/csv/sub_dps.csv
data/csv/support.csv
data/csv/exploration.csv
```

## Full Routine

```bash
# 1. Cached HTML → selected ranking tables
uv run extract-rankings --all --force

# 2. Selected ranking tables → archive-ID JSON
for f in data/extracted_rankings/relevant_tables/*.html; do
  uv run python extract_rankings/html_to_json.py \
    --version "$(basename "$f" .html)"
done

# 3. Archive-ID JSON → character-name JSON
uv run extract-rankings-json-names \
  --input-dir data/extracted_rankings/json \
  --output-dir data/extracted_rankings/json_names

# 4. Character-name JSON → role CSVs
uv run python -m generate_csv.cli \
  --repo-root . \
  --input-dir data/extracted_rankings/json_names \
  --template data/csv/template.csv \
  --output-dir data/csv
```

## Final Checks

```bash
git diff --stat

git diff -- data/extracted_rankings/relevant_tables
git diff -- data/extracted_rankings/json
git diff -- data/extracted_rankings/json_names
git diff -- data/csv
```

## Pipeline

```text
Cached archive HTML
    ↓ extract-rankings --all --force
Relevant table HTML
    ↓ html_to_json.py
Archive-ID JSON
    ↓ extract-rankings-json-names
Character-name JSON
    ↓ generate_csv.cli
Main DPS / Sub-DPS / Support / Exploration CSVs
```
