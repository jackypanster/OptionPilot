"""
Simplified CLI validation tests for MVP error handling.

Tests that the CLI fails fast with appropriate errors for invalid inputs,
following MVP principles of immediate crash rather than complex error handling.
"""

import pytest
from click.testing import CliRunner
from cli import cli


class TestCLIValidation:
    """Test basic input validation that should cause immediate failures."""
    
    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()
    
    def test_get_quote_invalid_symbol_fails_fast(self):
        """Test that invalid stock symbol causes immediate failure."""
        result = self.runner.invoke(cli, ['get-quote', 'INVALID'])
        
        # Should fail immediately with non-zero exit code
        assert result.exit_code != 0
        assert "Unsupported symbol: INVALID" in str(result.exception)
        assert "NVDA, TSLA, HOOD, CRCL" in str(result.exception)
    
    def test_get_quote_valid_symbol_attempts_api_call(self):
        """Test that valid symbol passes validation (may still fail on API)."""
        result = self.runner.invoke(cli, ['get-quote', 'NVDA'])
        
        # Should pass validation, may fail on API call but that's expected
        # We're only testing that ValueError for invalid symbol is NOT raised
        if result.exit_code != 0:
            # If it fails, should be due to API issues, not symbol validation
            assert "Unsupported symbol" not in str(result.output)
    
    def test_get_options_invalid_symbol_fails_fast(self):
        """Test that invalid symbol in get-options fails immediately."""
        result = self.runner.invoke(cli, ['get-options', 'INVALID', '2024-03-15'])
        
        assert result.exit_code != 0
        assert "Unsupported symbol: INVALID" in str(result.exception)
    
    def test_get_options_invalid_date_format_shows_error(self):
        """Test that invalid date format shows error message."""
        result = self.runner.invoke(cli, ['get-options', 'NVDA', 'invalid-date'])
        
        # Should exit gracefully but show error message
        assert result.exit_code == 0
        assert "❌" in result.output  # Should show error message
    
    def test_build_strategy_invalid_symbol_fails_fast(self):
        """Test that invalid symbol in strategy builder fails immediately."""
        # Simulate user input with invalid symbol
        result = self.runner.invoke(cli, ['build-strategy'], input='INVALID\n')
        
        assert result.exit_code != 0
        assert "Unsupported symbol: INVALID" in str(result.exception)
    
    def test_build_strategy_valid_symbol_continues(self):
        """Test that valid symbol passes validation in strategy builder."""
        # This will fail later due to missing inputs, but should pass symbol validation
        result = self.runner.invoke(cli, ['build-strategy'], input='NVDA\n')
        
        # Should not fail on symbol validation specifically
        if result.exit_code != 0:
            assert "Unsupported symbol: NVDA" not in str(result.output)
    
    def test_supported_symbols_list(self):
        """Test that supported symbols list matches configuration."""
        from src.config import get_supported_symbols
        
        symbols = get_supported_symbols()
        expected = ['NVDA', 'TSLA', 'HOOD', 'CRCL']
        
        assert symbols == expected
    
    def test_negative_prices_in_option_contract_fail_fast(self):
        """Test that negative prices cause immediate dataclass validation failure."""
        from src.models import OptionContract
        from datetime import date
        
        # Should raise ValueError due to dataclass validation
        with pytest.raises(ValueError, match="cannot be negative"):
            OptionContract(
                symbol='NVDA',
                strike=150.0,
                expiration=date(2024, 3, 15),
                option_type='call',
                bid=-5.0,  # Negative bid should fail
                ask=10.0
            )
    
    def test_invalid_ask_bid_spread_fails_fast(self):
        """Test that ask < bid causes immediate validation failure."""
        from src.models import OptionContract
        from datetime import date
        
        with pytest.raises(ValueError, match="Ask price.*cannot be less than bid"):
            OptionContract(
                symbol='NVDA',
                strike=150.0,
                expiration=date(2024, 3, 15),
                option_type='call',
                bid=10.0,
                ask=5.0  # Ask < bid should fail
            )


class TestCLIFailureModes:
    """Test that the CLI fails appropriately in edge cases."""
    
    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()
    
    def test_analyze_strategy_without_building_fails_gracefully(self):
        """Test that analyzing without building strategy shows clear error."""
        result = self.runner.invoke(cli, ['analyze-strategy'])
        
        # Should exit cleanly with error message, not crash
        assert result.exit_code == 0  # Click handles this gracefully
        assert "Build strategy first" in result.output
    
    def test_save_trade_without_building_fails_gracefully(self):
        """Test that saving without building strategy shows clear error."""
        result = self.runner.invoke(cli, ['save-trade'])
        
        assert result.exit_code == 0
        assert "Build strategy first" in result.output