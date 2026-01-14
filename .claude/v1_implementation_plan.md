# NFL Streamlit V1 Implementation Plan

## Project Overview

Building a Streamlit-based NFL betting analytics dashboard with 3 main pages:
1. **Team Performance** - League-wide team comparison with EPA scatter plots
2. **Matchups** - Head-to-head comparison for upcoming games with player grades
3. **Team Specific** - Single team deep dive with injury impact analysis

**Key Design Principles:**
- Start fresh (existing V0 files to be deleted/replaced)
- Reuse proven utility patterns from V0
- Use V1-approved datasets only (no `training_data_full_game` or `game_df_team_week_averages_3_week_sequence`)
- Implement team logos on scatter plots
- Focus on clean, maintainable code with proper caching

---

## Data Architecture

### Core Datasets (V1 Approved) - ACTUAL FILE PATHS

**Full documentation:** See `.claude/data_structure_findings.md` for detailed column listings

| Dataset | S3 Path | Grain | Columns | Key Fields |
|---------|---------|-------|---------|------------|
| Team-Week Data | `Prod/int/int_game_df_team_week_2017_2025.csv` | Team-Week | 212 | `team`, `against_team`, `season`, `week`, `epa_mean`, `run_epa_mean`, `pass_epa_mean`, `against_epa_mean`, `against_run_epa_mean`, `against_pass_epa_mean`, `spread`, `spread_cover`, `total_cover`, `score`, `against_score`, `division`, `conference`, `home_game`, `away_game` |
| Shifted Data | `Prod/core/game_df_team_week_shifted_2017_2025.csv` | Team-Week | ~200 | Same as above but lag-1 shifted for predictions |
| Game Data | `Prod/int/int_game_df_2017_2025.csv` | Game | 203 | `game_id`, `home_team`, `away_team`, `home_spread`, `away_spread`, home/away prefixed stats |
| Weekly Offense | `Prod/core/weekly_starters_depth_chart_offense_2016_2025.csv` | Player-Week | 761 | `gsis_id`, `player_name`, `team`, `season`, `week`, `position`, `grades_offense`, `grades_pass`, `grades_run`, `grades_pass_block`, `grades_run_block`, `grades_receiving`, `offense_pct` |
| Weekly Defense | `Prod/core/weekly_starters_depth_chart_defense_2016_2025.csv` | Player-Week | 247 | `gsis_id`, `player_name`, `team`, `season`, `week`, `position`, `defense_grade`, `coverage_grade`, `pass_rush_grade`, `run_defense_grade`, `defense_pct` |
| Healthy Offense | `Prod/core/healthy_starters_depth_chart_offense_2016_2025.csv` | Player-Week | 761 | Same as weekly_starters |
| Healthy Defense | `Prod/core/healthy_starters_depth_chart_defense_2016_2025.csv` | Player-Week | 247 | Same as weekly_starters |
| Team Logos | `Prod/aux/team_logos_and_wordmarks/Team Logos.xlsx` | Team | TBD | Excel file with logo URLs/paths |

### Data Loading Strategy

**Pattern:** Reuse V0's `@st.cache_data(ttl=3600)` pattern with 1-hour TTL
- Keep: `get_s3_client()` with `@st.cache_resource`
- Keep: `load_csv_from_s3()` with retry logic
- Create: V1-specific loader functions for each dataset

**Helper Functions to Reuse (No Changes):**
- `get_available_teams(df)`
- `get_available_seasons(df)`
- `get_available_weeks(df, season=None)`
- `get_current_week(training_data)`

### Calculation Logic

**Betting Records:**
- Reuse: `calculate_ats_record()` - Works with `spread_cover` flag
- Reuse: `calculate_over_under_record()` - Works with `total_cover` flag
- Reuse: `calculate_situational_ats()` - Handles home/away, favorite/underdog splits

**EPA Metrics:**
- Source: `int_game_df_team_week.csv` contains EPA columns directly
- Season aggregates: Calculate mean by team-season
- Opponent strength: Use `opp_against_*` columns for past opponent averages

**Injury Impact:**
- Compare: `healthy_starters_depth_chart_*` vs `weekly_starters_depth_chart_*`
- Calculate: Grade difference by position group for each week
- Aggregate: Sum differences across 12 categories

---

## File Structure

```
NFL_streamlit/
├── .claude/
│   ├── instructions.md (existing)
│   ├── commit-rules.md (existing)
│   └── v1_implementation_plan.md (NEW - saved copy of this plan)
├── app.py (REBUILD - V1 home page)
├── pages/
│   ├── 1_Team_Performance.py (REBUILD)
│   ├── 2_Matchups.py (NEW)
│   └── 3_Team_Specific.py (NEW)
├── utils/
│   ├── __init__.py (keep)
│   ├── data_loader.py (REFACTOR - V1 loaders)
│   ├── data_processor.py (REFACTOR - keep reusable functions)
│   └── plotting.py (NEW - chart creation utilities)
├── components/
│   ├── __init__.py (keep)
│   ├── filters.py (REFACTOR - keep core filters)
│   └── metrics_cards.py (NEW - reusable metric displays)
├── assets/
│   └── team_logos/ (NEW - cached logo images)
├── secrets.py (existing)
├── streamlit_environment.yml (NEW - Windows environment)
├── streamlit_environment_mac.yml (existing)
├── requirements.txt (NEW - pip alternative)
└── README.md (CREATE)
```

---

## Page Specifications

### Page 1: Team Performance (League-Wide Comparison)

