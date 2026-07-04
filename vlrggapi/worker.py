import asyncio
import httpx
import time
import argparse
import sys
import os
import socket

# Ensure the current directory is in the path for importing API modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.scrapers.match_detail import vlr_match_detail
from utils.http_client import close_http_client

def parse_args():
    parser = argparse.ArgumentParser(description="Distributed Match Scraper Worker (Library Version)")
    parser.add_argument(
        "--coordinator", 
        required=True, 
        help="Base URL of the coordinator server (e.g. http://COORDINATOR_IP:8000)"
    )
    parser.add_argument(
        "--worker-id", 
        default=None, 
        help="Unique identifier for this worker VPS (defaults to hostname)"
    )
    parser.add_argument(
        "--delay", 
        type=float, 
        default=0.5, 
        help="Delay in seconds between requests (default: 0.5)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=50,
        help="Number of match IDs to request in each chunk (default: 50)"
    )
    return parser.parse_args()

async def fetch_match(match_id: str) -> dict:
    retries = 3
    while retries > 0:
        try:
            # Import and scrape directly from the codebase logic
            res = await vlr_match_detail(match_id)
            if "data" in res and "segments" in res["data"] and res["data"]["segments"]:
                return res["data"]["segments"][0]
            return {"match_id": match_id, "status": "no_data"}
        except Exception as e:
            status_code = getattr(e, "status_code", 500)
            detail = getattr(e, "detail", str(e))
            print(f"\nError scraping ID {match_id} (Status {status_code}): {detail}")
            
        retries -= 1
        if retries > 0:
            await asyncio.sleep(3)
            
    return {"match_id": match_id, "status": "failed"}

async def main_async():
    args = parse_args()
    
    worker_id = args.worker_id or socket.gethostname()
    print(f"Starting async library worker '{worker_id}'...")
    
    get_chunk_url = f"{args.coordinator}/get_chunk"
    submit_chunk_url = f"{args.coordinator}/submit_chunk"
    status_url = f"{args.coordinator}/status"
    
    empty_chunk_count = 0
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            try:
                # 1. Request a chunk from the coordinator
                print(f"\nRequesting chunk (size={args.chunk_size}) from coordinator...")
                r = await client.get(
                    get_chunk_url, 
                    params={"worker_id": worker_id, "chunk_size": args.chunk_size}
                )
                
                if r.status_code != 200:
                    print(f"Error: Coordinator returned status {r.status_code}. Retrying in 10s...")
                    await asyncio.sleep(10)
                    continue
                    
                chunk = r.json().get("chunk", [])
                
                if not chunk:
                    empty_chunk_count += 1
                    if empty_chunk_count >= 3:
                        # After 3 empty chunks, verify progress status
                        status_resp = await client.get(status_url)
                        if status_resp.status_code == 200:
                            status = status_resp.json()
                            if status.get("pending", 0) == 0 and status.get("leased", 0) == 0:
                                print("\nAll match processing tasks are complete! Worker shutting down.")
                                break
                    
                    print("No pending matches available. Sleeping for 30s...")
                    await asyncio.sleep(30)
                    continue
                    
                empty_chunk_count = 0
                print(f"Received chunk containing {len(chunk)} match IDs. Processing...")
                
                # 2. Process the chunk of matches directly using imports
                results = []
                for idx, mid in enumerate(chunk):
                    print(f"[{idx+1}/{len(chunk)}] Fetching ID {mid}... ", end="", flush=True)
                    start_time = time.time()
                    match_data = await fetch_match(mid)
                    elapsed = time.time() - start_time
                    
                    status = match_data.get("status", "OK")
                    print(f"{status} ({elapsed:.1f}s)")
                    results.append(match_data)
                    
                    if idx < len(chunk) - 1:
                        await asyncio.sleep(args.delay)
                        
                # 3. Submit completed chunk back to coordinator
                print(f"Submitting {len(results)} matches back to coordinator...")
                submit_success = False
                submit_retries = 5
                
                while submit_retries > 0 and not submit_success:
                    try:
                        payload = {
                            "worker_id": worker_id,
                            "results": results
                        }
                        submit_resp = await client.post(submit_chunk_url, json=payload)
                        if submit_resp.status_code == 200 and submit_resp.json().get("status") == "success":
                            submit_success = True
                            print("Chunk submission successful.")
                        else:
                            print(f"Error submitting chunk: {submit_resp.text}")
                    except Exception as e:
                        print(f"Exception submitting chunk: {e}")
                        
                    if not submit_success:
                        submit_retries -= 1
                        if submit_retries > 0:
                            print("Retrying submission in 5s...")
                            await asyncio.sleep(5)
                        else:
                            print("Fatal: Failed to submit chunk results back to coordinator. Data for this chunk may be lost or reassigned.")
                            
            except httpx.ConnectError:
                print("Error connecting to coordinator. Sleeping for 15s...")
                await asyncio.sleep(15)
            except KeyboardInterrupt:
                print("\nWorker interrupted by user. Exiting.")
                break
            except Exception as e:
                print(f"Unexpected exception in worker loop: {e}. Sleeping for 10s...")
                await asyncio.sleep(10)
                
    # Cleanup API http clients
    print("Closing HTTP client sessions...")
    await close_http_client()

def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nShutdown complete.")

if __name__ == "__main__":
    main()
