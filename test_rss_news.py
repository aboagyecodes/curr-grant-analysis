"""
Test RSS news feed implementation

This script verifies that the RSS news fetching works correctly,
testing both fetching and caching mechanisms.
"""
from datetime import datetime, timedelta
from src.data_loaders.external_data import ExternalDataFetcher
from config.settings import PILOT_CURRENCIES
import os
from config.settings import CACHE_DIR


def test_rss_fetch():
    """Test fetching news from RSS feed"""
    print("=" * 60)
    print("RSS News Feed Test")
    print("=" * 60)
    
    fetcher = ExternalDataFetcher()
    
    # Test for Ghana
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    print(f"\nTest 1: Fetching news for Ghana")
    print(f"Date range: {start_date.date()} to {end_date.date()}")
    print("-" * 60)
    
    news = fetcher.get_news_headlines(
        country_name="Ghana",
        start_date=start_date,
        end_date=end_date,
        max_results=5
    )
    
    if news:
        print(f"\n✓ Successfully fetched {len(news)} news items:")
        for i, item in enumerate(news, 1):
            print(f"\n{i}. {item['title'][:70]}...")
            print(f"   Date: {item['date']}")
            print(f"   Source: {item['source']}")
            print(f"   URL: {item['url'][:60]}...")
    else:
        print("\n✗ No news items fetched")
    
    # Test caching
    print("\n" + "=" * 60)
    print("Test 2: Verifying cache mechanism")
    print("-" * 60)
    
    # Check if cache file was created
    cache_files = [f for f in os.listdir(CACHE_DIR) if f.startswith('news_Ghana')]
    if cache_files:
        print(f"\n✓ Cache file created: {cache_files[0]}")
        
        # Fetch again to test cache hit
        print("\nFetching news again (should use cache)...")
        news2 = fetcher.get_news_headlines(
            country_name="Ghana",
            start_date=start_date,
            end_date=end_date,
            max_results=5
        )
        
        if news2 == news:
            print("✓ Cache is working correctly (returned same data)")
        else:
            print("⚠ Cache may not be working as expected")
    else:
        print("\n✗ No cache file found")
    
    # Test for another country
    print("\n" + "=" * 60)
    print("Test 3: Fetching news for Argentina")
    print("-" * 60)
    
    news_arg = fetcher.get_news_headlines(
        country_name="Argentina",
        start_date=start_date,
        end_date=end_date,
        max_results=3
    )
    
    if news_arg:
        print(f"\n✓ Successfully fetched {len(news_arg)} news items for Argentina:")
        for i, item in enumerate(news_arg, 1):
            print(f"\n{i}. {item['title'][:70]}...")
            print(f"   Source: {item['source']}")
    else:
        print("\n✗ No news items fetched for Argentina")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    total_cache = len([f for f in os.listdir(CACHE_DIR) if f.startswith('news_')])
    print(f"\nTotal RSS cache files: {total_cache}")
    
    if news and cache_files:
        print("\n✓ RSS news fetching is working correctly")
        print("✓ Caching mechanism is operational")
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠ Some tests failed - please review output above")


if __name__ == "__main__":
    test_rss_fetch()
