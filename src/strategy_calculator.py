"""Strategy calculator for options spread analysis."""

from decimal import Decimal, ROUND_HALF_UP
from typing import List
import matplotlib.figure
from .models import Strategy, StrategyMetrics, OptionLeg
from .payoff_diagram import PayoffDiagramGenerator


class CalculationError(Exception):
    """Raised when strategy calculation fails."""
    pass


class StrategyCalculator:
    """Calculator for options strategy financial metrics."""
    
    def calculate_strategy_metrics(self, strategy: Strategy) -> StrategyMetrics:
        """Calculate all financial metrics for an options strategy."""
        if not strategy.legs or len(strategy.legs) > 2:
            raise CalculationError("Strategy must have 1-2 legs for MVP")
        
        net_premium = self._calculate_net_premium(strategy.legs)
        max_profit = self._calculate_max_profit(strategy.legs, net_premium)
        max_loss = self._calculate_max_loss(strategy.legs, net_premium)
        breakeven_points = self._calculate_breakeven_points(strategy.legs, net_premium)
        margin_requirement = self._calculate_margin_requirement(max_loss, net_premium)
        return_on_margin = self._calculate_return_on_margin(max_profit, margin_requirement)
        
        return StrategyMetrics(
            net_premium=float(net_premium),
            max_profit=float(max_profit),
            max_loss=float(max_loss),
            breakeven_points=[float(bp) for bp in breakeven_points],
            margin_requirement=float(margin_requirement),
            return_on_margin=float(return_on_margin)
        )
    
    def _calculate_net_premium(self, legs: List[OptionLeg]) -> Decimal:
        """Calculate net premium (credit positive, debit negative)."""
        net_premium = Decimal('0')
        for leg in legs:
            price = leg.contract.bid if leg.action == 'sell' else leg.contract.ask
            premium = Decimal(str(price)) * Decimal(str(leg.quantity))
            net_premium += premium if leg.action == 'sell' else -premium
        return net_premium.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def _calculate_max_profit(self, legs: List[OptionLeg], net_premium: Decimal) -> Decimal:
        """Calculate maximum theoretical profit."""
        if len(legs) == 1:
            leg = legs[0]
            if leg.action == 'buy' and leg.contract.option_type == 'call':
                return Decimal('99999')  # Unlimited upside
            return net_premium if leg.action == 'sell' else abs(net_premium)
        # Two-leg spread
        strikes = sorted([Decimal(str(leg.contract.strike)) for leg in legs])
        spread_value = (strikes[1] - strikes[0]) * Decimal('100')
        return net_premium if net_premium >= 0 else spread_value + net_premium
    
    def _calculate_max_loss(self, legs: List[OptionLeg], net_premium: Decimal) -> Decimal:
        """Calculate maximum theoretical loss."""
        if len(legs) == 1:
            leg = legs[0]
            return abs(net_premium) if leg.action == 'buy' else Decimal('99999')
        # Two-leg spread
        strikes = sorted([Decimal(str(leg.contract.strike)) for leg in legs])
        spread_value = (strikes[1] - strikes[0]) * Decimal('100')
        return spread_value - net_premium if net_premium >= 0 else abs(net_premium)
    
    def _calculate_breakeven_points(self, legs: List[OptionLeg], net_premium: Decimal) -> List[Decimal]:
        """Calculate breakeven points at expiration.""" 
        if len(legs) == 1:
            leg = legs[0]
            strike = Decimal(str(leg.contract.strike))
            premium_amount = abs(net_premium)
            if leg.contract.option_type == 'call':
                breakeven = strike + premium_amount
            else:
                breakeven = strike - premium_amount
            return [breakeven.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)]
        # Two-leg spread
        strikes = [Decimal(str(leg.contract.strike)) for leg in legs]
        lower_strike, upper_strike = min(strikes), max(strikes)
        option_types = [leg.contract.option_type for leg in legs]
        premium_per_share = net_premium / Decimal('100')
        breakeven = (lower_strike + premium_per_share) if 'call' in option_types else (upper_strike - premium_per_share)
        return [breakeven.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)]
    
    def _calculate_margin_requirement(self, max_loss: Decimal, net_premium: Decimal) -> Decimal:
        """Calculate margin requirement."""
        return max_loss if net_premium >= 0 else abs(net_premium)
    
    def _calculate_return_on_margin(self, max_profit: Decimal, margin_requirement: Decimal) -> Decimal:
        """Calculate return on margin percentage."""
        if margin_requirement <= 0 or max_profit >= Decimal('99999') or margin_requirement >= Decimal('99999'):
            return Decimal('0')
        return ((max_profit / margin_requirement) * Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def generate_payoff_diagram(self, strategy: Strategy, current_price: float) -> matplotlib.figure.Figure:
        """Generate payoff diagram for options strategy at expiration."""
        return PayoffDiagramGenerator().generate_payoff_diagram(strategy, current_price)