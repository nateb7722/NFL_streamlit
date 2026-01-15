"""
Plotting utilities for NFL Streamlit Dashboard V1
Creates EPA scatter plots, trend charts, and injury impact visualizations
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np


def create_epa_scatter(df, x_col, y_col, title, invert_x=False, invert_y=False,
                       logos_dict=None, team_col='team', x_label=None, y_label=None):
    """
    Create scatter plot with team logos or text markers

    Args:
        df: DataFrame with team data
        x_col: Column for x-axis
        y_col: Column for y-axis
        title: Chart title
        invert_x: Invert x-axis (for defensive metrics where lower is better)
        invert_y: Invert y-axis (for defensive metrics where lower is better)
        logos_dict: Dict mapping team names to logo URLs
        team_col: Column name for team identifier
        x_label: Custom x-axis label (optional)
        y_label: Custom y-axis label (optional)

    Returns:
        plotly.graph_objects.Figure
    """
    fig = go.Figure()

    # Calculate axis ranges for quadrant positioning
    x_min, x_max = df[x_col].min(), df[x_col].max()
    y_min, y_max = df[y_col].min(), df[y_col].max()
    x_range = x_max - x_min
    y_range = y_max - y_min

    if logos_dict:
        # Use team logos as markers via layout images
        for idx, row in df.iterrows():
            team = row[team_col]
            x_val = row[x_col]
            y_val = row[y_col]
            logo_url = logos_dict.get(team)

            if logo_url:
                # Add logo image at position
                fig.add_layout_image(
                    dict(
                        source=logo_url,
                        xref="x",
                        yref="y",
                        x=x_val,
                        y=y_val,
                        sizex=x_range * 0.06,
                        sizey=y_range * 0.06,
                        xanchor="center",
                        yanchor="middle",
                        layer="above"
                    )
                )

        # Add invisible scatter for hover functionality
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode='markers',
            marker=dict(size=30, opacity=0),
            text=df[team_col],
            customdata=df[[team_col, x_col, y_col]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>" +
                f"{x_label or x_col}: " + "%{customdata[1]:.3f}<br>" +
                f"{y_label or y_col}: " + "%{customdata[2]:.3f}<extra></extra>"
            )
        ))
    else:
        # Fallback to text markers with team abbreviations
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode='markers+text',
            text=df[team_col],
            textposition='top center',
            textfont=dict(size=10),
            marker=dict(size=12, color='steelblue', opacity=0.7),
            customdata=df[[team_col, x_col, y_col]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>" +
                f"{x_label or x_col}: " + "%{customdata[1]:.3f}<br>" +
                f"{y_label or y_col}: " + "%{customdata[2]:.3f}<extra></extra>"
            )
        ))

    # Add quadrant lines at 0,0
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)

    # Calculate padding for axis ranges
    x_padding = x_range * 0.1
    y_padding = y_range * 0.1

    # Axis configuration
    fig.update_xaxes(
        title=x_label or x_col.replace('_', ' ').title(),
        range=[x_max + x_padding, x_min - x_padding] if invert_x else [x_min - x_padding, x_max + x_padding],
        showgrid=True,
        gridwidth=1,
        gridcolor='lightgray'
    )
    fig.update_yaxes(
        title=y_label or y_col.replace('_', ' ').title(),
        range=[y_max + y_padding, y_min - y_padding] if invert_y else [y_min - y_padding, y_max + y_padding],
        showgrid=True,
        gridwidth=1,
        gridcolor='lightgray'
    )

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center'),
        hovermode='closest',
        height=500,
        showlegend=False,
        plot_bgcolor='white'
    )

    return fig


def create_weekly_epa_trend(df, team, season, team_col='team', week_col='week',
                            epa_col='epa_mean', color='steelblue'):
    """
    Create line chart showing weekly EPA trend for single team

    Args:
        df: DataFrame with weekly team data
        team: Team name to plot
        season: Season to filter
        team_col: Column name for team
        week_col: Column name for week
        epa_col: Column name for EPA metric
        color: Line color

    Returns:
        plotly.graph_objects.Figure
    """
    team_data = df[(df[team_col] == team) & (df['season'] == season)].sort_values(week_col)

    if team_data.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        return fig

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=team_data[week_col],
        y=team_data[epa_col],
        mode='lines+markers',
        name=team,
        line=dict(width=3, color=color),
        marker=dict(size=8, color=color),
        hovertemplate="Week %{x}<br>EPA: %{y:.3f}<extra></extra>"
    ))

    # Add reference line at 0
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

    fig.update_layout(
        title=dict(text=f"{team} Weekly EPA Trend - {season}", x=0.5, xanchor='center'),
        xaxis_title="Week",
        yaxis_title="EPA",
        hovermode='x unified',
        height=400,
        showlegend=True,
        plot_bgcolor='white'
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', dtick=1)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

    return fig


def create_weekly_epa_comparison(df, team_a, team_b, season, team_col='team',
                                 week_col='week', epa_col='epa_mean'):
    """
    Create line chart comparing weekly EPA for two teams

    Args:
        df: DataFrame with weekly team data
        team_a: First team name
        team_b: Second team name
        season: Season to filter
        team_col: Column name for team
        week_col: Column name for week
        epa_col: Column name for EPA metric

    Returns:
        plotly.graph_objects.Figure
    """
    team_a_data = df[(df[team_col] == team_a) & (df['season'] == season)].sort_values(week_col)
    team_b_data = df[(df[team_col] == team_b) & (df['season'] == season)].sort_values(week_col)

    fig = go.Figure()

    if not team_a_data.empty:
        fig.add_trace(go.Scatter(
            x=team_a_data[week_col],
            y=team_a_data[epa_col],
            mode='lines+markers',
            name=team_a,
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8),
            hovertemplate=f"{team_a}<br>Week %{{x}}<br>EPA: %{{y:.3f}}<extra></extra>"
        ))

    if not team_b_data.empty:
        fig.add_trace(go.Scatter(
            x=team_b_data[week_col],
            y=team_b_data[epa_col],
            mode='lines+markers',
            name=team_b,
            line=dict(color='#d62728', width=3),
            marker=dict(size=8),
            hovertemplate=f"{team_b}<br>Week %{{x}}<br>EPA: %{{y:.3f}}<extra></extra>"
        ))

    # Add reference line at 0
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

    fig.update_layout(
        title=dict(text=f"Weekly EPA Comparison - {season}", x=0.5, xanchor='center'),
        xaxis_title="Week",
        yaxis_title="EPA",
        hovermode='x unified',
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor='white'
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', dtick=1)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

    return fig


def create_injury_impact_chart(impact_df):
    """
    Create line chart showing aggregate injury impact across weeks

    Args:
        impact_df: DataFrame with columns: week, category, difference

    Returns:
        plotly.graph_objects.Figure
    """
    if impact_df is None or impact_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No injury impact data available", xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        return fig

    # Aggregate total difference by week
    weekly_impact = impact_df.groupby('week')['difference'].sum().reset_index()
    weekly_impact = weekly_impact.sort_values('week')

    fig = go.Figure()

    # Create color array based on values
    colors = ['red' if val < 0 else 'green' for val in weekly_impact['difference']]

    fig.add_trace(go.Scatter(
        x=weekly_impact['week'],
        y=weekly_impact['difference'],
        mode='lines+markers',
        name='Total Grade Impact',
        line=dict(width=3, color='gray'),
        marker=dict(size=10, color=colors, line=dict(width=2, color='black')),
        fill='tozeroy',
        fillcolor='rgba(128, 128, 128, 0.2)',
        hovertemplate="Week %{x}<br>Grade Impact: %{y:+.1f}<extra></extra>"
    ))

    # Add horizontal line at 0
    fig.add_hline(y=0, line_dash="dash", line_color="black", line_width=2)

    # Add zone annotations
    y_max = weekly_impact['difference'].max()
    y_min = weekly_impact['difference'].min()

    fig.update_layout(
        title=dict(
            text="Weekly Injury Impact (Grade Difference: Weekly vs Healthy Starters)",
            x=0.5, xanchor='center'
        ),
        xaxis_title="Week",
        yaxis_title="Total Grade Difference (Negative = Injury Impact)",
        hovermode='x unified',
        height=400,
        showlegend=False,
        plot_bgcolor='white'
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', dtick=1)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

    return fig


def create_grade_comparison_bar(team_a_name, team_a_grades, team_b_name, team_b_grades):
    """
    Create horizontal bar chart comparing player grades between two teams

    Args:
        team_a_name: Name of team A
        team_a_grades: Dict with category grades for team A
        team_b_name: Name of team B
        team_b_grades: Dict with category grades for team B

    Returns:
        plotly.graph_objects.Figure
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

    labels = [cat[1] for cat in categories]
    team_a_vals = [team_a_grades.get(cat[0], 0) for cat in categories]
    team_b_vals = [team_b_grades.get(cat[0], 0) for cat in categories]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name=team_a_name,
        y=labels,
        x=team_a_vals,
        orientation='h',
        marker_color='#1f77b4'
    ))

    fig.add_trace(go.Bar(
        name=team_b_name,
        y=labels,
        x=team_b_vals,
        orientation='h',
        marker_color='#d62728'
    ))

    fig.update_layout(
        title=dict(text="Player Grade Comparison by Category", x=0.5, xanchor='center'),
        barmode='group',
        height=500,
        xaxis_title="Grade",
        yaxis_title="Position Group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor='white'
    )

    return fig
