# Valorant Pro Play EDA — Analysis Results

This report presents findings from the exploratory data analysis comparing **Tier 1 (VCT)** and **Tier 2 (VCL)** Valorant matches, spanning **36,275 completed maps** across **16,177 final matches**.

---

## 1. Dataset Baseline & Volume
* **Total Completed Maps**: 36,275 (T1: 17,462 | T2: 18,813)
* **CT Round Win Rate**: T1 rounds are 50.00% CT-win, whereas T2 rounds are slightly T-sided at 49.26% CT-win.
* **Match Format**: Bo3 is dominant across both tiers, with Bo5 reserved for Grand Finals and late-stage brackets.
* **Map Selection Proportions (Temporal Skew)**: Tier 2 features a significantly higher proportion of newer maps in its history compared to Tier 1:
  - **Lotus**: T2: **13.20%** vs. T1: **5.14%**
  - **Pearl**: T2: **7.65%** vs. T1: **2.34%**
  - **Sunset**: T2: **5.74%** vs. T1: **2.26%**
  This is driven by a strong temporal skew: **71%** of Tier 1 matches in the dataset were played in the early era (2021–2022, Episodes 2–4) before these newer maps were introduced, whereas **88%** of Tier 2 matches are from the modern era (2023–2026, Episodes 6–12) when these maps were active in rotation.

![Tier & Region Distribution](figures/00_tier_region_distribution.png)
![Map Volume by Tier](figures/01_map_volume_by_tier.png)
![Best Of Format Distribution](figures/01_bestof_by_tier.png)
![Patch Timeline](figures/01_patch_timeline.png)

---

## 2. Map & Pick Dynamics

* **Median Score Margin**: 5.0 rounds (e.g. 13–8) in both T1 and T2. However, the Mann-Whitney U test shows a highly significant difference ($p < 0.0001$) in margin distributions.
* **Overtime Rate**: T1 maps go to overtime 7.66% of the time, compared to 8.05% in T2.
* **Pick Advantage**: Teams win on their own map picks 51.99% of the time in T1, and 51.00% of the time in T2. Map selection choice offers only a marginal win-rate boost.

> [!NOTE]
> The CT win rate per map is highly consistent, though certain maps (e.g. Ascent, Lotus) show slight side bias which is more pronounced in T2 play.

![CT Win Rate Heatmap](figures/02_ct_heatmap.png)
![Map Pickrate Norm](figures/02_map_pickrate.png)
![Score Margin Distribution](figures/02_score_margin.png)
![Overtime Rates](figures/02_ot_rate.png)

---

## 3. Player Performance & Agent Meta

| Metric | Tier 1 (VCT) Correlation | Tier 2 (VCL) Correlation |
| :--- | :---: | :---: |
| **Total KD Diff** | 0.833 | 0.831 |
| **Mean Rating** | 0.787 | 0.792 |
| **Mean ACS** | 0.721 | 0.714 |
| **Mean KAST** | 0.698 | 0.688 |
| **Mean ADR** | 0.667 | 0.679 |
| **Total FK Diff** | 0.519 | 0.508 |

### Clutches & Multifrags Comparison (per 100 Rounds)

| Event Type | Tier 1 (VCT) Rate | Tier 2 (VCL) Rate | Statistical Significance ($p$-value) |
| :--- | :---: | :---: | :---: |
| **Double Kill (2K)** | 12.42 | 12.37 | $0.830$ (Not Significant) |
| **Triple Kill (3K)** | 3.87 | 3.89 | $0.059$ (Not Significant) |
| **Quadra Kill (4K)** | 0.799 | 0.814 | **$0.002$ (Significant)** |
| **Ace (5K)** | 0.092 | 0.094 | $0.224$ (Not Significant) |
| **1v1 Clutch** | 0.949 | 0.987 | **$< 0.00001$ (Highly Significant)** |
| **1v2 Clutch** | 0.489 | 0.497 | **$0.041$ (Significant)** |
| **1v3 Clutch** | 0.129 | 0.079 | **$0.00002$ (Highly Significant)** |
| **1v4 Clutch** | 0.024 | 0.025 | $0.203$ (Not Significant) |
| **1v5 Clutch** | 0.003 | 0.003 | $0.510$ (Not Significant) |

> [!TIP]
> **Key Finding**: Clutches (especially 1v1 and 1v3) and Quadra Kills (4Ks) are won at statistically significantly higher rates in Tier 2 than in Tier 1. 
> This indicates that VCT (T1) teams display tighter team coordination, crossfires, and spacing in numbers-advantage situations, making individual clutch plays much more difficult to execute. In contrast, VCL (T2) matches exhibit slightly looser, more individualistic play that enables lone players to find isolated duels.

### KAST Quartile Map Win Rates
* **Q1 (low KAST)**: T1: 13.87% | T2: 14.90%
* **Q4 (high KAST)**: T1: 85.77% | T2: 83.99%

> [!IMPORTANT]
> The performance metrics correlate with winning at near-identical levels across both tiers. First blood differentials (`FK Diff`) remain highly valuable, yielding a strong advantage to teams that secure the opening pick.

![Player Stat Correlation](figures/03_stat_winrate_correlation.png)
![Agent Meta Heatmaps](figures/03_agent_meta.png)
![First Kill Advantage](figures/03_fk_advantage.png)
![Stat Violin Distributions](figures/03_stat_distributions.png)
![Clutches and Multifrags Comparison](figures/03_clutches_multifrags.png)
![Role Rating Distribution](figures/03_role_rating_distribution.png)

