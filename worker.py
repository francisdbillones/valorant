import httpx
import time
import argparse
import sys
import socket

def parse_args():
    parser = argparse.ArgumentParser(description="Distributed Match Scraper Worker")
    parser.add_argument(
        "--coordinator", 
        required=True, 
        help="Base URL of the coordinator server (e.g. http://COORDINATOR_IP:8000)"
    )
    parser.add_argument(
        "--api", 
        default="http://127.0.0.1:3001/v2/match/details", 
        help="Local vlrggapi details endpoint (default: http://127.0.0.1:3001/v2/match/details)"
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
    return parser.parse_args()

def fetch_match(client, api_url, match_id):
    url = f"{api_url}?match_id={match_id}"
    retries = 3
    while retries > 0:
        try:
            r = client.get(url, timeout=30.0)
            if r.status_code == 200:
                payload = r.json()
                if payload.get("status") == "success":
                    inner_data = payload.get("data", {})
                    segments = inner_data.get("segments", [])
                    if segments:
                        return segments[0]
                    else:
                        return {"match_id": match_id, "status": "no_data"}
        except Exception as e:
            print(f"Exception fetching ID {match_id}: {e}")
        retries -= 1
        if retries > 0:
            time.sleep(3)
    return {"match_id": match_id, "status": "failed"}

def main():
    args = parse_args()
    
    worker_id = args.worker_id or socket.gethostname()
    print(f"Starting worker '{worker_id}'...")
    
    coordinator_client = httpx.Client(timeout=30.0)
    local_client = httpx.Client(timeout=40.0)
    
    get_chunk_url = f"{args.coordinator}/get_chunk"
    submit_chunk_url = f"{args.coordinator}/submit_chunk"
    
    empty_chunk_count = 0
    
    while True:
        try:
            # 1. Request a chunk from the coordinator
            print(f"\nRequesting chunk from coordinator '{get_chunk_url}'...")
            r = coordinator_client.get(get_chunk_url, params={"worker_id": worker_id})
            if r.status_code != 200:
                print(f"Error: Coordinator returned status {r.status_code}. Retrying in 10s...")
                time.sleep(10)
                continue
                
            chunk = r.json().get("chunk", [])
            
            if not chunk:
                empty_chunk_count += 1
                if empty_chunk_count >= 3:
                    # After 3 empty chunks, check if all tasks are complete
                    status_url = f"{args.coordinator}/status"
                    status_resp = coordinator_client.get(status_url)
                    if status_resp.status_code == 200:
                        status = status_resp.json()
                        if status.get("pending", 0) == 0 and status.get("leased", 0) == 0:
                            print("\nAll match processing tasks are complete! Worker shutting down.")
                            sys.exit(0)
                
                print("No pending matches available. Sleeping for 30s...")
                time.sleep(30)
                continue
                
            empty_chunk_count = 0
            print(f"Received chunk containing {len(chunk)} match IDs. Processing...")
            
            # 2. Process the chunk of matches
            results = []
            for idx, mid in enumerate(chunk):
                print(f"[{idx+1}/{len(chunk)}] Fetching ID {mid}... ", end="", flush=True)
                start_time = time.time()
                match_data = fetch_match(local_client, args.api, mid)
                elapsed = time.time() - start_time
                
                status = match_data.get("status", "OK")
                print(f"{status} ({elapsed:.1f}s)")
                results.append(match_data)
                
                if idx < len(chunk) - 1:
                    time.sleep(args.delay)
                    
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
                    submit_resp = coordinator_client.post(submit_chunk_url, json=payload)
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
                        time.sleep(5)
                    else:
                        print("Fatal: Failed to submit chunk results back to coordinator. Data for this chunk may be lost or reassigned.")
                        
        except httpx.ConnectError:
            print("Error connecting to coordinator. Sleeping for 15s...")
            time.sleep(15)
        except KeyboardInterrupt:
            print("\nWorker interrupted by user. Exiting.")
            sys.exit(0)
        except Exception as e:
            print(f"Unexpected exception in worker loop: {e}. Sleeping for 10s...")
            time.sleep(10)

if __name__ == "__main__":
    main()
