"""
Configuration settings for IMF/World Bank Currency Impact Analysis App
"""

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

import os

# Pilot Currencies
PILOT_CURRENCIES = {
    'GHS': {'name': 'Ghanaian Cedi', 'country': 'Ghana', 'commodities': ['Gold', 'Cocoa']},
    'ARS': {'name': 'Argentine Peso', 'country': 'Argentina', 'commodities': ['Soybeans', 'Corn']},
    'TRY': {'name': 'Turkish Lira', 'country': 'Turkey', 'commodities': ['Steel', 'Textiles']},
    'EGP': {'name': 'Egyptian Pound', 'country': 'Egypt', 'commodities': ['Natural Gas', 'Petroleum']},
    'PKR': {'name': 'Pakistani Rupee', 'country': 'Pakistan', 'commodities': ['Textiles', 'Rice']},
    'LKR': {'name': 'Sri Lankan Rupee', 'country': 'Sri Lanka', 'commodities': ['Tea', 'Textiles']},
    'LBP': {'name': 'Lebanese Pound', 'country': 'Lebanon', 'commodities': ['Gold', 'Diamonds']},
    'COP': {'name': 'Colombian Peso', 'country': 'Colombia', 'commodities': ['Oil', 'Coffee']},
}

# Currency symbols for Yahoo Finance
CURRENCY_SYMBOLS = {
    'GHS': 'USDGHS=X',
    'ARS': 'USDARS=X',
    'TRY': 'USDTRY=X',
    'EGP': 'USDEGP=X',
    'PKR': 'USDPKR=X',
    'LKR': 'USDLKR=X',
    'LBP': 'USDLBP=X',
    'COP': 'USDCOP=X',
}

# Commodity symbols for Yahoo Finance
COMMODITY_SYMBOLS = {
    'Gold': 'GC=F',
    'Cocoa': 'CC=F',
    'Oil': 'CL=F',
    'Soybeans': 'ZS=F',
    'Corn': 'ZC=F',
    'Coffee': 'KC=F',
    'Natural Gas': 'NG=F',
    'Petroleum': 'CL=F',  # Same as Oil
    'Steel': 'HG=F',  # Copper as proxy
    'Textiles': None,  # No single symbol
    'Tea': None,  # No single symbol
    'Rice': 'ZR=F',
    'Diamonds': None,  # No single symbol
}

# Color Palette
COLORS = {
    'currency_line': '#22333B',      # Deep Teal
    'commodity_1': '#7FB3D5',        # Soft Blue
    'commodity_2': '#F6C6EA',        # Muted Pink
    'grant_marker': '#FF9900',       # Vibrant Orange
    'anomaly_highlight': '#E74C3C',  # Soft Red
    'card_background': '#F8F8F8',    # Light Grey
    'dashboard_background': '#FFFFFF', # White
}

# Anomaly Detection Thresholds
ANOMALY_THRESHOLD_PERCENT = 10.0  # 10% change
ANOMALY_WINDOW_DAYS = 30          # Within 30 days
GRANT_CORRELATION_DAYS = 7        # ±7 days for grant correlation
COMMODITY_CORRELATION_PERCENT = 5.0  # 5% commodity movement

# Analysis Windows (in weeks)
ANALYSIS_WINDOWS = {
    'short_term': {'pre': 4, 'post': 4},      # 1 month
    'medium_term': {'pre': 12, 'post': 12},   # 3 months
    'long_term': {'pre': 26, 'post': 26},     # 6 months
}

# Data Paths
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
GRANTS_DIR = os.path.join(DATA_DIR, 'grants')
IMF_DIR = os.path.join(GRANTS_DIR, 'imf')
WORLDBANK_DIR = os.path.join(GRANTS_DIR, 'worldbank')
STANDARDIZED_DIR = os.path.join(GRANTS_DIR, 'standardized')
FX_DIR = os.path.join(DATA_DIR, 'fx_rates')
COMMODITIES_DIR = os.path.join(DATA_DIR, 'commodities')
CACHE_DIR = os.path.join(DATA_DIR, 'cache')

# Standardized Grant Schema
GRANT_SCHEMA = [
    'country_code',      # ISO 3-letter code
    'country_name',      # Full country name
    'disbursement_date', # YYYY-MM-DD format
    'amount_usd',        # Grant amount in USD
    'grant_type',        # Type/Purpose of grant
    'source',            # IMF or World Bank
    'program_name',      # Name of the program
]

