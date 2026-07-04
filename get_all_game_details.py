import httpx
import json
import os
import re
import time
import argparse
import sys

def parse_args():
    parser = argparse.ArgumentParser(description="Bulk Match Details Downloader for vlrggapi")
    parser.add_argument(
        "--input", 
        default="all_recorded_games.json", 
        help="Path to the input JSON file containing matches list"
    )
    parser.add_argument(
        "--output", 
        default="all_match_details.json", 
        help="Path to the output JSON file to save match details"
    )
    parser.add_argument(
        "--api", 
        default="http://127.0.0.1:3001/v2/match/details", 
        help="Base endpoint URL for match details"
    )
    parser.add_argument(
        "--delay", 
        type=float, 
        default=0.5, 
        help="Delay in seconds between requests (default: 0.5)"
    )
    parser.add_argument(
        "--limit", 
        type=int, 
        default=None, 
        help="Limit the number of matches to process (useful for testing)"
    )
    parser.add_argument(
        "--reverse", 
        action="store_true", 
        help="Process the missing matches in reverse order (useful for running two parallel instances meeting in the middle)"
    )
    return parser.parse_args()

def extract_match_id(url_path):
    match = re.search(r"/(\d+)/", url_path)
    if match:
        return match.group(1)
    if url_path.isdigit():
        return url_path
    return None

def load_input_matches(filepath):
    if not os.path.exists(filepath):
        print(f"Error: Input file '{filepath}' does not exist.")
        sys.exit(1)
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
        
        match_ids = []
        seen = set()
        for item in data:
            page = item.get("match_page", "")
            match_id = extract_match_id(page)
            if match_id and match_id not in seen:
                seen.add(match_id)
                match_ids.append(match_id)
        
        print(f"Successfully loaded {len(match_ids)} unique match IDs from '{filepath}'.")
        return match_ids
    except Exception as e:
        print(f"Error reading '{filepath}': {e}")
        sys.exit(1)

def load_existing_details(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                
            details_dict = {}
            if isinstance(data, list):
                for item in data:
                    mid = item.get("match_id")
                    if mid:
                        details_dict[str(mid)] = item
            elif isinstance(data, dict):
                details_dict = {str(k): v for k, v in data.items()}
                
            print(f"Resuming download. Found {len(details_dict)} matches already processed in '{filepath}'.")
            return details_dict
        except Exception as e:
            print(f"Warning: Error reading existing output file '{filepath}': {e}. Starting fresh.")
    return {}

def save_details(filepath, details_dict):
    try:
        output_list = list(details_dict.values())
        temp_file = filepath + ".tmp"
        with open(temp_file, "w") as f:
            json.dump(output_list, f, indent=2)
        os.replace(temp_file, filepath)
    except Exception as e:
        print(f"\nError saving progress to '{filepath}': {e}")

def main():
    args = parse_args()
    
    match_ids = load_input_matches(args.input)
    details_dict = load_existing_details(args.output)
    missing_ids = [mid for mid in match_ids if mid not in details_dict]
    
    if args.reverse:
        missing_ids.reverse()
        print("Reversing the order of missing matches for execution.")
        
    if args.limit:
        missing_ids = missing_ids[:args.limit]
        print(f"Limiting execution to the first {args.limit} missing matches.")
        
    if not missing_ids:
        print("All match details have already been fetched! Nothing to do.")
        return
        
    total_to_process = len(missing_ids)
    print(f"Starting fetch for {total_to_process} missing match details...")
    
    client = httpx.Client(timeout=30.0)
    start_time = time.time()
    processed_count = 0
    
    try:
        for idx, mid in enumerate(missing_ids):
            print(f"[{idx+1}/{total_to_process}] Fetching ID {mid}... ", end="", flush=True)
            
            url = f"{args.api}?match_id={mid}"
            retries = 3
            success = False
            status_text = "FAILED"
            
            while retries > 0 and not success:
                try:
                    r = client.get(url)
                    if r.status_code == 200:
                        payload = r.json()
                        if payload.get("status") == "success":
                            inner_data = payload.get("data", {})
                            segments = inner_data.get("segments", [])
                            
                            if segments:
                                match_data = segments[0]
                                details_dict[str(mid)] = match_data
                                success = True
                                status_text = "OK"
                            else:
                                details_dict[str(mid)] = {"match_id": mid, "status": "no_data"}
                                success = True
                                status_text = "EMPTY"
                        else:
                            status_text = f"API_ERROR ({payload.get('detail')})"
                    else:
                        status_text = f"HTTP_{r.status_code}"
                except Exception as e:
                    status_text = f"EXC_{type(e).__name__}"
                    
                if not success:
                    retries -= 1
                    if retries > 0:
                        time.sleep(3)
            
            # Save progress after every match
            save_details(args.output, details_dict)
            processed_count += 1
            
            # Calculate running ETA
            elapsed = time.time() - start_time
            avg_time_per_request = elapsed / processed_count
            remaining_requests = total_to_process - processed_count
            eta_seconds = remaining_requests * avg_time_per_request
            
            eta_hours = int(eta_seconds // 3600)
            eta_mins = int((eta_seconds % 3600) // 60)
            eta_secs = int(eta_seconds % 60)
            eta_str = f"{eta_hours:02d}:{eta_mins:02d}:{eta_secs:02d}"
            
            print(f"{status_text} | Avg: {avg_time_per_request:.2f}s/req | ETA: {eta_str}")
            
            # Rate limit delay
            if idx < len(missing_ids) - 1:
                time.sleep(args.delay)
                
    except KeyboardInterrupt:
        print("\nDownload interrupted by user. Saving current progress...")
        save_details(args.output, details_dict)
        print("Progress saved successfully. Exiting.")
        sys.exit(0)
        
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"\n--- Completed in {elapsed:.1f} seconds ---")
    print(f"Total matches in output file: {len(details_dict)}")

if __name__ == "__main__":
    main()