**URL:** `/` (home page via app.py)

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│  🏈 NFL Team Performance Comparison                 │
│  Compare all teams across EPA metrics               │
└─────────────────────────────────────────────────────┘

┌──SIDEBAR───────────────┐  ┌─────MAIN CONTENT─────────┐
│ Filters:                │  │  2x2 Grid of Scatter Plots│
│ - Season: [dropdown]    │  │  ┌─────────┬─────────┐   │
│ - Week: [dropdown]      │  │  │  Chart1 │ Chart2  │   │
│ - Division/Conf:        │  │  │  Off vs │ Pass vs │   │
│   [dropdown with All]   │  │  │  Def EPA│ Run EPA │   │
│                         │  │  ├─────────┼─────────┤   │
│                         │  │  │  Chart3 │ Chart4  │   │
│                         │  │  │  Def EPA│ Strength│   │
│                         │  │  │  Detail │ Sched   │   │
│                         │  │  └─────────┴─────────┘   │
└─────────────────────────┘  └──────────────────────────┘
```

**Charts (All Plotly scatter plots with team logos):**

1. **Offensive EPA vs Defensive EPA**
   - X-axis: Defensive EPA (inverted)
   - Y-axis: Offensive EPA
   - Markers: Team logos
   - Quadrant lines: X=0, Y=0
   - Hover: Team name, exact values

2. **Pass EPA vs Run EPA (Offense)**
   - X-axis: Run EPA (offense)
   - Y-axis: Pass EPA (offense)
   - Markers: Team logos
   - Quadrant indicators

3. **Pass EPA Allowed vs Run EPA Allowed (Defense)**
   - X-axis: Run EPA allowed (inverted)
   - Y-axis: Pass EPA allowed (inverted)
   - Markers: Team logos
   - Lower-left = best defense

4. **Strength of Schedule**
   - X-axis: Avg opponent defensive EPA (inverted)
   - Y-axis: Avg opponent offensive EPA
   - Markers: Team logos
   - Shows difficulty of schedule

**Data Flow:**
1. Load `int_game_df_team_week.csv`
2. Filter by season/week
3. Calculate team season aggregates:
   - Mean offensive EPA, defensive EPA
   - Mean pass EPA, run EPA (offense)
   - Mean pass EPA allowed, run EPA allowed (defense)
4. Calculate opponent averages from `opp_against_*` columns
5. Filter by division/conference if selected
6. Load team logos
7. Render 4 scatter plots

**Components Needed:**
- Filter: Season, Week, Division/Conference dropdowns
- Chart function: `create_epa_scatter(df, x_col, y_col, title, invert_x, invert_y, logos_df)`
- Logo loader: `load_team_logos()` - reads Team Logos.xlsx, returns mapping

---

### Page 2: Matchups (Head-to-Head Comparison)

**URL:** `/pages/2_Matchups.py`

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│  🏈 NFL Matchup Analysis                            │
│  Compare two teams head-to-head                     │
└─────────────────────────────────────────────────────┘

┌──SIDEBAR───────────────┐  ┌─────MAIN CONTENT─────────┐
│ Team Selection:         │  │  ┌─TEAM A─┐  ┌─TEAM B─┐ │
│ - Home Team: [dropdown] │  │  │ Logo   │  │ Logo   │ │
│ - Away Team: [dropdown] │  │  │ Record │  │ Record │ │
│                         │  │  │ ATS    │  │ ATS    │ │
│ - OR -                  │  │  │ O/U    │  │ O/U    │ │
│ - Upcoming Matchup:     │  │  └────────┘  └────────┘ │
│   [dropdown]            │  │                          │
│                         │  │  Performance Metrics     │
│                         │  │  [Side-by-side table]    │
│                         │  │                          │
│                         │  │  Weekly EPA Trend Chart  │
│                         │  │  [Both teams overlay]    │
│                         │  │                          │
│                         │  │  Player Grades Comparison│
│                         │  │  [12-category table]     │
└─────────────────────────┘  └──────────────────────────┘
```

**Sections:**

1. **Team Header Cards (Side-by-Side)**
   - Team logo
   - Overall record (W-L)
   - ATS record
   - O/U record
   - Record as favorite
   - Record as underdog
   - Home/road record

2. **Performance Metrics Table**
   | Metric | Team A | Team B |
   |--------|--------|--------|
   | Avg Points Scored | X | Y |
   | Avg Points Allowed | X | Y |
   | Avg Offensive EPA | X | Y |
   | Avg Defensive EPA | X | Y |
   | Avg Run Yards/Game | X | Y |
   | Avg Pass Yards/Game | X | Y |
   | Avg Opp Offensive EPA | X | Y |
   | Avg Opp Defensive EPA | X | Y |

3. **Weekly EPA Trend Chart**
   - X-axis: Week number
   - Y-axis: Overall team EPA
   - Two lines: Team A (blue), Team B (red)
   - Hover: Week, EPA value

4. **Player Grades Comparison (12 Categories)**
   | Position Group | Team A Grade | Team B Grade | Advantage |
   |----------------|--------------|--------------|-----------|
   | Pass Blocking | 75.2 | 68.1 | Team A +7.1 |
   | Run Blocking | 72.5 | 74.8 | Team B +2.3 |
   | QB Passing | 85.3 | 78.9 | Team A +6.4 |
   | QB Running | 65.2 | 70.1 | Team B +4.9 |
   | Receiving | 78.5 | 81.2 | Team B +2.7 |
   | RB Rushing | 72.8 | 69.5 | Team A +3.3 |
   | Run Defense | 68.9 | 72.1 | Team B +3.2 |
   | Pass Defense | 74.5 | 70.2 | Team A +4.3 |
   | Overall Defense | 71.2 | 68.8 | Team A +2.4 |
   | Special Teams | 66.5 | 69.8 | Team B +3.3 |
   | Pass Rush | 75.8 | 72.4 | Team A +3.4 |
   | Coverage | 70.2 | 68.5 | Team A +1.7 |

   - Color coding: Green = advantage, red = disadvantage
   - Grades: Aggregate from `weekly_starters_depth_chart_*` for current/latest week

