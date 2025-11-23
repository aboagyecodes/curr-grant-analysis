"""
Chart Building Utilities

Creates Plotly charts for currency, commodity, and anomaly visualizations.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import COLORS


def create_currency_chart(fx_data, grants_data=None, commodity_data=None, 
                          show_commodities=True, title="Currency Analysis"):
    """
    Create main currency timeline chart with grants and commodity overlays
    
    Args:
        fx_data: DataFrame with date, rate columns
        grants_data: DataFrame with grant disbursements
        commodity_data: dict of {commodity_name: DataFrame}
        show_commodities: Whether to show commodity overlays
        title: Chart title
    
    Returns:
        plotly.graph_objects.Figure
    """
    # Create figure with secondary y-axis for commodities
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add currency line
    fig.add_trace(
        go.Scatter(
            x=fx_data['date'],
            y=fx_data['rate'],
            name='Currency Rate',
            line=dict(color=COLORS['currency_line'], width=2),
            mode='lines',
            hovertemplate='<b>Date:</b> %{x}<br><b>Rate:</b> %{y:.4f}<extra></extra>'
        ),
        secondary_y=False
    )
    
    # Add grant markers
    if grants_data is not None and len(grants_data) > 0:
        # Get FX rates at grant dates
        grant_rates = []
        for _, grant in grants_data.iterrows():
            grant_date = pd.to_datetime(grant['disbursement_date'])
            # Find closest FX rate
            # Ensure fx_data['date'] is datetime64[ns] for subtraction
            dates = pd.to_datetime(fx_data['date'])
            closest_idx = (dates - grant_date).abs().idxmin()
            grant_rate = fx_data.loc[closest_idx, 'rate']
            grant_rates.append(grant_rate)
        
        fig.add_trace(
            go.Scatter(
                x=grants_data['disbursement_date'],
                y=grant_rates,
                name='Grant Disbursements',
                mode='markers',
                marker=dict(
                    color=COLORS['grant_marker'],
                    size=8,
                    symbol='circle',
                    line=dict(color='white', width=1)
                ),
                hovertemplate='<b>Grant:</b> %{text}<br><b>Amount:</b> $%{customdata:,.0f}<extra></extra>',
                text=[f"{row['source']}" for _, row in grants_data.iterrows()],
                customdata=grants_data['amount_usd']
            ),
            secondary_y=False
        )
    
    # Add commodity overlays
    if show_commodities and commodity_data:
        colors = [COLORS['commodity_1'], COLORS['commodity_2']]
        for idx, (commodity_name, commodity_df) in enumerate(commodity_data.items()):
            if idx < 2:  # Only show top 2
                fig.add_trace(
                    go.Scatter(
                        x=commodity_df['date'],
                        y=commodity_df['price'],
                        name=commodity_name,
                        line=dict(color=colors[idx], width=1.5, dash='dot'),
                        opacity=0.7,
                        mode='lines',
                        hovertemplate=f'<b>{commodity_name}:</b> $%{{y:.2f}}<extra></extra>'
                    ),
                    secondary_y=True
                )
    
    # Update layout
    fig.update_xaxes(
        title_text="Date",
        rangeslider=dict(
            visible=True,
            thickness=0.02
        ),
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all", label="All")
            ]),
            bgcolor=COLORS['card_background'],
            activecolor=COLORS['grant_marker']
        )
    )
    
    fig.update_yaxes(title_text="Currency Rate (vs USD)", secondary_y=False)
    fig.update_yaxes(title_text="Commodity Price (USD)", secondary_y=True)
    
    fig.update_layout(
        title=title,
        hovermode='x unified',
        template='plotly_white',
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        plot_bgcolor=COLORS['card_background'],
        paper_bgcolor=COLORS['card_background']
    )
    
    return fig


def create_anomaly_chart(fx_data, anomaly, grants_data=None, title="Anomaly Investigation"):
    """
    Create focused chart for anomaly period
    
    Args:
        fx_data: Full FX data
        anomaly: Anomaly dict with start_date, end_date
        grants_data: Grant data
        title: Chart title
    
    Returns:
        plotly.graph_objects.Figure
    """
    start_date = pd.to_datetime(anomaly['start_date'])
    end_date = pd.to_datetime(anomaly['end_date'])
    
    # Add buffer
    from datetime import timedelta
    buffer_start = start_date - timedelta(days=7)
    buffer_end = end_date + timedelta(days=7)
    
    # Filter FX data
    mask = (fx_data['date'] >= buffer_start) & (fx_data['date'] <= buffer_end)
    focused_data = fx_data[mask].copy()
    
    fig = go.Figure()
    
    # Add currency line
    fig.add_trace(
        go.Scatter(
            x=focused_data['date'],
            y=focused_data['rate'],
            name='Currency Rate',
            line=dict(color=COLORS['currency_line'], width=2.5),
            mode='lines+markers',
            marker=dict(size=4)
        )
    )
    
    # Highlight anomaly period
    fig.add_vrect(
        x0=start_date, x1=end_date,
        fillcolor=COLORS['anomaly_highlight'],
        opacity=0.2,
        layer="below",
        line_width=0,
        annotation_text=f"{anomaly['change_percent']:.1f}% change",
        annotation_position="top left"
    )
    
    # Add grant markers if any
    if grants_data is not None and len(grants_data) > 0:
        grant_mask = ((grants_data['disbursement_date'] >= buffer_start) &
                     (grants_data['disbursement_date'] <= buffer_end))
        period_grants = grants_data[grant_mask]
        
        if len(period_grants) > 0:
            grant_rates = []
            for _, grant in period_grants.iterrows():
                grant_date = pd.to_datetime(grant['disbursement_date'])
                closest_idx = (focused_data['date'] - grant_date).abs().idxmin()
                grant_rate = focused_data.loc[closest_idx, 'rate']
                grant_rates.append(grant_rate)
            
            fig.add_trace(
                go.Scatter(
                    x=period_grants['disbursement_date'],
                    y=grant_rates,
                    name='Grant',
                    mode='markers',
                    marker=dict(
                        color=COLORS['grant_marker'],
                        size=10,
                        symbol='circle',
                        line=dict(color='white', width=1.5)
                    )
                )
            )
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Currency Rate (vs USD)",
        hovermode='x unified',
        template='plotly_white',
        height=500,
        plot_bgcolor=COLORS['card_background'],
        paper_bgcolor=COLORS['card_background']
    )
    
    return fig


def create_summary_metrics_chart(grant_analyses):
    """
    Create summary visualization of grant impact scores
    
    Args:
        grant_analyses: List of grant analysis results
    
    Returns:
        plotly.graph_objects.Figure
    """
    if not grant_analyses:
        return go.Figure()
    
    # Extract data
    dates = [analysis['grant_date'] for analysis in grant_analyses]
    scores = [analysis['impact_score'] for analysis in grant_analyses]
    sources = [analysis['grant_source'] for analysis in grant_analyses]
    
    # Create bar chart
    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(
            x=dates,
            y=scores,
            marker=dict(
                color=scores,
                colorscale=[[0, '#90EE90'], [0.5, '#FFD700'], [1, '#FF6347']],
                cmin=1,
                cmax=5,
                showscale=True,
                colorbar=dict(title="Impact<br>Score")
            ),
            text=[f"{s:.1f}" for s in scores],
            textposition='auto',
            hovertemplate='<b>Date:</b> %{x}<br><b>Score:</b> %{y:.2f}<br><b>Source:</b> %{customdata}<extra></extra>',
            customdata=sources
        )
    )
    
    fig.update_layout(
        title="Grant Impact Scores Over Time",
        xaxis_title="Grant Date",
        yaxis_title="Impact Score (1-5)",
        yaxis_range=[0, 5.5],
        template='plotly_white',
        height=400,
        plot_bgcolor=COLORS['card_background']
    )
    
    return fig


if __name__ == '__main__':
    print("Chart utilities loaded")
