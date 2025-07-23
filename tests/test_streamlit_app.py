"""
Tests for Streamlit web application functionality.

Basic tests to verify the app structure and key components load correctly.
Following MVP principles with simple validation of core functionality.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestStreamlitApp:
    """Test Streamlit app components and functionality."""
    
    def test_app_imports_successfully(self):
        """Test that the app.py file imports without errors."""
        try:
            # This tests that all imports work correctly
            import app
            assert True  # If we get here, imports succeeded
        except ImportError as e:
            pytest.fail(f"App imports failed: {e}")
    
    def test_required_modules_available(self):
        """Test that all required modules are available for the app."""
        # Test core modules
        from src.market_data import MarketDataService, MarketDataError
        from src.strategy_calculator import StrategyCalculator
        from src.ai_analyzer import AIAnalyzer, AIAnalysisError
        from src.trading_journal import TradingJournal, TradingJournalError
        from src.models import Strategy, OptionLeg, OptionContract
        from src.config import ConfigError, get_supported_symbols
        
        # Verify classes can be instantiated
        assert MarketDataService is not None
        assert StrategyCalculator is not None
        assert AIAnalyzer is not None
        assert TradingJournal is not None
        
        # Verify functions work
        symbols = get_supported_symbols()
        assert isinstance(symbols, list)
        assert len(symbols) > 0
    
    @patch('streamlit.set_page_config')
    @patch('streamlit.title')
    @patch('streamlit.markdown')
    def test_app_basic_structure(self, mock_markdown, mock_title, mock_config):
        """Test that app sets up basic structure correctly."""
        import app
        
        # Verify page config was called
        mock_config.assert_called_once()
        
        # Verify title was set
        mock_title.assert_called_once()
        
        # Verify markdown was called for description
        assert mock_markdown.called
    
    def test_strategy_validation_components(self):
        """Test that strategy validation components work."""
        from src.models import OptionContract, OptionLeg, Strategy
        from datetime import date, datetime
        
        # Test contract creation (should work)
        contract = OptionContract(
            symbol='NVDA',
            strike=150.0,
            expiration=date(2024, 3, 15),
            option_type='call',
            bid=8.50,
            ask=8.70
        )
        assert contract.symbol == 'NVDA'
        assert contract.strike == 150.0
        
        # Test leg creation
        leg = OptionLeg(action='buy', contract=contract)
        assert leg.action == 'buy'
        
        # Test strategy creation
        strategy = Strategy(
            legs=[leg],
            underlying_symbol='NVDA',
            created_at=datetime.now()
        )
        assert len(strategy.legs) == 1
        assert strategy.underlying_symbol == 'NVDA'
    
    def test_calculator_integration(self):
        """Test that StrategyCalculator works with strategy objects."""
        from src.strategy_calculator import StrategyCalculator
        from src.models import OptionContract, OptionLeg, Strategy
        from datetime import date, datetime
        
        # Create a simple strategy
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
        
        # Test metrics calculation
        calculator = StrategyCalculator()
        metrics = calculator.calculate_strategy_metrics(strategy)
        
        # Verify metrics are calculated
        assert metrics.net_premium is not None
        assert metrics.max_profit is not None
        assert metrics.max_loss is not None
        assert isinstance(metrics.breakeven_points, list)
        assert metrics.margin_requirement is not None
        assert metrics.return_on_margin is not None
    
    def test_payoff_diagram_integration(self):
        """Test that payoff diagram generation works for web app."""
        from src.strategy_calculator import StrategyCalculator
        from src.models import OptionContract, OptionLeg, Strategy
        from datetime import date, datetime
        import matplotlib.figure
        
        # Create a simple strategy
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
        
        # Test payoff diagram generation
        calculator = StrategyCalculator()
        current_price = 150.0
        fig = calculator.generate_payoff_diagram(strategy, current_price)
        
        # Verify matplotlib figure is created
        assert isinstance(fig, matplotlib.figure.Figure)
        
        # Verify figure has data
        axes = fig.get_axes()
        assert len(axes) == 1
        
        # Verify chart has payoff data
        ax = axes[0]
        lines = ax.get_lines()
        assert len(lines) >= 1  # At least the payoff line


class TestAppConfiguration:
    """Test application configuration and setup."""
    
    def test_supported_symbols_configuration(self):
        """Test that supported symbols are configured correctly."""
        from src.config import get_supported_symbols
        
        symbols = get_supported_symbols()
        expected_symbols = ['NVDA', 'TSLA', 'HOOD', 'CRCL']
        
        assert symbols == expected_symbols
        assert all(isinstance(s, str) for s in symbols)
        assert all(s.isupper() for s in symbols)
    
    def test_error_classes_available(self):
        """Test that error classes are properly defined."""
        from src.market_data import MarketDataError
        from src.ai_analyzer import AIAnalysisError
        from src.trading_journal import TradingJournalError
        from src.config import ConfigError
        
        # Verify error classes can be instantiated
        market_error = MarketDataError("test")
        ai_error = AIAnalysisError("test")
        journal_error = TradingJournalError("test")
        config_error = ConfigError("test")
        
        assert isinstance(market_error, Exception)
        assert isinstance(ai_error, Exception)
        assert isinstance(journal_error, Exception)
        assert isinstance(config_error, Exception)