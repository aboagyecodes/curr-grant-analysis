"""
Test Yahoo Finance historical data availability for all currencies
"""

import yfinance as yf
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config.settings import CURRENCY_SYMBOLS

print("=" * 80)
print("Testing Yahoo Finance Historical Data Availability")
print("=" * 80)

start_date = datetime(2010, 1, 1)
end_date = datetime.now()

print(f"\nRequested range: {start_date.date()} to {end_date.date()}\n")

for currency_code, symbol in CURRENCY_SYMBOLS.items():
    print(f"\nTesting {currency_code} ({symbol})...")
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, auto_adjust=True)
        
        if not df.empty:
            first_date = df.index[0].date()
            last_date = df.index[-1].date()
            row_count = len(df)
            
            print(f"  ✓ Data available: {first_date} to {last_date}")
            print(f"  ✓ Total rows: {row_count}")
            
            # Check if we got data from 2010
            if first_date.year > 2010:
                print(f"  ⚠️  WARNING: Data starts in {first_date.year}, not 2010!")
        else:
            print(f"  ✗ No data returned")
            
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\n" + "=" * 80)
print("Test Complete")
print("=" * 80)
