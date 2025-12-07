#!/usr/bin/env python3
"""Test the enhanced RSS feed aggregation"""

from datetime import datetime, timedelta
from src.data_loaders.external_data import ExternalDataFetcher
import json

def test_rss_aggregation():
    """Test the new _fetch_from_enhanced_rss method"""
    
    fetcher = ExternalDataFetcher()
    
    # Test date range: last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"\n{'='*60}")
    print(f"Testing RSS Feed Aggregation")
    print(f"Date Range: {start_date.date()} to {end_date.date()}")
    print(f"{'='*60}\n")
    
    try:
        # Test with multiple countries
        test_countries = ['Ghana', 'Turkey', 'Argentina']
        all_articles = []
        
        for country in test_countries:
            print(f"\nFetching articles for {country}...")
            articles = fetcher._fetch_from_enhanced_rss(country, start_date, end_date)
            all_articles.extend(articles)
            print(f"  → Got {len(articles)} articles")
        
        articles = all_articles
        
        print(f"✓ Successfully fetched {len(articles)} articles from RSS feeds")
        print(f"\nFirst 5 articles:")
        print("-" * 60)
        
        for i, article in enumerate(articles[:5], 1):
            print(f"\n{i}. {article.get('title', 'N/A')[:70]}")
            print(f"   Source: {article.get('source', 'N/A')}")
            print(f"   Date: {article.get('date', 'N/A')}")
            print(f"   URL: {article.get('url', 'N/A')[:60]}...")
        
        # Count by source
        print(f"\n{'='*60}")
        print("Articles by source:")
        print("-" * 60)
        sources = {}
        for article in articles:
            source = article.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count} articles")
        
        print(f"\n{'='*60}")
        print("✓ RSS aggregation test completed successfully!")
        print(f"{'='*60}\n")
        
        return len(articles) > 0
        
    except Exception as e:
        print(f"✗ Error during RSS aggregation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rss_aggregation()
    exit(0 if success else 1)
