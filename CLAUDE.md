# CLAUDE.md — Valorant Pro Play Research Codebase

This file helps AI assistants understand the structure, purpose, and current state of this repository.

---

## Project Summary

**Goal**: Research project analysing professional Valorant match data scraped from VLR.gg.

**Research Question**: *What factors affect winrate across the different tiers of Valorant pro play (Tier 1 vs. Tier 2)?*

**Status**: Data collection ✅ → Parsing ✅ → EDA ✅ (in progress / being iterated)

**Data scale**: ~32,691 matches spanning Valorant Ep1 (2021) through Ep13 (2026), covering all major regions.

---

## Directory Structure

```
valorant/
├── CLAUDE.md                    ← You are here
├── vlrggapi/                    ← Third-party VLR.gg REST API wrapper (FastAPI)
├── scraper/                     ← Data collection scripts
├── parser/                      ← ETL: raw JSON → 9 normalized parquet tables
├── output/                      ← Generated data files (parquet + reports)
├── eda/                         ← Exploratory data analysis notebooks
└── plans/                       ← Planning documents (gitignored from remote)
```

> **Note**: `*.json` and `*.db` files are gitignored — the raw data files are large (1.4 GB JSON, 652 MB SQLite) and not in version control.

---

## Component 1: `vlrggapi/` — VLR.gg API

A self-hosted FastAPI wrapper around VLR.gg's website. Run this locally to serve match data.

- `main.py` — FastAPI app entrypoint (uvicorn)
- `worker.py` — Background scraping worker
- `routers/` — API route definitions
- `models/` — Pydantic data models
- `api/` — Core scraping logic

**Key endpoint used by the scraper**: `GET /v2/match/details?match_id={id}` — returns structured match data for a single VLR.gg match ID.

**How to run**: `uvicorn main:app --port 3001` (from `vlrggapi/`)

---

## Component 2: `scraper/` — Data Collection

Two-phase collection system for downloading all match details.

### Phase 1: Get match IDs → `all_recorded_games.json`
This was done separately (not in this repo). The file contains a list of match page URLs.

### Phase 2: Download match details

**`get_all_game_details.py`** — Standalone single-process downloader.
```bash
python scraper/get_all_game_details.py \
  --input scraper/all_recorded_games.json \
  --output scraper/all_match_details.json \
  --api http://127.0.0.1:3001/v2/match/details \
  --delay 0.5
```

**`coordinator.py`** — FastAPI coordinator for parallel/distributed scraping. Workers call `/get_chunk` to lease IDs and `/submit_chunk` to write results to SQLite. Supports crashed-worker recovery via lease timeouts.
- Stores data in `scraper/all_match_details.db` (SQLite)
- Export to JSON: `GET /export`

**`collect_failed.py`** — Re-scrapes matches that previously returned empty/error responses.

**`clean_failed_from_outputs.py`** — Removes failed/empty records from output files.

**Output**: `scraper/all_match_details.json` — 1.4 GB JSON list of raw match objects.

---

## Component 3: `parser/` — ETL Pipeline

Transforms the raw JSON into 9 normalized, typed Apache Parquet tables.

**Run**: `python -m parser.main` from the repo root.

### Pipeline steps (in `parser/main.py`):
1. **Load** — `loader.py` reads raw JSON, validates records, quarantines malformed ones
2. **VetoResolver** — two-pass system to map team abbreviation tags to team IDs across all matches (needed because veto strings use short tags like "SEN" not full team IDs)
3. **Transform** — 9 independent transform modules in `parser/transforms/`
4. **Write** — parquet files to `output/`
5. **QA** — `qa.py` runs integrity checks, writes `output/qa_report.md`
6. **Data Dictionary** — `data_dictionary.py` auto-generates `output/data_dictionary.md`

### Transform modules (`parser/transforms/`):
| File | Output Table | Notes |
|---|---|---|
| `matches.py` | `matches` | One row per match |
| `teams.py` | `teams` | Deduped team registry |
| `maps.py` | `maps` | One row per map per match, resolves pick/decider via VetoResolver |
| `map_player_stats.py` | `map_player_stats` | Per-player per-map stats |
| `map_rounds.py` | `map_rounds` | Per-round winner and side |
| `series_economy.py` | `series_economy` | Economy round counts per team per match |
| `series_advanced_stats.py` | `series_advanced_stats` | Multi-kills and clutch counts |
| `series_kill_matrix.py` | `series_kill_matrix` | Player-vs-player kill counts |
| `map_vetos.py` | `map_vetos` | Structured veto actions |

### VetoResolver (`parser/veto_resolver.py`):
The veto string format is e.g. `"SEN ban Haven; TL pick Bind; ..."`. Resolving the short tag ("SEN") to a team ID requires a corpus-level majority-vote lookup built in a first pass over all matches, then applied per-match. Tags with <90% majority are left unresolved (NULL).

---

## Component 4: `output/` — Generated Tables

All parquet files are auto-generated and should not be manually edited.

| File | Rows | Description |
|---|---|---|
| `matches.parquet` | 32,691 | One row per match. Primary key: `match_id`. |
| `teams.parquet` | 5,653 | Team registry. PK: `team_id`. |
| `maps.parquet` | 68,366 | One row per map per match. PK: `map_id`. |
| `map_player_stats.parquet` | 682,905 | Per-player per-map stats. |
| `map_rounds.parquet` | 1,395,133 | Per-round records. |
| `series_economy.parquet` | 41,644 | Economy stats (~63% match coverage). |
| `series_advanced_stats.parquet` | 209,312 | Multi-kill/clutch stats (~63% coverage). |
| `series_kill_matrix.parquet` | 520,550 | Player-vs-player kills (~63% coverage). |
| `map_vetos.parquet` | 94,146 | Structured veto actions. |
| `data_dictionary.md` | — | Auto-generated column documentation. |
| `qa_report.md` | — | Auto-generated data quality report. |
| `valorant.db` | — | SQLite mirror of parquet tables (for SQL queries). |

