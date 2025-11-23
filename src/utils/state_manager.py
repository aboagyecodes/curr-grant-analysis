"""
State Manager

Centralizes session state initialization, navigation logic, and widget synchronization
to ensure a seamless user experience across the application.
"""

import streamlit as st

def init_session_state():
    """Initialize all necessary session state variables with defaults."""
    
    # Configuration
    if 'config' not in st.session_state:
        st.session_state['config'] = {
            'configured': False,
            'currencies': [],
            'start_date': None,
            'end_date': None
        }
    
    # Shared UI State
    if 'selected_currency' not in st.session_state:
        st.session_state['selected_currency'] = None
        
    # ETL Status
    if 'etl_run' not in st.session_state:
        st.session_state['etl_run'] = False
        
    # Analysis Results
    if 'grant_analyses' not in st.session_state:
        st.session_state['grant_analyses'] = None
        
    if 'anomalies' not in st.session_state:
        st.session_state['anomalies'] = None
        
    if 'detector' not in st.session_state:
        st.session_state['detector'] = None
        
    # Navigation State
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = None


def navigate_to(page_name):
    """
    Navigate to a specific page by setting query params and rerunning.
    Also updates session state for robustness.
    
    Args:
        page_name (str): 'grant', 'anomaly', or None (for config)
    """
    st.session_state['current_page'] = page_name
    
    if page_name:
        st.query_params["page"] = page_name
    else:
        st.query_params.clear()
    
    st.rerun()


def get_current_page():
    """
    Get the current page from query parameters, falling back to session state.
    """
    # Handle query parameters for deep linking
    try:
        # Streamlit 1.51.0+ (returns dict-like object)
        page = st.query_params.get("page")
        # Handle case where it might return a list (older versions) or single value
        if isinstance(page, list) and len(page) > 0:
            page = page[0]
    except:
        # Fallback for older versions
        try:
            query_params = st.experimental_get_query_params()
            page = query_params.get("page", [None])[0]
        except:
            page = None
    
    if page:
        # Sync session state if param exists
        st.session_state['current_page'] = page
        return page
    
    # Fallback to session state if param is missing (e.g. during some reruns)
    return st.session_state.get('current_page')


def sync_currency_selection():
    """
    Callback to ensure the selected currency is valid and persisted.
    Should be called on change of the currency selectbox.
    """
    # The value is automatically updated in session_state['selected_currency']
    # due to the key argument in the widget.
    # We can add additional logic here if needed (e.g., clearing results)
    pass
