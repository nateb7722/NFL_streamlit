"""
Reusable metric display components for NFL Streamlit Dashboard V1
Provides consistent UI elements for metrics, team cards, and comparison tables
"""

import streamlit as st
import pandas as pd


def render_key_metrics(metrics_dict, cols=4):
    """
    Render key metrics in columns using st.metric

    Args:
        metrics_dict: Dict with {label: value} pairs or {label: (value, delta)} tuples
        cols: Number of columns
    """
    columns = st.columns(cols)
    items = list(metrics_dict.items())

    for idx, (label, value) in enumerate(items):
        with columns[idx % cols]:
            if isinstance(value, tuple):
                st.metric(label, value[0], delta=value[1])
            else:
                st.metric(label, value)


def render_team_header_card(team_name, team_data, logo_url=None):
    """
    Render team header card with logo and key records

    Args:
        team_name: Team name
        team_data: Dict with record information including:
            - overall_record, ats_record, ou_record
            - home_record, road_record
            - favorite_record, underdog_record
        logo_url: Optional team logo URL
    """
    col_logo, col_info = st.columns([1, 3])

    with col_logo:
        if logo_url:
            st.image(logo_url, width=100)
        else:
            st.markdown(f"### {team_name[:3].upper()}")

    with col_info:
        st.subheader(team_name)

        # Records row
        rec_cols = st.columns(4)
        with rec_cols[0]:
            st.metric("Record", team_data.get('overall_record', 'N/A'))
        with rec_cols[1]:
            st.metric("ATS", team_data.get('ats_record', 'N/A'))
        with rec_cols[2]:
            st.metric("O/U", team_data.get('ou_record', 'N/A'))
        with rec_cols[3]:
            st.metric("Avg EPA", team_data.get('avg_epa', 'N/A'))


def render_team_comparison_cards(team_a_name, team_a_data, team_b_name, team_b_data,
                                  logo_a_url=None, logo_b_url=None):
    """
    Render side-by-side team header cards for matchup comparison

    Args:
        team_a_name: Name of team A
        team_a_data: Dict with metrics for team A
        team_b_name: Name of team B
        team_b_data: Dict with metrics for team B
        logo_a_url: Logo URL for team A
        logo_b_url: Logo URL for team B
    """
    col_a, col_vs, col_b = st.columns([5, 1, 5])

    with col_a:
        st.markdown("---")
        if logo_a_url:
            st.image(logo_a_url, width=80)
        st.subheader(team_a_name)

        metrics_a = st.columns(3)
        with metrics_a[0]:
            st.metric("Record", team_a_data.get('overall_record', 'N/A'))
            st.metric("Home", team_a_data.get('home_record', 'N/A'))
        with metrics_a[1]:
            st.metric("ATS", team_a_data.get('ats_record', 'N/A'))
            st.metric("Favorite", team_a_data.get('favorite_record', 'N/A'))
        with metrics_a[2]:
            st.metric("O/U", team_a_data.get('ou_record', 'N/A'))
            st.metric("Road", team_a_data.get('road_record', 'N/A'))

    with col_vs:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("### VS")

    with col_b:
        st.markdown("---")
        if logo_b_url:
            st.image(logo_b_url, width=80)
        st.subheader(team_b_name)

        metrics_b = st.columns(3)
        with metrics_b[0]:
            st.metric("Record", team_b_data.get('overall_record', 'N/A'))
            st.metric("Home", team_b_data.get('home_record', 'N/A'))
        with metrics_b[1]:
            st.metric("ATS", team_b_data.get('ats_record', 'N/A'))
            st.metric("Favorite", team_b_data.get('favorite_record', 'N/A'))
        with metrics_b[2]:
            st.metric("O/U", team_b_data.get('ou_record', 'N/A'))
            st.metric("Road", team_b_data.get('road_record', 'N/A'))


