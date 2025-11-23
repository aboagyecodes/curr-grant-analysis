"""
Test RSS date filtering with historical anomalies
"""
from datetime import datetime, timedelta
from src.data_loaders.external_data import ExternalDataFetcher
from src.data_loaders.fx_loader import get_fx_data
from src.data_loaders.commodity_loader import get_all_commodities
from src.data_loaders.etl_grants import load_standardized_grants
from src.analysis.anomaly_detector import AnomalyDetector
from config.settings import PILOT_CURRENCIES

print("=" * 70)
print("Testing RSS Date Filtering with Recent Anomalies")
print("=" * 70)

# Load data for Ghana - use recent period
currency = "GHS"
country = PILOT_CURRENCIES[currency]["country"]
end_date = datetime.now()
start_date = end_date - timedelta(days=60)  # Last 60 days

print(f"\n1. Loading recent FX data for {country}...")
print(f"   Period: {start_date.date()} to {end_date.date()}")
fx_data = get_fx_data([currency], start_date, end_date, use_cache=True)
print(f"   ✓ Loaded {len(fx_data[currency])} FX data points")

print(f"\n2. Loading commodity data...")
commodity_data = get_all_commodities([currency], start_date, end_date, use_cache=True)
print(f"   ✓ Loaded commodity data")

print(f"\n3. Loading grant data...")
grants = load_standardized_grants()
print(f"   ✓ Loaded {len(grants)} grants")

print(f"\n4. Detecting recent anomalies (lower threshold for testing)...")
detector = AnomalyDetector(
    fx_data[currency], 
    grants, 
    commodity_data[currency],
    None
)
anomalies = detector.detect_steep_movements(threshold_percent=3, window_days=14)
print(f"   ✓ Detected {len(anomalies)} anomalies")

if anomalies:
    print(f"\n5. Testing RSS news date filtering...")
    fetcher = ExternalDataFetcher()
    
    # Test first 3 anomalies with different date ranges
    for i, anom in enumerate(anomalies[:3], 1):
        print(f"\n   Anomaly {i}:")
        print(f"   Period: {anom['start_date'].date()} to {anom['end_date'].date()}")
        print(f"   Change: {anom['change_percent']:.1f}%")
        print(f"   Direction: {anom['direction']}")
        
        # Fetch news for anomaly period
        news = fetcher.get_news_headlines(
            country_name=country,
            start_date=anom['start_date'],
            end_date=anom['end_date'],
            max_results=3
        )
        
        if news:
            print(f"   ✓ Found {len(news)} news articles:")
            for j, article in enumerate(news, 1):
                print(f"      {j}. [{article['date']}] {article['title'][:55]}...")
                print(f"         Source: {article['source']}")
        else:
            print(f"   ⚠ No news within this specific date range")
            print(f"      (RSS feed may not have articles for this older period)")
    
    print("\n" + "=" * 70)
    print("Key Insight:")
    print("=" * 70)
    print("\nGoogle News RSS feeds only contain RECENT news (typically last 30 days).")
    print("For historical anomalies, news may not be available via RSS.")
    print("\nThis is a limitation of free RSS feeds - they don't maintain archives.")
    print("For comprehensive historical news coverage, we would need:")
    print("  • A paid news API with archival access (e.g., NewsAPI premium)")
    print("  • A news archive service")
    print("  • Pre-collected news database")
else:
    print("\n⚠ No recent anomalies detected")
    print("   Try lowering the threshold or expanding the date range")
