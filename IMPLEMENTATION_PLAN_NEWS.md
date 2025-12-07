# News Enhancement Implementation Plan

## Objective
Aggregate news from multiple free sources (no additional API keys) to get comprehensive coverage for currency/grant analysis filtering.

## Phase 1: Enhanced RSS Feed Fetching

### Sources to Add:
1. **BBC News RSS** - `http://feeds.bbc.co.uk/news/world/rss.xml`
2. **Reuters RSS** - `https://www.reuters.com/rssFeed/worldNews`
3. **Financial Times RSS** - `https://feeds.ft.com/world`
4. **Economist RSS** - `https://www.economist.com/international/index.rss`
5. **IMF Blog RSS** - `https://blogs.imf.org/feed/`
6. **World Bank News RSS** - `https://www.worldbank.org/en/news/all`
7. **Currency News RSS** - Google News search (via RSS)
8. **Commodity News** - Relevant for currency correlation

### Implementation:
- Create `_fetch_from_rss_feeds()` method that:
  - Fetches from curated list of financial RSS feeds
  - Deduplicates articles by URL
  - Caches results for 12 hours
  - Returns more articles (100+) for better filtering

---

## Phase 2: Central Bank Website Scraping

### Sources:
For each country code, scrape official central bank press releases:
- Ghana Central Bank (BoG)
- Reserve Bank of India, South Africa, Argentina, etc.
- Turkish Central Bank
- Egyptian Central Bank
- Pakistani State Bank

### Implementation:
- Create `_scrape_central_bank_news()` method with:
  - Country-specific URLs
  - BeautifulSoup parsing
  - Fallback if scraping fails
  - Caching to avoid repeated scraping

---

## Phase 3: Semantic Filtering & Relevance Scoring

### Keywords by Relevance:
```
CRITICAL: ['currency crisis', 'devaluation', 'monetary policy', 'exchange rate']
HIGH: ['IMF', 'World Bank', 'grant', 'inflation', 'interest rate']
MEDIUM: ['economy', 'finance', 'trade', 'investment']
```

### Implementation:
- Create `filter_and_score_news()` method that:
  - Assigns relevance scores (1-5)
  - Filters by minimum relevance
  - Sorts by date + relevance
  - Returns top N articles per country

---

## Phase 4: Deduplication & Smart Caching

### Features:
- Deduplicate by URL + title similarity (using difflib)
- Cache full article list per country + date range
- Smart cache invalidation (daily)
- Store in `data/cache/news_*.json`

### Implementation:
- Create `_deduplicate_articles()` method
- Enhance cache key strategy
- Implement cache invalidation logic

---

## Phase 5: Integration

### Update Locations:
1. **external_data.py** - Add new fetching methods
2. **config/settings.py** - Add RSS feed URLs + keywords
3. **anomaly_dashboard.py** - Display filtered news with relevance scores
4. **.env.example** - Document that no new API keys needed

---

## Expected Outcomes

### Before Enhancement:
- 0-3 articles per country (NewsData.io + RSS fallback)
- Limited relevance filtering
- High failure rate

### After Enhancement:
- 20-100+ articles per country (multiple RSS + central bank)
- Smart relevance scoring
- Better anomaly correlation capability
- Graceful degradation (multiple sources mean one failure won't stop news)

---

## Implementation Order

1. ✅ Plan created
2. Add RSS feed aggregation (Phase 1)
3. Add central bank scraping (Phase 2)
4. Add relevance filtering (Phase 3)
5. Add deduplication (Phase 4)
6. Integrate into dashboard (Phase 5)
7. Test and optimize

---

## Files to Modify
- `src/data_loaders/external_data.py` (core logic)
- `config/settings.py` (configuration)
- `src/ui/anomaly_dashboard.py` (display)
- `.env.example` (documentation)

## Files to Create
- None (enhancements only)

---

## Estimated Impact
- **Code changes**: ~400-500 lines
- **Performance**: Minimal (RSS feeds cached, central bank scraping one-time)
- **Dependencies**: None (already have requests, feedparser, BeautifulSoup)
- **API keys needed**: 0 (same as current)