# Country Code Mapping (for standardization)
COUNTRY_CODE_MAP = {
    'Ghana': 'GHA',
    'Argentina': 'ARG',
    'Turkey': 'TUR',
    'Egypt': 'EGY',
    'Pakistan': 'PAK',
    'Sri Lanka': 'LKA',
    'Lebanon': 'LBN',
    'Colombia': 'COL',
}

# Impact Scoring Weights
IMPACT_SCORE_WEIGHTS = {
    'commodity_stability': 0.3,   # 30% weight
    'trend_deviation': 0.5,       # 50% weight
    'magnitude': 0.2,             # 20% weight
}

# Default API Keys (loaded from environment variables)
# Set these in your .env file - see .env.example for template
DEFAULT_NEWSAPI_KEY = os.getenv('NEWSAPI_KEY', '')
DEFAULT_FRED_KEY = os.getenv('FRED_API_KEY', '')
DEFAULT_NEWSDATA_KEY = os.getenv('NEWSDATA_API_KEY', '')

# Free RSS Feeds for Financial News (Google News - most reliable)
# Note: Google News feeds are dynamic and work best with specific search queries
RSS_FEEDS = {
    'Google News': 'https://news.google.com/rss',
    'BBC World': 'https://www.bbc.co.uk/news/world/?ns_mchannel=social&ns_source=twitter&ns_campaign=bbc_news&ns_linkname=news_central',
}

# Central Bank Press Release URLs (scraped, no API required)
CENTRAL_BANK_URLS = {
    'GHS': {
        'name': 'Bank of Ghana',
        'press_url': 'https://www.bog.org.gh/news-and-media/press-releases',
        'selector': '.press-release, .news-item'
    },
    'TRY': {
        'name': 'Central Bank of Turkey (TCMB)',
        'press_url': 'https://www.tcmb.gov.tr/wps/wcm/connect/EN/TCMB+EN/Main+Page',
        'selector': '.news-item, .press-release'
    },
    'EGP': {
        'name': 'Central Bank of Egypt',
        'press_url': 'https://www.cbe.org.eg/en/pages/default.aspx',
        'selector': '.news, .press-release'
    },
    'PKR': {
        'name': 'State Bank of Pakistan',
        'press_url': 'https://www.sbp.org.pk/press/index.html',
        'selector': '.press, .announcement'
    },
    'LKR': {
        'name': 'Central Bank of Sri Lanka',
        'press_url': 'https://www.cbsl.gov.lk/en/news',
        'selector': '.news-item, .press-release'
    },
    'LBP': {
        'name': 'Banque du Liban',
        'press_url': 'https://www.bdl.gov.lb/en/news',
        'selector': '.news, .press-release'
    },
    'ARS': {
        'name': 'Central Bank of Argentina',
        'press_url': 'https://www.bcra.gob.ar/es/noticias/',
        'selector': '.noticia, .news-item'
    },
    'COP': {
        'name': 'Banco de la República de Colombia',
        'press_url': 'https://www.banrep.gov.co/en/news',
        'selector': '.news-item, .press-release'
    }
}

# News Filtering Configuration
NEWS_KEYWORDS = {
    'CRITICAL': [
        'currency crisis', 'devaluation', 'monetary policy', 'exchange rate',
        'central bank rate hike', 'currency peg', 'currency board',
        'foreign reserves', 'currency intervention'
    ],
    'HIGH': [
        'IMF', 'World Bank', 'grant', 'inflation', 'interest rate',
        'central bank', 'policy rate', 'reserve requirement', 'quantitative easing'
    ],
    'MEDIUM': [
        'economy', 'finance', 'trade', 'investment', 'fiscal policy',
        'recession', 'growth', 'GDP', 'debt', 'sanctions'
    ]
}

# Country-Specific Keywords for Better Filtering
COUNTRY_KEYWORDS = {
    'GHS': ['cedis', 'gold', 'cocoa', 'Ghana', 'BoG'],
    'ARS': ['peso', 'soy', 'Argentina', 'BCRA', 'inflation'],
    'TRY': ['lira', 'Türkiye', 'Turkey', 'TCMB', 'inflation'],
    'EGP': ['pound', 'Egypt', 'CBE', 'Suez'],
    'PKR': ['rupee', 'Pakistan', 'SBP', 'remittances'],
    'LKR': ['rupee', 'Sri Lanka', 'CBSL', 'tea', 'tourism'],
    'LBP': ['pound', 'Lebanon', 'BDL', 'banking'],
    'COP': ['peso', 'Colombia', 'coffee', 'oil', 'Banrep']
}

# News Caching Configuration
NEWS_CACHE_VALIDITY_HOURS = 12
NEWS_MAX_ARTICLES_PER_FETCH = 100
NEWS_MAX_ARTICLES_TO_DISPLAY = 20

