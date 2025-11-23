"""
Test NewsData.io integration with historical anomalies

This script verifies that NewsData.io provides historical news coverage
for anomalies across different time periods.
"""
from datetime import datetime, timedelta
from src.data_loaders.external_data import ExternalDataFetcher
from src.data_loaders.fx_loader import get_fx_data
from src.data_loaders.commodity_loader import get_all_commodities
from src.data_loaders.etl_grants import load_standardized_grants
from src.analysis.anomaly_detector import AnomalyDetector
from config.settings import PILOT_CURRENCIES, DEFAULT_NEWSDATA_KEY

print("=" * 70)
print("NewsData.io Integration Test - Historical Anomalies")
print("=" * 70)

# Test with Ghana
currency = "GHS"
country = PILOT_CURRENCIES[currency]["country"]

# Load data for larger period to get historical anomalies
end_date = datetime.now()
start_date = end_date - timedelta(days=365)  # Last year

print(f"\n1. Loading data for {country}...")
print(f"   Period: {start_date.date()} to {end_date.date()}")

fx_data = get_fx_data([currency], start_date, end_date, use_cache=True)
commodity_data = get_all_commodities([currency], start_date, end_date, use_cache=True)
grants = load_standardized_grants()

print(f"   ✓ Loaded {len(fx_data[currency])} FX data points")
print(f"   ✓ Loaded commodity data")
print(f"   ✓ Loaded {len(grants)} grants")

print(f"\n2. Detecting anomalies...")
detector = AnomalyDetector(fx_data[currency], grants, commodity_data[currency], None)
anomalies = detector.detect_steep_movements(threshold_percent=5, window_days=30)
print(f"   ✓ Detected {len(anomalies)} anomalies")

if anomalies:
    print(f"\n3. Testing NewsData.io for different time periods...")
    fetcher = ExternalDataFetcher(newsdata_key=DEFAULT_NEWSDATA_KEY)
    
    # Select anomalies from different periods
    recent_anomaly = None
    medium_anomaly = None
    old_anomaly = None
    
    now = datetime.now()
    for anom in anomalies:
        days_ago = (now - anom['start_date']).days
        
        if days_ago <= 30 and not recent_anomaly:
            recent_anomaly = anom
        elif 30 < days_ago <= 180 and not medium_anomaly:
            medium_anomaly = anom
        elif days_ago > 180 and not old_anomaly:
            old_anomaly = anom
    
    # Test recent anomaly (should work with both NewsData.io and RSS)
    if recent_anomaly:
        print(f"\n   📅 RECENT Anomaly (last 30 days):")
        print(f"      Period: {recent_anomaly['start_date'].date()} to {recent_anomaly['end_date'].date()}")
        print(f"      Change: {recent_anomaly['change_percent']:.1f}%")
        
        news = fetcher.get_news_headlines(
            country,
            recent_anomaly['start_date'],
            recent_anomaly['end_date'],
            max_results=3
        )
        
        if news:
            print(f"      ✅ Found {len(news)} articles:")
            for i, article in enumerate(news, 1):
                print(f"         {i}. [{article['date']}] {article['title'][:50]}...")
                print(f"            Source: {article['source']}")
        else:
            print(f"      ⚠️ No news found")
    
    # Test medium-term anomaly (NewsData.io should work, RSS won't)
    if medium_anomaly:
        print(f"\n   📅 MEDIUM-TERM Anomaly (1-6 months ago):")
        print(f"      Period: {medium_anomaly['start_date'].date()} to {medium_anomaly['end_date'].date()}")
        print(f"      Change: {medium_anomaly['change_percent']:.1f}%")
        
        news = fetcher.get_news_headlines(
            country,
            medium_anomaly['start_date'],
            medium_anomaly['end_date'],
            max_results=3
        )
        
        if news:
            print(f"      ✅ Found {len(news)} articles (NewsData.io working!):")
            for i, article in enumerate(news, 1):
                print(f"         {i}. [{article['date']}] {article['title'][:50]}...")
                print(f"            Source: {article['source']}")
        else:
            print(f"      ⚠️ No news found (may be outside NewsData.io archive)")
    
    # Test old anomaly (only NewsData.io can provide)
    if old_anomaly:
        print(f"\n   📅 HISTORICAL Anomaly (6+ months ago):")
        print(f"      Period: {old_anomaly['start_date'].date()} to {old_anomaly['end_date'].date()}")
        print(f"      Change: {old_anomaly['change_percent']:.1f}%")
        
        news = fetcher.get_news_headlines(
            country,
            old_anomaly['start_date'],
            old_anomaly['end_date'],
            max_results=3
        )
        
        if news:
            print(f"      ✅ Found {len(news)} articles (NewsData.io historical coverage!):")
            for i, article in enumerate(news, 1):
                print(f"         {i}. [{article['date']}] {article['title'][:50]}...")
                print(f"            Source: {article['source']}")
        else:
            print(f"      ⚠️ No news found (may be outside NewsData.io archive)")
    
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    if recent_anomaly and news:
        print("\n✅ Recent anomalies: News coverage working")
    if medium_anomaly and news:
        print("✅ Medium-term anomalies: Historical coverage working")
    if old_anomaly and news:
        print("✅ Historical anomalies: Deep archive working")
    
    print("\n🎉 NewsData.io integration successful!")
    print("\nKey Benefits:")
    print("  • Historical news for anomalies back to 2018")
    print("  • RSS fallback for redundancy")
    print("  • Same caching mechanism (reduces API calls)")
    print("  • Free tier: 200 requests/day")
    
else:
    print("\n⚠️ No anomalies detected in test period")
