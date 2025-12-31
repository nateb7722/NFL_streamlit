"""
Reusable filter components for consistent UX across pages
"""

import streamlit as st


def render_global_filters(teams_list, seasons_list, default_season=None):
    """
    Render consistent filters across all pages

    Args:
        teams_list (list): Available teams
        seasons_list (list): Available seasons
        default_season (int, optional): Default selected season

    Returns:
        dict: Selected filter values
    """
    st.sidebar.header("Filters")

    # Season selector
    if not default_season and seasons_list:
        default_season = max(seasons_list)

    selected_seasons = st.sidebar.multiselect(
        "Season(s)",
        options=seasons_list,
        default=[default_season] if default_season else []
    )

    # Week selector
    week_range = st.sidebar.slider(
        "Week Range",
        min_value=1,
        max_value=18,
        value=(1, 18),
        help="Select the range of weeks to analyze"
    )

    # Team selector
    selected_teams = st.sidebar.multiselect(
        "Team(s)",
        options=teams_list,
        default=None,
        help="Leave empty to include all teams"
    )

    # Location filter
    location = st.sidebar.radio(
        "Game Location",
        options=["All", "Home", "Away"],
        index=0,
        help="Filter by home/away games"
    )

    return {
        'seasons': selected_seasons,
        'weeks': week_range,
        'teams': selected_teams if selected_teams else None,
        'location': location
    }


def render_team_selector(teams_list, key="team_select", multi=False, label="Select Team"):
    """
    Render a team selector dropdown

    Args:
        teams_list (list): Available teams
        key (str): Unique key for the widget
        multi (bool): Allow multiple team selection
        label (str): Label for the selector

    Returns:
        str or list: Selected team(s)
    """
    if multi:
        return st.multiselect(
            label,
            options=teams_list,
            key=key
        )
    else:
        return st.selectbox(
            label,
            options=teams_list,
            key=key
        )


def render_season_week_filters(seasons_list, weeks_list=None, default_season=None):
    """
    Render season and week filters

    Args:
        seasons_list (list): Available seasons
        weeks_list (list, optional): Available weeks
        default_season (int, optional): Default season

    Returns:
        dict: Selected season and week values
    """
    col1, col2 = st.columns(2)

    with col1:
        if not default_season and seasons_list:
            default_season = max(seasons_list)

        selected_season = st.selectbox(
            "Season",
            options=seasons_list,
            index=seasons_list.index(default_season) if default_season in seasons_list else 0
        )

    with col2:
        if weeks_list:
            selected_week = st.selectbox(
                "Week",
                options=weeks_list
            )
        else:
            selected_week = st.slider(
                "Week",
                min_value=1,
                max_value=18,
                value=1
            )

    return {
        'season': selected_season,
        'week': selected_week
    }


def render_quick_filters():
    """
    Render quick filter presets

    Returns:
        str: Selected preset
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("Quick Filters")

    preset = st.sidebar.radio(
        "Select Preset",
        options=[
            "Custom",
            "Current Week",
            "Last 3 Weeks",
            "Last 5 Weeks",
            "Current Season",
            "Playoffs Only"
        ],
        index=0
    )

    return preset


def apply_quick_filter_preset(preset, current_season, current_week):
    """
    Convert preset selection to filter values

    Args:
        preset (str): Selected preset
        current_season (int): Current season
        current_week (int): Current week

    Returns:
        dict: Filter values based on preset
    """
    if preset == "Current Week":
        return {
            'seasons': [current_season],
            'weeks': (current_week, current_week)
        }
    elif preset == "Last 3 Weeks":
        return {
            'seasons': [current_season],
            'weeks': (max(1, current_week - 2), current_week)
        }
    elif preset == "Last 5 Weeks":
        return {
            'seasons': [current_season],
            'weeks': (max(1, current_week - 4), current_week)
        }
    elif preset == "Current Season":
        return {
            'seasons': [current_season],
            'weeks': (1, current_week)
        }
    elif preset == "Playoffs Only":
        return {
            'seasons': [current_season],
            'weeks': (19, 23)  # Playoff weeks
        }
    else:  # Custom
        return {}


def render_comparison_mode_toggle():
    """
    Render a toggle for comparison mode (single vs multiple teams)

    Returns:
        bool: True if comparison mode is enabled
    """
    return st.sidebar.checkbox(
        "Enable Team Comparison",
        value=False,
        help="Compare multiple teams side-by-side"
    )
