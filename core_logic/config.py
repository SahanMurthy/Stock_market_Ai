import os
from dotenv import load_dotenv
import logging
from typing import Dict, List, Optional

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== API KEYS ====================

# Primary APIs
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "")

# Secondary/Alternative APIs
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")


# ==================== API DETECTION ====================

def detect_available_apis() -> Dict[str, bool]:
    """Detect which APIs are configured and available."""
    return {
        'gemini': bool(GEMINI_API_KEY),
        'alpha_vantage': bool(ALPHA_VANTAGE_API_KEY),
        'finnhub': bool(FINNHUB_API_KEY),
        'polygon': bool(POLYGON_API_KEY),
        'twelve_data': bool(TWELVE_DATA_API_KEY),
        'newsapi': bool(NEWSAPI_KEY),
        'twitter': bool(TWITTER_BEARER_TOKEN),
        'rapidapi': bool(RAPIDAPI_KEY),
    }


AVAILABLE_APIS = detect_available_apis()

# Log available APIs at startup
available_names = [name for name, available in AVAILABLE_APIS.items() if available]
if available_names:
    logger.info(f"✅ Available APIs: {', '.join(available_names)}")
else:
    logger.warning("⚠️  No API keys configured - limited functionality")

# ==================== FEATURE FLAGS ====================

# Enable features based on available APIs
ENABLE_AI_RECOMMENDATIONS = AVAILABLE_APIS['gemini']
ENABLE_ALTERNATIVE_DATA = len(available_names) > 1
ENABLE_NEWS_SENTIMENT = AVAILABLE_APIS['newsapi'] or AVAILABLE_APIS['twitter']
ENABLE_REAL_TIME_DATA = any([
    AVAILABLE_APIS['alpha_vantage'],
    AVAILABLE_APIS['finnhub'],
    AVAILABLE_APIS['polygon'],
    AVAILABLE_APIS['twelve_data']
])

# Feature toggle from environment
ENABLE_CACHING = os.getenv("ENABLE_CACHING", "True").lower() == "true"
ENABLE_PARALLEL_FETCH = os.getenv("ENABLE_PARALLEL_FETCH", "True").lower() == "true"

# ==================== DATABASE SETTINGS ====================

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///stock_data.db")
REDIS_URL = os.getenv("REDIS_URL", "")  # For caching
USE_REDIS = bool(REDIS_URL)

# ==================== CACHE SETTINGS ====================

CACHE_TIMEOUT = int(os.getenv("CACHE_TIMEOUT", "300"))  # 5 minutes for historical
REALTIME_CACHE_TIMEOUT = int(os.getenv("REALTIME_CACHE_TIMEOUT", "60"))  # 1 minute for real-time
SYMBOL_CACHE_TIMEOUT = int(os.getenv("SYMBOL_CACHE_TIMEOUT", "86400"))  # 24 hours for symbol lists

# ==================== DATA FETCH SETTINGS ====================

DEFAULT_PERIOD = os.getenv("DEFAULT_PERIOD", "2y")
MAX_CONCURRENT_FETCHES = int(os.getenv("MAX_CONCURRENT_FETCHES", "8"))
FETCH_TIMEOUT = int(os.getenv("FETCH_TIMEOUT", "15"))  # seconds
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# ==================== RISK MANAGEMENT SETTINGS ====================

# These are general risk parameters, NOT return rate assumptions
DEFAULT_RISK_PER_TRADE = float(os.getenv("DEFAULT_RISK_PER_TRADE", "1.0"))  # 1% risk per trade
DEFAULT_STOP_LOSS = float(os.getenv("DEFAULT_STOP_LOSS", "5.0"))  # 5% stop loss
MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", "20.0"))  # Max 20% in one position

# ==================== SIP/INVESTMENT SETTINGS ====================

# REMOVED ALL DEFAULT RETURN RATES
# Users MUST provide their own expected return rates
# NO DEFAULT_ANNUAL_RETURN
# NO DEFAULT_INFLATION_RATE - users must specify inflation assumptions


# ==================== TECHNICAL INDICATOR SETTINGS ====================

RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))
RSI_OVERBOUGHT = int(os.getenv("RSI_OVERBOUGHT", "70"))
RSI_OVERSOLD = int(os.getenv("RSI_OVERSOLD", "30"))

MACD_FAST = int(os.getenv("MACD_FAST", "12"))
MACD_SLOW = int(os.getenv("MACD_SLOW", "26"))
MACD_SIGNAL = int(os.getenv("MACD_SIGNAL", "9"))

BOLLINGER_PERIOD = int(os.getenv("BOLLINGER_PERIOD", "20"))
BOLLINGER_STD = float(os.getenv("BOLLINGER_STD", "2.0"))

SMA_PERIODS = [int(x) for x in os.getenv("SMA_PERIODS", "20,50,200").split(",")]
EMA_PERIODS = [int(x) for x in os.getenv("EMA_PERIODS", "12,26").split(",")]

