"""
Tests for payoff diagram generation functionality.

Tests basic payoff diagram generation for single-leg and two-leg strategies,
following MVP principles with simple validation of chart generation.
"""

import pytest
from datetime import datetime, date
import matplotlib.figure
from src.strategy_calculator import StrategyCalculator
from src.models import Strategy, OptionLeg, OptionContract


class TestPayoffDiagram:
    """Test payoff diagram generation for options strategies."""
    
    def setup_method(self):
        """Set up test calculator."""
        self.calculator = StrategyCalculator()
    
    def test_single_long_call_payoff_diagram(self):
        """Test payoff diagram generation for single long call."""
        # Create a long call strategy
        contract = OptionContract(
            symbol='NVDA',
            strike=150.0,
            expiration=date(2024, 3, 15),
            option_type='call',
            bid=8.50,
            ask=8.70
        )
        leg = OptionLeg(action='buy', contract=contract)
        strategy = Strategy(
            legs=[leg],
            underlying_symbol='NVDA',
            created_at=datetime.now()
        )
        
        # Generate payoff diagram
        current_price = 150.25
        fig = self.calculator.generate_payoff_diagram(strategy, current_price)
        
        # Verify matplotlib figure is created
        assert isinstance(fig, matplotlib.figure.Figure)
        
        # Verify basic chart properties
        axes = fig.get_axes()
        assert len(axes) == 1
        ax = axes[0]
        
        # Check labels
        assert 'Stock Price' in ax.get_xlabel()
        assert 'Profit/Loss' in ax.get_ylabel()
        assert 'NVDA' in ax.get_title()
    
    def test_bull_call_spread_payoff_diagram(self):
        """Test payoff diagram for bull call spread (two-leg strategy)."""
        # Buy 145 call, sell 155 call
        buy_contract = OptionContract(
            symbol='NVDA',
            strike=145.0,
            expiration=date(2024, 3, 15),
            option_type='call',
            bid=11.80,
            ask=12.20
        )
        sell_contract = OptionContract(
            symbol='NVDA',
            strike=155.0,
            expiration=date(2024, 3, 15),
            option_type='call',
            bid=6.80,
            ask=7.20
        )
        
        legs = [
            OptionLeg(action='buy', contract=buy_contract),
            OptionLeg(action='sell', contract=sell_contract)
        ]
        strategy = Strategy(
            legs=legs,
            underlying_symbol='NVDA',
            created_at=datetime.now()
        )
        
        # Generate diagram
        current_price = 150.25
        fig = self.calculator.generate_payoff_diagram(strategy, current_price)
        
        # Verify figure creation
        assert isinstance(fig, matplotlib.figure.Figure)
        
        # Verify chart has data
        axes = fig.get_axes()
        assert len(axes) == 1
        ax = axes[0]
        lines = ax.get_lines()
        assert len(lines) >= 1  # At least payoff line
        
        # Verify payoff line has data points
        payoff_line = lines[0]
        x_data, y_data = payoff_line.get_data()
        assert len(x_data) == 51  # Should have 51 price points
        assert len(y_data) == 51
        
        # Verify price range covers ±50% of current price
        expected_min = current_price * 0.5
        expected_max = current_price * 1.5
        assert min(x_data) == pytest.approx(expected_min, rel=1e-3)
        assert max(x_data) == pytest.approx(expected_max, rel=1e-3)
    
    def test_long_put_payoff_diagram(self):
        """Test payoff diagram for single long put."""
        contract = OptionContract(
            symbol='TSLA',
            strike=200.0,
            expiration=date(2024, 4, 19),
            option_type='put',
            bid=15.20,
            ask=15.60
        )
        leg = OptionLeg(action='buy', contract=contract)
        strategy = Strategy(
            legs=[leg],
            underlying_symbol='TSLA',
            created_at=datetime.now()
        )
        
        current_price = 195.50
        fig = self.calculator.generate_payoff_diagram(strategy, current_price)
        
        # Basic validation
        assert isinstance(fig, matplotlib.figure.Figure)
        ax = fig.get_axes()[0]
        assert 'TSLA' in ax.get_title()
        
        # Verify payoff calculation at key points
        lines = ax.get_lines()
        payoff_line = lines[0]
        x_data, y_data = payoff_line.get_data()
        
        # At very low stock prices, long put should be profitable
        # At high stock prices, long put should lose premium
        lowest_price_idx = 0
        highest_price_idx = -1
        
        # Long put: profitable when stock price well below strike
        assert y_data[lowest_price_idx] > 0  # Should be profitable at low prices
        assert y_data[highest_price_idx] < 0  # Should lose premium at high prices
    
    def test_short_call_payoff_diagram(self):
        """Test payoff diagram for single short call."""
        contract = OptionContract(
            symbol='HOOD',
            strike=25.0,
            expiration=date(2024, 5, 17),
            option_type='call',
            bid=2.80,
            ask=3.20
        )
        leg = OptionLeg(action='sell', contract=contract)
        strategy = Strategy(
            legs=[leg],
            underlying_symbol='HOOD',
            created_at=datetime.now()
        )
        
        current_price = 24.50
        fig = self.calculator.generate_payoff_diagram(strategy, current_price)
        
        # Verify diagram creation
        assert isinstance(fig, matplotlib.figure.Figure)
        ax = fig.get_axes()[0]
        
        # Verify payoff characteristics for short call
        lines = ax.get_lines()
        payoff_line = lines[0]
        x_data, y_data = payoff_line.get_data()
        
        # Short call: keep premium at low prices, lose money at high prices
        lowest_price_idx = 0
        highest_price_idx = -1
        
        assert y_data[lowest_price_idx] > 0  # Keep premium at low prices
        assert y_data[highest_price_idx] < 0  # Lose money at high prices


