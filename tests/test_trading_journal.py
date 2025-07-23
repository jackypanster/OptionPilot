"""
Tests for trading journal with SQLite persistence.

These tests verify CRUD operations, P&L calculations, and data persistence.
"""

import pytest
import os
import tempfile
from datetime import datetime, date
from src.trading_journal import TradingJournal, TradingJournalError
from src.models import Strategy, StrategyMetrics, OptionLeg, OptionContract


def create_bull_call_spread(symbol: str = 'NVDA', 
                           buy_strike: float = 145.0, 
                           sell_strike: float = 155.0) -> Strategy:
    """Factory function for creating bull call spread strategies."""
    buy_leg = OptionLeg(
        action='buy',
        contract=OptionContract(
            symbol=symbol,
            strike=buy_strike,
            expiration=date(2024, 3, 15),
            option_type='call',
            bid=11.80,
            ask=12.20
        )
    )
    sell_leg = OptionLeg(
        action='sell',
        contract=OptionContract(
            symbol=symbol,
            strike=sell_strike,
            expiration=date(2024, 3, 15),
            option_type='call',
            bid=6.80,
            ask=7.20
        )
    )
    return Strategy(
        legs=[buy_leg, sell_leg],
        underlying_symbol=symbol,
        created_at=datetime.now()
    )


def create_sample_metrics(net_premium: float = -5.40) -> StrategyMetrics:
    """Factory function for creating sample strategy metrics."""
    return StrategyMetrics(
        net_premium=net_premium,
        max_profit=994.60,
        max_loss=abs(net_premium),
        breakeven_points=[150.54],
        margin_requirement=abs(net_premium),
        return_on_margin=18418.52
    )


def create_single_leg_strategy(symbol: str = 'TSLA', 
                              strike: float = 200.0,
                              action: str = 'buy',
                              option_type: str = 'call') -> Strategy:
    """Factory function for creating single leg strategies."""
    return Strategy(
        legs=[OptionLeg(
            action=action,
            contract=OptionContract(
                symbol=symbol,
                strike=strike,
                expiration=date(2024, 3, 15),
                option_type=option_type,
                bid=10.0,
                ask=10.50
            )
        )],
        underlying_symbol=symbol,
        created_at=datetime.now()
    )


