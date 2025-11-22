import math
from typing import Dict, List, Optional


class SIPCalculator:
    """
    Systematic Investment Plan (SIP) calculator with NO default return rates.
    All return rates must be explicitly provided by the user.
    """

    def calculate(self,
                  monthly_investment: float = None,
                  target_amount: float = None,
                  years: int = None,
                  annual_return: float = None,  # REQUIRED - no default
                  inflation_rate: float = 0.0,
                  step_up_rate: float = 0.0
                  ) -> Dict:
        """
        Calculate SIP - REQUIRES annual_return to be explicitly provided.

        Args:
            monthly_investment: Monthly SIP amount (required if target_amount not given)
            target_amount: Target corpus (required if monthly_investment not given)
            years: Investment period in years (REQUIRED)
            annual_return: Expected annual return % (REQUIRED - must be provided by user)
            inflation_rate: Inflation rate % (optional, default 0)
            step_up_rate: Annual SIP increase % (optional, default 0)

        Returns:
            Dict with SIP calculations

        Raises:
            ValueError if required parameters missing
        """
        # Validate required inputs
        if annual_return is None:
            raise ValueError("annual_return is required - user must specify expected return rate")

        if years is None or years <= 0:
            raise ValueError("years must be specified and greater than 0")

        if not monthly_investment and not target_amount:
            raise ValueError("Either monthly_investment or target_amount must be provided")

        monthly_rate = annual_return / 100 / 12
        months = years * 12

        # Calculate monthly investment if target is given
        if target_amount and not monthly_investment:
            inflated_target = target_amount * ((1 + inflation_rate / 100) ** years)
            if monthly_rate == 0:
                monthly_investment = inflated_target / months
            else:
                monthly_investment = inflated_target * monthly_rate / (((1 + monthly_rate) ** months) - 1)

        # Calculate future value
        if step_up_rate == 0:
            if monthly_rate == 0:
                future_value = monthly_investment * months
            else:
                future_value = monthly_investment * (((1 + monthly_rate) ** months) - 1) / monthly_rate
            total_investment = monthly_investment * months
        else:
            future_value, total_investment = self._calculate_step_up_sip(
                monthly_investment, years, monthly_rate, step_up_rate
            )

        projections = self._generate_projections(monthly_investment, years, monthly_rate, step_up_rate)

        total_returns = future_value - total_investment
        returns_percent = (total_returns / total_investment) * 100 if total_investment > 0 else 0

        return {
            'monthly_sip': round(monthly_investment, 2),
            'total_investment': round(total_investment, 2),
            'future_value': round(future_value, 2),
            'total_returns': round(total_returns, 2),
            'returns_percent': round(returns_percent, 2),
            'wealth_multiplier': round(future_value / total_investment, 2) if total_investment > 0 else 0,
            'projections': projections,
            'parameters': {
                'years': years,
                'annual_return': annual_return,
                'inflation_rate': inflation_rate,
                'step_up_rate': step_up_rate
            }
        }

    def _calculate_step_up_sip(self, initial_sip: float, years: int, monthly_rate: float, step_up_rate: float) -> tuple:
        """Calculate step-up SIP."""
        total_investment = 0
        future_value = 0
        current_sip = initial_sip
        annual_step_up = step_up_rate / 100

        for year in range(years):
            year_investment = current_sip * 12
            remaining_months = (years - year) * 12
            if monthly_rate == 0:
                year_fv = year_investment
            else:
                year_fv = year_investment * (((1 + monthly_rate) ** remaining_months) - 1) / monthly_rate / 12
            total_investment += year_investment
            future_value += year_fv
            current_sip = current_sip * (1 + annual_step_up)

        return future_value, total_investment

    def _generate_projections(self, monthly_sip: float, years: int, monthly_rate: float, step_up_rate: float) -> List[
        Dict]:
        """Generate year-wise projections."""
        projections = []
        current_sip = monthly_sip
        cumulative_investment = 0
        cumulative_value = 0

        for year in range(1, years + 1):
            year_months = year * 12
            year_investment = current_sip * 12
            cumulative_investment += year_investment

            if step_up_rate == 0:
                if monthly_rate == 0:
                    corpus = monthly_sip * year_months
                else:
                    corpus = monthly_sip * (((1 + monthly_rate) ** year_months) - 1) / monthly_rate
            else:
                year_fv = year_investment * (((1 + monthly_rate) ** 12) - 1) / monthly_rate / 12
                cumulative_value += year_fv
                corpus = cumulative_value

            returns = corpus - cumulative_investment
            projections.append({
                'year': year,
                'monthly_sip': round(current_sip, 2),
                'invested': round(cumulative_investment, 2),
                'corpus': round(corpus, 2),
                'returns': round(returns, 2)
            })
            current_sip = current_sip * (1 + step_up_rate / 100)

        return projections

    def calculate_retirement_corpus(self,
                                    current_age: int,
                                    retirement_age: int,
                                    monthly_expenses: float,
                                    inflation_rate: float,
                                    post_retirement_return: float,  # REQUIRED
                                    life_expectancy: int = 85) -> Dict:
        """Calculate retirement corpus - requires all rates to be specified."""
        if post_retirement_return is None:
            raise ValueError("post_retirement_return must be specified")

        years_to_retirement = retirement_age - current_age
        retirement_years = life_expectancy - retirement_age

        future_monthly_expenses = monthly_expenses * ((1 + inflation_rate / 100) ** years_to_retirement)
        monthly_return_rate = post_retirement_return / 100 / 12
        retirement_months = retirement_years * 12

        if monthly_return_rate == 0:
            required_corpus = future_monthly_expenses * retirement_months
        else:
            required_corpus = future_monthly_expenses * (
                    1 - (1 + monthly_return_rate) ** (-retirement_months)
            ) / monthly_return_rate

        return {
            'required_corpus': round(required_corpus, 2),
            'future_monthly_expenses': round(future_monthly_expenses, 2),
            'years_to_retirement': years_to_retirement,
            'retirement_years': retirement_years
        }


# Standalone usage example
if __name__ == "__main__":
    calc = SIPCalculator()
    result = calc.calculate(monthly_investment=10000, years=15, annual_return=12)
    print(f"Monthly SIP: ₹{result['monthly_sip']}")
    print(f"Future Value: ₹{result['future_value']}")
    print(f"Returns: {result['returns_percent']}%")
