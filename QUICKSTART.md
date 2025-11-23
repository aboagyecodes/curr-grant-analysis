# Quick Start Guide

## Installation

1. **Activate virtual environment**:
   ```bash
   cd /Users/clementaboagyeyeboah/Desktop/aboagyecodes/project
   source venv/bin/activate
   ```

2. **Dependencies already installed** ✓

## Before Running

Upload your grant data files:

- **IMF files**: Place in `data/grants/imf/`
- **World Bank files**: Place in `data/grants/worldbank/`

Expected format: CSV or Excel with columns for Country, Date, Amount, Program/Project name

## Launch Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage Flow

### Step 1: Configuration Page
1. Select currencies to analyze (e.g., GHS, ARS, TRY)
2. Choose date range (default: 2 years)
3. Click **"Standardize Grant Data"** button (if files uploaded)
4. (Optional) Enter API keys for NewsAPI and FRED
5. Click **"Run Analysis"** button

### Step 2: Grant Impact Dashboard
1. Select a currency from dropdown
2. View timeline chart with grant markers
3. Toggle commodity overlays on/off
4. Set analysis windows:
   - Choose preset (short/medium/long term)
   - Or custom weeks for pre/post analysis
5. Click **"Analyze Grant Impact"**
6. Review results:
   - Impact scores chart
   - Detailed table
   - Download CSV

### Step 3: Anomaly Investigator
1. Select a currency
2. Adjust detection settings:
   - Volatility threshold (default: 10%)
   - Window size (default: 30 days)
3. Click **"Detect Anomalies"**
4. Select an anomaly from the list
5. Review investigation:
   - Grant correlations
   - Commodity movements
   - Policy rate changes
   - IMF press releases
   - News headlines
6. Add research notes and save

## Pilot Currencies

- **GHS** - Ghanaian Cedi
- **ARS** - Argentine Peso
- **TRY** - Turkish Lira
- **EGP** - Egyptian Pound
- **PKR** - Pakistani Rupee
- **LKR** - Sri Lankan Rupee
- **LBP** - Lebanese Pound
- **COP** - Colombian Peso

## API Keys (Optional but Recommended)

- **NewsAPI**: Get free key at https://newsapi.org
- **FRED**: Get key at https://fred.stlouisfed.org

These enable news headlines and policy rate analysis in the Anomaly Investigator.

## Troubleshooting

**"No grant files detected"**: Upload CSV/Excel files to `data/grants/imf/` or `data/grants/worldbank/`

**"No FX data available"**: The app will fetch from Yahoo Finance automatically. Check internet connection.

**"API key required"**: Some features (news, policy rates) need API keys entered in Configuration page.

## Data Sources

- **FX Rates**: Yahoo Finance (automatic)
- **Commodities**: Yahoo Finance futures (automatic)
- **Grants**: Your uploaded files
- **News**: NewsAPI (requires key)
- **Policy Rates**: FRED API (requires key)

All data is cached locally after first fetch to improve performance.
