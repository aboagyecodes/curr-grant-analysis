
import sys
import os
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_loaders.external_data import ExternalDataFetcher
from config.settings import DEFAULT_NEWSAPI_KEY, DEFAULT_FRED_KEY, PILOT_CURRENCIES

def test_news_fetching():
    print("Testing News Fetching with Default Keys...")
    print(f"NewsAPI Key: {DEFAULT_NEWSAPI_KEY[:5]}...")
    print(f"FRED Key: {DEFAULT_FRED_KEY[:5]}...")
    
    fetcher = ExternalDataFetcher(
        newsapi_key=DEFAULT_NEWSAPI_KEY,
        fred_api_key=DEFAULT_FRED_KEY
    )
    
    # Test with Ghana (GHS)
    country_code = 'GHS'
    country_name = PILOT_CURRENCIES[country_code]['country']
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"\nFetching news for {country_name}...")
    headlines = fetcher.get_news_headlines(country_name, start_date, end_date)
    
    if headlines:
        print(f"SUCCESS: Found {len(headlines)} headlines.")
        for h in headlines:
            print(f"- {h['date']}: {h['title']}")
    else:
        print("WARNING: No headlines found. Check debug output.")

if __name__ == "__main__":
    test_news_fetching()
