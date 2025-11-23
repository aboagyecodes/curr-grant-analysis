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

