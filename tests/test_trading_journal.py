"""Tests for trading journal with real SQLite database operations."""

import pytest
import os
import tempfile
from datetime import datetime, date
from src.trading_journal import TradingJournal, TradingJournalError
from src.models import Strategy, StrategyMetrics, OptionLeg, OptionContract, TradeRecord


class TestTradingJournal:
    """Test suite for TradingJournal with real SQLite operations."""
    
    @pytest.fixture
    def temp_db_journal(self):
        """Create temporary journal with isolated database."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            temp_db_path = temp_db.name
        
        # Mock get_database_path to use temp file
        import src.trading_journal
        original_get_path = src.trading_journal.get_database_path
        src.trading_journal.get_database_path = lambda: temp_db_path
        
        try:
            journal = TradingJournal()
            yield journal
        finally:
            # Cleanup
            src.trading_journal.get_database_path = original_get_path
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
    
    @pytest.fixture
    def sample_bull_call_spread(self):
        """Create sample bull call spread for testing."""
        buy_leg = OptionLeg(
            action='buy',
            contract=OptionContract(
                symbol='NVDA', strike=145.0, expiration=date(2024, 3, 15),
                option_type='call', bid=11.80, ask=12.20
            )
        )
        sell_leg = OptionLeg(
            action='sell',
            contract=OptionContract(
                symbol='NVDA', strike=155.0, expiration=date(2024, 3, 15),
                option_type='call', bid=6.80, ask=7.20
            )
        )
        return Strategy(legs=[buy_leg, sell_leg], underlying_symbol='NVDA', created_at=datetime.now())
    
    @pytest.fixture
    def sample_metrics(self):
        """Create sample strategy metrics."""
        return StrategyMetrics(
            net_premium=-5.40, max_profit=994.60, max_loss=5.40,
            breakeven_points=[150.54], margin_requirement=5.40, return_on_margin=18418.52
        )
    
    def test_journal_initialization(self, temp_db_journal):
        """Test journal initializes with proper database schema."""
        journal = temp_db_journal
        assert os.path.exists(journal.db_path)
        
        # Verify database has correct schema
        import sqlite3
        with sqlite3.connect(journal.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert 'trades' in tables
    
    def test_save_trade_creates_record(self, temp_db_journal, sample_bull_call_spread, sample_metrics):
        """Test saving a trade creates proper database record."""
        journal = temp_db_journal
        trade_record = journal.save_trade(sample_bull_call_spread, sample_metrics)
        
        # Verify returned trade record
        assert isinstance(trade_record, TradeRecord)
        assert trade_record.id > 0
        assert trade_record.strategy.underlying_symbol == 'NVDA'
        assert trade_record.metrics.net_premium == -5.40
        assert trade_record.status == 'open'
        assert trade_record.entry_date == date.today()
    
    def test_get_all_trades_retrieves_records(self, temp_db_journal, sample_bull_call_spread, sample_metrics):
        """Test retrieving all trades from journal."""
        journal = temp_db_journal
        
        # Initially empty
        assert len(journal.get_all_trades()) == 0
        
        # Save multiple trades
        journal.save_trade(sample_bull_call_spread, sample_metrics)
        
        # Create second strategy (bear put spread)
        bear_put = Strategy(
            legs=[OptionLeg(
                action='buy',
                contract=OptionContract(
                    symbol='TSLA', strike=150.0, expiration=date(2024, 3, 15),
                    option_type='put', bid=9.40, ask=9.70
                )
            )],
            underlying_symbol='TSLA', created_at=datetime.now()
        )
        bear_metrics = StrategyMetrics(
            net_premium=-9.70, max_profit=99999.0, max_loss=9.70,
            breakeven_points=[140.30], margin_requirement=9.70, return_on_margin=0.0
        )
        journal.save_trade(bear_put, bear_metrics)
        
        # Verify retrieval
        trades = journal.get_all_trades()
        assert len(trades) == 2
        assert all(isinstance(trade, TradeRecord) for trade in trades)
        assert trades[0].strategy.underlying_symbol in ['NVDA', 'TSLA']
        assert trades[1].strategy.underlying_symbol in ['NVDA', 'TSLA']
    
    def test_close_trade_calculates_pnl(self, temp_db_journal, sample_bull_call_spread, sample_metrics):
        """Test closing a trade with P&L calculation."""
        journal = temp_db_journal
        
        # Save trade
        open_trade = journal.save_trade(sample_bull_call_spread, sample_metrics)
        assert open_trade.status == 'open'
        
        # Close trade
        closing_price = 160.0  # Above upper strike, should be max profit
        closed_trade = journal.close_trade(open_trade.id, closing_price)
        
        # Verify closed trade
        assert closed_trade.status == 'closed'
        assert closed_trade.closing_price == 160.0
        assert closed_trade.final_pnl == sample_metrics.max_profit
        assert closed_trade.id == open_trade.id
    
    def test_calculate_final_pnl_credit_spread(self, temp_db_journal):
        """Test P&L calculation for credit spreads."""
        journal = temp_db_journal
        
        # Create credit spread (net premium > 0)
        strategy = Strategy(
            legs=[OptionLeg(
                action='sell',
                contract=OptionContract(
                    symbol='HOOD', strike=20.0, expiration=date(2024, 3, 15),
                    option_type='put', bid=2.00, ask=2.20
                )
            )],
            underlying_symbol='HOOD', created_at=datetime.now()
        )
        metrics = StrategyMetrics(
            net_premium=2.00, max_profit=2.00, max_loss=8.00,
            breakeven_points=[18.00], margin_requirement=8.00, return_on_margin=25.0
        )
        
        # Test different closing prices
        assert journal.calculate_final_pnl(strategy, metrics, 22.0) == 2.00  # Keep premium
        assert journal.calculate_final_pnl(strategy, metrics, 15.0) == 2.00  # Single leg, keep premium
    
    def test_calculate_final_pnl_debit_spread(self, temp_db_journal, sample_bull_call_spread, sample_metrics):
        """Test P&L calculation for debit spreads."""
        journal = temp_db_journal
        
        # Debit spread (net premium < 0)
        closing_above_breakeven = 155.0  # Above breakeven
        closing_below_breakeven = 145.0  # Below breakeven
        
        pnl_profit = journal.calculate_final_pnl(sample_bull_call_spread, sample_metrics, closing_above_breakeven)
        pnl_loss = journal.calculate_final_pnl(sample_bull_call_spread, sample_metrics, closing_below_breakeven)
        
        assert pnl_profit == sample_metrics.max_profit
        assert pnl_loss == sample_metrics.max_loss
    
    def test_close_nonexistent_trade_raises_error(self, temp_db_journal):
        """Test closing non-existent trade raises error."""
        journal = temp_db_journal
        
        with pytest.raises(TradingJournalError) as exc_info:
            journal.close_trade(999, 100.0)
        
        assert "not found" in str(exc_info.value)
    
    def test_close_already_closed_trade_raises_error(self, temp_db_journal, sample_bull_call_spread, sample_metrics):
        """Test closing already closed trade raises error."""
        journal = temp_db_journal
        
        # Save and close trade
        trade = journal.save_trade(sample_bull_call_spread, sample_metrics)
        journal.close_trade(trade.id, 150.0)
        
        # Try to close again
        with pytest.raises(TradingJournalError) as exc_info:
            journal.close_trade(trade.id, 160.0)
        
        assert "already closed" in str(exc_info.value)
    
    def test_strategy_serialization_deserialization(self, temp_db_journal, sample_bull_call_spread, sample_metrics):
        """Test strategy and metrics survive serialization round trip."""
        journal = temp_db_journal
        
        # Save trade
        original_trade = journal.save_trade(sample_bull_call_spread, sample_metrics)
        
        # Retrieve trade
        all_trades = journal.get_all_trades()
        retrieved_trade = all_trades[0]
        
        # Verify strategy details preserved
        assert retrieved_trade.strategy.underlying_symbol == original_trade.strategy.underlying_symbol
        assert len(retrieved_trade.strategy.legs) == len(original_trade.strategy.legs)
        
        for orig_leg, retr_leg in zip(original_trade.strategy.legs, retrieved_trade.strategy.legs):
            assert orig_leg.action == retr_leg.action
            assert orig_leg.contract.symbol == retr_leg.contract.symbol
            assert orig_leg.contract.strike == retr_leg.contract.strike
            assert orig_leg.contract.option_type == retr_leg.contract.option_type
        
        # Verify metrics preserved
        assert retrieved_trade.metrics.net_premium == original_trade.metrics.net_premium
        assert retrieved_trade.metrics.max_profit == original_trade.metrics.max_profit
        assert retrieved_trade.metrics.breakeven_points == original_trade.metrics.breakeven_points
    
    def test_database_persistence(self, temp_db_journal, sample_bull_call_spread, sample_metrics):
        """Test data persists across journal instances."""
        journal1 = temp_db_journal
        db_path = journal1.db_path
        
        # Save trade with first instance
        trade1 = journal1.save_trade(sample_bull_call_spread, sample_metrics)
        
        # Create second instance with same database
        import src.trading_journal
        src.trading_journal.get_database_path = lambda: db_path
        journal2 = TradingJournal()
        
        # Verify data accessible from second instance
        trades = journal2.get_all_trades()
        assert len(trades) == 1
        assert trades[0].id == trade1.id
        assert trades[0].strategy.underlying_symbol == 'NVDA'


class TestTradingJournalIntegration:
    """Integration tests for trading journal operations."""
    
    def test_complete_trade_lifecycle(self):
        """Test complete trade lifecycle from save to close."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            temp_db_path = temp_db.name
        
        import src.trading_journal
        original_get_path = src.trading_journal.get_database_path
        src.trading_journal.get_database_path = lambda: temp_db_path
        
        try:
            journal = TradingJournal()
            
            # Create comprehensive strategy
            strategy = Strategy(
                legs=[
                    OptionLeg(action='buy', contract=OptionContract(
                        symbol='CRCL', strike=25.0, expiration=date(2024, 4, 19),
                        option_type='call', bid=3.80, ask=4.10
                    )),
                    OptionLeg(action='sell', contract=OptionContract(
                        symbol='CRCL', strike=30.0, expiration=date(2024, 4, 19),
                        option_type='call', bid=1.90, ask=2.10
                    ))
                ],
                underlying_symbol='CRCL', created_at=datetime.now()
            )
            
            metrics = StrategyMetrics(
                net_premium=-2.20, max_profit=2.80, max_loss=2.20,
                breakeven_points=[27.20], margin_requirement=2.20, return_on_margin=127.27
            )
            
            # Save trade
            saved_trade = journal.save_trade(strategy, metrics)
            assert saved_trade.status == 'open'
            
            # Verify in journal
            all_trades = journal.get_all_trades()
            assert len(all_trades) == 1
            assert all_trades[0].id == saved_trade.id
            
            # Close trade
            closed_trade = journal.close_trade(saved_trade.id, 28.5)
            assert closed_trade.status == 'closed'
            assert closed_trade.final_pnl == metrics.max_profit
            
            # Verify updated in journal
            updated_trades = journal.get_all_trades()
            assert len(updated_trades) == 1
            assert updated_trades[0].status == 'closed'
            assert updated_trades[0].final_pnl == metrics.max_profit
            
        finally:
            src.trading_journal.get_database_path = original_get_path
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)