"""Trading journal with SQLite persistence for paper trading records."""

import sqlite3
import json
from datetime import datetime, date
from typing import List
from .config import get_database_path
from .models import Strategy, StrategyMetrics, TradeRecord, OptionLeg, OptionContract


class TradingJournalError(Exception):
    """Base exception for trading journal errors."""
    pass


class TradingJournal:
    """SQLite-based trading journal for paper trading records."""
    
    def __init__(self):
        self.db_path = get_database_path()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT, strategy_data TEXT NOT NULL,
                metrics_data TEXT NOT NULL, entry_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open', closing_price REAL NULL,
                final_pnl REAL NULL)""")
    
    def save_trade(self, strategy: Strategy, metrics: StrategyMetrics) -> TradeRecord:
        """Save a new strategy as trade record."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO trades (strategy_data, metrics_data, entry_date, status) VALUES (?, ?, ?, ?)",
                          (json.dumps(self._strategy_to_dict(strategy)), json.dumps(metrics.__dict__),
                           date.today().isoformat(), 'open'))
            return TradeRecord(id=cursor.lastrowid, strategy=strategy, metrics=metrics,
                              entry_date=date.today(), status='open')
    
    def get_all_trades(self) -> List[TradeRecord]:
        """Retrieve all trades from journal."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trades ORDER BY entry_date DESC, id DESC")
            return [self._row_to_trade(row) for row in cursor.fetchall()]
    
    def close_trade(self, trade_id: int, closing_price: float) -> TradeRecord:
        """Close a trade with manual closing price and calculate P&L."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trades WHERE id = ?", (trade_id,))
            row = cursor.fetchone()
            if not row or row[4] == 'closed':
                raise TradingJournalError(f"Trade {trade_id} not found or already closed")
            
            strategy = self._dict_to_strategy(json.loads(row[1]))
            metrics = self._dict_to_metrics(json.loads(row[2]))
            final_pnl = self.calculate_final_pnl(strategy, metrics, closing_price)
            cursor.execute("UPDATE trades SET status = ?, closing_price = ?, final_pnl = ? WHERE id = ?",
                          ('closed', closing_price, final_pnl, trade_id))
            return TradeRecord(id=trade_id, strategy=strategy, metrics=metrics,
                              entry_date=date.fromisoformat(row[3]), status='closed',
                              closing_price=closing_price, final_pnl=final_pnl)
    
    def calculate_final_pnl(self, strategy: Strategy, metrics: StrategyMetrics, closing_price: float) -> float:
        """Calculate final P&L based on closing stock price."""
        if metrics.net_premium > 0:  # Credit spread
            strikes = [leg.contract.strike for leg in strategy.legs]
            if len(strikes) == 2:
                lower, upper = sorted(strikes)
                return -metrics.max_loss if lower <= closing_price <= upper else metrics.max_profit
            return metrics.net_premium
        else:  # Debit spread
            if metrics.breakeven_points:
                return metrics.max_profit if closing_price > metrics.breakeven_points[0] else metrics.max_loss
            return metrics.net_premium
    
    def _strategy_to_dict(self, strategy: Strategy) -> dict:
        """Convert strategy to dictionary."""
        return {'underlying_symbol': strategy.underlying_symbol, 'created_at': strategy.created_at.isoformat(),
                'legs': [{'action': leg.action, 'quantity': leg.quantity,
                         'contract': {'symbol': leg.contract.symbol, 'strike': leg.contract.strike,
                                    'expiration': leg.contract.expiration.isoformat(),
                                    'option_type': leg.contract.option_type,
                                    'bid': leg.contract.bid, 'ask': leg.contract.ask}} for leg in strategy.legs]}
    
    def _dict_to_strategy(self, data: dict) -> Strategy:
        """Convert dictionary to strategy."""
        legs = [OptionLeg(action=leg['action'], quantity=leg['quantity'],
                         contract=OptionContract(symbol=leg['contract']['symbol'], strike=leg['contract']['strike'],
                                               expiration=date.fromisoformat(leg['contract']['expiration']),
                                               option_type=leg['contract']['option_type'],
                                               bid=leg['contract']['bid'], ask=leg['contract']['ask'])) for leg in data['legs']]
        return Strategy(legs=legs, underlying_symbol=data['underlying_symbol'], created_at=datetime.fromisoformat(data['created_at']))
    
    def _dict_to_metrics(self, data: dict) -> StrategyMetrics:
        return StrategyMetrics(**data)
    
    def _row_to_trade(self, row: tuple) -> TradeRecord:
        """Convert database row to trade record."""
        return TradeRecord(id=row[0], strategy=self._dict_to_strategy(json.loads(row[1])),
                          metrics=self._dict_to_metrics(json.loads(row[2])), entry_date=date.fromisoformat(row[3]),
                          status=row[4], closing_price=row[5], final_pnl=row[6])