def render_metrics_comparison_table(team_a_name, team_a_data, team_b_name, team_b_data):
    """
    Render side-by-side metrics comparison table

    Args:
        team_a_name: Name of team A
        team_a_data: Dict with metrics for team A
        team_b_name: Name of team B
        team_b_data: Dict with metrics for team B
    """
    metrics_keys = [
        ('avg_points_scored', 'Avg Points Scored'),
        ('avg_points_allowed', 'Avg Points Allowed'),
        ('avg_offensive_epa', 'Avg Offensive EPA'),
        ('avg_defensive_epa', 'Avg Defensive EPA'),
        ('avg_pass_epa', 'Avg Pass EPA'),
        ('avg_run_epa', 'Avg Run EPA'),
        ('avg_opp_offensive_epa', 'Avg Opp Offensive EPA'),
        ('avg_opp_defensive_epa', 'Avg Opp Defensive EPA'),
    ]

    comparison_data = []
    for key, label in metrics_keys:
        a_val = team_a_data.get(key, 'N/A')
        b_val = team_b_data.get(key, 'N/A')

        # Determine advantage
        try:
            a_num = float(a_val) if a_val != 'N/A' else None
            b_num = float(b_val) if b_val != 'N/A' else None

            if a_num is not None and b_num is not None:
                # For "allowed" and "against" metrics, lower is better
                lower_is_better = 'allowed' in key.lower() or 'against' in key.lower() or 'defensive' in key.lower()

                if lower_is_better:
                    if a_num < b_num:
                        advantage = team_a_name
                    elif b_num < a_num:
                        advantage = team_b_name
                    else:
                        advantage = "Even"
                else:
                    if a_num > b_num:
                        advantage = team_a_name
                    elif b_num > a_num:
                        advantage = team_b_name
                    else:
                        advantage = "Even"
            else:
                advantage = "N/A"
        except (ValueError, TypeError):
            advantage = "N/A"

        # Format values
        a_display = f"{a_val:.2f}" if isinstance(a_val, (int, float)) else str(a_val)
        b_display = f"{b_val:.2f}" if isinstance(b_val, (int, float)) else str(b_val)

        comparison_data.append({
            'Metric': label,
            team_a_name: a_display,
            team_b_name: b_display,
            'Advantage': advantage
        })

    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_player_grades_comparison(team_a_name, team_a_grades, team_b_name, team_b_grades):
    """
    Render player grades comparison table with 12 categories

    Args:
        team_a_name: Name of team A
        team_a_grades: Dict with category grades for team A
        team_b_name: Name of team B
        team_b_grades: Dict with category grades for team B
    """
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
        ('pass_rush', 'Pass Rush'),
        ('coverage', 'Coverage'),
    ]

    comparison_data = []

    for key, label in categories:
        a_grade = team_a_grades.get(key, 0) or 0
        b_grade = team_b_grades.get(key, 0) or 0

        # Handle NaN values
        if pd.isna(a_grade):
            a_grade = 0
        if pd.isna(b_grade):
            b_grade = 0

        diff = a_grade - b_grade

        if diff > 0:
            advantage = f"{team_a_name} +{diff:.1f}"
        elif diff < 0:
            advantage = f"{team_b_name} +{abs(diff):.1f}"
        else:
            advantage = "Even"

        comparison_data.append({
            'Position Group': label,
            f'{team_a_name} Grade': f"{a_grade:.1f}" if a_grade else "N/A",
            f'{team_b_name} Grade': f"{b_grade:.1f}" if b_grade else "N/A",
            'Advantage': advantage
        })

    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_injury_impact_table(healthy_grades, weekly_grades):
    """
    Render injury impact table showing healthy vs weekly starter grades

    Args:
        healthy_grades: Dict with category grades (healthy starters)
        weekly_grades: Dict with category grades (weekly starters)
    """
    category_labels = {
        'pass_blocking': 'Pass Blocking',
        'run_blocking': 'Run Blocking',
        'qb_passing': 'QB Passing',
        'qb_running': 'QB Running',
        'receiving': 'Receiving',
        'rb_rushing': 'RB Rushing',
        'run_defense': 'Run Defense',
        'pass_defense': 'Pass Defense',
        'overall_defense': 'Overall Defense',
        'pass_rush': 'Pass Rush',
        'coverage': 'Coverage',
    }

    impact_data = []

    for key, label in category_labels.items():
        healthy = healthy_grades.get(key, 0) or 0
        weekly = weekly_grades.get(key, 0) or 0

        # Handle NaN values
        if pd.isna(healthy):
            healthy = 0
        if pd.isna(weekly):
            weekly = 0

        diff = weekly - healthy

        if diff < -3:
            status = "Major Impact"
            status_color = "red"
        elif diff < 0:
            status = "Minor Impact"
            status_color = "orange"
        elif diff > 3:
            status = "Upgrade"
            status_color = "green"
        elif diff > 0:
            status = "Slight Upgrade"
            status_color = "lightgreen"
        else:
            status = "No Change"
            status_color = "gray"

        impact_data.append({
            'Position Group': label,
            'Healthy Grade': f"{healthy:.1f}" if healthy else "N/A",
            'Weekly Grade': f"{weekly:.1f}" if weekly else "N/A",
            'Difference': f"{diff:+.1f}",
            'Status': status
        })

    df = pd.DataFrame(impact_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_team_stats_table(team_data):
    """
    Render detailed team stats table

    Args:
        team_data: Dict with various team statistics
    """
    stats_config = [
        ('avg_points_scored', 'Avg Points Scored'),
        ('avg_points_allowed', 'Avg Points Allowed'),
        ('avg_offensive_epa', 'Avg Offensive EPA'),
        ('avg_defensive_epa', 'Avg Defensive EPA'),
        ('avg_pass_epa', 'Avg Pass EPA'),
        ('avg_run_epa', 'Avg Run EPA'),
        ('avg_pass_epa_allowed', 'Avg Pass EPA Allowed'),
        ('avg_run_epa_allowed', 'Avg Run EPA Allowed'),
        ('favorite_record', 'Record as Favorite'),
        ('underdog_record', 'Record as Underdog'),
        ('home_record', 'Home Record'),
        ('road_record', 'Road Record'),
    ]

    stats_data = []
    for key, label in stats_config:
        value = team_data.get(key, 'N/A')
        if isinstance(value, (int, float)):
            value = f"{value:.2f}"
        stats_data.append({
            'Metric': label,
            'Value': value
        })

    df = pd.DataFrame(stats_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
