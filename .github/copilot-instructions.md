# Copilot Instructions for Currency Impact Analysis

## Project Overview

This is a **Streamlit data analysis application** that analyzes IMF/World Bank grant impacts on developing nation currency valuations. The app combines grant data, FX rates, commodity prices, and news/policy data to detect anomalies and quantify grant effectiveness.

**Key Stack**: Streamlit, pandas, yfinance, plotly, FRED API, NewsData API

## Architecture

### Three-Layer Pattern

1. **Data Layer** (`src/data_loaders/`)
   - `etl_grants.py`: Standardizes raw IMF/WorldBank CSVs into unified schema with country mapping
   - `fx_loader.py`: Fetches FX rates from Yahoo Finance; caches to `data/fx_rates/*.csv`
   - `commodity_loader.py`: Fetches commodity futures; caches to `data/commodities/*.csv`
   - `external_data.py`: Fetches IMF press releases, policy rates (FRED), news (RSS/NewsData)

2. **Analysis Layer** (`src/analysis/`)
   - `grant_impact.py`: Analyzes pre/post grant trends; calculates impact scores (1-5)
   - `anomaly_detector.py`: Detects steep currency moves (>10% in <30 days); correlates with grants/commodities

3. **UI Layer** (`src/ui/`)
   - `config_page.py`: Landing page; currency/date selection; standardizes grant data on first run
   - `grant_dashboard.py`: Impact analysis; timeline with grant markers; commodity overlays
   - `anomaly_dashboard.py`: Anomaly detection/investigation; saves research notes

**State Management** (`src/utils/state_manager.py`): Centralized session state ensures data persists across page reloads. Navigation via query params (`?page=grant|anomaly`).

## Critical Workflows

### Grant Data Processing (auto-triggered on first app run)

```bash
python src/data_loaders/etl_grants.py  # Manual run if needed
```

- Reads IMF/WorldBank CSVs from `data/grants/{imf,worldbank}/`
- Maps country names via `COUNTRY_CODE_MAP` (handles "Türkiye" → "Turkey", etc.)
- Outputs standardized CSV to `data/grants/standardized/grants.csv` (schema: country_code, disbursement_date, amount_usd, program_type)
- **Key pattern**: Graceful failure; app runs without grants, just with FX/commodities

### Running the App

```bash
streamlit run app.py --server.enableCORS false --server.enableXsrfProtection false
```

- Initializes session state (`config`, `selected_currency`, `grant_analyses`, `anomalies`)
- Auto-prefetches commodity/FX data in background (non-blocking)
- Redirects to config page if not configured; otherwise uses query param `?page=grant|anomaly`

## Key Patterns & Conventions

### Configuration & Settings
- All hardcoded values live in `config/settings.py`: PILOT_CURRENCIES, CURRENCY_SYMBOLS, COMMODITY_SYMBOLS, thresholds
- Currency → commodity mapping: e.g., `GHS → [Gold, Cocoa]`; `ARS → [Soybeans, Corn]`
- API keys injected via `.env` file; loaded by `dotenv` in settings.py

### Data Loading & Caching
- FX/commodity CSVs cached in `data/` directories to avoid repeated API calls
- External data (news, IMF press releases) cached as JSON in `data/cache/`
- **Strategy**: Fetch once, cache indefinitely; prefetch in background to avoid UI blocking

### Analysis Patterns
- **Time windows**: Grant impact analyzed in pre/post windows (default 4 weeks each, configurable)
- **Anomaly detection**: Percentage change over sliding window; flagged if threshold exceeded
- **Correlation logic**: For anomalies, search grants/commodities within ±CORRELATION_DAYS (default ~14 days)

### UI/Session State
- Single session state object in `st.session_state['config']` holds: configured flag, selected currencies, date range
- Query params (`st.query_params["page"]`) drive page navigation; `navigate_to()` handles sync
- Download buttons export CSV using `st.download_button()`; results keyed by currency + analysis window

## Integration Points & External Data

| Source | Module | Cache | Notes |
|--------|--------|-------|-------|
| Yahoo Finance FX | `fx_loader.py` | `data/fx_rates/*.csv` | Real-time; USDXXX=X format |
| Yahoo Finance Commodities | `commodity_loader.py` | `data/commodities/*.csv` | Futures; GC=F, CL=F, ZS=F, etc. |
| FRED API | `external_data.py` | `data/cache/` | Policy rates; requires API key |
| NewsData.io | `external_data.py` | `data/cache/news_*.json` | News headlines; RSS fallback available |
| IMF Press Releases | `external_data.py` | `data/cache/imf_*.json` | Web-scraped; placeholder implementation |

## Project-Specific Conventions

1. **Country Code Mapping**: All grants normalized to 3-letter ISO codes (GHS, ARS, TRY, etc.). Manual mappings in `COUNTRY_CODE_MAP` + IMF-specific map in `parse_imf_csv()`
2. **Date Handling**: All dates converted to `pd.to_datetime()` early; format output as `YYYY-MM-DD`
3. **Impact Scores**: Calculated via weighted formula in `grant_impact.py` using `IMPACT_SCORE_WEIGHTS`; always 1-5 integer scale
4. **Anomaly IDs**: Unique per date-range; format: `{start_date_YYYY-MM-DD}_{end_date_YYYY-MM-DD}`
5. **Error Handling**: Graceful degradation; missing data sources don't crash the app (e.g., news unavailable → skip news section)

## Common Development Tasks

### Adding a New Currency
1. Add to `PILOT_CURRENCIES` dict in `config/settings.py` with name, country, commodities list
2. Add Yahoo Finance symbol to `CURRENCY_SYMBOLS` (e.g., `'NEW': 'USDNEW=X'`)
3. Ensure commodity symbols exist in `COMMODITY_SYMBOLS`
4. Add country mapping in `etl_grants.py` for grant data

### Fixing Data Loading Issues
- Check `data/fx_rates/`, `data/commodities/`, `data/cache/` for stale/missing files
- Inspect grant CSV format; verify column names match `parse_imf_csv()` expectations
- Enable debug prints in `app.py` (currently active); check console output

### Testing
- Run `pytest tests/` for data loading tests
- Manual: `python verify_news.py`, `python test_apis.py` for API integration validation

## Debugging Tips

- **Session state mismatch**: Check both `st.session_state` AND `st.query_params` when debugging navigation
- **Cache stale data**: Delete files in `data/cache/` to force re-fetch
- **API failures**: Check `.env` keys; add logging in `external_data.py` before API calls
- **ETL hangs**: Grant CSV parsing can timeout on large files; add row limits in `etl_grants.py` if needed

## Development Commands

```bash
# Run app
streamlit run app.py --server.enableCORS false --server.enableXsrfProtection false

# Manually standardize grants
python src/data_loaders/etl_grants.py

# Validate imports & config
python -c "from config.settings import *; print('Config OK')"

# Check data availability
python verify_news.py  # Validate news API integration
python test_apis.py    # Test FRED, yfinance
```
