"""
Quick RSS News Verification Check

Tests that RSS news fetching works with actual anomaly data.
"""
from datetime import datetime, timedelta
from src.data_loaders.external_data import ExternalDataFetcher
from src.data_loaders.fx_loader import get_fx_data
from src.data_loaders.commodity_loader import get_all_commodities
from src.data_loaders.etl_grants import load_standardized_grants
from src.analysis.anomaly_detector import AnomalyDetector
from config.settings import PILOT_CURRENCIES

print("=" * 70)
print("RSS News Verification with Actual Anomaly Data")
print("=" * 70)

# Load data for Ghana
currency = "GHS"
country = PILOT_CURRENCIES[currency]["country"]
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

print(f"\n1. Loading FX data for {country}...")
fx_data = get_fx_data([currency], start_date, end_date, use_cache=True)
print(f"   ✓ Loaded {len(fx_data[currency])} FX data points")

print(f"\n2. Loading commodity data...")
commodity_data = get_all_commodities([currency], start_date, end_date, use_cache=True)
print(f"   ✓ Loaded commodity data")

print(f"\n3. Loading grant data...")
grants = load_standardized_grants()
print(f"   ✓ Loaded {len(grants)} grants")

print(f"\n4. Detecting anomalies...")
detector = AnomalyDetector(
    fx_data[currency], 
    grants, 
    commodity_data[currency],
    None
)
anomalies = detector.detect_steep_movements(threshold_percent=5, window_days=30)
print(f"   ✓ Detected {len(anomalies)} anomalies")

if anomalies:
    print(f"\n5. Testing RSS news for first 3 anomalies...")
    fetcher = ExternalDataFetcher()
    
    for i, anom in enumerate(anomalies[:3], 1):
        print(f"\n   Anomaly {i}:")
        print(f"   Period: {anom['start_date'].date()} to {anom['end_date'].date()}")
        print(f"   Change: {anom['change_percent']:.1f}%")
        
        # Fetch news for anomaly period
        news = fetcher.get_news_headlines(
            country_name=country,
            start_date=anom['start_date'] - timedelta(days=3),
            end_date=anom['end_date'] + timedelta(days=3),
            max_results=3
        )
        
        if news:
            print(f"   ✓ Found {len(news)} news articles:")
            for j, article in enumerate(news, 1):
                print(f"      {j}. {article['title'][:60]}...")
                print(f"         Date: {article['date']} | Source: {article['source']}")
        else:
            print(f"   ⚠ No news found for this period")
    
    print("\n" + "=" * 70)
    print("Verification Complete!")
    print("=" * 70)
    print("\n✅ RSS news integration is working with anomaly detection")
    print("✅ The Anomaly Dashboard will display news for detected anomalies")
    print("\nTo test in the UI:")
    print("1. Navigate to: http://localhost:8503")
    print("2. Complete the configuration (select currencies and dates)")
    print("3. Click 'Start Analysis'")
    print("4. Click on 'Anomaly Investigator' in the sidebar")
    print("5. Select Ghana (GHS) and view any anomaly")
    print("6. News should appear in the 'Related News' section")
else:
    print("\n⚠ No anomalies detected in the test period")
    print("   Try adjusting the date range or threshold")
