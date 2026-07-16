import os
import pandas as pd

COLUMN_DESCRIPTIONS = {
    "matches": {
        "match_id": "Unique identifier for the match page on VLR.gg (Primary Key).",
        "event_name": "Name of the tournament/event.",
        "event_series": "Series/stage of the event (e.g. Group Stage, Playoff).",
        "event_logo_url": "URL of the event logo image.",
        "patch": "Game patch version during which the match was played (e.g. 13.0).",
        "status": "Match state (e.g. final, upcoming, no_data).",
        "best_of": "Inferred best-of count based on map entries.",
        "team1_id": "Unique identifier for Team 1 (Foreign Key).",
        "team2_id": "Unique identifier for Team 2 (Foreign Key).",
        "team1_score": "Series score of Team 1.",
        "team2_score": "Series score of Team 2.",
        "winner_team_id": "The ID of the winning team. Null if no winner (Foreign Key).",
        "map_veto_raw": "Unparsed string representing the complete veto process."
    },
    "teams": {
        "team_id": "Unique identifier for the team (Primary Key).",
        "name": "Clean name of the team.",
        "tag": "Short abbreviation tag for the team (often empty).",
        "logo_url": "URL of the team's logo image.",
        "veto_tag": "The short tag abbreviation used for the team in the veto strings.",
        "first_seen_match_id": "First match in which the team appeared in the dataset.",
        "last_seen_match_id": "Last match in which the team appeared in the dataset.",
        "match_count": "Total matches played by this team in the dataset."
    },
    "maps": {
        "match_id": "Foreign key referring to the matches table.",
        "map_id": "Unique identifier for the game/map played.",
        "map_order": "Order of the map in the match (1-based).",
        "map_name": "Name of the map (e.g. Ascent, Breeze).",
        "map_status": "Status of the map (completed, partial, not_played).",
        "picked_by_team_id": "Team that selected this map. Null if decider or unresolvable.",
        "is_decider": "Whether this map was the final decider map.",
        "duration_seconds": "Duration of the map in seconds.",
        "team1_score": "Final score for Team 1 on this map.",
        "team2_score": "Final score for Team 2 on this map.",
        "team1_score_ct": "Rounds won by Team 1 on CT side.",
        "team2_score_ct": "Rounds won by Team 2 on CT side.",
        "team1_score_t": "Rounds won by Team 1 on T side.",
        "team2_score_t": "Rounds won by Team 2 on T side.",
        "team1_score_ot": "Rounds won by Team 1 in Overtime.",
        "team2_score_ot": "Rounds won by Team 2 in Overtime."
    },
    "map_player_stats": {
        "match_id": "Foreign key referring to the matches table.",
        "map_id": "Foreign key referring to the maps table.",
        "team_id": "Foreign key referring to the teams table.",
        "player_name": "Player name.",
        "agent": "Valorant agent played.",
        "rating": "Overall player rating for the map.",
        "acs": "Average Combat Score.",
        "kills": "Total kills.",
        "deaths": "Total deaths.",
        "assists": "Total assists.",
        "kd_diff": "Kill/Death difference.",
        "kast_pct": "Percentage of rounds where player got a Kill, Assist, Survival, or traded Death.",
        "adr": "Average Damage per Round.",
        "hs_pct": "Headshot percentage.",
        "fk": "First Kills.",
        "fd": "First Deaths.",
        "fk_diff": "First Kill/Death difference."
    },
    "map_rounds": {
        "match_id": "Foreign key referring to the matches table.",
        "map_id": "Foreign key referring to the maps table.",
        "round_num": "Round number (1-based).",
        "winning_team_id": "Foreign key referring to the teams table.",
        "winning_side": "Side that won the round (t or ct)."
    },
    "series_kill_matrix": {
        "match_id": "Foreign key referring to the matches table.",
        "player_name": "Name of the player getting kills.",
        "player_team_id": "Resolved team ID of the player.",
        "opponent_name": "Name of the opponent player being killed.",
        "opponent_team_id": "Resolved team ID of the opponent.",
        "kills": "Kills by player on opponent.",
        "deaths": "Deaths of player to opponent.",
        "diff": "Kill differential."
    },
    "series_advanced_stats": {
        "match_id": "Foreign key referring to the matches table.",
        "player_name": "Player name.",
        "team_id": "Resolved team ID of the player.",
        "k2": "Rounds with 2 kills.",
        "k3": "Rounds with 3 kills.",
        "k4": "Rounds with 4 kills.",
        "k5": "Rounds with 5 kills.",
        "clutch_1v1": "1v1 clutches won.",
        "clutch_1v2": "1v2 clutches won.",
        "clutch_1v3": "1v3 clutches won.",
        "clutch_1v4": "1v4 clutches won.",
        "clutch_1v5": "1v5 clutches won.",
        "econ": "Economy score.",
        "pl": "Number of spike plants.",
        "de": "Number of spike defuses."
    },
    "series_economy": {
        "match_id": "Foreign key referring to the matches table.",
        "team_id": "Resolved team ID.",
        "team_tag": "Raw team tag in economy stats.",
        "pistols_won": "Number of pistol rounds won in the series.",
        "eco_rounds": "Number of eco rounds played (spend < $5k).",
        "eco_won": "Number of eco rounds won.",
        "semi_eco_rounds": "Number of semi-eco rounds played (spend $5k - $10k).",
        "semi_eco_won": "Number of semi-eco rounds won.",
        "semi_buy_rounds": "Number of semi-buy rounds played (spend $10k - $20k).",
        "semi_buy_won": "Number of semi-buy rounds won.",
        "full_buy_rounds": "Number of full-buy rounds played (spend > $20k).",
        "full_buy_won": "Number of full-buy rounds won."
    },
    "map_vetos": {
        "match_id": "Foreign key referring to the matches table.",
        "veto_order": "Order of the veto action (1-based).",
        "team_id": "Team performing the veto action.",
        "team_tag": "Abbreviation tag of the team.",
        "action": "Type of veto action (ban, pick, remains).",
        "map_name": "Name of the map."
    }
}

def generate(tables):
    print("Generating Data Dictionary...")
    
    lines = []
    lines.append("# VLR Match Data — Data Dictionary\n")
    lines.append("This document outlines the schemas, data types, and field descriptions for all 9 tables exported by the match parser pipeline. All tables are saved in Apache Parquet format.\n")
    
    for t_name, df in tables.items():
        lines.append(f"## Table: `{t_name}`\n")
        lines.append("| Column | Data Type | Description |")
        lines.append("|---|---|---|")
        
        descriptions = COLUMN_DESCRIPTIONS.get(t_name, {})
        
        for col in df.columns:
            dtype_str = str(df[col].dtype)
            # Map standard pandas dtypes to cleaner representations
            if dtype_str == "object":
                dtype_str = "string"
            elif dtype_str.startswith("Int") or dtype_str.startswith("int"):
                dtype_str = dtype_str.lower()
            elif dtype_str.startswith("Float") or dtype_str.startswith("float"):
                dtype_str = "float"
            elif dtype_str == "boolean":
                dtype_str = "boolean"
                
            desc = descriptions.get(col, "No description available.")
            lines.append(f"| `{col}` | `{dtype_str}` | {desc} |")
        lines.append("\n")
        
    dd_path = "output/data_dictionary.md"
    with open(dd_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    print(f"Data dictionary written to {dd_path}")
