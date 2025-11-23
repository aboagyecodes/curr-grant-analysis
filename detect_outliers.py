"""
Detect outliers in FX data across all currencies
"""

import pandas as pd
import glob

# Load all FX data
fx_files = glob.glob('data/fx_rates/*_fx_rates.csv')

print("=" * 80)
print("Detecting Outliers in FX Data")
print("=" * 80)

for fx_file in sorted(fx_files):
    currency = fx_file.split('/')[-1].replace('_fx_rates.csv', '')
    
    df = pd.read_csv(fx_file)
    
    # Calculate statistics
    mean = df['rate'].mean()
    std = df['rate'].std()
    median = df['rate'].median()
    min_val = df['rate'].min()
    max_val = df['rate'].max()
    
    # Find outliers (>3 std deviations from mean)
    threshold = mean + (3 * std)
    outliers = df[df['rate'] > threshold]
    
    print(f"\n{currency}:")
    print(f"  Range: {min_val:.2f} to {max_val:.2f}")
    print(f"  Mean: {mean:.2f}, Median: {median:.2f}, Std: {std:.2f}")
    print(f"  3σ threshold: {threshold:.2f}")
    
    if len(outliers) > 0:
        print(f"  ⚠️  {len(outliers)} outliers detected:")
        for _, row in outliers.iterrows():
            print(f"    - {row['date']}: {row['rate']:.2f}")
    else:
        print(f"  ✓ No outliers detected")

print("\n" + "=" * 80)
