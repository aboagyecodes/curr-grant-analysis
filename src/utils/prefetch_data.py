"""
Background Data Prefetching

Automatically fetches and caches FX and commodity data for all currencies
from 2010 to present with 12-hour cache validity.
"""

import sys
import os
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loaders.fx_loader import get_fx_data, is_cache_valid, FX_DIR
from src.data_loaders.commodity_loader import get_all_commodities, COMMODITIES_DIR
from config.settings import PILOT_CURRENCIES


def should_prefetch():
    """
    Check if we need to prefetch data by verifying cache validity.
    Returns True if any cache is missing or expired.
    """
    import glob
    
    # Check FX cache
    fx_files = glob.glob(os.path.join(FX_DIR, '*_fx_rates.csv'))
    if len(fx_files) == 0:
        return True  # No cache at all
    
    # Check if any FX cache is expired
    for fx_file in fx_files:
        if not is_cache_valid(fx_file, hours=12):
            return True
    
    # Check commodity cache
    comm_files = glob.glob(os.path.join(COMMODITIES_DIR, '*_prices.csv'))
    if len(comm_files) == 0:
        return True
    
    # Check if any commodity cache is expired
    for comm_file in comm_files:
        if not is_cache_valid(comm_file, hours=12):
            return True
    
    return False  # All cache is valid


def prefetch_all_data():
    """
    Prefetch FX and commodity data for all currencies from 2010 to present.
    Data is cached with 12-hour validity.
    Only runs if cache is missing or expired.
    """
    # Check if prefetch is needed
    if not should_prefetch():
        print("✓ All market data cache is valid (< 12 hours old)\n")
        return
    
    print("🔄 Prefetching market data...")
    
    # Get all currency codes
    all_currencies = list(PILOT_CURRENCIES.keys())
    
    # Define date range from 2010 to now
    start_date = datetime(2010, 1, 1)
    end_date = datetime.now()
    
    # Fetch FX data for all currencies
    print(f"  Fetching FX data for {len(all_currencies)} currencies...")
    fx_data = get_fx_data(all_currencies, start_date, end_date, use_cache=True)
    fx_count = sum(len(df) if not df.empty else 0 for df in fx_data.values())
    print(f"  ✓ {fx_count} FX data points cached")
    
    # Fetch commodity data for all currencies
    print(f"  Fetching commodity data...")
    comm_data = get_all_commodities(all_currencies, start_date, end_date, use_cache=True)
    comm_count = sum(sum(len(df) if not df.empty else 0 for df in currency_comms.values()) 
                     for currency_comms in comm_data.values())
    print(f"  ✓ {comm_count} commodity data points cached")
    
    print("✓ Data prefetch complete\n")


if __name__ == "__main__":
    prefetch_all_data()