class TestPayoffCalculation:
    """Test underlying payoff calculation logic."""
    
    def setup_method(self):
        """Set up test calculator."""
        self.calculator = StrategyCalculator()
    
    def test_payoff_calculation_accuracy(self):
        """Test that payoff calculations match expected values."""
        # Simple long call: buy NVDA 150 call for $8.70
        contract = OptionContract(
            symbol='NVDA',
            strike=150.0,
            expiration=date(2024, 3, 15),
            option_type='call',
            bid=8.50,
            ask=8.70
        )
        leg = OptionLeg(action='buy', contract=contract)
        strategy = Strategy(
            legs=[leg],
            underlying_symbol='NVDA',
            created_at=datetime.now()
        )
        
        # Generate diagram to access payoff calculation
        current_price = 150.0
        fig = self.calculator.generate_payoff_diagram(strategy, current_price)
        
        # Verify we get a valid figure
        assert isinstance(fig, matplotlib.figure.Figure)
        
        # Get payoff data
        ax = fig.get_axes()[0]
        lines = ax.get_lines()
        payoff_line = lines[0]
        x_data, y_data = payoff_line.get_data()
        
        # Manual verification of a few key points
        # At strike price (150), should lose premium: 0 - 8.70 = -8.70
        strike_idx = None
        for i, price in enumerate(x_data):
            if abs(price - 150.0) < 0.1:  # Find closest to strike
                strike_idx = i
                break
        
        if strike_idx is not None:
            expected_payoff_at_strike = -8.70  # Premium paid
            actual_payoff = y_data[strike_idx]
            assert abs(actual_payoff - expected_payoff_at_strike) < 1.0  # Allow some tolerance
        
        # At price well above strike (e.g., 170), should be profitable
        high_price_idx = None
        for i, price in enumerate(x_data):
            if abs(price - 170.0) < 1.0:
                high_price_idx = i
                break
        
        if high_price_idx is not None:
            # At 170: intrinsic value = 170-150 = 20, minus premium = 20*100 - 8.70 = 1991.30
            expected_payoff = 20 * 100 - 8.70  # Rough calculation
            actual_payoff = y_data[high_price_idx]
            assert actual_payoff > 1000  # Should be significantly profitable