"""Payoff diagram generation for options strategies."""

from decimal import Decimal
from typing import List
import matplotlib.pyplot as plt
import matplotlib.figure
from .models import Strategy, OptionLeg


class PayoffDiagramGenerator:
    """Generator for options strategy payoff diagrams."""
    
    def generate_payoff_diagram(self, strategy: Strategy, current_price: float) -> matplotlib.figure.Figure:
        """Generate basic payoff diagram for options strategy at expiration."""
        # Price range: ±50% of current price, 51 points for smooth curve
        min_price = current_price * 0.5
        max_price = current_price * 1.5
        prices = [min_price + i * (max_price - min_price) / 50 for i in range(51)]
        
        # Calculate payoff at each price point
        payoffs = []
        for price in prices:
            payoff = self._calculate_payoff_at_price(strategy.legs, price)
            payoffs.append(float(payoff))
        
        # Create matplotlib figure with basic styling
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(prices, payoffs, 'b-', linewidth=2, label='Strategy P&L')
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.7, label='Breakeven')
        ax.axvline(x=current_price, color='green', linestyle=':', alpha=0.7, 
                  label=f'Current Price ${current_price:.2f}')
        
        # Add labels and formatting
        ax.set_xlabel('Stock Price at Expiration ($)')
        ax.set_ylabel('Profit/Loss ($)')
        ax.set_title(f'{strategy.underlying_symbol} Options Strategy Payoff')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        return fig
    
    def _calculate_payoff_at_price(self, legs: List[OptionLeg], stock_price: float) -> Decimal:
        """Calculate total payoff for strategy at given stock price."""
        total_payoff = Decimal('0')
        
        for leg in legs:
            contract = leg.contract
            strike = Decimal(str(contract.strike))
            stock_price_dec = Decimal(str(stock_price))
            
            # Calculate intrinsic value at expiration
            if contract.option_type == 'call':
                intrinsic_value = max(Decimal('0'), stock_price_dec - strike)
            else:  # put
                intrinsic_value = max(Decimal('0'), strike - stock_price_dec)
            
            # Calculate position P&L based on buy/sell action
            if leg.action == 'buy':
                # Bought option: pay premium upfront, receive intrinsic value at expiration
                premium_paid = Decimal(str(contract.ask)) * Decimal(str(leg.quantity))
                position_payoff = (intrinsic_value * Decimal('100') * Decimal(str(leg.quantity))) - premium_paid
            else:  # sell
                # Sold option: receive premium upfront, pay intrinsic value at expiration
                premium_received = Decimal(str(contract.bid)) * Decimal(str(leg.quantity))
                position_payoff = premium_received - (intrinsic_value * Decimal('100') * Decimal(str(leg.quantity)))
            
            total_payoff += position_payoff
        
        return total_payoff.quantize(Decimal('0.01'))