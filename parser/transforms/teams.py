import pandas as pd
import logging

# Set up logging for conflicts
logger = logging.getLogger("teams_transform")

def transform(matches, resolver):
    team_data = {} # team_id -> dict of info
    
    # Invert the veto resolver's global tag lookup to get team_id -> veto_tag
    veto_tag_by_team = {}
    if resolver and hasattr(resolver, 'global_tag_lookup'):
        for tag, team_id in resolver.global_tag_lookup.items():
            veto_tag_by_team[str(team_id)] = tag
            
    for m in matches:
        match_id = str(m.get("match_id")) if m.get("match_id") else None
        teams = m.get("teams") or []
        
        for t in teams:
            t_id = t.get("id")
            if not t_id:
                continue
            t_id_str = str(t_id)
            
            name = t.get("name")
            tag = t.get("tag")
            logo_url = t.get("logo")
            
            # Clean string fields
            name = name.strip() if name else None
            tag = tag.strip() if tag else None
            logo_url = logo_url.strip() if logo_url else None
            
            if t_id_str not in team_data:
                team_data[t_id_str] = {
                    "team_id": t_id_str,
                    "name": name,
                    "tag": tag,
                    "logo_url": logo_url,
                    "veto_tag": veto_tag_by_team.get(t_id_str),
                    "first_seen_match_id": match_id,
                    "last_seen_match_id": match_id,
                    "match_count": 1
                }
            else:
                existing = team_data[t_id_str]
                existing["match_count"] += 1
                existing["last_seen_match_id"] = match_id
                
                # Check and log conflicts
                if name and existing["name"] and name != existing["name"]:
                    logger.warning(f"Conflict for team_id {t_id_str}: name '{existing['name']}' -> '{name}'")
                    existing["name"] = name  # last-seen wins
                elif name and not existing["name"]:
                    existing["name"] = name
                    
                if tag and existing["tag"] and tag != existing["tag"]:
                    logger.warning(f"Conflict for team_id {t_id_str}: tag '{existing['tag']}' -> '{tag}'")
                    existing["tag"] = tag
                elif tag and not existing["tag"]:
                    existing["tag"] = tag
                    
                if logo_url and existing["logo_url"] and logo_url != existing["logo_url"]:
                    existing["logo_url"] = logo_url
                elif logo_url and not existing["logo_url"]:
                    existing["logo_url"] = logo_url
                    
    rows = list(team_data.values())
    
    dtypes = {
        "team_id": "str",
        "name": "str",
        "tag": "str",
        "logo_url": "str",
        "veto_tag": "str",
        "first_seen_match_id": "str",
        "last_seen_match_id": "str",
        "match_count": "int32"
    }
    
    if not rows:
        df = pd.DataFrame(columns=dtypes.keys())
    else:
        df = pd.DataFrame(rows)
        
    for col, dtype in dtypes.items():
        if col in df.columns:
            df[col] = df[col].astype(dtype)
            
    return df
