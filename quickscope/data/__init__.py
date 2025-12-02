"""Data layer for QuickScope."""

from .models import (
    StockData,
    Fundamentals,
    OptionContract,
    OptionsChain,
    NewsItem,
    AnalystRecommendation,
    AnalystRatings,
    MarketData,
)
from .cache import Cache

# Lazy import for DataFetcher to avoid yfinance dependency for testing
try:
    from .fetcher import DataFetcher
    _FETCHER_AVAILABLE = True
except ImportError:
    DataFetcher = None
    _FETCHER_AVAILABLE = False

__all__ = [
    'StockData',
    'Fundamentals',
    'OptionContract',
    'OptionsChain',
    'NewsItem',
    'AnalystRecommendation',
    'AnalystRatings',
    'MarketData',
    'DataFetcher',
    'Cache',
]
