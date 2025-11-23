"""
FX Rates Data Loader

Loads foreign exchange rate data for pilot currencies using yfinance
or from user-uploaded CSV files.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import CURRENCY_SYMBOLS, FX_DIR


def fetch_fx_rates(currency_code, start_date, end_date):
    """
    Fetch FX rates from Yahoo Finance
    
    Args:
        currency_code: ISO 3-letter currency code (e.g., 'GHS')
        start_date: Start date (datetime or string 'YYYY-MM-DD')
        end_date: End date (datetime or string 'YYYY-MM-DD')
    
    Returns:
        pd.DataFrame: DataFrame with Date and Rate columns
    """
    try:
        symbol = CURRENCY_SYMBOLS.get(currency_code)
        if not symbol:
            print(f"No symbol found for currency: {currency_code}")
            return pd.DataFrame()
        
        # Convert dates to datetime if strings
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)
        
        # Fetch data from Yahoo Finance
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)
        
        if df.empty:
            print(f"No FX data available for {currency_code}")
            return pd.DataFrame()
        
        # Use Close price as the exchange rate
        result = pd.DataFrame({
            'date': df.index,
            'rate': df['Close'].values,
            'currency': currency_code
        })
        
        result['date'] = pd.to_datetime(result['date']).dt.date
        result = result.reset_index(drop=True)
        
        return result
        
    except Exception as e:
        print(f"Error fetching FX rates for {currency_code}: {e}")
        return pd.DataFrame()


def load_fx_from_csv(file_path, currency_code):
    """
    Load FX rates from user-uploaded CSV
    
    Expected format:
    - Date column (various date formats supported)
    - Rate/Price/Close column
    
    Args:
        file_path: Path to CSV file
        currency_code: Currency code for labeling
    
    Returns:
        pd.DataFrame: Standardized FX data
    """
    try:
        df = pd.read_csv(file_path)
        
        # Find date column
        date_col = None
        for col in df.columns:
            if 'date' in col.lower():
                date_col = col
                break
        
        # Find rate column
        rate_col = None
        for col in df.columns:
            col_lower = col.lower()
            if any(x in col_lower for x in ['rate', 'price', 'close', 'value']):
                rate_col = col
                break
        
        if not date_col or not rate_col:
            print(f"Could not identify date or rate columns in {file_path}")
            return pd.DataFrame()
        
        # Standardize
        result = pd.DataFrame({
            'date': pd.to_datetime(df[date_col]).dt.date,
            'rate': df[rate_col],
            'currency': currency_code
        })
        
        return result
        
    except Exception as e:
        print(f"Error loading FX CSV {file_path}: {e}")
        return pd.DataFrame()


import time
import json

def is_cache_valid(cache_file, hours=12):
    """
    Check if cache file exists and is less than N hours old
    
    Args:
        cache_file: Path to cache file
        hours: Maximum age in hours (default 12)
    
    Returns:
        bool: True if cache is valid, False otherwise
    """
    if not os.path.exists(cache_file):
        return False
    
    file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
    age = datetime.now() - file_time
    
    return age < timedelta(hours=hours)


def clean_outliers(df, column='rate', sigma_threshold=3):
    """
    Remove outliers from FX data using statistical methods
    
    Outliers are defined as values > mean + (sigma_threshold * std)
    They are replaced with interpolated values for smooth charting
    
    Args:
        df: DataFrame with FX data
        column: Column name to clean (default 'rate')
        sigma_threshold: Number of standard deviations for outlier detection (default 3)
    
    Returns:
        DataFrame: Cleaned data with outliers replaced
    """
    if df.empty or column not in df.columns:
        return df
    
    df = df.copy()
    
    # Calculate statistics
    mean = df[column].mean()
    std = df[column].std()
    
    # Define outlier threshold
    upper_threshold = mean + (sigma_threshold * std)
    lower_threshold = mean - (sigma_threshold * std)
    
    # Identify outliers
    outliers_mask = (df[column] > upper_threshold) | (df[column] < lower_threshold)
    outlier_count = outliers_mask.sum()
    
    if outlier_count > 0:
        print(f"  Cleaning {outlier_count} outlier(s) in {df['currency'].iloc[0] if 'currency' in df.columns else 'data'}")
        
        # Replace outliers with NaN, then interpolate
        df.loc[outliers_mask, column] = np.nan
        df[column] = df[column].interpolate(method='linear')
        
        # Fill any remaining NaNs at the edges using ffill (forward fill) and bfill (backward fill)
        df[column] = df[column].bfill().ffill()
    
    return df


def get_fx_data(currencies, start_date, end_date, use_cache=True):
    """
    Get FX data for multiple currencies, using cache or fetching fresh
    
    Args:
        currencies: List of currency codes
        start_date: Start date
        end_date: End date
        use_cache: Whether to use cached CSV files if available
    
    Returns:
        dict: {currency_code: DataFrame}
    """
    fx_data = {}
    
    for currency in currencies:
        cache_file = os.path.join(FX_DIR, f'{currency}_fx_rates.csv')
        
        # Determine if we should use cache
        cache_exists = os.path.exists(cache_file)
        cache_fresh = is_cache_valid(cache_file, hours=12)
        
        # Try to load from cache if it's fresh and use_cache is True
        if use_cache and cache_exists and cache_fresh:
            print(f"Loading cached FX data for {currency} (Fresh)")
            df = load_fx_from_csv(cache_file, currency)
            if not df.empty:
                # Clean outliers from cached data
                df = clean_outliers(df, column='rate', sigma_threshold=3)
                # Filter by date range
                df['date'] = pd.to_datetime(df['date'])
                df = df[(df['date'] >= pd.to_datetime(start_date)) & 
                       (df['date'] <= pd.to_datetime(end_date))]
                fx_data[currency] = df
                continue
        
        # If we're here, we need to fetch fresh data
        print(f"Fetching fresh FX data for {currency}...")
        df = pd.DataFrame()
        
        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                df = fetch_fx_rates(currency, start_date, end_date)
                if not df.empty:
                    break
                else:
                    print(f"  Attempt {attempt+1}/{max_retries}: No data returned")
            except Exception as e:
                print(f"  Attempt {attempt+1}/{max_retries} failed: {e}")
            
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
        
        # If fetch succeeded
        if not df.empty:
            fx_data[currency] = df
            
            # Cache it
            try:
                os.makedirs(FX_DIR, exist_ok=True)
                df.to_csv(cache_file, index=False)
                print(f"  Cached to {cache_file}")
            except Exception as e:
                print(f"  Warning: Could not save cache: {e}")
        
        # Fallback: If fetch failed but we have old cache, use it
        elif cache_exists:
            print(f"  ⚠️ API failed. using expired cache for {currency}")
            df = load_fx_from_csv(cache_file, currency)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df[(df['date'] >= pd.to_datetime(start_date)) & 
                       (df['date'] <= pd.to_datetime(end_date))]
                fx_data[currency] = df
    
    return fx_data


def save_fx_data(fx_data, output_dir=None):
    """
    Save FX data to CSV files
    
    Args:
        fx_data: dict of {currency: DataFrame}
        output_dir: Directory to save files (defaults to FX_DIR)
    """
    if output_dir is None:
        output_dir = FX_DIR
    
    os.makedirs(output_dir, exist_ok=True)
    
    for currency, df in fx_data.items():
        output_path = os.path.join(output_dir, f'{currency}_fx_rates.csv')
        df.to_csv(output_path, index=False)
        print(f"Saved {currency} FX data to {output_path}")


if __name__ == '__main__':
    # Test with one currency
    test_currency = 'GHS'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    print(f"Testing FX loader for {test_currency}")
    df = fetch_fx_rates(test_currency, start_date, end_date)
    print(df.head())
    print(f"\nTotal records: {len(df)}")