**Data Flow:**
1. Load `int_game_df_team_week.csv` and `game_df_team_week_shifted.csv`
2. Get selected teams (home/away or from matchup dropdown)
3. Filter data for both teams
4. Calculate all aggregate metrics (season averages)
5. Calculate situational records (home/away, favorite/underdog, ATS, O/U)
6. Load weekly starter grades for both teams (latest week or selected week)
7. Aggregate grades by position group (12 categories)
8. Render components

**Components Needed:**
- Filter: Team selectors or matchup dropdown
- Metrics card: `render_team_comparison_card(team_data, logo)`
- Comparison table: `render_metrics_comparison_table(team_a_data, team_b_data)`
- Chart: `create_weekly_epa_comparison_chart(team_a_weeks, team_b_weeks)`
- Grades table: `render_player_grades_comparison(team_a_grades, team_b_grades)`

**Player Grade Aggregation Logic:**
```python
def aggregate_team_grades_by_category(weekly_starters_off, weekly_starters_def, team, week):
    """
    Aggregate player grades into 12 categories

    Returns: dict with keys:
    - pass_blocking, run_blocking, qb_passing, qb_running, receiving, rb_rushing,
      run_defense, pass_defense, overall_defense, special_teams, pass_rush, coverage
    """
    # Offense categories from weekly_starters_depth_chart_offense
    # Defense categories from weekly_starters_depth_chart_defense
    # Filter by team and week, take mean of relevant grade columns
```

---

### Page 3: Team Specific (Single Team Deep Dive)

**URL:** `/pages/3_Team_Specific.py`

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│  🏈 Team Deep Dive - [TEAM NAME]                    │
│  Analyze single team performance and injury impact  │
└─────────────────────────────────────────────────────┘

┌──SIDEBAR───────────────┐  ┌─────MAIN CONTENT─────────┐
│ Filters:                │  │  Key Metrics Cards       │
│ - Team: [dropdown]      │  │  ┌────┬────┬────┬────┐  │
│ - Season: [dropdown]    │  │  │W-L │ATS │O/U │EPA │  │
│                         │  │  └────┴────┴────┴────┘  │
│                         │  │                          │
│                         │  │  Performance Stats Table │
│                         │  │  [Yards, Points, etc.]   │
│                         │  │                          │
│                         │  │  Weekly EPA Trend Chart  │
│                         │  │  [Single team over time] │
│                         │  │                          │
│                         │  │  Injury Impact Analysis  │
│                         │  │  ┌──────────────────┐   │
│                         │  │  │ Weekly dropdown  │   │
│                         │  │  │ Grade Diff Chart │   │
│                         │  │  │ Grade Diff Table │   │
│                         │  │  └──────────────────┘   │
└─────────────────────────┘  └──────────────────────────┘
```

**Sections:**

1. **Key Metrics Cards (4 columns)**
   - Overall Record (W-L)
   - ATS Record
   - O/U Record
   - Avg EPA (Off + Def)

2. **Performance Stats Table**
   | Metric | Value |
   |--------|-------|
   | Avg Points Scored | X |
   | Avg Points Allowed | Y |
   | Avg Offensive EPA | X |
   | Avg Defensive EPA | Y |
   | Avg Run Yards/Game | X |
   | Avg Pass Yards/Game | Y |
   | Record as Favorite | X-Y |
   | Record as Underdog | X-Y |
   | Home Record | X-Y |
   | Road Record | X-Y |

3. **Weekly EPA Trend Chart**
   - X-axis: Week number
   - Y-axis: Overall team EPA
   - Single line for selected team
   - Show full season progression

4. **Injury Impact Analysis**

   **A. Week Selector Dropdown**
   - Choose specific week or "All Weeks"

   **B. Grade Difference Chart (LINE CHART - New Feature)**
   - X-axis: Week number
   - Y-axis: Total grade difference (sum across all 12 categories)
   - Shows aggregate injury impact over time
   - Color zones: Red (negative impact), yellow (moderate), green (minimal)
   - This answers user's question: "weekly chart showing the drop in ratings"

   **C. Grade Difference Table (for selected week or season aggregate)**
   | Position Group | Healthy Grade | Weekly Grade | Difference | Status |
   |----------------|---------------|--------------|------------|--------|
   | Pass Blocking | 75.2 | 68.1 | -7.1 | 🔴 |
   | Run Blocking | 72.5 | 74.8 | +2.3 | 🟢 |
   | QB Passing | 85.3 | 78.9 | -6.4 | 🔴 |
   | ... | ... | ... | ... | ... |

   - Color coding: 🔴 = worse, 🟢 = better, ⚪ = same
   - Difference = Weekly - Healthy (negative = injury impact)

**Data Flow:**
1. Load `int_game_df_team_week.csv`
2. Load `healthy_starters_depth_chart_offense.csv` and `_defense.csv`
3. Load `weekly_starters_depth_chart_offense.csv` and `_defense.csv`
4. Filter by selected team and season
5. Calculate all aggregate metrics
6. For each week:
   - Aggregate healthy starter grades by 12 categories
   - Aggregate weekly starter grades by 12 categories
   - Calculate difference
7. Render metrics, table, charts
8. Render injury impact section with week selector

**Components Needed:**
- Filter: Team dropdown, Season dropdown
- Metrics cards: `render_key_metrics(team_data)`
- Stats table: `render_team_stats_table(team_data)`
- Chart: `create_weekly_epa_trend(team_weeks)`
- Chart: `create_injury_impact_weekly_chart(grade_diffs_by_week)` - NEW
- Table: `render_injury_impact_table(healthy_grades, weekly_grades, week)`

---

## Technical Implementation Details

### 1. Data Loading (`utils/data_loader.py`)

**Reuse from V0 (no changes):**
```python
@st.cache_resource
def get_s3_client():
    # Existing implementation - KEEP AS-IS