> **Coverage note**: `series_economy`, `series_advanced_stats`, and `series_kill_matrix` only cover ~63% of matches — the ones where VLR.gg had complete performance stats blocks. Always account for this when joining.

---

## Component 5: `eda/` — Exploratory Data Analysis

Jupyter notebooks and support files for the research analysis.

### Key files:
| File | Purpose |
|---|---|
| `tournament_labels.csv` | **Manually curated** tier/region/stage_type lookup for all 1,550 tournament series names. Primary join key for tier classification. |
| `generate_labels_csv.py` | Script that generates `tournament_labels.csv` with `auto:` prefilled values from keyword matching. Run once; user then edits. |
| `utils.py` | Shared helpers imported by all notebooks: `load_tables()`, `enrich_matches()`, `get_working_matches()`, `get_completed_maps()`, `savefig()`. |
| `figures/` | Auto-generated chart PNGs (23 files). |
| `analysis_results.md` | Written summary of all EDA findings. |

### Notebook sequence:
| Notebook | Focus |
|---|---|
| `00_validate_labels.ipynb` | Verify tier label coverage and sanity checks |
| `01_overview.ipynb` | Dataset baseline: volume, CT win rates, patch timeline |
| `02_map_analysis.ipynb` | Map pick rates, score margins, CT heatmap, OT rate |
| `03_player_performance.ipynb` | Stat-winrate correlations, FK advantage, agent meta, role ratings, clutches |
| `04_economy.ipynb` | Pistol impact, buy-type win rates, full-buy efficiency |
| `05_round_level.ipynb` | Halftime as predictor, deficit win probability, win streaks |
| `06_team_trajectory.ipynb` | T2→T1 win rate transfer scatter (R²=0.01) |

### Tier classification system:
Tournaments are classified in `tournament_labels.csv` with these values:
- `tier1` — VCT, Champions Tour, Masters, LOCK//IN, Esports World Cup, Ascension
- `tier2` — Challengers, Challengers League (all regions)
- `game_changers` — VCT Game Changers
- `tier3` — Regional third-tier leagues
- `collegiate` — Collegiate leagues
- (blank) — Excluded from analysis

> **Important**: Classification is manual, not regex-based. The CSV is the source of truth. `enrich_matches()` in `utils.py` joins it to the matches table on the `tournament` column (derived from `event_name` by stripping the `event_series` suffix).

### How to load data in any notebook:
```python
import sys; sys.path.insert(0, '..')
from eda.utils import load_tables, enrich_matches, get_working_matches, get_completed_maps

tables = load_tables()
matches = enrich_matches(tables['matches'])
working = get_working_matches(matches)       # final status, T1/T2/GC/T3/collegiate only
comp_maps = get_completed_maps(tables['maps'], working)  # completed maps with map_winner_id
```

---

## Plans & Documentation (`plans/`)

> ⚠️ Plans are gitignored from remote (`plans/*.md` in `.gitignore`).

| File | Purpose |
|---|---|
| `parser_spec.md` | Original spec for the parser |
| `parser_spec_review.md` | Review of the spec |
| `parser_implementation_plan.md` | Detailed implementation plan for the parser |
| `eda_plan.md` | High-level EDA plan (phases, decisions) |
| `eda_handoff.md` | **Full implementing-agent handoff** — complete code for EDA files |

---

## Key Data Facts & Gotchas

1. **Temporal confound**: 71% of T1 data is from Ep2–4 (2021–2022), while 88% of T2 data is from Ep6+ (2023–2026). Direct T1 vs T2 comparisons are confounded by era/meta differences. Always filter to overlapping patches for valid comparisons.

2. **`event_name` structure**: Contains both the tournament name and stage (e.g. `"Challengers 2026: SEA Split 2 Playoffs: Lower Final"`). The `event_series` column holds just the stage suffix (`"Playoffs: Lower Final"`). `extract_tournament_name()` in `utils.py` strips the suffix.

3. **`map_id` format**: `"{match_id}_{map_order}"` — deterministic, join-safe.

4. **Team1/Team2 is positional**: In `matches`, `team1_id`/`team2_id` are just the order VLR.gg listed them, not home/away. Team1 map win rate should be ~50% (confirmed in validation).

5. **VetoResolver NULLs**: Some maps have `picked_by_team_id = NULL` — the veto tag couldn't be resolved. `is_decider` is more reliable than `picked_by_team_id`.

6. **Match status**: Most matches are `final`. A handful are `forfeited by <team_name>`. `status == 'no_data'` means VLR.gg returned an empty response. Filter to `status == 'final'` for analysis.

7. **Economy/advanced stats coverage**: Only ~63% of matches have `series_economy`, `series_advanced_stats`, and `series_kill_matrix` data. These tables exist only for matches where VLR.gg displayed the full stats breakdown.

---

## How to Re-run the Parser

```bash
# From repo root, with vlrggapi not needed (parser reads the local JSON)
python -m parser.main
# Output: output/*.parquet, output/qa_report.md, output/data_dictionary.md
```

## Dependencies

```bash
pip install pandas pyarrow matplotlib seaborn scipy scikit-learn jupyter fastapi uvicorn httpx
```

Python version: 3.12 (see `vlrggapi/.python-version`).
