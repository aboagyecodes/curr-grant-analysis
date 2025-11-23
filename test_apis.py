"""
Test script to verify NewsAPI and FRED API keys
"""

from datetime import datetime, timedelta
from config.settings import DEFAULT_NEWSAPI_KEY, DEFAULT_FRED_KEY

# Test NewsAPI
print("=" * 60)
print("Testing NewsAPI")
print("=" * 60)

try:
    from newsapi import NewsApiClient
    
    newsapi_key = DEFAULT_NEWSAPI_KEY
    newsapi = NewsApiClient(api_key=newsapi_key)
    
    # Search for Ghana news in last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"Searching for 'Ghana' news from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    response = newsapi.get_everything(
        q='Ghana',
        from_param=start_date.strftime('%Y-%m-%d'),
        to=end_date.strftime('%Y-%m-%d'),
        language='en',
        sort_by='relevancy',
        page_size=3
    )
    
    if response['status'] == 'ok':
        print(f"✓ Success! Found {response['totalResults']} total articles")
        print(f"\nShowing first {len(response['articles'])} articles:")
        for i, article in enumerate(response['articles'][:3], 1):
            print(f"\n{i}. {article['title']}")
            print(f"   Source: {article['source']['name']}")
            print(f"   Published: {article['publishedAt'][:10]}")
    else:
        print(f"✗ API returned status: {response['status']}")
        
except Exception as e:
    print(f"✗ NewsAPI Error: {e}")

# Test FRED API
print("\n" + "=" * 60)
print("Testing FRED API")
print("=" * 60)

try:
    from fredapi import Fred
    
    fred_key = DEFAULT_FRED_KEY
    fred = Fred(api_key=fred_key)
    
    # Test with Turkey policy rate (known series)
    series_id = 'INTDSRTRM193N'
    print(f"Fetching Turkey policy rate series: {series_id}")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    data = fred.get_series(series_id, start_date, end_date)
    
    if len(data) > 0:
        print(f"✓ Success! Retrieved {len(data)} data points")
        print(f"\nLatest data points:")
        print(data.tail())
    else:
        print("✗ No data retrieved")
        
except Exception as e:
    print(f"✗ FRED API Error: {e}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
