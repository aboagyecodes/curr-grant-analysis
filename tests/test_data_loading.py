import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loaders.fx_loader import get_fx_data, FX_DIR
from src.data_loaders.commodity_loader import get_commodities_for_currency, COMMODITIES_DIR

def test_fx_loading():
    print("\n--- Testing FX Loading ---")
    currency = 'GHS'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Clear cache for test
    cache_file = os.path.join(FX_DIR, f'{currency}_fx_rates.csv')
    if os.path.exists(cache_file):
        os.remove(cache_file)
    
    # Create a dummy "stale" cache file
    print("Creating dummy stale cache file...")
    os.makedirs(FX_DIR, exist_ok=True)
    dummy_df = pd.DataFrame({
        'date': [start_date.date(), end_date.date()],
        'rate': [10.0, 11.0],
        'currency': [currency, currency]
    })
    dummy_df.to_csv(cache_file, index=False)
    
    # Set mtime to 24 hours ago
    old_time = time.time() - (24 * 3600)
    os.utime(cache_file, (old_time, old_time))
    
    # 1. Fetch fresh (should fail API and fallback)
    print("\n1. Fetching fresh data (expecting API failure + fallback)...")
    start_time = time.time()
    data = get_fx_data([currency], start_date, end_date, use_cache=True)
    duration = time.time() - start_time
    
    if currency in data and not data[currency].empty:
        print(f"✅ Success: Fetched {len(data[currency])} records in {duration:.2f}s")
        if os.path.exists(cache_file):
            print("✅ Cache file created")
        else:
            print("❌ Cache file NOT created")
    else:
        print("❌ Failed to fetch data")
        return

    # 2. Fetch from cache
    print("\n2. Fetching from cache...")
    start_time = time.time()
    data_cached = get_fx_data([currency], start_date, end_date, use_cache=True)
    duration = time.time() - start_time
    
    if currency in data_cached and not data_cached[currency].empty:
        print(f"✅ Success: Loaded {len(data_cached[currency])} records in {duration:.2f}s")
        # It should be much faster
        if duration < 1.0:
            print("✅ Speed indicates cache usage")
        else:
            print("⚠️ Warning: Slow load time, might not be using cache")
    else:
        print("❌ Failed to load from cache")

def test_commodity_loading():
    print("\n--- Testing Commodity Loading ---")
    currency = 'GHS' # Gold, Cocoa
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Clear cache for test
    for comm in ['Gold', 'Cocoa']:
        cache_file = os.path.join(COMMODITIES_DIR, f'{comm}_prices.csv')
        if os.path.exists(cache_file):
            os.remove(cache_file)
            print(f"Cleared cache for {comm}")
    
    # 1. Fetch fresh
    print("\n1. Fetching fresh data...")
    start_time = time.time()
    data = get_commodities_for_currency(currency, start_date, end_date, use_cache=True)
    duration = time.time() - start_time
    
    if data:
        print(f"✅ Success: Fetched commodities {list(data.keys())} in {duration:.2f}s")
    else:
        print("❌ Failed to fetch commodities")
        return

    # 2. Fetch from cache
    print("\n2. Fetching from cache...")
    start_time = time.time()
    data_cached = get_commodities_for_currency(currency, start_date, end_date, use_cache=True)
    duration = time.time() - start_time
    
    if data_cached:
        print(f"✅ Success: Loaded commodities {list(data_cached.keys())} in {duration:.2f}s")
    else:
        print("❌ Failed to load from cache")

if __name__ == "__main__":
    test_fx_loading()
    test_commodity_loading()
