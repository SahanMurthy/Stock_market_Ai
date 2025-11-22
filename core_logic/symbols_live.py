# symbols_live.py

import requests
import pandas as pd
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class SymbolsLive:
    """
    Utility for fetching and searching live stock/currency/crypto symbols.
    """

    NSE_SYMBOLS_URL = "https://www1.nseindia.com/content/equities/EQUITY_L.csv"

    def fetch_nse_symbols(self) -> pd.DataFrame:
        """
        Fetch the full list of NSE symbols (live pull from the official source).
        Returns:
            Dataframe with columns: 'SYMBOL', 'NAME OF COMPANY', 'ISIN NUMBER', ...
        """
        try:
            response = requests.get(self.NSE_SYMBOLS_URL, timeout=15)
            response.raise_for_status()
            df = pd.read_csv(pd.compat.StringIO(response.text))
            return df
        except Exception as e:
            logger.warning(f"Unable to fetch NSE symbols: {e}")
            return pd.DataFrame()

    def search_nse_symbols(self, query: str) -> List[str]:
        """
        Search symbols or names in NSE listings.
        Returns:
            List of matching symbol strings.
        """
        df = self.fetch_nse_symbols()
        if df.empty:
            return []
        # Case-insensitive search
        mask = df['SYMBOL'].str.contains(query, case=False, na=False) | \
               df['NAME OF COMPANY'].str.contains(query, case=False, na=False)
        return df.loc[mask, 'SYMBOL'].tolist()

    # Optionally add similar methods for BSE, Currency, Crypto, etc.
    def get_all_nse_symbols(self) -> List[str]:
        """
        Get all available NSE stock symbols.
        Returns:
            List of symbol strings (e.g., ['RELIANCE', 'TCS', ...])
        """
        df = self.fetch_nse_symbols()
        if df.empty:
            logger.warning("No NSE symbols fetched")
            return []
        return df['SYMBOL'].tolist()

    def get_nifty_50_symbols(self) -> List[str]:
        """
        Get NIFTY 50 index constituents (as of real-time data).
        Note: This requires a live source or hardcoded fallback.
        """
        # Placeholder: In production, scrape from NSE or use an API
        # For now, returning empty to enforce dynamic fetch
        return []

    def get_nifty_next_50_symbols(self) -> List[str]:
        """
        Get NIFTY Next 50 index constituents (real-time).
        """
        # Placeholder: fetch from official NSE source
        return []

    def search_crypto_symbols(self, query: str) -> List[str]:
        """
        Search cryptocurrency symbols (e.g., via CoinGecko or similar).
        """
        # Placeholder: integrate with CoinGecko, Binance, etc.
        return []

    def search_currency_pairs(self, query: str) -> List[str]:
        """
        Search forex currency pairs (e.g., via OANDA or similar).
        """
        # Placeholder: integrate with forex data provider
        return []

# Standalone usage example
if __name__ == "__main__":
    sl = SymbolsLive()
    query = input("Search NSE symbols (name or symbol): ")
    results = sl.search_nse_symbols(query)
    print(f"Found {len(results)} symbols:")
    for symbol in results[:10]:
        print(f"  - {symbol}")
