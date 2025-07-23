# Trading Journal Documentation

This document explains the paper trading journal system for tracking options strategy performance.

## Overview

The trading journal provides a SQLite-based persistence layer for paper trading records, allowing users to:
- Save strategies as trade records
- Track open and closed positions
- Calculate final P&L based on closing prices
- Maintain trading history across sessions

## Database Schema

### Trades Table

```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_data TEXT NOT NULL,        -- JSON serialized Strategy object
    metrics_data TEXT NOT NULL,         -- JSON serialized StrategyMetrics object
    entry_date TEXT NOT NULL,           -- ISO format date (YYYY-MM-DD)
    status TEXT NOT NULL DEFAULT 'open', -- 'open' or 'closed'
    closing_price REAL NULL,            -- Stock price when position was closed
    final_pnl REAL NULL                 -- Calculated profit/loss at closing
);
```

### Data Storage Format

**Strategy Data (JSON):**
```json
{
    "underlying_symbol": "NVDA",
    "created_at": "2024-01-15T10:30:00",
    "legs": [
        {
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
        }
    ]
}
```

**Metrics Data (JSON):**
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

## Usage

### Initialize Journal

```python
from src.trading_journal import TradingJournal

# Creates SQLite database if it doesn't exist
journal = TradingJournal()
```

### Save a Trade

```python
# Save strategy as new trade record
trade_record = journal.save_trade(strategy, metrics)

print(f"Trade saved with ID: {trade_record.id}")
print(f"Status: {trade_record.status}")  # 'open'
```

### Retrieve All Trades

```python
# Get all trades ordered by entry date (newest first)
all_trades = journal.get_all_trades()

for trade in all_trades:
    print(f"ID: {trade.id}")
    print(f"Symbol: {trade.strategy.underlying_symbol}")
    print(f"Entry Date: {trade.entry_date}")
    print(f"Status: {trade.status}")
    print(f"Net Premium: ${trade.metrics.net_premium}")
    if trade.status == 'closed':
        print(f"Final P&L: ${trade.final_pnl}")
```

### Close a Trade

```python
# Close trade with manual closing price
closed_trade = journal.close_trade(trade_id=1, closing_price=152.50)

print(f"Trade closed at ${closed_trade.closing_price}")
print(f"Final P&L: ${closed_trade.final_pnl}")
```

## P&L Calculation Logic

### Credit Spreads (Net Premium > 0)

For credit spreads, the trader receives money upfront and profits if the spread expires worthless.

**Logic:**
- If stock price is between the strikes → Keep full credit (max profit)
- If stock price is outside the strikes → Pay the difference (partial to max loss)

**Example - Bull Put Credit Spread:**
```python
# Sell 150 Put, Buy 140 Put for $2.00 credit
# If NVDA closes at $145 (between strikes) → Keep $2.00 credit
# If NVDA closes at $135 (below both strikes) → Lose $8.00 (spread width - credit)
```

### Debit Spreads (Net Premium < 0)

For debit spreads, the trader pays money upfront and profits if the spread moves in-the-money.

**Logic:**
- If stock price is favorable to the spread → Profit up to max profit
- If stock price is unfavorable → Lose the premium paid

**Example - Bull Call Debit Spread:**
```python
# Buy 145 Call, Sell 155 Call for $5.40 debit
# If NVDA closes at $160 (above both strikes) → Profit $4.60 (spread width - debit)
# If NVDA closes at $140 (below both strikes) → Lose $5.40 (premium paid)
```

### Single Leg Positions

**Long Options:**
- Profit = max(0, intrinsic_value) - premium_paid
- Loss = premium_paid (if expires worthless)

**Short Options:**
- Profit = premium_received (if expires worthless)
- Loss = premium_received - intrinsic_value (if assigned)

## Configuration

### Database Location

Default: `trading_journal.db` in project root

Override with environment variable:
```bash
DATABASE_PATH=/path/to/custom/journal.db
```

### Connection Management

The journal uses SQLite with:
- Automatic table creation on first use
- Context managers for connection safety
- Transaction rollback on errors

## Error Handling

### Common Exceptions

**TradingJournalError:** Base exception for journal operations

**Scenarios:**
- Trade not found when closing
- Trade already closed
- Database connection issues
- Invalid data serialization

**Example:**
```python
try:
    journal.close_trade(999, 150.0)
except TradingJournalError as e:
    print(f"Error: {e}")  # "Trade 999 not found or already closed"
```

## Data Validation

### Strategy Validation

Before saving, the journal validates:
- Strategy has valid legs
- All option contracts have required fields
- Dates are properly formatted
- Numeric values are valid

### Metrics Validation

Metrics are validated for:
- Numeric types for all financial values
- Non-empty breakeven points list
- Reasonable value ranges

## Performance Considerations

### Database Optimization

- Primary key index on trade ID
- Date-based queries for recent trades
- JSON storage for flexible schema evolution

### Memory Management

- Lazy loading of trade data
- Connection pooling for concurrent access
- Automatic cleanup of database connections

## Testing

### Unit Tests

Comprehensive test coverage includes:
- CRUD operations (Create, Read, Update, Delete)
- P&L calculation accuracy
- Error handling scenarios
- Data persistence across sessions

### Test Examples

```python
def test_save_and_retrieve_trade():
    journal = TradingJournal()
    
    # Save trade
    saved_trade = journal.save_trade(strategy, metrics)
    assert saved_trade.id is not None
    assert saved_trade.status == 'open'
    
    # Retrieve trade
    all_trades = journal.get_all_trades()
    assert len(all_trades) >= 1
    assert all_trades[0].id == saved_trade.id

def test_close_trade_pnl_calculation():
    journal = TradingJournal()
    
    # Save and close trade
    saved_trade = journal.save_trade(bull_call_spread, metrics)
    closed_trade = journal.close_trade(saved_trade.id, 160.0)
    
    # Verify P&L calculation
    assert closed_trade.status == 'closed'
    assert closed_trade.final_pnl == metrics.max_profit
```

## Integration with UI

### CLI Interface

```bash
# List all trades
python cli.py list-trades

# Close a trade
python cli.py close-trade --id 1 --price 152.50
```

### Web Interface

The Streamlit web app provides:
- Trade history table with sorting/filtering
- Trade detail views with all metrics
- Close trade interface with P&L preview
- Performance analytics and charts

## Backup and Recovery

### Database Backup

```bash
# Create backup
cp trading_journal.db trading_journal_backup_$(date +%Y%m%d).db

# Restore from backup
cp trading_journal_backup_20240115.db trading_journal.db
```

### Data Export

```python
# Export trades to CSV
import pandas as pd

trades = journal.get_all_trades()
df = pd.DataFrame([{
    'id': t.id,
    'symbol': t.strategy.underlying_symbol,
    'entry_date': t.entry_date,
    'status': t.status,
    'net_premium': t.metrics.net_premium,
    'final_pnl': t.final_pnl
} for t in trades])

df.to_csv('trades_export.csv', index=False)
```

## Future Enhancements

Potential improvements:
- Trade categories and tags
- Performance analytics and reporting
- Import/export functionality
- Multi-user support with user accounts
- Integration with real broker APIs
- Automated expiration handling
- Risk management alerts