"""
Commodity Prices Data Loader

Loads commodity price data for top exports of each pilot country.
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import COMMODITY_SYMBOLS, COMMODITIES_DIR, PILOT_CURRENCIES


def fetch_commodity_prices(commodity_name, start_date, end_date):
    """
    Fetch commodity prices from Yahoo Finance
    
    Args:
        commodity_name: Commodity name (e.g., 'Gold', 'Oil')
        start_date: Start date
        end_date: End date
    
    Returns:
        pd.DataFrame: DataFrame with Date and Price columns
    """
    try:
        symbol = COMMODITY_SYMBOLS.get(commodity_name)
        if not symbol:
            print(f"No symbol available for commodity: {commodity_name}")
            return pd.DataFrame()
        
        # Convert dates
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)
        
        # Fetch from Yahoo Finance
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)
        
        if df.empty:
            print(f"No data available for {commodity_name}")
            return pd.DataFrame()
        
        result = pd.DataFrame({
            'date': df.index,
            'price': df['Close'].values,
            'commodity': commodity_name
        })
        
        result['date'] = pd.to_datetime(result['date']).dt.date
        result = result.reset_index(drop=True)
        
        return result
        
    except Exception as e:
        print(f"Error fetching commodity prices for {commodity_name}: {e}")
        return pd.DataFrame()


def load_commodity_from_csv(file_path, commodity_name):
    """
    Load commodity prices from CSV
    
    Args:
        file_path: Path to CSV
        commodity_name: Name for labeling
    
    Returns:
        pd.DataFrame: Standardized commodity data
    """
    try:
        df = pd.read_csv(file_path)
        
        # Find date column
        date_col = None
        for col in df.columns:
            if 'date' in col.lower():
                date_col = col
                break
        
        # Find price column
        price_col = None
        for col in df.columns:
            col_lower = col.lower()
            if any(x in col_lower for x in ['price', 'close', 'value', 'rate']):
                price_col = col
                break
        
        if not date_col or not price_col:
            print(f"Could not identify columns in {file_path}")
            return pd.DataFrame()
        
        result = pd.DataFrame({
            'date': pd.to_datetime(df[date_col]).dt.date,
            'price': df[price_col],
            'commodity': commodity_name
        })
        
        return result
        
    except Exception as e:
        print(f"Error loading commodity CSV {file_path}: {e}")
        return pd.DataFrame()


import time
import json

def is_cache_valid(file_path, hours=12):
    """Check if a cache file is valid (less than 'hours' old)"""
    if not os.path.exists(file_path):
        return False
    
    file_age = time.time() - os.path.getmtime(file_path)
    return file_age < (hours * 3600)


def get_commodities_for_currency(currency_code, start_date, end_date, use_cache=True):
    """
    Get commodity data for a specific currency's top exports
    
    Args:
        currency_code: Currency code
        start_date: Start date
        end_date: End date
        use_cache: Use cached data if available
    
    Returns:
        dict: {commodity_name: DataFrame}
    """
    commodity_data = {}
    
    # Get commodities for this currency
    currency_info = PILOT_CURRENCIES.get(currency_code)
    if not currency_info:
        return commodity_data
    
    commodities = currency_info.get('commodities', [])
    
    for commodity in commodities:
        cache_file = os.path.join(COMMODITIES_DIR, f'{commodity.replace(" ", "_")}_prices.csv')
        
        # Determine if we should use cache
        cache_exists = os.path.exists(cache_file)
        cache_fresh = is_cache_valid(cache_file, hours=12)
        
        # Try to load from cache if it's fresh and use_cache is True
        if use_cache and cache_exists and cache_fresh:
            print(f"Loading cached commodity data for {commodity} (Fresh)")
            df = load_commodity_from_csv(cache_file, commodity)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df[(df['date'] >= pd.to_datetime(start_date)) & 
                       (df['date'] <= pd.to_datetime(end_date))]
                commodity_data[commodity] = df
                continue
        
        # If we're here, we need to fetch fresh data
        print(f"Fetching fresh commodity data for {commodity}...")
        df = pd.DataFrame()
        
        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                df = fetch_commodity_prices(commodity, start_date, end_date)
                if not df.empty:
                    break
                else:
                    print(f"  Attempt {attempt+1}/{max_retries}: No data returned")
            except Exception as e:
                print(f"  Attempt {attempt+1}/{max_retries} failed: {e}")
            
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
        
        # If fetch succeeded
        if not df.empty:
            commodity_data[commodity] = df
            
            # Cache it
            try:
                os.makedirs(COMMODITIES_DIR, exist_ok=True)
                df.to_csv(cache_file, index=False)
                print(f"  Cached to {cache_file}")
            except Exception as e:
                print(f"  Warning: Could not save cache: {e}")
        
        # Fallback: If fetch failed but we have old cache, use it
        elif cache_exists:
            print(f"  ⚠️ API failed. using expired cache for {commodity}")
            df = load_commodity_from_csv(cache_file, commodity)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df[(df['date'] >= pd.to_datetime(start_date)) & 
                       (df['date'] <= pd.to_datetime(end_date))]
                commodity_data[commodity] = df
    
    return commodity_data


def get_all_commodities(currencies, start_date, end_date, use_cache=True):
    """
    Get all commodities for multiple currencies
    
    Args:
        currencies: List of currency codes
        start_date: Start date
        end_date: End date
        use_cache: Use cached data
    
    Returns:
        dict: {currency_code: {commodity_name: DataFrame}}
    """
    all_data = {}
    
    for currency in currencies:
        print(f"\nFetching commodities for {currency}...")
        commodity_data = get_commodities_for_currency(currency, start_date, end_date, use_cache)
        all_data[currency] = commodity_data
    
    return all_data


if __name__ == '__main__':
    # Test with Ghana (Gold, Cocoa)
    test_currency = 'GHS'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    print(f"Testing commodity loader for {test_currency}")
    data = get_commodities_for_currency(test_currency, start_date, end_date, use_cache=False)
    
    for commodity, df in data.items():
        print(f"\n{commodity}:")
        print(df.head())
        print(f"Total records: {len(df)}")
