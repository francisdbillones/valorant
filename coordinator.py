from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from contextlib import asynccontextmanager
import json
import os
import sqlite3
import time
import re
from typing import List

# Resolve paths relative to this script's directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "all_recorded_games.json")
DB_FILE = os.path.join(BASE_DIR, "all_match_details.db")

DEFAULT_CHUNK_SIZE = 50
LEASE_TIMEOUT = 600  # 10 minutes (reclaim if worker dies)

# State
all_match_ids = []
completed_ids = set()
leased_ids = {}      # match_id -> lease_time

def extract_match_id(url_path):
    match = re.search(r"/(\d+)/", url_path)
    if match:
        return match.group(1)
    if url_path.isdigit():
        return url_path
    return None

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            match_id TEXT PRIMARY KEY,
            data TEXT
        )
    """)
    conn.commit()
    return conn

def load_all_data():
    global all_match_ids, completed_ids
    
    # 1. Load input matches
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file '{INPUT_FILE}' not found. Expected at: {INPUT_FILE}")
        return
        
    with open(INPUT_FILE, "r") as f:
        data = json.load(f)
    
    seen = set()
    for item in data:
        mid = extract_match_id(item.get("match_page", ""))
        if mid and mid not in seen:
            seen.add(mid)
            all_match_ids.append(mid)
            
    # 2. Init SQLite and load completed match IDs
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute("SELECT match_id FROM matches")
    rows = cursor.fetchall()
    for row in rows:
        completed_ids.add(str(row[0]))
    conn.close()
            
    print(f"Loaded {len(completed_ids)} completed matches from database '{DB_FILE}'.")
    print(f"Total match IDs to process: {len(all_match_ids)}. Pending: {len(all_match_ids) - len(completed_ids)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Perform startup load
    load_all_data()
    yield

app = FastAPI(title="Valorant Scraper Coordinator", lifespan=lifespan)

def save_matches_to_db(matches: List[dict]):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        # Bulk insert/replace matching data
        data_tuples = []
        for match in matches:
            mid = str(match.get("match_id"))
            if mid:
                data_tuples.append((mid, json.dumps(match)))
        
        if data_tuples:
            cursor.executemany("INSERT OR REPLACE INTO matches (match_id, data) VALUES (?, ?)", data_tuples)
            conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Database error saving progress: {e}")
        raise
    finally:
        conn.close()

@app.get("/get_chunk")
def get_chunk(
    worker_id: str = "unknown", 
    chunk_size: int = Query(DEFAULT_CHUNK_SIZE, description="Number of match IDs to return in the chunk", ge=1, le=500)
):
    global leased_ids
    now = time.time()
    
    # Reclaim expired leases
    expired_ids = [mid for mid, lease_time in leased_ids.items() if now - lease_time > LEASE_TIMEOUT]
    for mid in expired_ids:
        del leased_ids[mid]
        print(f"Reclaimed expired lease for match ID {mid}")
        
    # Find next available chunk
    chunk = []
    for mid in all_match_ids:
        if mid not in completed_ids and mid not in leased_ids:
            chunk.append(mid)
            leased_ids[mid] = now
            if len(chunk) >= chunk_size:
                break
                
    if chunk:
        print(f"Leased chunk of {len(chunk)} IDs to worker '{worker_id}'")
    return {"chunk": chunk}

class SubmitChunkPayload(BaseModel):
    worker_id: str
    results: List[dict]

@app.post("/submit_chunk")
def submit_chunk(payload: SubmitChunkPayload):
    global leased_ids, completed_ids
    
    try:
        # Save directly to SQLite
        save_matches_to_db(payload.results)
        
        count = 0
        for match in payload.results:
            mid = str(match.get("match_id"))
            if mid:
                completed_ids.add(mid)
                leased_ids.pop(mid, None)
                count += 1
                
        if count > 0:
            print(f"Worker '{payload.worker_id}' successfully submitted {count} matches to SQLite.")
            
        return {"status": "success", "processed": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database write failed: {str(e)}")

@app.get("/status")
def get_status():
    total = len(all_match_ids)
    completed = len(completed_ids)
    leased = len(leased_ids)
    pending = total - completed - leased
    return {
        "total": total,
        "completed": completed,
        "leased": leased,
        "pending": pending,
        "percentage_completed": f"{(completed / total * 100):.2f}%" if total > 0 else "0%"
    }

@app.get("/export")
def export_to_json(filepath: str = "all_match_details.json"):
    """Export SQLite database to a single JSON list file."""
    if not os.path.isabs(filepath):
        filepath = os.path.join(BASE_DIR, filepath)
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT data FROM matches")
    rows = cursor.fetchall()
    conn.close()
    
    matches_list = []
    for row in rows:
        matches_list.append(json.loads(row[0]))
        
    try:
        with open(filepath, "w") as f:
            json.dump(matches_list, f, indent=2)
        return {"status": "success", "exported_records": len(matches_list), "file": filepath}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write JSON: {str(e)}")
