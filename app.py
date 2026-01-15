"""
IMF/World Bank Currency Impact Analysis App
Main Streamlit Application Entry Point
"""

import streamlit as st

# CRITICAL: st.set_page_config() MUST be the first Streamlit command
# This is required for Streamlit Cloud deployment
st.set_page_config(
    page_title="Currency Impact Analysis",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="auto"
)

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(__file__))

# Import pages
from src.ui.config_page import render_config_page
from src.ui.grant_dashboard import render_grant_dashboard
from src.ui.anomaly_dashboard import render_anomaly_dashboard
from src.data_loaders.etl_grants import standardize_grants, save_standardized
from src.utils.state_manager import init_session_state, navigate_to, get_current_page
from config.settings import IMF_DIR, WORLDBANK_DIR, STANDARDIZED_DIR
import glob

# Initialize session state
init_session_state()

# Auto-standardize grant data on first launch
if not st.session_state['etl_run']:
    # Check if grant files exist but haven't been standardized
    imf_files = glob.glob(os.path.join(IMF_DIR, '*.csv')) + glob.glob(os.path.join(IMF_DIR, '*.xls'))
    wb_files = glob.glob(os.path.join(WORLDBANK_DIR, '*.csv')) + glob.glob(os.path.join(WORLDBANK_DIR, '*.xlsx'))
    standardized_exists = os.path.exists(os.path.join(STANDARDIZED_DIR, 'grants.csv'))
    
    if (len(imf_files) > 0 or len(wb_files) > 0) and not standardized_exists:
        # Silently process grant data
        try:
            grants_df = standardize_grants()
            if not grants_df.empty:
                save_standardized(grants_df)
        except:
            pass  # Fail silently
    
    st.session_state['etl_run'] = True


# Background data prefetching (only runs if cache is expired)
try:
    from src.utils.prefetch_data import prefetch_all_data
    prefetch_all_data()
except Exception as e:
    print(f"Warning: Data prefetch failed: {e}")
    # Don't block app if prefetch fails

# Check if configured
is_configured = st.session_state.get('config', {}).get('configured', False)

# Get current page
query_page = get_current_page()

print(f"DEBUG: Page Load - query_page: {query_page}, is_configured: {is_configured}")
print(f"DEBUG: Session State Config: {st.session_state.get('config', 'MISSING')}")

# Determine which page to show
if not is_configured:
    # Show config page as landing page
    # Load custom CSS for config page too
    css_path = os.path.join(os.path.dirname(__file__), 'assets', 'styles.css')
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
            
    render_config_page()
    
elif query_page == "grant":
    # Show Grant Impact Dashboard with sidebar
    # Load custom CSS
    css_path = os.path.join(os.path.dirname(__file__), 'assets', 'styles.css')
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("🌍 Navigation")
    
    if st.sidebar.button("⚙️ Configuration", use_container_width=True, key="grant_to_config"):
        navigate_to(None)
    
    if st.sidebar.button("🔍 Anomaly Investigator", use_container_width=True, key="grant_to_anomaly"):
        navigate_to("anomaly")
    
    st.sidebar.markdown("---")
    
    with st.sidebar.expander("ℹ️ About"):
        st.markdown("""
        **Currency Impact Analysis**
        
        Analyzing IMF/World Bank grant impacts on developing nation currencies.
        """)
    
    render_grant_dashboard()
    
elif query_page == "anomaly":
    # Show Anomaly Dashboard with sidebar
    # Load custom CSS
    css_path = os.path.join(os.path.dirname(__file__), 'assets', 'styles.css')
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("🌍 Navigation")
    
    if st.sidebar.button("⚙️ Configuration", use_container_width=True, key="anomaly_to_config"):
        navigate_to(None)
    
    if st.sidebar.button("📊 Grant Impact Analysis", use_container_width=True, key="anomaly_to_grant"):
        navigate_to("grant")
    
    st.sidebar.markdown("---")
    
    with st.sidebar.expander("ℹ️ About"):
        st.markdown("""
        **Currency Impact Analysis**
        
        Detecting and investigating currency anomalies.
        """)
    
    render_anomaly_dashboard()
    
else:
    # Default to config page
    # Load custom CSS (CRITICAL: Fixes layout shift after config)
    css_path = os.path.join(os.path.dirname(__file__), 'assets', 'styles.css')
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
            
    render_config_page()

