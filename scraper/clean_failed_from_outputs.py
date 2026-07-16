import os
import json
import sqlite3

BASE_DIR = "/Users/francis/school/y2/t3/model/valorant"
DB_FILE = os.path.join(BASE_DIR, "all_match_details.db")
JSON_FILE = os.path.join(BASE_DIR, "all_match_details.json")

def main():
    print("Starting cleanup of failed match placeholders from output files...")
    
    # 1. Clean SQLite database
    if os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Get count before
        cursor.execute("SELECT COUNT(*) FROM matches")
        count_before = cursor.fetchone()[0]
        
        # We can extract status from the json data column
        # SQLite has JSON support built-in
        cursor.execute("SELECT match_id FROM matches")
        rows = cursor.fetchall()
        
        failed_ids = []
        for row in rows:
            mid = row[0]
            cursor.execute("SELECT data FROM matches WHERE match_id = ?", (mid,))
            data_str = cursor.fetchone()[0]
            try:
                data = json.loads(data_str)
                status = data.get("status", "")
                if status in ("failed", "no_data"):
                    failed_ids.append(mid)
            except Exception:
                failed_ids.append(mid)
                
        print(f"Found {len(failed_ids)} failed/no_data match records in database.")
        
        if failed_ids:
            # Delete in bulk
            cursor.executemany("DELETE FROM matches WHERE match_id = ?", [(mid,) for mid in failed_ids])
            conn.commit()
            print(f"Deleted {len(failed_ids)} records from database '{DB_FILE}'.")
            
            cursor.execute("SELECT COUNT(*) FROM matches")
            count_after = cursor.fetchone()[0]
            print(f"Database record count: {count_before} -> {count_after}")
        conn.close()
    else:
        print("Database file not found.")
        failed_ids = []

    # 2. Clean JSON file
    if os.path.exists(JSON_FILE):
        print(f"Reading '{JSON_FILE}' (this might take a few seconds as it is 1.35 GB)...")
        
        # Load JSON file
        with open(JSON_FILE, "r") as f:
            all_matches = json.load(f)
            
        initial_json_count = len(all_matches)
        print(f"Loaded {initial_json_count} records from JSON file.")
        
        # Filter out failed entries
        cleaned_matches = []
        removed_json_count = 0
        for match in all_matches:
            mid = str(match.get("match_id"))
            status = match.get("status", "")
            if status in ("failed", "no_data") or mid in failed_ids:
                removed_json_count += 1
            else:
                cleaned_matches.append(match)
                
        print(f"Found {removed_json_count} placeholder records to remove from JSON.")
        
        if removed_json_count > 0:
            print(f"Writing cleaned JSON back to '{JSON_FILE}'...")
            # Write temp file and replace to be safe
            temp_json_file = JSON_FILE + ".tmp"
            with open(temp_json_file, "w") as f:
                json.dump(cleaned_matches, f, indent=2)
            os.replace(temp_json_file, JSON_FILE)
            print(f"Successfully cleaned JSON file. Record count: {initial_json_count} -> {len(cleaned_matches)}")
        else:
            print("No failed placeholders found in JSON file.")
    else:
        print("JSON file not found.")

if __name__ == "__main__":
    main()