def load_csv_from_s3(file_key, max_retries=3):
    # Existing implementation - KEEP AS-IS
```

**New V1 Loaders (WITH CORRECT FILE PATHS):**
```python
@st.cache_data(ttl=3600)
def load_int_game_df_team_week():
    """Load team-week performance data (non-shifted)"""
    df = load_csv_from_s3('Prod/int/int_game_df_team_week_2017_2025.csv')
    if df is not None:
        # Type conversions
        if 'game_date' in df.columns:
            df['game_date'] = pd.to_datetime(df['game_date'], errors='coerce')
        numeric_cols = ['season', 'week', 'score_differential', 'spread', 'total_line']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

@st.cache_data(ttl=3600)
def load_game_df_team_week_shifted():
    """Load team-week pre-game data (shifted for predictions)"""
    df = load_csv_from_s3('Prod/core/game_df_team_week_shifted_2017_2025.csv')
    if df is not None:
        if 'game_date' in df.columns:
            df['game_date'] = pd.to_datetime(df['game_date'], errors='coerce')
        numeric_cols = ['season', 'week']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

@st.cache_data(ttl=3600)
def load_int_game_df():
    """Load game-level data"""
    df = load_csv_from_s3('Prod/int/int_game_df_2017_2025.csv')
    if df is not None:
        if 'game_date' in df.columns:
            df['game_date'] = pd.to_datetime(df['game_date'], errors='coerce')
        numeric_cols = ['season', 'week']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

@st.cache_data(ttl=3600)
def load_weekly_starters(side='offense'):
    """Load weekly starter depth charts with grades pre-merged"""
    df = load_csv_from_s3(f'Prod/core/weekly_starters_depth_chart_{side}_2016_2025.csv')
    if df is not None:
        numeric_cols = ['season', 'week']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

@st.cache_data(ttl=3600)
def load_healthy_starters(side='offense'):
    """Load healthy starter depth charts with grades pre-merged"""
    df = load_csv_from_s3(f'Prod/core/healthy_starters_depth_chart_{side}_2016_2025.csv')
    if df is not None:
        numeric_cols = ['season', 'week']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

@st.cache_data(ttl=3600)
def load_team_logos():
    """Load team logo mappings from Excel"""
    import openpyxl  # Required for Excel files
    df = load_csv_from_s3('Prod/aux/team_logos_and_wordmarks/Team Logos.xlsx')
    # Note: load_csv_from_s3 needs to be updated to handle Excel files
    # Return as dict: {team_name: logo_url}
    return df.set_index('team_name')['logo_url'].to_dict()
```

**Keep from V0:**
```python
def get_available_teams(df):
    # KEEP AS-IS

def get_available_seasons(df):
    # KEEP AS-IS

def get_available_weeks(df, season=None):
    # KEEP AS-IS
```

---

### 2. Data Processing (`utils/data_processor.py`)

**Reuse from V0 (no changes):**
```python
def get_current_week(training_data):
    # KEEP AS-IS

def filter_by_season_week(df, seasons=None, weeks=None, teams=None):
    # KEEP AS-IS

def calculate_ats_record(training_data, team=None, location=None):
    # KEEP AS-IS

def calculate_over_under_record(training_data, team=None):
    # KEEP AS-IS

def calculate_situational_ats(training_data):
    # KEEP AS-IS
```

**New V1 Functions:**
```python
def calculate_team_season_aggregates(df, team, season):
    """
    Calculate season-level aggregates for a team

    Returns dict with:
    - avg_offensive_epa, avg_defensive_epa
    - avg_pass_epa, avg_run_epa
    - avg_pass_epa_allowed, avg_run_epa_allowed
    - avg_points_scored, avg_points_allowed
    - avg_run_yards, avg_pass_yards
    - avg_opp_offensive_epa, avg_opp_defensive_epa
    """
    team_data = df[(df['team'] == team) & (df['season'] == season)]

    aggregates = {
        'avg_offensive_epa': team_data['epa_offense'].mean(),
        'avg_defensive_epa': team_data['epa_defense'].mean(),
        # ... calculate all metrics
    }
    return aggregates

def calculate_records_by_situation(df, team, season):
    """
    Calculate W-L records by situation

    Returns dict with:
    - overall_record, home_record, away_record
    - favorite_record, underdog_record
    """
    team_data = df[(df['team'] == team) & (df['season'] == season)]

    # Use existing helpers + custom logic
    # ... implementation

    return records

