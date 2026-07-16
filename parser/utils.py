import re

DATE_PATCH_REGEX = re.compile(r"Patch\s+([\w.]+)", re.IGNORECASE)

def parse_patch(date_str):
    if not date_str:
        return None
    match = DATE_PATCH_REGEX.search(date_str)
    if match:
        return match.group(1).strip()
    return None

def clean_int(val):
    if val is None or val == "":
        return None
    try:
        return int(val)
    except ValueError:
        cleaned = re.sub(r"[^\d\-]", "", str(val))
        if cleaned:
            try:
                return int(cleaned)
            except ValueError:
                return None
        return None

def clean_float(val):
    if val is None or val == "":
        return None
    try:
        return float(val)
    except ValueError:
        cleaned = re.sub(r"[^\d\.\-]", "", str(val))
        if cleaned:
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None

def clean_pct(val):
    if val is None or val == "":
        return None
    val_str = str(val).strip()
    try:
        if val_str.endswith("%"):
            return float(val_str[:-1]) / 100.0
        return float(val_str)
    except ValueError:
        cleaned = re.sub(r"[^\d\.\-]", "", val_str)
        if cleaned:
            try:
                if val_str.endswith("%"):
                    return float(cleaned) / 100.0
                return float(cleaned)
            except ValueError:
                return None
        return None

def duration_to_seconds(duration_str):
    if not duration_str:
        return None
    parts = duration_str.strip().split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 1 and parts[0].isdigit():
            return int(parts[0])
    except Exception:
        pass
    return None

def parse_packed_kd(s):
    if not s:
        return None, None, None
    parts = s.strip().split()
    if len(parts) >= 2:
        kills = clean_int(parts[0])
        deaths = clean_int(parts[1])
        diff = clean_int(parts[2]) if len(parts) > 2 else None
        return kills, deaths, diff
    return None, None, None

def parse_economy_tuple(s):
    """
    Parse '3 (1)' -> (3, 1) or '1' -> (1, None) or similar.
    """
    if not s:
        return None, None
    s = s.strip()
    match = re.match(r"^(\d+)\s*\((.*?)\)$", s)
    if match:
        rounds = clean_int(match.group(1))
        won = clean_int(match.group(2))
        return rounds, won
    else:
        # Check if it's just a number
        val = clean_int(s)
        return val, None

def resolve_player_team(player_name_with_tag, team1_name, team2_name, team1_id, team2_id, veto_tag_lookup=None):
    """
    Try to match the suffix of 'Chronicle VIT' to a team.
    """
    if not player_name_with_tag:
        return None
        
    parts = player_name_with_tag.rsplit(' ', 1)
    if len(parts) == 2:
        suffix = parts[1].strip()
        
        # Check veto_tag_lookup (most reliable if global veto resolver has mapped it)
        if veto_tag_lookup:
            resolved_id = veto_tag_lookup.get(suffix)
            if resolved_id in (team1_id, team2_id):
                return resolved_id
        
        # Fallback: substring match against team names (case-insensitive)
        if team1_name and suffix.lower() in team1_name.lower():
            return team1_id
        if team2_name and suffix.lower() in team2_name.lower():
            return team2_id
            
    return None
