# Data Structure Findings - NFL Streamlit V1

**Date:** 2026-01-13
**Pipeline Version:** 2017-2025 datasets

## S3 Folder Structure

```
nateb-nfl-project/
├── Prod/
│   ├── int/           (Intermediate/internal datasets)
│   ├── core/          (Core processed datasets - USE THESE FOR V1)
│   ├── aux/           (Auxiliary files: logos, injury adjustments)
│   └── documentation/ (Dataset documentation)
```

---

## Core Datasets for V1 (all in `Prod/core/`)

### 1. Game/Team Data

**File:** `int_game_df_team_week_2017_2025.csv` (in `Prod/int/`)
**Grain:** Team-Week (each game appears twice: once per team)
**Columns:** 212 total

**Key EPA Columns:**
- `epa_mean` - Overall EPA
- `run_epa_mean` - Running EPA
- `pass_epa_mean` - Passing EPA
- `against_epa_mean` - Defensive EPA (opponent's EPA)
- `against_run_epa_mean` - Run defense EPA
- `against_pass_epa_mean` - Pass defense EPA

**Betting Columns:**
- `spread` - Point spread
- `spread_cover` - Boolean: covered spread
- `total_line` - Over/under line
- `total_cover` - Boolean: hit over/under
- `total` - Actual total points

**Team Info:**
- `team` - Team name
- `against_team` - Opponent name
- `season`, `week`, `game_id`
- `division`, `conference` - Team's division/conference
- `against_division`, `against_conference` - Opponent's division/conference
- `home_game`, `away_game` - Boolean home/away indicators
- `home_team`, `away_team` - Actual home/away team names

**Scores:**
- `score` - Team's score
- `against_score` - Opponent's score
- `score_differential` - Point differential

**Yards:**
- `run_yards_gained_total` - Total rushing yards
- `pass_yards_gained_total` - Total passing yards
- `against_run_yards_gained_total` - Opp rushing yards allowed
- `against_pass_yards_gained_total` - Opp passing yards allowed

**Opponent Strength (all `opp_against_*` columns):**
- Use these to calculate strength of schedule
- Example: `opp_against_epa_mean` = avg opponent's EPA

---

**File:** `int_game_df_2017_2025.csv` (in `Prod/int/`)
**Grain:** Game (home/away split)
**Columns:** 203 total

**Use for:** Game-level view with `home_*` and `away_*` prefixes
- `home_spread`, `away_spread`
- `home_spread_cover`, `away_spread_cover`
- `home_epa_mean`, `away_epa_mean`
- etc.

---

**File:** `game_df_team_week_shifted_2017_2025.csv`
**Grain:** Team-Week (shifted/lagged for predictions)
**Columns:** Similar to int_game_df_team_week but with lag-1 shift

**Use for:** Predictive features for upcoming matchups (pre-game stats)

---

### 2. Player Grades & Depth Charts

**Weekly Starters - Offense:**
**File:** `weekly_starters_depth_chart_offense_2016_2025.csv`
**Columns:** 761 total (111 grade columns!)

**Key Columns:**
- `gsis_id`, `player_name`, `team`, `season`, `week`
- `position`, `position_general`
- `weekly_depth_level` - Depth chart position for that week
- `offense_pct` - Snap percentage

**Grade Columns:**
- `grades_offense` - Overall offense grade
- `grades_pass` - Passing grade (for QB)
- `grades_run` - Running grade
- `grades_pass_block` - Pass blocking (for OL)
- `grades_run_block` - Run blocking (for OL)
- `grades_receiving` - Receiving grade (for WR/TE)
- Plus 105+ situational grades

---

**Weekly Starters - Defense:**
**File:** `weekly_starters_depth_chart_defense_2016_2025.csv`
**Columns:** 247 total (27 grade columns)

**Grade Columns:**
- `defense_grade` - Overall defense grade
- `coverage_grade` - Coverage grade
- `pass_rush_grade` - Pass rush grade
- `run_defense_grade` - Run defense grade
- `defense_grade_tackle` - Tackling grade
- `man_coverage_grade` - Man coverage
- `zone_coverage_grade` - Zone coverage

---

**Healthy Starters - Offense:**
**File:** `healthy_starters_depth_chart_offense_2016_2025.csv`
**Columns:** Same as weekly_starters

**Purpose:** Shows who SHOULD start if all players were healthy
**Use:** Compare to weekly_starters to measure injury impact

---

**Healthy Starters - Defense:**
**File:** `healthy_starters_depth_chart_defense_2016_2025.csv`
**Columns:** Same as weekly_starters

**Purpose:** Healthy/ideal starters
**Use:** Compare to weekly_starters for injury analysis

---

### 3. Team Logos

**File:** `Team Logos.xlsx` (in `Prod/aux/team_logos_and_wordmarks/`)

**Format:** Excel file with team names and logo URLs/paths

---

## Grade Aggregation Strategy for V1

To get the 12 categories for matchups and team-specific pages:

### Offense (from weekly_starters_depth_chart_offense):

| Category | Position Filter | Grade Column |
|----------|----------------|--------------|
| **Pass Blocking** | `position` IN ('T', 'G', 'C') | `grades_pass_block` |
| **Run Blocking** | `position` IN ('T', 'G', 'C') | `grades_run_block` |
| **QB Passing** | `position` = 'QB' | `grades_pass` |
| **QB Running** | `position` = 'QB' | `grades_run` |
| **Receiving** | `position` IN ('WR', 'TE') | `grades_receiving` |
| **RB Rushing** | `position` = 'RB' | `grades_offense` |

### Defense (from weekly_starters_depth_chart_defense):

| Category | Grade Column |
|----------|--------------|
| **Run Defense** | `run_defense_grade` |
| **Pass Defense** | `coverage_grade` |
| **Overall Defense** | `defense_grade` |
| **Pass Rush** | `pass_rush_grade` |
| **Coverage** | `coverage_grade` (same as pass defense) |

### Special Teams:

| Category | Source |
|----------|--------|
| **Special Teams** | May need to load from separate `player_ratings_special_teams_grades.csv` OR use a grade column from offense/defense files if available |

---

## File Path Updates for V1 Implementation Plan

### OLD (Planned) → NEW (Actual):

| Category | OLD Path | NEW Path |
|----------|----------|----------|
| Team-Week Data | `Prod/core/int_game_df_team_week.csv` | `Prod/int/int_game_df_team_week_2017_2025.csv` |
| Shifted Data | `Prod/core/game_df_team_week_shifted.csv` | `Prod/core/game_df_team_week_shifted_2017_2025.csv` |
| Game Data | `Prod/core/int_game_df.csv` | `Prod/int/int_game_df_2017_2025.csv` |
| Weekly Offense | `Prod/core/weekly_starters_depth_chart_offense.csv` | `Prod/core/weekly_starters_depth_chart_offense_2016_2025.csv` |
| Weekly Defense | `Prod/core/weekly_starters_depth_chart_defense.csv` | `Prod/core/weekly_starters_depth_chart_defense_2016_2025.csv` |
| Healthy Offense | `Prod/core/healthy_starters_depth_chart_offense.csv` | `Prod/core/healthy_starters_depth_chart_offense_2016_2025.csv` |
| Healthy Defense | `Prod/core/healthy_starters_depth_chart_defense.csv` | `Prod/core/healthy_starters_depth_chart_defense_2016_2025.csv` |
| Team Logos | `Prod/aux/Team Logos.xlsx` | `Prod/aux/team_logos_and_wordmarks/Team Logos.xlsx` |

---

## Important Notes

1. **Year Ranges:** All files have year ranges in filenames (2016_2025 or 2017_2025)
2. **Grades Pre-Merged:** Weekly and healthy starter files already have grades merged in
3. **No Separate Player Ratings Needed:** Don't need to load `player_ratings_*_grades.csv` separately - grades are in depth chart files
4. **Division/Conference Filters:** Available in `int_game_df_team_week` via `division` and `conference` columns
5. **Home/Away Indicators:** Multiple ways to identify: `home_game`/`away_game` booleans, or `home_team`/`away_team` columns
6. **Opponent Stats:** All `against_*` columns provide opponent performance (useful for SOS calculations)

---

## Data Validation Checklist

- [x] Confirmed EPA columns exist (`epa_mean`, `run_epa_mean`, `pass_epa_mean`)
- [x] Confirmed defensive EPA columns (`against_epa_mean`, etc.)
- [x] Confirmed spread/betting columns (`spread`, `spread_cover`, `total_cover`)
- [x] Confirmed score columns (`score`, `against_score`, `score_differential`)
- [x] Confirmed division/conference columns (`division`, `conference`)
- [x] Confirmed home/away indicators (`home_game`, `away_game`)
- [x] Confirmed weekly starters files exist with grades
- [x] Confirmed healthy starters files exist with grades
- [x] Confirmed Team Logos.xlsx location
- [x] Confirmed grade columns in depth chart files

---

## Next Steps for Implementation

1. Update all data loader functions with correct file paths (add `_2017_2025` or `_2016_2025` suffixes)
2. Update column name references in data processing functions
3. Implement grade aggregation logic using the tables above
4. Test data loading with actual files
5. Verify division/conference filtering works
6. Verify logo loading from Excel file