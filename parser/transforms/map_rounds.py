import pandas as pd
from parser.utils import clean_int
from parser.transforms.maps import get_map_ids

def transform(matches):
    rows = []
    
    dtypes = {
        "match_id": "str",
        "map_id": "str",
        "round_num": "Int8",
        "winning_team_id": "str",
        "winning_side": "str"
    }
    
    for m in matches:
        match_id = str(m.get("match_id")) if m.get("match_id") else None
        maps_list = m.get("maps") or []
        map_ids = get_map_ids(m)
        
        teams = m.get("teams") or []
        team1_id = str(teams[0].get("id")) if len(teams) >= 1 and teams[0].get("id") else None
        team2_id = str(teams[1].get("id")) if len(teams) >= 2 and teams[1].get("id") else None
        
        for idx, map_entry in enumerate(maps_list):
            map_name = map_entry.get("map_name")
            if not map_name:
                continue
                
            map_id = map_ids[idx]
            rounds = map_entry.get("rounds") or []
            
            for r in rounds:
                winner_str = r.get("winner")
                # Exclude unplayed rounds
                if not winner_str or winner_str == "":
                    continue
                    
                winning_side = r.get("side")
                winning_side = winning_side.strip().lower() if winning_side else None
                
                round_num = clean_int(r.get("round_num"))
                
                winning_team_id = None
                if winner_str == "team1":
                    winning_team_id = team1_id
                elif winner_str == "team2":
                    winning_team_id = team2_id
                    
                rows.append({
                    "match_id": match_id,
                    "map_id": map_id,
                    "round_num": round_num,
                    "winning_team_id": winning_team_id,
                    "winning_side": winning_side
                })
                
    if not rows:
        df = pd.DataFrame(columns=dtypes.keys())
    else:
        df = pd.DataFrame(rows)
        
    for col, dtype in dtypes.items():
        if col in df.columns:
            df[col] = df[col].astype(dtype)
            
    return df
