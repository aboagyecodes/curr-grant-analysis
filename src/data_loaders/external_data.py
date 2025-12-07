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
        - Pre-scored articles (from historical CSV) are kept as-is
        
        Returns:
            list: Scored and filtered articles, sorted by score then date
        """
        scored_articles = []
        
        country_keywords = COUNTRY_KEYWORDS.get(country_code, [])
        
        for article in articles:
            # If article already has relevance_score (from CSV/archives), keep it
            if 'relevance_score' in article:
                # Still filter by minimum threshold
                if article['relevance_score'] >= 2:
                    scored_articles.append(article)
                continue
            
            # Otherwise, calculate score from content
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
            key=lambda x: (
                x.get('relevance_score', 0),
                x.get('published_at', x.get('date', ''))
            ),
            reverse=True
        )
        
        return scored_articles
    
    def _fetch_from_historical_events_csv(self, country_name, start_date, end_date, max_results=50):
        """
        Fetch pre-curated historical economic events from CSV
        
        CSV contains major economic/currency events matched to countries
        Covers 2000-present, most relevant events for currency analysis
        
        Returns:
            list: List of historical events within date range
        """
        try:
            events_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'data', 'historical_economic_events.csv'
            )
            
            if not os.path.exists(events_file):
                return []
            
            df = pd.read_csv(events_file)
            df['date'] = pd.to_datetime(df['date'])
            
            # Filter by country
            country_events = df[df['country_name'] == country_name]
            
            # Filter by date range
            filtered = country_events[
                (country_events['date'].dt.date >= start_date.date()) &
                (country_events['date'].dt.date <= end_date.date())
            ]
            
            articles = []
            for _, row in filtered.iterrows():
                articles.append({
                    'date': row['date'].strftime('%Y-%m-%d'),
                    'title': row['event_title'],
                    'source': row['source'],
                    'url': row.get('source_url', '#'),  # Use source_url from CSV
                    'description': '',
                    'published_at': row['date'].isoformat(),
                    'relevance_score': int(row['relevance_score'])
                })
            
            return articles[:max_results]
            
        except Exception as e:
            logger.debug(f"Error reading historical events CSV: {e}")
            return []
    
    def _fetch_from_wikipedia_events(self, country_name, start_date, end_date, max_results=50):
        """
        Fetch historical economic events from Wikipedia
        
        Wikipedia maintains curated historical timelines with dates
        This is highly reliable for major economic events
        
        Returns:
            list: List of historical events with dates
        """
        try:
            articles = []
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Common Wikipedia pages for economic/crisis events by country
            wikipedia_search_urls = [
                f"https://en.wikipedia.org/wiki/{country_name}",
                f"https://en.wikipedia.org/wiki/Economy_of_{country_name}",
                f"https://en.wikipedia.org/wiki/{country_name}_economic_crisis",
                "https://en.wikipedia.org/wiki/Currency_crisis",
                "https://en.wikipedia.org/wiki/IMF_external_interventions",
            ]
            
            for wiki_url in wikipedia_search_urls:
                try:
                    response = requests.get(wiki_url, headers=headers, timeout=10)
                    if response.status_code != 200:
                        continue
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for infoboxes with dates
                    infoboxes = soup.find_all(['table'], {'class': ['infobox', 'wikitable']})
                    
                    for box in infoboxes:
                        for row in box.find_all('tr'):
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 2:
                                text = ' '.join([cell.get_text(strip=True) for cell in cells])
                                
                                # Look for date patterns
                                try:
                                    # Try to find dates in the text
                                    if any(str(year) in text for year in range(start_date.year, end_date.year + 1)):
                                        # Try to parse date
                                        possible_dates = []
                                        for year in range(start_date.year, end_date.year + 1):
                                            if str(year) in text:
                                                possible_dates.append((year, text))
                                        
                                        if possible_dates:
                                            year, event_text = possible_dates[0]
                                            date_str = f'{year}-01-01'
                                            articles.append({
                                                'date': date_str,
                                                'title': event_text[:100],
                                                'source': f'Wikipedia: {country_name}',
                                                'url': wiki_url,
                                                'description': '',
                                                'published_at': f'{year}-01-01T00:00:00',
                                                'relevance_score': 2  # Wikipedia events are moderately relevant
                                            })
                                except:
                                    continue
                    
                    # Look for historical sections with dates
                    for section in soup.find_all(['h2', 'h3']):
                        section_title = section.get_text(strip=True)
                        if any(word in section_title.lower() for word in ['history', 'crisis', 'crisis', 'economy', 'financial']):
                            # Get content after this section
                            content = section.find_next('p')
                            if content:
                                text = content.get_text(strip=True)
                                # Look for dates
                                for year in range(start_date.year, end_date.year + 1):
                                    if str(year) in text:
                                        articles.append({
                                            'date': f'{year}-06-15',  # Use mid-year
                                            'title': f'{section_title}: {text[:80]}',
                                            'source': 'Wikipedia',
                                            'url': wiki_url,
                                            'description': '',
                                            'published_at': f'{year}-06-15T00:00:00',
                                            'relevance_score': 2
                                        })
                                        break
                
                except Exception as e:
                    logger.debug(f"Error fetching Wikipedia {wiki_url}: {e}")
                    continue
            
            return articles[:max_results]
            
        except Exception as e:
            logger.debug(f"Error in _fetch_from_wikipedia_events: {e}")
            return []
    
    def _fetch_from_imf_archive(self, country_name, start_date, end_date, max_results=50):
        """
        Fetch historical news from IMF Press Release Archive
        
        Works for any date range including historical data
        
        Returns:
            list: List of news dicts from IMF, or empty list on failure
        """
        try:
            # Convert dates to strings
            start_str = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date)
            end_str = end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else str(end_date)
            
            # Normalize country name for search
            search_terms = [country_name.lower()]
            if country_name.lower() == 'turkey':
                search_terms.append('türkiye')
            
            articles = []
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            for search_term in search_terms:
                try:
                    # IMF News Search with date filtering
                    # Note: IMF website may require pagination for historical search
                    url = f"https://www.imf.org/en/News/SearchNews"
                    params = {
                        'page': 1,
                        'pageSize': 20,
                        'sort': 'NewestFirst',
                    }
                    
                    response = requests.get(url, params=params, headers=headers, timeout=15)
                    if response.status_code != 200:
                        continue
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find news items (structure may vary)
                    for item in soup.find_all(['article', 'div'], {'class': ['news-item', 'release', 'story']}):
                        try:
                            # Extract title
                            title_elem = item.find(['h3', 'h2', 'a'])
                            title = title_elem.get_text(strip=True) if title_elem else None
                            
                            # Extract date
                            date_elem = item.find(['time', 'span'], {'class': ['date', 'pubdate']})
                            date_str = date_elem.get_text(strip=True) if date_elem else None
                            
                            # Extract URL
                            link_elem = item.find('a')
                            url = link_elem.get('href', '') if link_elem else ''
                            
                            if not (title and date_str):
                                continue
                            
                            # Parse date
                            try:
                                pub_date = pd.to_datetime(date_str)
                                # Filter by date range
                                if pub_date.date() >= start_date.date() and pub_date.date() <= end_date.date():
                                    articles.append({
                                        'date': pub_date.strftime('%Y-%m-%d'),
                                        'title': title,
                                        'source': 'IMF Press Release',
                                        'url': url if url.startswith('http') else f'https://www.imf.org{url}',
                                        'description': '',
                                        'published_at': pub_date.isoformat(),
                                        'relevance_score': 3  # IMF releases are highly relevant
                                    })
                            except:
                                continue
                        except Exception as e:
                            logger.debug(f"Error parsing IMF news item: {e}")
                            continue
                
                except Exception as e:
                    logger.debug(f"Error fetching IMF archive for '{search_term}': {e}")
                    continue
            
            return articles[:max_results] if articles else []
            
        except Exception as e:
            logger.debug(f"Error in _fetch_from_imf_archive: {e}")
            return []
    
    def _fetch_from_worldbank_archive(self, country_name, start_date, end_date, max_results=50):
        """
        Fetch historical news from World Bank Archives
        
        Works for any date range including historical data
        
        Returns:
            list: List of news dicts from World Bank, or empty list on failure
        """
        try:
            start_str = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date)
            end_str = end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else str(end_date)
            
            articles = []
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            try:
                # World Bank News archive search
                url = "https://www.worldbank.org/en/news/all"
                params = {
                    'qterm': country_name,
                    'start_year': start_date.year if hasattr(start_date, 'year') else int(str(start_date)[:4]),
                    'end_year': end_date.year if hasattr(end_date, 'year') else int(str(end_date)[:4]),
                }
                
                response = requests.get(url, params=params, headers=headers, timeout=15)
                if response.status_code != 200:
                    return []
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find news articles
                for item in soup.find_all(['article', 'div'], {'class': ['news-item', 'news', 'story']}):
                    try:
                        # Extract title
                        title_elem = item.find(['h3', 'h2', 'a'])
                        title = title_elem.get_text(strip=True) if title_elem else None
                        
                        # Extract date
                        date_elem = item.find(['time', 'span'], {'class': ['date', 'pubdate', 'pub-date']})
                        date_str = date_elem.get_text(strip=True) if date_elem else None
                        
                        # Extract URL
                        link_elem = item.find('a')
                        article_url = link_elem.get('href', '') if link_elem else ''
                        
                        if not (title and date_str):
                            continue
                        
                        # Parse date
                        try:
                            pub_date = pd.to_datetime(date_str)
                            # Filter by date range
                            if pub_date.date() >= start_date.date() and pub_date.date() <= end_date.date():
                                articles.append({
                                    'date': pub_date.strftime('%Y-%m-%d'),
                                    'title': title,
                                    'source': 'World Bank News',
                                    'url': article_url if article_url.startswith('http') else f'https://www.worldbank.org{article_url}',
                                    'description': '',
                                    'published_at': pub_date.isoformat(),
                                    'relevance_score': 3  # World Bank news is highly relevant
                                })
                        except:
                            continue
                    except Exception as e:
                        logger.debug(f"Error parsing World Bank news item: {e}")
                        continue
            
            except Exception as e:
                logger.debug(f"Error fetching World Bank archive: {e}")
            
            return articles[:max_results] if articles else []
            
        except Exception as e:
            logger.debug(f"Error in _fetch_from_worldbank_archive: {e}")
            return []
    
    def get_historical_news(self, country_name, start_date, end_date, max_results=50):
        """
        Get historical news from official sources only
        
        Specifically designed for historical periods (1986-2025)
        Pulls from pre-curated CSV, IMF, and World Bank archives
        (Wikipedia excluded - only uses official news sources)
        
        Args:
            country_name: Country name
            start_date: Start date (any date, including historical)
            end_date: End date
            max_results: Maximum articles to return
        
        Returns:
            list: List of news dicts with relevance scores
        """
        all_articles = []
        
        # Try curated historical events first (fastest, most reliable)
        csv_articles = self._fetch_from_historical_events_csv(country_name, start_date, end_date, max_results)
        all_articles.extend(csv_articles)
        logger.debug(f"Found {len(csv_articles)} events from historical CSV")
        
        # Try IMF archive
        imf_articles = self._fetch_from_imf_archive(country_name, start_date, end_date, max_results)
        all_articles.extend(imf_articles)
        logger.debug(f"Found {len(imf_articles)} articles from IMF archive")
        
        # Try World Bank archive
        wb_articles = self._fetch_from_worldbank_archive(country_name, start_date, end_date, max_results)
        all_articles.extend(wb_articles)
        logger.debug(f"Found {len(wb_articles)} articles from World Bank archive")
        
        # Deduplicate by URL (skip CSV entries without URLs)
        unique_articles = {}
        for article in all_articles:
            url = article.get('url', '')
            title = article.get('title', '')
            
            # Use URL if available, otherwise use title
            if url and url != '#':
                key = url
            else:
                key = title
            
            if key and key not in unique_articles:
                unique_articles[key] = article
        
        # Sort by date (newest first)
        sorted_articles = sorted(
            unique_articles.values(),
            key=lambda x: x['date'],
            reverse=True
        )
        
        return sorted_articles[:max_results]
    
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
        
        # Determine if this is historical or recent data
        # Recent = within last 60 days (good Google News coverage)
        # Historical = older than 60 days (use archive sources)
        now = datetime.now()
        if hasattr(end_date, 'date'):
            end_date_obj = end_date
        else:
            end_date_obj = datetime.strptime(str(end_date), '%Y-%m-%d')
        
        days_ago = (now - end_date_obj).days
        is_historical = days_ago > 60
        
        logger.debug(f"Analysis period: {days_ago} days ago - Strategy: {'HISTORICAL' if is_historical else 'RECENT'}")
        
        # Aggregate articles from multiple sources based on date range
        all_articles = []
        
        if is_historical:
            # Use archival sources for historical data
            logger.debug("Using historical archives (IMF, World Bank)")
            hist_articles = self.get_historical_news(country_name, start_date, end_date, max_results)
            all_articles.extend(hist_articles)
        
        # Always try recent sources (may have some overlap for edge cases)
        # Source 1: Enhanced RSS feeds (recent data)
        rss_articles = self._fetch_from_enhanced_rss(country_name, start_date, end_date, NEWS_MAX_ARTICLES_PER_FETCH)
        all_articles.extend(rss_articles)
        
        # Source 2: Central bank press releases
        cb_articles = self._fetch_from_central_bank(country_code, start_date, end_date, 50)
        all_articles.extend(cb_articles)
        
        # Source 3: NewsData.io API (if available and working)
        newsdata_articles = self._fetch_from_newsdata_io(country_name, start_date, end_date, NEWS_MAX_ARTICLES_PER_FETCH)
        all_articles.extend(newsdata_articles)
        
        # Deduplicate by URL (but keep CSV entries even if no URL)
        unique_articles = {}
        for article in all_articles:
            url = article.get('url', '')
            title = article.get('title', '')
            source = article.get('source', '')
            
            # For CSV events, use title + source as key (no URL)
            if url == '#' or not url:
                key = f"{title}|{source}"
            else:
                key = url
            
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