def aggregate_player_grades_by_category(weekly_starters_off, weekly_starters_def,
                                        team, week, season):
    """
    Aggregate player grades into 12 categories for a specific team/week

    Args:
        weekly_starters_off: Weekly offense depth chart DataFrame
        weekly_starters_def: Weekly defense depth chart DataFrame
        team: Team name
        week: Week number
        season: Season year

    Returns:
        dict with 12 keys (pass_blocking, run_blocking, etc.) and mean grades
    """
    off_data = weekly_starters_off[
        (weekly_starters_off['team'] == team) &
        (weekly_starters_off['week'] == week) &
        (weekly_starters_off['season'] == season)
    ]

    def_data = weekly_starters_def[
        (weekly_starters_def['team'] == team) &
        (weekly_starters_def['week'] == week) &
        (weekly_starters_def['season'] == season)
    ]

    grades = {
        # Offense
        'pass_blocking': off_data[off_data['position'].isin(['T', 'G', 'C'])]['grades_pass_block'].mean(),
        'run_blocking': off_data[off_data['position'].isin(['T', 'G', 'C'])]['grades_run_block'].mean(),
        'qb_passing': off_data[off_data['position'] == 'QB']['grades_pass'].mean(),
        'qb_running': off_data[off_data['position'] == 'QB']['grades_run'].mean(),
        'receiving': off_data[off_data['position'].isin(['WR', 'TE'])]['grades_receiving'].mean(),
        'rb_rushing': off_data[off_data['position'] == 'RB']['grades_offense'].mean(),

        # Defense
        'run_defense': def_data['run_defense_grade'].mean(),
        'pass_defense': def_data['coverage_grade'].mean(),
        'overall_defense': def_data['defense_grade'].mean(),
        'special_teams': off_data['grades_special_teams'].mean(),  # May need separate dataset
        'pass_rush': def_data['pass_rush_grade'].mean(),
        'coverage': def_data['coverage_grade'].mean(),
    }

    return grades

def calculate_injury_impact_by_week(healthy_off, healthy_def, weekly_off, weekly_def,
                                    team, season):
    """
    Calculate grade differences across all weeks for injury impact analysis

    Returns:
        DataFrame with columns: week, category, healthy_grade, weekly_grade, difference
    """
    weeks = weekly_off[weekly_off['team'] == team]['week'].unique()

    impact_data = []
    for week in weeks:
        healthy_grades = aggregate_player_grades_by_category(
            healthy_off, healthy_def, team, week, season
        )
        weekly_grades = aggregate_player_grades_by_category(
            weekly_off, weekly_def, team, week, season
        )

        for category in healthy_grades.keys():
            impact_data.append({
                'week': week,
                'category': category,
                'healthy_grade': healthy_grades[category],
                'weekly_grade': weekly_grades[category],
                'difference': weekly_grades[category] - healthy_grades[category]
            })

    return pd.DataFrame(impact_data)
```

---

### 3. Plotting Utilities (`utils/plotting.py` - NEW FILE)

```python
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image
import requests
from io import BytesIO

def create_epa_scatter(df, x_col, y_col, title, invert_x=False, invert_y=False,
                       logos_dict=None, team_col='team'):
    """
    Create scatter plot with team logos as markers

    Args:
        df: DataFrame with team data
        x_col: Column for x-axis
        y_col: Column for y-axis
        title: Chart title
        invert_x: Invert x-axis (for defensive metrics)
        invert_y: Invert y-axis (for defensive metrics)
        logos_dict: Dict mapping team names to logo URLs
        team_col: Column name for team identifier

    Returns:
        plotly.graph_objects.Figure
    """
    fig = go.Figure()

    if logos_dict:
        # Use add_layout_image for each team logo
        for idx, row in df.iterrows():
            team = row[team_col]
            x_val = row[x_col]
            y_val = row[y_col]
            logo_url = logos_dict.get(team)

            if logo_url:
                # Add logo image at position
                fig.add_layout_image(
                    dict(
                        source=logo_url,
                        xref="x",
                        yref="y",
                        x=x_val,
                        y=y_val,
                        sizex=0.05,  # Adjust size
                        sizey=0.05,
                        xanchor="center",
                        yanchor="middle"
                    )
                )
    else:
        # Fallback to text markers
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode='markers+text',
            text=df[team_col],
            textposition='top center',
            marker=dict(size=10)
        ))

    # Add quadrant lines
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)

    # Axis configuration
    fig.update_xaxes(
        title=x_col.replace('_', ' ').title(),
        autorange='reversed' if invert_x else True
    )
    fig.update_yaxes(
        title=y_col.replace('_', ' ').title(),
        autorange='reversed' if invert_y else True
    )

    fig.update_layout(
        title=title,
        hovermode='closest',
        height=500
    )

    return fig

def create_weekly_epa_trend(df, team, season, team_col='team', week_col='week',
                            epa_col='epa_total'):
    """
    Create line chart showing weekly EPA trend for single team
    """
    team_data = df[(df[team_col] == team) & (df['season'] == season)].sort_values(week_col)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=team_data[week_col],
        y=team_data[epa_col],
        mode='lines+markers',
        name=team,
        line=dict(width=2)
    ))

    fig.update_layout(
        title=f"{team} Weekly EPA Trend - {season}",
        xaxis_title="Week",
        yaxis_title="EPA",
        hovermode='x unified',
        height=400
    )

    return fig

def create_weekly_epa_comparison(df, team_a, team_b, season, team_col='team',
                                 week_col='week', epa_col='epa_total'):
    """
    Create line chart comparing weekly EPA for two teams
    """
    team_a_data = df[(df[team_col] == team_a) & (df['season'] == season)].sort_values(week_col)
    team_b_data = df[(df[team_col] == team_b) & (df['season'] == season)].sort_values(week_col)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=team_a_data[week_col],
        y=team_a_data[epa_col],
        mode='lines+markers',
        name=team_a,
        line=dict(color='blue', width=2)
    ))

    fig.add_trace(go.Scatter(
        x=team_b_data[week_col],
        y=team_b_data[epa_col],
        mode='lines+markers',
        name=team_b,
        line=dict(color='red', width=2)
    ))

    fig.update_layout(
        title=f"Weekly EPA Comparison - {season}",
        xaxis_title="Week",
        yaxis_title="EPA",
        hovermode='x unified',
        height=400
    )

    return fig

