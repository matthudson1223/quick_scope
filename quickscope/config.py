"""Configuration module for QuickScope.

Loads API keys and settings from environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Configuration class for API keys and application settings."""

    # API Keys (optional - yfinance works without them)
    ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY', '')
    FINNHUB_KEY = os.getenv('FINNHUB_KEY', '')
    NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')
    FRED_API_KEY = os.getenv('FRED_API_KEY', '')

    # Cache settings
    CACHE_DIR = Path(__file__).parent.parent / '.cache'
    CACHE_DB = CACHE_DIR / 'quickscope.duckdb'

    # Cache expiration times (in seconds)
    PRICE_CACHE_EXPIRY = 15 * 60  # 15 minutes
    FUNDAMENTAL_CACHE_EXPIRY = 24 * 60 * 60  # 24 hours
    NEWS_CACHE_EXPIRY = 60 * 60  # 1 hour
    OPTIONS_CACHE_EXPIRY = 15 * 60  # 15 minutes

    # Application settings
    DEFAULT_RISK_PROFILE = 'moderate'
    DEFAULT_STRATEGY_TYPE = 'long_only'

    # Financial constants
    RISK_FREE_RATE = 0.045  # 4.5% (approximate current 10-year Treasury)
    MARKET_RISK_PREMIUM = 0.08  # 8% historical average

    @classmethod
    def ensure_cache_dir(cls):
        """Ensure the cache directory exists."""
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def has_api_key(cls, key_name: str) -> bool:
        """Check if a specific API key is configured."""
        return bool(getattr(cls, key_name, ''))


# Ensure cache directory exists on import
Config.ensure_cache_dir()
