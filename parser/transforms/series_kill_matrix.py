import pandas as pd
from parser.utils import parse_packed_kd, resolve_player_team

def transform(matches, resolver=None):
    rows = []
    
    dtypes = {
        "match_id": "str",
        "player_name": "str",
        "player_team_id": "str",
        "opponent_name": "str",
        "opponent_team_id": "str",
        "kills": "Int16",
        "deaths": "Int16",
        "diff": "Int16"
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
        kill_matrix = perf.get("kill_matrix") or []
        
        if len(kill_matrix) < 2:
            continue
            
        header = kill_matrix[0]
        opponent_names = header.get("kills_vs") or {}
        
        for entry in kill_matrix[1:]:
            player = entry.get("player")
            if not player:
                continue
                
            kills_vs = entry.get("kills_vs") or {}
            
            for idx, packed in kills_vs.items():
                opponent = opponent_names.get(idx)
                if not opponent:
                    continue
                    
                kills, deaths, diff = parse_packed_kd(packed)
                
                player_team_id = resolve_player_team(
                    player, team1_name, team2_name, team1_id, team2_id, veto_tag_lookup
                )
                opponent_team_id = resolve_player_team(
                    opponent, team1_name, team2_name, team1_id, team2_id, veto_tag_lookup
                )
                
                rows.append({
                    "match_id": match_id,
                    "player_name": player,
                    "player_team_id": player_team_id,
                    "opponent_name": opponent,
                    "opponent_team_id": opponent_team_id,
                    "kills": kills,
                    "deaths": deaths,
                    "diff": diff
                })
                
    if not rows:
        df = pd.DataFrame(columns=dtypes.keys())
    else:
        df = pd.DataFrame(rows)
        
    for col, dtype in dtypes.items():
        if col in df.columns:
            df[col] = df[col].astype(dtype)
            
    return df
