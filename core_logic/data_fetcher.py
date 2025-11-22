# Data Fetcher Module - FIXED

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from typing import Optional, Dict, List
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

# Suppress yfinance warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher:
    """Enhanced stock data fetcher with caching and error handling"""

    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes for historical data
        self.realtime_cache_timeout = 60  # 1 minute for real-time data
        self.failed_symbols = set()  # Track failed symbols to avoid retry spam
        self.retry_cooldown = {}  # Cooldown for failed symbols

    def _is_cache_valid(self, cache_key: str, timeout: int = None) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        timeout = timeout or self.cache_timeout
        cached_time, _ = self.cache[cache_key]
        return (time.time() - cached_time) < timeout

    def _get_cached_data(self, cache_key: str, timeout: int = None) -> Optional[pd.DataFrame]:
        """Get cached data if valid"""
        if self._is_cache_valid(cache_key, timeout):
            _, data = self.cache[cache_key]
            return data.copy() if data is not None else None
        return None

    def _cache_data(self, cache_key: str, data: Optional[pd.DataFrame]):
        """Cache data with timestamp"""
        self.cache[cache_key] = (time.time(), data.copy() if data is not None else None)

    def _should_retry_symbol(self, symbol: str) -> bool:
        """Check if we should retry a previously failed symbol"""
        if symbol not in self.failed_symbols:
            return True
        # Allow retry after 1 hour cooldown
        if symbol in self.retry_cooldown:
            return (time.time() - self.retry_cooldown[symbol]) > 3600
        return False

    def _mark_symbol_failed(self, symbol: str):
        """Mark symbol as failed and set cooldown"""
        self.failed_symbols.add(symbol)
        self.retry_cooldown[symbol] = time.time()

    def _mark_symbol_success(self, symbol: str):
        """Mark symbol as successful (remove from failed list)"""
        self.failed_symbols.discard(symbol)
        self.retry_cooldown.pop(symbol, None)

    def get_stock_data(self, symbol: str, period: str = "2y") -> Optional[pd.DataFrame]:
        """
        Fetch historical stock data with caching and error handling

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            period: Time period ('1y', '2y', '5y', etc.)
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        cache_key = f"{symbol}_{period}_historical"

        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            logger.debug(f"Using cached historical data for {symbol}")
            return cached_data

        # Check if symbol should be retried
        if not self._should_retry_symbol(symbol):
            logger.debug(f"Skipping {symbol} due to recent failure")
            return None

        try:
            logger.info(f"Fetching historical data for {symbol} ({period})")

            # Create ticker object
            ticker = yf.Ticker(symbol)

            # Fetch historical data - REMOVED progress=False
            stock_data = ticker.history(
                period=period,
                auto_adjust=True,
                timeout=10
            )

            # Validate data
            if stock_data is None or stock_data.empty:
                logger.warning(f"No data returned for {symbol}")
                self._mark_symbol_failed(symbol)
                self._cache_data(cache_key, None)
                return None

            # Check minimum data requirements
            if len(stock_data) < 50:  # Need at least 50 days for meaningful analysis
                logger.warning(f"Insufficient data for {symbol}: {len(stock_data)} rows")
                self._mark_symbol_failed(symbol)
                self._cache_data(cache_key, None)
                return None

            # Validate required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in stock_data.columns]
            if missing_columns:
                logger.error(f"Missing columns for {symbol}: {missing_columns}")
                self._mark_symbol_failed(symbol)
                self._cache_data(cache_key, None)
                return None

            # Data quality checks
            if stock_data['Close'].isnull().all():
                logger.warning(f"All Close prices are null for {symbol}")
                self._mark_symbol_failed(symbol)
                self._cache_data(cache_key, None)
                return None

            # Remove any rows with all NaN values
            stock_data = stock_data.dropna(how='all')

            # Forward fill any remaining NaN values - FIXED deprecated method
            stock_data = stock_data.ffill()  # Changed from fillna(method='ffill')

            # Cache the result
            self._cache_data(cache_key, stock_data)
            self._mark_symbol_success(symbol)

            return stock_data

        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            self._mark_symbol_failed(symbol)
            self._cache_data(cache_key, None)
            return None

    def get_realtime_price(self, symbol: str) -> Optional[float]:
        """
        Fetch the latest real-time price for a stock with short-term caching

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
        Returns:
            Latest market price or None if failed
        """
        cache_key = f"{symbol}_realtime"
        cached_price = self._get_cached_data(cache_key, self.realtime_cache_timeout)

        if cached_price is not None:
            logger.debug(f"Using cached real-time price for {symbol}")
            return cached_price

        if not self._should_retry_symbol(symbol):
            return None

        try:
            logger.info(f"Fetching real-time price for {symbol}")
            ticker = yf.Ticker(symbol)
            price = ticker.info.get("regularMarketPrice")

            if price is not None:
                self._cache_data(cache_key, price)
                self._mark_symbol_success(symbol)
                return price

        except Exception as e:
            logger.error(f"Error fetching real-time price for {symbol}: {e}")
            self._mark_symbol_failed(symbol)
            self._cache_data(cache_key, None)

        return None

    def get_bulk_stock_data(self, symbols: List[str], period: str = "2y", threads: int = 8) -> Dict[
        str, Optional[pd.DataFrame]]:
        """
        Fetch historical data for many symbols in parallel

        Args:
            symbols: List of stock symbols
            period: Time period
            threads: Number of concurrent fetch threads
        Returns:
            Dict {symbol: DataFrame or None}
        """
        results = {}
        logger.info(f"Bulk fetching data for {len(symbols)} symbols...")

        with ThreadPoolExecutor(max_workers=threads) as executor:
            future_to_symbol = {
                executor.submit(self.get_stock_data, symbol, period): symbol
                for symbol in symbols
            }

            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    data = future.result()
                except Exception as e:
                    logger.error(f"Concurrent fetch error for {symbol}: {e}")
                    data = None
                results[symbol] = data

        logger.info("Completed bulk fetch.")
        return results

    def get_active_symbols(self, exchange: str = "NSE") -> List[str]:
        """
        Fetch symbol list from a live official or 3rd-party API.

        Args:
            exchange: Only 'NSE', 'BSE', etc.
        Returns:
            List of strings (symbols)
        """
        # Placeholder - implement with real API
        return []

    def search_symbols(self, query: str) -> List[str]:
        """
        Search for available stock symbols in real-time.

        Args:
            query: User query (by symbol or company name)
        Returns:
            Matching list of symbols
        """
        # Placeholder - implement with real search API
        return []


# Standalone test
if __name__ == "__main__":
    fetcher = DataFetcher()
    symbol = input("Enter a stock symbol: ")
    data = fetcher.get_stock_data(symbol, "1y")
    print(data.tail() if data is not None else "No data found")
