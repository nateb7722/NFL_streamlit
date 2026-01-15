"""
Data processing and transformation utilities for NFL Dashboard V1
Business logic for team aggregates, EPA calculations, player grades, and injury impact
"""

import pandas as pd
import numpy as np
from datetime import datetime


# =============================================================================
# CORE FILTERING FUNCTIONS - Reused from V0
# =============================================================================

def get_current_week(training_data):
    """
    Determine the current NFL week based on the latest available data

    Args:
        training_data (pd.DataFrame): Training data with game results

    Returns:
        tuple: (current_season, current_week)
    """
    if training_data is None or training_data.empty:
        return (datetime.now().year, 1)

    max_season = training_data['season'].max()
    max_week = training_data[training_data['season'] == max_season]['week'].max()

    if pd.notna(max_week) and max_week < 18:
        return (int(max_season), int(max_week) + 1)
    else:
        return (int(max_season), int(max_week)) if pd.notna(max_week) else (int(max_season), 1)


def filter_by_season_week(df, seasons=None, weeks=None, teams=None):
    """
    Filter dataframe by season, week, and/or teams

    Args:
        df (pd.DataFrame): Input dataframe
        seasons (list, optional): List of seasons to include
        weeks (tuple or list, optional): Week range (min, max) or list of weeks
        teams (list, optional): List of teams to include

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    if df is None or df.empty:
        return df

    filtered_df = df.copy()

    if seasons is not None and len(seasons) > 0:
        filtered_df = filtered_df[filtered_df['season'].isin(seasons)]

    if weeks is not None:
        if isinstance(weeks, tuple) and len(weeks) == 2:
            filtered_df = filtered_df[
                (filtered_df['week'] >= weeks[0]) &
                (filtered_df['week'] <= weeks[1])
            ]
        elif isinstance(weeks, list):
            filtered_df = filtered_df[filtered_df['week'].isin(weeks)]

    if teams is not None and len(teams) > 0:
        team_col = 'team' if 'team' in filtered_df.columns else 'team_name' if 'team_name' in filtered_df.columns else None
        if team_col:
            filtered_df = filtered_df[filtered_df[team_col].isin(teams)]

    return filtered_df


# =============================================================================
# V1 TEAM AGGREGATE FUNCTIONS
# =============================================================================

def calculate_team_season_aggregates(df, team, season):
    """
    Calculate season-level aggregates for a team

    Args:
        df (pd.DataFrame): Team-week data
        team (str): Team name
        season (int): Season year

    Returns:
        dict: Aggregated metrics
    """
    team_data = df[(df['team'] == team) & (df['season'] == season)]

    if team_data.empty:
        return {}

    aggregates = {}

    # EPA metrics
    epa_cols = {
        'epa_mean': 'avg_offensive_epa',
        'against_epa_mean': 'avg_defensive_epa',
        'pass_epa_mean': 'avg_pass_epa',
        'run_epa_mean': 'avg_run_epa',
        'against_pass_epa_mean': 'avg_pass_epa_allowed',
        'against_run_epa_mean': 'avg_run_epa_allowed',
    }

    for col, key in epa_cols.items():
        if col in team_data.columns:
            aggregates[key] = team_data[col].mean()

    # Scoring metrics
    if 'score' in team_data.columns:
        aggregates['avg_points_scored'] = team_data['score'].mean()
    if 'against_score' in team_data.columns:
        aggregates['avg_points_allowed'] = team_data['against_score'].mean()

    # Opponent strength (if available)
    opp_cols = {
        'opp_against_epa_mean': 'avg_opp_offensive_epa',
        'opp_epa_mean': 'avg_opp_defensive_epa',
    }

    for col, key in opp_cols.items():
        if col in team_data.columns:
            aggregates[key] = team_data[col].mean()

    return aggregates


def calculate_league_season_aggregates(df, season, through_week=None):
    """
    Calculate EPA aggregates for all teams in a season

    Args:
        df (pd.DataFrame): Team-week data
        season (int): Season year
        through_week (int, optional): Include data up to this week

    Returns:
        pd.DataFrame: League-wide aggregates by team
    """
    season_data = df[df['season'] == season]

    if through_week is not None:
        season_data = season_data[season_data['week'] <= through_week]

    if season_data.empty:
        return pd.DataFrame()

    # Define aggregation columns based on what's available
    agg_dict = {}

    epa_cols = ['epa_mean', 'against_epa_mean', 'pass_epa_mean', 'run_epa_mean',
                'against_pass_epa_mean', 'against_run_epa_mean']

    for col in epa_cols:
        if col in season_data.columns:
            agg_dict[col] = 'mean'

    if 'score' in season_data.columns:
        agg_dict['score'] = 'mean'
    if 'against_score' in season_data.columns:
        agg_dict['against_score'] = 'mean'

    # Opponent strength columns
    for col in ['opp_against_epa_mean', 'opp_epa_mean']:
        if col in season_data.columns:
            agg_dict[col] = 'mean'

    if not agg_dict:
        return pd.DataFrame()

    league_agg = season_data.groupby('team').agg(agg_dict).reset_index()

    return league_agg


def calculate_records_by_situation(df, team, season):
    """
    Calculate W-L records by situation for a team

    Args:
        df (pd.DataFrame): Team-week data with game results
        team (str): Team name
        season (int): Season year

    Returns:
        dict: Records by situation
    """
    team_data = df[(df['team'] == team) & (df['season'] == season)]

    if team_data.empty:
        return {}

    records = {}

    # Calculate wins/losses
    if 'score' in team_data.columns and 'against_score' in team_data.columns:
        team_data = team_data.copy()
        team_data['win'] = team_data['score'] > team_data['against_score']
        team_data['loss'] = team_data['score'] < team_data['against_score']

        wins = team_data['win'].sum()
        losses = team_data['loss'].sum()
        records['overall_record'] = f"{wins}-{losses}"

        # Home/Away splits
        if 'home_game' in team_data.columns:
            home_games = team_data[team_data['home_game'] == 1]
            home_wins = home_games['win'].sum()
            home_losses = home_games['loss'].sum()
            records['home_record'] = f"{home_wins}-{home_losses}"

            away_games = team_data[team_data['home_game'] == 0]
            away_wins = away_games['win'].sum()
            away_losses = away_games['loss'].sum()
            records['road_record'] = f"{away_wins}-{away_losses}"

        # Favorite/Underdog splits
        if 'spread' in team_data.columns:
            favorites = team_data[team_data['spread'] < 0]
            fav_wins = favorites['win'].sum()
            fav_losses = favorites['loss'].sum()
            records['favorite_record'] = f"{fav_wins}-{fav_losses}"

            underdogs = team_data[team_data['spread'] > 0]
            dog_wins = underdogs['win'].sum()
            dog_losses = underdogs['loss'].sum()
            records['underdog_record'] = f"{dog_wins}-{dog_losses}"

    # ATS record
    if 'spread_cover' in team_data.columns:
        ats_wins = (team_data['spread_cover'] == 1).sum()
        ats_losses = (team_data['spread_cover'] == 0).sum()
        records['ats_record'] = f"{ats_wins}-{ats_losses}"

    # O/U record
    if 'total_cover' in team_data.columns:
        overs = (team_data['total_cover'] == 1).sum()
        unders = (team_data['total_cover'] == 0).sum()
        records['ou_record'] = f"{overs}-{unders}"

    return records


# =============================================================================
# BETTING CALCULATIONS - Reused from V0
# =============================================================================

def calculate_ats_record(training_data, team=None, location=None):
    """
    Calculate Against The Spread (ATS) record for team(s)

    Args:
        training_data (pd.DataFrame): Training data with spread and results
        team (str, optional): Specific team name
        location (str, optional): 'Home', 'Away', or None for all games

    Returns:
        pd.DataFrame: ATS record summary
    """
    if training_data is None or training_data.empty:
        return pd.DataFrame()

    df = training_data.copy()

    if team:
        df = df[df['team'] == team]

    # Use spread_cover flag if available
    if 'spread_cover' in df.columns:
        team_col = 'team' if 'team' in df.columns else 'team_name'

        ats_summary = df.groupby(team_col).agg(
            games=('spread_cover', 'count'),
            ats_wins=('spread_cover', 'sum'),
        ).reset_index()

        ats_summary['ats_losses'] = ats_summary['games'] - ats_summary['ats_wins']
        ats_summary['ats_record'] = (
            ats_summary['ats_wins'].astype(int).astype(str) + '-' +
            ats_summary['ats_losses'].astype(int).astype(str)
        )
        ats_summary['ats_pct'] = (
            ats_summary['ats_wins'] / ats_summary['games']
        ).round(3)

        return ats_summary.sort_values('ats_pct', ascending=False)

    # Fallback to calculating from spread/score if spread_cover not available
    if 'spread' in df.columns and 'score' in df.columns and 'against_score' in df.columns:
        df['margin'] = df['score'] - df['against_score']
        df['ats_result'] = df.apply(
            lambda row: 'W' if row['margin'] + row.get('spread', 0) > 0
            else 'L' if row['margin'] + row.get('spread', 0) < 0
            else 'P',
            axis=1
        )

        team_col = 'team' if 'team' in df.columns else 'team_name'

        ats_summary = df.groupby(team_col).agg(
            games=('ats_result', 'count'),
            ats_wins=('ats_result', lambda x: (x == 'W').sum()),
            ats_losses=('ats_result', lambda x: (x == 'L').sum()),
            ats_pushes=('ats_result', lambda x: (x == 'P').sum())
        ).reset_index()

        ats_summary['ats_record'] = (
            ats_summary['ats_wins'].astype(str) + '-' +
            ats_summary['ats_losses'].astype(str)
        )
        ats_summary['ats_pct'] = (
            ats_summary['ats_wins'] /
            (ats_summary['ats_wins'] + ats_summary['ats_losses'])
        ).round(3)

        return ats_summary.sort_values('ats_pct', ascending=False)

    return pd.DataFrame()


def calculate_over_under_record(training_data, team=None):
    """
    Calculate Over/Under record

    Args:
        training_data (pd.DataFrame): Game data with total_line
        team (str, optional): Specific team

    Returns:
        pd.DataFrame: O/U record summary
    """
    if training_data is None or training_data.empty:
        return pd.DataFrame()

    df = training_data.copy()

    if team:
        df = df[df['team'] == team]

    # Use total_cover flag if available
    if 'total_cover' in df.columns:
        team_col = 'team' if 'team' in df.columns else 'team_name'

        ou_summary = df.groupby(team_col).agg(
            games=('total_cover', 'count'),
            overs=('total_cover', 'sum'),
        ).reset_index()

        ou_summary['unders'] = ou_summary['games'] - ou_summary['overs']
        ou_summary['ou_record'] = (
            ou_summary['overs'].astype(int).astype(str) + '-' +
            ou_summary['unders'].astype(int).astype(str)
        )
        ou_summary['over_pct'] = (
            ou_summary['overs'] / ou_summary['games']
        ).round(3)

        return ou_summary

    # Fallback calculation
    if all(col in df.columns for col in ['score', 'against_score', 'total_line']):
        df['total_points'] = df['score'] + df['against_score']
        df['ou_result'] = df.apply(
            lambda row: 'O' if row['total_points'] > row.get('total_line', 0)
            else 'U' if row['total_points'] < row.get('total_line', 0)
            else 'P',
            axis=1
        )

        team_col = 'team' if 'team' in df.columns else 'team_name'

        ou_summary = df.groupby(team_col).agg(
            games=('ou_result', 'count'),
            overs=('ou_result', lambda x: (x == 'O').sum()),
            unders=('ou_result', lambda x: (x == 'U').sum()),
            pushes=('ou_result', lambda x: (x == 'P').sum())
        ).reset_index()

        ou_summary['ou_record'] = (
            ou_summary['overs'].astype(str) + '-' +
            ou_summary['unders'].astype(str)
        )
        ou_summary['over_pct'] = (
            ou_summary['overs'] /
            (ou_summary['overs'] + ou_summary['unders'])
        ).round(3)

        return ou_summary

    return pd.DataFrame()


def calculate_situational_ats(training_data):
    """
    Calculate ATS records in different situations

    Args:
        training_data (pd.DataFrame): Game data with spread results

    Returns:
        dict: Dictionary of situational ATS dataframes
    """
    if training_data is None or training_data.empty:
        return {}

    df = training_data.copy()
    results = {}

    results['overall'] = calculate_ats_record(df)

    if 'spread' in df.columns:
        favorites = df[df['spread'] < 0]
        underdogs = df[df['spread'] > 0]

        results['as_favorite'] = calculate_ats_record(favorites)
        results['as_underdog'] = calculate_ats_record(underdogs)

    return results


# =============================================================================
# V1 PLAYER GRADE FUNCTIONS
# =============================================================================

def aggregate_player_grades_by_category(weekly_starters_off, weekly_starters_def,
                                         team, week, season):
    """
    Aggregate player grades into categories for a specific team/week

    Args:
        weekly_starters_off: Weekly offense depth chart DataFrame
        weekly_starters_def: Weekly defense depth chart DataFrame
        team: Team name
        week: Week number
        season: Season year

    Returns:
        dict with grade categories (pass_blocking, run_blocking, etc.)
    """
    grades = {}

    # Filter offense data
    if weekly_starters_off is not None:
        off_data = weekly_starters_off[
            (weekly_starters_off['team'] == team) &
            (weekly_starters_off['week'] == week) &
            (weekly_starters_off['season'] == season)
        ]

        if not off_data.empty:
            # Offensive line grades
            ol_positions = ['T', 'G', 'C', 'OT', 'OG', 'LT', 'RT', 'LG', 'RG']
            ol_data = off_data[off_data['position'].isin(ol_positions)]

            if 'grades_pass_block' in off_data.columns:
                grades['pass_blocking'] = ol_data['grades_pass_block'].mean() if not ol_data.empty else np.nan
            if 'grades_run_block' in off_data.columns:
                grades['run_blocking'] = ol_data['grades_run_block'].mean() if not ol_data.empty else np.nan

            # QB grades
            qb_data = off_data[off_data['position'] == 'QB']
            if 'grades_pass' in off_data.columns:
                grades['qb_passing'] = qb_data['grades_pass'].mean() if not qb_data.empty else np.nan
            if 'grades_run' in off_data.columns:
                grades['qb_running'] = qb_data['grades_run'].mean() if not qb_data.empty else np.nan

            # Receiver grades
            rec_positions = ['WR', 'TE']
            rec_data = off_data[off_data['position'].isin(rec_positions)]
            if 'grades_receiving' in off_data.columns:
                grades['receiving'] = rec_data['grades_receiving'].mean() if not rec_data.empty else np.nan

            # RB grades
            rb_data = off_data[off_data['position'] == 'RB']
            if 'grades_offense' in off_data.columns:
                grades['rb_rushing'] = rb_data['grades_offense'].mean() if not rb_data.empty else np.nan

    # Filter defense data
    if weekly_starters_def is not None:
        def_data = weekly_starters_def[
            (weekly_starters_def['team'] == team) &
            (weekly_starters_def['week'] == week) &
            (weekly_starters_def['season'] == season)
        ]

        if not def_data.empty:
            if 'run_defense_grade' in def_data.columns:
                grades['run_defense'] = def_data['run_defense_grade'].mean()
            if 'coverage_grade' in def_data.columns:
                grades['pass_defense'] = def_data['coverage_grade'].mean()
                grades['coverage'] = def_data['coverage_grade'].mean()
            if 'defense_grade' in def_data.columns:
                grades['overall_defense'] = def_data['defense_grade'].mean()
            if 'pass_rush_grade' in def_data.columns:
                grades['pass_rush'] = def_data['pass_rush_grade'].mean()

    return grades


def calculate_injury_impact_by_week(healthy_off, healthy_def, weekly_off, weekly_def,
                                    team, season):
    """
    Calculate grade differences across all weeks for injury impact analysis

    Args:
        healthy_off: Healthy offense depth chart DataFrame
        healthy_def: Healthy defense depth chart DataFrame
        weekly_off: Weekly offense depth chart DataFrame
        weekly_def: Weekly defense depth chart DataFrame
        team: Team name
        season: Season year

    Returns:
        DataFrame with columns: week, category, healthy_grade, weekly_grade, difference
    """
    if weekly_off is None:
        return pd.DataFrame()

    # Get weeks for this team/season
    team_weeks = weekly_off[
        (weekly_off['team'] == team) &
        (weekly_off['season'] == season)
    ]['week'].unique()

    impact_data = []

    for week in sorted(team_weeks):
        healthy_grades = aggregate_player_grades_by_category(
            healthy_off, healthy_def, team, week, season
        )
        weekly_grades = aggregate_player_grades_by_category(
            weekly_off, weekly_def, team, week, season
        )

        for category in healthy_grades.keys():
            healthy_val = healthy_grades.get(category, np.nan)
            weekly_val = weekly_grades.get(category, np.nan)

            if pd.notna(healthy_val) and pd.notna(weekly_val):
                diff = weekly_val - healthy_val
            else:
                diff = np.nan

            impact_data.append({
                'week': int(week),
                'category': category,
                'healthy_grade': healthy_val,
                'weekly_grade': weekly_val,
                'difference': diff
            })

    return pd.DataFrame(impact_data)


def get_team_weekly_data(df, team, season):
    """
    Get weekly performance data for a team

    Args:
        df: Team-week DataFrame
        team: Team name
        season: Season year

    Returns:
        DataFrame with weekly data sorted by week
    """
    if df is None:
        return pd.DataFrame()

    team_data = df[(df['team'] == team) & (df['season'] == season)]
    return team_data.sort_values('week')


# =============================================================================
# EPA DIFFERENTIAL CALCULATIONS
# =============================================================================

def calculate_epa_differential(team_averages, team1, team2, season, week=None):
    """
    Calculate EPA differential between two teams

    Args:
        team_averages (pd.DataFrame): Team performance data
        team1 (str): First team
        team2 (str): Second team
        season (int): Season
        week (int, optional): Up to this week

    Returns:
        dict: EPA differential metrics
    """
    if team_averages is None or team_averages.empty:
        return {}

    team_col = 'team' if 'team' in team_averages.columns else 'team_name'

    # Get latest data for both teams
    team1_data = team_averages[
        (team_averages[team_col] == team1) &
        (team_averages['season'] == season)
    ]
    team2_data = team_averages[
        (team_averages[team_col] == team2) &
        (team_averages['season'] == season)
    ]

    if week is not None:
        team1_data = team1_data[team1_data['week'] <= week]
        team2_data = team2_data[team2_data['week'] <= week]

    if team1_data.empty or team2_data.empty:
        return {}

    result = {}

    # Calculate EPA differentials
    epa_col = 'epa_mean' if 'epa_mean' in team_averages.columns else 'epa_per_play_offense'
    def_epa_col = 'against_epa_mean' if 'against_epa_mean' in team_averages.columns else 'epa_per_play_defense'

    if epa_col in team_averages.columns:
        result['off_epa_diff'] = (
            team1_data[epa_col].mean() -
            team2_data[epa_col].mean()
        )

    if def_epa_col in team_averages.columns:
        result['def_epa_diff'] = (
            team2_data[def_epa_col].mean() -
            team1_data[def_epa_col].mean()
        )

    if 'off_epa_diff' in result and 'def_epa_diff' in result:
        result['total_epa_edge'] = result['off_epa_diff'] + result['def_epa_diff']

    return result
