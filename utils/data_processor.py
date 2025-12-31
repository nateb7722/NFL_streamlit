"""
Data processing and transformation utilities
Business logic for ATS calculations, EPA differentials, and betting analytics
"""

import pandas as pd
import numpy as np
from datetime import datetime


def get_current_week(training_data):
    """
    Determine the current NFL week based on the latest available data

    Args:
        training_data (pd.DataFrame): Training data with game results

    Returns:
        tuple: (current_season, current_week)
    """
    if training_data is None or training_data.empty:
        # Default to week 1 of current year if no data
        return (datetime.now().year, 1)

    # Get the most recent season and week
    max_season = training_data['season'].max()
    max_week = training_data[training_data['season'] == max_season]['week'].max()

    # Return next week (current week to predict)
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

    # Filter by seasons
    if seasons is not None and len(seasons) > 0:
        filtered_df = filtered_df[filtered_df['season'].isin(seasons)]

    # Filter by weeks
    if weeks is not None:
        if isinstance(weeks, tuple) and len(weeks) == 2:
            # Week range (min, max)
            filtered_df = filtered_df[
                (filtered_df['week'] >= weeks[0]) &
                (filtered_df['week'] <= weeks[1])
            ]
        elif isinstance(weeks, list):
            # Specific weeks
            filtered_df = filtered_df[filtered_df['week'].isin(weeks)]

    # Filter by teams
    if teams is not None and len(teams) > 0:
        # Check if 'team' or 'team_name' column exists
        team_col = 'team' if 'team' in filtered_df.columns else 'team_name' if 'team_name' in filtered_df.columns else None
        if team_col:
            filtered_df = filtered_df[filtered_df[team_col].isin(teams)]

    return filtered_df


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

    # Filter by team
    if team:
        df = df[df['team'] == team]

    # Filter by location (assuming there's a way to identify home/away)
    # This depends on the data structure - adjust as needed
    # For now, skipping location filter unless column exists

    # Calculate ATS result if not already present
    # ATS Win: team covers the spread
    # Assuming spread is from team's perspective
    if 'spread' in df.columns and 'score' in df.columns and 'against_score' in df.columns:
        df['margin'] = df['score'] - df['against_score']
        df['ats_result'] = df.apply(
            lambda row: 'W' if row['margin'] + row.get('spread', 0) > 0
            else 'L' if row['margin'] + row.get('spread', 0) < 0
            else 'P',  # Push
            axis=1
        )

    # Group by team and calculate ATS record
    if 'ats_result' in df.columns:
        team_col = 'team' if 'team' in df.columns else 'team_name'

        ats_summary = df.groupby(team_col).agg(
            games=('ats_result', 'count'),
            ats_wins=('ats_result', lambda x: (x == 'W').sum()),
            ats_losses=('ats_result', lambda x: (x == 'L').sum()),
            ats_pushes=('ats_result', lambda x: (x == 'P').sum())
        ).reset_index()

        ats_summary['ats_record'] = (
            ats_summary['ats_wins'].astype(str) + '-' +
            ats_summary['ats_losses'].astype(str) +
            (ats_summary['ats_pushes'] > 0).apply(lambda x: '' if not x else '-') +
            ats_summary['ats_pushes'].apply(lambda x: '' if x == 0 else str(int(x)))
        )

        ats_summary['ats_pct'] = (
            ats_summary['ats_wins'] /
            (ats_summary['ats_wins'] + ats_summary['ats_losses'])
        ).round(3)

        return ats_summary.sort_values('ats_pct', ascending=False)

    return pd.DataFrame()


