# OptionPilot User Guide

Complete guide for using OptionPilot, the AI-powered options strategy analyzer for individual investors.

## Table of Contents

1. [Quick Start](#quick-start)
2. [CLI Interface Usage](#cli-interface-usage)
3. [Web Interface Usage](#web-interface-usage)
4. [Core Features Guide](#core-features-guide)
5. [Troubleshooting](#troubleshooting)
6. [FAQ](#faq)

---

## Quick Start

### Prerequisites

- **Python 3.11+** installed on your system
- **uv package manager** ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- API keys for Alpha Vantage and OpenRouter

### Step 1: Installation

```bash
# Clone the repository
git clone https://github.com/jackypanster/OptionPilot.git
cd OptionPilot

# Install dependencies
uv pip install -r requirements.txt
```

### Step 2: API Configuration

1. **Get Alpha Vantage API key:**
   - Visit [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
   - Sign up for free account (25 requests/day limit)
   - Copy your API key

2. **Get OpenRouter API key:**
   - Visit [OpenRouter](https://openrouter.ai/keys)
   - Create account and generate API key
   - Copy your API key

3. **Configure environment:**
   ```bash
   # Create .env file
   cp .env.example .env
   
   # Edit .env file with your keys:
   ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
   OPENROUTER_API_KEY=your_openrouter_key_here
   ```

### Step 3: First Run

```bash
# Test configuration
uv run python -c "from src.config import validate_config; validate_config(); print('✅ Configuration valid')"

# Try CLI help
uv run python cli.py --help

# Launch web interface
uv run streamlit run app.py
```

---

## CLI Interface Usage

The CLI provides a command-line interface for all core functions. Perfect for scripting and quick analysis.

### Available Commands

```bash
# Get help
uv run python cli.py --help

# Available commands:
# - get-quote      Get real-time stock price
# - get-options    Get options chain data
# - build-strategy Interactive strategy builder
# - analyze-strategy AI analysis of current strategy
# - save-trade     Save strategy to journal
# - list-trades    View all saved trades
# - close-trade    Close position with P&L calculation
```

### Complete Workflow Example

#### 1. Check Stock Price
```bash
uv run python cli.py get-quote NVDA
# Output: 📊 NVDA: $875.28
```

#### 2. View Options Chain
```bash
uv run python cli.py get-options NVDA 2024-03-15
# Output: 
# 📈 NVDA 2024-03-15:
#   CALL $145.0: $11.80-$12.20
#   CALL $150.0: $8.90-$9.30
#   PUT $140.0: $5.00-$5.40
```

#### 3. Build Strategy Interactively
```bash
uv run python cli.py build-strategy
# Interactive prompts:
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

#### 4. Get AI Analysis
```bash
uv run python cli.py analyze-strategy
# Current stock price: 150.25
# 🤖 This is a bull call spread strategy that profits from moderate upward movement
# 📈 Strategy expects NVDA to rise moderately and stay above $150.54 by expiration
# ⚠️ Maximum loss of $5.40 occurs if stock closes below $145 at expiration
```

#### 5. Save to Trading Journal
```bash
uv run python cli.py save-trade
# Output: 💾 Saved! ID: 1
```

#### 6. View Trading Journal
```bash
uv run python cli.py list-trades
# Output:
# 📋 Trading Journal:
#   🟢 1 NVDA 2024-01-15 - Open
#   🔴 2 TSLA 2024-01-14 - $45.60
#   🟢 3 HOOD 2024-01-13 - Open
```

#### 7. Close Position
```bash
uv run python cli.py close-trade --id 1 --price 158.50
# Output: 🔒 Closed! P&L: $994.60
```

---

## Web Interface Usage

The web interface provides a user-friendly GUI with interactive forms and real-time calculations.

### Launching Web Interface

```bash
uv run streamlit run app.py
# Opens in browser at http://localhost:8501
```

### Strategy Builder Tab

#### 1. Stock Selection
- **Sidebar**: Choose from supported symbols (NVDA, TSLA, HOOD, CRCL)
- **Get Quote**: Click button to fetch current stock price
- Current price displays in info box when fetched

#### 2. Building Your Strategy

**Expiration Date:**
- Select expiration date from date picker
- Default: 30 days from today

**Leg 1 Configuration:**
- **Action**: Choose "buy" or "sell"
- **Option Type**: Choose "call" or "put"
- **Strike Price**: Enter strike price (default: 150.0)
- **Bid/Ask**: Enter current bid/ask prices (defaults: 8.50/8.70)

**Optional Leg 2:**
- Check "Add second leg" to create spreads
- Same configuration options as Leg 1
- Defaults for leg 2: Strike 155.0, Bid 6.80, Ask 7.20

#### 3. Real-time Calculations
When you click "Build Strategy":
- **Net Premium**: Shows credit (+) or debit (-) 
- **Max Profit/Loss**: Theoretical maximum outcomes
- **Breakeven Points**: Stock price for zero P&L
- **Margin Requirement**: Capital needed
- **Return on Margin**: Percentage return potential

#### 4. Payoff Diagram
- Automatically generates interactive chart
- Shows profit/loss across stock price range
- Current stock price marked with vertical line
- Breakeven line at zero P&L

#### 5. AI Strategy Analysis
- **Analysis Button**: Click "Analyze Strategy with AI"
- **Loading State**: Shows spinner while processing
- **Results Display**:
  - **Strategy Interpretation**: What type of strategy this is
  - **Market Outlook**: Market conditions that favor this strategy
  - **Risk Warning**: Primary risks and loss scenarios
- **Session Persistence**: Results stay visible throughout session

### Trading Journal Tab

#### Overview Dashboard
- **Total Trades**: Count of all saved strategies
- **Open Positions**: Number of active trades
- **Closed Positions**: Number of completed trades
- **Total P&L**: Sum of all closed position profits/losses

#### Trade History
- **Expandable Cards**: Click to view detailed trade information
- **Trade Details**: Shows all legs, strikes, premiums, and calculated metrics
- **Status Indicator**: Green (Open) or Red (Closed)

#### Position Management
For open trades:
- **Closing Price Input**: Enter current stock price
- **Close Trade Button**: Calculates final P&L and updates status
- **Automatic P&L**: System calculates profit/loss based on strategy type

---

## Core Features Guide

### Strategy Types Supported

OptionPilot supports all single and two-leg strategies:

#### Single Leg Strategies
- **Long Call**: Buy call option (unlimited upside)
- **Short Call**: Sell call option (limited profit, unlimited risk)
- **Long Put**: Buy put option (profit from decline)
- **Short Put**: Sell put option (collect premium)

#### Two-Leg Spreads
- **Bull Call Spread**: Buy lower strike call, sell higher strike call
- **Bear Put Spread**: Buy higher strike put, sell lower strike put
- **Credit Spreads**: Collect premium upfront
- **Debit Spreads**: Pay premium upfront

### Financial Calculations Explained

#### Net Premium
- **Credit (+)**: You receive money upfront
- **Debit (-)**: You pay money upfront
- Calculated using bid prices for sells, ask prices for buys

#### Maximum Profit
- **Single Long Call**: Unlimited (shows 99999)
- **Single Short**: Premium received
- **Spreads**: Either premium received (credit) or spread width minus premium paid (debit)

#### Maximum Loss
- **Single Long**: Premium paid
- **Single Short**: Unlimited (shows 99999)
- **Spreads**: Either spread width minus premium received (credit) or premium paid (debit)

#### Breakeven Points
- **Single Options**: Strike ± premium per share
- **Spreads**: Adjusted for net premium across the spread

#### Margin Requirement
- **Credit Spreads**: Maximum loss amount
- **Debit Spreads**: Premium paid

### AI Analysis Features

#### Analysis Components
1. **Strategy Identification**: Names the strategy type
2. **Market Outlook**: Explains profit conditions
3. **Risk Assessment**: Highlights primary risks

#### AI Model Configuration
- **Model**: Claude 3.5 Sonnet (optimized for financial analysis)
- **Temperature**: 0.3 (balanced creativity and consistency)
- **Max Tokens**: 300 (concise analysis)

---

## Troubleshooting

### Common Issues

#### Configuration Problems
**Error**: "Missing ALPHA_VANTAGE_API_KEY in environment variables"
- **Solution**: Check .env file exists and contains valid API key
- **Verify**: Run `uv run python -c "from src.config import validate_config; validate_config()"`

#### API Rate Limits
**Error**: "Rate limit exceeded: 25 requests per day limit reached"
- **Cause**: Alpha Vantage free tier limit
- **Solutions**:
  - Wait for next day reset
  - Upgrade to premium plan
  - Use cached data when possible

#### Network Issues
**Error**: Connection timeouts or request failures
- **Check**: Internet connection
- **Try**: Increase timeout in .env: `API_TIMEOUT=60`
- **Verify**: API service status

#### Symbol Not Supported
**Error**: "Unsupported symbol: AAPL"
- **Supported**: Only NVDA, TSLA, HOOD, CRCL (MVP limitation)
- **Solution**: Use one of the supported symbols

#### Import Errors
**Error**: Module import failures
- **Solution**: Ensure dependencies installed: `uv pip install -r requirements.txt`
- **Check**: Python version 3.11+

### Debug Mode

For detailed troubleshooting:
```bash
# Enable debug logging
export PYTHONPATH=.
uv run python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from src.market_data import MarketDataService
service = MarketDataService()
# Detailed logs will show request/response
"
```

### File Permissions
If database issues occur:
```bash
# Check SQLite database permissions
ls -la trading_journal.db
# Ensure read/write access
chmod 644 trading_journal.db
```

---

## FAQ

### General Questions

**Q: Is this for real trading?**
A: No, OptionPilot is for paper trading and strategy analysis only. No real broker integration.

**Q: What strategies can I analyze?**
A: Single options (calls/puts) and two-leg spreads. MVP limitation prevents more complex strategies.

**Q: Do I need both API keys?**
A: Yes, Alpha Vantage for market data and OpenRouter for AI analysis are both required.

### Technical Questions

**Q: Why only 4 stock symbols?**
A: MVP scope focuses on popular symbols (NVDA, TSLA, HOOD, CRCL) to keep complexity manageable.

**Q: Can I change the AI model?**
A: No, the model is hardcoded to Claude 3.5 Sonnet for optimal financial analysis (MVP design).

**Q: How accurate are the calculations?**
A: Very accurate - uses standard options pricing formulas with 2 decimal precision.

**Q: Can I export my trading journal?**
A: Currently no export feature. Data stored in SQLite database `trading_journal.db`.

### Performance Questions

**Q: Why is the web interface slow?**
A: Usually due to API calls. Stock quotes and AI analysis require external API requests.

**Q: How much does this cost to run?**
A: Free with API limits. Alpha Vantage free tier (25 requests/day), OpenRouter pay-per-use.

**Q: Can I run this offline?**
A: No, requires internet for market data and AI analysis.

### Troubleshooting

**Q: Web interface won't start?**
A: Check if port 8501 is available. Try: `uv run streamlit run app.py --server.port 8502`

**Q: CLI commands not working?**
A: Ensure you're in project directory and using `uv run python cli.py` prefix.

**Q: AI analysis fails?**
A: Check OpenRouter API key and account balance. AI analysis requires API credits.

---

## Support and Resources

### Documentation
- **README.md**: Project overview and setup
- **CLI_USAGE.md**: Detailed CLI command reference
- **AI_INTEGRATION.md**: AI analysis setup and usage
- **CALCULATIONS.md**: Financial formula explanations

### Getting Help
- Check error messages carefully
- Verify API key configuration
- Ensure supported symbols only
- Review this user guide FAQ section

### Contributing
This is an MVP project focused on core functionality. Complex features and additional symbols are outside the current scope.

---

*Happy Trading! 📈 (Paper trading only)*