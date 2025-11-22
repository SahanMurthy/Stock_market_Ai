# risk_manager.py

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
logger = logging.getLogger(__name__)

class RiskManager:
    """
    Pure Python risk management & assessment engine.
    """

    def calculate_var(self, returns: pd.Series, confidence_level: float = 0.95) -> float:
        """Calculate Value-at-Risk (VaR) using the historical method."""
        # Ensure no NaN
        returns = returns.dropna()
        if len(returns) == 0:
            return 0.0
        return -np.percentile(returns, 100 * (1 - confidence_level))

    def calculate_expected_shortfall(self, returns: pd.Series, confidence_level: float = 0.95) -> float:
        """Calculate Expected Shortfall (also known as CVaR or ES)."""
        returns = returns.dropna()
        var = self.calculate_var(returns, confidence_level)
        # Losses worse than VaR
        es = returns[returns < -var].mean() if len(returns) > 0 else 0.0
        return -es if es < 0 else 0

    def position_size(self, capital: float, risk_per_trade_pct: float, stop_loss_pct: float) -> int:
        """
        Calculate recommended position size for a trade, given capital and risk constraints.

        Args:
            capital: total capital (money) available
            risk_per_trade_pct: percent of capital to risk on each trade (e.g., 1)
            stop_loss_pct: percent stop loss for trade (e.g., 5)
        Returns:
            Number of shares/contracts recommended
        """
        if stop_loss_pct == 0:
            return 0
        max_risk = capital * (risk_per_trade_pct / 100)
        shares = max_risk / (stop_loss_pct / 100)
        return int(shares)

    def compute_drawdown(self, equity_curve: pd.Series) -> float:
        """Compute max drawdown percent for an equity curve."""
        running_max = equity_curve.cummax()
        drawdown = (equity_curve - running_max) / running_max
        return drawdown.min() * 100  # min should be negative

    # Add more risk analytics as per your real file...
    def calculate_risk_metrics(self, prices: pd.DataFrame, holding_period: int = 20) -> Dict:
        """
        Calculate common risk metrics on a price series.
        Expects DataFrame with 'Close' price column.
        """
        metrics = {}
        if prices is None or prices.empty or 'Close' not in prices.columns:
            metrics['error'] = 'Invalid or missing price data'
            return metrics
        returns = prices['Close'].pct_change().dropna()
        metrics['annual_volatility_pct'] = returns.std() * (252 ** 0.5) * 100 if not returns.empty else None
        metrics['value_at_risk_95'] = self.calculate_var(returns, 0.95)
        metrics['expected_shortfall_95'] = self.calculate_expected_shortfall(returns, 0.95)
        if len(prices['Close']) > holding_period:
            equity_curve = (1 + returns).cumprod()
            metrics['max_drawdown_pct'] = self.compute_drawdown(equity_curve)
        return metrics

    def stop_loss_price(self, entry_price: float, stop_loss_pct: float, is_long: bool = True) -> float:
        """
        Calculate stop loss price given entry price and percent.
        For long: below entry, for short: above entry.
        """
        if is_long:
            stop_price = entry_price * (1 - stop_loss_pct / 100)
        else:
            stop_price = entry_price * (1 + stop_loss_pct / 100)
        return stop_price

    def risk_reward_ratio(self, entry_price: float, stop_price: float, target_price: float, is_long: bool = True) -> float:
        """
        Calculate risk:reward ratio for a trade setup.
        """
        if is_long:
            risk = entry_price - stop_price
            reward = target_price - entry_price
        else:
            risk = stop_price - entry_price
            reward = entry_price - target_price
        if risk == 0:
            return float('inf') if reward > 0 else 0
        return reward / risk if risk != 0 else 0

    def portfolio_risk_metrics(self, symbol_to_prices: Dict[str, pd.DataFrame]) -> Dict:
        """
        Calculate portfolio risk (aggregate).
        Takes a dict of symbol to price dataframe.
        """
        results = {}
        all_returns = []
        for symbol, df in symbol_to_prices.items():
            if df is not None and not df.empty and 'Close' in df.columns:
                returns = df['Close'].pct_change().dropna()
                all_returns.append(returns)
        if all_returns:
            all_combined = pd.concat(all_returns, ignore_index=True)
            results['portfolio_annual_volatility_pct'] = all_combined.std() * (252 ** 0.5) * 100
            results['portfolio_var_95'] = self.calculate_var(all_combined, 0.95)
            results['portfolio_es_95'] = self.calculate_expected_shortfall(all_combined, 0.95)
        return results

# Example usage (not run in Django):
if __name__ == "__main__":
    rm = RiskManager()
    # You would load real price data here for testing
    # prices = pd.read_csv('some_prices.csv')
    # metrics = rm.calculate_risk_metrics(prices)
    # print(metrics)
