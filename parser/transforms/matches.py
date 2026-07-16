import pandas as pd
from parser.utils import parse_patch, clean_int

def transform(matches):
    rows = []
    
    dtypes = {
        "match_id": "str",
        "event_name": "str",
        "event_series": "str",
        "event_logo_url": "str",
        "patch": "str",
        "status": "str",
        "best_of": "Int8",
        "team1_id": "str",
        "team2_id": "str",
        "team1_score": "Int8",
        "team2_score": "Int8",
        "winner_team_id": "str",
        "map_veto_raw": "str"
    }
    
    for m in matches:
        match_id = str(m.get("match_id")) if m.get("match_id") else None
        event = m.get("event") or {}
        event_name = event.get("name")
        event_series = event.get("series")
        event_logo_url = event.get("logo")
        
        date_raw = m.get("date")
        patch = parse_patch(date_raw)
        
        status = m.get("status")
        
        maps = m.get("maps") or []
        best_of = len(maps)
        
        teams = m.get("teams") or []
        team1_id = None
        team2_id = None
        team1_score = None
        team2_score = None
        winner_team_id = None
        
        if len(teams) >= 1:
            t1 = teams[0]
            team1_id = str(t1.get("id")) if t1.get("id") else None
            team1_score = clean_int(t1.get("score"))
            t1_is_winner = t1.get("is_winner")
            if t1_is_winner is True or str(t1_is_winner).lower() == 'true':
                winner_team_id = team1_id
                
        if len(teams) >= 2:
            t2 = teams[1]
            team2_id = str(t2.get("id")) if t2.get("id") else None
            team2_score = clean_int(t2.get("score"))
            t2_is_winner = t2.get("is_winner")
            if t2_is_winner is True or str(t2_is_winner).lower() == 'true':
                winner_team_id = team2_id
                
        map_veto_raw = m.get("map_vetos")
        
        rows.append({
            "match_id": match_id,
            "event_name": event_name,
            "event_series": event_series,
            "event_logo_url": event_logo_url,
            "patch": patch,
            "status": status,
            "best_of": best_of,
            "team1_id": team1_id,
            "team2_id": team2_id,
            "team1_score": team1_score,
            "team2_score": team2_score,
            "winner_team_id": winner_team_id,
            "map_veto_raw": map_veto_raw
        })
        
    if not rows:
        df = pd.DataFrame(columns=dtypes.keys())
    else:
        df = pd.DataFrame(rows)
        
    for col, dtype in dtypes.items():
        if col in df.columns:
            df[col] = df[col].astype(dtype)
            
    return df
