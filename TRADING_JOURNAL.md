# Trading Journal Documentation

This document explains the trading journal functionality for paper trading record management.

## Overview

The TradingJournal provides SQLite-based persistence for paper trading records, allowing users to save strategies, track performance, and manually close positions with P&L calculations.

## Database Schema

### Trades Table
```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_data TEXT NOT NULL,           -- JSON serialized strategy
    metrics_data TEXT NOT NULL,            -- JSON serialized metrics
    entry_date TEXT NOT NULL,              -- Entry date (YYYY-MM-DD)
    status TEXT NOT NULL DEFAULT 'open',   -- 'open' or 'closed'
    closing_price REAL NULL,               -- Manual closing price
    final_pnl REAL NULL                    -- Calculated final P&L
);
```

## Usage Examples

### Basic Operations

```python
from src.trading_journal import TradingJournal
from src.models import Strategy, StrategyMetrics

# Initialize journal
journal = TradingJournal()

# Save a strategy as trade record
strategy = # ... your strategy object
metrics = # ... your calculated metrics
trade = journal.save_trade(strategy, metrics)
print(f"Saved trade ID: {trade.id}")

# Get all trades
all_trades = journal.get_all_trades()
for trade in all_trades:
    print(f"Trade {trade.id}: {trade.strategy.underlying_symbol} - {trade.status}")

# Close a trade with manual price
closed_trade = journal.close_trade(trade.id, closing_price=155.50)
print(f"Final P&L: ${closed_trade.final_pnl:.2f}")
```

### Complete Workflow Example

```python
from datetime import datetime, date
from src.trading_journal import TradingJournal
from src.models import Strategy, StrategyMetrics, OptionLeg, OptionContract

# Create bull call spread
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

strategy = Strategy(
    legs=[buy_leg, sell_leg],
    underlying_symbol='NVDA',
    created_at=datetime.now()
)

metrics = StrategyMetrics(
    net_premium=-5.40,
    max_profit=994.60,
    max_loss=5.40,
    breakeven_points=[150.54],
    margin_requirement=5.40,
    return_on_margin=18418.52
)

# Save to journal
journal = TradingJournal()
trade = journal.save_trade(strategy, metrics)

# Later: close the trade
final_trade = journal.close_trade(trade.id, closing_price=158.50)
print(f"Strategy closed with P&L: ${final_trade.final_pnl:.2f}")
```

## P&L Calculation Logic

### Credit Spreads (net_premium > 0)
- **Two-leg spreads**: Max loss if closing price between strikes, max profit otherwise
- **Single-leg**: Keep premium received

### Debit Spreads (net_premium < 0)  
- **Breakeven comparison**: Max profit if above breakeven, max loss if below
- **Fallback**: Use net premium if no breakeven points

### Examples

```python
# Credit spread: Sell $20 Put for $2.00 premium
# Closing at $22: Keep $2.00 (max profit)
# Closing at $18: Lose premium + intrinsic value

# Debit spread: Bull call spread with breakeven at $150.54
# Closing at $155: Max profit ($994.60)
# Closing at $145: Max loss ($5.40)
```

## Configuration

### Database Location
```python
# Default: trading_journal.db in current directory
# Configure via environment variable:
DATABASE_PATH=/path/to/your/journal.db
```

### Testing with Temporary Database
```python
import tempfile
import os
from src.trading_journal import TradingJournal

# Create temporary database for testing
with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
    temp_db_path = temp_db.name

# Mock database path
import src.trading_journal
original_get_path = src.trading_journal.get_database_path
src.trading_journal.get_database_path = lambda: temp_db_path

try:
    journal = TradingJournal()
    # ... test operations
finally:
    src.trading_journal.get_database_path = original_get_path
    os.unlink(temp_db_path)
```

## Data Serialization

### Strategy Storage
Strategies are stored as JSON with full contract details:
```json
{
  "underlying_symbol": "NVDA",
  "created_at": "2024-01-15T10:30:00",
  "legs": [{
    "action": "buy",
    "quantity": 1,
    "contract": {
      "symbol": "NVDA",
      "strike": 145.0,
      "expiration": "2024-03-15",
      "option_type": "call",
      "bid": 11.80,
      "ask": 12.20
    }
  }]
}
```

### Metrics Storage
Metrics are serialized directly from StrategyMetrics attributes:
```json
{
  "net_premium": -5.40,
  "max_profit": 994.60,
  "max_loss": 5.40,
  "breakeven_points": [150.54],
  "margin_requirement": 5.40,
  "return_on_margin": 18418.52
}
```

## Error Handling

### Common Errors
- **TradingJournalError**: Base exception for all journal operations
- **Trade not found**: Attempting to close non-existent trade ID
- **Already closed**: Attempting to close already closed trade
- **Database errors**: SQLite connection or schema issues

### Error Examples
```python
from src.trading_journal import TradingJournalError

try:
    journal.close_trade(999, 100.0)  # Non-existent trade
except TradingJournalError as e:
    print(f"Error: {e}")  # "Trade 999 not found or already closed"
```

## Testing

### Unit Tests
```bash
# Run all trading journal tests
uv run python -m pytest tests/test_trading_journal.py -v

# Test specific functionality
uv run python -m pytest tests/test_trading_journal.py::TestTradingJournal::test_save_trade_creates_record -v
```

### Integration Tests
```bash
# Test complete lifecycle
uv run python -m pytest tests/test_trading_journal.py::TestTradingJournalIntegration::test_complete_trade_lifecycle -v
```

## CLI Integration

The trading journal integrates with the CLI interface:
```bash
# Save current strategy to journal (future CLI command)
uv run python cli.py save-trade

# List all trades
uv run python cli.py list-trades

# Close a trade
uv run python cli.py close-trade --id 1 --price 155.50
```

## Performance Notes

- **SQLite**: Suitable for single-user desktop application
- **JSON Serialization**: Compact storage for complex strategy objects  
- **Atomic Operations**: Each trade operation is wrapped in transaction
- **File Size**: Typical trade record ~1KB, suitable for thousands of trades

## Future Enhancements

1. **Trade Categories**: Add strategy type categorization
2. **Performance Analytics**: Calculate win/loss ratios and returns
3. **Export Functionality**: CSV/Excel export for external analysis
4. **Backup/Sync**: Cloud synchronization capabilities
5. **Advanced P&L**: Time-decay and Greeks-aware calculations