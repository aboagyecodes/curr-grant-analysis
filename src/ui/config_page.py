"""
Configuration Page

Initial setup page for selecting currencies, date ranges, and uploading data.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import PILOT_CURRENCIES, DEFAULT_NEWSAPI_KEY, DEFAULT_FRED_KEY
from src.data_loaders.etl_grants import standardize_grants, save_standardized
from src.utils.state_manager import navigate_to


def render_config_page():
    """Render the configuration page as a landing page"""
    
    # Centered header
    st.markdown("""
    <div style='text-align: center; padding: 40px 0 30px 0;'>
        <h1 style='font-size: 48px; font-weight: 700; color: #1a1a1a; margin-bottom: 10px; border: none;'>
            Currency Impact Analysis
        </h1>
        <p style='font-size: 18px; color: #666; margin: 0;'>
            Analyze IMF &amp; World Bank grant impacts on developing nation currencies
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Centered container
    col_spacer1, col_main, col_spacer2 = st.columns([1, 3, 1])
    
    with col_main:
        # Country Selection
        st.subheader("1. Select Currencies")
        
        selected_currencies = st.multiselect(
            "Choose currencies to analyze",
            options=list(PILOT_CURRENCIES.keys()),
            default=['GHS'],
            format_func=lambda x: f"{x} - {PILOT_CURRENCIES[x]['name']}"
        )
        
        # Show selected currencies as text
        if selected_currencies:
            # Filter out any invalid keys (e.g. if indices were somehow returned)
            valid_currencies = [c for c in selected_currencies if c in PILOT_CURRENCIES]
            currency_names = ", ".join([PILOT_CURRENCIES[c]['name'] for c in valid_currencies])
            st.caption(f"**Selected:** {currency_names}")
        
        st.markdown("---")
        
        # Date Range Selection
        st.subheader("2. Select Analysis Period")
        col1, col2 = st.columns(2)
        
        default_end = datetime.now()
        default_start = default_end - timedelta(days=365*2)  # 2 years
        
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=default_start,
                max_value=default_end
            )
        
        with col2:
            end_date = st.date_input(
                "End Date",
                value=default_end,
                min_value=start_date
            )
        
        
        # Check for standardized data (auto-processed on launch)
        from config.settings import STANDARDIZED_DIR
        standardized_exists = os.path.exists(os.path.join(STANDARDIZED_DIR, 'grants.csv'))
        
        st.markdown("---")
        
        # API Keys - Collapsible
        show_api = st.checkbox("⚙️ Configure API Keys (Optional)", value=False)
        
        newsapi_key = ""
        fred_key = ""
        
        if show_api:
            st.caption("API keys enable news headlines and policy rate analysis in the Anomaly Investigator.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                newsapi_key = st.text_input(
                    "NewsAPI Key",
                    type="password",
                    value=st.session_state.get('newsapi_key', DEFAULT_NEWSAPI_KEY),
                    help="Get your free key at newsapi.org"
                )
                if newsapi_key:
                    st.session_state['newsapi_key'] = newsapi_key
                else:
                     st.session_state['newsapi_key'] = DEFAULT_NEWSAPI_KEY
            
            with col2:
                fred_key = st.text_input(
                    "FRED API Key",
                    type="password",
                    value=st.session_state.get('fred_key', DEFAULT_FRED_KEY),
                    help="Get your key at fred.stlouisfed.org"
                )
                if fred_key:
                    st.session_state['fred_key'] = fred_key
                else:
                    st.session_state['fred_key'] = DEFAULT_FRED_KEY
        
        st.markdown("---")
        
        # Run Analysis Button
        st.subheader("3. Start Analysis")
        
        can_proceed = (
            len(selected_currencies) > 0 and
            standardized_exists
        )
        
        if can_proceed:
            col1, col2 = st.columns([0.7, 0.3])
            
            with col1:
                if st.button("🚀 Run Analysis", type="primary", use_container_width=True, key="run_analysis_btn"):
                    # Save configuration to session state
                    st.session_state['config'] = {
                        'currencies': selected_currencies,
                        'start_date': start_date,
                        'end_date': end_date,
                        'newsapi_key': newsapi_key or DEFAULT_NEWSAPI_KEY,
                        'fred_key': fred_key or DEFAULT_FRED_KEY,
                        'configured': True
                    }
                    # Initialize selected_currency to first currency
                    st.session_state['selected_currency'] = selected_currencies[0]
                    st.toast("✓ Configuration saved!", icon="✅")
                    st.rerun()
            
            with col2:
                # Only show/enable if configured
                is_configured = st.session_state.get('config', {}).get('configured', False)
                if st.button("📊 Dashboards", disabled=not is_configured, use_container_width=True):
                    navigate_to("grant")
        
        if not can_proceed:
            st.error("""
            **Cannot proceed:**
            - Select at least one currency
            - Ensure grant data is standardized
            """)
        
        # Display current configuration status at bottom
        if st.session_state.get('config', {}).get('configured'):
            st.markdown("---")
            config = st.session_state['config']
            st.success("✓ System Configured")
            st.caption(f"Currencies: {', '.join(config['currencies'])} | Period: {(config['end_date'] - config['start_date']).days} days")


if __name__ == '__main__':
    render_config_page()