def create_injury_impact_chart(impact_df):
    """
    Create line chart showing aggregate injury impact across weeks

    Args:
        impact_df: DataFrame with columns: week, category, difference

    Returns:
        plotly.graph_objects.Figure
    """
    # Aggregate total difference by week
    weekly_impact = impact_df.groupby('week')['difference'].sum().reset_index()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=weekly_impact['week'],
        y=weekly_impact['difference'],
        mode='lines+markers',
        name='Total Grade Impact',
        line=dict(width=3),
        fill='tozeroy',
        fillcolor='rgba(255, 0, 0, 0.2)'
    ))

    # Add horizontal line at 0
    fig.add_hline(y=0, line_dash="dash", line_color="gray")

    fig.update_layout(
        title="Weekly Injury Impact (Grade Difference: Healthy vs Weekly Starters)",
        xaxis_title="Week",
        yaxis_title="Total Grade Difference",
        hovermode='x unified',
        height=400
    )

    return fig
```

---

### 4. Component Utilities (`components/metrics_cards.py` - NEW FILE)

```python
import streamlit as st

def render_key_metrics(metrics_dict, cols=4):
    """
    Render key metrics in columns

    Args:
        metrics_dict: Dict with {label: value} pairs
        cols: Number of columns
    """
    columns = st.columns(cols)
    items = list(metrics_dict.items())

    for idx, (label, value) in enumerate(items):
        with columns[idx % cols]:
            st.metric(label, value)

def render_team_comparison_card(team_name, team_data, logo_url=None):
    """
    Render team header card with logo and key records

    Args:
        team_name: Team name
        team_data: Dict with record information
        logo_url: Optional team logo URL
    """
    if logo_url:
        st.image(logo_url, width=100)

    st.subheader(team_name)

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Record", team_data['overall_record'])
        st.metric("ATS", team_data['ats_record'])
        st.metric("Home", team_data['home_record'])

    with col2:
        st.metric("O/U", team_data['ou_record'])
        st.metric("Favorite", team_data['favorite_record'])
        st.metric("Road", team_data['road_record'])

