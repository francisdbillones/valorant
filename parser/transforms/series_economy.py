import pandas as pd
from parser.utils import clean_int, parse_economy_tuple

def resolve_team_by_tag(tag, team1_name, team2_name, team1_id, team2_id, veto_tag_lookup):
    if not tag:
        return None
    tag_clean = tag.strip()
    
    # 1. Try veto_tag_lookup
    if veto_tag_lookup:
        resolved_id = veto_tag_lookup.get(tag_clean)
        if resolved_id in (team1_id, team2_id):
            return resolved_id
            
    # 2. Try matching tag to team names
    if team1_name and tag_clean.lower() in team1_name.lower():
        return team1_id
    if team2_name and tag_clean.lower() in team2_name.lower():
        return team2_id
        
    return None

def transform(matches, resolver=None):
    rows = []
    
    dtypes = {
        "match_id": "str",
        "team_id": "str",
        "team_tag": "str",
        "pistols_won": "Int8",
        "eco_rounds": "Int16",
        "eco_won": "Int16",
        "semi_eco_rounds": "Int16",
        "semi_eco_won": "Int16",
        "semi_buy_rounds": "Int16",
        "semi_buy_won": "Int16",
        "full_buy_rounds": "Int16",
        "full_buy_won": "Int16"
    }
    
    veto_tag_lookup = resolver.global_tag_lookup if resolver else None
    
    for m in matches:
        match_id = str(m.get("match_id")) if m.get("match_id") else None
        
        teams = m.get("teams") or []
        team1_id = str(teams[0].get("id")) if len(teams) >= 1 and teams[0].get("id") else None
        team1_name = teams[0].get("name") if len(teams) >= 1 else None
        team2_id = str(teams[1].get("id")) if len(teams) >= 2 and teams[1].get("id") else None
        team2_name = teams[1].get("name") if len(teams) >= 2 else None
        
        economy_list = m.get("economy") or []
        # Support economy being a dict with economy_by_map list (as in some structures) or direct list
        # Wait, the spec review said: "economy type: <class 'list'>; economy: [{'0': 'VIT', '1': '1', '2': '3 (1)', '3': '1 (0)', '4': '5 (2)', '5': '21 (13)'}, ...]"
        # So we expect it to be a list. If it is a dictionary, we should check for a 'by_map' or similar, but let's assume it is a list of dicts.
        if not isinstance(economy_list, list):
            continue
            
        for entry in economy_list:
            if not isinstance(entry, dict):
                continue
                
            tag = entry.get("0")
            team_id = resolve_team_by_tag(
                tag, team1_name, team2_name, team1_id, team2_id, veto_tag_lookup
            )
            
            pistols_won = clean_int(entry.get("1"))
            eco_rounds, eco_won = parse_economy_tuple(entry.get("2"))
            semi_eco_rounds, semi_eco_won = parse_economy_tuple(entry.get("3"))
            semi_buy_rounds, semi_buy_won = parse_economy_tuple(entry.get("4"))
            full_buy_rounds, full_buy_won = parse_economy_tuple(entry.get("5"))
            
            rows.append({
                "match_id": match_id,
                "team_id": team_id,
                "team_tag": tag,
                "pistols_won": pistols_won,
                "eco_rounds": eco_rounds,
                "eco_won": eco_won,
                "semi_eco_rounds": semi_eco_rounds,
                "semi_eco_won": semi_eco_won,
                "semi_buy_rounds": semi_buy_rounds,
                "semi_buy_won": semi_buy_won,
                "full_buy_rounds": full_buy_rounds,
                "full_buy_won": full_buy_won
            })
            
    if not rows:
        df = pd.DataFrame(columns=dtypes.keys())
    else:
        df = pd.DataFrame(rows)
        
    for col, dtype in dtypes.items():
        if col in df.columns:
            df[col] = df[col].astype(dtype)
            
    return df
