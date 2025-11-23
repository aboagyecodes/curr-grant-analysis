"""
Helper script to create sample FX data CSV files for testing
when Yahoo Finance API is unavailable.

Creates CSV files with synthetic data for all pilot currencies.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Base directory
data_dir = 'data/fx_rates'
os.makedirs(data_dir, exist_ok=True)

# Currencies and their approximate exchange rates
currencies = {
    'GHS': 12.0,   # Ghana Cedi
    'ARS': 800.0,  # Argentine Peso
    'TRY': 28.0,   # Turkish Lira
    'EGP': 48.0,   # Egyptian Pound
    'PKR': 278.0,  # Pakistani Rupee
    'LKR': 325.0,  # Sri Lankan Rupee
    'LBP': 89500.0,  # Lebanese Pound
    'COP': 4000.0,  # Colombian Peso
}

# Generate 2 years of daily data
end_date = datetime.now()
start_date = end_date - timedelta(days=730)
dates = pd.date_range(start=start_date, end=end_date, freq='D')

for currency, base_rate in currencies.items():
    print(f'Generating data for {currency}...')
    
    # Create synthetic data with realistic trends and volatility
    np.random.seed(hash(currency) % 2**32)  # Consistent seed per currency
    
    # Random walk with trend
    returns = np.random.normal(0.0002, 0.01, len(dates))  # Slight depreciation trend
    prices = base_rate * np.exp(np.cumsum(returns))
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'rate': prices,
        'currency': currency
    })
    
    # Save to CSV
    output_file = os.path.join(data_dir, f'{currency}_fx_rates.csv')
    df.to_csv(output_file, index=False)
    print(f'  Saved to {output_file}')

print('\n✓ Sample FX data files created!')
print(f'Location: {data_dir}/')
print('\nThese files will be used when Yahoo Finance API is unavailable.')
