from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
import json
import os
import time
import re
from typing import List

# Configuration
INPUT_FILE = "all_recorded_games.json"
OUTPUT_FILE = "all_match_details.json"
CHUNK_SIZE = 50
LEASE_TIMEOUT = 600  # 10 minutes (reclaim if worker dies)

# State
all_match_ids = []
completed_ids = set()
leased_ids = {}      # match_id -> lease_time
match_details = {}   # match_id -> data

def extract_match_id(url_path):
    match = re.search(r"/(\d+)/", url_path)
    if match:
        return match.group(1)
    if url_path.isdigit():
        return url_path
    return None

def load_all_data():
    global all_match_ids, completed_ids, match_details
    
    # 1. Load input matches
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file '{INPUT_FILE}' not found in the current working directory.")
        return
        
    with open(INPUT_FILE, "r") as f:
        data = json.load(f)
    
    seen = set()
    for item in data:
        mid = extract_match_id(item.get("match_page", ""))
        if mid and mid not in seen:
            seen.add(mid)
            all_match_ids.append(mid)
            
    # 2. Load completed matches to resume progress
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r") as f:
                existing_data = json.load(f)
            for item in existing_data:
                mid = item.get("match_id")
                if mid:
                    completed_ids.add(str(mid))
                    match_details[str(mid)] = item
            print(f"Loaded {len(completed_ids)} completed matches from '{OUTPUT_FILE}'.")
        except Exception as e:
            print(f"Error loading '{OUTPUT_FILE}': {e}")
            
    print(f"Total match IDs to process: {len(all_match_ids)}. Pending: {len(all_match_ids) - len(completed_ids)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Perform startup load
    load_all_data()
    yield

app = FastAPI(title="Valorant Scraper Coordinator", lifespan=lifespan)

def save_progress():
    try:
        temp_file = OUTPUT_FILE + ".tmp"
        with open(temp_file, "w") as f:
            json.dump(list(match_details.values()), f, indent=2)
        os.replace(temp_file, OUTPUT_FILE)
    except Exception as e:
        print(f"Error saving output file: {e}")

@app.get("/get_chunk")
def get_chunk(worker_id: str = "unknown"):
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
            if len(chunk) >= CHUNK_SIZE:
                break
                
    if chunk:
        print(f"Leased chunk of {len(chunk)} IDs to worker '{worker_id}'")
    return {"chunk": chunk}

class SubmitChunkPayload(BaseModel):
    worker_id: str
    results: List[dict]

@app.post("/submit_chunk")
def submit_chunk(payload: SubmitChunkPayload):
    global leased_ids, completed_ids, match_details
    
    count = 0
    for match in payload.results:
        mid = str(match.get("match_id"))
        if mid:
            match_details[mid] = match
            completed_ids.add(mid)
            # Remove from leased dict if present
            leased_ids.pop(mid, None)
            count += 1
            
    if count > 0:
        save_progress()
        print(f"Worker '{payload.worker_id}' successfully submitted {count} matches.")
        
    return {"status": "success", "processed": count}

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
