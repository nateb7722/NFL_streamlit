"""
Data loading utilities for NFL Betting Analytics Dashboard V1
Handles S3 connections and data caching with V1-approved datasets
"""

import boto3
import pandas as pd
import streamlit as st
import os
import sys
from io import BytesIO
import time

# Add parent directory to path to import secrets_config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import secrets_config  # This sets AWS environment variables


@st.cache_resource
def get_s3_client():
    """
    Initialize S3 client with cached connection

    Returns:
        boto3.client: S3 client instance
    """
    return boto3.client(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
    )


def load_csv_from_s3(file_key, max_retries=3):
    """
    Load a CSV file from S3 with retry logic

    Args:
        file_key (str): S3 object key/path
        max_retries (int): Maximum number of retry attempts

    Returns:
        pd.DataFrame: Loaded dataframe
    """
    s3 = get_s3_client()
    bucket = os.environ.get('AWS_S3_BUCKET')

    for attempt in range(max_retries):
        try:
            obj = s3.get_object(Bucket=bucket, Key=file_key)
            df = pd.read_csv(BytesIO(obj['Body'].read()))
            return df
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                st.error(f"Failed to load {file_key} after {max_retries} attempts: {str(e)}")
                return None


def load_excel_from_s3(file_key, max_retries=3):
    """
    Load an Excel file from S3 with retry logic

    Args:
        file_key (str): S3 object key/path
        max_retries (int): Maximum number of retry attempts

    Returns:
        pd.DataFrame: Loaded dataframe
    """
    s3 = get_s3_client()
    bucket = os.environ.get('AWS_S3_BUCKET')

    for attempt in range(max_retries):
        try:
            obj = s3.get_object(Bucket=bucket, Key=file_key)
            df = pd.read_excel(BytesIO(obj['Body'].read()), engine='openpyxl')
            return df
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            else:
                st.error(f"Failed to load {file_key} after {max_retries} attempts: {str(e)}")
                return None


# =============================================================================
# V1 DATA LOADERS - Primary datasets for V1 dashboard
# =============================================================================

@st.cache_data(ttl=3600)
def load_int_game_df_team_week():
    """
    Load team-week performance data (non-shifted)
    Contains EPA metrics, betting results, and team performance by week

    Returns:
        pd.DataFrame: Team-week performance data with 212 columns
    """
    df = load_csv_from_s3('Prod/int/int_game_df_team_week_2017_2025.csv')

    if df is not None:
        # Type conversions
        if 'game_date' in df.columns:
            df['game_date'] = pd.to_datetime(df['game_date'], errors='coerce')

        numeric_cols = ['season', 'week', 'score', 'against_score', 'spread', 'total_line']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


@st.cache_data(ttl=3600)
def load_game_df_team_week_shifted():
    """
    Load team-week pre-game data (shifted for predictions)
    Contains lag-1 shifted stats for making predictions before games

    Returns:
        pd.DataFrame: Shifted team-week data
    """
    df = load_csv_from_s3('Prod/core/game_df_team_week_shifted_2017_2025.csv')

    if df is not None:
        if 'game_date' in df.columns:
            df['game_date'] = pd.to_datetime(df['game_date'], errors='coerce')

        numeric_cols = ['season', 'week']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


@st.cache_data(ttl=3600)
def load_int_game_df():
    """
    Load game-level data with home/away team stats

    Returns:
        pd.DataFrame: Game-level data with 203 columns
    """
    df = load_csv_from_s3('Prod/int/int_game_df_2017_2025.csv')

    if df is not None:
        if 'game_date' in df.columns:
            df['game_date'] = pd.to_datetime(df['game_date'], errors='coerce')

        numeric_cols = ['season', 'week']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


@st.cache_data(ttl=3600)
def load_weekly_starters(side='offense'):
    """
    Load weekly starter depth charts with grades pre-merged

    Args:
        side (str): 'offense' or 'defense'

    Returns:
        pd.DataFrame: Weekly starter data with player grades
    """
    df = load_csv_from_s3(f'Prod/core/weekly_starters_depth_chart_{side}_2016_2025.csv')

    if df is not None:
        numeric_cols = ['season', 'week']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


