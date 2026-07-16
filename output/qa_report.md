# VLR Match Data Parser — QA Validation Report

**Total Input Matches**: 32691
**Quarantined Matches**: 0
**Matches Processed**: 32691

## 1. Coverage Report

| Table | Row Count | Unique Matches | Null Rates by Column |
|---|---|---|---|
| `matches` | 32,691 | 32691 | **patch**: 5.52%<br>**team1_id**: 0.03%<br>**team2_id**: 0.05%<br>**winner_team_id**: 0.80% |
| `teams` | 5,653 | N/A | **tag**: 98.30%<br>**veto_tag**: 75.27% |
| `maps` | 68,366 | 32390 | **picked_by_team_id**: 62.33%<br>**duration_seconds**: 5.12%<br>**team1_score_ct**: 1.16%<br>**team2_score_ct**: 1.17%<br>**team1_score_t**: 1.17%<br>**team2_score_t**: 1.17%<br>**team1_score_ot**: 89.83%<br>**team2_score_ot**: 89.83% |
| `map_player_stats` | 682,905 | 32380 | **team_id**: 0.01%<br>**rating**: 17.92%<br>**acs**: 0.77%<br>**kills**: 0.64%<br>**deaths**: 0.64%<br>**assists**: 0.66%<br>**kd_diff**: 1.24%<br>**kast_pct**: 17.88%<br>**adr**: 4.63%<br>**hs_pct**: 4.77%<br>**fk**: 2.44%<br>**fd**: 4.78%<br>**fk_diff**: 4.78% |
| `map_rounds` | 1,395,133 | 31704 | **winning_side**: 0.01% |
| `series_kill_matrix` | 520,550 | 20822 | **player_team_id**: 22.49%<br>**opponent_team_id**: 22.47%<br>**diff**: 0.01% |
| `series_advanced_stats` | 209,312 | 20822 | **team_id**: 22.49%<br>**k2**: 0.89%<br>**k3**: 18.43%<br>**k4**: 67.96%<br>**k5**: 95.43%<br>**clutch_1v1**: 61.99%<br>**clutch_1v2**: 77.96%<br>**clutch_1v3**: 93.38%<br>**clutch_1v4**: 98.75%<br>**clutch_1v5**: 99.87% |
| `series_economy` | 41,644 | 20822 | **team_id**: 23.07% |
| `map_vetos` | 94,146 | 14077 | **team_id**: 20.15%<br>**team_tag**: 14.18% |


## 2. Duplication Check

- **Matches with performance discrepancies**: 0
- **Matches with economy discrepancies**: 0

## 3. Score Consistency

- **Completed maps with score vs round count mismatch**: 0


## 4. Referential Integrity

- ✅ All foreign key and referential checks passed successfully!



## 5. Veto Resolution Report

- **Matches with Veto strings**: 32691 (100.00% of processed matches)
- **Veto Action Resolution Rate**: 93.04% (75,174 resolved vs 5,620 unresolved)
- **Maps Pick Attribution**:
  - Maps with picking team resolved: 25,751
  - Maps with null picking team: 42,615
  - Decider maps identified: 5,709
