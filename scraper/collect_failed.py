import os
import json
import sqlite3
import re

BASE_DIR = "/Users/francis/school/y2/t3/model/valorant"
INPUT_FILE = os.path.join(BASE_DIR, "all_recorded_games.json")
DB_FILE = os.path.join(BASE_DIR, "all_match_details.db")
OUTPUT_FILE = os.path.join(BASE_DIR, "missing_and_failed_games.json")

def extract_match_id(url_path):
    if not url_path:
        return None
    match = re.search(r"/(\d+)/", url_path)
    if match:
        return match.group(1)
    if str(url_path).isdigit():
        return str(url_path)
    return None

def main():
    print("Collecting failed and missing matches...")
    
    # 1. Load original recorded games
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Original input file not found at '{INPUT_FILE}'")
        return
        
    with open(INPUT_FILE, "r") as f:
        original_games = json.load(f)
    print(f"Loaded {len(original_games)} games from '{INPUT_FILE}'")
    
    # Create mapping of match_id -> game item
    id_to_game = {}
    for item in original_games:
        mid = extract_match_id(item.get("match_page", ""))
        if mid:
            # Keep the first occurrence or list them (assuming match_page is unique)
            id_to_game[mid] = item
            
    print(f"Unique match IDs in original list: {len(id_to_game)}")
    
    # 2. Check SQLite database for match statuses
    if not os.path.exists(DB_FILE):
        print(f"Error: Database not found at '{DB_FILE}'")
        return
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT match_id, data FROM matches")
    rows = cursor.fetchall()
    conn.close()
    
    db_matches = {}
    for mid, data_str in rows:
        try:
            d = json.loads(data_str)
            db_matches[mid] = d.get("status", "unknown")
        except Exception:
            db_matches[mid] = "parse_error"
            
    print(f"Matches in database: {len(db_matches)}")
    
    # 3. Identify failed and missing match IDs
    failed_ids = []
    missing_ids = []
    
    for mid in id_to_game.keys():
        if mid not in db_matches:
            missing_ids.append(mid)
        elif db_matches[mid] == "failed" or db_matches[mid] == "parse_error":
            failed_ids.append(mid)
            
    print(f"Found {len(failed_ids)} matches marked as 'failed' in DB.")
    print(f"Found {len(missing_ids)} matches completely missing from DB.")
    
    total_to_retry = failed_ids + missing_ids
    print(f"Total matches to retrieve: {len(total_to_retry)}")
    
    # 4. Map them back to the original game format
    retry_list = []
    for mid in total_to_retry:
        game_item = id_to_game.get(mid)
        if game_item:
            retry_list.append(game_item)
            
    # 5. Save to the new output file
    with open(OUTPUT_FILE, "w") as f:
        json.dump(retry_list, f, indent=2)
        
    print(f"Successfully wrote {len(retry_list)} items to '{OUTPUT_FILE}'")
    
    # Delete the failed matches from the database if they are marked as 'failed',
    # so that the next run can insert them as fresh matches without constraint conflict
    # or overwriting them.
    # Note: We won't delete them yet unless the user approves, but let's write the code or instruct them.
    
if __name__ == "__main__":
    main()
