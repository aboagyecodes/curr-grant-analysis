#!/usr/bin/env python3
"""Test the full enhanced news pipeline with relevance scoring"""

from datetime import datetime, timedelta
from src.data_loaders.external_data import ExternalDataFetcher
import json

def test_news_pipeline():
    """Test the complete news aggregation and filtering pipeline"""
    
    fetcher = ExternalDataFetcher()
    
    # Test date range: last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"\n{'='*70}")
    print(f"Testing Enhanced News Pipeline with Relevance Filtering")
    print(f"Date Range: {start_date.date()} to {end_date.date()}")
    print(f"{'='*70}\n")
    
    try:
        # Test with Ghana (pilot country)
        country = 'Ghana'
        print(f"Testing with {country}...")
        
        # Call the main method that orchestrates the pipeline
        headlines = fetcher.get_news_headlines(country, start_date, end_date)
        
        print(f"✓ Pipeline completed successfully!")
        print(f"✓ Retrieved {len(headlines)} articles for {country}")
        
        if headlines:
            print(f"\n{'='*70}")
            print("Top 10 Articles (by relevance score):")
            print(f"{'='*70}\n")
            
            for i, article in enumerate(headlines[:10], 1):
                score = article.get('relevance_score', 'N/A')
                title = article.get('title', 'N/A')[:70]
                source = article.get('source', 'N/A')
                date = article.get('date', 'N/A')
                
                print(f"{i}. [{score}⭐] {title}")
                print(f"   Source: {source} | Date: {date}")
                print()
            
            # Statistics
            print(f"{'='*70}")
            print("Pipeline Statistics:")
            print(f"{'='*70}")
            sources = {}
            score_distribution = {}
            
            for article in headlines:
                source = article.get('source', 'Unknown')
                sources[source] = sources.get(source, 0) + 1
                
                score = article.get('relevance_score', 0)
                score_distribution[score] = score_distribution.get(score, 0) + 1
            
            print(f"\nArticles by source:")
            for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {source}: {count} articles")
            
            print(f"\nRelevance score distribution:")
            for score in sorted(score_distribution.keys(), reverse=True):
                print(f"  {score}⭐: {score_distribution[score]} articles")
        
        print(f"\n{'='*70}")
        print("✓ News pipeline test completed successfully!")
        print(f"{'='*70}\n")
        
        return len(headlines) > 0
        
    except Exception as e:
        print(f"✗ Error during pipeline test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_news_pipeline()
    exit(0 if success else 1)