@pytest.fixture
def temp_journal():
    """Create TradingJournal with temporary database."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
        temp_db_path = temp_db.name
    
    # Override database path
    original_path = os.environ.get('DATABASE_PATH')
    os.environ['DATABASE_PATH'] = temp_db_path
    
    try:
        journal = TradingJournal()
        yield journal
    finally:
        # Cleanup environment
        if original_path:
            os.environ['DATABASE_PATH'] = original_path
        elif 'DATABASE_PATH' in os.environ:
            del os.environ['DATABASE_PATH']
        
        # Remove temporary file
        try:
            os.unlink(temp_db_path)
        except OSError:
            pass


class TestTradingJournal:
    """Test suite for TradingJournal with temporary database."""
    

    
    @pytest.fixture
    def sample_bull_call_spread(self):
        """Create sample bull call spread strategy."""
        return create_bull_call_spread()
    
    @pytest.fixture
    def sample_metrics(self):
        """Create sample strategy metrics."""
        return create_sample_metrics()
    
    def test_journal_initialization(self, temp_journal):
        """Test that journal initializes and creates database."""
        # Database should be created automatically
        assert os.path.exists(temp_journal.db_path)
        
        # Should be able to get empty trade list
        trades = temp_journal.get_all_trades()
        assert isinstance(trades, list)
        assert len(trades) == 0
    
    def test_save_trade(self, temp_journal, sample_bull_call_spread, sample_metrics):
        """Test saving a trade to the journal."""
        # Save trade
        saved_trade = temp_journal.save_trade(sample_bull_call_spread, sample_metrics)
        
        # Verify trade record
        assert saved_trade.id is not None
        assert saved_trade.id > 0
        assert saved_trade.strategy.underlying_symbol == 'NVDA'
        assert saved_trade.metrics.net_premium == -5.40
        assert saved_trade.status == 'open'
        assert saved_trade.entry_date == date.today()
        assert saved_trade.closing_price is None
        assert saved_trade.final_pnl is None
    
    def test_get_all_trades(self, temp_journal, sample_bull_call_spread, sample_metrics):
        """Test retrieving all trades from journal."""
        # Initially empty
        trades = temp_journal.get_all_trades()
        assert len(trades) == 0
        
        # Save a trade
        saved_trade = temp_journal.save_trade(sample_bull_call_spread, sample_metrics)
        
        # Should now have one trade
        trades = temp_journal.get_all_trades()
        assert len(trades) == 1
        assert trades[0].id == saved_trade.id
        assert trades[0].strategy.underlying_symbol == 'NVDA'
        assert trades[0].status == 'open'
    
    def test_close_trade(self, temp_journal, sample_bull_call_spread, sample_metrics):
        """Test closing a trade with P&L calculation."""
        # Save trade
        saved_trade = temp_journal.save_trade(sample_bull_call_spread, sample_metrics)
        
        # Close trade at profitable price
        closing_price = 160.0  # Above both strikes
        closed_trade = temp_journal.close_trade(saved_trade.id, closing_price)
        
        # Verify closed trade
        assert closed_trade.id == saved_trade.id
        assert closed_trade.status == 'closed'
        assert closed_trade.closing_price == closing_price
        assert closed_trade.final_pnl == sample_metrics.max_profit
    
    def test_close_trade_at_loss(self, temp_journal, sample_bull_call_spread, sample_metrics):
        """Test closing a trade at a loss."""
        # Save trade
        saved_trade = temp_journal.save_trade(sample_bull_call_spread, sample_metrics)
        
        # Close trade at losing price
        closing_price = 140.0  # Below both strikes
        closed_trade = temp_journal.close_trade(saved_trade.id, closing_price)
        
        # Verify loss calculation
        assert closed_trade.status == 'closed'
        assert closed_trade.closing_price == closing_price
        assert closed_trade.final_pnl == sample_metrics.max_loss
    
    def test_close_nonexistent_trade(self, temp_journal):
        """Test error handling when closing nonexistent trade."""
        with pytest.raises(TradingJournalError):
            temp_journal.close_trade(999, 150.0)
    
    def test_close_already_closed_trade(self, temp_journal, sample_bull_call_spread, sample_metrics):
        """Test error handling when closing already closed trade."""
        # Save and close trade
        saved_trade = temp_journal.save_trade(sample_bull_call_spread, sample_metrics)
        temp_journal.close_trade(saved_trade.id, 160.0)
        
        # Try to close again
        with pytest.raises(TradingJournalError):
            temp_journal.close_trade(saved_trade.id, 150.0)
    
    def test_multiple_trades_ordering(self, temp_journal, sample_bull_call_spread, sample_metrics):
        """Test that trades are returned in correct order (newest first)."""
        # Save multiple trades with slight delay
        trade1 = temp_journal.save_trade(sample_bull_call_spread, sample_metrics)
        
        # Create second strategy with different symbol
        strategy2 = create_single_leg_strategy('TSLA')
        
        trade2 = temp_journal.save_trade(strategy2, sample_metrics)
        
        # Get all trades
        trades = temp_journal.get_all_trades()
        assert len(trades) == 2
        
        # Should be ordered by entry date descending (newest first)
        # Since both have same date, order by ID descending
        assert trades[0].id >= trades[1].id
    
    def test_pnl_calculation_credit_spread(self, temp_journal):
        """Test P&L calculation for credit spread."""
        # Create bull put credit spread
        strategy = Strategy(
            legs=[
                OptionLeg(
                    action='sell',
                    contract=OptionContract(
                        symbol='NVDA',
                        strike=150.0,
                        expiration=date(2024, 3, 15),
                        option_type='put',
                        bid=8.00,
                        ask=8.20
                    )
                ),
                OptionLeg(
                    action='buy',
                    contract=OptionContract(
                        symbol='NVDA',
                        strike=140.0,
                        expiration=date(2024, 3, 15),
                        option_type='put',
                        bid=4.50,
                        ask=4.70
                    )
                )
            ],
            underlying_symbol='NVDA',
            created_at=datetime.now()
        )
        
        # Credit spread metrics
        metrics = StrategyMetrics(
            net_premium=3.30,  # Credit
            max_profit=3.30,
            max_loss=6.70,
            breakeven_points=[146.70],
            margin_requirement=6.70,
            return_on_margin=49.25
        )
        
        # Save trade
        saved_trade = temp_journal.save_trade(strategy, metrics)
        
        # Test closing at different prices
        # Close above both strikes (max profit)
        closed_trade = temp_journal.close_trade(saved_trade.id, 155.0)
        assert closed_trade.final_pnl == metrics.max_profit
    
    def test_data_persistence(self, temp_journal, sample_bull_call_spread, sample_metrics):
        """Test that data persists across journal instances."""
        # Save trade
        saved_trade = temp_journal.save_trade(sample_bull_call_spread, sample_metrics)
        db_path = temp_journal.db_path
        
        # Create new journal instance with same database
        os.environ['DATABASE_PATH'] = db_path
        new_journal = TradingJournal()
        
        # Should be able to retrieve the trade
        trades = new_journal.get_all_trades()
        assert len(trades) == 1
        assert trades[0].id == saved_trade.id
        assert trades[0].strategy.underlying_symbol == 'NVDA'
    
    def test_strategy_serialization_roundtrip(self, temp_journal, sample_bull_call_spread, sample_metrics):
        """Test that strategy data survives serialization/deserialization."""
        # Save trade
        saved_trade = temp_journal.save_trade(sample_bull_call_spread, sample_metrics)
        
        # Retrieve trade
        trades = temp_journal.get_all_trades()
        retrieved_trade = trades[0]
        
        # Verify all strategy details are preserved
        original_strategy = sample_bull_call_spread
        retrieved_strategy = retrieved_trade.strategy
        
        assert retrieved_strategy.underlying_symbol == original_strategy.underlying_symbol
        assert len(retrieved_strategy.legs) == len(original_strategy.legs)
        
        # Check first leg details
        orig_leg = original_strategy.legs[0]
        retr_leg = retrieved_strategy.legs[0]
        
        assert retr_leg.action == orig_leg.action
        assert retr_leg.quantity == orig_leg.quantity
        assert retr_leg.contract.symbol == orig_leg.contract.symbol
        assert retr_leg.contract.strike == orig_leg.contract.strike
        assert retr_leg.contract.option_type == orig_leg.contract.option_type
        assert retr_leg.contract.bid == orig_leg.contract.bid
        assert retr_leg.contract.ask == orig_leg.contract.ask
    
    def test_metrics_serialization_roundtrip(self, temp_journal, sample_bull_call_spread, sample_metrics):
        """Test that metrics data survives serialization/deserialization."""
        # Save trade
        saved_trade = temp_journal.save_trade(sample_bull_call_spread, sample_metrics)
        
        # Retrieve trade
        trades = temp_journal.get_all_trades()
        retrieved_metrics = trades[0].metrics
        
        # Verify all metrics are preserved
        assert retrieved_metrics.net_premium == sample_metrics.net_premium
        assert retrieved_metrics.max_profit == sample_metrics.max_profit
        assert retrieved_metrics.max_loss == sample_metrics.max_loss
        assert retrieved_metrics.breakeven_points == sample_metrics.breakeven_points
        assert retrieved_metrics.margin_requirement == sample_metrics.margin_requirement
        assert retrieved_metrics.return_on_margin == sample_metrics.return_on_margin


class TestTradingJournalPnLCalculations:
    """Specific tests for P&L calculation logic."""
    
    @pytest.mark.parametrize("closing_price,expected_pnl,scenario", [
        (140.0, 5.40, "below_both_strikes"),
        (150.0, 5.40, "between_strikes_below_breakeven"),
        (151.0, 994.60, "above_breakeven"),
        (160.0, 994.60, "above_both_strikes"),
    ])
    def test_bull_call_spread_pnl_scenarios(self, temp_journal, closing_price, expected_pnl, scenario):
        """Test P&L calculation for bull call spread at different closing prices."""
        # Bull call spread: Buy 145 Call, Sell 155 Call
        strategy = create_bull_call_spread()
        metrics = create_sample_metrics()
        
        # Save and close trade
        saved_trade = temp_journal.save_trade(strategy, metrics)
        closed_trade = temp_journal.close_trade(saved_trade.id, closing_price)
        
        assert closed_trade.final_pnl == expected_pnl, \
            f"Scenario {scenario}: Expected P&L {expected_pnl} for closing price {closing_price}, got {closed_trade.final_pnl}"
    
    def test_single_long_call_pnl(self, temp_journal):
        """Test P&L calculation for single long call."""
        strategy = create_single_leg_strategy('NVDA', 150.0, 'buy', 'call')
        
        metrics = StrategyMetrics(
            net_premium=-8.70,  # Premium paid
            max_profit=99999.0,  # Unlimited
            max_loss=8.70,
            breakeven_points=[158.70],
            margin_requirement=8.70,
            return_on_margin=0.0
        )
        
        # Save trade
        saved_trade = temp_journal.save_trade(strategy, metrics)
        
        # Test closing below breakeven (loss)
        closed_trade = temp_journal.close_trade(saved_trade.id, 155.0)
        assert closed_trade.final_pnl == metrics.max_loss
    
    def test_database_error_handling(self):
        """Test handling of database connection errors."""
        # Test with invalid database path
        original_path = os.environ.get('DATABASE_PATH')
        os.environ['DATABASE_PATH'] = '/invalid/path/database.db'
        
        try:
            # This should raise an error when trying to create tables
            with pytest.raises((OSError, PermissionError, Exception)):
                TradingJournal()
        finally:
            # Restore original path
            if original_path:
                os.environ['DATABASE_PATH'] = original_path
            elif 'DATABASE_PATH' in os.environ:
                del os.environ['DATABASE_PATH']