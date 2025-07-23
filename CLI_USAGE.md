# CLI Usage Guide

This document provides comprehensive guidance for using the OptionPilot CLI interface.

## Overview

The OptionPilot CLI provides a command-line interface for options trading analysis, integrating all core components: market data, strategy calculator, AI analyzer, and trading journal.

## Installation & Setup

```bash
# Ensure all dependencies are installed
uv pip install -r requirements.txt

# Configure API keys in .env file
ALPHA_VANTAGE_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here

# Test configuration
uv run python -c "from src.config import validate_config; validate_config()"
```

## Available Commands

### Help Command
```bash
# Show all available commands
uv run python cli.py --help

# Get help for specific command
uv run python cli.py get-quote --help
```

### Market Data Commands

#### Get Stock Quote
```bash
# Get real-time stock price
uv run python cli.py get-quote NVDA
uv run python cli.py get-quote TSLA
uv run python cli.py get-quote HOOD
uv run python cli.py get-quote CRCL

# Example output:
# 📊 NVDA: $875.28
```

#### Get Options Chain
```bash
# Get options chain for specific expiration
uv run python cli.py get-options NVDA 2024-03-15
uv run python cli.py get-options TSLA 2024-04-19

# Example output:
# 📈 NVDA 2024-03-15:
#   CALL $145.0: $11.80-$12.20
#   CALL $150.0: $8.90-$9.30
#   PUT $140.0: $5.00-$5.40
```

### Strategy Building Commands

#### Build Strategy (Interactive)
```bash
# Interactive strategy builder
uv run python cli.py build-strategy

# Example interaction:
# 🔧 Strategy Builder
# Symbol: NVDA
# Expiration (YYYY-MM-DD): 2024-03-15
# --- Leg 1 ---
# Action (buy/sell): buy
# Type (call/put): call
# Strike: 145.0
# Bid: 11.80
# Ask: 12.20
# Add second leg? [y/N]: y
# --- Leg 2 ---
# Action (buy/sell): sell
# Type (call/put): call
# Strike: 155.0
# Bid: 6.80
# Ask: 7.20
#
# 📊 Premium: $-5.40 | P/L: $994.60/$5.40
# ✅ Built! Use 'analyze-strategy' or 'save-trade'
```

#### Analyze Strategy with AI
```bash
# Analyze current strategy (after building)
uv run python cli.py analyze-strategy

# Example interaction:
# Current stock price: 150.25
# 🤖 This is a bull call spread strategy that profits from moderate upward movement
# 📈 Strategy expects NVDA to rise moderately and stay above $150.54 by expiration
# ⚠️ Maximum loss of $5.40 occurs if stock closes below $145 at expiration
```

### Trading Journal Commands

#### Save Trade
```bash
# Save current strategy to journal (after building)
uv run python cli.py save-trade

# Example output:
# 💾 Saved! ID: 1
```

#### List Trades
```bash
# Show all trades in journal
uv run python cli.py list-trades

# Example output:
# 📋 Trading Journal:
#   🟢 1 NVDA 2024-01-15 - Open
#   🔴 2 TSLA 2024-01-14 - $45.60
#   🟢 3 HOOD 2024-01-13 - Open
```

#### Close Trade
```bash
# Close trade with manual closing price
uv run python cli.py close-trade --id 1 --price 158.50

# Example output:
# 🔒 Closed! P&L: $994.60
```

## Complete Workflow Examples

### Example 1: Bull Call Spread Analysis
```bash
# Step 1: Check current stock price
uv run python cli.py get-quote NVDA

# Step 2: Check options chain
uv run python cli.py get-options NVDA 2024-03-15

# Step 3: Build strategy interactively
uv run python cli.py build-strategy
# Input: NVDA, 2024-03-15, buy call 145, sell call 155

# Step 4: Get AI analysis
uv run python cli.py analyze-strategy
# Input: current price 150.25

# Step 5: Save to journal
uv run python cli.py save-trade

# Step 6: View journal
uv run python cli.py list-trades

# Step 7: Close when ready
uv run python cli.py close-trade --id 1 --price 158.50
```

### Example 2: Single Long Call
```bash
# Build single-leg strategy
uv run python cli.py build-strategy
# Input: HOOD, 2024-04-19, buy call 25.0, no second leg

# Analyze
uv run python cli.py analyze-strategy
# Input: current price 24.50

# Save and track
uv run python cli.py save-trade
uv run python cli.py list-trades
```

### Example 3: Credit Put Spread
```bash
# Build credit spread
uv run python cli.py build-strategy
# Input: CRCL, 2024-06-21, sell put 30.0, buy put 25.0

# Get AI insights
uv run python cli.py analyze-strategy
# Input: current price 28.50

# Journal management
uv run python cli.py save-trade
uv run python cli.py list-trades
uv run python cli.py close-trade --id 3 --price 31.00
```

## Command Reference

