#!/usr/bin/env python3
"""Debug RSS feed fetching with improved headers"""

import feedparser
import requests
from config.settings import RSS_FEEDS

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

print("\n" + "="*60)
print("Debugging RSS Feed Connections (with headers)")
print("="*60 + "\n")

# Test each feed
for feed_name, feed_url in RSS_FEEDS.items():
    print(f"\n{feed_name}:")
    print(f"  URL: {feed_url}")
    
    try:
        # Fetch with headers
        response = requests.get(feed_url, headers=headers, timeout=10)
        print(f"  HTTP Status: {response.status_code}")
        
        # Parse the content
        feed = feedparser.parse(response.content)
        
        # Check connection
        print(f"  Entries found: {len(feed.entries)}")
        
        if feed.entries:
            print(f"  Feed title: {feed.feed.get('title', 'N/A')}")
            
            # Show first entry details
            entry = feed.entries[0]
            print(f"\n  First entry:")
            print(f"    Title: {entry.get('title', 'N/A')[:60]}")
            print(f"    Published: {entry.get('published', 'N/A')}")
            print(f"    Updated: {entry.get('updated', 'N/A')}")
            print(f"    Link: {entry.get('link', 'N/A')}")
            
            # Check dates
            pub_date_str = entry.get('published', entry.get('updated', ''))
            if pub_date_str:
                try:
                    from email.utils import parsedate_to_datetime
                    pub_date = parsedate_to_datetime(pub_date_str)
                    print(f"    Parsed date: {pub_date.date()}")
                except Exception as e:
                    print(f"    Date parse error: {e}")
    
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "="*60)
print("Debugging completed")
print("="*60 + "\n")
