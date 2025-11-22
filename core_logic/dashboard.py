# dashboard.py

import pandas as pd
import numpy as np
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from core_logic.data_fetcher import DataFetcher
from core_logic.risk_manager import RiskManager
from core_logic.sip_calculator import SIPCalculator

# Optionally, add more imports as needed from your core_logic modules

logger = logging.getLogger(__name__)

class Dashboard:
    def __init__(self):
        self.fetcher = DataFetcher()
        self.risk_manager = RiskManager()
        self.sip_calculator = SIPCalculator()

    def get_portfolio_performance(self, portfolio: List[Dict], start_date: str, end_date: str) -> Dict:
        """
        Calculates the total portfolio performance over a specified period.
        """
        performance = []
        for holding in portfolio:
            symbol = holding['symbol']
            qty = holding['quantity']
            data = self.fetcher.get_stock_data(symbol, period="2y")
            if data is not None and not data.empty:
                mask = (data.index >= pd.to_datetime(start_date)) & (data.index <= pd.to_datetime(end_date))
                period_data = data.loc[mask]
                if not period_data.empty:
                    initial_price = period_data.iloc[0]['Close']
                    final_price = period_data.iloc[-1]['Close']
                    gain = (final_price - initial_price) * qty
                    performance.append({
                        'symbol': symbol,
                        'gain': gain,
                        'return_pct': 100 * (final_price - initial_price) / initial_price
                    })
        total_gain = sum([p['gain'] for p in performance])
        avg_return = np.mean([p['return_pct'] for p in performance]) if performance else 0
        return {'total_gain': total_gain, 'avg_return': avg_return, 'details': performance}

    def get_market_overview(self, symbols: List[str]) -> List[Dict]:
        """
        Returns overview stats for a list of symbols (real time).
        """
        overview = []
        prices = self.fetcher.get_bulk_stock_data(symbols, period="5d")
        for symbol, df in prices.items():
            if df is not None and not df.empty:
                last = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else last
                overview.append({
                    'symbol': symbol,
                    'last_close': last['Close'],
                    'change_pct': 100 * (last['Close'] - prev['Close']) / prev['Close'] if prev['Close'] else 0,
                    'volume': last['Volume']
                })
        return overview

    # Add more methods from your own dashboard.py as appropriate
    # This is a template; insert your analytics, signal logic, etc.
    def get_trending_stocks(self, all_symbols: List[str], window_days: int = 5, top_n: int = 10) -> List[Dict]:
        """
        Find stocks with highest volatility or biggest price movers in recent window.
        """
        volatility_list = []
        prices = self.fetcher.get_bulk_stock_data(all_symbols, period=f"{window_days}d")
        for symbol, df in prices.items():
            if df is not None and not df.empty and len(df) >= window_days:
                price_changes = df['Close'].pct_change().dropna()
                volatility = price_changes.std()
                last = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else last
                price_chg_pct = 100 * (last['Close'] - prev['Close']) / prev['Close'] if prev['Close'] else 0
                volatility_list.append({
                    'symbol': symbol,
                    'volatility': volatility,
                    'price_chg_pct': price_chg_pct,
                    'latest_price': last['Close'],
                    'volume': last['Volume']
                })
        # Sort by volatility descending
        sorted_list = sorted(volatility_list, key=lambda d: d['volatility'], reverse=True)
        return sorted_list[:top_n]

    def build_dashboard_context(self, user_symbols: Optional[List[str]] = None) -> Dict:
        """
        Build the full dashboard data context for given user portfolio or symbol list.
        """
        if not user_symbols:
            raise ValueError("No symbols provided - all context must be built from real-time dynamic input.")
        market_overview = self.get_market_overview(user_symbols)
        trending = self.get_trending_stocks(user_symbols)
        # Optionally, add AI signals, risk scores, etc
        return {
            'market_overview': market_overview,
            'trending': trending,
            # …add more keys as needed…
        }

# Example usage—this will NOT execute on import for Django
if __name__ == "__main__":
    # Just a test driver if needed
    # User inputs symbols (no static list!)
    user_symbols = input("Enter comma-separated NSE symbols: ").split(",")
    dash = Dashboard()
    context = dash.build_dashboard_context([s.strip() for s in user_symbols if s.strip()])
    print(context)
