"""
NFL Betting Analytics Dashboard V1 - Team Performance Page
League-wide team comparison with EPA scatter plots
"""

import streamlit as st
import pandas as pd

from utils.data_loader import (
    load_int_game_df_team_week,
    load_team_logos,
    get_available_teams,
    get_available_seasons,
    get_available_weeks,
    get_current_season_week
)
from utils.data_processor import calculate_league_season_aggregates
from utils.plotting import create_epa_scatter
from components.filters import (
    render_sidebar_filters,
    apply_division_conference_filter
)

# Page configuration
st.set_page_config(
    page_title="NFL Team Performance",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("🏈 NFL Team Performance Comparison")
st.markdown("Compare all teams across EPA metrics. Each point represents a team's season average.")

# Load data with error handling
with st.spinner("Loading data from S3..."):
    try:
        # Load primary data
        team_week_data = load_int_game_df_team_week()

        if team_week_data is None or team_week_data.empty:
            st.error("Failed to load team performance data. Please check your S3 connection.")
            st.stop()

        # Load team logos (optional - fallback to text if not available)
        logos_dict = load_team_logos()

        # Get current season/week
        current_season, current_week = get_current_season_week(team_week_data)

        st.success(f"Data loaded! Latest: Season {current_season}, Week {current_week}")

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Please ensure your AWS credentials are correct and the S3 bucket is accessible.")
        st.stop()

# Sidebar filters
st.sidebar.header("Filters")

# Season filter
seasons = get_available_seasons(team_week_data)
selected_season = st.sidebar.selectbox(
    "Season",
    options=seasons,
    index=0  # Most recent
)

# Week filter (through week X)
weeks = get_available_weeks(team_week_data, selected_season)
week_options = ["All Weeks"] + [f"Through Week {w}" for w in weeks]
selected_week_option = st.sidebar.selectbox(
    "Data Through",
    options=week_options,
    index=0
)

# Parse week selection
if selected_week_option == "All Weeks":
    selected_week = None
else:
    selected_week = int(selected_week_option.replace("Through Week ", ""))

# Division/Conference filter
div_conf_options = ["All Teams"]

if 'conference' in team_week_data.columns:
    conferences = team_week_data['conference'].dropna().unique().tolist()
    div_conf_options.extend(sorted(conferences))

if 'division' in team_week_data.columns:
    divisions = team_week_data['division'].dropna().unique().tolist()
    div_conf_options.extend(sorted(divisions))

selected_div_conf = st.sidebar.selectbox(
    "Filter by Division/Conference",
    options=div_conf_options
)

# Calculate league aggregates
league_agg = calculate_league_season_aggregates(
    team_week_data,
    selected_season,
    through_week=selected_week
)

if league_agg.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# Apply division/conference filter
filtered_agg = apply_division_conference_filter(league_agg, selected_div_conf)

if filtered_agg.empty:
    st.warning("No teams match the selected filter criteria.")
    st.stop()

# Display info
filter_desc = selected_div_conf if selected_div_conf != "All Teams" else "All Teams"
week_desc = f"through Week {selected_week}" if selected_week else "full season"
st.markdown(f"**Showing:** {filter_desc} | **Season:** {selected_season} | **Data:** {week_desc} | **Teams:** {len(filtered_agg)}")

# Create 2x2 grid of scatter plots
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    # Chart 1: Offensive EPA vs Defensive EPA
    st.subheader("Offensive vs Defensive EPA")

    if 'epa_mean' in filtered_agg.columns and 'against_epa_mean' in filtered_agg.columns:
        fig1 = create_epa_scatter(
            filtered_agg,
            x_col='against_epa_mean',
            y_col='epa_mean',
            title='Team Efficiency: Offense vs Defense',
            invert_x=True,  # Lower defensive EPA allowed is better
            logos_dict=logos_dict if logos_dict else None,
            team_col='team',
            x_label='Defensive EPA (Points Allowed per Play)',
            y_label='Offensive EPA (Points per Play)'
        )
        st.plotly_chart(fig1, use_container_width=True)
        st.caption("Top-left = Best teams (good offense + good defense). X-axis inverted.")
    else:
        st.info("Offensive/Defensive EPA columns not available in data.")

with col2:
    # Chart 2: Pass EPA vs Run EPA (Offense)
    st.subheader("Offensive Pass vs Run EPA")

    if 'pass_epa_mean' in filtered_agg.columns and 'run_epa_mean' in filtered_agg.columns:
        fig2 = create_epa_scatter(
            filtered_agg,
            x_col='run_epa_mean',
            y_col='pass_epa_mean',
            title='Offensive Balance: Pass vs Run',
            invert_x=False,
            logos_dict=logos_dict if logos_dict else None,
            team_col='team',
            x_label='Run EPA',
            y_label='Pass EPA'
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("Top-right = Elite offenses (good at passing and running).")
    else:
        st.info("Pass/Run EPA columns not available in data.")

col3, col4 = st.columns(2)

with col3:
    # Chart 3: Pass EPA Allowed vs Run EPA Allowed (Defense)
    st.subheader("Defensive Pass vs Run EPA Allowed")

    if 'against_pass_epa_mean' in filtered_agg.columns and 'against_run_epa_mean' in filtered_agg.columns:
        fig3 = create_epa_scatter(
            filtered_agg,
            x_col='against_run_epa_mean',
            y_col='against_pass_epa_mean',
            title='Defensive Efficiency: Pass vs Run',
            invert_x=True,  # Lower EPA allowed is better
            invert_y=True,
            logos_dict=logos_dict if logos_dict else None,
            team_col='team',
            x_label='Run EPA Allowed',
            y_label='Pass EPA Allowed'
        )
        st.plotly_chart(fig3, use_container_width=True)
        st.caption("Bottom-left = Best defenses (stop both pass and run). Both axes inverted.")
    else:
        st.info("Defensive EPA allowed columns not available in data.")

with col4:
    # Chart 4: Strength of Schedule
    st.subheader("Strength of Schedule")

    if 'opp_against_epa_mean' in filtered_agg.columns and 'opp_epa_mean' in filtered_agg.columns:
        fig4 = create_epa_scatter(
            filtered_agg,
            x_col='opp_epa_mean',
            y_col='opp_against_epa_mean',
            title='Opponent Strength: Offense vs Defense',
            invert_x=True,  # Faced tougher defenses = lower opponent defensive EPA
            logos_dict=logos_dict if logos_dict else None,
            team_col='team',
            x_label='Avg Opponent Defensive EPA',
            y_label='Avg Opponent Offensive EPA'
        )
        st.plotly_chart(fig4, use_container_width=True)
        st.caption("Top-left = Toughest schedule (faced good offenses and defenses).")
    else:
        st.info("Opponent EPA columns not available. Showing scoring instead.")

        # Fallback to scoring data
        if 'score' in filtered_agg.columns and 'against_score' in filtered_agg.columns:
            fig4 = create_epa_scatter(
                filtered_agg,
                x_col='against_score',
                y_col='score',
                title='Points Scored vs Points Allowed',
                invert_x=True,
                logos_dict=logos_dict if logos_dict else None,
                team_col='team',
                x_label='Avg Points Allowed',
                y_label='Avg Points Scored'
            )
            st.plotly_chart(fig4, use_container_width=True)
            st.caption("Top-left = Best teams (high scoring, low points allowed).")

# Data table section
st.markdown("---")
st.subheader("Team Statistics Table")

# Prepare display columns
display_cols = ['team']
col_names = {'team': 'Team'}

# Add available metrics
metric_mappings = {
    'epa_mean': 'Offensive EPA',
    'against_epa_mean': 'Defensive EPA',
    'pass_epa_mean': 'Pass EPA',
    'run_epa_mean': 'Run EPA',
    'against_pass_epa_mean': 'Pass EPA Allowed',
    'against_run_epa_mean': 'Run EPA Allowed',
    'score': 'Avg Points',
    'against_score': 'Avg Points Allowed'
}

for col, name in metric_mappings.items():
    if col in filtered_agg.columns:
        display_cols.append(col)
        col_names[col] = name

# Create display dataframe
display_df = filtered_agg[display_cols].copy()
display_df = display_df.rename(columns=col_names)

# Round numeric columns
for col in display_df.columns:
    if col != 'Team':
        display_df[col] = display_df[col].round(3)

# Sort by offensive EPA if available
sort_col = 'Offensive EPA' if 'Offensive EPA' in display_df.columns else display_df.columns[1]
display_df = display_df.sort_values(sort_col, ascending=False)

st.dataframe(display_df, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.markdown("""
**Chart Guide:**
- **Top-left in Offense vs Defense** = Best overall teams (good at scoring, good at preventing scores)
- **EPA (Expected Points Added)** = Points contributed per play above average
- Positive EPA = Above average, Negative EPA = Below average
- **Inverted axes** show metrics where lower is better (defense)

Navigate to other pages using the sidebar for Matchup Analysis and Team Deep Dives.
""")
