# IMF/World Bank Currency Impact Analysis App

A comprehensive Streamlit application for analyzing the impact of IMF and World Bank grants on currency valuation in developing nations.

## Features

### 1. Grant Impact Analyzer
- Analyze grant-to-currency correlations
- Track commodity price influences
- Compare pre/post-disbursement trends
- Generate impact scores (1-5 scale)

### 2. Anomaly Investigator
- Detect steep currency movements (>10% in <30 days)
- Correlate with grants, commodities, and external events
- Integrate IMF press releases, policy rates, and news
- Save research notes for each anomaly

## Pilot Currencies

- **GHS** - Ghanaian Cedi
- **ARS** - Argentine Peso
- **TRY** - Turkish Lira
- **EGP** - Egyptian Pound
- **PKR** - Pakistani Rupee
- **LKR** - Sri Lankan Rupee
- **LBP** - Lebanese Pound
- **COP** - Colombian Peso

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare Grant Data

Place your IMF and World Bank CSV/Excel files in:
- IMF files: `data/grants/imf/`
- World Bank files: `data/grants/worldbank/`

### 3. Configure Environment Variables

**REQUIRED** - The application needs API keys to fetch external data:

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```bash
   # Get your free API keys from:
   # - FRED: https://fred.stlouisfed.org/docs/api/api_key.html
   # - NewsData.io: https://newsdata.io/
   # - NewsAPI: https://newsapi.org/ (optional, deprecated)
   
   FRED_API_KEY=your_actual_fred_key_here
   NEWSDATA_API_KEY=your_actual_newsdata_key_here
   NEWSAPI_KEY=your_actual_newsapi_key_here
   ```

3. **IMPORTANT**: Never commit your `.env` file to version control. It's already in `.gitignore`.

### 4. Run ETL Process


The app will prompt you to standardize the grant data on first run, or you can run manually:

```bash
python src/data_loaders/etl_grants.py
```

### 4. Optional: Configure API Keys

For enhanced analysis with external data:
- **NewsAPI**: Get free key at [newsapi.org](https://newsapi.org)
- **FRED API**: Get key at [fred.stlouisfed.org](https://fred.stlouisfed.org)

Enter these in the Configuration page of the app.

### 5. Launch Application

```bash
streamlit run app.py
```

## Usage Workflow

1. **Configuration Page**
   - Select currencies to analyze
   - Choose date range
   - Upload/standardize grant data
   - Enter API keys (optional)
   - Click "Run Analysis"

2. **Grant Impact Dashboard**
   - View currency timeline with grant markers
   - Toggle commodity overlays
   - Set analysis windows (pre/post grant)
   - Review impact scores and detailed results
   - Download results as CSV

3. **Anomaly Investigator**
   - Detect currency anomalies
   - Investigate selected anomalies
   - View correlations with:
     - Grant disbursements
     - Commodity price movements
     - Policy rate changes
     - IMF press releases
     - News headlines
   - Save research notes

## Data Sources

- **FX Rates**: Yahoo Finance (via yfinance)
- **Commodities**: Yahoo Finance futures
- **Policy Rates**: FRED API
- **News**: NewsAPI
- **Grants**: User-provided IMF/World Bank files

## Project Structure

```
project/
├── app.py                      # Main Streamlit app
├── requirements.txt            # Dependencies
├── config/
│   └── settings.py             # Configuration
├── src/
│   ├── data_loaders/           # ETL and data fetching
│   ├── analysis/               # Analysis engines
│   ├── ui/                     # Streamlit pages
│   └── utils/                  # Charts and persistence
├── data/                       # Data storage
└── assets/                     # CSS styling
```

## Expected Grant Data Format

The ETL module will attempt to auto-detect columns, but ideally your CSV/Excel files should contain:

**IMF Files:**
- Country/Member name
- Disbursement date
- Amount (in USD)
- Program/Arrangement type

**World Bank Files:**
- Country name
- Approval/Effective date
- Total commitment/Amount (in USD)
- Project name/Purpose

## Notes

- Auto-detect columns in grant files for flexible input formats
- Caches FX and commodity data to minimize API calls
- Stores user research notes in `data/cache/anomaly_notes.json`
- All analysis is performed locally

## Security Best Practices

- **Never commit API keys** to version control
- **Never share your `.env` file** - it contains sensitive credentials
- **Rotate API keys** if they are accidentally exposed
- **Use `.env.example`** as a template when setting up on new machines
- Review `.gitignore` before committing to ensure sensitive files are excluded

## License

This project is for analytical purposes. Please ensure compliance with data provider terms of use.
