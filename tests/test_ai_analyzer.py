"""
Tests for AI analyzer with real OpenRouter API calls.

These tests require valid OPENROUTER_API_KEY in environment.
Tests may be slow due to API latency and rate limits.
"""

import pytest
from datetime import datetime, date
from src.ai_analyzer import AIAnalyzer, AIAnalysisError
from src.models import Strategy, StrategyMetrics, OptionLeg, OptionContract
from src.config import ConfigError


class TestAIAnalyzer:
    """Test suite for AIAnalyzer with real OpenRouter API calls."""
    
    @pytest.fixture
    def service(self):
        """Create AIAnalyzer instance."""
        try:
            return AIAnalyzer()
        except ConfigError:
            pytest.skip("OPENROUTER_API_KEY not configured")
    
    @pytest.fixture
    def bull_call_spread(self):
        """Create a bull call spread strategy for testing."""
        buy_leg = OptionLeg(
            action='buy',
            contract=OptionContract(
                symbol='NVDA',
                strike=145.0,
                expiration=date(2024, 3, 15),
                option_type='call',
                bid=11.80,
                ask=12.20
            )
        )
        sell_leg = OptionLeg(
            action='sell',
            contract=OptionContract(
                symbol='NVDA',
                strike=155.0,
                expiration=date(2024, 3, 15),
                option_type='call',
                bid=6.80,
                ask=7.20
            )
        )
        return Strategy(
            legs=[buy_leg, sell_leg],
            underlying_symbol='NVDA',
            created_at=datetime.now()
        )
    
    @pytest.fixture
    def bull_call_metrics(self):
        """Create realistic metrics for bull call spread."""
        return StrategyMetrics(
            net_premium=-5.40,
            max_profit=994.60,
            max_loss=5.40,
            breakeven_points=[150.54],
            margin_requirement=5.40,
            return_on_margin=18418.52
        )
    
    @pytest.fixture
    def bear_put_spread(self):
        """Create a bear put spread strategy for testing."""
        buy_leg = OptionLeg(
            action='buy',
            contract=OptionContract(
                symbol='TSLA',
                strike=150.0,
                expiration=date(2024, 3, 15),
                option_type='put',
                bid=9.40,
                ask=9.70
            )
        )
        sell_leg = OptionLeg(
            action='sell',
            contract=OptionContract(
                symbol='TSLA',
                strike=140.0,
                expiration=date(2024, 3, 15),
                option_type='put',
                bid=5.00,
                ask=5.20
            )
        )
        return Strategy(
            legs=[buy_leg, sell_leg],
            underlying_symbol='TSLA',
            created_at=datetime.now()
        )
    
    @pytest.fixture
    def bear_put_metrics(self):
        """Create realistic metrics for bear put spread."""
        return StrategyMetrics(
            net_premium=-4.50,
            max_profit=995.50,
            max_loss=4.50,
            breakeven_points=[145.50],
            margin_requirement=4.50,
            return_on_margin=22122.22
        )
    
    def test_analyzer_initialization(self, service):
        """Test AIAnalyzer initializes with proper configuration."""
        assert service.api_key is not None
        assert service.base_url == "https://openrouter.ai/api/v1/chat/completions"
        assert service.timeout > 0
    
    def test_bull_call_spread_analysis(self, service, bull_call_spread, bull_call_metrics):
        """Test real AI analysis of bull call spread strategy."""
        analysis = service.analyze_strategy(bull_call_spread, bull_call_metrics, 150.25)
        
        # Verify all required keys are present
        assert 'interpretation' in analysis
        assert 'market_outlook' in analysis
        assert 'risk_warning' in analysis
        
        # Verify content is meaningful (not empty strings)
        assert len(analysis['interpretation']) > 10
        assert len(analysis['market_outlook']) > 10
        assert len(analysis['risk_warning']) > 10
        
        # Verify strategy understanding (should mention bull/call/spread concepts)
        interpretation = analysis['interpretation'].lower()
        assert any(word in interpretation for word in ['bull', 'call', 'spread', 'upward', 'rise'])
    
    def test_bear_put_spread_analysis(self, service, bear_put_spread, bear_put_metrics):
        """Test real AI analysis of bear put spread strategy."""
        analysis = service.analyze_strategy(bear_put_spread, bear_put_metrics, 145.75)
        
        # Verify all required keys are present
        assert 'interpretation' in analysis
        assert 'market_outlook' in analysis
        assert 'risk_warning' in analysis
        
        # Verify content quality
        assert len(analysis['interpretation']) > 10
        assert len(analysis['market_outlook']) > 10  
        assert len(analysis['risk_warning']) > 10
        
        # Verify strategy understanding (should mention bear/put/spread concepts)
        interpretation = analysis['interpretation'].lower()
        assert any(word in interpretation for word in ['bear', 'put', 'spread', 'downward', 'decline'])
    
    def test_single_leg_long_call_analysis(self, service):
        """Test AI analysis of single leg long call strategy."""
        long_call = Strategy(
            legs=[OptionLeg(
                action='buy',
                contract=OptionContract(
                    symbol='HOOD',
                    strike=25.0,
                    expiration=date(2024, 3, 15),
                    option_type='call',
                    bid=2.80,
                    ask=3.10
                )
            )],
            underlying_symbol='HOOD',
            created_at=datetime.now()
        )
        
        metrics = StrategyMetrics(
            net_premium=-3.10,
            max_profit=99999.0,  # Unlimited
            max_loss=3.10,
            breakeven_points=[28.10],
            margin_requirement=3.10,
            return_on_margin=0.0  # Unlimited profit scenario
        )
        
        analysis = service.analyze_strategy(long_call, metrics, 24.50)
        
        # Verify response structure
        assert all(key in analysis for key in ['interpretation', 'market_outlook', 'risk_warning'])
        
        # Should recognize unlimited profit potential
        interpretation = analysis['interpretation'].lower()
        assert any(word in interpretation for word in ['long', 'call', 'buy', 'unlimited', 'bullish'])
    
    def test_format_analysis_prompt(self, service, bull_call_spread, bull_call_metrics):
        """Test that prompt formatting includes all required strategy details."""
        prompt = service._format_analysis_prompt(bull_call_spread, bull_call_metrics, 150.25)
        
        # Verify all key information is in prompt
        assert 'NVDA at $150.25' in prompt
        assert 'buy call $145.0' in prompt
        assert 'sell call $155.0' in prompt
        assert '$-5.40' in prompt
        assert '$994.60' in prompt
        assert '[150.54]' in prompt
        assert 'JSON' in prompt
        assert 'interpretation' in prompt
        assert 'market_outlook' in prompt
        assert 'risk_warning' in prompt
    
    def test_analyzer_error_handling_invalid_api_key(self):
        """Test handling of invalid API key."""
        # Temporarily create analyzer with invalid key
        import os
        original_key = os.environ.get('OPENROUTER_API_KEY')
        os.environ['OPENROUTER_API_KEY'] = 'invalid_key_12345'
        
        try:
            analyzer = AIAnalyzer()
            
            # Create minimal test strategy
            strategy = Strategy(
                legs=[OptionLeg(
                    action='buy',
                    contract=OptionContract(
                        symbol='TEST',
                        strike=100.0,
                        expiration=date(2024, 3, 15),
                        option_type='call',
                        bid=1.0,
                        ask=1.5
                    )
                )],
                underlying_symbol='TEST',
                created_at=datetime.now()
            )
            
            metrics = StrategyMetrics(
                net_premium=-1.5,
                max_profit=99999.0,
                max_loss=1.5,
                breakeven_points=[101.5],
                margin_requirement=1.5,
                return_on_margin=0.0
            )
            
            # Should raise AIAnalysisError due to invalid key
            with pytest.raises(AIAnalysisError):
                analyzer.analyze_strategy(strategy, metrics, 100.0)
        
        finally:
            # Restore original API key
            if original_key:
                os.environ['OPENROUTER_API_KEY'] = original_key
            elif 'OPENROUTER_API_KEY' in os.environ:
                del os.environ['OPENROUTER_API_KEY']
    
    def test_consistency_across_calls(self, service, bull_call_spread, bull_call_metrics):
        """Test that repeated calls return consistent analysis structure."""
        analysis1 = service.analyze_strategy(bull_call_spread, bull_call_metrics, 150.25)
        analysis2 = service.analyze_strategy(bull_call_spread, bull_call_metrics, 150.25)
        
        # Both should have same structure
        assert set(analysis1.keys()) == set(analysis2.keys())
        assert all(len(analysis1[key]) > 0 for key in analysis1.keys())
        assert all(len(analysis2[key]) > 0 for key in analysis2.keys())
        
        # Content may differ slightly but should be related to same strategy type
        assert 'call' in analysis1['interpretation'].lower()
        assert 'call' in analysis2['interpretation'].lower()


