"""
Team Performance Page
Analyze team trends, EPA, win/loss records, and performance metrics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import (
    load_training_data_full_game,
    load_team_week_averages,
    load_strength_of_schedule,
    get_available_teams,
    get_available_seasons
)
from utils.data_processor import (
    get_current_week,
    filter_by_season_week,
    calculate_ats_record,
    calculate_over_under_record,
    get_team_trends
)
from components.filters import render_team_selector, render_season_week_filters

# Page configuration
st.set_page_config(
    page_title="Team Performance - NFL Betting Analytics",
    page_icon="🏈",
    layout="wide"
)

st.title("🏈 Team Performance Analysis")
st.markdown("Analyze team trends, offensive/defensive performance, and betting records")

# Load data
@st.cache_data(ttl=3600)
def load_performance_data():
    """Load all required data for team performance page"""
    return {
        'training': load_training_data_full_game(),
        'team_averages': load_team_week_averages(),
        'sos': load_strength_of_schedule()
    }

with st.spinner("Loading data..."):
    try:
        data = load_performance_data()

        if data['training'] is None or data['training'].empty:
            st.error("Failed to load data. Please check your S3 connection.")
            st.stop()

        current_season, current_week = get_current_week(data['training'])
        teams_list = get_available_teams(data['training'])
        seasons_list = get_available_seasons(data['training'])

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.stop()

# Team Selection
st.sidebar.header("Team Selection")
selected_team = render_team_selector(
    teams_list,
    key="team_perf_select",
    multi=False,
    label="Select Team to Analyze"
)

if not selected_team:
    st.info("Please select a team from the sidebar to begin analysis.")
    st.stop()

# Season/Week Filters
st.sidebar.header("Time Period")
filter_values = render_season_week_filters(
    seasons_list,
    default_season=current_season
)

selected_season = filter_values['season']
selected_week = filter_values['week']

# Filter data for selected team
team_data = data['training'][data['training']['team'] == selected_team].copy()
team_avg_data = data['team_averages'][
    data['team_averages']['team' if 'team' in data['team_averages'].columns else 'team_name'] == selected_team
].copy() if data['team_averages'] is not None else pd.DataFrame()

# Performance Overview
st.header(f"📊 {selected_team} Performance Overview")

# Key Metrics Row
col1, col2, col3, col4 = st.columns(4)

# Calculate overall record
season_games = team_data[team_data['season'] == selected_season]

if not season_games.empty and 'score' in season_games.columns and 'against_score' in season_games.columns:
    wins = (season_games['score'] > season_games['against_score']).sum()
    losses = (season_games['score'] < season_games['against_score']).sum()

    with col1:
        st.metric("Win-Loss Record", f"{wins}-{losses}")

    with col2:
        win_pct = wins / (wins + losses) if (wins + losses) > 0 else 0
        st.metric("Win %", f"{win_pct:.1%}")

    # ATS Record
    ats_record = calculate_ats_record(season_games)
    if not ats_record.empty and 'ats_record' in ats_record.columns:
        with col3:
            st.metric("ATS Record", ats_record['ats_record'].iloc[0])

        with col4:
            st.metric("ATS %", f"{ats_record['ats_pct'].iloc[0]:.1%}")

# Trends over time
st.header("📈 Performance Trends")

if not team_avg_data.empty:
    # Filter to selected season
    season_trends = team_avg_data[team_avg_data['season'] == selected_season].sort_values('week')

    if not season_trends.empty:
        # Create tabs for different metric categories
        tab1, tab2, tab3 = st.tabs(["EPA Metrics", "Scoring", "Win/Loss"])

        with tab1:
            st.subheader("Expected Points Added (EPA) Trends")

            # EPA chart
            if 'epa_per_play_offense' in season_trends.columns and 'epa_per_play_defense' in season_trends.columns:
                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=season_trends['week'],
                    y=season_trends['epa_per_play_offense'],
                    mode='lines+markers',
                    name='Offensive EPA',
                    line=dict(color='green', width=2)
                ))

                fig.add_trace(go.Scatter(
                    x=season_trends['week'],
                    y=season_trends['epa_per_play_defense'],
                    mode='lines+markers',
                    name='Defensive EPA (allowed)',
                    line=dict(color='red', width=2)
                ))

                fig.update_layout(
                    title=f"{selected_team} EPA per Play by Week",
                    xaxis_title="Week",
                    yaxis_title="EPA per Play",
                    hovermode='x unified',
                    height=400
                )

                st.plotly_chart(fig, use_container_width=True)

                # EPA interpretation
                latest_off_epa = season_trends['epa_per_play_offense'].iloc[-1] if len(season_trends) > 0 else 0
                latest_def_epa = season_trends['epa_per_play_defense'].iloc[-1] if len(season_trends) > 0 else 0

                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "Latest Offensive EPA",
                        f"{latest_off_epa:.3f}",
                        help="Higher is better. Positive values indicate above-average offense."
                    )
                with col2:
                    st.metric(
                        "Latest Defensive EPA",
                        f"{latest_def_epa:.3f}",
                        help="Lower is better. Negative values indicate above-average defense."
                    )
            else:
                st.info("EPA data not available for this team/season.")

        with tab2:
            st.subheader("Scoring Trends")

            # Scoring chart from training data
            season_games_sorted = season_games.sort_values('week')

            if not season_games_sorted.empty and 'score' in season_games_sorted.columns:
                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=season_games_sorted['week'],
                    y=season_games_sorted['score'],
                    mode='lines+markers',
                    name='Points Scored',
                    line=dict(color='blue', width=2)
                ))

                fig.add_trace(go.Scatter(
                    x=season_games_sorted['week'],
                    y=season_games_sorted['against_score'],
                    mode='lines+markers',
                    name='Points Allowed',
                    line=dict(color='orange', width=2)
                ))

                fig.update_layout(
                    title=f"{selected_team} Points Scored vs. Allowed",
                    xaxis_title="Week",
                    yaxis_title="Points",
                    hovermode='x unified',
                    height=400
                )

                st.plotly_chart(fig, use_container_width=True)

                # Scoring stats
                col1, col2 = st.columns(2)
                with col1:
                    avg_scored = season_games_sorted['score'].mean()
                    st.metric("Avg Points Scored", f"{avg_scored:.1f}")
                with col2:
                    avg_allowed = season_games_sorted['against_score'].mean()
                    st.metric("Avg Points Allowed", f"{avg_allowed:.1f}")

        with tab3:
            st.subheader("Win/Loss by Week")

            if not season_games_sorted.empty and 'score' in season_games_sorted.columns:
                season_games_sorted['result'] = season_games_sorted.apply(
                    lambda row: 'W' if row['score'] > row['against_score'] else 'L',
                    axis=1
                )

                # Create win/loss visualization
                season_games_sorted['result_numeric'] = season_games_sorted['result'].map({'W': 1, 'L': 0})

                fig = px.bar(
                    season_games_sorted,
                    x='week',
                    y='result_numeric',
                    color='result',
                    color_discrete_map={'W': 'green', 'L': 'red'},
                    title=f"{selected_team} Win/Loss by Week",
                    labels={'result_numeric': 'Result', 'week': 'Week'}
                )

                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

    else:
        st.info(f"No trend data available for {selected_team} in {selected_season} season.")
else:
    st.warning("Team averages data not available.")

# Recent Games Table
st.header("🎯 Recent Games")

if not season_games.empty:
    recent_games = season_games.sort_values('week', ascending=False).head(5)

    # Select relevant columns
    display_cols = ['week', 'against_team', 'score', 'against_score']
    if 'spread' in recent_games.columns:
        display_cols.append('spread')

    recent_display = recent_games[display_cols].copy()

    # Add result column
    if 'score' in recent_display.columns and 'against_score' in recent_display.columns:
        recent_display['result'] = recent_display.apply(
            lambda row: 'W' if row['score'] > row['against_score'] else 'L',
            axis=1
        )
        recent_display['margin'] = recent_display['score'] - recent_display['against_score']

    # Rename columns for display
    recent_display = recent_display.rename(columns={
        'week': 'Week',
        'against_team': 'Opponent',
        'score': 'Score',
        'against_score': 'Opp Score',
        'spread': 'Spread',
        'result': 'Result',
        'margin': 'Margin'
    })

    st.dataframe(recent_display, use_container_width=True, hide_index=True)

# ATS and O/U Records
st.header("💰 Betting Performance")

col1, col2 = st.columns(2)

with col1:
    st.subheader("ATS Record")
    ats_full = calculate_ats_record(team_data)

    if not ats_full.empty:
        st.metric("Overall ATS Record", ats_full['ats_record'].iloc[0])
        st.metric("ATS Win %", f"{ats_full['ats_pct'].iloc[0]:.1%}")

with col2:
    st.subheader("Over/Under Record")
    ou_record = calculate_over_under_record(team_data)

    if not ou_record.empty and 'ou_record' in ou_record.columns:
        st.metric("O/U Record", ou_record['ou_record'].iloc[0])
        st.metric("Over %", f"{ou_record['over_pct'].iloc[0]:.1%}")

# Footer
st.markdown("---")
st.markdown("Use the sidebar to select different teams and time periods for analysis.")
