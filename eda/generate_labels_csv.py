"""
Run once to generate tournament_labels.csv for manual editing.
    python eda/generate_labels_csv.py
"""
import pandas as pd
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "output"
SCRAPED_PATH = Path(__file__).parent / "vlr_scraped_events.json"

# Load scraped events for ground truth classification
if SCRAPED_PATH.exists():
    with open(SCRAPED_PATH, 'r', encoding='utf-8') as f:
        scraped = json.load(f)
    VCT_EVENTS = set(scraped.get('vct_tier1', []))
    VCL_EVENTS = set(scraped.get('vcl_tier2', []))
else:
    VCT_EVENTS = set()
    VCL_EVENTS = set()

def extract_tournament_name(row):
    name = str(row.get('event_name', ''))
    series = str(row.get('event_series', ''))
    if series and name.endswith(series):
        return name[:-len(series)].rstrip(': ')
    return name.split(':')[0].strip()

def get_tier(name):
    n = name.lower()
    # Check ground truth lists first
    if name in VCT_EVENTS:
        return 'tier1'
    if name in VCL_EVENTS:
        # Ascension events are tier1 as per plan
        if 'champions tour' in n or 'vct' in n:
            return 'tier1'
        return 'tier2'
    
    # Fallbacks for events not in scraped lists
    if any(k in n for k in ['game changers', 'first strike']):
        return ''
    if any(k in n for k in ['vct ', 'champions tour', 'champions 20', 'masters',
                              'lock//in', 'esports world cup']):
        return 'auto:tier1'
    if 'challengers' in n:
        return 'auto:tier2'
    return ''  # blank = user must decide

def auto_region(name):
    n = name.lower()
    region_map = [
        ('north america', 'NA'), (' ace', 'NA'), ('nerd street', 'NA'),
        ('knights', 'NA'), ('boom', 'NA'),
        ('americas', 'Americas'),
        ('europe', 'EMEA'), ('emea', 'EMEA'), ('dach', 'EMEA'),
        ('france', 'EMEA'), ('spain', 'EMEA'), ('italy', 'EMEA'),
        ('portugal', 'EMEA'), ('turkey', 'EMEA'), ('türkiye', 'EMEA'),
        ('northern europe', 'EMEA'), ('polaris', 'EMEA'), ('mena', 'EMEA'),
        ('cis', 'CIS'),
        ('korea', 'Korea'), ('japan', 'Japan'),
        ('pacific', 'APAC'), ('asia-pacific', 'APAC'),
        ('hong kong', 'APAC'), ('taiwan', 'APAC'),
        ('southeast asia', 'SEA'), (' sea ', 'SEA'), ('indonesia', 'SEA'),
        ('philippines', 'SEA'), ('thailand', 'SEA'),
        ('malaysia', 'SEA'), ('singapore', 'SEA'), ('vietnam', 'SEA'),
        ('china', 'China'),
        ('brazil', 'Brazil'), ('latam', 'LATAM'),
        ('oceania', 'Oceania'),
        ('global', 'Global'), ('world', 'Global'), ('international', 'Global'),
    ]
    for kw, region in region_map:
        if kw in n:
            return f'auto:{region}'
    return ''

def auto_stage_type(name):
    n = name.lower()
    if 'last chance' in n or 'lcq' in n:
        return 'auto:lcq'
    if 'open qualifier' in n or 'open qual' in n:
        return 'auto:open_qualifier'
    if 'qualifier' in n or 'qualif' in n:
        return 'auto:qualifier'
    return 'auto:main_event'

def main():
    matches = pd.read_parquet(DATA_DIR / 'matches.parquet')
    matches['tournament'] = matches.apply(extract_tournament_name, axis=1)
    
    t_counts = (matches.groupby('tournament')
                .size()
                .sort_values(ascending=False)
                .reset_index(name='match_count'))
    
    t_counts['tier']       = t_counts['tournament'].apply(get_tier)
    t_counts['region']     = t_counts['tournament'].apply(auto_region)
    t_counts['stage_type'] = t_counts['tournament'].apply(auto_stage_type)
    t_counts['notes']      = ''
    
    out = Path(__file__).parent / 'tournament_labels.csv'
    t_counts.to_csv(out, index=False)
    print(f"Written {len(t_counts)} rows to {out}")
    print()
    print("Next steps:")
    print("  1. Open tournament_labels.csv in a spreadsheet app")
    print("  2. Rows sorted by match_count descending — label the top rows first")
    print("  3. Confirm auto: values (remove the 'auto:' prefix when confirmed)")
    print("  4. Fill in blank 'tier' for ambiguous rows, or leave blank to exclude")
    print("  5. Save and run 00_validate_labels.ipynb")

if __name__ == '__main__':
    main()