class TestAIAnalyzerIntegration:
    """Integration tests with real AI analysis."""
    
    @pytest.fixture
    def service(self):
        """Create AIAnalyzer instance for integration tests."""
        try:
            return AIAnalyzer()
        except ConfigError:
            pytest.skip("OPENROUTER_API_KEY not configured")
    
    def test_end_to_end_analysis_workflow(self, service):
        """Test complete analysis workflow with realistic data."""
        # Create a realistic iron condor-like strategy (but limited to 2 legs for MVP)
        strategy = Strategy(
            legs=[
                OptionLeg(
                    action='sell',
                    contract=OptionContract(
                        symbol='CRCL',
                        strike=30.0,
                        expiration=date(2024, 4, 19),
                        option_type='put',
                        bid=1.80,
                        ask=2.00
                    )
                ),
                OptionLeg(
                    action='buy',
                    contract=OptionContract(
                        symbol='CRCL',
                        strike=25.0,
                        expiration=date(2024, 4, 19),
                        option_type='put',
                        bid=0.90,
                        ask=1.10
                    )
                )
            ],
            underlying_symbol='CRCL',
            created_at=datetime.now()
        )
        
        metrics = StrategyMetrics(
            net_premium=0.70,  # Credit spread
            max_profit=0.70,
            max_loss=4.30,
            breakeven_points=[29.30],
            margin_requirement=4.30,
            return_on_margin=16.28
        )
        
        # Perform analysis
        analysis = service.analyze_strategy(strategy, metrics, 28.50)
        
        # Comprehensive verification
        assert isinstance(analysis, dict)
        assert len(analysis) == 3
        
        # Check all required components
        required_keys = ['interpretation', 'market_outlook', 'risk_warning']
        for key in required_keys:
            assert key in analysis
            assert isinstance(analysis[key], str)
            assert len(analysis[key]) > 20  # Meaningful content
        
        # Verify strategy understanding
        interpretation = analysis['interpretation'].lower()
        assert any(word in interpretation for word in ['put', 'spread', 'credit', 'bear'])
        
        # Verify risk awareness
        risk_warning = analysis['risk_warning'].lower()
        assert any(word in risk_warning for word in ['risk', 'loss', 'maximum', 'below'])