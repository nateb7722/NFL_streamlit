"""
Utilities package for NFL Betting Analytics Dashboard V1
"""

# V1 Data Loaders
from .data_loader import (
    get_s3_client,
    load_csv_from_s3,
    load_excel_from_s3,
    load_int_game_df_team_week,
    load_game_df_team_week_shifted,
    load_int_game_df,
    load_weekly_starters,
    load_healthy_starters,
    load_team_logos,
    get_available_teams,
    get_available_seasons,
    get_available_weeks,
    get_current_season_week,
    # Legacy
    load_training_data_full_game,
)

# V1 Data Processors
from .data_processor import (
    get_current_week,
    filter_by_season_week,
    calculate_team_season_aggregates,
    calculate_league_season_aggregates,
    calculate_records_by_situation,
    calculate_ats_record,
    calculate_over_under_record,
    calculate_situational_ats,
    aggregate_player_grades_by_category,
    calculate_injury_impact_by_week,
    get_team_weekly_data,
    calculate_epa_differential,
)

# Plotting utilities
from .plotting import (
    create_epa_scatter,
    create_weekly_epa_trend,
    create_weekly_epa_comparison,
    create_injury_impact_chart,
    create_grade_comparison_bar,
)

__all__ = [
    # Data Loaders
    'get_s3_client',
    'load_csv_from_s3',
    'load_excel_from_s3',
    'load_int_game_df_team_week',
    'load_game_df_team_week_shifted',
    'load_int_game_df',
    'load_weekly_starters',
    'load_healthy_starters',
    'load_team_logos',
    'get_available_teams',
    'get_available_seasons',
    'get_available_weeks',
    'get_current_season_week',
    'load_training_data_full_game',
    # Data Processors
    'get_current_week',
    'filter_by_season_week',
    'calculate_team_season_aggregates',
    'calculate_league_season_aggregates',
    'calculate_records_by_situation',
    'calculate_ats_record',
    'calculate_over_under_record',
    'calculate_situational_ats',
    'aggregate_player_grades_by_category',
    'calculate_injury_impact_by_week',
    'get_team_weekly_data',
    'calculate_epa_differential',
    # Plotting
    'create_epa_scatter',
    'create_weekly_epa_trend',
    'create_weekly_epa_comparison',
    'create_injury_impact_chart',
    'create_grade_comparison_bar',
]
