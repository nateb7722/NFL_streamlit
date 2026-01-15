"""
NFL Betting Analytics Dashboard V1 - Team Specific Page
Single team deep dive with injury impact analysis
"""

import streamlit as st
import pandas as pd

from utils.data_loader import (
    load_int_game_df_team_week,
    load_weekly_starters,
    load_healthy_starters,
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
    calculate_injury_impact_by_week,
    get_team_weekly_data
)
from utils.plotting import create_weekly_epa_trend, create_injury_impact_chart
from components.metrics_cards import (
    render_key_metrics,
    render_team_stats_table,
    render_injury_impact_table
)

# Page configuration
st.set_page_config(
    page_title="NFL Team Deep Dive",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("🏈 Team Deep Dive")
st.markdown("Analyze single team performance and injury impact on player grades.")

# Load data
with st.spinner("Loading data..."):
    try:
        team_week_data = load_int_game_df_team_week()
        weekly_starters_off = load_weekly_starters('offense')
        weekly_starters_def = load_weekly_starters('defense')
        healthy_starters_off = load_healthy_starters('offense')
        healthy_starters_def = load_healthy_starters('defense')
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

# Team selector
selected_team = st.sidebar.selectbox(
    "Select Team",
    options=teams,
    index=0
)

# Get logo
team_logo = logos_dict.get(selected_team) if logos_dict else None

# Main Content
st.markdown("---")

# Team Header
col_logo, col_title = st.columns([1, 4])

with col_logo:
    if team_logo:
        st.image(team_logo, width=100)
    else:
        st.markdown(f"### {selected_team[:3].upper()}")

with col_title:
    st.header(f"{selected_team} - {selected_season} Season")

# Calculate team metrics
team_metrics = calculate_team_season_aggregates(team_week_data, selected_team, selected_season)
team_records = calculate_records_by_situation(team_week_data, selected_team, selected_season)

# Key Metrics Cards
st.markdown("---")
st.subheader("Key Metrics")

key_metrics = {
    "Record": team_records.get('overall_record', 'N/A'),
    "ATS": team_records.get('ats_record', 'N/A'),
    "O/U": team_records.get('ou_record', 'N/A'),
}

# Add EPA if available
if 'avg_offensive_epa' in team_metrics:
    off_epa = team_metrics['avg_offensive_epa']
    def_epa = team_metrics.get('avg_defensive_epa', 0)
    total_epa = off_epa - def_epa  # Net EPA advantage
    key_metrics["Net EPA"] = f"{total_epa:.3f}"

render_key_metrics(key_metrics, cols=4)

# Performance Stats Table
st.markdown("---")
st.subheader("Performance Statistics")

combined_data = {**team_metrics, **team_records}
render_team_stats_table(combined_data)

# Weekly EPA Trend
st.markdown("---")
st.subheader("Weekly EPA Trend")

if 'epa_mean' in team_week_data.columns:
    fig = create_weekly_epa_trend(
        team_week_data,
        selected_team,
        selected_season,
        epa_col='epa_mean'
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Weekly EPA trend data not available.")

# Injury Impact Analysis
st.markdown("---")
st.header("Injury Impact Analysis")
st.markdown("""
This section compares player grades between **healthy starters** (best available lineup)
and **weekly starters** (who actually played). Negative differences indicate injury impact.
""")

# Check if we have the necessary data
has_injury_data = (
    weekly_starters_off is not None and
    weekly_starters_def is not None and
    healthy_starters_off is not None and
    healthy_starters_def is not None
)

if has_injury_data:
    # Calculate injury impact across all weeks
    impact_df = calculate_injury_impact_by_week(
        healthy_starters_off, healthy_starters_def,
        weekly_starters_off, weekly_starters_def,
        selected_team, selected_season
    )

    if not impact_df.empty:
        # Weekly injury impact chart
        st.subheader("Weekly Injury Impact Trend")
        fig = create_injury_impact_chart(impact_df)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Negative values = injury impact (weekly starters graded lower than healthy starters)")

        # Week selector for detailed view
        st.markdown("---")
        st.subheader("Detailed Grade Comparison by Week")

        available_weeks = sorted(impact_df['week'].unique())
        week_options = ["Season Average"] + [f"Week {w}" for w in available_weeks]

        selected_week_option = st.selectbox(
            "Select Week for Detailed View",
            options=week_options
        )

        if selected_week_option == "Season Average":
            # Show season average
            st.markdown("**Season Average Grade Differences**")

            # Aggregate healthy and weekly grades across all weeks
            healthy_avg = aggregate_player_grades_by_category(
                healthy_starters_off, healthy_starters_def,
                selected_team, available_weeks[-1], selected_season  # Use latest week structure
            )
            weekly_avg = aggregate_player_grades_by_category(
                weekly_starters_off, weekly_starters_def,
                selected_team, available_weeks[-1], selected_season
            )

            # For season average, calculate means from impact_df
            season_healthy = {}
            season_weekly = {}

            for category in impact_df['category'].unique():
                cat_data = impact_df[impact_df['category'] == category]
                season_healthy[category] = cat_data['healthy_grade'].mean()
                season_weekly[category] = cat_data['weekly_grade'].mean()

            render_injury_impact_table(season_healthy, season_weekly)

        else:
            # Show specific week
            selected_week = int(selected_week_option.replace("Week ", ""))

            st.markdown(f"**Week {selected_week} Grade Comparison**")

            # Get grades for specific week
            healthy_grades = aggregate_player_grades_by_category(
                healthy_starters_off, healthy_starters_def,
                selected_team, selected_week, selected_season
            )
            weekly_grades = aggregate_player_grades_by_category(
                weekly_starters_off, weekly_starters_def,
                selected_team, selected_week, selected_season
            )

            render_injury_impact_table(healthy_grades, weekly_grades)

        # Summary statistics
        st.markdown("---")
        st.subheader("Injury Impact Summary")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Total negative impact weeks
            weekly_totals = impact_df.groupby('week')['difference'].sum()
            negative_weeks = (weekly_totals < 0).sum()
            st.metric("Weeks with Injury Impact", f"{negative_weeks} / {len(weekly_totals)}")

        with col2:
            # Average weekly impact
            avg_impact = weekly_totals.mean()
            st.metric("Avg Weekly Grade Impact", f"{avg_impact:+.1f}")

        with col3:
            # Most impacted category
            category_impact = impact_df.groupby('category')['difference'].mean()
            if not category_impact.empty:
                worst_category = category_impact.idxmin()
                worst_impact = category_impact.min()
                st.metric("Most Impacted Area", f"{worst_category.replace('_', ' ').title()}", f"{worst_impact:+.1f}")

    else:
        st.info(f"No injury impact data available for {selected_team} in {selected_season}.")
else:
    st.warning("Injury impact analysis requires weekly starter and healthy starter data, which is not available.")

# Situational Records
st.markdown("---")
st.subheader("Situational Performance")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Home/Away Splits**")
    home_rec = team_records.get('home_record', 'N/A')
    road_rec = team_records.get('road_record', 'N/A')
    st.write(f"- Home Record: **{home_rec}**")
    st.write(f"- Road Record: **{road_rec}**")

with col2:
    st.markdown("**Favorite/Underdog Splits**")
    fav_rec = team_records.get('favorite_record', 'N/A')
    dog_rec = team_records.get('underdog_record', 'N/A')
    st.write(f"- As Favorite: **{fav_rec}**")
    st.write(f"- As Underdog: **{dog_rec}**")

# Footer
st.markdown("---")
st.markdown("""
**Analysis Guide:**
- **Injury Impact**: Compares healthy starter grades to actual weekly starter grades
- Negative impact = backups performing worse than projected starters
- Position groups with consistent negative impact may indicate key injuries
- Use this data to assess team strength accounting for injuries

Navigate to other pages for league-wide comparisons and head-to-head matchup analysis.
""")
