# VLR Match Data — Data Dictionary

This document outlines the schemas, data types, and field descriptions for all 9 tables exported by the match parser pipeline. All tables are saved in Apache Parquet format.

## Table: `matches`

| Column | Data Type | Description |
|---|---|---|
| `match_id` | `str` | Unique identifier for the match page on VLR.gg (Primary Key). |
| `event_name` | `str` | Name of the tournament/event. |
| `event_series` | `str` | Series/stage of the event (e.g. Group Stage, Playoff). |
| `event_logo_url` | `str` | URL of the event logo image. |
| `patch` | `str` | Game patch version during which the match was played (e.g. 13.0). |
| `status` | `str` | Match state (e.g. final, upcoming, no_data). |
| `best_of` | `int8` | Inferred best-of count based on map entries. |
| `team1_id` | `str` | Unique identifier for Team 1 (Foreign Key). |
| `team2_id` | `str` | Unique identifier for Team 2 (Foreign Key). |
| `team1_score` | `int8` | Series score of Team 1. |
| `team2_score` | `int8` | Series score of Team 2. |
| `winner_team_id` | `str` | The ID of the winning team. Null if no winner (Foreign Key). |
| `map_veto_raw` | `str` | Unparsed string representing the complete veto process. |


## Table: `teams`

| Column | Data Type | Description |
|---|---|---|
| `team_id` | `str` | Unique identifier for the team (Primary Key). |
| `name` | `str` | Clean name of the team. |
| `tag` | `str` | Short abbreviation tag for the team (often empty). |
| `logo_url` | `str` | URL of the team's logo image. |
| `veto_tag` | `str` | The short tag abbreviation used for the team in the veto strings. |
| `first_seen_match_id` | `str` | First match in which the team appeared in the dataset. |
| `last_seen_match_id` | `str` | Last match in which the team appeared in the dataset. |
| `match_count` | `int32` | Total matches played by this team in the dataset. |


## Table: `maps`

| Column | Data Type | Description |
|---|---|---|
| `match_id` | `str` | Foreign key referring to the matches table. |
| `map_id` | `str` | Unique identifier for the game/map played. |
| `map_order` | `int8` | Order of the map in the match (1-based). |
| `map_name` | `str` | Name of the map (e.g. Ascent, Breeze). |
| `map_status` | `str` | Status of the map (completed, partial, not_played). |
| `picked_by_team_id` | `str` | Team that selected this map. Null if decider or unresolvable. |
| `is_decider` | `boolean` | Whether this map was the final decider map. |
| `duration_seconds` | `int16` | Duration of the map in seconds. |
| `team1_score` | `int8` | Final score for Team 1 on this map. |
| `team2_score` | `int8` | Final score for Team 2 on this map. |
| `team1_score_ct` | `int8` | Rounds won by Team 1 on CT side. |
| `team2_score_ct` | `int8` | Rounds won by Team 2 on CT side. |
| `team1_score_t` | `int8` | Rounds won by Team 1 on T side. |
| `team2_score_t` | `int8` | Rounds won by Team 2 on T side. |
| `team1_score_ot` | `int8` | Rounds won by Team 1 in Overtime. |
| `team2_score_ot` | `int8` | Rounds won by Team 2 in Overtime. |


## Table: `map_player_stats`

| Column | Data Type | Description |
|---|---|---|
| `match_id` | `str` | Foreign key referring to the matches table. |
| `map_id` | `str` | Foreign key referring to the maps table. |
| `team_id` | `str` | Foreign key referring to the teams table. |
| `player_name` | `str` | Player name. |
| `agent` | `str` | Valorant agent played. |
| `rating` | `float` | Overall player rating for the map. |
| `acs` | `int16` | Average Combat Score. |
| `kills` | `int16` | Total kills. |
| `deaths` | `int16` | Total deaths. |
| `assists` | `int16` | Total assists. |
| `kd_diff` | `int16` | Kill/Death difference. |
| `kast_pct` | `float` | Percentage of rounds where player got a Kill, Assist, Survival, or traded Death. |
| `adr` | `float` | Average Damage per Round. |
| `hs_pct` | `float` | Headshot percentage. |
| `fk` | `int16` | First Kills. |
| `fd` | `int16` | First Deaths. |
| `fk_diff` | `int16` | First Kill/Death difference. |