---

### Player Performance across Roles & Tiers

| Player Role | Tier 1 (VCT) Rating | Tier 2 (VCL) Rating | T-Test Statistical Significance ($p$-value) |
| :--- | :---: | :---: | :---: |
| **Duelist** | **1.0319** | **1.0248** | **$0.0089$ (Significant)** |
| **Sentinel** | **0.9822** | **0.9962** | **$< 0.00001$ (Highly Significant)** |
| **Controller** | **0.9855** | **1.0036** | **$< 0.00001$ (Highly Significant)** |
| **Initiator** | **0.9786** | **0.9820** | $0.1265$ (Not Significant) |

> [!TIP]
> **Key Finding**: Controllers and Sentinels perform significantly better (achieving higher average player Ratings and ACS/ADR) in Tier 2 than in Tier 1. 
> In Tier 1, advanced utility coordination makes site-anchoring (Sentinels) and passive positioning (Controllers) much harder to solo-play. In Tier 2, looser tactical execution enables Sentinels and Controllers to secure isolated duels and leverage setup traps for higher statistical output. 
> Conversely, Duelists achieve higher ratings in Tier 1, where they are heavily supported by their team's structured utility entries.

## 4. Economic & Halftime Dynamics

* **Pistol Round Leverage**: Winning both pistol rounds on a map boosts match winrate to 57.35% in T1 and 54.94% in T2.
* **Halftime Leader winrate**: Leading at halftime (rounds 1–12) is a massive predictor of map victory:
  - **Tier 1 (VCT)**: 78.86% win rate
  - **Tier 2 (VCL)**: 77.66% win rate

![Pistol Impact](figures/04_pistol_impact.png)
![Buy Type Winrates](figures/04_buy_type_winrate.png)
![Full Buy Efficiency](figures/04_fullbuy_efficiency.png)
![Halftime Predictor](figures/05_halftime_predictor.png)
![Max Win Streaks](figures/05_win_streaks.png)

---

### Win Probability by Halftime Round Deficit

| Halftime Deficit | Tier 1 (VCT) Win Rate | Tier 2 (VCL) Win Rate | Deficit Score Examples (Leader - Trailer) |
| :--- | :---: | :---: | :---: |
| **0 rounds (Tie)** | 50.00% | 50.00% | 6 - 6 |
| **2 rounds** | 32.38% | 32.29% | 7 - 5 |
| **4 rounds** | 18.32% | 18.81% | 8 - 4 |
| **6 rounds** | 8.28% | 9.02% | 9 - 3 ("9-3 curse") |
| **8 rounds** | 3.00% | 3.07% | 10 - 2 |
| **10 rounds** | 0.53% | 0.82% | 11 - 1 |
| **12 rounds** | 0.00% | 0.00% | 12 - 0 |

> [!TIP]
> **Key Finding**: Comebacks by trailing teams are statistically significantly more common in Tier 2 (VCL) than in Tier 1 (VCT). A Chi-Square Test of Independence across all deficits reveals a significant relationship ($p \approx 0.0195$).
> Combined comeback rate for all trailing teams:
> - **Tier 1 (VCT)**: **17.01%** (2,566 / 15,081)
> - **Tier 2 (VCL)**: **18.03%** (2,905 / 16,114)
> This suggests that VCT (T1) matches are slightly more stable once a team secures a halftime lead, while VCL (T2) matches have a higher propensity for momentum swings and comeback victories (e.g. the 9-3 deficit win rate is 9.02% in T2 vs. 8.28% in T1).

## 5. Team Tier Trajectory (T2 → T1 Win Rate Transfer)

For the **56 teams** that played at least 20 maps in both Tier 1 and Tier 2:
* **Linear OLS Fit**: $y = 0.07x + 0.45$
* **$R^2$**: $0.0082$

> [!CAUTION]
> A team's Tier 2 map win rate has almost zero correlation ($R^2 \approx 0.82\%$) with their subsequent win rate in Tier 1. The slope is extremely flat ($0.07$). This indicates a severe step-up in competition, where historical dominance in Tier 2 fails to predict success in the Tier 1 arena.

![Team Trajectory winrate Transfer (n=56)](figures/06_team_trajectory.png)
![Team Trajectory (All Teams, n=180)](figures/06_team_trajectory_all.png)

---

For the **180 teams** that played at least 1 map in both Tier 1 and Tier 2 (unfiltered by map volume, requiring at least 3 players in common):
* **Linear OLS Fit**: $y = 0.33x + 0.33$
* **$R^2$**: $0.0985$

> [!NOTE]
> Lowering the map volume filter to 1 map introduces more variance but captures **180 teams** (including **8 recent VCT teams** like Xi Lai Gaming and Team Heretics). 
> The OLS fit shows a higher $R^2 \approx 9.85\%$ and slope of $0.33$, but this is heavily influenced by high-variance teams with very small map samples (e.g. 1-2 maps) achieving win rates of 1.0 or 0.0.

## Completed Notebooks
All analysis runs are preserved and fully executed in the respective notebooks:
1. [00_validate_labels.ipynb](00_validate_labels.ipynb)
2. [01_overview.ipynb](01_overview.ipynb)
3. [02_map_analysis.ipynb](02_map_analysis.ipynb)
4. [03_player_performance.ipynb](03_player_performance.ipynb)
5. [04_economy.ipynb](04_economy.ipynb)
6. [05_round_level.ipynb](05_round_level.ipynb)
7. [06_team_trajectory.ipynb](06_team_trajectory.ipynb)