| Command | Arguments | Description |
|---------|-----------|-------------|
| `get-quote` | `SYMBOL` | Get real-time stock price |
| `get-options` | `SYMBOL DATE` | Get options chain for expiration date |
| `build-strategy` | _interactive_ | Build options strategy step-by-step |
| `analyze-strategy` | _interactive_ | AI analysis of current strategy |
| `save-trade` | _none_ | Save current strategy to journal |
| `list-trades` | _none_ | Show all journal entries |
| `close-trade` | `--id ID --price PRICE` | Close trade with manual price |

## Error Handling & Validation

### Input Validation (MVP Style)

The CLI includes basic input validation that follows MVP principles: **fail fast and crash immediately** when encountering invalid inputs. This is intentional - it's better to restart than hide problems.

#### Supported Stock Symbols
Only these symbols are supported:
- **NVDA** (NVIDIA)
- **TSLA** (Tesla) 
- **HOOD** (Robinhood)
- **CRCL** (Circle Internet Financial)

```bash
# Valid symbol - works
uv run python cli.py get-quote NVDA

# Invalid symbol - crashes immediately  
uv run python cli.py get-quote AAPL
# ValueError: Unsupported symbol: AAPL. Supported: NVDA, TSLA, HOOD, CRCL
```

### Common Errors

#### Unsupported Symbols
```bash
uv run python cli.py get-quote INVALID
# ValueError: Unsupported symbol: INVALID. Supported: NVDA, TSLA, HOOD, CRCL

uv run python cli.py get-options AAPL 2024-03-15  
# ValueError: Unsupported symbol: AAPL. Supported: NVDA, TSLA, HOOD, CRCL
```

#### API Rate Limits
```bash
uv run python cli.py get-quote NVDA
# ❌ Rate limit exceeded: 25 requests per day limit reached
```

#### Missing Configuration
```bash
# ❌ Missing ALPHA_VANTAGE_API_KEY in environment variables
```

#### Invalid Dates
```bash
uv run python cli.py build-strategy
# Input invalid date format
# ❌ Invalid date
```

#### Strategy Not Built
```bash
uv run python cli.py analyze-strategy
# ❌ Build strategy first
```

#### Non-existent Trade
```bash
uv run python cli.py close-trade --id 999 --price 100
# ❌ Trade 999 not found or already closed
```

### MVP Troubleshooting

1. **Validation Crashes**: Restart the CLI - this is expected behavior for invalid inputs
2. **API Key Issues**: Verify `.env` file contains valid API keys
3. **Network Errors**: Check internet connection and API service status  
4. **Rate Limits**: Wait for rate limit reset or upgrade API plan
5. **Database Issues**: Check file permissions for SQLite database

### MVP Philosophy
- **Crashes are features**: Invalid inputs should crash immediately to expose problems
- **No complex error recovery**: Simply restart the CLI when something fails
- **Transparent errors**: Technical error messages help with debugging
- **Fail fast**: Better to crash early than continue with bad data

## Integration Testing

```bash
# Run CLI integration tests
uv run python -m pytest tests/test_cli.py -v

# Test specific functionality
uv run python -m pytest tests/test_cli.py::TestCLIIntegration::test_cli_help_command -v

# Test end-to-end workflow
uv run python -m pytest tests/test_cli.py::TestCLIEndToEndWorkflow::test_simulated_strategy_workflow -v
```

## Best Practices

### Strategy Building
1. **Check Current Prices**: Use `get-quote` before building strategies
2. **Review Options Chain**: Use `get-options` to see available strikes and prices
3. **Realistic Pricing**: Use actual bid/ask prices from options chain
4. **Validate Strategy**: Review calculated metrics before proceeding

### Journal Management  
1. **Save After Analysis**: Always save strategies after AI analysis
2. **Track Performance**: Regularly review `list-trades` output
3. **Close Methodically**: Use realistic closing prices for P&L accuracy
4. **Review Results**: Analyze closed trades for performance patterns

### API Usage
1. **Respect Rate Limits**: Alpha Vantage free tier has 25 requests/day
2. **Cache Results**: Save frequently-used data to avoid repeated API calls
3. **Monitor Costs**: Track OpenRouter usage for AI analysis features
4. **Backup Data**: SQLite journal database should be backed up regularly

## Advanced Usage

### Batch Operations
```bash
# Check multiple symbols
for symbol in NVDA TSLA HOOD CRCL; do
  uv run python cli.py get-quote $symbol
done

# Build and save multiple strategies
# (requires manual interaction for each)
```

### Data Export
```bash
# Export journal data (SQLite query)
sqlite3 trading_journal.db "SELECT * FROM trades;"
```

### Configuration Validation
```bash
# Test all configurations
uv run python -c "
from src.config import validate_config;
from src.market_data import MarketDataService;
from src.ai_analyzer import AIAnalyzer;
from src.trading_journal import TradingJournal;
validate_config();
print('✅ All systems operational')
"
```