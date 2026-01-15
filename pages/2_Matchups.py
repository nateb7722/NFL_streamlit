"""
NFL Betting Analytics Dashboard V1 - Matchups Page
Head-to-head team comparison with player grades
"""

import streamlit as st
import pandas as pd

from utils.data_loader import (
    load_int_game_df_team_week,
    load_int_game_df,
    load_weekly_starters,
    load_team_logos,
    get_available_teams,
    get_available_seasons,
    get_available_weeks,
    get_current_season_week
)
from utils.data_processor import (
    calculate_team_season_aggregates,
    calculate_records_by_situation,
    aggregate_player_grades_by_category,
    get_team_weekly_data
)
from utils.plotting import create_weekly_epa_comparison, create_grade_comparison_bar
from components.metrics_cards import (
    render_team_comparison_cards,
    render_metrics_comparison_table,
    render_player_grades_comparison
)
from components.filters import render_team_selector, render_season_selector

# Page configuration
st.set_page_config(
    page_title="NFL Matchup Analysis",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("🏈 NFL Matchup Analysis")
st.markdown("Compare two teams head-to-head with performance metrics and player grades.")

# Load data
with st.spinner("Loading data..."):
    try:
        team_week_data = load_int_game_df_team_week()
        game_data = load_int_game_df()
        weekly_starters_off = load_weekly_starters('offense')
        weekly_starters_def = load_weekly_starters('defense')
        logos_dict = load_team_logos()

        if team_week_data is None or team_week_data.empty:
            st.error("Failed to load team data. Please check your S3 connection.")
            st.stop()

        current_season, current_week = get_current_season_week(team_week_data)
        st.success(f"Data loaded! Latest: Season {current_season}, Week {current_week}")

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.stop()

# Sidebar - Team Selection
st.sidebar.header("Team Selection")

# Get available teams and seasons
teams = get_available_teams(team_week_data)
seasons = get_available_seasons(team_week_data)

# Season selector
selected_season = st.sidebar.selectbox(
    "Season",
    options=seasons,
    index=0
)

# Team selection mode
selection_mode = st.sidebar.radio(
    "Selection Mode",
    options=["Manual Selection", "Select from Matchups"],
    index=0
)

home_team = None
away_team = None

if selection_mode == "Manual Selection":
    # Manual team dropdowns
    st.sidebar.markdown("---")
    st.sidebar.subheader("Select Teams")

    home_team = st.sidebar.selectbox(
        "Home Team",
        options=teams,
        index=0,
        key="home_team_select"
    )

    # Filter away team options to exclude home team
    away_team_options = [t for t in teams if t != home_team]
    away_team = st.sidebar.selectbox(
        "Away Team",
        options=away_team_options,
        index=0,
        key="away_team_select"
    )

else:
    # Select from existing matchups
    st.sidebar.markdown("---")
    st.sidebar.subheader("Select Matchup")

    if game_data is not None and not game_data.empty:
        # Get matchups for selected season
        season_games = game_data[game_data['season'] == selected_season]

        if not season_games.empty and 'home_team' in season_games.columns and 'away_team' in season_games.columns:
            # Create matchup options
            matchup_options = []
            matchup_map = {}

            for _, row in season_games[['home_team', 'away_team', 'week']].drop_duplicates().sort_values('week', ascending=False).iterrows():
                matchup_str = f"Week {int(row['week'])}: {row['away_team']} @ {row['home_team']}"
                matchup_options.append(matchup_str)
                matchup_map[matchup_str] = (row['home_team'], row['away_team'])

            if matchup_options:
                selected_matchup = st.sidebar.selectbox(
                    "Select Matchup",
                    options=matchup_options
                )

                if selected_matchup:
                    home_team, away_team = matchup_map[selected_matchup]
        else:
            st.sidebar.warning("No matchup data available for this season.")
    else:
        st.sidebar.warning("Game data not available.")

# Validate team selection
if not home_team or not away_team:
    st.warning("Please select two teams to compare.")
    st.stop()

if home_team == away_team:
    st.warning("Please select two different teams.")
    st.stop()

# Get data through week filter
weeks = get_available_weeks(team_week_data, selected_season)
through_week = st.sidebar.selectbox(
    "Data Through Week",
    options=weeks,
    index=len(weeks) - 1 if weeks else 0
)

# Main Content
st.markdown("---")

# Team comparison header cards
st.header(f"{away_team} @ {home_team}")

# Calculate metrics for both teams
home_metrics = calculate_team_season_aggregates(team_week_data, home_team, selected_season)
away_metrics = calculate_team_season_aggregates(team_week_data, away_team, selected_season)

# Calculate records
home_records = calculate_records_by_situation(team_week_data, home_team, selected_season)
away_records = calculate_records_by_situation(team_week_data, away_team, selected_season)

# Combine metrics and records
home_data = {**home_metrics, **home_records}
away_data = {**away_metrics, **away_records}

# Get logos
home_logo = logos_dict.get(home_team) if logos_dict else None
away_logo = logos_dict.get(away_team) if logos_dict else None

# Render comparison cards
render_team_comparison_cards(
    away_team, away_data,
    home_team, home_data,
    logo_a_url=away_logo,
    logo_b_url=home_logo
)

# Performance Metrics Comparison
st.markdown("---")
st.subheader("Performance Metrics Comparison")

render_metrics_comparison_table(away_team, away_metrics, home_team, home_metrics)

# Weekly EPA Trend Chart
st.markdown("---")
st.subheader("Weekly EPA Trend Comparison")

if 'epa_mean' in team_week_data.columns:
    fig = create_weekly_epa_comparison(
        team_week_data,
        away_team,
        home_team,
        selected_season,
        epa_col='epa_mean'
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("EPA trend data not available.")

# Player Grades Comparison
st.markdown("---")
st.subheader("Player Grades Comparison by Position Group")

# Get latest week with data for both teams
if weekly_starters_off is not None and weekly_starters_def is not None:
    # Use through_week for grades
    home_grades = aggregate_player_grades_by_category(
        weekly_starters_off, weekly_starters_def,
        home_team, through_week, selected_season
    )
    away_grades = aggregate_player_grades_by_category(
        weekly_starters_off, weekly_starters_def,
        away_team, through_week, selected_season
    )

    if home_grades or away_grades:
        # Display as table
        render_player_grades_comparison(away_team, away_grades, home_team, home_grades)

        # Also show bar chart comparison
        st.markdown("---")
        st.subheader("Visual Grade Comparison")

        fig = create_grade_comparison_bar(away_team, away_grades, home_team, home_grades)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"Player grade data not available for Week {through_week}.")
else:
    st.info("Player grade data not available.")

# Betting Summary
st.markdown("---")
st.subheader("Betting Summary")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**{away_team} (Away)**")

    away_summary = {
        "Overall Record": away_data.get('overall_record', 'N/A'),
        "ATS Record": away_data.get('ats_record', 'N/A'),
        "O/U Record": away_data.get('ou_record', 'N/A'),
        "Road Record": away_data.get('road_record', 'N/A'),
        "As Underdog": away_data.get('underdog_record', 'N/A'),
    }

    for key, val in away_summary.items():
        st.write(f"- {key}: **{val}**")

with col2:
    st.markdown(f"**{home_team} (Home)**")

    home_summary = {
        "Overall Record": home_data.get('overall_record', 'N/A'),
        "ATS Record": home_data.get('ats_record', 'N/A'),
        "O/U Record": home_data.get('ou_record', 'N/A'),
        "Home Record": home_data.get('home_record', 'N/A'),
        "As Favorite": home_data.get('favorite_record', 'N/A'),
    }

    for key, val in home_summary.items():
        st.write(f"- {key}: **{val}**")

# Footer
st.markdown("---")
st.markdown("""
**Note:** Player grades are aggregated from weekly starter data by position group.
EPA metrics show offensive efficiency (higher is better for offense).
Records are based on season performance through the selected week.
""")