# ==================== MARKET SETTINGS ====================

# Market hours (IST - Indian Standard Time)
MARKET_OPEN_HOUR = int(os.getenv("MARKET_OPEN_HOUR", "9"))  # 9:15 AM
MARKET_OPEN_MINUTE = int(os.getenv("MARKET_OPEN_MINUTE", "15"))
MARKET_CLOSE_HOUR = int(os.getenv("MARKET_CLOSE_HOUR", "15"))  # 3:30 PM
MARKET_CLOSE_MINUTE = int(os.getenv("MARKET_CLOSE_MINUTE", "30"))

# Trading days
TRADING_DAYS_PER_YEAR = int(os.getenv("TRADING_DAYS_PER_YEAR", "252"))

# ==================== SYMBOL/DATA SOURCE URLs ====================

NSE_SYMBOLS_URL = os.getenv(
    "NSE_SYMBOLS_URL",
    "https://www1.nseindia.com/content/equities/EQUITY_L.csv"
)
BSE_SYMBOLS_URL = os.getenv("BSE_SYMBOLS_URL", "")
CRYPTO_SYMBOLS_URL = os.getenv("CRYPTO_SYMBOLS_URL", "")

# ==================== AI/ML SETTINGS ====================

AI_MODEL_PATH = os.getenv("AI_MODEL_PATH", "models/stock_predictor.pkl")
AI_CONFIDENCE_THRESHOLD = float(os.getenv("AI_CONFIDENCE_THRESHOLD", "0.75"))
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "2048"))
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))

# ==================== LOGGING SETTINGS ====================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "stock_market.log")
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# ==================== DJANGO INTEGRATION ====================

# Django-specific settings (if config is shared)
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")


# ==================== UTILITY FUNCTIONS ====================

def get_primary_api() -> Optional[str]:
    """
    Get the primary API to use based on priority and availability.
    Priority: Gemini > Alpha Vantage > Finnhub > Polygon > Twelve Data
    """
    priority_order = ['gemini', 'alpha_vantage', 'finnhub', 'polygon', 'twelve_data']
    for api in priority_order:
        if AVAILABLE_APIS.get(api):
            return api
    return None


def get_data_api() -> Optional[str]:
    """Get the best available API for stock data."""
    data_apis = ['alpha_vantage', 'finnhub', 'polygon', 'twelve_data']
    for api in data_apis:
        if AVAILABLE_APIS.get(api):
            return api
    return None


def get_api_key(api_name: str) -> Optional[str]:
    """Get API key by name."""
    api_keys = {
        'gemini': GEMINI_API_KEY,
        'alpha_vantage': ALPHA_VANTAGE_API_KEY,
        'finnhub': FINNHUB_API_KEY,
        'polygon': POLYGON_API_KEY,
        'twelve_data': TWELVE_DATA_API_KEY,
        'newsapi': NEWSAPI_KEY,
        'twitter': TWITTER_BEARER_TOKEN,
        'rapidapi': RAPIDAPI_KEY,
    }
    return api_keys.get(api_name, "")


def validate_config() -> Dict[str, List[str]]:
    """
    Validate configuration and return warnings/errors.
    Returns dict with 'errors' and 'warnings' lists.
    """
    errors = []
    warnings = []

    # Check if at least one API is configured
    if not any(AVAILABLE_APIS.values()):
        errors.append("No API keys configured - system will have limited functionality")

    # Warn if no AI API available
    if not ENABLE_AI_RECOMMENDATIONS:
        warnings.append("Gemini API not configured - AI recommendations disabled")

    # Warn if no real-time data source
    if not ENABLE_REAL_TIME_DATA:
        warnings.append("No real-time data API configured - using yfinance only")

    # Check cache settings
    if CACHE_TIMEOUT < 60:
        warnings.append("Cache timeout very low - may cause excessive API calls")

    return {'errors': errors, 'warnings': warnings}


# ==================== STARTUP VALIDATION ====================

# Validate configuration on import
validation = validate_config()
if validation['errors']:
    for error in validation['errors']:
        logger.error(f"❌ CONFIG ERROR: {error}")
if validation['warnings']:
    for warning in validation['warnings']:
        logger.warning(f"⚠️  CONFIG WARNING: {warning}")

# ==================== EXAMPLE .env FILE ====================

ENV_TEMPLATE = """
# API Keys
GEMINI_API_KEY=your_gemini_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FINNHUB_API_KEY=your_finnhub_key

# Cache Settings
CACHE_TIMEOUT=300
REALTIME_CACHE_TIMEOUT=60

# Feature Flags
ENABLE_CACHING=True
ENABLE_PARALLEL_FETCH=True

# Logging
LOG_LEVEL=INFO
LOG_FILE=stock_market.log

# Django (if using)
DEBUG=False
SECRET_KEY=change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1
"""
