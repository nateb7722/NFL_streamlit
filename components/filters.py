"""
Reusable filter components for NFL Streamlit Dashboard V1
Provides consistent filter UI across all pages
"""

import streamlit as st


def render_team_selector(teams_list, key="team_select", multi=False, label="Select Team",
                         default=None):
    """
    Render a team selector dropdown

    Args:
        teams_list (list): Available teams
        key (str): Unique key for the widget
        multi (bool): Allow multiple team selection
        label (str): Label for the selector
        default: Default selection

    Returns:
        str or list: Selected team(s)
    """
    if not teams_list:
        st.warning("No teams available")
        return None if not multi else []

    if multi:
        return st.multiselect(
            label,
            options=teams_list,
            default=default,
            key=key
        )
    else:
        index = 0
        if default and default in teams_list:
            index = teams_list.index(default)
        return st.selectbox(
            label,
            options=teams_list,
            index=index,
            key=key
        )


def render_season_selector(seasons_list, key="season_select", label="Season", default=None):
    """
    Render a season selector dropdown

    Args:
        seasons_list (list): Available seasons (should be sorted descending)
        key (str): Unique key for the widget
        label (str): Label for the selector
        default: Default selection

    Returns:
        int: Selected season
    """
    if not seasons_list:
        st.warning("No seasons available")
        return None

    index = 0
    if default and default in seasons_list:
        index = seasons_list.index(default)

    return st.selectbox(
        label,
        options=seasons_list,
        index=index,
        key=key
    )


def render_week_selector(weeks_list, key="week_select", label="Week",
                         include_all=True, default=None):
    """
    Render a week selector dropdown

    Args:
        weeks_list (list): Available weeks
        key (str): Unique key for the widget
        label (str): Label for the selector
        include_all (bool): Include "All Weeks" option
        default: Default selection

    Returns:
        int or str: Selected week or "All"
    """
    if not weeks_list:
        st.warning("No weeks available")
        return None

    if include_all:
        options = ["All Weeks"] + list(weeks_list)
    else:
        options = list(weeks_list)

    index = 0
    if default:
        if default == "All Weeks" and include_all:
            index = 0
        elif default in options:
            index = options.index(default)

    selected = st.selectbox(
        label,
        options=options,
        index=index,
        key=key
    )

    if selected == "All Weeks":
        return None  # Return None to indicate all weeks
    return selected


def render_season_week_filters(seasons_list, weeks_list=None, default_season=None,
                                default_week=None, key_prefix=""):
    """
    Render season and week filters side by side

    Args:
        seasons_list (list): Available seasons
        weeks_list (list, optional): Available weeks
        default_season (int, optional): Default season
        default_week (int, optional): Default week
        key_prefix (str): Prefix for widget keys

    Returns:
        dict: Selected season and week values
    """
    col1, col2 = st.columns(2)

    with col1:
        if not default_season and seasons_list:
            default_season = seasons_list[0]  # Most recent

        selected_season = render_season_selector(
            seasons_list,
            key=f"{key_prefix}season",
            default=default_season
        )

    with col2:
        # Default weeks_list if not provided
        if weeks_list is None:
            weeks_list = list(range(1, 19))

        selected_week = render_week_selector(
            weeks_list,
            key=f"{key_prefix}week",
            include_all=True,
            default=default_week
        )

    return {
        'season': selected_season,
        'week': selected_week
    }


def render_division_conference_filter(df, key="div_conf_filter"):
    """
    Render division/conference filter dropdown

    Args:
        df: DataFrame with 'division' and 'conference' columns
        key: Unique key for widget

    Returns:
        str: Selected filter value (e.g., "All Teams", "NFC East", "AFC")
    """
    options = ["All Teams"]

    # Add conferences
    if df is not None and 'conference' in df.columns:
        conferences = df['conference'].dropna().unique().tolist()
        options.extend(sorted(conferences))

    # Add divisions
    if df is not None and 'division' in df.columns:
        divisions = df['division'].dropna().unique().tolist()
        options.extend(sorted(divisions))

    selected = st.selectbox("Filter by Division/Conference", options, key=key)

    return selected


