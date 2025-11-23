"""
Anomaly Detection Engine

Detects steep currency movements (>10% in <30 days) and correlates them
with grants, commodities, policy rates, and external events.
"""

import pandas as pd
import numpy as np
from datetime import timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import (
    ANOMALY_THRESHOLD_PERCENT, ANOMALY_WINDOW_DAYS,
    GRANT_CORRELATION_DAYS, COMMODITY_CORRELATION_PERCENT,
    PILOT_CURRENCIES
)


class AnomalyDetector:
    """Detects and analyzes currency anomalies"""
    
    def __init__(self, fx_data, grants_data, commodity_data, external_data_fetcher=None):
        """
        Initialize detector
        
        Args:
            fx_data: DataFrame with FX rates
            grants_data: DataFrame with grants
            commodity_data: dict of commodity DataFrames
            external_data_fetcher: ExternalDataFetcher instance
        """
        self.fx_data = fx_data.copy()
        self.grants_data = grants_data.copy()
        self.commodity_data = commodity_data
        self.external_fetcher = external_data_fetcher
        
        # Ensure dates
        self.fx_data['date'] = pd.to_datetime(self.fx_data['date'])
        self.grants_data['disbursement_date'] = pd.to_datetime(self.grants_data['disbursement_date'])
    
    def detect_steep_movements(self, threshold_percent=None, window_days=None):
        """
        Detect periods where currency changed >threshold% in <window days
        
        Args:
            threshold_percent: Percent change threshold (default from config)
            window_days: Window size in days (default from config)
        
        Returns:
            list: List of anomaly dicts
        """
        if threshold_percent is None:
            threshold_percent = ANOMALY_THRESHOLD_PERCENT
        if window_days is None:
            window_days = ANOMALY_WINDOW_DAYS
        
        anomalies = []
        
        # Sort by date
        fx_sorted = self.fx_data.sort_values('date').reset_index(drop=True)
        
        # Sliding window detection
        for i in range(len(fx_sorted)):
            current_date = fx_sorted.iloc[i]['date']
            current_rate = fx_sorted.iloc[i]['rate']
            
            # Look ahead in window
            window_end = current_date + timedelta(days=window_days)
            window_mask = (fx_sorted['date'] > current_date) & (fx_sorted['date'] <= window_end)
            window_data = fx_sorted[window_mask]
            
            if len(window_data) == 0:
                continue
            
            # Check for steep movements
            for j, row in window_data.iterrows():
                end_date = row['date']
                end_rate = row['rate']
                
                # Calculate percent change
                if current_rate != 0:
                    change_percent = ((end_rate - current_rate) / current_rate) * 100
                else:
                    change_percent = 0
                
                # Check if exceeds threshold
                if abs(change_percent) >= threshold_percent:
                    # Check if we already have this period
                    duplicate = False
                    for existing in anomalies:
                        if (abs((existing['start_date'] - current_date).days) < 7 and
                            abs((existing['end_date'] - end_date).days) < 7):
                            duplicate = True
                            break
                    
                    if not duplicate:
                        anomalies.append({
                            'start_date': current_date,
                            'end_date': end_date,
                            'start_rate': current_rate,
                            'end_rate': end_rate,
                            'change_percent': change_percent,
                            'direction': 'appreciation' if change_percent < 0 else 'depreciation',
                            'magnitude': abs(change_percent),
                            'duration_days': (end_date - current_date).days
                        })
        
        # Sort by magnitude
        anomalies.sort(key=lambda x: x['magnitude'], reverse=True)
        
        return anomalies
    
    def correlate_with_grants(self, anomaly, correlation_days=7):
        """
        Check if a grant occurred near the anomaly
        
        Args:
            anomaly: Anomaly dict
            correlation_days: Days to search before/after anomaly (default 7)
        
        Returns:
            dict: {
                'has_grant': bool,
                'grants': list of nearby grants
            }
        """
        start_date = anomaly['start_date']
        end_date = anomaly['end_date']
        
        # Expand search window
        search_start = start_date - timedelta(days=correlation_days)
        search_end = end_date + timedelta(days=correlation_days)
        
        # Find grants in window
        mask = ((self.grants_data['disbursement_date'] >= search_start) &
                (self.grants_data['disbursement_date'] <= search_end))
        nearby_grants = self.grants_data[mask]
        
        grants_list = []
        for _, grant in nearby_grants.iterrows():
            grants_list.append({
                'date': grant['disbursement_date'].strftime('%Y-%m-%d'),
                'amount': grant['amount_usd'],
                'source': grant['source'],
                'program': grant['program_name']
            })
        
        return {
            'has_grant': len(grants_list) > 0,
            'grants': grants_list
        }
    
    def correlate_with_commodities(self, anomaly):
        """
        Check if commodities moved significantly during anomaly
        
        Args:
            anomaly: Anomaly dict
        
        Returns:
            dict: Commodity correlation data
        """
        start_date = anomaly['start_date']
        end_date = anomaly['end_date']
        
        commodity_movements = {}
        
        for commodity_name, commodity_df in self.commodity_data.items():
            commodity_df['date'] = pd.to_datetime(commodity_df['date'])
            
            # Get prices at start and end
            start_mask = commodity_df['date'] <= start_date
            end_mask = commodity_df['date'] <= end_date
            
            start_data = commodity_df[start_mask].tail(1)
            end_data = commodity_df[end_mask].tail(1)
            
            if len(start_data) > 0 and len(end_data) > 0:
                start_price = start_data.iloc[0]['price']
                end_price = end_data.iloc[0]['price']
                
                if start_price != 0:
                    change_percent = ((end_price - start_price) / start_price) * 100
                    
                    commodity_movements[commodity_name] = {
                        'change_percent': change_percent,
                        'significant': abs(change_percent) >= COMMODITY_CORRELATION_PERCENT
                    }
        
        # Determine if commodities likely influenced
        significant_movements = [c for c in commodity_movements.values() if c['significant']]
        
        return {
            'movements': commodity_movements,
            'has_significant_movement': len(significant_movements) > 0,
            'likely_influence': len(significant_movements) > 0
        }
    
    def get_external_events(self, anomaly, country_code):
        """
        Get external events (IMF, policy rates, news) during anomaly
        
        Args:
            anomaly: Anomaly dict
            country_code: Currency code
        
        Returns:
            dict: External events data
        """
        if not self.external_fetcher:
            return {
                'imf_releases': [],
                'policy_rate_changes': [],
                'news': []
            }
        
        start_date = anomaly['start_date']
        end_date = anomaly['end_date']
        
        # Fetch external data
        external_data = self.external_fetcher.get_all_correlation_data(
            country_code, start_date, end_date
        )
        
        # Process policy rates to find changes
        policy_changes = []
        if not external_data['policy_rates'].empty:
            rates_df = external_data['policy_rates']
            if len(rates_df) > 1:
                # Check for significant changes
                for i in range(1, len(rates_df)):
                    prev_rate = rates_df.iloc[i-1]['rate']
                    curr_rate = rates_df.iloc[i]['rate']
                    if prev_rate != curr_rate:
                        policy_changes.append({
                            'date': rates_df.iloc[i]['date'].strftime('%Y-%m-%d'),
                            'previous_rate': prev_rate,
                            'new_rate': curr_rate,
                            'change': curr_rate - prev_rate
                        })
        
        return {
            'imf_releases': external_data['imf_releases'],
            'policy_rate_changes': policy_changes,
            'news': external_data['news']
        }
    
    def investigate_anomaly(self, anomaly, country_code, correlation_days=7):
        """
        Full investigation of an anomaly with all correlations
        
        Args:
            anomaly: Anomaly dict
            country_code: Currency code
            correlation_days: Days for grant correlation window (default 7)
        
        Returns:
            dict: Complete investigation results
        """
        investigation = {
            'anomaly': anomaly,
            'grant_correlation': self.correlate_with_grants(anomaly, correlation_days),
            'commodity_correlation': self.correlate_with_commodities(anomaly),
            'external_events': self.get_external_events(anomaly, country_code)
        }
        
        return investigation
    
    def investigate_all_anomalies(self, country_code):
        """
        Detect and investigate all anomalies
        
        Args:
            country_code: Currency code
        
        Returns:
            list: List of investigation results
        """
        # Detect anomalies
        anomalies = self.detect_steep_movements()
        
        print(f"Detected {len(anomalies)} anomalies")
        
        # Investigate each
        investigations = []
        for anomaly in anomalies:
            investigation = self.investigate_anomaly(anomaly, country_code)
            investigations.append(investigation)
        
        return investigations
    def check_correlations_lightweight(self, anomaly, country_code):
        """
        Quickly check for existence of correlations without expensive API calls
        
        Args:
            anomaly: Anomaly dict
            country_code: Currency code
            
        Returns:
            dict: {
                'has_grant': bool,
                'has_commodity': bool,
                'has_news': bool
            }
        """
        # Check grants (fast, local)
        grant_check = self.correlate_with_grants(anomaly, correlation_days=GRANT_CORRELATION_DAYS)
        
        # Check commodities (fast, local)
        comm_check = self.correlate_with_commodities(anomaly)
        
        # Check news (cache only)
        has_news = False
        if self.external_fetcher:
            country_info = PILOT_CURRENCIES.get(country_code, {})
            country_name = country_info.get('country', '')
            
            # Use check_cache_only=True to avoid API calls
            news = self.external_fetcher.get_news_headlines(
                country_name, 
                anomaly['start_date'], 
                anomaly['end_date'],
                check_cache_only=True
            )
            has_news = len(news) > 0
            
        return {
            'has_grant': grant_check['has_grant'],
            'has_commodity': comm_check['has_significant_movement'],
            'has_news': has_news
        }

if __name__ == '__main__':
    print("Anomaly Detector initialized")
