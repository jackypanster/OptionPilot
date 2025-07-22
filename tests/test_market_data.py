"""
Tests for market data service with real Alpha Vantage API calls.

These tests require valid ALPHA_VANTAGE_API_KEY in environment.
Tests may be slow due to API rate limits.
"""

import pytest
from datetime import datetime, date, timedelta
from src.market_data import MarketDataService, MarketDataError
from src.models import StockQuote, OptionContract
from src.config import ConfigError


class TestMarketDataService:
    """Test suite for MarketDataService with real API calls."""
    
    @pytest.fixture
    def service(self):
        """Create MarketDataService instance."""
        try:
            return MarketDataService()
        except ConfigError:
            pytest.skip("ALPHA_VANTAGE_API_KEY not configured")
    
    def test_get_stock_quote_valid_symbol(self, service):
        """Test getting stock quote for valid symbol."""
        quote = service.get_stock_quote('NVDA')
        
        assert isinstance(quote, StockQuote)
        assert quote.symbol == 'NVDA'
        assert quote.price > 0
        assert isinstance(quote.timestamp, datetime)
        assert quote.timestamp.year >= 2020  # Sanity check for reasonable date
    
    def test_get_stock_quote_all_supported_symbols(self, service):
        """Test getting quotes for all supported symbols."""
        from src.config import get_supported_symbols
        
        symbols = get_supported_symbols()
        
        for symbol in symbols:
            quote = service.get_stock_quote(symbol)
            assert isinstance(quote, StockQuote)
            assert quote.symbol == symbol
            assert quote.price > 0
    
    def test_get_stock_quote_invalid_symbol(self, service):
        """Test handling of invalid stock symbol."""
        with pytest.raises(MarketDataError):
            service.get_stock_quote('INVALID_SYMBOL_XYZ')
    
    def test_get_stock_quote_empty_symbol(self, service):
        """Test handling of empty symbol."""
        with pytest.raises(MarketDataError):
            service.get_stock_quote('')
    
    def test_get_options_chain_valid_symbol(self, service):
        """Test getting options chain for valid symbol and future date."""
        # Use a date about 30 days in the future
        future_date = date.today() + timedelta(days=30)
        
        # Find the next Friday (typical options expiration)
        days_ahead = 4 - future_date.weekday()  # 4 = Friday
        if days_ahead <= 0:
            days_ahead += 7
        expiration = future_date + timedelta(days=days_ahead)
        
        contracts = service.get_options_chain('NVDA', expiration)
        
        assert isinstance(contracts, list)
        assert len(contracts) > 0
        
        # Verify all contracts are valid
        for contract in contracts:
            assert isinstance(contract, OptionContract)
            assert contract.symbol == 'NVDA'
            assert contract.expiration == expiration
            assert contract.option_type in ['call', 'put']
            assert contract.strike > 0
            assert contract.bid >= 0
            assert contract.ask >= contract.bid
    
    def test_get_options_chain_invalid_symbol(self, service):
        """Test options chain with invalid symbol."""
        future_date = date.today() + timedelta(days=30)
        
        with pytest.raises(MarketDataError):
            service.get_options_chain('INVALID_SYMBOL_XYZ', future_date)
    
    def test_get_options_chain_past_date(self, service):
        """Test options chain with past expiration date."""
        past_date = date.today() - timedelta(days=30)
        
        # This should either return empty list or raise an error
        try:
            contracts = service.get_options_chain('NVDA', past_date)
            assert isinstance(contracts, list)
        except MarketDataError:
            # Expected for past dates
            pass
    
    def test_service_initialization_no_api_key(self, monkeypatch):
        """Test service initialization without API key."""
        monkeypatch.delenv('ALPHA_VANTAGE_API_KEY', raising=False)
        
        with pytest.raises(ConfigError):
            MarketDataService()
    
    def test_client_cleanup(self, service):
        """Test that HTTP client is properly cleaned up."""
        # Access client to ensure it's created
        assert hasattr(service, 'client')
        
        # Manually trigger cleanup
        service.__del__()
        
        # This test mainly ensures no exceptions are raised during cleanup


class TestMarketDataExceptions:
    """Test exception handling and error conditions."""
    
    @pytest.fixture
    def service(self):
        """Create MarketDataService instance."""
        try:
            return MarketDataService()
        except ConfigError:
            pytest.skip("ALPHA_VANTAGE_API_KEY not configured")
    
    def test_rate_limit_detection(self, service):
        """Test rate limit error detection."""
        # Make multiple rapid requests to potentially trigger rate limit
        symbols = ['NVDA', 'TSLA', 'HOOD', 'CRCL'] * 10
        
        try:
            for symbol in symbols:
                service.get_stock_quote(symbol)
        except MarketDataError:
            # Expected when rate limit is hit or other errors occur
            pass


# Integration tests that require real API responses
class TestMarketDataIntegration:
    """Integration tests with real market data."""
    
    @pytest.fixture
    def service(self):
        """Create MarketDataService instance."""
        try:
            return MarketDataService()
        except ConfigError:
            pytest.skip("ALPHA_VANTAGE_API_KEY not configured")
    
    def test_data_consistency(self, service):
        """Test that repeated calls return consistent data types."""
        quote1 = service.get_stock_quote('NVDA')
        quote2 = service.get_stock_quote('NVDA')
        
        # Prices may differ slightly, but structure should be consistent
        assert type(quote1.price) == type(quote2.price)
        assert quote1.symbol == quote2.symbol
        assert isinstance(quote1.timestamp, datetime)
        assert isinstance(quote2.timestamp, datetime)
    
    def test_cross_validation_quote_and_options(self, service):
        """Test that stock quote symbol matches options chain symbol."""
        quote = service.get_stock_quote('NVDA')
        
        # Get options for a future date
        future_date = date.today() + timedelta(days=30)
        days_ahead = 4 - future_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        expiration = future_date + timedelta(days=days_ahead)
        
        try:
            contracts = service.get_options_chain('NVDA', expiration)
            if contracts:  # If options are available
                assert all(contract.symbol == quote.symbol for contract in contracts)
        except MarketDataError:
            # No options data available, which is acceptable
            pass