import pandas as pd
from parser.utils import clean_int, clean_float, clean_pct
from parser.transforms.maps import get_map_ids

def transform(matches):
    rows = []
    
    dtypes = {
        "match_id": "str",
        "map_id": "str",
        "team_id": "str",
        "player_name": "str",
        "agent": "str",
        "rating": "Float32",
        "acs": "Int16",
        "kills": "Int16",
        "deaths": "Int16",
        "assists": "Int16",
        "kd_diff": "Int16",
        "kast_pct": "Float32",
        "adr": "Float32",
        "hs_pct": "Float32",
        "fk": "Int16",
        "fd": "Int16",
        "fk_diff": "Int16"
    }
    
    for m in matches:
        match_id = str(m.get("match_id")) if m.get("match_id") else None
        maps_list = m.get("maps") or []
        map_ids = get_map_ids(m)
        
        teams = m.get("teams") or []
        team1_id = str(teams[0].get("id")) if len(teams) >= 1 and teams[0].get("id") else None
        team2_id = str(teams[1].get("id")) if len(teams) >= 2 and teams[1].get("id") else None
        
        for idx, map_entry in enumerate(maps_list):
            # Check map_name to filter out maps with no name
            map_name = map_entry.get("map_name")
            if not map_name:
                continue
                
            map_id = map_ids[idx]
            players_dict = map_entry.get("players") or {}
            
            for team_key, p_list in players_dict.items():
                p_team_id = team1_id if team_key == "team1" else (team2_id if team_key == "team2" else None)
                if not p_list:
                    continue
                    
                for p in p_list:
                    p_name = p.get("name")
                    if not p_name:
                        continue
                        
                    agent = p.get("agent")
                    
                    rows.append({
                        "match_id": match_id,
                        "map_id": map_id,
                        "team_id": p_team_id,
                        "player_name": p_name,
                        "agent": agent,
                        "rating": clean_float(p.get("rating")),
                        "acs": clean_int(p.get("acs")),
                        "kills": clean_int(p.get("kills")),
                        "deaths": clean_int(p.get("deaths")),
                        "assists": clean_int(p.get("assists")),
                        "kd_diff": clean_int(p.get("kd_diff")),
                        "kast_pct": clean_pct(p.get("kast")),
                        "adr": clean_float(p.get("adr")),
                        "hs_pct": clean_pct(p.get("hs_pct")),
                        "fk": clean_int(p.get("fk")),
                        "fd": clean_int(p.get("fd")),
                        "fk_diff": clean_int(p.get("fk_diff"))
                    })
                    
    if not rows:
        df = pd.DataFrame(columns=dtypes.keys())
    else:
        df = pd.DataFrame(rows)
        
    for col, dtype in dtypes.items():
        if col in df.columns:
            df[col] = df[col].astype(dtype)
            
    return df