def render_metrics_comparison_table(team_a_name, team_a_data, team_b_name, team_b_data):
    """
    Render side-by-side metrics comparison table

    Args:
        team_a_name: Name of team A
        team_a_data: Dict with metrics for team A
        team_b_name: Name of team B
        team_b_data: Dict with metrics for team B
    """
    import pandas as pd

    comparison_data = []

    metrics_keys = [
        ('avg_points_scored', 'Avg Points Scored'),
        ('avg_points_allowed', 'Avg Points Allowed'),
        ('avg_offensive_epa', 'Avg Offensive EPA'),
        ('avg_defensive_epa', 'Avg Defensive EPA'),
        ('avg_run_yards', 'Avg Run Yards/Game'),
        ('avg_pass_yards', 'Avg Pass Yards/Game'),
        ('avg_opp_offensive_epa', 'Avg Opp Offensive EPA'),
        ('avg_opp_defensive_epa', 'Avg Opp Defensive EPA'),
    ]

    for key, label in metrics_keys:
        comparison_data.append({
            'Metric': label,
            team_a_name: team_a_data.get(key, 'N/A'),
            team_b_name: team_b_data.get(key, 'N/A')
        })

    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_player_grades_comparison(team_a_name, team_a_grades, team_b_name, team_b_grades):
    """
    Render player grades comparison table with 12 categories

    Args:
        team_a_name: Name of team A
        team_a_grades: Dict with 12 category grades for team A
        team_b_name: Name of team B
        team_b_grades: Dict with 12 category grades for team B
    """
    import pandas as pd

    categories = [
        ('pass_blocking', 'Pass Blocking'),
        ('run_blocking', 'Run Blocking'),
        ('qb_passing', 'QB Passing'),
        ('qb_running', 'QB Running'),
        ('receiving', 'Receiving'),
        ('rb_rushing', 'RB Rushing'),
        ('run_defense', 'Run Defense'),
        ('pass_defense', 'Pass Defense'),
        ('overall_defense', 'Overall Defense'),
        ('special_teams', 'Special Teams'),
        ('pass_rush', 'Pass Rush'),
        ('coverage', 'Coverage'),
    ]

    comparison_data = []

    for key, label in categories:
        a_grade = team_a_grades.get(key, 0)
        b_grade = team_b_grades.get(key, 0)
        diff = a_grade - b_grade

        if diff > 0:
            advantage = f"{team_a_name} +{diff:.1f}"
        elif diff < 0:
            advantage = f"{team_b_name} +{abs(diff):.1f}"
        else:
            advantage = "Even"

        comparison_data.append({
            'Position Group': label,
            f'{team_a_name} Grade': f"{a_grade:.1f}",
            f'{team_b_name} Grade': f"{b_grade:.1f}",
            'Advantage': advantage
        })

    df = pd.DataFrame(comparison_data)

    # Style with color coding (optional - requires st.dataframe styling)
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_injury_impact_table(healthy_grades, weekly_grades, category_labels):
    """
    Render injury impact table showing healthy vs weekly starter grades

    Args:
        healthy_grades: Dict with 12 category grades (healthy starters)
        weekly_grades: Dict with 12 category grades (weekly starters)
        category_labels: Dict mapping keys to display labels
    """
    import pandas as pd

    impact_data = []

    for key, label in category_labels.items():
        healthy = healthy_grades.get(key, 0)
        weekly = weekly_grades.get(key, 0)
        diff = weekly - healthy

        if diff < -2:
            status = "🔴"
        elif diff > 2:
            status = "🟢"
        else:
            status = "⚪"

        impact_data.append({
            'Position Group': label,
            'Healthy Grade': f"{healthy:.1f}",
            'Weekly Grade': f"{weekly:.1f}",
            'Difference': f"{diff:+.1f}",
            'Status': status
        })

    df = pd.DataFrame(impact_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
```

---

### 5. Filter Components (`components/filters.py` - REFACTOR)

**Keep from V0:**
- `render_team_selector()`
- `render_season_week_filters()`

**New V1 Filters:**
```python
def render_division_conference_filter(df, key="div_conf_filter"):
    """
    Render division/conference filter dropdown

    Args:
        df: DataFrame with 'division' and 'conference' columns
        key: Unique key for widget

    Returns:
        Selected filter value (e.g., "All", "NFC East", "AFC")
    """
    options = ["All Teams"]

    # Add conferences
    if 'conference' in df.columns:
        conferences = df['conference'].dropna().unique().tolist()
        options.extend(sorted(conferences))

    # Add divisions
    if 'division' in df.columns:
        divisions = df['division'].dropna().unique().tolist()
        options.extend(sorted(divisions))

    selected = st.selectbox("Filter by Division/Conference", options, key=key)

    return selected

def render_matchup_selector(df, key="matchup_select"):
    """
    Render matchup dropdown for upcoming games

    Args:
        df: DataFrame with game data (home_team, away_team, week)
        key: Unique key for widget

    Returns:
        Tuple of (home_team, away_team)
    """
    # Get unique matchups
    matchups = df[['home_team', 'away_team', 'week']].drop_duplicates()
    matchup_options = [
        f"{row['away_team']} @ {row['home_team']} (Week {row['week']})"
        for _, row in matchups.iterrows()
    ]

    selected = st.selectbox("Select Matchup", matchup_options, key=key)

    # Parse selection
    if selected:
        parts = selected.split(" @ ")
        away_team = parts[0]
        home_parts = parts[1].split(" (Week ")
        home_team = home_parts[0]
        return home_team, away_team

    return None, None
```

---

### 6. Caching Strategy

**Resource Caching (Connection):**
- `@st.cache_resource` for S3 client
- Persists across reruns and user sessions
- Only clears on app restart

**Data Caching (DataFrames):**
- `@st.cache_data(ttl=3600)` for all data loaders
- 1-hour TTL ensures fresh data
- Clears automatically after timeout

**Session State (Filters):**
- Use `st.session_state` for filter persistence within a user session
- Store: selected team, season, week
- Prevents resetting on rerun

---

### 7. Error Handling Pattern

**Wrap all data operations:**
```python
with st.spinner("Loading data..."):
    try:
        data = load_int_game_df_team_week()

        if data is None or data.empty:
            st.error("Failed to load data. Please check your S3 connection.")
            st.stop()

        # Success - proceed

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Please ensure your AWS credentials are correct.")
        st.stop()
```

**For missing columns:**
```python
if 'epa_offense' not in df.columns:
    st.warning("EPA offense data not available in dataset.")
    # Graceful degradation or skip feature
```

---

## Implementation Checklist

### Phase 1: Setup & Infrastructure
- [ ] Delete existing pages (1_Team_Performance.py, 3_Betting_Analysis.py)
- [ ] Create new file structure (plotting.py, metrics_cards.py)
- [ ] Update `utils/data_loader.py` with V1 loaders
- [ ] Update `utils/data_processor.py` with V1 functions
- [ ] Add openpyxl to `streamlit_environment.yml` for Excel reading
- [ ] Test S3 connection and data loading

### Phase 2: Team Performance Page (Page 1)
- [ ] Implement `load_team_logos()` function
- [ ] Implement `create_epa_scatter()` with logo support
- [ ] Build `app.py` with 4 scatter plots
- [ ] Add division/conference filter
- [ ] Test with sample data
- [ ] Verify logo rendering
- [ ] Add error handling

### Phase 3: Matchups Page (Page 2)
- [ ] Create `2_Matchups.py`
- [ ] Implement team selection (home/away dropdowns)
- [ ] Implement matchup dropdown option
- [ ] Build team comparison cards
- [ ] Build metrics comparison table
- [ ] Implement `aggregate_player_grades_by_category()`
- [ ] Build player grades comparison table
- [ ] Add weekly EPA comparison chart
- [ ] Test with sample matchups

### Phase 4: Team Specific Page (Page 3)
- [ ] Create `3_Team_Specific.py`
- [ ] Build team selector and key metrics cards
- [ ] Build performance stats table
- [ ] Add weekly EPA trend chart
- [ ] Implement `calculate_injury_impact_by_week()`
- [ ] Build injury impact weekly chart (NEW FEATURE)
- [ ] Build injury impact table
- [ ] Add week selector for detailed view
- [ ] Test with sample team

### Phase 5: Refinement & Documentation
- [ ] Test all pages end-to-end
- [ ] Verify caching works correctly
- [ ] Test error handling (disconnect S3, missing columns)
- [ ] Verify mobile responsiveness
- [ ] Create README.md with:
  - Setup instructions
  - Environment setup (conda)
  - AWS credentials setup
  - Data pipeline overview
  - Usage guide
- [ ] Save final implementation plan to `.claude/v1_implementation_plan.md`

### Phase 6: Polish & Enhancements
- [ ] Add loading indicators for slow operations
- [ ] Improve chart aesthetics (colors, fonts)
- [ ] Add hover tooltips to charts
- [ ] Add data freshness indicator (last updated timestamp)
- [ ] Test with multiple teams/weeks
- [ ] Performance optimization (if needed)

---

## Verification & Testing

### Manual Testing Checklist

**Team Performance Page:**
1. Load page - verify all 4 charts render
2. Select different season - verify data updates
3. Select different week - verify data updates
4. Filter by division - verify only division teams show
5. Filter by conference - verify only conference teams show
6. Hover over team logos - verify tooltips show correct data
7. Verify axes are inverted correctly (defensive metrics)

**Matchups Page:**
1. Select home team and away team - verify both team cards render
2. Verify all metrics populate correctly
3. Verify player grades table shows all 12 categories
4. Verify weekly EPA chart shows both teams
5. Try matchup dropdown option
6. Switch teams - verify data updates correctly

**Team Specific Page:**
1. Select team - verify metrics cards populate
2. Verify stats table shows all metrics
3. Verify weekly EPA chart shows trend over season
4. Select different week - verify injury impact table updates
5. Verify injury impact weekly chart shows all weeks
6. Verify color coding (red/green/gray) works correctly
7. Try different teams - verify no data errors

**Error Handling:**
1. Temporarily break S3 connection - verify error message shows
2. Remove required column from test data - verify graceful degradation
3. Select team with no data - verify appropriate message
4. Test with empty dataset - verify app doesn't crash

### Data Validation

**Verify these calculations are correct:**
- [ ] ATS record matches manual calculation
- [ ] O/U record matches manual calculation
- [ ] Favorite/underdog splits are correct
- [ ] Home/road splits are correct
- [ ] EPA aggregates match raw data
- [ ] Player grade aggregations are reasonable
- [ ] Injury impact differences are calculated correctly (weekly - healthy)

---

## Dependencies & Environment

**Python Packages Required:**
- streamlit >= 1.31.0
- pandas >= 2.2.0
- numpy >= 1.26.0
- boto3 >= 1.34.0
- plotly >= 5.18.0
- openpyxl >= 3.1.0 (for Excel reading)

**AWS Resources:**
- S3 bucket: `nateb-nfl-project`
- Folder: `Prod/core/` (datasets)
- Folder: `Prod/aux/` (team logos)
- Environment: Prod

**Local Setup:**
1. Create conda environment: `conda env create -f streamlit_environment.yml`
2. Activate: `conda activate nfl_streamlit`
3. Run secrets.py to set environment variables
4. Launch: `streamlit run app.py`

---

## Notes & Considerations

1. **Team Logo Loading:**
   - Logos may be URLs or local file paths
   - Need to verify format in Team Logos.xlsx
   - May need to cache logo images locally in `assets/team_logos/`
   - Fallback to team abbreviations if logos fail

2. **Player Grade Aggregation:**
   - Assumes weekly_starters and healthy_starters have consistent grade column names
   - May need to map position codes to categories (e.g., 'T', 'G', 'C' → pass_blocking)
   - Special teams grades may require separate dataset

3. **Performance Optimization:**
   - With 1-hour TTL, data loads should be infrequent
   - Consider lazy loading for less-used features
   - Monitor Streamlit performance with large datasets

4. **Future Enhancements (Post-V1):**
   - Add export to PDF/image feature
   - Add betting line integration (if available)
   - Add historical matchup analysis
   - Add playoff probability calculator
   - Add custom date range filters

5. **Data Pipeline Dependency:**
   - V1 assumes data pipeline is running and keeping S3 updated
   - Need to handle cases where data is stale (add timestamp check)
   - Consider adding "Data last updated: [timestamp]" indicator

---

## Risk Mitigation

**Risk:** Team Logos.xlsx format unknown
- **Mitigation:** Check file structure first, add fallback to text markers

**Risk:** Player grade column names may differ from assumptions
- **Mitigation:** Review actual column names before implementing aggregation logic

**Risk:** Missing data for certain teams/weeks
- **Mitigation:** Add defensive checks, show "N/A" instead of crashing

**Risk:** S3 data not ready (pipeline running)
- **Mitigation:** Add retry logic, show user-friendly message

**Risk:** Performance issues with large datasets
- **Mitigation:** Use TTL caching, load only needed columns, add pagination if needed

---

## Summary

This plan provides a comprehensive roadmap for implementing V1 of the NFL Streamlit betting analytics dashboard. It reuses proven patterns from V0 while building new features specific to V1 requirements. The modular structure ensures maintainability, and the caching strategy ensures performance. The implementation is broken into phases with clear verification steps at each stage.

**Estimated Complexity:**
- Phase 1 (Setup): Low - mostly refactoring existing code
- Phase 2 (Team Performance): Medium - logo integration is new
- Phase 3 (Matchups): Medium-High - player grade aggregation is complex
- Phase 4 (Team Specific): Medium-High - injury impact analysis is new
- Phase 5 (Documentation): Low
- Phase 6 (Polish): Low-Medium

**Key Success Factors:**
1. Verify data structure early (confirm column names)
2. Test logo loading immediately
3. Validate player grade aggregation logic with sample data
4. Implement error handling from the start
5. Test incrementally (don't wait until the end)
