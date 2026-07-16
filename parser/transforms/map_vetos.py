import pandas as pd

def transform(matches, resolver):
    rows = []
    
    dtypes = {
        "match_id": "str",
        "veto_order": "Int8",
        "team_id": "str",
        "team_tag": "str",
        "action": "str",
        "map_name": "str"
    }
    
    if not resolver:
        return pd.DataFrame(columns=dtypes.keys())
        
    for m in matches:
        match_id = str(m.get("match_id")) if m.get("match_id") else None
        veto_str = m.get("map_vetos")
        if not veto_str:
            continue
            
        # Parse the veto string into segments/actions
        actions = resolver.parse_veto_string(veto_str)
        # Get team mapping for this match
        _, _, resolved_mapping = resolver.resolve_match(m)
        
        for idx, act in enumerate(actions):
            tag = act["tag"]
            action = act["action"]
            map_name = act["map_name"]
            
            team_id = None
            if tag:
                team_id = resolved_mapping.get(tag)
                
            rows.append({
                "match_id": match_id,
                "veto_order": idx + 1,
                "team_id": team_id,
                "team_tag": tag,
                "action": action,
                "map_name": map_name
            })
            
    if not rows:
        df = pd.DataFrame(columns=dtypes.keys())
    else:
        df = pd.DataFrame(rows)
        
    for col, dtype in dtypes.items():
        if col in df.columns:
            df[col] = df[col].astype(dtype)
            
    return df
