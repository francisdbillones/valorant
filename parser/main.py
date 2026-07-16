import os
import time
from parser import loader
from parser.veto_resolver import VetoResolver
from parser.transforms import (
    matches,
    teams,
    maps,
    map_player_stats,
    map_rounds,
    series_kill_matrix,
    series_advanced_stats,
    series_economy,
    map_vetos
)
from parser import qa
from parser import data_dictionary

def main():
    start_time = time.time()
    print("=== Starting VLR Match Data Parser Pipeline ===")
    
    # 0. Set directories
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, "all_match_details.json")
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Load and validate raw JSON
    raw_matches = loader.load_json(json_path)
    
    # 2. Build Veto Resolver (Pass 1 of Veto Resolution)
    print("Building veto resolver (Pass 1: Tag -> Team lookup)...")
    resolver = VetoResolver(raw_matches)
    print(f"Veto Resolver built. Resolved {len(resolver.global_tag_lookup)} global tag mappings.")
    
    # 3. Transform tables independently
    print("Starting transforms...")
    tables = {}
    
    t_start = time.time()
    tables['matches'] = matches.transform(raw_matches)
    print(f" - matches table completed: {len(tables['matches'])} rows (took {time.time() - t_start:.2f}s)")
    
    t_start = time.time()
    tables['teams'] = teams.transform(raw_matches, resolver)
    print(f" - teams table completed: {len(tables['teams'])} rows (took {time.time() - t_start:.2f}s)")
    
    t_start = time.time()
    tables['maps'] = maps.transform(raw_matches, resolver)
    print(f" - maps table completed: {len(tables['maps'])} rows (took {time.time() - t_start:.2f}s)")
    
    t_start = time.time()
    tables['map_player_stats'] = map_player_stats.transform(raw_matches)
    print(f" - map_player_stats table completed: {len(tables['map_player_stats'])} rows (took {time.time() - t_start:.2f}s)")
    
    t_start = time.time()
    tables['map_rounds'] = map_rounds.transform(raw_matches)
    print(f" - map_rounds table completed: {len(tables['map_rounds'])} rows (took {time.time() - t_start:.2f}s)")
    
    t_start = time.time()
    tables['series_kill_matrix'] = series_kill_matrix.transform(raw_matches, resolver)
    print(f" - series_kill_matrix table completed: {len(tables['series_kill_matrix'])} rows (took {time.time() - t_start:.2f}s)")
    
    t_start = time.time()
    tables['series_advanced_stats'] = series_advanced_stats.transform(raw_matches, resolver)
    print(f" - series_advanced_stats table completed: {len(tables['series_advanced_stats'])} rows (took {time.time() - t_start:.2f}s)")
    
    t_start = time.time()
    tables['series_economy'] = series_economy.transform(raw_matches, resolver)
    print(f" - series_economy table completed: {len(tables['series_economy'])} rows (took {time.time() - t_start:.2f}s)")
    
    t_start = time.time()
    tables['map_vetos'] = map_vetos.transform(raw_matches, resolver)
    print(f" - map_vetos table completed: {len(tables['map_vetos'])} rows (took {time.time() - t_start:.2f}s)")
    
    # 4. Write parquet tables
    print("Writing Parquet files to output/...")
    for name, df in tables.items():
        parquet_path = os.path.join(output_dir, f"{name}.parquet")
        df.to_parquet(parquet_path, index=False)
        print(f" - Wrote {parquet_path}")
        
    # 5. QA validation pass
    qa.run(tables, raw_matches)
    
    # 6. Data dictionary generation
    data_dictionary.generate(tables)
    
    elapsed = time.time() - start_time
    print(f"=== Parser Pipeline Completed in {elapsed:.2f}s ===")

if __name__ == "__main__":
    main()
