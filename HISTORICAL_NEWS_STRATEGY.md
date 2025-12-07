# Historical News Strategy for Grant Period (1986-2026)

## Problem
Current implementation uses Google News RSS (last 30 days only), but grant data spans 40 years (1986-2026). We need historical news correlating with anomalies throughout this entire period.

## Solution: Multi-Tier Historical News Strategy

### Tier 1: Archive-Based News Sources (Searchable Historical Data)
These sources allow historical queries with date ranges:

1. **Google News Archive Search** (1900-present, limited free access)
   - Free tier: ~50 searches/day
   - API: `https://news.google.com/newspapers?nstart={date}&output=rss`
   - Coverage: Most major news events archived

2. **NewsData.io Historical API** (if API key available)
   - Your API key already supports historical queries
   - Coverage: 2020-present (varies by source)
   - Implementation: Already partially integrated

3. **Wikipedia Event Timelines** (curated, structured)
   - Country crisis timelines
   - Economic events (currency crises, policy changes)
   - IMF bailout announcements
   - Highly reliable for major events

### Tier 2: Secondary Data Sources (News Aggregators)
Sources that maintain archives or indexed historical content:

1. **Internet Archive Wayback Machine**
   - Captures news site snapshots
   - Can extract historical headlines
   - Coverage: 1996-present

2. **Historical Financial News Databases**
   - IMF Press Releases (downloadable archive)
   - World Bank Announcements
   - Central Bank Press Releases

### Tier 3: Structured Event Data
Pre-curated historical events:

1. **ACLED Dataset** (Armed Conflict Location & Event Data)
   - Political/economic events
   - Dates, locations, types
   - Coverage: 1997-present (free)

2. **FRED Economic Events Calendar**
   - Policy rate changes
   - Economic reports
   - Coverage: Full historical FRED data available

3. **IMF & World Bank Archives**
   - Press release archives (searchable by date/country)
   - Published decisions
   - Coverage: Complete since founding

## Proposed Implementation

### Phase 1: Structured Historical Events (Immediate)
```python
# Add to external_data.py
def get_historical_events(country_name, start_date, end_date):
    """
    Fetch from structured historical sources:
    - IMF press release archives (by date)
    - World Bank announcements
    - Central bank policy decisions (from FRED)
    - Wikipedia economic event timelines
    """
```

### Phase 2: News Archive Search (2-3 days)
```python
# Add archive search methods
def search_google_news_archive(country_name, start_date, end_date):
    """Search Google News Archive for historical news"""
    
def search_newsdata_historical(country_name, start_date, end_date):
    """Query NewsData.io historical API if available"""
```

### Phase 3: Wayback Machine Scraping (Optional)
```python
# Advanced: Extract headlines from archived news pages
def scrape_wayback_machine(news_domain, start_date, end_date):
    """Scrape Internet Archive for historical news"""
```

## Recommended Quick Win: Historical IMF/World Bank Data

IMF and World Bank maintain complete archives of:
- **IMF Press Releases**: Full searchable archive
- **World Bank News**: Archive searchable by date and country
- **Both organizations document grant disbursements** with dates

These are highly relevant to your analysis and provide:
✅ Exact dates (not just news articles)
✅ Direct connection to grant programs
✅ Complete historical coverage
✅ No API limits
✅ Already partially configured in code

## Implementation Priority

**HIGH PRIORITY (Do First):**
1. Scrape IMF press release archives by country+date
2. Scrape World Bank news archives by country+date
3. Extract central bank policy announcements from FRED

**MEDIUM PRIORITY (Do Second):**
4. Implement Google News Archive search
5. Add NewsData.io historical query support
6. Create Wikipedia event timeline scraper

**LOW PRIORITY (Optional):**
7. Wayback Machine integration
8. ACLED event data import
9. Advanced news sentiment analysis

## Data Sources Ready to Use (No Extra APIs)

### 1. IMF Press Release Archives
```
https://www.imf.org/en/News/SearchNews?page={page}
Searchable by:
- Country name
- Date range
- News type (press releases, statements, etc.)
```

### 2. World Bank News
```
https://www.worldbank.org/en/news/all
Searchable by date and country
Complete archive available
```

### 3. FRED Economic Events
```
Already integrated - contains all policy rate changes with dates
Complete historical data since policy tracking began
```

### 4. Wikipedia Economic Crisis Timeline
```
https://en.wikipedia.org/wiki/Currency_crisis
https://en.wikipedia.org/wiki/1998_Russian_financial_crisis
etc. - all with dates and references
```

## Expected Outcome

Instead of:
```
Recent News Only (2025-2026)
Ghana inflation slows
```

We'll have:
```
2008 Financial Crisis Events
2014 Ghana Economic Crisis
2020 COVID Impact
2023 IMF Bailout Agreement
Plus 100+ other dated events throughout period
```

This enables proper correlation with:
- Grant disbursement dates
- Currency anomalies
- Commodity price shocks
- Policy changes

## Next Steps

1. **Decision**: Which sources to prioritize?
   - Recommend: IMF + World Bank archives first (direct grant correlation)
   - Then: FRED policy data
   - Then: Google News Archive if free tier sufficient

2. **Implementation Path**:
   - Use existing BeautifulSoup scraping framework
   - Add date-range filtering to archive searches
   - Create historical event caching (no need to re-fetch)

3. **Testing**:
   - Verify date coverage for each country
   - Compare with actual grant disbursement dates
   - Validate correlation with currency anomalies