## Table: `map_rounds`

| Column | Data Type | Description |
|---|---|---|
| `match_id` | `str` | Foreign key referring to the matches table. |
| `map_id` | `str` | Foreign key referring to the maps table. |
| `round_num` | `int8` | Round number (1-based). |
| `winning_team_id` | `str` | Foreign key referring to the teams table. |
| `winning_side` | `str` | Side that won the round (t or ct). |


## Table: `series_kill_matrix`

| Column | Data Type | Description |
|---|---|---|
| `match_id` | `str` | Foreign key referring to the matches table. |
| `player_name` | `str` | Name of the player getting kills. |
| `player_team_id` | `str` | Resolved team ID of the player. |
| `opponent_name` | `str` | Name of the opponent player being killed. |
| `opponent_team_id` | `str` | Resolved team ID of the opponent. |
| `kills` | `int16` | Kills by player on opponent. |
| `deaths` | `int16` | Deaths of player to opponent. |
| `diff` | `int16` | Kill differential. |


## Table: `series_advanced_stats`

| Column | Data Type | Description |
|---|---|---|
| `match_id` | `str` | Foreign key referring to the matches table. |
| `player_name` | `str` | Player name. |
| `team_id` | `str` | Resolved team ID of the player. |
| `k2` | `int16` | Rounds with 2 kills. |
| `k3` | `int16` | Rounds with 3 kills. |
| `k4` | `int16` | Rounds with 4 kills. |
| `k5` | `int16` | Rounds with 5 kills. |
| `clutch_1v1` | `int16` | 1v1 clutches won. |
| `clutch_1v2` | `int16` | 1v2 clutches won. |
| `clutch_1v3` | `int16` | 1v3 clutches won. |
| `clutch_1v4` | `int16` | 1v4 clutches won. |
| `clutch_1v5` | `int16` | 1v5 clutches won. |
| `econ` | `int16` | Economy score. |
| `pl` | `int16` | Number of spike plants. |
| `de` | `int16` | Number of spike defuses. |


## Table: `series_economy`

| Column | Data Type | Description |
|---|---|---|
| `match_id` | `str` | Foreign key referring to the matches table. |
| `team_id` | `str` | Resolved team ID. |
| `team_tag` | `str` | Raw team tag in economy stats. |
| `pistols_won` | `int8` | Number of pistol rounds won in the series. |
| `eco_rounds` | `int16` | Number of eco rounds played (spend < $5k). |
| `eco_won` | `int16` | Number of eco rounds won. |
| `semi_eco_rounds` | `int16` | Number of semi-eco rounds played (spend $5k - $10k). |
| `semi_eco_won` | `int16` | Number of semi-eco rounds won. |
| `semi_buy_rounds` | `int16` | Number of semi-buy rounds played (spend $10k - $20k). |
| `semi_buy_won` | `int16` | Number of semi-buy rounds won. |
| `full_buy_rounds` | `int16` | Number of full-buy rounds played (spend > $20k). |
| `full_buy_won` | `int16` | Number of full-buy rounds won. |


## Table: `map_vetos`

| Column | Data Type | Description |
|---|---|---|
| `match_id` | `str` | Foreign key referring to the matches table. |
| `veto_order` | `int8` | Order of the veto action (1-based). |
| `team_id` | `str` | Team performing the veto action. |
| `team_tag` | `str` | Abbreviation tag of the team. |
| `action` | `str` | Type of veto action (ban, pick, remains). |
| `map_name` | `str` | Name of the map. |

