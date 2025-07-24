"""AI-powered strategy analysis using OpenRouter API integration."""

import httpx
import json
from typing import Dict, Any
from .config import get_api_key, get_api_timeout
from .models import Strategy, StrategyMetrics


class AIAnalysisError(Exception):
    """Base exception for AI analysis errors."""
    pass


class AIAnalyzer:
    """Service for AI-powered options strategy analysis."""
    
    def __init__(self):
        self.api_key = get_api_key('openrouter')
        self.timeout = get_api_timeout()
        self.client = httpx.Client(timeout=self.timeout)
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def analyze_strategy(self, strategy: Strategy, metrics: StrategyMetrics, 
                        current_stock_price: float) -> Dict[str, str]:
        """
        Analyze options strategy and return AI insights.
        
        Returns:
            Dict with keys: 'interpretation', 'market_outlook', 'risk_warning'
        """
        prompt = self._format_analysis_prompt(strategy, metrics, current_stock_price)
        response = self._make_api_request(prompt)
        return self._parse_analysis_response(response)
    
    def _format_analysis_prompt(self, strategy: Strategy, metrics: StrategyMetrics, 
                               current_price: float) -> str:
        """Format strategy data into structured prompt for AI analysis."""
        legs_desc = []
        for leg in strategy.legs:
            contract = leg.contract
            legs_desc.append(f"{leg.action} {contract.option_type} ${contract.strike} "
                           f"(bid: ${contract.bid}, ask: ${contract.ask})")
        
        return f"""Analyze this options strategy:

Stock: {strategy.underlying_symbol} at ${current_price:.2f}
Strategy: {' | '.join(legs_desc)}
Net Premium: ${metrics.net_premium:.2f}
Max Profit: ${metrics.max_profit:.2f}
Max Loss: ${metrics.max_loss:.2f}
Breakeven: {metrics.breakeven_points}

Provide exactly 3 responses:
1. INTERPRETATION: One sentence explaining what strategy this is
2. MARKET_OUTLOOK: What market expectation this strategy implies
3. RISK_WARNING: Primary risk if market moves against position

Format: JSON with keys "interpretation", "market_outlook", "risk_warning"."""
    
    def _make_api_request(self, prompt: str) -> Dict[str, Any]:
        """Make API request to OpenRouter with error handling."""
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": "google/gemini-2.5-flash-lite", "messages": [{"role": "user", "content": prompt}], "temperature": 0.3, "max_tokens": 300}
        
        try:
            response = self.client.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            if 'error' in data:
                raise AIAnalysisError(f"API error: {data['error']}")
            return data
        except httpx.HTTPStatusError as e:
            raise AIAnalysisError("Invalid API key" if e.response.status_code == 401 else f"HTTP error {e.response.status_code}")
        except httpx.RequestError as e:
            raise AIAnalysisError(f"Request failed: {e}")
    
    def _parse_analysis_response(self, response: Dict[str, Any]) -> Dict[str, str]:
        """Parse AI response and extract analysis components."""
        try:
            content = response['choices'][0]['message']['content']
            analysis = json.loads(content.strip())
            required_keys = ['interpretation', 'market_outlook', 'risk_warning']
            for key in required_keys:
                if key not in analysis:
                    raise AIAnalysisError(f"Missing required key: {key}")
            return {key: analysis[key] for key in required_keys}
        except (KeyError, json.JSONDecodeError, IndexError) as e:
            raise AIAnalysisError(f"Invalid response format: {e}")
    
    def __del__(self):
        """Clean up HTTP client."""
        if hasattr(self, 'client'):
            self.client.close()