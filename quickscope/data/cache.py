"""Cache module for QuickScope using DuckDB.

Implements caching to avoid redundant API calls with expiration logic.
"""

import logging
import pickle
import json
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from pathlib import Path
import duckdb

from ..config import Config

logger = logging.getLogger(__name__)


class Cache:
    """DuckDB-based cache for financial data."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the cache.

        Args:
            db_path: Path to DuckDB database file. If None, uses config default.
        """
        self.db_path = db_path or Config.CACHE_DB
        self._ensure_schema()

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get a DuckDB connection."""
        return duckdb.connect(str(self.db_path))

    def _ensure_schema(self):
        """Ensure the cache table exists."""
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key VARCHAR PRIMARY KEY,
                    value BLOB,
                    data_type VARCHAR,
                    timestamp TIMESTAMP,
                    expiry_seconds INTEGER
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def _make_key(self, ticker: str, data_type: str) -> str:
        """Create a cache key.

        Args:
            ticker: Stock ticker symbol
            data_type: Type of data (price, fundamental, options, news, etc.)

        Returns:
            Cache key string
        """
        return f"{ticker.upper()}:{data_type}"

    def _is_expired(self, timestamp: datetime, expiry_seconds: int) -> bool:
        """Check if a cache entry is expired.

        Args:
            timestamp: Time when data was cached
            expiry_seconds: Number of seconds until expiration

        Returns:
            True if expired, False otherwise
        """
        expiry_time = timestamp + timedelta(seconds=expiry_seconds)
        return datetime.now() > expiry_time

    def get(self, ticker: str, data_type: str) -> Optional[Any]:
        """Get data from cache if available and not expired.

        Args:
            ticker: Stock ticker symbol
            data_type: Type of data to retrieve

        Returns:
            Cached data if available and valid, None otherwise
        """
        key = self._make_key(ticker, data_type)
        conn = self._get_connection()

        try:
            result = conn.execute(
                "SELECT value, timestamp, expiry_seconds FROM cache WHERE key = ?",
                [key]
            ).fetchone()

            if result is None:
                logger.debug(f"Cache miss for {key}")
                return None

            value_blob, timestamp, expiry_seconds = result

            # Check if expired
            if self._is_expired(timestamp, expiry_seconds):
                logger.debug(f"Cache expired for {key}")
                self.delete(ticker, data_type)
                return None

            # Deserialize the data
            data = pickle.loads(value_blob)
            logger.debug(f"Cache hit for {key}")
            return data

        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            return None
        finally:
            conn.close()

    def set(
        self,
        ticker: str,
        data_type: str,
        data: Any,
        expiry_seconds: Optional[int] = None
    ):
        """Store data in cache.

        Args:
            ticker: Stock ticker symbol
            data_type: Type of data being stored
            data: Data to cache
            expiry_seconds: Seconds until expiration. If None, uses default based on data type.
        """
        key = self._make_key(ticker, data_type)

        # Determine expiry time if not provided
        if expiry_seconds is None:
            expiry_seconds = self._get_default_expiry(data_type)

        # Serialize the data
        try:
            value_blob = pickle.dumps(data)
        except Exception as e:
            logger.error(f"Error serializing data for cache: {e}")
            return

        conn = self._get_connection()
        try:
            # Use INSERT OR REPLACE to update if exists
            conn.execute("""
                INSERT OR REPLACE INTO cache (key, value, data_type, timestamp, expiry_seconds)
                VALUES (?, ?, ?, ?, ?)
            """, [key, value_blob, data_type, datetime.now(), expiry_seconds])
            conn.commit()
            logger.debug(f"Cached {key} with {expiry_seconds}s expiry")

        except Exception as e:
            logger.error(f"Error storing to cache: {e}")
        finally:
            conn.close()

    def delete(self, ticker: str, data_type: str):
        """Delete a cache entry.

        Args:
            ticker: Stock ticker symbol
            data_type: Type of data to delete
        """
        key = self._make_key(ticker, data_type)
        conn = self._get_connection()

        try:
            conn.execute("DELETE FROM cache WHERE key = ?", [key])
            conn.commit()
            logger.debug(f"Deleted cache entry: {key}")
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
        finally:
            conn.close()

    def clear_ticker(self, ticker: str):
        """Clear all cached data for a ticker.

        Args:
            ticker: Stock ticker symbol
        """
        conn = self._get_connection()
        try:
            pattern = f"{ticker.upper()}:%"
            conn.execute("DELETE FROM cache WHERE key LIKE ?", [pattern])
            conn.commit()
            logger.info(f"Cleared all cache for {ticker}")
        except Exception as e:
            logger.error(f"Error clearing ticker cache: {e}")
        finally:
            conn.close()

    def clear_all(self):
        """Clear all cached data."""
        conn = self._get_connection()
        try:
            conn.execute("DELETE FROM cache")
            conn.commit()
            logger.info("Cleared all cache")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
        finally:
            conn.close()

    def clear_expired(self):
        """Remove all expired cache entries."""
        conn = self._get_connection()
        try:
            result = conn.execute("""
                SELECT key, timestamp, expiry_seconds FROM cache
            """).fetchall()

            deleted_count = 0
            for key, timestamp, expiry_seconds in result:
                if self._is_expired(timestamp, expiry_seconds):
                    conn.execute("DELETE FROM cache WHERE key = ?", [key])
                    deleted_count += 1

            conn.commit()
            logger.info(f"Cleared {deleted_count} expired cache entries")

        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        conn = self._get_connection()
        try:
            total = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]

            # Count expired entries
            result = conn.execute(
                "SELECT timestamp, expiry_seconds FROM cache"
            ).fetchall()

            expired_count = sum(
                1 for timestamp, expiry_seconds in result
                if self._is_expired(timestamp, expiry_seconds)
            )

            # Get size of database file
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

            return {
                'total_entries': total,
                'expired_entries': expired_count,
                'valid_entries': total - expired_count,
                'db_size_bytes': db_size,
                'db_size_mb': round(db_size / (1024 * 1024), 2),
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
        finally:
            conn.close()

    def _get_default_expiry(self, data_type: str) -> int:
        """Get default expiry time for a data type.

        Args:
            data_type: Type of data

        Returns:
            Expiry time in seconds
        """
        expiry_map = {
            'price': Config.PRICE_CACHE_EXPIRY,
            'stock_data': Config.PRICE_CACHE_EXPIRY,
            'fundamental': Config.FUNDAMENTAL_CACHE_EXPIRY,
            'fundamentals': Config.FUNDAMENTAL_CACHE_EXPIRY,
            'options': Config.OPTIONS_CACHE_EXPIRY,
            'options_chain': Config.OPTIONS_CACHE_EXPIRY,
            'news': Config.NEWS_CACHE_EXPIRY,
            'analyst_ratings': Config.FUNDAMENTAL_CACHE_EXPIRY,
            'market_data': Config.PRICE_CACHE_EXPIRY,
        }

        return expiry_map.get(data_type, Config.FUNDAMENTAL_CACHE_EXPIRY)


class CachedDataFetcher:
    """Data fetcher with integrated caching."""

    def __init__(self, fetcher, cache: Optional[Cache] = None, use_cache: bool = True):
        """Initialize cached data fetcher.

        Args:
            fetcher: DataFetcher instance
            cache: Cache instance. If None, creates new cache.
            use_cache: Whether to use caching
        """
        self.fetcher = fetcher
        self.cache = cache or Cache()
        self.use_cache = use_cache

    def fetch_stock_price_history(self, ticker: str, **kwargs):
        """Fetch stock price history with caching."""
        if self.use_cache:
            cached = self.cache.get(ticker, 'stock_data')
            if cached is not None:
                return cached

        data = self.fetcher.fetch_stock_price_history(ticker, **kwargs)

        if self.use_cache:
            self.cache.set(ticker, 'stock_data', data)

        return data

    def fetch_fundamental_data(self, ticker: str):
        """Fetch fundamental data with caching."""
        if self.use_cache:
            cached = self.cache.get(ticker, 'fundamentals')
            if cached is not None:
                return cached

        data = self.fetcher.fetch_fundamental_data(ticker)

        if self.use_cache:
            self.cache.set(ticker, 'fundamentals', data)

        return data

    def fetch_options_chain(self, ticker: str):
        """Fetch options chain with caching."""
        if self.use_cache:
            cached = self.cache.get(ticker, 'options_chain')
            if cached is not None:
                return cached

        data = self.fetcher.fetch_options_chain(ticker)

        if self.use_cache:
            self.cache.set(ticker, 'options_chain', data)

        return data

    def fetch_analyst_recommendations(self, ticker: str):
        """Fetch analyst recommendations with caching."""
        if self.use_cache:
            cached = self.cache.get(ticker, 'analyst_ratings')
            if cached is not None:
                return cached

        data = self.fetcher.fetch_analyst_recommendations(ticker)

        if self.use_cache:
            self.cache.set(ticker, 'analyst_ratings', data)

        return data

    def fetch_news_headlines(self, ticker: str, **kwargs):
        """Fetch news headlines with caching."""
        if self.use_cache:
            cached = self.cache.get(ticker, 'news')
            if cached is not None:
                return cached

        data = self.fetcher.fetch_news_headlines(ticker, **kwargs)

        if self.use_cache:
            self.cache.set(ticker, 'news', data)

        return data

    def fetch_all_data(self, ticker: str):
        """Fetch all data with caching."""
        if self.use_cache:
            cached = self.cache.get(ticker, 'market_data')
            if cached is not None:
                return cached

        data = self.fetcher.fetch_all_data(ticker)

        if self.use_cache:
            self.cache.set(ticker, 'market_data', data)

        return data