def apply_division_conference_filter(df, filter_value):
    """
    Apply division/conference filter to dataframe

    Args:
        df: DataFrame to filter
        filter_value: Selected filter value from render_division_conference_filter

    Returns:
        DataFrame: Filtered dataframe
    """
    if filter_value == "All Teams" or filter_value is None:
        return df

    if df is None:
        return df

    # Check if it's a conference filter
    if 'conference' in df.columns and filter_value in df['conference'].unique():
        return df[df['conference'] == filter_value]

    # Check if it's a division filter
    if 'division' in df.columns and filter_value in df['division'].unique():
        return df[df['division'] == filter_value]

    return df


def render_matchup_selector(game_df, season, week=None, key="matchup_select"):
    """
    Render matchup dropdown for selecting a specific game

    Args:
        game_df: DataFrame with home_team, away_team columns
        season: Current season
        week: Specific week (optional)
        key: Unique key for widget

    Returns:
        tuple: (home_team, away_team) or (None, None)
    """
    if game_df is None or game_df.empty:
        st.warning("No matchup data available")
        return None, None

    # Filter to season
    matchups = game_df[game_df['season'] == season]

    if week is not None:
        matchups = matchups[matchups['week'] == week]

    if matchups.empty:
        st.warning("No matchups found for selected criteria")
        return None, None

    # Create matchup options
    matchup_options = []
    for _, row in matchups[['home_team', 'away_team', 'week']].drop_duplicates().iterrows():
        matchup_options.append(
            f"{row['away_team']} @ {row['home_team']} (Week {int(row['week'])})"
        )

    if not matchup_options:
        return None, None

    selected = st.selectbox("Select Matchup", matchup_options, key=key)

    if selected:
        # Parse selection
        parts = selected.split(" @ ")
        away_team = parts[0]
        home_parts = parts[1].split(" (Week ")
        home_team = home_parts[0]
        return home_team, away_team

    return None, None


def render_sidebar_filters(df, show_division=True, show_week=True, key_prefix="sidebar_"):
    """
    Render standard sidebar filters for team/season/week

    Args:
        df: DataFrame to extract options from
        show_division: Show division/conference filter
        show_week: Show week filter
        key_prefix: Prefix for widget keys

    Returns:
        dict: Filter selections
    """
    st.sidebar.header("Filters")

    filters = {}

    # Get available options from data
    if df is not None:
        # Season filter
        seasons = df['season'].dropna().unique().tolist()
        seasons = sorted([int(s) for s in seasons], reverse=True)

        filters['season'] = render_season_selector(
            seasons,
            key=f"{key_prefix}season",
            label="Season"
        )

        # Week filter
        if show_week:
            if filters['season']:
                weeks = df[df['season'] == filters['season']]['week'].dropna().unique().tolist()
                weeks = sorted([int(w) for w in weeks])
            else:
                weeks = list(range(1, 19))

            filters['week'] = render_week_selector(
                weeks,
                key=f"{key_prefix}week",
                label="Through Week",
                include_all=True
            )
        else:
            filters['week'] = None

        # Division/Conference filter
        if show_division:
            filters['div_conf'] = render_division_conference_filter(
                df,
                key=f"{key_prefix}div_conf"
            )
        else:
            filters['div_conf'] = "All Teams"

    return filters


def render_global_filters(teams_list, seasons_list, default_season=None):
    """
    [Legacy] Render consistent filters across all pages

    Args:
        teams_list (list): Available teams
        seasons_list (list): Available seasons
        default_season (int, optional): Default selected season

    Returns:
        dict: Selected filter values
    """
    st.sidebar.header("Filters")

    if not default_season and seasons_list:
        default_season = max(seasons_list)

    selected_seasons = st.sidebar.multiselect(
        "Season(s)",
        options=seasons_list,
        default=[default_season] if default_season else []
    )

    week_range = st.sidebar.slider(
        "Week Range",
        min_value=1,
        max_value=18,
        value=(1, 18),
        help="Select the range of weeks to analyze"
    )

    selected_teams = st.sidebar.multiselect(
        "Team(s)",
        options=teams_list,
        default=None,
        help="Leave empty to include all teams"
    )

    return {
        'seasons': selected_seasons,
        'weeks': week_range,
        'teams': selected_teams if selected_teams else None,
    }
