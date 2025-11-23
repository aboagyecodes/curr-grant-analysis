"""
External Data Integration Module

Fetches data from external sources:
- IMF Press Releases
- Central Bank Policy Rates (via FRED)
- News Headlines (via RSS feeds)
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import os
import json
import sys
import feedparser
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import CACHE_DIR, PILOT_CURRENCIES, DEFAULT_NEWSDATA_KEY


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
    
    def get_news_headlines(self, country_name, start_date, end_date, max_results=3, check_cache_only=False):
        """
        Get news headlines with historical coverage
        
        Strategy:
        1. Check cache first
        2. Try NewsData.io API (historical coverage: 7+ years)
        3. Fall back to RSS if NewsData.io fails (recent news only)
        4. Cache successful results
        
        Args:
            country_name: Full country name
            start_date: Start date
            end_date: End date
            max_results: Max number of results (default 3)
            check_cache_only: If True, only return cached results (no API calls)
        
        Returns:
            list: List of dicts with {date, title, source, url}
        """
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
        cache_key = f"news_{country_name.replace(' ', '_')}_{start_str}_{end_str}.json"
        cache_file = os.path.join(CACHE_DIR, cache_key)
        
        # Check cache first
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    # print(f"DEBUG: Using cached news for {country_name} ({len(cached_data)} articles)")
                    return cached_data[:max_results]
            except Exception as e:
                print(f"Warning: Could not read cache file {cache_file}: {e}")
        
        # If cache only mode, return empty list if no cache found
        if check_cache_only:
            return []
        
        #  Try NewsData.io first (historical coverage)
        headlines = self._fetch_from_newsdata_io(country_name, start_date, end_date, max_results)
        
        # Fall back to RSS if NewsData.io returns no results
        if not headlines:
            headlines = self._fetch_from_rss(country_name, start_date, end_date, max_results)
        
        # Cache the results
        if headlines:
            try:
                with open(cache_file, 'w') as f:
                    json.dump(headlines, f, indent=2)
            except Exception:
                # Silently fail on cache write
                pass
        
        return headlines
    
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
