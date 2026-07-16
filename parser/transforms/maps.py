import pandas as pd
from parser.utils import clean_int, duration_to_seconds

def derive_map_status(map_entry):
    rounds = map_entry.get('rounds') or []
    played_rounds = [r for r in rounds if r.get('winner') != '']
    
    score = map_entry.get('score') or {}
    t1 = clean_int(score.get('team1')) or 0
    t2 = clean_int(score.get('team2')) or 0
    
    if not played_rounds and t1 == 0 and t2 == 0:
        return 'not_played'
    elif len(played_rounds) == t1 + t2 and (t1 >= 13 or t2 >= 13 or t1 + t2 >= 24):
        return 'completed'
    else:
        return 'partial'

def get_map_ids(match):
    """Extract game_ids from economy_by_map or performance.by_map."""
    ids = []
    
    # Try economy_by_map
    for ebm in match.get('economy_by_map') or []:
        gid = ebm.get('game_id')
        if gid:
            ids.append(str(gid))
            
    # Fallback to performance.by_map
    if not ids:
        perf = match.get('performance') or {}
        for bm in perf.get('by_map') or []:
            gid = bm.get('game_id')
            if gid:
                ids.append(str(gid))
                
    # Final fallback: synthetic
    maps_list = match.get('maps') or []
    if not ids or len(ids) != len(maps_list):
        match_id = match.get('match_id')
        ids = [f"{match_id}_map{i+1}" for i in range(len(maps_list))]
        
    return ids

def transform(matches, resolver):
    rows = []
    
    dtypes = {
        "match_id": "str",
        "map_id": "str",
        "map_order": "Int8",
        "map_name": "str",
        "map_status": "str",
        "picked_by_team_id": "str",
        "is_decider": "boolean",
        "duration_seconds": "Int16",
        "team1_score": "Int8",
        "team2_score": "Int8",
        "team1_score_ct": "Int8",
        "team2_score_ct": "Int8",
        "team1_score_t": "Int8",
        "team2_score_t": "Int8",
        "team1_score_ot": "Int8",
        "team2_score_ot": "Int8"
    }
    
    for m in matches:
        match_id = str(m.get("match_id")) if m.get("match_id") else None
        maps_list = m.get("maps") or []
        map_ids = get_map_ids(m)
        
        # Resolve pick and decider info for this match
        picks, deciders, _ = resolver.resolve_match(m) if resolver else ({}, {}, {})
        
        for idx, map_entry in enumerate(maps_list):
            map_name = map_entry.get("map_name")
            if not map_name:
                continue
                
            map_id = map_ids[idx]
            map_order = idx + 1
            map_status = derive_map_status(map_entry)
            
            map_name_lower = map_name.lower()
            picked_by_team_id = picks.get(map_name_lower)
            is_decider = deciders.get(map_name_lower, False)
            
            dur_str = map_entry.get("duration")
            dur_secs = duration_to_seconds(dur_str)
            
            score = map_entry.get("score") or {}
            score_ct = map_entry.get("score_ct") or {}
            score_t = map_entry.get("score_t") or {}
            score_ot = map_entry.get("score_ot") or {}
            
            rows.append({
                "match_id": match_id,
                "map_id": map_id,
                "map_order": map_order,
                "map_name": map_name,
                "map_status": map_status,
                "picked_by_team_id": picked_by_team_id,
                "is_decider": is_decider,
                "duration_seconds": dur_secs,
                "team1_score": clean_int(score.get("team1")),
                "team2_score": clean_int(score.get("team2")),
                "team1_score_ct": clean_int(score_ct.get("team1")),
                "team2_score_ct": clean_int(score_ct.get("team2")),
                "team1_score_t": clean_int(score_t.get("team1")),
                "team2_score_t": clean_int(score_t.get("team2")),
                "team1_score_ot": clean_int(score_ot.get("team1")),
                "team2_score_ot": clean_int(score_ot.get("team2"))
            })
            
    if not rows:
        df = pd.DataFrame(columns=dtypes.keys())
    else:
        df = pd.DataFrame(rows)
        
    for col, dtype in dtypes.items():
        if col in df.columns:
            df[col] = df[col].astype(dtype)
            
    return df
