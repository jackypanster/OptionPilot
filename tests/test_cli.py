"""Integration tests for CLI interface with real API calls."""

import pytest
import tempfile
import os
from click.testing import CliRunner
from cli import cli
from src.config import ConfigError


class TestCLIIntegration:
    """Integration tests for CLI with real API calls."""
    
    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()
    
    @pytest.fixture
    def temp_db_cli(self):
        """Setup CLI with temporary database."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            temp_db_path = temp_db.name
        
        # Mock database path for CLI tests
        import src.trading_journal
        original_get_path = src.trading_journal.get_database_path
        src.trading_journal.get_database_path = lambda: temp_db_path
        
        yield temp_db_path
        
        # Cleanup
        src.trading_journal.get_database_path = original_get_path
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)
    
    def test_cli_help_command(self, runner):
        """Test CLI help shows all commands."""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'OptionPilot' in result.output
        assert 'get-quote' in result.output
        assert 'get-options' in result.output
        assert 'build-strategy' in result.output
        assert 'analyze-strategy' in result.output
        assert 'save-trade' in result.output
        assert 'list-trades' in result.output
        assert 'close-trade' in result.output
    
    def test_get_quote_command_with_real_api(self, runner):
        """Test get-quote command with real Alpha Vantage API."""
        try:
            result = runner.invoke(cli, ['get-quote', 'NVDA'])
            # CLI always exits with 0, but shows error in output
            assert result.exit_code == 0
            
            # Should either succeed with stock price or show real API error
            if 'NVDA:' in result.output and '$' in result.output:
                # Successful API call
                pass
            else:
                # Real API errors are expected (rate limits, etc.)
                assert any(phrase in result.output.lower() for phrase in 
                         ['rate limit', 'api', 'network', 'timeout', 'exceeded'])
            
            # Verify we're getting real API response (not config error)
            assert 'Missing' not in result.output
            assert 'ALPHA_VANTAGE_API_KEY' not in result.output
        except Exception as e:
            # Configuration errors indicate test environment issues
            if "Missing" in str(e) and "API_KEY" in str(e):
                pytest.skip("Alpha Vantage API key not configured")
            else:
                raise
    
    def test_get_options_command_with_real_api(self, runner):
        """Test get-options command with real Alpha Vantage API."""
        try:
            result = runner.invoke(cli, ['get-options', 'TSLA', '2024-03-15'])
            # Should either succeed or fail with real API error
            if result.exit_code == 0:
                assert 'TSLA' in result.output
                assert '2024-03-15' in result.output
            else:
                # Real API errors are acceptable
                assert any(phrase in result.output.lower() for phrase in 
                         ['rate limit', 'api', 'network', 'timeout', 'invalid'])
        except Exception as e:
            if "Missing" in str(e) and "API_KEY" in str(e):
                pytest.skip("Alpha Vantage API key not configured")
            else:
                raise
    
    def test_list_trades_empty_journal(self, runner, temp_db_cli):
        """Test list-trades with empty journal."""
        result = runner.invoke(cli, ['list-trades'])
        assert result.exit_code == 0
        assert 'No trades found' in result.output
    
    def test_analyze_strategy_without_building(self, runner):
        """Test analyze-strategy command without building strategy first."""
        result = runner.invoke(cli, ['analyze-strategy'])
        assert result.exit_code == 0
        assert 'Build strategy first' in result.output
    
    def test_save_trade_without_building(self, runner):
        """Test save-trade command without building strategy first."""
        result = runner.invoke(cli, ['save-trade'])
        assert result.exit_code == 0
        assert 'Build strategy first' in result.output
    
    def test_close_trade_nonexistent(self, runner, temp_db_cli):
        """Test close-trade command with non-existent trade ID."""
        result = runner.invoke(cli, ['close-trade', '--id', '999', '--price', '100.0'])
        assert result.exit_code == 0
        assert 'not found' in result.output.lower()
    
    def test_build_strategy_invalid_date_format(self, runner):
        """Test build-strategy with invalid date format."""
        result = runner.invoke(cli, ['build-strategy'], input='NVDA\ninvalid-date\n')
        assert result.exit_code == 0
        assert 'Invalid date' in result.output
    
    def test_command_error_handling(self, runner):
        """Test CLI error handling for invalid commands."""
        result = runner.invoke(cli, ['nonexistent-command'])
        assert result.exit_code != 0
        assert 'No such command' in result.output


class TestCLIEndToEndWorkflow:
    """End-to-end workflow tests with real integrations."""
    
    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()
    
    @pytest.fixture
    def isolated_cli(self):
        """Setup CLI with isolated database and mocked globals."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            temp_db_path = temp_db.name
        
        import src.trading_journal
        original_get_path = src.trading_journal.get_database_path
        src.trading_journal.get_database_path = lambda: temp_db_path
        
        # Reset CLI global state
        import cli
        cli.current_strategy = None
        cli.current_metrics = None
        
        yield temp_db_path
        
        # Cleanup
        src.trading_journal.get_database_path = original_get_path
        cli.current_strategy = None
        cli.current_metrics = None
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)
    
    def test_simulated_strategy_workflow(self, runner, isolated_cli):
        """Test complete strategy workflow with simulated user input."""
        # Build a bull call spread strategy
        strategy_input = """NVDA
2024-03-15
buy
call
145.0
11.80
12.20
y
sell
call
155.0
6.80
7.20
"""
        
        # Build strategy
        result = runner.invoke(cli, ['build-strategy'], input=strategy_input)
        assert result.exit_code == 0
        assert 'Built!' in result.output
        assert 'Premium:' in result.output
        
        # Save the strategy
        result = runner.invoke(cli, ['save-trade'])
        assert result.exit_code == 0
        assert 'Saved!' in result.output
        assert 'ID:' in result.output
        
        # List trades to verify it was saved
        result = runner.invoke(cli, ['list-trades'])
        assert result.exit_code == 0
        assert 'NVDA' in result.output
        assert 'Open' in result.output
        
        # Close the trade
        result = runner.invoke(cli, ['close-trade', '--id', '1', '--price', '160.0'])
        assert result.exit_code == 0
        assert 'Closed!' in result.output
        assert 'P&L:' in result.output
        
        # Verify trade is closed
        result = runner.invoke(cli, ['list-trades'])
        assert result.exit_code == 0
        assert '🔴' in result.output  # Closed trade indicator
    
    def test_ai_analysis_workflow_with_real_api(self, runner, isolated_cli):
        """Test AI analysis workflow with real OpenRouter API."""
        # Build strategy first
        strategy_input = """HOOD
2024-04-19
buy
call
25.0
2.80
3.10
n
"""
        
        result = runner.invoke(cli, ['build-strategy'], input=strategy_input)
        assert result.exit_code == 0
        
        # Test AI analysis
        try:
            result = runner.invoke(cli, ['analyze-strategy'], input='24.50\n')
            if result.exit_code == 0:
                assert '🤖' in result.output
                assert any(word in result.output.lower() for word in 
                         ['strategy', 'call', 'bullish', 'buy'])
            else:
                # Real API errors are acceptable
                assert any(phrase in result.output.lower() for phrase in 
                         ['api', 'error', 'invalid', 'authentication'])
        except Exception as e:
            if "Missing" in str(e) and "OPENROUTER_API_KEY" in str(e):
                pytest.skip("OpenRouter API key not configured")
            else:
                raise
    
    def test_strategy_persistence_across_commands(self, runner, isolated_cli):
        """Test that strategy persists across different CLI commands."""
        # Build strategy
        strategy_input = """CRCL
2024-06-21
sell
put
30.0
1.80
2.00
n
"""
        
        result = runner.invoke(cli, ['build-strategy'], input=strategy_input)
        assert result.exit_code == 0
        
        # Save should work with the built strategy
        result = runner.invoke(cli, ['save-trade'])
        assert result.exit_code == 0
        assert 'Saved!' in result.output
        
        # Verify it's in the journal
        result = runner.invoke(cli, ['list-trades'])
        assert result.exit_code == 0
        assert 'CRCL' in result.output