def calculate_betting_edges(training_data, team_averages, current_season, current_week):
    """
    Calculate betting edges based on EPA differentials and team performance

    Args:
        training_data (pd.DataFrame): Historical game data
        team_averages (pd.DataFrame): Team performance metrics with EPA
        current_season (int): Current season
        current_week (int): Current week

    Returns:
        pd.DataFrame: Betting edges with recommendations
    """
    if training_data is None or team_averages is None:
        return pd.DataFrame()

    # Get current week's matchups (if available in future data)
    # For now, calculate edges based on latest team performance

    # Filter team averages to most recent week
    latest_data = team_averages[
        (team_averages['season'] == current_season) &
        (team_averages['week'] == current_week - 1)  # Previous week's stats
    ].copy()

    if latest_data.empty:
        return pd.DataFrame()

    # Calculate offensive and defensive EPA rankings
    if 'epa_per_play_offense' in latest_data.columns:
        latest_data['off_epa_rank'] = latest_data['epa_per_play_offense'].rank(ascending=False)

    if 'epa_per_play_defense' in latest_data.columns:
        latest_data['def_epa_rank'] = latest_data['epa_per_play_defense'].rank(ascending=True)  # Lower defense EPA is better

    # Calculate overall edge score
    if 'off_epa_rank' in latest_data.columns and 'def_epa_rank' in latest_data.columns:
        latest_data['edge_score'] = (
            (latest_data['off_epa_rank'] + latest_data['def_epa_rank']) / 2
        )
        latest_data = latest_data.sort_values('edge_score')

    return latest_data


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

    # Calculate ATS result if needed
    if 'ats_result' not in df.columns and all(col in df.columns for col in ['score', 'against_score', 'spread']):
        df['margin'] = df['score'] - df['against_score']
        df['ats_result'] = df.apply(
            lambda row: 'W' if row['margin'] + row.get('spread', 0) > 0
            else 'L' if row['margin'] + row.get('spread', 0) < 0
            else 'P',
            axis=1
        )

    results = {}

    # Overall ATS
    results['overall'] = calculate_ats_record(df)

    # Home/Away splits (if identifiable)
    # This would require a column identifying home/away - adjust as needed

    # As favorite/underdog
    if 'spread' in df.columns:
        favorites = df[df['spread'] < 0]
        underdogs = df[df['spread'] > 0]

        results['as_favorite'] = calculate_ats_record(favorites)
        results['as_underdog'] = calculate_ats_record(underdogs)

    # Divisional games (if identifiable)
    if 'div_game' in df.columns:
        divisional = df[df['div_game'] == True]
        results['divisional'] = calculate_ats_record(divisional)

    return results


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

    # Calculate O/U result
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


def get_team_trends(team_averages, team, num_weeks=3):
    """
    Get recent performance trends for a team

    Args:
        team_averages (pd.DataFrame): Team performance data
        team (str): Team name
        num_weeks (int): Number of recent weeks to analyze

    Returns:
        pd.DataFrame: Recent performance trends
    """
    if team_averages is None or team_averages.empty:
        return pd.DataFrame()

    team_col = 'team' if 'team' in team_averages.columns else 'team_name'
    team_data = team_averages[team_averages[team_col] == team].copy()

    # Sort by season and week
    team_data = team_data.sort_values(['season', 'week'], ascending=False)

    # Get last N weeks
    recent = team_data.head(num_weeks)

    return recent


def identify_injury_impacts(play_by_play, depth_charts):
    """
    Identify games with significant injury impacts

    Args:
        play_by_play (pd.DataFrame): Play-by-play data with injury flags
        depth_charts (pd.DataFrame): Depth chart data

    Returns:
        pd.DataFrame: Games with injury flags
    """
    if play_by_play is None or play_by_play.empty:
        return pd.DataFrame()

    # Look for injury-related columns
    injury_cols = [col for col in play_by_play.columns if 'injury' in col.lower()]

    if injury_cols:
        # Filter to games with injuries
        injured_games = play_by_play[
            play_by_play[injury_cols].notna().any(axis=1)
        ].copy()

        return injured_games

    return pd.DataFrame()


def calculate_epa_differential(team_averages, team1, team2, season, week):
    """
    Calculate EPA differential between two teams

    Args:
        team_averages (pd.DataFrame): Team performance data
        team1 (str): First team
        team2 (str): Second team
        season (int): Season
        week (int): Week

    Returns:
        dict: EPA differential metrics
    """
    if team_averages is None or team_averages.empty:
        return {}

    team_col = 'team' if 'team' in team_averages.columns else 'team_name'

    # Get latest data for both teams
    team1_data = team_averages[
        (team_averages[team_col] == team1) &
        (team_averages['season'] == season) &
        (team_averages['week'] <= week)
    ].sort_values('week', ascending=False).head(1)

    team2_data = team_averages[
        (team_averages[team_col] == team2) &
        (team_averages['season'] == season) &
        (team_averages['week'] <= week)
    ].sort_values('week', ascending=False).head(1)

    if team1_data.empty or team2_data.empty:
        return {}

    result = {}

    # Offensive EPA differential
    if 'epa_per_play_offense' in team_averages.columns:
        result['off_epa_diff'] = (
            team1_data['epa_per_play_offense'].values[0] -
            team2_data['epa_per_play_offense'].values[0]
        )

    # Defensive EPA differential
    if 'epa_per_play_defense' in team_averages.columns:
        result['def_epa_diff'] = (
            team2_data['epa_per_play_defense'].values[0] -
            team1_data['epa_per_play_defense'].values[0]
        )

    # Overall EPA edge
    if 'off_epa_diff' in result and 'def_epa_diff' in result:
        result['total_epa_edge'] = result['off_epa_diff'] + result['def_epa_diff']

    return result
