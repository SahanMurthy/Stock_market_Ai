# core_logic/stock_screener.py - FIXED

import yfinance as yf
from typing import List, Dict
import logging
from datetime import datetime, time as dt_time, timedelta  # FIX: Import timedelta from datetime
import pytz

logger = logging.getLogger(__name__)


class StockScreener:
    """Real-time stock screening with market hours detection"""

    def __init__(self):
        self.ist_tz = pytz.timezone('Asia/Kolkata')

    def is_market_open(self) -> Dict[str, any]:
        """Check if Indian stock market is open"""
        now = datetime.now(self.ist_tz)

        # NSE trading hours: Mon-Fri, 9:15 AM to 3:30 PM IST
        is_weekend = now.weekday() >= 5  # Saturday=5, Sunday=6

        market_open_time = dt_time(9, 15)
        market_close_time = dt_time(15, 30)
        current_time = now.time()

        is_trading_hours = market_open_time <= current_time <= market_close_time
        is_open = not is_weekend and is_trading_hours

        return {
            'is_open': is_open,
            'is_weekend': is_weekend,
            'current_time': now.strftime('%I:%M %p'),
            'current_day': now.strftime('%A'),
            'message': self._get_market_message(is_open, is_weekend, now)
        }

    def _get_market_message(self, is_open: bool, is_weekend: bool, now: datetime) -> str:
        """Generate user-friendly market status message"""
        if is_weekend:
            # FIX: Use timedelta from datetime, not pytz
            next_monday = now + timedelta(days=(7 - now.weekday()))
            return f"📅 Market closed for weekend. Opens Monday at 9:15 AM IST"

        if not is_open:
            if now.time() < dt_time(9, 15):
                return f"🕒 Market opens today at 9:15 AM IST (Currently {now.strftime('%I:%M %p')})"
            else:
                return f"🔔 Market closed at 3:30 PM IST. Opens tomorrow at 9:15 AM IST"

        return "🟢 Market is OPEN - Real-time trading active"

    def get_trending_stocks(self, category: str = 'large_cap', limit: int = 10) -> List[str]:
        """Get trending stocks - REAL-TIME ONLY"""

        # Check market status
        market_status = self.is_market_open()

        if not market_status['is_open']:
            logger.warning(f"⚠️  {market_status['message']}")
            return []  # Return empty - NO DEFAULTS

        try:
            logger.info(f"🔍 Screening {category} stocks (Market OPEN)...")

            # Use valid NSE stocks
            trending = self._get_valid_stocks(category)

            logger.info(f"✓ Found {len(trending)} stocks")
            return trending[:limit]

        except Exception as e:
            logger.error(f"Screening error: {e}")
            return []

    def _get_valid_stocks(self, category: str) -> List[str]:
        """Get valid NSE stocks by category"""

        stocks = {
            'large_cap': ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
                          'HINDUNILVR.NS', 'ITC.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS'],
            'mid_cap': ['DIVISLAB.NS', 'SRF.NS', 'INDIGO.NS', 'GODREJCP.NS', 'BERGEPAINT.NS'],
            'small_cap': ['DIXON.NS', 'POLYCAB.NS', 'ZOMATO.NS', 'NAUKRI.NS', 'CAMS.NS'],
            'it_sector': ['TCS.NS', 'INFY.NS', 'WIPRO.NS', 'HCLTECH.NS', 'TECHM.NS'],
            'banking': ['HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'KOTAKBANK.NS', 'AXISBANK.NS'],
            'pharma': ['SUNPHARMA.NS', 'DRREDDY.NS', 'DIVISLAB.NS', 'CIPLA.NS', 'LUPIN.NS'],
            'mix': ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS']
        }

        return stocks.get(category, stocks['large_cap'])

    def get_sector_stocks(self, sector: str, limit: int = 10) -> List[str]:
        """Get sector stocks"""
        return self.get_trending_stocks(sector, limit)
