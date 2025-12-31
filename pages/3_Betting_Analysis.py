"""
Betting Analysis Page
Core betting insights: ATS records, spreads, EPA-based edges, and recommendations
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import (
    load_training_data_full_game,
    load_team_week_averages,
    load_strength_of_schedule,
    load_play_by_play,
    get_available_teams,
    get_available_seasons
)
from utils.data_processor import (
    get_current_week,
    calculate_ats_record,
    calculate_over_under_record,
    calculate_situational_ats,
    calculate_epa_differential
)

# Page configuration
st.set_page_config(
    page_title="Betting Analysis - NFL Analytics",
    page_icon="💰",
    layout="wide"
)

st.title("💰 NFL Betting Analysis")
st.markdown("Data-driven betting insights with ATS records, EPA edges, and situational analysis")

# Load data
@st.cache_data(ttl=3600)
def load_betting_data():
    """Load all required data for betting analysis"""
    return {
        'training': load_training_data_full_game(),
        'team_averages': load_team_week_averages(),
        'sos': load_strength_of_schedule(),
        'pbp': load_play_by_play()
    }

with st.spinner("Loading betting data..."):
    try:
        data = load_betting_data()

        if data['training'] is None or data['training'].empty:
            st.error("Failed to load betting data. Please check your S3 connection.")
            st.stop()

        current_season, current_week = get_current_week(data['training'])
        teams_list = get_available_teams(data['training'])
        seasons_list = get_available_seasons(data['training'])

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.stop()

# Sidebar filters
st.sidebar.header("Filters")
selected_season = st.sidebar.selectbox(
    "Season",
    options=seasons_list,
    index=seasons_list.index(current_season) if current_season in seasons_list else 0
)

analysis_type = st.sidebar.radio(
    "Analysis Type",
    options=["Overall ATS Records", "Situational ATS", "Spread Analysis", "EPA-Based Edges"],
    index=0
)

# Main content based on analysis type
if analysis_type == "Overall ATS Records":
    st.header("📊 Overall ATS Records")
    st.markdown(f"Against The Spread performance for {selected_season} season")

    # Calculate ATS records
    season_data = data['training'][data['training']['season'] == selected_season]
    ats_records = calculate_ats_record(season_data)

    if not ats_records.empty:
        # Display full ATS table
        display_cols = ['team' if 'team' in ats_records.columns else 'team_name',
                        'games', 'ats_wins', 'ats_losses', 'ats_pushes',
                        'ats_record', 'ats_pct']

        ats_display = ats_records[[col for col in display_cols if col in ats_records.columns]].copy()

        # Rename columns
        ats_display = ats_display.rename(columns={
            'team': 'Team',
            'team_name': 'Team',
            'games': 'Games',
            'ats_wins': 'Wins',
            'ats_losses': 'Losses',
            'ats_pushes': 'Pushes',
            'ats_record': 'Record',
            'ats_pct': 'Win %'
        })

        # Add conditional formatting
        st.dataframe(
            ats_display.style.background_gradient(
                subset=['Win %'],
                cmap='RdYlGn',
                vmin=0.3,
                vmax=0.7
            ),
            use_container_width=True,
            hide_index=True
        )

        # Visualization
        st.subheader("ATS Win % Distribution")

        fig = px.bar(
            ats_records.sort_values('ats_pct', ascending=False),
            x='team' if 'team' in ats_records.columns else 'team_name',
            y='ats_pct',
            title=f"ATS Win % by Team ({selected_season})",
            labels={'ats_pct': 'ATS Win %', 'team': 'Team', 'team_name': 'Team'},
            color='ats_pct',
            color_continuous_scale='RdYlGn'
        )

        fig.update_layout(height=500, showlegend=False)
        fig.add_hline(y=0.5, line_dash="dash", line_color="gray",
                      annotation_text="Break Even (50%)")

        st.plotly_chart(fig, use_container_width=True)

        # Key insights
        st.subheader("🔍 Key Insights")

        col1, col2, col3 = st.columns(3)

        with col1:
            best_ats = ats_records.iloc[0]
            st.metric(
                "Best ATS Team",
                best_ats['team' if 'team' in ats_records.columns else 'team_name'],
                f"{best_ats['ats_pct']:.1%}"
            )

        with col2:
            worst_ats = ats_records.iloc[-1]
            st.metric(
                "Worst ATS Team",
                worst_ats['team' if 'team' in ats_records.columns else 'team_name'],
                f"{worst_ats['ats_pct']:.1%}"
            )

        with col3:
            avg_ats = ats_records['ats_pct'].mean()
            st.metric("League Average", f"{avg_ats:.1%}")

    else:
        st.warning("No ATS data available for this season.")

elif analysis_type == "Situational ATS":
    st.header("🎯 Situational ATS Analysis")
    st.markdown("ATS performance in different game situations")

    # Team selector
    selected_team = st.selectbox("Select Team (optional)", ["All Teams"] + teams_list)

    season_data = data['training'][data['training']['season'] == selected_season]

    if selected_team != "All Teams":
        season_data = season_data[season_data['team'] == selected_team]

    # Calculate situational ATS
    situational_ats = calculate_situational_ats(season_data)

    if situational_ats:
        # Create tabs for different situations
        tabs = st.tabs(["Favorite vs Underdog", "Overall", "Divisional"])

        with tabs[0]:
            st.subheader("ATS as Favorite vs Underdog")

            col1, col2 = st.columns(2)

            with col1:
                if 'as_favorite' in situational_ats and not situational_ats['as_favorite'].empty:
                    st.markdown("**As Favorite (negative spread)**")
                    fav_data = situational_ats['as_favorite']

                    if selected_team == "All Teams":
                        st.dataframe(
                            fav_data[['team' if 'team' in fav_data.columns else 'team_name',
                                      'games', 'ats_record', 'ats_pct']].rename(columns={
                                'team': 'Team', 'team_name': 'Team',
                                'games': 'Games', 'ats_record': 'Record', 'ats_pct': 'Win %'
                            }),
                            hide_index=True
                        )
                    else:
                        st.metric("As Favorite Record",
                                  fav_data['ats_record'].iloc[0] if len(fav_data) > 0 else "N/A")
                        st.metric("Win %",
                                  f"{fav_data['ats_pct'].iloc[0]:.1%}" if len(fav_data) > 0 else "N/A")

            with col2:
                if 'as_underdog' in situational_ats and not situational_ats['as_underdog'].empty:
                    st.markdown("**As Underdog (positive spread)**")
                    dog_data = situational_ats['as_underdog']

                    if selected_team == "All Teams":
                        st.dataframe(
                            dog_data[['team' if 'team' in dog_data.columns else 'team_name',
                                      'games', 'ats_record', 'ats_pct']].rename(columns={
                                'team': 'Team', 'team_name': 'Team',
                                'games': 'Games', 'ats_record': 'Record', 'ats_pct': 'Win %'
                            }),
                            hide_index=True
                        )
                    else:
                        st.metric("As Underdog Record",
                                  dog_data['ats_record'].iloc[0] if len(dog_data) > 0 else "N/A")
                        st.metric("Win %",
                                  f"{dog_data['ats_pct'].iloc[0]:.1%}" if len(dog_data) > 0 else "N/A")

        with tabs[1]:
            if 'overall' in situational_ats and not situational_ats['overall'].empty:
                st.subheader("Overall ATS Records")
                overall_data = situational_ats['overall']
                st.dataframe(
                    overall_data[['team' if 'team' in overall_data.columns else 'team_name',
                                  'games', 'ats_record', 'ats_pct']].rename(columns={
                        'team': 'Team', 'team_name': 'Team',
                        'games': 'Games', 'ats_record': 'Record', 'ats_pct': 'Win %'
                    }),
                    hide_index=True,
                    use_container_width=True
                )

        with tabs[2]:
            if 'divisional' in situational_ats and not situational_ats['divisional'].empty:
                st.subheader("Divisional Games ATS")
                div_data = situational_ats['divisional']
                st.dataframe(
                    div_data[['team' if 'team' in div_data.columns else 'team_name',
                              'games', 'ats_record', 'ats_pct']].rename(columns={
                        'team': 'Team', 'team_name': 'Team',
                        'games': 'Games', 'ats_record': 'Record', 'ats_pct': 'Win %'
                    }),
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("No divisional game data available.")

elif analysis_type == "Spread Analysis":
    st.header("📈 Spread vs Actual Margin Analysis")
    st.markdown("How teams perform relative to the spread")

    season_data = data['training'][data['training']['season'] == selected_season].copy()

    if not season_data.empty and all(col in season_data.columns for col in ['spread', 'score', 'against_score']):
        # Calculate actual margin
        season_data['margin'] = season_data['score'] - season_data['against_score']
        season_data['cover_margin'] = season_data['margin'] + season_data['spread']

        # Scatter plot: Spread vs Actual Margin
        st.subheader("Spread vs Actual Margin")

        fig = px.scatter(
            season_data,
            x='spread',
            y='margin',
            color='team',
            title=f"Spread vs Actual Margin ({selected_season})",
            labels={'spread': 'Spread', 'margin': 'Actual Margin'},
            hover_data=['team', 'week', 'against_team']
        )

        # Add 45-degree line (perfect prediction)
        fig.add_trace(go.Scatter(
            x=[-20, 20],
            y=[-20, 20],
            mode='lines',
            line=dict(color='gray', dash='dash'),
            name='Perfect Prediction',
            showlegend=True
        ))

        # Add cover line (spread = 0)
        fig.add_hline(y=0, line_dash="dot", line_color="red",
                      annotation_text="Actual Tie")
        fig.add_vline(x=0, line_dash="dot", line_color="blue",
                      annotation_text="Pick 'em")

        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)

        # Cover margin distribution
        st.subheader("Cover Margin Distribution")

        fig2 = px.histogram(
            season_data,
            x='cover_margin',
            nbins=50,
            title="Distribution of Cover Margins",
            labels={'cover_margin': 'Cover Margin (points)'},
            color_discrete_sequence=['steelblue']
        )

        fig2.add_vline(x=0, line_dash="dash", line_color="red",
                       annotation_text="Push Line")

        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)

        # Stats
        st.subheader("📊 Spread Statistics")

        col1, col2, col3 = st.columns(3)

        with col1:
            covers = (season_data['cover_margin'] > 0).sum()
            total = len(season_data)
            st.metric("Cover Rate", f"{covers/total:.1%}" if total > 0 else "N/A")

        with col2:
            avg_cover_margin = season_data['cover_margin'].mean()
            st.metric("Avg Cover Margin", f"{avg_cover_margin:+.1f} pts")

        with col3:
            pushes = (season_data['cover_margin'] == 0).sum()
            st.metric("Pushes", pushes)

    else:
        st.warning("Spread data not available for this season.")

elif analysis_type == "EPA-Based Edges":
    st.header("🎯 EPA-Based Betting Edges")
    st.markdown("Identify betting value using Expected Points Added metrics")

    if data['team_averages'] is not None and not data['team_averages'].empty:
        # Get latest week's data
        latest_week = data['team_averages'][
            data['team_averages']['season'] == selected_season
        ]['week'].max()

        latest_data = data['team_averages'][
            (data['team_averages']['season'] == selected_season) &
            (data['team_averages']['week'] == latest_week)
        ].copy()

        if not latest_data.empty and 'epa_per_play_offense' in latest_data.columns:
            # Create EPA quadrant chart
            st.subheader(f"EPA Quadrant Analysis (Week {latest_week})")

            team_col = 'team' if 'team' in latest_data.columns else 'team_name'

            fig = px.scatter(
                latest_data,
                x='epa_per_play_offense',
                y='epa_per_play_defense',
                text=team_col,
                title="Offensive vs Defensive EPA",
                labels={
                    'epa_per_play_offense': 'Offensive EPA (higher is better)',
                    'epa_per_play_defense': 'Defensive EPA allowed (lower is better)'
                }
            )

            # Add quadrant lines
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            fig.add_vline(x=0, line_dash="dash", line_color="gray")

            # Add quadrant labels
            fig.add_annotation(x=0.2, y=-0.2, text="Elite", showarrow=False,
                               font=dict(size=16, color="green"))
            fig.add_annotation(x=-0.2, y=-0.2, text="Good Defense", showarrow=False,
                               font=dict(size=14, color="blue"))
            fig.add_annotation(x=0.2, y=0.2, text="Good Offense", showarrow=False,
                               font=dict(size=14, color="orange"))
            fig.add_annotation(x=-0.2, y=0.2, text="Struggling", showarrow=False,
                               font=dict(size=16, color="red"))

            fig.update_traces(textposition='top center')
            fig.update_layout(height=600)

            st.plotly_chart(fig, use_container_width=True)

            # Top EPA teams
            st.subheader("🏆 Top EPA Performers")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Best Offenses (EPA/play)**")
                top_off = latest_data.nlargest(5, 'epa_per_play_offense')[
                    [team_col, 'epa_per_play_offense']
                ].rename(columns={team_col: 'Team', 'epa_per_play_offense': 'Off EPA'})

                st.dataframe(top_off, hide_index=True)

            with col2:
                st.markdown("**Best Defenses (EPA/play allowed)**")
                top_def = latest_data.nsmallest(5, 'epa_per_play_defense')[
                    [team_col, 'epa_per_play_defense']
                ].rename(columns={team_col: 'Team', 'epa_per_play_defense': 'Def EPA'})

                st.dataframe(top_def, hide_index=True)

        else:
            st.warning("EPA data not available for this season.")
    else:
        st.warning("Team averages data not available.")

# Over/Under Analysis
st.markdown("---")
st.header("🎲 Over/Under Analysis")

season_data = data['training'][data['training']['season'] == selected_season]
ou_records = calculate_over_under_record(season_data)

if not ou_records.empty:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Team O/U Records")

        ou_display = ou_records[['team' if 'team' in ou_records.columns else 'team_name',
                                  'games', 'overs', 'unders', 'ou_record', 'over_pct']].copy()

        ou_display = ou_display.rename(columns={
            'team': 'Team',
            'team_name': 'Team',
            'games': 'Games',
            'overs': 'Overs',
            'unders': 'Unders',
            'ou_record': 'O/U Record',
            'over_pct': 'Over %'
        })

        st.dataframe(
            ou_display.style.background_gradient(
                subset=['Over %'],
                cmap='coolwarm',
                vmin=0.3,
                vmax=0.7
            ),
            use_container_width=True,
            hide_index=True
        )

    with col2:
        st.subheader("League Trends")

        avg_over_pct = ou_records['over_pct'].mean()
        st.metric("Avg Over %", f"{avg_over_pct:.1%}")

        total_overs = ou_records['overs'].sum()
        total_unders = ou_records['unders'].sum()
        st.metric("League O/U", f"{total_overs}-{total_unders}")

# Footer
st.markdown("---")
st.markdown("""
**Betting Tips:**
- ATS win % above 55% suggests strong value
- EPA differentials help identify mismatched spreads
- Situational trends reveal betting patterns
- Always bet responsibly
""")
