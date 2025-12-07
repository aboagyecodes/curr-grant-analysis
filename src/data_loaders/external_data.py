"""
External Data Integration Module

Fetches data from external sources:
- IMF Press Releases
- Central Bank Policy Rates (via FRED)
- News Headlines (via multiple RSS feeds + central bank scraping)
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import os
import json
import sys
import feedparser
import logging
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import (
    CACHE_DIR, PILOT_CURRENCIES, DEFAULT_NEWSDATA_KEY,
    RSS_FEEDS, CENTRAL_BANK_URLS, NEWS_KEYWORDS, COUNTRY_KEYWORDS,
    NEWS_CACHE_VALIDITY_HOURS, NEWS_MAX_ARTICLES_PER_FETCH
)

logger = logging.getLogger(__name__)


class ExternalDataFetcher:
    """Handles fetching and caching of external data sources"""
    
    def __init__(self, newsapi_key=None, fred_api_key=None, newsdata_key=None):
        self.newsapi_key = newsapi_key  # Deprecated
        self.fred_api_key = fred_api_key
        self.newsdata_key = newsdata_key or DEFAULT_NEWSDATA_KEY
        os.makedirs(CACHE_DIR, exist_ok=True)
    
    def get_imf_press_releases(self, country_name, start_date, end_date):
        """
        Scrape IMF press releases for a specific country
        
        Args:
            country_name: Full country name
            start_date: Start date
            end_date: End date
        
        Returns:
            list: List of dicts with {date, title, url}
        """
        cache_file = os.path.join(CACHE_DIR, f'imf_{country_name.replace(" ", "_")}_press.json')
        
        # Check cache
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cached = json.load(f)
                # Filter by date range
                filtered = [
                    item for item in cached
                    if start_date <= item['date'] <= end_date
                ]
                if filtered:
                    return filtered
        
        # Fetch fresh data
        try:
            # IMF Press Release search URL
            base_url = "https://www.imf.org/en/News/SearchNews"
            params = {
                'q': country_name,
                'from': start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else start_date,
                'to': end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else end_date,
            }
            
            # Note: This is a simplified scraper. IMF website structure may vary.
            # In production, you may need to use Selenium or IMF API if available
            
            releases = []
            # Placeholder implementation - actual scraping would go here
            print(f"IMF press releases scraping not fully implemented. Using placeholder.")
            
            # Cache results
            with open(cache_file, 'w') as f:
                json.dump(releases, f)
            
            return releases
            
        except Exception as e:
            print(f"Error fetching IMF press releases: {e}")
            return []
    
    def get_policy_rates(self, country_code, start_date, end_date):
        """
        Get central bank policy rates from FRED
        
        Args:
            country_code: ISO currency code
            start_date: Start date
            end_date: End date
        
        Returns:
            pd.DataFrame: Date and Rate columns (may be empty if not available)
        """
        if not self.fred_api_key:
            return pd.DataFrame()
        
        try:
            from fredapi import Fred
            fred = Fred(api_key=self.fred_api_key)
            
            # FRED series IDs for policy rates (examples)
            # Map currencies to FRED series IDs (IMF Discount Rates: INTDSR + 2-letter ISO + M193N)
            series_map = {
                'TRY': 'INTDSRTRM193N',  # Turkey
                'GHS': 'INTDSRGHM193N',  # Ghana
                'EGP': 'INTDSREGM193N',  # Egypt
                'PKR': 'INTDSRPKM193N',  # Pakistan
                'BDT': 'INTDSRBDM193N',  # Bangladesh
                'ARS': 'INTDSRARM193N',  # Argentina
                'LKR': 'INTDSRLKM193N',  # Sri Lanka
                'LBP': 'INTDSRLBM193N',  # Lebanon
                'COP': 'COLIRSTCI01STM', # Colombia (Interbank Rate)
            }
            
            series_id = series_map.get(country_code)
            if not series_id:
                # Policy rates not available for this country
                return pd.DataFrame()
            
            # Silently return empty if series doesn't exist or no data available
            try:
                df = fred.get_series(series_id, start_date, end_date)
                if df.empty:
                    return pd.DataFrame()
                    
                result = pd.DataFrame({
                    'date': df.index,
                    'rate': df.values
                })
                return result
            except Exception:
                # FRED series doesn't exist or other FRED API error
                return pd.DataFrame()
            
        except Exception:
            # API key error or other initialization issue
            return pd.DataFrame()
    
    
    def _fetch_from_newsdata_io(self, country_name, start_date, end_date, max_results=3):
        """
        Fetch news from NewsData.io API (historical coverage)
        
        Returns:
            list: List of news dicts, or empty list on failure
        """
        if not self.newsdata_key:
            return []
        
        try:
            start_str = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date)
            end_str = end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else str(end_date)
            
            url = "https://newsdata.io/api/1/news"
            params = {
                'apikey': self.newsdata_key,
                'q': country_name,
                'from_date': start_str,
                'to_date': end_str,
                'language': 'en',
                'size': max_results
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'success':
                # NewsData.io returned an error (e.g., 422, API plan limits)
                return []
            
            headlines = []
            for article in data.get('results', []):
                headlines.append({
                    'date': article.get('pubDate', '')[:10],
                    'title': article.get('title', ''),
                    'source': article.get('source_id', 'Unknown'),
                    'url': article.get('link', '')
                })
            
            return headlines
            
        except requests.exceptions.RequestException:
            # API rate limit, 422 error, or connection issue - return empty to trigger RSS fallback
            return []
        except Exception:
            # JSON parsing or other error
            return []
    
    def _fetch_from_rss(self, country_name, start_date, end_date, max_results=3):
        """
        Fetch news from RSS feed (fallback, recent news only)
        
        Returns:
            list: List of news dicts, or empty list on failure
        """
        # Convert dates to datetime objects if they aren't already
        if hasattr(start_date, 'strftime'):
            start_dt = start_date
        else:
            start_dt = datetime.strptime(str(start_date), '%Y-%m-%d')
        
        if hasattr(end_date, 'strftime'):
            end_dt = end_date
        else:
            end_dt = datetime.strptime(str(end_date), '%Y-%m-%d')
        
        try:
            # Build Google News RSS URL
            query = country_name.replace(' ', '+')
            rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            
            # Parse RSS feed
            feed = feedparser.parse(rss_url)
            
            if feed.bozo:
                print(f"RSS parsing error: {feed.bozo_exception}")
                return []
            
            all_headlines = []
            # Process up to 100 entries for date filtering
            for entry in feed.entries[:100]:
                pub_date_str = entry.get('published', entry.get('updated', ''))
                
                try:
                    from email.utils import parsedate_to_datetime
                    pub_date_obj = parsedate_to_datetime(pub_date_str)
                    
                    # Filter by date range with buffer
                    buffer_days = 2
                    if (pub_date_obj.date() >= (start_dt - timedelta(days=buffer_days)).date() and 
                        pub_date_obj.date() <= (end_dt + timedelta(days=buffer_days)).date()):
                        
                        # Extract source
                        source = ''
                        try:
                            if hasattr(entry, 'source') and 'title' in entry.source:
                                source = entry.source['title']
                            else:
                                link_parts = entry.link.split('//')
                                if len(link_parts) > 1:
                                    domain_parts = link_parts[1].split('/')
                                    source = domain_parts[0]
                        except Exception:
                            source = 'Google News'
                        
                        all_headlines.append({
                            'date': pub_date_obj.strftime('%Y-%m-%d'),
                            'title': entry.title,
                            'source': source,
                            'url': entry.link,
                            '_pub_date_obj': pub_date_obj
                        })
                except Exception:
                    continue
            
            # Sort and limit
            all_headlines.sort(key=lambda x: x['_pub_date_obj'], reverse=True)
            for h in all_headlines:
                del h['_pub_date_obj']
            headlines = all_headlines[:max_results]
            
            return headlines
            
        except Exception:
            return []
    
    def _fetch_from_enhanced_rss(self, country_name, start_date, end_date, max_results=100):
        """
        Fetch news from Google News (country-specific search)
        Falls back to general country searches to maximize coverage
        
        Returns:
            list: List of news dicts, sorted by date
        """
        all_articles = []
        
        # List of search queries to try (country + relevant keywords)
        keywords = COUNTRY_KEYWORDS.get(country_name, [country_name])
        search_queries = [country_name] + keywords[:3]  # Top 3 keywords
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        for query in search_queries:
            try:
                # Build Google News RSS URL with search query
                query_encoded = query.replace(' ', '+')
                feed_url = f"https://news.google.com/rss/search?q={query_encoded}&hl=en-US&gl=US&ceid=US:en"
                
                # Fetch with headers
                response = requests.get(feed_url, headers=headers, timeout=15)
                response.raise_for_status()
                
                # Parse RSS feed
                feed = feedparser.parse(response.content)
                
                if not feed.entries:
                    logger.debug(f"No entries found for query: {query}")
                    continue
                
                logger.debug(f"Found {len(feed.entries)} entries for query: {query}")
                
                for entry in feed.entries[:30]:  # Process more entries per query
                    try:
                        pub_date_str = entry.get('published', entry.get('updated', ''))
                        
                        if not pub_date_str:
                            continue
                        
                        pub_date_obj = parsedate_to_datetime(pub_date_str)
                        
                        # Filter by date range with buffer
                        buffer_days = 3
                        if not (pub_date_obj.date() >= (start_date - timedelta(days=buffer_days)).date() and 
                                pub_date_obj.date() <= (end_date + timedelta(days=buffer_days)).date()):
                            continue
                        
                        # Extract source from entry
                        source = 'Google News'
                        try:
                            if hasattr(entry, 'source') and 'title' in entry.source:
                                source = entry.source['title']
                        except:
                            pass
                        
                        article = {
                            'date': pub_date_obj.strftime('%Y-%m-%d'),
                            'title': entry.get('title', 'No title'),
                            'description': entry.get('summary', '')[:300],
                            'source': source,
                            'url': entry.get('link', ''),
                            'published_at': pub_date_obj.isoformat()
                        }
                        
                        all_articles.append(article)
                    except Exception as e:
                        logger.debug(f"Error parsing entry: {e}")
                        continue
                        
            except Exception as e:
                logger.debug(f"Error fetching for query '{query}': {e}")
                continue
        
        # Deduplicate by URL
        unique_articles = {}
        for article in all_articles:
            url = article.get('url', '')
            if url and url not in unique_articles:
                unique_articles[url] = article
        
        # Sort by date (newest first)
        sorted_articles = sorted(
            unique_articles.values(),
            key=lambda x: x['published_at'],
            reverse=True
        )
        
        return sorted_articles[:max_results]
    
    def _fetch_from_central_bank(self, country_code, start_date, end_date, max_results=50):
        """
        Fetch news from central bank press releases via web scraping
        
        Returns:
            list: List of news dicts from central bank sources
        """
        if country_code not in CENTRAL_BANK_URLS:
            return []
        
        try:
            cb_info = CENTRAL_BANK_URLS[country_code]
            press_url = cb_info['press_url']
            
            response = requests.get(press_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Try to find news items (selectors may vary by site)
            selectors = [
                cb_info.get('selector', ''),
                '.press-release', '.news-item', '.announcement',
                '[class*="press"]', '[class*="news"]', '[class*="release"]',
                'article', '.article'
            ]
            
            news_items = []
            for selector in selectors:
                if selector:
                    news_items.extend(soup.select(selector))
            
            # Extract information from found items
            for item in news_items[:max_results]:
                try:
                    # Try to extract title
                    title_elem = item.find(['h2', 'h3', 'a', 'p'])
                    title = title_elem.get_text(strip=True) if title_elem else ''
                    
                    if not title or len(title) < 5:
                        continue
                    
                    # Try to extract URL
                    link_elem = item.find('a')
                    url = link_elem.get('href', '') if link_elem else ''
                    if url and not url.startswith('http'):
                        url = press_url.rsplit('/', 1)[0] + '/' + url
                    
                    # Try to extract date (often in class or data attribute)
                    date_elem = item.find(class_=lambda x: x and ('date' in x.lower() or 'time' in x.lower()))
                    if not date_elem:
                        date_elem = item.find(['time', 'span'])
                    
                    date_str = date_elem.get_text(strip=True) if date_elem else ''
                    
                    # Try to parse date
                    try:
                        from dateutil import parser as date_parser
                        pub_date = date_parser.parse(date_str)
                    except:
                        pub_date = datetime.now()
                    
                    # Check if within date range
                    if pub_date.date() < start_date or pub_date.date() > end_date:
                        continue
                    
                    article = {
                        'date': pub_date.strftime('%Y-%m-%d'),
                        'title': title[:200],
                        'description': '',
                        'source': cb_info['name'],
                        'url': url,
                        'published_at': pub_date.isoformat()
                    }
                    
                    articles.append(article)
                except Exception as e:
                    continue
            
            return articles[:max_results]
            
        except Exception as e:
            logger.debug(f"Error fetching central bank news for {country_code}: {e}")
            return []
    
    def _filter_and_score_news(self, articles, country_code):
        """
        Filter and score news articles by relevance to currency analysis
        
        Scoring:
        - CRITICAL keywords: +3 points
        - HIGH keywords: +2 points
        - MEDIUM keywords: +1 point
        - Country-specific keywords: +2 points
        - Minimum score to include: 2
        
        Returns:
            list: Scored and filtered articles, sorted by score then date
        """
        scored_articles = []
        
        country_keywords = COUNTRY_KEYWORDS.get(country_code, [])
        
        for article in articles:
            content = f"{article.get('title', '')} {article.get('description', '')}".lower()
            score = 0
            
            # Check for critical keywords
            for keyword in NEWS_KEYWORDS.get('CRITICAL', []):
                if keyword.lower() in content:
                    score += 3
            
            # Check for high-relevance keywords
            for keyword in NEWS_KEYWORDS.get('HIGH', []):
                if keyword.lower() in content:
                    score += 2
            
            # Check for medium-relevance keywords
            for keyword in NEWS_KEYWORDS.get('MEDIUM', []):
                if keyword.lower() in content:
                    score += 1
            
            # Check for country-specific keywords
            for keyword in country_keywords:
                if keyword.lower() in content:
                    score += 2
            
            # Only include articles with minimum relevance
            if score >= 2:
                article['relevance_score'] = score
                scored_articles.append(article)
        
        # Sort by score (descending) then by date (newest first)
        scored_articles.sort(
            key=lambda x: (x['relevance_score'], x['published_at']),
            reverse=True
        )
        
        return scored_articles
    
    def get_news_headlines(self, country_name, start_date, end_date, max_results=20, check_cache_only=False):
        """
        Get news headlines with enhanced multi-source coverage
        
        Strategy:
        1. Check cache first
        2. Fetch from enhanced RSS feeds (BBC, Reuters, FT, Economist, IMF, World Bank)
        3. Fetch from central bank press releases (country-specific)
        4. Try NewsData.io API if available (historical coverage)
        5. Filter and score by relevance
        6. Deduplicate
        7. Cache results
        
        Args:
            country_name: Full country name
            start_date: Start date
            end_date: End date
            max_results: Max number of results to return
            check_cache_only: If True, only return cached results
        
        Returns:
            list: Scored and filtered news articles
        """
        # Get country code from country name
        country_code = None
        for code, info in PILOT_CURRENCIES.items():
            if info.get('country') == country_name:
                country_code = code
                break
        
        if not country_code:
            return []
        
        # Convert dates to strings for cache key
        if hasattr(start_date, 'strftime'):
            start_str = start_date.strftime('%Y-%m-%d')
        else:
            start_str = str(start_date)
        
        if hasattr(end_date, 'strftime'):
            end_str = end_date.strftime('%Y-%m-%d')
        else:
            end_str = str(end_date)
        
        # Create cache key
        cache_key = f"news_enhanced_{country_name.replace(' ', '_')}_{start_str}_{end_str}.json"
        cache_file = os.path.join(CACHE_DIR, cache_key)
        
        # Check cache first
        if os.path.exists(cache_file):
            try:
                # Check cache validity
                cache_age_hours = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))).total_seconds() / 3600
                if cache_age_hours < NEWS_CACHE_VALIDITY_HOURS:
                    with open(cache_file, 'r') as f:
                        cached_data = json.load(f)
                        return cached_data[:max_results]
            except Exception as e:
                logger.debug(f"Could not read cache: {e}")
        
        # If cache only mode, return empty
        if check_cache_only:
            return []
        
        # Aggregate articles from multiple sources
        all_articles = []
        
        # Source 1: Enhanced RSS feeds
        rss_articles = self._fetch_from_enhanced_rss(country_name, start_date, end_date, NEWS_MAX_ARTICLES_PER_FETCH)
        all_articles.extend(rss_articles)
        
        # Source 2: Central bank press releases
        cb_articles = self._fetch_from_central_bank(country_code, start_date, end_date, 50)
        all_articles.extend(cb_articles)
        
        # Source 3: NewsData.io API (if available and working)
        newsdata_articles = self._fetch_from_newsdata_io(country_name, start_date, end_date, NEWS_MAX_ARTICLES_PER_FETCH)
        all_articles.extend(newsdata_articles)
        
        # Deduplicate by URL
        unique_articles = {}
        for article in all_articles:
            url = article.get('url', '')
            title = article.get('title', '')
            
            # Use URL as primary key, fallback to title
            key = url if url else title
            
            if key and key not in unique_articles:
                unique_articles[key] = article
        
        # Filter and score for relevance
        scored_articles = self._filter_and_score_news(
            list(unique_articles.values()),
            country_code
        )
        
        # Cache the results
        if scored_articles:
            try:
                with open(cache_file, 'w') as f:
                    json.dump(scored_articles, f, indent=2, default=str)
            except Exception as e:
                logger.debug(f"Could not write cache: {e}")
        
        return scored_articles[:max_results]
    
    def get_all_correlation_data(self, country_code, start_date, end_date):
        """
        Get all external correlation data for a country/date range
        
        Args:
            country_code: ISO currency code
            start_date: Start date
            end_date: End date
        
        Returns:
            dict: {
                'imf_releases': list,
                'policy_rates': DataFrame,
                'news': list
            }
        """
        country_info = PILOT_CURRENCIES.get(country_code, {})
        country_name = country_info.get('country', '')
        
        print(f"Fetching external data for {country_name}...")
        
        return {
            'imf_releases': self.get_imf_press_releases(country_name, start_date, end_date),
            'policy_rates': self.get_policy_rates(country_code, start_date, end_date),
            'news': self.get_news_headlines(country_name, start_date, end_date)
        }


if __name__ == '__main__':
    # Test (requires API keys)
    fetcher = ExternalDataFetcher()
    
    test_country = 'GHS'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    data = fetcher.get_all_correlation_data(test_country, start_date, end_date)
    print(json.dumps(data, indent=2, default=str))
