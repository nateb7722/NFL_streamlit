"""
NFL Betting Analytics Dashboard - Home Page
Main entry point with current week betting recommendations
"""

import streamlit as st
import pandas as pd
from utils.data_loader import (
    load_training_data_full_game,
    load_team_week_averages,
    load_strength_of_schedule,
    get_available_teams,
    get_available_seasons
)
from utils.data_processor import (
    get_current_week,
    calculate_ats_record,
    calculate_betting_edges
)

# Page configuration
st.set_page_config(
    page_title="NFL Betting Analytics",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("🏈 NFL Betting Analytics Dashboard")
st.markdown("""
Welcome to the NFL Betting Analytics Dashboard. This tool provides data-driven insights
for NFL betting decisions based on historical performance, EPA metrics, and injury data.
""")

# Load data with error handling
@st.cache_data(ttl=3600)
def load_all_data():
    """Load all required data for home page"""
    data = {
        'training': load_training_data_full_game(),
        'team_averages': load_team_week_averages(),
        'sos': load_strength_of_schedule()
    }
    return data

with st.spinner("Loading data from S3..."):
    try:
        data = load_all_data()

        # Check if data loaded successfully
        if data['training'] is None or data['training'].empty:
            st.error("Failed to load training data. Please check your S3 connection and credentials.")
            st.stop()

        # Get current week
        current_season, current_week = get_current_week(data['training'])

        # Display data freshness
        st.success(f"Data loaded successfully! Latest data: Season {current_season}, Week {current_week - 1}")

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Please ensure your AWS credentials in secrets_env.py are correct and the S3 bucket is accessible.")
        st.stop()

# Sidebar navigation guidance
st.sidebar.header("Navigation")
st.sidebar.markdown("""
Use the sidebar navigation to access different pages:

- **Team Performance**: Analyze team trends, EPA, and records
- **Betting Analysis**: Core betting insights, ATS records, and edges
- **Player Statistics**: Individual player performance (coming soon)
- **Head-to-Head**: Historical matchup analysis (coming soon)
""")

# Main content
st.header(f"Week {current_week} Overview")

# Create columns for key metrics
col1, col2, col3 = st.columns(3)

with col1:
    total_teams = len(get_available_teams(data['training']))
    st.metric("Total Teams", total_teams)

with col2:
    total_games = len(data['training'][
        (data['training']['season'] == current_season) &
        (data['training']['week'] < current_week)
    ]) if data['training'] is not None else 0
    st.metric("Games This Season", total_games)

with col3:
    seasons_available = len(get_available_seasons(data['training']))
    st.metric("Seasons Available", seasons_available)

# Top Betting Edges section
st.header("🎯 Top Betting Edges")
st.markdown("Teams with the strongest EPA performance (updated weekly)")

try:
    if data['team_averages'] is not None and not data['team_averages'].empty:
        edges = calculate_betting_edges(
            data['training'],
            data['team_averages'],
            current_season,
            current_week
        )

        if not edges.empty and 'edge_score' in edges.columns:
            # Display top 10 teams
            top_edges = edges.head(10)[['team', 'epa_per_play_offense', 'epa_per_play_defense', 'edge_score']]

            # Rename columns for display
            top_edges = top_edges.rename(columns={
                'team': 'Team',
                'epa_per_play_offense': 'Offensive EPA',
                'epa_per_play_defense': 'Defensive EPA',
                'edge_score': 'Edge Score (Rank)'
            })

            st.dataframe(
                top_edges,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Insufficient data to calculate betting edges. Check back after more games are played.")
    else:
        st.warning("Team averages data not available.")

except Exception as e:
    st.error(f"Error calculating betting edges: {str(e)}")

# ATS Leaders section
st.header("📊 ATS Performance Leaders")
st.markdown("Teams with the best Against The Spread records")

try:
    if data['training'] is not None and not data['training'].empty:
        ats_records = calculate_ats_record(data['training'])

        if not ats_records.empty:
            # Display top 10 ATS performers
            top_ats = ats_records.head(10)[[
                'team' if 'team' in ats_records.columns else 'team_name',
                'games',
                'ats_wins',
                'ats_losses',
                'ats_record',
                'ats_pct'
            ]]

            # Rename columns for display
            top_ats = top_ats.rename(columns={
                'team': 'Team',
                'team_name': 'Team',
                'games': 'Games',
                'ats_wins': 'ATS Wins',
                'ats_losses': 'ATS Losses',
                'ats_record': 'ATS Record',
                'ats_pct': 'ATS %'
            })

            st.dataframe(
                top_ats,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No ATS data available.")
    else:
        st.warning("Training data not available.")

except Exception as e:
    st.error(f"Error calculating ATS records: {str(e)}")

# Quick stats
st.header("📈 Quick Stats")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Current Season Trends")
    if data['training'] is not None and not data['training'].empty:
        season_data = data['training'][data['training']['season'] == current_season]

        if not season_data.empty and 'score' in season_data.columns and 'against_score' in season_data.columns:
            avg_total_points = (season_data['score'] + season_data['against_score']).mean()
            st.metric("Avg Total Points Per Game", f"{avg_total_points:.1f}")

            if 'spread' in season_data.columns:
                avg_spread = abs(season_data['spread']).mean()
                st.metric("Avg Spread", f"{avg_spread:.1f}")

with col2:
    st.subheader("Data Coverage")
    if data['training'] is not None and not data['training'].empty:
        min_season = data['training']['season'].min()
        max_season = data['training']['season'].max()
        st.info(f"Historical data from {int(min_season)} to {int(max_season)}")

# Footer
st.markdown("---")
st.markdown("""
**Note:** This dashboard uses historical NFL data and advanced metrics like EPA (Expected Points Added)
to identify betting opportunities. Always gamble responsibly.
""")
