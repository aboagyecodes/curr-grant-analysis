import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.data_loaders.external_data import ExternalDataFetcher
from config.settings import PILOT_CURRENCIES, DEFAULT_NEWSAPI_KEY, DEFAULT_FRED_KEY

def test_external_data():
    print("="*60)
    print("EXTENSIVE EXTERNAL DATA VERIFICATION")
    print("="*60)
    print(f"Testing {len(PILOT_CURRENCIES)} currencies: {', '.join(PILOT_CURRENCIES.keys())}")
    print(f"FRED Key: {DEFAULT_FRED_KEY[:5]}...{DEFAULT_FRED_KEY[-5:] if DEFAULT_FRED_KEY else 'None'}")
    print(f"NewsAPI Key: {DEFAULT_NEWSAPI_KEY[:5]}...{DEFAULT_NEWSAPI_KEY[-5:] if DEFAULT_NEWSAPI_KEY else 'None'}")
    print("-" * 60)

    fetcher = ExternalDataFetcher(
        newsapi_key=DEFAULT_NEWSAPI_KEY,
        fred_api_key=DEFAULT_FRED_KEY
    )

    results = []

    for currency_code, info in PILOT_CURRENCIES.items():
        country = info['country']
        print(f"\nTesting {currency_code} ({country})...")
        
        # 1. Test FRED Policy Rate
        print("  > Fetching FRED Policy Rate...", end=" ", flush=True)
        try:
            # Fetch for last 5 years to ensure we hit some data
            start_date = datetime.now() - timedelta(days=365*5)
            end_date = datetime.now()
            policy_rate = fetcher.get_policy_rates(currency_code, start_date, end_date)
            
            if not policy_rate.empty:
                # Debug index type
                # print(f"DEBUG: Index type: {type(policy_rate.index)}")
                # print(f"DEBUG: First few rows:\n{policy_rate.head()}")
                
                idx = policy_rate.index.max()
                if hasattr(idx, 'strftime'):
                    latest_date = idx.strftime('%Y-%m-%d')
                else:
                    latest_date = str(idx)
                    
                latest_val = policy_rate.iloc[-1]['rate']
                print(f"✅ SUCCESS ({len(policy_rate)} records, Latest: {latest_val}% on {latest_date})")
                fred_status = "OK"
                fred_details = f"{len(policy_rate)} pts, Last: {latest_val}%"
            else:
                print("⚠️ EMPTY (No data returned)")
                fred_status = "EMPTY"
                fred_details = "No data"
        except Exception as e:
            print(f"❌ FAILED ({str(e)})")
            fred_status = "ERROR"
            fred_details = str(e)

        # 2. Test NewsData.io (Historical)
        print("  > Fetching NewsData.io Headlines...", end=" ", flush=True)
        try:
            # Search for a known event or just general query
            # Using a wide window to maximize chance of hits
            news_start = datetime.now() - timedelta(days=30)
            news_end = datetime.now()
            
            # We use the cache_only=False to force a real check if needed, 
            # but let's respect the cache first to avoid spamming if we ran this before.
            # Actually, user wants to test if it's *working*, so we should probably allow API calls.
            # But get_news_headlines defaults to cache, then API.
            
            headlines = fetcher.get_news_headlines(
                currency_code, 
                news_start, 
                news_end,
                check_cache_only=False 
            )
            
            if headlines:
                print(f"✅ SUCCESS ({len(headlines)} articles)")
                news_status = "OK"
                news_details = f"{len(headlines)} articles"
            else:
                print("⚠️ EMPTY (No articles found)")
                news_status = "EMPTY"
                news_details = "No articles"
                
        except Exception as e:
            print(f"❌ FAILED ({str(e)})")
            news_status = "ERROR"
            news_details = str(e)
            
        results.append({
            'Currency': currency_code,
            'Country': country,
            'FRED Status': fred_status,
            'FRED Details': fred_details,
            'News Status': news_status,
            'News Details': news_details
        })

    # Summary Table
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    print("="*80)

if __name__ == "__main__":
    test_external_data()
