"""
Data loading utilities for NFL Betting Analytics Dashboard
Handles S3 connections and data caching
"""

import boto3
import pandas as pd
import streamlit as st
import os
import sys
from io import BytesIO
import time

# Add parent directory to path to import secrets_env
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from secrets_env import *


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


@st.cache_data(ttl=3600)
def load_training_data_full_game():
    """
    Load main training dataset with ATS, spreads, scores

    Returns:
        pd.DataFrame: Training data with betting information
    """
    df = load_csv_from_s3('Prod/core/training_data_full_game.csv')

    if df is not None:
        # Data type conversions
        if 'game_date' in df.columns:
            df['game_date'] = pd.to_datetime(df['game_date'], errors='coerce')

        # Ensure numeric columns
        numeric_cols = ['season', 'week', 'score', 'against_score', 'total_line']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


@st.cache_data(ttl=3600)
def load_team_week_averages():
    """
    Load 3-week rolling averages with EPA metrics

    Returns:
        pd.DataFrame: Team performance metrics with rolling averages
    """
    df = load_csv_from_s3('Prod/core/game_df_team_week_averages_3_week_sequence.csv')

    if df is not None:
        # Ensure numeric columns
        numeric_cols = ['season', 'week']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


@st.cache_data(ttl=3600)
def load_strength_of_schedule():
    """
    Load strength of schedule data

    Returns:
        pd.DataFrame: Weekly strength of schedule metrics
    """
    df = load_csv_from_s3('Prod/core/weekly_strength_of_schedule.csv')

    if df is not None:
        # Ensure numeric columns
        numeric_cols = ['season', 'week']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


@st.cache_data(ttl=3600)
def load_play_by_play():
    """
    Load play-by-play data with injury adjustments

    Returns:
        pd.DataFrame: Play-by-play level data
    """
    df = load_csv_from_s3('Prod/core/play_by_play.csv')

    if df is not None:
        # Data type conversions
        if 'game_date' in df.columns:
            df['game_date'] = pd.to_datetime(df['game_date'], errors='coerce')

        numeric_cols = ['season', 'week']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


@st.cache_data(ttl=3600)
def load_team_week_shifted():
    """
    Load shifted team/week data for predictive modeling

    Returns:
        pd.DataFrame: Shifted team performance data
    """
    df = load_csv_from_s3('Prod/core/game_df_team_week_shifted.csv')

    if df is not None:
        numeric_cols = ['season', 'week']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


@st.cache_data(ttl=3600)
def load_player_ratings_grades(position_group):
    """
    Load player ratings grades for a specific position group

    Args:
        position_group (str): One of 'blocking', 'defense', 'passing', 'receiving',
                             'rushing', 'special_teams'

    Returns:
        pd.DataFrame: Player grades
    """
    file_key = f'Prod/core/player_ratings_{position_group}_grades.csv'
    df = load_csv_from_s3(file_key)

    if df is not None:
        numeric_cols = ['season']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


@st.cache_data(ttl=3600)
def load_player_ratings_stats(position_group):
    """
    Load player ratings stats for a specific position group

    Args:
        position_group (str): One of 'blocking', 'defense', 'passing', 'receiving',
                             'rushing', 'special_teams'

    Returns:
        pd.DataFrame: Player stats
    """
    file_key = f'Prod/core/player_ratings_{position_group}_stats.csv'
    df = load_csv_from_s3(file_key)

    if df is not None:
        numeric_cols = ['season']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


@st.cache_data(ttl=3600)
def load_depth_charts(chart_type):
    """
    Load depth chart data

    Args:
        chart_type (str): One of 'weekly_starters_offense', 'weekly_starters_defense',
                         'healthy_starters_offense', 'healthy_starters_defense'

    Returns:
        pd.DataFrame: Depth chart data
    """
    file_key = f'Prod/core/{chart_type}_depth_chart.csv'
    df = load_csv_from_s3(file_key)

    if df is not None:
        numeric_cols = ['season', 'week']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


@st.cache_data(ttl=3600)
def load_coaching_game_level():
    """
    Load coaching data by game

    Returns:
        pd.DataFrame: Coaching matchup data
    """
    df = load_csv_from_s3('Prod/core/coaching_game_level.csv')

    if df is not None:
        numeric_cols = ['season', 'week']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


@st.cache_data(ttl=3600)
def load_player_id_dictionary():
    """
    Load player ID mappings

    Returns:
        pd.DataFrame: Player ID cross-reference
    """
    return load_csv_from_s3('Prod/core/player_id_dictionary.csv')


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
        list: Sorted list of unique seasons
    """
    if df is None or 'season' not in df.columns:
        return []

    seasons = df['season'].dropna().unique().tolist()
    return sorted([int(s) for s in seasons if pd.notna(s)])


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
