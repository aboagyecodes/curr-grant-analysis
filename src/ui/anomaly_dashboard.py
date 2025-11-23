"""
Anomaly Investigator Dashboard

Detects and investigates currency anomalies with external event correlation.
"""

import streamlit as st
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import PILOT_CURRENCIES, DEFAULT_NEWSAPI_KEY, DEFAULT_FRED_KEY
from src.data_loaders.etl_grants import load_standardized_grants
from src.data_loaders.fx_loader import get_fx_data
from src.data_loaders.commodity_loader import get_all_commodities
from src.data_loaders.external_data import ExternalDataFetcher
from src.analysis.anomaly_detector import AnomalyDetector
from src.utils.charts import create_anomaly_chart
from src.utils.persistence import load_notes, save_note, generate_anomaly_id
from src.utils.quick_settings import render_quick_settings
from src.utils.icons import load_material_icons_css, get_icon_html, icon


def render_anomaly_dashboard():
    """Render the Anomaly Investigator Dashboard"""
    
    
    # Load Material Icons
    st.markdown(load_material_icons_css(), unsafe_allow_html=True)
    
    # Check if configured
    if not st.session_state.get('config', {}).get('configured'):
        st.warning("⚠️ Please complete configuration first!")
        st.info("Navigate to 'Configuration' in the sidebar.")
        return
    
    config = st.session_state['config']
    
    # Ensure selected_currency is valid
    if st.session_state['selected_currency'] not in config['currencies']:
        st.session_state['selected_currency'] = config['currencies'][0]
    
    # Quick Settings Panel (collapsible)
    render_quick_settings()
    st.sidebar.markdown("---")
        
    selected_currency = st.sidebar.selectbox(
        "Select Currency",
        options=config['currencies'],
        format_func=lambda x: f"{x} - {PILOT_CURRENCIES[x]['name']}",
        key='selected_currency'
    )
    
    # Detection Settings in Sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Detection Settings")
    
    # Initialize session state for sliders with better defaults
    if 'volatility_threshold' not in st.session_state:
        st.session_state['volatility_threshold'] = 15
    if 'detection_window' not in st.session_state:
        st.session_state['detection_window'] = 30
    
    threshold = st.sidebar.slider(
        "Volatility Threshold (%)", 
        5, 30, 
        value=15,
        key='volatility_threshold'
    )
    
    window_days = st.sidebar.slider(
        "Detection Window (days)", 
        7, 60,
        value=30,
        key='detection_window'
    )
    
    # Grant Correlation Window
    st.sidebar.caption("Grant Correlation Window")
    corr_col1, corr_col2, corr_col3 = st.sidebar.columns(3)
    with corr_col1:
        if st.button("7d", use_container_width=True, key="corr_7"):
            st.session_state['correlation_days'] = 7
        if st.button("30d", use_container_width=True, key="corr_30"):
            st.session_state['correlation_days'] = 30
    with corr_col2:
        if st.button("15d", use_container_width=True, key="corr_15"):
            st.session_state['correlation_days'] = 15
        if st.button("45d", use_container_width=True, key="corr_45"):
            st.session_state['correlation_days'] = 45
    with corr_col3:
        if st.button("60d", use_container_width=True, key="corr_60"):
            st.session_state['correlation_days'] = 60
    
    # Initialize default
    if 'correlation_days' not in st.session_state:
        st.session_state['correlation_days'] = 7
    
    st.sidebar.caption(f"Current: ±{st.session_state['correlation_days']} days")
    
    currency_name = PILOT_CURRENCIES[selected_currency]['name']
    country_name = PILOT_CURRENCIES[selected_currency]['country']
    
    st.markdown(f"### Anomaly Detection for {currency_name} ({selected_currency})")
    
    # Load data
    with st.spinner("Loading data..."):
        # Load grants
        all_grants = load_standardized_grants()
        
        # Get the country name from currency and find matching grants
        country_name = PILOT_CURRENCIES[selected_currency]['country']
        
        # Filter grants by matching country_name field in grants data
        currency_grants = all_grants[
            all_grants['country_name'] == country_name
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
        
        # Initialize external data fetcher
        external_fetcher = ExternalDataFetcher(
            newsapi_key=config.get('newsapi_key') or DEFAULT_NEWSAPI_KEY,
            fred_api_key=config.get('fred_key') or DEFAULT_FRED_KEY
        )
    
    # Detect Button in Sidebar
    if st.sidebar.button("Detect Anomalies", type="primary", use_container_width=True, key="detect_anomalies_btn"):
        if fx_data.empty:
            st.sidebar.error("No FX data available")
        else:
            with st.spinner("Detecting anomalies..."):
                detector = AnomalyDetector(fx_data, currency_grants, commodity_data, external_fetcher)
                anomalies = detector.detect_steep_movements(threshold, window_days)
                
                st.session_state['anomalies'] = anomalies
                st.session_state['detector'] = detector
                st.session_state['last_detection_params'] = {
                    'threshold': threshold,
                    'window': window_days,
                    'currency': selected_currency
                }
                st.sidebar.success(f"Found {len(anomalies)} anomalies")
                st.rerun()
    
    # Auto-detect on first load OR when parameters change
    should_auto_detect = False
    if 'anomalies' not in st.session_state or st.session_state['anomalies'] is None:
        should_auto_detect = True
    elif 'last_detection_params' in st.session_state:
        # Check if any detection parameter changed
        last_params = st.session_state['last_detection_params']
        if (last_params['currency'] != selected_currency or 
            last_params['threshold'] != threshold or 
            last_params['window'] != window_days):
            should_auto_detect = True
            
    if should_auto_detect:
        if not fx_data.empty:
            with st.spinner("Detecting anomalies..."):
                detector = AnomalyDetector(fx_data, currency_grants, commodity_data, external_fetcher)
                anomalies = detector.detect_steep_movements(threshold, window_days)
                
                st.session_state['anomalies'] = anomalies
                st.session_state['detector'] = detector
                st.session_state['last_detection_params'] = {
                    'threshold': threshold,
                    'window': window_days,
                    'currency': selected_currency
                }
                if len(anomalies) > 0:
                    st.sidebar.info(f"Detected {len(anomalies)} anomalies")
                st.rerun()
    
    if fx_data.empty:
        st.error(f"No FX data available for {selected_currency}")
        return
    

    
    # Display Anomalies
    st.markdown("---")
    if 'anomalies' in st.session_state and st.session_state['anomalies'] is not None:
        anomalies = st.session_state['anomalies']
        detector = st.session_state.get('detector')
        
        if not detector:
            st.warning("⚠️ Detector not initialized. Please run detection again.")
            return
        
        if len(anomalies) == 0:
            st.info("No anomalies detected with current settings.")
            return
        
        # Layout: Two independently scrollable columns
        col_list, col_canvas = st.columns([1, 2])
        
        # LEFT COLUMN: Anomaly List (Scrollable)
        with col_list:
            st.markdown(f'<h3>{icon("search", 24)} Detected Anomalies ({len(anomalies)})</h3>', unsafe_allow_html=True)
            
            # Use native scrollable container (Streamlit 1.30+)
            with st.container(height=800):
                # Anomaly list with cached correlation indicators
                anomaly_options = []
                
                # Check if we need to compute correlation indicators
                # (only compute once per detection, then cache)
                cache_key = f"corr_indicators_{selected_currency}_{threshold}_{window_days}"
                
                if cache_key not in st.session_state:
                    # Compute indicators once and cache them
                    with st.spinner("Loading correlation indicators..."):
                        indicators_cache = {}
                        for idx, anomaly in enumerate(anomalies):
                            indicators = ""
                            if detector:
                                corrs = detector.check_correlations_lightweight(anomaly, selected_currency)
                                if corrs['has_grant']:
                                    indicators += " 💰"
                                if corrs['has_commodity']:
                                    indicators += " 🌾"
                                if corrs['has_news']:
                                    indicators += " 📰"
                            indicators_cache[idx] = indicators
                        st.session_state[cache_key] = indicators_cache
                
                # Use cached indicators
                indicators_cache = st.session_state[cache_key]
                
                for idx, anomaly in enumerate(anomalies):
                    start = pd.to_datetime(anomaly['start_date']).strftime('%Y-%m-%d')
                    magnitude = anomaly['magnitude']
                    direction_arrow = "↑" if anomaly['direction'] == 'depreciation' else "↓"
                    
                    # Get cached indicators
                    indicators = indicators_cache.get(idx, "")
                    anomaly_options.append(f"{direction_arrow} {magnitude:.1f}% | {start}{indicators}")
                
                selected_idx = st.radio(
                    "Select anomaly:",
                    range(len(anomalies)),
                    format_func=lambda i: anomaly_options[i],
                    label_visibility="collapsed"
                )
        
        # RIGHT COLUMN: Investigation Canvas (Fixed Header + Scrollable Content)
        with col_canvas:
            selected_anomaly = anomalies[selected_idx]
            
            # --- FIXED HEADER SECTION ---
            st.markdown(f'<h3>{icon("science", 24)} Investigation Canvas</h3>', unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Change", f"{selected_anomaly['change_percent']:.2f}%")
            with col2:
                st.metric("Duration", f"{selected_anomaly['duration_days']} days")
            with col3:
                st.metric("Direction", selected_anomaly['direction'].title())
            
            st.markdown("---")
            
            # --- SCROLLABLE CONTENT SECTION ---
            # Use native scrollable container for content below header
            with st.container(height=800, border=False):
            

                # Focused Chart
                fig = create_anomaly_chart(
                    fx_data,
                    selected_anomaly,
                    currency_grants,
                    title=f"Anomaly: {selected_anomaly['start_date'].strftime('%Y-%m-%d')} to {selected_anomaly['end_date'].strftime('%Y-%m-%d')}"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("---")
                
                # Correlation Analysis (with caching for performance)
                st.markdown(f'<h4>{icon("link", 22)} Correlations & Events</h4>', unsafe_allow_html=True)
                
                # Create a cache key for this anomaly
                anomaly_cache_key = f"{selected_anomaly['start_date']}_{selected_anomaly['end_date']}_{selected_currency}"
                correlation_days = st.session_state.get('correlation_days', 7)
                investigation_cache_key = f"{anomaly_cache_key}_{correlation_days}"
                
                # Check if we already analyzed this anomaly with these parameters
                if 'investigation_cache' not in st.session_state:
                    st.session_state['investigation_cache'] = {}
                
                if investigation_cache_key in st.session_state['investigation_cache']:
                    investigation = st.session_state['investigation_cache'][investigation_cache_key]
                else:
                    with st.spinner("Analyzing correlations..."):
                        investigation = detector.investigate_anomaly(selected_anomaly, selected_currency, correlation_days)
                        st.session_state['investigation_cache'][investigation_cache_key] = investigation
                
                # Grant Correlation
                st.markdown(f'<h5>{icon("volunteer_activism", 20)} Grant Disbursements (±{correlation_days} days)</h5>', unsafe_allow_html=True)
                grant_corr = investigation['grant_correlation']
                if grant_corr['has_grant']:
                    st.success(f"{len(grant_corr['grants'])} grant(s) found nearby")
                    for grant in grant_corr['grants']:
                        st.write(f"- **{grant['date']}**: ${grant['amount']:,.0f} from {grant['source']}")
                        st.caption(f"  Program: {grant['program']}")
                else:
                    st.info(f"No grants found in ±{correlation_days} day window")
                
                # Commodity Correlation
                st.markdown(f'<h5>{icon("agriculture", 20)} Commodity Movements</h5>', unsafe_allow_html=True)
                comm_corr = investigation['commodity_correlation']
                if comm_corr['movements']:
                    for commodity, data in comm_corr['movements'].items():
                        if data['significant']:
                            st.warning(f"⚠️ **{commodity}**: {data['change_percent']:.2f}% (Significant)")
                        else:
                            st.write(f"• **{commodity}**: {data['change_percent']:.2f}%")
                else:
                    st.info("No commodity data available")
                
                st.markdown("""
        <style>
        /* Hide scrollbar for the right column container */
        .scrollable-right::-webkit-scrollbar {
            display: none; /* Chrome/Safari/Opera */
        }
        
        /* Style for Save Note button */
        div.stButton > button {
            border: 1px solid #4CAF50 !important;
            border-radius: 4px !important;
        }
        </style>
        """, unsafe_allow_html=True)
                
                # External Events
                st.markdown(f'<h5>{icon("article", 20)} External Events</h5>', unsafe_allow_html=True)
                external = investigation['external_events']
                
                # Debug info
                print(f"DEBUG External Events: {external.keys()}")
                print(f"DEBUG News count: {len(external.get('news', []))}")
                print(f"DEBUG IMF releases: {len(external.get('imf_releases', []))}")
                print(f"DEBUG Policy changes: {len(external.get('policy_rate_changes', []))}")
                
                # IMF Releases
                if external['imf_releases']:
                    with st.expander("IMF Press Releases"):
                        for release in external['imf_releases']:
                            st.write(f"**{release['date']}**: {release['title']}")
                else:
                    st.caption("No IMF releases found")
                
                # Policy Rates
                if external['policy_rate_changes']:
                    with st.expander("Policy Rate Changes"):
                        for change in external['policy_rate_changes']:
                            st.write(f"**{change['date']}**: {change['previous_rate']}% → {change['new_rate']}%")
                else:
                    st.caption("No policy rate changes found")
                
                # News Headlines
                news_list = external.get('news', [])
                
                # Debug info for user
                if not news_list:
                    st.caption(f"Debug: No news found for period {selected_anomaly['start_date'].strftime('%Y-%m-%d')} to {selected_anomaly['end_date'].strftime('%Y-%m-%d')}")
                
                if news_list and len(news_list) > 0:
                    with st.expander(f"Related News ({len(news_list)} articles)", expanded=True):
                        for article in news_list[:5]:
                            st.write(f"**{article['date']}** - {article['title']}")
                            st.caption(f"Source: {article['source']}")
                            if 'url' in article:
                                st.markdown(f"[Read more]({article['url']})")
                else:
                    st.info("No news articles found for this specific period.")
                    if not getattr(external_fetcher, 'newsdata_key', None):
                         st.warning("⚠️ NewsData.io key missing. Only recent news (RSS) available.")
                
                st.markdown("---")
                
                # Research Notes (Moved inside scrollable container)
                # Research Notes (Moved inside scrollable container)
                st.markdown("#### 📝 Research Notes")
                anomaly_id = generate_anomaly_id(selected_anomaly)
                current_note = load_notes().get(anomaly_id, '')
                
                # Use a unique key for the text area to prevent state issues
                note_key = f"note_{anomaly_id}"
                
                note_text = st.text_area(
                    "Your investigation notes:",
                    value=current_note,
                    height=150,
                    placeholder="e.g., 'Election uncertainty led to capital flight...'",
                    key=note_key
                )
                
                col_save, col_spacer = st.columns([1, 3])
                with col_save:
                    if st.button("Save Note", key=f"save_{anomaly_id}"):
                        save_note(anomaly_id, note_text)
                        st.success("Note saved!")
    
    # About Section at Bottom of Sidebar
    st.sidebar.markdown("---")
    with st.sidebar.expander("ℹ️ About"):
        st.markdown("""
        **Anomaly Investigator**
        
        Detects and investigates unusual currency movements.
        
        **Logic:**
        - Identifies steep FX rate changes
        - Correlates with grant disbursements
        - Analyzes commodity context
        - Fetches related news events
        
        **Data Sources:**
        - Yahoo Finance for FX data
        - NewsAPI & FRED for context
        """)


if __name__ == '__main__':
    render_anomaly_dashboard()
