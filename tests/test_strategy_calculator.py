"""
Tests for strategy calculator with known financial scenarios.

These tests use predetermined option prices to verify calculation accuracy.
"""

import pytest
from datetime import datetime, date
from decimal import Decimal
from src.strategy_calculator import StrategyCalculator, CalculationError
from src.models import Strategy, OptionLeg, OptionContract


class TestStrategyCalculator:
    """Test suite for StrategyCalculator with known scenarios."""
    
    @pytest.fixture
    def calculator(self):
        """Create StrategyCalculator instance."""
        return StrategyCalculator()
    
    @pytest.fixture
    def sample_call_option(self):
        """Create sample call option contract."""
        return OptionContract(
            symbol='NVDA',
            strike=150.0,
            expiration=date(2024, 12, 20),
            option_type='call',
            bid=8.50,
            ask=8.70
        )
    
    @pytest.fixture  
    def sample_put_option(self):
        """Create sample put option contract."""
        return OptionContract(
            symbol='NVDA',
            strike=140.0,
            expiration=date(2024, 12, 20),
            option_type='put',
            bid=5.20,
            ask=5.40
        )
    
    def test_single_long_call_calculation(self, calculator, sample_call_option):
        """Test calculations for single long call position."""
        leg = OptionLeg(action='buy', contract=sample_call_option)
        strategy = Strategy(
            legs=[leg],
            underlying_symbol='NVDA', 
            created_at=datetime.now()
        )
        
        metrics = calculator.calculate_strategy_metrics(strategy)
        
        # Long call: pay ask price
        assert metrics.net_premium == -8.70  # Debit
        assert metrics.max_profit == 99999.0  # Unlimited upside
        assert metrics.max_loss == 8.70  # Premium paid
        assert len(metrics.breakeven_points) == 1
        assert metrics.breakeven_points[0] == 158.70  # Strike + premium per share
        assert metrics.margin_requirement == 8.70  # Premium paid
        assert metrics.return_on_margin == 0.0  # Unlimited profit
    
    def test_single_short_call_calculation(self, calculator, sample_call_option):
        """Test calculations for single short call position."""
        leg = OptionLeg(action='sell', contract=sample_call_option)
        strategy = Strategy(
            legs=[leg],
            underlying_symbol='NVDA',
            created_at=datetime.now()
        )
        
        metrics = calculator.calculate_strategy_metrics(strategy)
        
        # Short call: receive bid price
        assert metrics.net_premium == 8.50  # Credit
        assert metrics.max_profit == 8.50  # Premium received
        assert metrics.max_loss == 99999.0  # Unlimited risk
        assert len(metrics.breakeven_points) == 1
        assert metrics.breakeven_points[0] == 158.50  # Strike + premium per share
        assert metrics.margin_requirement == 99999.0  # Unlimited risk
        assert metrics.return_on_margin == 0.0  # Unlimited risk
    
    def test_bull_call_spread_calculation(self, calculator):
        """Test bull call spread (buy lower strike, sell higher strike)."""
        # Buy 145 call
        long_call = OptionContract(
            symbol='NVDA', strike=145.0, expiration=date(2024, 12, 20),
            option_type='call', bid=12.0, ask=12.20
        )
        # Sell 155 call  
        short_call = OptionContract(
            symbol='NVDA', strike=155.0, expiration=date(2024, 12, 20),
            option_type='call', bid=6.80, ask=7.00
        )
        
        strategy = Strategy(
            legs=[
                OptionLeg(action='buy', contract=long_call),
                OptionLeg(action='sell', contract=short_call)
            ],
            underlying_symbol='NVDA',
            created_at=datetime.now()
        )
        
        metrics = calculator.calculate_strategy_metrics(strategy)
        
        # Net premium: pay 12.20 - receive 6.80 = -5.40 (debit)
        assert metrics.net_premium == -5.40
        
        # Max profit: spread width - net premium = (155-145)*100 - 5.40 = 994.60
        assert metrics.max_profit == 994.60
        
        # Max loss: net premium paid = 5.40
        assert metrics.max_loss == 5.40
        
        # Breakeven: lower strike + net premium per share = 145 + (-5.40/100) = 144.946
        assert len(metrics.breakeven_points) == 1
        assert abs(metrics.breakeven_points[0] - 144.95) < 0.01  # 145 - 5.40/100
        
        # Margin: net premium for debit spread
        assert metrics.margin_requirement == 5.40
        
        # Return on margin: 994.60 / 5.40 * 100 = 18,418.5%
        assert abs(metrics.return_on_margin - 18418.52) < 0.01
    
    def test_bear_put_spread_calculation(self, calculator):
        """Test bear put spread (buy higher strike, sell lower strike)."""
        # Buy 150 put
        long_put = OptionContract(
            symbol='NVDA', strike=150.0, expiration=date(2024, 12, 20),
            option_type='put', bid=9.50, ask=9.70
        )
        # Sell 140 put
        short_put = OptionContract(
            symbol='NVDA', strike=140.0, expiration=date(2024, 12, 20),
            option_type='put', bid=5.20, ask=5.40
        )
        
        strategy = Strategy(
            legs=[
                OptionLeg(action='buy', contract=long_put),
                OptionLeg(action='sell', contract=short_put)
            ],
            underlying_symbol='NVDA',
            created_at=datetime.now()
        )
        
        metrics = calculator.calculate_strategy_metrics(strategy)
        
        # Net premium: pay 9.70 - receive 5.20 = -4.50 (debit)
        assert metrics.net_premium == -4.50
        
        # Max profit: spread width - net premium = (150-140)*100 - 4.50 = 995.50
        assert metrics.max_profit == 995.50
        
        # Max loss: net premium = 4.50
        assert metrics.max_loss == 4.50
        
        # Margin: net premium for debit spread
        assert metrics.margin_requirement == 4.50
    
    def test_invalid_strategy_raises_error(self, calculator):
        """Test that invalid strategies raise CalculationError."""
        # Strategy validation happens in Strategy.__post_init__, so we test with
        # a strategy that has too many legs instead
        call_option = OptionContract(
            symbol='NVDA', strike=150.0, expiration=date(2024, 12, 20),
            option_type='call', bid=8.50, ask=8.70
        )
        
        # Create a mock strategy with too many legs by bypassing validation
        strategy = Strategy(
            legs=[OptionLeg(action='buy', contract=call_option)],
            underlying_symbol='NVDA', created_at=datetime.now()
        )
        # Manually add extra legs to bypass Strategy validation
        strategy.legs.extend([
            OptionLeg(action='buy', contract=call_option),
            OptionLeg(action='buy', contract=call_option)
        ])
        
        with pytest.raises(CalculationError):
            calculator.calculate_strategy_metrics(strategy)
    
    def test_precision_handling(self, calculator):
        """Test that calculations handle precision correctly."""
        # Use option with fractional prices
        call_option = OptionContract(
            symbol='NVDA', strike=150.0, expiration=date(2024, 12, 20),
            option_type='call', bid=8.555, ask=8.777
        )
        
        strategy = Strategy(
            legs=[OptionLeg(action='buy', contract=call_option)],
            underlying_symbol='NVDA',
            created_at=datetime.now()
        )
        
        metrics = calculator.calculate_strategy_metrics(strategy)
        
        # Should be rounded to 2 decimal places
        assert metrics.net_premium == -8.78  # Rounded from -8.777
        assert metrics.max_loss == 8.78
        assert isinstance(metrics.breakeven_points[0], float)
        assert round(metrics.breakeven_points[0], 2) == metrics.breakeven_points[0]