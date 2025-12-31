"""
Utilities package for NFL Betting Analytics Dashboard
"""

from .data_loader import (
    get_s3_client,
    load_training_data_full_game,
    load_team_week_averages,
    load_strength_of_schedule,
    load_play_by_play
)

from .data_processor import (
    calculate_ats_record,
    calculate_betting_edges,
    get_current_week,
    filter_by_season_week
)

__all__ = [
    'get_s3_client',
    'load_training_data_full_game',
    'load_team_week_averages',
    'load_strength_of_schedule',
    'load_play_by_play',
    'calculate_ats_record',
    'calculate_betting_edges',
    'get_current_week',
    'filter_by_season_week'
]
