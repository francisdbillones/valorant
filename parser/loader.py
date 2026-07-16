import json
import os

def load_json(filepath):
    """
    Load JSON file, validate records, and quarantine malformed records.
    Returns a list of validated match dictionaries.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"JSON source file not found at {filepath}")
        
    print(f"Loading raw JSON from {filepath}...")
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            records = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse JSON file {filepath}: {e}")
            
    if not isinstance(records, list):
        raise ValueError(f"Expected a JSON list of matches, but got {type(records)}")
        
    validated_records = []
    quarantined = []
    
    for idx, r in enumerate(records):
        if not isinstance(r, dict):
            quarantined.append({
                "index": idx,
                "reason": "Record is not a JSON object/dictionary",
                "data_preview": str(r)[:200]
            })
            continue
            
        match_id = r.get("match_id")
        teams = r.get("teams")
        maps = r.get("maps")
        
        reasons = []
        if not match_id:
            reasons.append("Missing match_id")
        if teams is None:
            reasons.append("Missing teams key")
        elif not isinstance(teams, list):
            reasons.append("teams is not a list")
        if maps is None:
            reasons.append("Missing maps key")
        elif not isinstance(maps, list):
            reasons.append("maps is not a list")
            
        if reasons:
            quarantined.append({
                "index": idx,
                "match_id": match_id,
                "reasons": reasons,
                "record": r
            })
        else:
            validated_records.append(r)
            
    # Write quarantined records to output directory
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(filepath))), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    quarantine_path = os.path.join(output_dir, "quarantined.json")
    with open(quarantine_path, "w", encoding="utf-8") as f:
        json.dump(quarantined, f, indent=2)
        
    print(f"Loader completed. Loaded: {len(validated_records)}, Quarantined: {len(quarantined)}")
    return validated_records