@st.cache_data(ttl=3600)
def load_healthy_starters(side='offense'):
    """
    Load healthy starter depth charts with grades pre-merged

    Args:
        side (str): 'offense' or 'defense'

    Returns:
        pd.DataFrame: Healthy starter data with player grades
    """
    df = load_csv_from_s3(f'Prod/core/healthy_starters_depth_chart_{side}_2016_2025.csv')

    if df is not None:
        numeric_cols = ['season', 'week']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


@st.cache_data(ttl=3600)
def load_team_logos():
    """
    Load team logo mappings from Excel

    Returns:
        dict: Mapping of team names to logo URLs {team: url}
    """
    df = load_excel_from_s3('Prod/aux/team_logos_and_wordmarks/Team Logos.xlsx')

    if df is not None:
        # Try common column naming conventions
        team_col = None
        url_col = None

        # Find team column
        for col in ['team', 'team_name', 'Team', 'Team Name', 'team_abbr', 'Team Abbr']:
            if col in df.columns:
                team_col = col
                break

        # Find URL column
        for col in ['logo_url', 'url', 'Logo URL', 'URL', 'logo', 'Logo', 'team_logo_espn']:
            if col in df.columns:
                url_col = col
                break

        if team_col and url_col:
            return df.set_index(team_col)[url_col].to_dict()

        # If specific columns not found, try first two columns
        if len(df.columns) >= 2:
            return df.set_index(df.columns[0])[df.columns[1]].to_dict()

    return {}


# =============================================================================
# HELPER FUNCTIONS - Reused from V0
# =============================================================================

def get_available_teams(df):
    """
    Extract unique team names from a dataframe

    Args:
        df (pd.DataFrame): DataFrame containing 'team' or 'team_name' column

    Returns:
        list: Sorted list of unique team names
    """
    if df is None:
        return []

    team_col = 'team' if 'team' in df.columns else 'team_name' if 'team_name' in df.columns else None

    if team_col:
        teams = df[team_col].dropna().unique().tolist()
        return sorted(teams)

    return []


def get_available_seasons(df):
    """
    Extract unique seasons from a dataframe

    Args:
        df (pd.DataFrame): DataFrame containing 'season' column

    Returns:
        list: Sorted list of unique seasons (descending - most recent first)
    """
    if df is None or 'season' not in df.columns:
        return []

    seasons = df['season'].dropna().unique().tolist()
    return sorted([int(s) for s in seasons if pd.notna(s)], reverse=True)


def get_available_weeks(df, season=None):
    """
    Extract unique weeks from a dataframe, optionally filtered by season

    Args:
        df (pd.DataFrame): DataFrame containing 'week' column
        season (int, optional): Filter to specific season

    Returns:
        list: Sorted list of unique weeks
    """
    if df is None or 'week' not in df.columns:
        return []

    filtered_df = df if season is None else df[df['season'] == season]
    weeks = filtered_df['week'].dropna().unique().tolist()
    return sorted([int(w) for w in weeks if pd.notna(w)])


def get_current_season_week(df):
    """
    Determine the current NFL season and week based on the latest available data

    Args:
        df (pd.DataFrame): DataFrame with season and week columns

    Returns:
        tuple: (current_season, current_week)
    """
    if df is None or df.empty:
        from datetime import datetime
        return (datetime.now().year, 1)

    max_season = int(df['season'].max())
    max_week = int(df[df['season'] == max_season]['week'].max())

    return (max_season, max_week)


# =============================================================================
# LEGACY LOADERS - Kept for backwards compatibility if needed
# =============================================================================

@st.cache_data(ttl=3600)
def load_training_data_full_game():
    """
    [LEGACY] Load main training dataset with ATS, spreads, scores
    Note: This is V0 dataset - prefer load_int_game_df_team_week() for V1

    Returns:
        pd.DataFrame: Training data with betting information
    """
    df = load_csv_from_s3('Prod/core/training_data_full_game.csv')

    if df is not None:
        if 'game_date' in df.columns:
            df['game_date'] = pd.to_datetime(df['game_date'], errors='coerce')

        numeric_cols = ['season', 'week', 'score', 'against_score', 'total_line']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

    return df
