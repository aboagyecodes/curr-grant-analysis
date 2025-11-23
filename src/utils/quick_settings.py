"""
Quick Settings Component

Reusable component for inline configuration editing in dashboards
"""

import streamlit as st
from datetime import date, timedelta
from config.settings import PILOT_CURRENCIES, DEFAULT_NEWSAPI_KEY, DEFAULT_FRED_KEY


def render_quick_settings():
    """
    Render a collapsible Quick Settings panel in the sidebar
    
    Allows users to modify configuration without leaving the current dashboard
    """
    
    # Only show if already configured
    if not st.session_state.get('config', {}).get('configured'):
        return
    
    config = st.session_state['config']
    
    # Quick Settings Expander at top of sidebar
    with st.sidebar.expander("⚙️ Quick Settings", expanded=False):
        st.caption("Update configuration without leaving this page")
        
        # Currency Selection
        st.markdown("**Currencies**")
        all_currency_codes = list(PILOT_CURRENCIES.keys())
        current_currencies = config.get('currencies', [])
        
        new_currencies = st.multiselect(
            "Select currencies",
            options=all_currency_codes,
            default=current_currencies,
            format_func=lambda x: f"{x} - {PILOT_CURRENCIES[x]['name']}",
            key="quick_currencies",
            label_visibility="collapsed"
        )
        
        # Date Range
        st.markdown("**Date Range**")
        col1, col2 = st.columns(2)
        with col1:
            new_start_date = st.date_input(
                "Start",
                value=config.get('start_date', date.today() - timedelta(days=730)),
                max_value=date.today(),
                key="quick_start_date"
            )
        with col2:
            new_end_date = st.date_input(
                "End",
                value=config.get('end_date', date.today()),
                min_value=new_start_date,
                max_value=date.today(),
                key="quick_end_date"
            )
        
        # API Keys (optional)
        show_api = st.checkbox("Show API Keys", value=False, key="quick_show_api")
        
        new_newsapi_key = config.get('newsapi_key', DEFAULT_NEWSAPI_KEY)
        new_fred_key = config.get('fred_key', DEFAULT_FRED_KEY)
        
        if show_api:
            new_newsapi_key = st.text_input(
                "NewsAPI Key",
                value=config.get('newsapi_key', DEFAULT_NEWSAPI_KEY),
                type="password",
                key="quick_newsapi_key"
            )
            new_fred_key = st.text_input(
                "FRED API Key",
                value=config.get('fred_key', DEFAULT_FRED_KEY),
                type="password",
                key="quick_fred_key"
            )
        
        st.markdown("---")
        
        # Apply Changes Button
        if st.button("✓ Apply Changes", type="primary", use_container_width=True, key="apply_quick_settings"):
            # Validate
            if not new_currencies:
                st.error("Please select at least one currency")
                return
            
            if new_start_date >= new_end_date:
                st.error("Start date must be before end date")
                return
            
            # Update configuration
            st.session_state['config'] = {
                'currencies': new_currencies,
                'start_date': new_start_date,
                'end_date': new_end_date,
                'newsapi_key': new_newsapi_key or DEFAULT_NEWSAPI_KEY,
                'fred_key': new_fred_key or DEFAULT_FRED_KEY,
                'configured': True
            }
            
            # Reset selected currency if needed
            if 'selected_currency' in st.session_state:
                if st.session_state['selected_currency'] not in new_currencies:
                    st.session_state['selected_currency'] = new_currencies[0]
            
            # Clear cached analysis/anomalies since config changed
            if 'grant_analyses' in st.session_state:
                del st.session_state['grant_analyses']
            if 'anomalies' in st.session_state:
                del st.session_state['anomalies']
            if 'detector' in st.session_state:
                del st.session_state['detector']
            if 'investigation_cache' in st.session_state:
                del st.session_state['investigation_cache']
            
            st.success("✓ Configuration updated!")
            st.rerun()
