"""
Shared utilities for all EDA notebooks.
Import with: import sys; sys.path.insert(0, '..'); from eda.utils import *
Or from within eda/: from utils import *
"""
import pandas as pd
from pathlib import Path

# Paths
EDA_DIR  = Path(__file__).parent
DATA_DIR = EDA_DIR.parent / "output"
FIG_DIR  = EDA_DIR / "figures"
FIG_DIR.mkdir(exist_ok=True)

# ── Data loading ──────────────────────────────────────────────────────────────

def load_tables() -> dict[str, pd.DataFrame]:
    """Load all 9 parquet tables from output/."""
    names = [
        'matches', 'teams', 'maps', 'map_player_stats', 'map_rounds',
        'series_economy', 'series_advanced_stats', 'series_kill_matrix', 'map_vetos'
    ]
    return {n: pd.read_parquet(DATA_DIR / f"{n}.parquet") for n in names}

# ── Tournament name extraction ─────────────────────────────────────────────────

def extract_tournament_name(row: pd.Series) -> str:
    """Extract the tournament series name from event_name by stripping event_series."""
    name = str(row.get('event_name', ''))
    series = str(row.get('event_series', ''))
    if series and name.endswith(series):
        return name[:-len(series)].rstrip(': ')
    return name.split(':')[0].strip()

# ── Label loading ──────────────────────────────────────────────────────────────

def load_tournament_labels() -> pd.DataFrame:
    """Load the user-edited tournament_labels.csv."""
    path = EDA_DIR / "tournament_labels.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"tournament_labels.csv not found at {path}.\n"
            "Run: python eda/generate_labels_csv.py"
        )
    labels = pd.read_csv(path, dtype=str)
    # Strip 'auto:' prefix from any unconfirmed rows
    for col in ['tier', 'region', 'stage_type']:
        if col in labels.columns:
            labels[col] = (labels[col]
                           .fillna('')
                           .str.removeprefix('auto:')
                           .str.strip()
                           .replace('', None))
    return labels

# ── Match enrichment ───────────────────────────────────────────────────────────

def enrich_matches(matches: pd.DataFrame) -> pd.DataFrame:
    """
    Add tournament, tier, region, stage_type columns to matches table.
    Rows without a tier label get tier=NaN (excluded from working dataset).
    """
    m = matches.copy()
    m['tournament'] = m.apply(extract_tournament_name, axis=1)
    labels = load_tournament_labels()
    return m.merge(
        labels[['tournament', 'tier', 'region', 'stage_type']],
        on='tournament',
        how='left'
    )

def get_working_matches(matches: pd.DataFrame) -> pd.DataFrame:
    """Return final T1/T2/GC matches only."""
    return matches[
        (matches['status'] == 'final') &
        (matches['tier'].isin(['tier1', 'tier2', 'game_changers']))
    ].copy()

# ── Map helpers ────────────────────────────────────────────────────────────────

def get_completed_maps(maps: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    """
    Return completed maps joined with tier, region, team IDs, and map winner.

    Adds columns:
      - tier, region (from matches)
      - map_winner_id: team_id of the team that won this map
      - team1_id, team2_id (from matches)
    """
    m = maps.merge(
        matches[['match_id', 'tier', 'region', 'team1_id', 'team2_id']],
        on='match_id',
        how='inner'
    )
    m = m[m['map_status'] == 'completed'].copy()
    m['map_winner_id'] = m.apply(
        lambda r: r['team1_id']
                  if (pd.notna(r['team1_score']) and
                      pd.notna(r['team2_score']) and
                      int(r['team1_score']) > int(r['team2_score']))
                  else r['team2_id'],
        axis=1
    )
    return m

def add_won_column(df: pd.DataFrame, comp_maps: pd.DataFrame) -> pd.DataFrame:
    """
    For a table with (map_id, team_id), add a binary 'won' column.
    comp_maps must have map_id and map_winner_id.
    """
    winner_map = comp_maps.set_index('map_id')['map_winner_id']
    df = df.copy()
    df['won'] = (df['team_id'] == df['map_id'].map(winner_map)).astype(int)
    return df

# ── Figure helpers ─────────────────────────────────────────────────────────────

def savefig(fig, name: str):
    """Save a matplotlib figure to eda/figures/<name>.png."""
    path = FIG_DIR / f"{name}.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    print(f"Saved → {path}")

# ── Sanity checks ──────────────────────────────────────────────────────────────

def assert_no_row_explosion(df_before: pd.DataFrame, df_after: pd.DataFrame,
                             label: str = "merge"):
    n_before, n_after = len(df_before), len(df_after)
    if n_after != n_before:
        print(f"WARNING [{label}]: row count changed {n_before} → {n_after} "
              f"(diff={n_after - n_before:+d})")
    else:
        print(f"OK [{label}]: {n_after:,} rows")
