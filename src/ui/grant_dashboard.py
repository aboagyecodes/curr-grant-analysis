"""
Grant Impact Analysis Dashboard

Visualizes grant-to-currency correlations with commodity influences.
"""

import streamlit as st
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import PILOT_CURRENCIES, ANALYSIS_WINDOWS
from src.utils.icons import load_material_icons_css, icon
from src.utils.quick_settings import render_quick_settings
from src.data_loaders.etl_grants import load_standardized_grants
from src.data_loaders.fx_loader import get_fx_data
from src.data_loaders.commodity_loader import get_all_commodities
from src.analysis.grant_impact import GrantImpactAnalyzer
from src.utils.charts import create_currency_chart, create_summary_metrics_chart


def render_grant_dashboard():
    """Render the Grant Impact Analysis Dashboard"""
    
    # Load Material Icons
    st.markdown(load_material_icons_css(), unsafe_allow_html=True)
    
    # Custom CSS for buttons (consistent with Anomaly Dashboard)
    st.markdown("""
    <style>
    div.stButton > button {
        border: 1px solid #4CAF50 !important;
        border-radius: 4px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f'<h1>{icon("analytics", 32)} Grant Impact Analysis Dashboard</h1>', unsafe_allow_html=True)
    
    # Check if configured
    if not st.session_state.get('config', {}).get('configured'):
        st.warning("⚠️ Please configure the app first!")
        st.info("Navigate to 'Configuration' in the sidebar.")
        return
    
    
    config = st.session_state['config']
    
    # Ensure selected_currency is valid
    if st.session_state['selected_currency'] not in config['currencies']:
        st.session_state['selected_currency'] = config['currencies'][0]
    
    # Quick Settings Panel (collapsible)
    render_quick_settings()
    st.sidebar.markdown("---")
    
    # SIDEBAR CONTROLS
    selected_currency = st.sidebar.selectbox(
        "Select Currency",
        options=config['currencies'],
        format_func=lambda x: f"{x} - {PILOT_CURRENCIES[x]['name']}",
        key='selected_currency'
    )
    
    currency_name = PILOT_CURRENCIES[selected_currency]['name']
    country_name = PILOT_CURRENCIES[selected_currency]['country']
    
    st.markdown(f"### Analysis for {currency_name} ({selected_currency})")
    
    # Load data
    with st.spinner("Loading data..."):
        # Load grants
        all_grants = load_standardized_grants()
        
        # Get the country name from currency and find matching grants
        country_name = PILOT_CURRENCIES[selected_currency]['country']
        
        # Filter grants by matching country_name field in grants data
        currency_grants = all_grants[
            (all_grants['country_name'] == country_name) &
            (all_grants['disbursement_date'] >= pd.to_datetime(config['start_date'])) &
            (all_grants['disbursement_date'] <= pd.to_datetime(config['end_date']))
        ]
        
        # Load FX data
        fx_data_dict = get_fx_data(
            [selected_currency],
            config['start_date'],
            config['end_date'],
            use_cache=True
        )
        fx_data = fx_data_dict.get(selected_currency, pd.DataFrame())
        
        # Load commodity data
        commodity_data_all = get_all_commodities(
            [selected_currency],
            config['start_date'],
            config['end_date'],
            use_cache=True
        )
        commodity_data = commodity_data_all.get(selected_currency, {})
    
    
    if fx_data.empty:
        st.error(f"❌ No FX data available for {selected_currency}")
        st.warning("""
        **Yahoo Finance API appears to be unavailable**
        
        This can happen due to API outages or rate limiting.
        
        **Solution: Generate sample data**
        Run this command in your terminal:
        ```bash
        cd /Users/clementaboagyeyeboah/Desktop/aboagyecodes/project
        source venv/bin/activate
        python create_sample_fx_data.py
        ```
        
        Then refresh this page and the app will use the generated CSV files.
        
        **Or upload your own FX data:**
        Place CSV files in `data/fx_rates/` with columns: date, rate, currency
        """)
        return
    
    # Summary Metrics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Grants", len(currency_grants))
    with col2:
        total_value = currency_grants['amount_usd'].sum() if len(currency_grants) > 0 else 0
        st.metric("Total Value", f"${total_value/1e9:.2f}B")
    with col3:
        date_range = (config['end_date'] - config['start_date']).days
        st.metric("Analysis Period", f"{date_range} days")
    with col4:
        current_rate = fx_data.iloc[-1]['rate'] if len(fx_data) > 0 else 0
        st.metric("Current Rate", f"{current_rate:.4f}")
    
    # Minimal FX data info under metrics
    st.caption(f"Data loaded: {len(fx_data)} FX points")
    
    st.markdown("---")
    
    # Main Visualization
    st.subheader("Currency & Commodity Trends")
    
    # Commodity controls in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Commodity Overlays")
    
    # Individual toggles for each commodity
    selected_commodities = []
    for commodity in PILOT_CURRENCIES[selected_currency]['commodities']:
        if st.sidebar.checkbox(commodity, value=True, key=f"commodity_{commodity}"):
            selected_commodities.append(commodity)
    
    # Filter commodity data to only show selected ones
    filtered_commodity_data = {k: v for k, v in commodity_data.items() if k in selected_commodities}
    
    # Grant Impact Analysis Settings in Sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Grant Impact Settings")
    
    analysis_preset = st.sidebar.selectbox(
        "Analysis Window",
        options=['custom', 'short_term', 'medium_term', 'long_term'],
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    if analysis_preset == 'custom':
        pre_weeks = st.sidebar.number_input("Pre-Grant (weeks)", min_value=1, max_value=52, value=4)
        post_weeks = st.sidebar.number_input("Post-Grant (weeks)", min_value=1, max_value=52, value=4)
    else:
        preset = ANALYSIS_WINDOWS[analysis_preset]
        pre_weeks = preset['pre']
        post_weeks = preset['post']
        st.sidebar.caption(f"Pre: {pre_weeks}w | Post: {post_weeks}w")
    
    # Run Analysis Button
    if st.sidebar.button("Analyze Grants", type="primary", use_container_width=True):
        if len(currency_grants) == 0:
            st.sidebar.warning("No grants found")
        else:
            with st.spinner("Analyzing grant impacts..."):
                analyzer = GrantImpactAnalyzer(fx_data, commodity_data, currency_grants)
                analyses = analyzer.analyze_all_grants(pre_weeks, post_weeks)
                st.session_state['grant_analyses'] = analyses
                st.sidebar.success(f"{len(analyses)} grants analyzed successfully")
    
    # About Section at Bottom
    st.sidebar.markdown("---")
    with st.sidebar.expander("ℹ️ About"):
        st.markdown("""
        **Grant Impact Analyzer**
        
        This tool analyzes the relationship between international grants and currency movements.
        
        **Logic:**
        - Analyzes FX trends before & after grant disbursements
        - Compares with commodity price movements
        - Scores impact based on trend deviation and stability
        
        **Data Sources:**
        - IMF & World Bank grant data
        - Yahoo Finance for FX & commodities
        """)
    
    # Main Chart (full width)
    fig = create_currency_chart(
        fx_data,
        grants_data=currency_grants,
        commodity_data=filtered_commodity_data,
        show_commodities=len(selected_commodities) > 0,
        title=f"{currency_name} vs USD with Grant Markers"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    
    # Display Analysis Results
    if 'grant_analyses' in st.session_state and st.session_state['grant_analyses'] is not None:
        st.markdown("---")
        st.subheader("Analysis Results")
        
        analyses = st.session_state['grant_analyses']
        
        # Best Grant Showcase
        if len(analyses) > 0:
            # Find the grant with the highest impact score
            best_grant = max(analyses, key=lambda x: x['impact_score'])
            
            st.markdown(f'<h3>{icon("emoji_events", 26)} Highest Impact Grant</h3>', unsafe_allow_html=True)
            
            # Create a visually appealing card for the best grant
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"**{best_grant['grant_source']}** — {best_grant['grant_date'].strftime('%B %Y')}")
                st.markdown(f"*{best_grant.get('program_name', 'N/A')}*")
            
            with col2:
                st.metric(
                    "Amount",
                    f"${best_grant['grant_amount']/1e6:.1f}M",
                )
            
            with col3:
                st.metric(
                    "Impact Score",
                    f"{best_grant['impact_score']:.1f}/5",
                    delta=None
                )
            
            # Detailed metrics in expandable section
            with st.expander("📊 Detailed Impact Analysis"):
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    st.markdown("**Pre-Grant Trend**")
                    st.write(f"Direction: {best_grant['pre_metrics']['trend_direction']}")
                    st.write(f"Change: {best_grant['pre_metrics']['change_percent']:.2f}%")
                
                with col_b:
                    st.markdown("**Post-Grant Trend**")
                    st.write(f"Direction: {best_grant['post_metrics']['trend_direction']}")
                    st.write(f"Change: {best_grant['post_metrics']['change_percent']:.2f}%")
                
                with col_c:
                    st.markdown("**Commodity Context**")
                    st.write(f"Stability: {best_grant['commodity_metrics']['stability']}")
                    st.write(f"Trend: {best_grant['trend_status']}")
            
            st.markdown("")
            st.info("💡 This grant showed the strongest correlation with favorable currency movements, accounting for commodity price trends.")
        
        # Detailed Table
        st.markdown("### Event-by-Event Details")
        
        # Create results table
        results_data = []
        for analysis in analyses:
            results_data.append({
                'Date': analysis['grant_date'].strftime('%Y-%m-%d'),
                'Source': analysis['grant_source'],
                'Amount (USD)': f"${analysis['grant_amount']:,.0f}",
                'Pre-Trend': analysis['pre_metrics']['trend_direction'],
                'Post-Trend': analysis['post_metrics']['trend_direction'],
                'Trend Status': analysis['trend_status'],
                'Commodity Stability': analysis['commodity_metrics']['stability'],
                'Impact Score': f"{analysis['impact_score']:.2f}",
                'Post Change %': f"{analysis['post_metrics']['change_percent']:.2f}%"
            })
        
        results_df = pd.DataFrame(results_data)
        
        # Color code by impact score
        st.dataframe(
            results_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Download button
        csv = results_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name=f"grant_impact_{selected_currency}_{config['start_date']}.csv",
            mime="text/csv"
        )


if __name__ == '__main__':
    render_grant_dashboard()
