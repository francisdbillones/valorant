import os
import json
import pandas as pd
import numpy as np

def run(tables, raw_matches):
    print("Running QA Validation...")
    
    # Load quarantined count
    quarantined_count = 0
    quarantine_file = "output/quarantined.json"
    if os.path.exists(quarantine_file):
        try:
            with open(quarantine_file, "r") as f:
                quarantined_data = json.load(f)
                quarantined_count = len(quarantined_data)
        except Exception:
            pass
            
    matches_df = tables['matches']
    teams_df = tables['teams']
    maps_df = tables['maps']
    map_player_stats_df = tables['map_player_stats']
    map_rounds_df = tables['map_rounds']
    series_kill_matrix_df = tables['series_kill_matrix']
    series_advanced_stats_df = tables['series_advanced_stats']
    series_economy_df = tables['series_economy']
    map_vetos_df = tables['map_vetos']
    
    # 4.1 Coverage Report
    coverage_rows = []
    for name, df in tables.items():
        row_count = len(df)
        match_cov = df['match_id'].nunique() if 'match_id' in df.columns else None
        
        null_rates = {}
        for col in df.columns:
            null_count = df[col].isnull().sum()
            null_rate = null_count / row_count if row_count > 0 else 0
            null_rates[col] = f"{null_rate:.2%}"
            
        coverage_rows.append({
            "Table": name,
            "Row Count": row_count,
            "Unique Matches": match_cov if match_cov is not None else "N/A",
            "Null Rates": null_rates
        })
        
    # 4.2 Duplication Check
    perf_mismatches = 0
    econ_mismatches = 0
    perf_mismatch_examples = []
    
    for m in raw_matches:
        match_id = m.get("match_id")
        perf = m.get("performance") or {}
        top_km = perf.get("kill_matrix") or []
        top_as = perf.get("advanced_stats") or []
        
        # Check performance duplication
        mismatch_found = False
        for i, map_entry in enumerate(m.get("maps") or []):
            map_perf = map_entry.get("performance") or {}
            if map_perf:
                if map_perf.get("kill_matrix") != top_km:
                    mismatch_found = True
                if map_perf.get("advanced_stats") != top_as:
                    mismatch_found = True
        if mismatch_found:
            perf_mismatches += 1
            if len(perf_mismatch_examples) < 10:
                perf_mismatch_examples.append(match_id)
                
        # Check economy duplication
        # Compare map-level economy lists (inside economy_by_map) to top-level economy list.
        # Since structure differs, we check if the first item (team_tag) matches
        top_econ = m.get("economy") or []
        top_tags = sorted([entry.get("0") for entry in top_econ if isinstance(entry, dict) and entry.get("0")])
        
        ebm_list = m.get("economy_by_map") or []
        econ_mismatch_found = False
        for ebm in ebm_list:
            ebm_econ = ebm.get("economy") or {}
            # team1 contains a list of team econ info
            team1_list = ebm_econ.get("team1") or []
            ebm_tags = sorted([t_info[0] for t_info in team1_list if isinstance(t_info, list) and len(t_info) > 0])
            if ebm_tags and top_tags and ebm_tags != top_tags:
                econ_mismatch_found = True
                break
        if econ_mismatch_found:
            econ_mismatches += 1
            
    # 4.3 Score Consistency
    completed_maps = maps_df[maps_df['map_status'] == 'completed']
    rounds_count_df = map_rounds_df.groupby('map_id').size().reset_index(name='actual_rounds')
    score_check_df = pd.merge(completed_maps, rounds_count_df, on='map_id', how='left')
    
    score_check_df['actual_rounds'] = score_check_df['actual_rounds'].fillna(0).astype(int)
    score_check_df['expected_rounds'] = (score_check_df['team1_score'].fillna(0) + score_check_df['team2_score'].fillna(0)).astype(int)
    
    score_mismatches_df = score_check_df[score_check_df['expected_rounds'] != score_check_df['actual_rounds']]
    score_mismatch_count = len(score_mismatches_df)
    score_mismatch_examples = score_mismatches_df[['match_id', 'map_id', 'map_name', 'expected_rounds', 'actual_rounds']].head(10).to_dict(orient='records')
    
    # 4.4 Referential Integrity
    ri_issues = []
    
    # helper for checking foreign key
    def check_fk(child_df, child_col, parent_df, parent_col, child_name, parent_name):
        invalid_mask = ~child_df[child_col].isnull() & ~child_df[child_col].isin(parent_df[parent_col])
        invalid_count = invalid_mask.sum()
        if invalid_count > 0:
            ri_issues.append(f"Foreign Key violation: {invalid_count} rows in `{child_name}` column `{child_col}` do not exist in `{parent_name}` column `{parent_col}`.")
            
    check_fk(maps_df, 'match_id', matches_df, 'match_id', 'maps', 'matches')
    check_fk(map_player_stats_df, 'match_id', matches_df, 'match_id', 'map_player_stats', 'matches')
    check_fk(map_player_stats_df, 'map_id', maps_df, 'map_id', 'map_player_stats', 'maps')
    check_fk(map_player_stats_df, 'team_id', teams_df, 'team_id', 'map_player_stats', 'teams')
    
    check_fk(map_rounds_df, 'match_id', matches_df, 'match_id', 'map_rounds', 'matches')
    check_fk(map_rounds_df, 'map_id', maps_df, 'map_id', 'map_rounds', 'maps')
    check_fk(map_rounds_df, 'winning_team_id', teams_df, 'team_id', 'map_rounds', 'teams')
    
    check_fk(map_vetos_df, 'match_id', matches_df, 'match_id', 'map_vetos', 'matches')
    check_fk(map_vetos_df, 'team_id', teams_df, 'team_id', 'map_vetos', 'teams')
    
    # 4.5 Veto Resolution Report
    total_with_veto = matches_df['map_veto_raw'].notnull().sum()
    
    # Resolution rates of tags
    total_veto_actions = len(map_vetos_df)
    unresolved_veto_actions = map_vetos_df[map_vetos_df['action'] != 'remains']['team_id'].isnull().sum()
    resolved_veto_actions = map_vetos_df[map_vetos_df['action'] != 'remains']['team_id'].notnull().sum()
    
    resolution_rate = resolved_veto_actions / (resolved_veto_actions + unresolved_veto_actions) if (resolved_veto_actions + unresolved_veto_actions) > 0 else 0
    
    maps_with_picks = maps_df['picked_by_team_id'].notnull().sum()
    maps_with_null_picks = maps_df['picked_by_team_id'].isnull().sum()
    decider_maps_count = maps_df['is_decider'].fillna(False).sum()
    
    # Write QA Report Markdown
    report_lines = []
    report_lines.append("# VLR Match Data Parser — QA Validation Report\n")
    report_lines.append(f"**Total Input Matches**: {len(raw_matches)}")
    report_lines.append(f"**Quarantined Matches**: {quarantined_count}")
    report_lines.append(f"**Matches Processed**: {len(matches_df)}\n")
    
    report_lines.append("## 1. Coverage Report\n")
    report_lines.append("| Table | Row Count | Unique Matches | Null Rates by Column |")
    report_lines.append("|---|---|---|---|")
    for r in coverage_rows:
        null_rates_str = "<br>".join([f"**{k}**: {v}" for k, v in r["Null Rates"].items() if v != "0.00%"])
        if not null_rates_str:
            null_rates_str = "None"
        report_lines.append(f"| `{r['Table']}` | {r['Row Count']:,} | {r['Unique Matches']} | {null_rates_str} |")
    report_lines.append("\n")
    
    report_lines.append("## 2. Duplication Check\n")
    report_lines.append(f"- **Matches with performance discrepancies**: {perf_mismatches}")
    if perf_mismatches > 0:
        report_lines.append(f"  - Examples: {', '.join(perf_mismatch_examples)}")
    report_lines.append(f"- **Matches with economy discrepancies**: {econ_mismatches}\n")
    
    report_lines.append("## 3. Score Consistency\n")
    report_lines.append(f"- **Completed maps with score vs round count mismatch**: {score_mismatch_count}")
    if score_mismatch_count > 0:
        report_lines.append("\n| Match ID | Map ID | Map Name | Expected Rounds (Score sum) | Actual Rounds (Round count) |")
        report_lines.append("|---|---|---|---|---|")
        for ex in score_mismatch_examples:
            report_lines.append(f"| {ex['match_id']} | {ex['map_id']} | {ex['map_name']} | {ex['expected_rounds']} | {ex['actual_rounds']} |")
    report_lines.append("\n")
    
    report_lines.append("## 4. Referential Integrity\n")
    if ri_issues:
        for issue in ri_issues:
            report_lines.append(f"- ❌ {issue}")
    else:
        report_lines.append("- ✅ All foreign key and referential checks passed successfully!\n")
    report_lines.append("\n")
    
    report_lines.append("## 5. Veto Resolution Report\n")
    report_lines.append(f"- **Matches with Veto strings**: {total_with_veto} ({total_with_veto / len(matches_df):.2%} of processed matches)")
    report_lines.append(f"- **Veto Action Resolution Rate**: {resolution_rate:.2%} ({resolved_veto_actions:,} resolved vs {unresolved_veto_actions:,} unresolved)")
    report_lines.append(f"- **Maps Pick Attribution**:")
    report_lines.append(f"  - Maps with picking team resolved: {maps_with_picks:,}")
    report_lines.append(f"  - Maps with null picking team: {maps_with_null_picks:,}")
    report_lines.append(f"  - Decider maps identified: {decider_maps_count:,}\n")
    
    qa_path = "output/qa_report.md"
    with open(qa_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"QA report written to {qa_path}")
