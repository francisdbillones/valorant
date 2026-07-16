import pandas as pd
from parser.utils import clean_int, resolve_player_team

def transform(matches, resolver=None):
    rows = []
    
    dtypes = {
        "match_id": "str",
        "player_name": "str",
        "team_id": "str",
        "k2": "Int16",
        "k3": "Int16",
        "k4": "Int16",
        "k5": "Int16",
        "clutch_1v1": "Int16",
        "clutch_1v2": "Int16",
        "clutch_1v3": "Int16",
        "clutch_1v4": "Int16",
        "clutch_1v5": "Int16",
        "econ": "Int16",
        "pl": "Int16",
        "de": "Int16"
    }
    
    veto_tag_lookup = resolver.global_tag_lookup if resolver else None
    
    for m in matches:
        match_id = str(m.get("match_id")) if m.get("match_id") else None
        
        teams = m.get("teams") or []
        team1_id = str(teams[0].get("id")) if len(teams) >= 1 and teams[0].get("id") else None
        team1_name = teams[0].get("name") if len(teams) >= 1 else None
        team2_id = str(teams[1].get("id")) if len(teams) >= 2 and teams[1].get("id") else None
        team2_name = teams[1].get("name") if len(teams) >= 2 else None
        
        perf = m.get("performance") or {}
        adv_stats = perf.get("advanced_stats") or []
        
        for entry in adv_stats:
            player = entry.get("player")
            if not player:
                continue
                
            team_id = resolve_player_team(
                player, team1_name, team2_name, team1_id, team2_id, veto_tag_lookup
            )
            
            rows.append({
                "match_id": match_id,
                "player_name": player,
                "team_id": team_id,
                "k2": clean_int(entry.get("2")),
                "k3": clean_int(entry.get("3")),
                "k4": clean_int(entry.get("4")),
                "k5": clean_int(entry.get("5")),
                "clutch_1v1": clean_int(entry.get("6")),
                "clutch_1v2": clean_int(entry.get("7")),
                "clutch_1v3": clean_int(entry.get("8")),
                "clutch_1v4": clean_int(entry.get("9")),
                "clutch_1v5": clean_int(entry.get("10")),
                "econ": clean_int(entry.get("11")),
                "pl": clean_int(entry.get("12")),
                "de": clean_int(entry.get("13"))
            })
            
    if not rows:
        df = pd.DataFrame(columns=dtypes.keys())
    else:
        df = pd.DataFrame(rows)
        
    for col, dtype in dtypes.items():
        if col in df.columns:
            df[col] = df[col].astype(dtype)
            
    return df
