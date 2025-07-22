"""Market data service for Alpha Vantage API integration."""

import httpx
from datetime import datetime, date
from typing import List, Dict, Any
from .config import get_api_key, get_api_timeout
from .models import StockQuote, OptionContract


class MarketDataError(Exception):
    """Base exception for market data service errors."""
    pass


class MarketDataService:
    """Service for retrieving market data from Alpha Vantage API."""
    
    def __init__(self):
        self.api_key = get_api_key('alpha_vantage')
        self.timeout = get_api_timeout()
        self.client = httpx.Client(timeout=self.timeout)
    
    def get_stock_quote(self, symbol: str) -> StockQuote:
        """Get real-time stock quote for given symbol."""
        data = self._request('GLOBAL_QUOTE', {'symbol': symbol})
        return self._parse_stock_quote(data, symbol)
    
    def get_options_chain(self, symbol: str, expiration: date) -> List[OptionContract]:
        """Get options chain data for given symbol and expiration date."""
        params = {
            'symbol': symbol,
            'date': expiration.strftime('%Y-%m-%d')
        }
        data = self._request('REALTIME_OPTIONS', params)
        return self._parse_options_chain(data, symbol, expiration)
    
    def _request(self, function: str, params: Dict[str, str]) -> Dict[str, Any]:
        """Make API request with error handling."""
        params.update({'function': function, 'apikey': self.api_key})
        
        try:
            response = self.client.get('https://www.alphavantage.co/query', params=params)
            response.raise_for_status()
            data = response.json()
            self._check_errors(data, params.get('symbol', ''))
            return data
        except httpx.RequestError as e:
            raise MarketDataError(f"Request failed: {e}")
    
    def _check_errors(self, data: Dict[str, Any], symbol: str) -> None:
        """Check for API errors and raise appropriate exceptions."""
        if 'Error Message' in data:
            raise MarketDataError(f"Invalid symbol: {symbol}")
        if any(key in data for key in ['Note', 'Information']):
            msg = data.get('Note') or data.get('Information', '')
            if 'rate limit' in msg.lower():
                raise MarketDataError(f"Rate limit exceeded: {msg}")
    
    def _parse_stock_quote(self, data: Dict[str, Any], symbol: str) -> StockQuote:
        """Parse stock quote response."""
        quote_data = data.get('Global Quote', {})
        if not quote_data:
            raise MarketDataError(f"No data for {symbol}")
        
        try:
            return StockQuote(
                symbol=symbol.upper(),
                price=float(quote_data['05. price']),
                timestamp=datetime.strptime(quote_data['07. latest trading day'], '%Y-%m-%d')
            )
        except (KeyError, ValueError) as e:
            raise MarketDataError(f"Invalid response format: {e}")
    
    def _parse_options_chain(self, data: Dict[str, Any], symbol: str, expiration: date) -> List[OptionContract]:
        """Parse options chain response."""
        options_data = data.get('data', [])
        if not options_data:
            raise MarketDataError(f"No options data for {symbol}")
        
        contracts = []
        for option in options_data:
            try:
                contracts.append(OptionContract(
                    symbol=symbol.upper(),
                    strike=float(option['strike']),
                    expiration=expiration,
                    option_type=option['type'].lower(),
                    bid=float(option['bid']),
                    ask=float(option['ask'])
                ))
            except (KeyError, ValueError):
                continue
        
        if not contracts:
            raise MarketDataError(f"No valid options found for {symbol}")
        return contracts
    
    def __del__(self):
        """Clean up HTTP client."""
        if hasattr(self, 'client'):
            self.client.close()