# Technology Stack & Build System

## Core Technologies

**Backend Language:** Python 3.11+  
**Package Manager:** uv for dependency and virtual environment management  
**Architecture:** Modular design with clear separation of data access, business logic, and presentation layers

## Key Dependencies

- **HTTP Client:** httpx for async API calls
- **Data Processing:** pandas for options chain manipulation  
- **Visualization:** matplotlib for payoff diagrams
- **Web Framework:** Streamlit for rapid MVP development
- **Database:** SQLite for local trading journal persistence
- **Configuration:** python-dotenv for API key management

## External Integrations

- **Market Data:** Alpha Vantage API for stock quotes and options chains
- **AI Analysis:** OpenRouter API with Claude 4 Sonnet model

## Common Commands

### Environment Setup
```bash
# Install uv package manager first
# Create virtual environment
uv venv

# Install dependencies  
uv pip install -r requirements.txt

# Configure API keys in .env file
```

### Development Workflow
```bash
# Run CLI interface (Milestone 1)
python cli.py

# Run web application (Milestone 2)  
streamlit run app.py

# Run tests
python -m pytest tests/ -v

# Run specific test modules
python -m pytest tests/test_strategy_calculator.py -v
```

### Testing Commands
```bash
# Test model imports
python -c "from models import StockQuote, OptionContract; print('Models imported successfully')"

# Test market data service
python -c "from market_data import MarketDataService; svc = MarketDataService(); print(svc.get_stock_quote('NVDA'))"

# Test calculator
python -c "from strategy_calculator import StrategyCalculator; calc = StrategyCalculator(); print('Calculator ready')"
```

## Development Standards

### Code Quality Principles
- **Single Responsibility:** Each file should have one clear purpose, keep under 100 lines of code
- **Fail Fast:** Throw exceptions immediately when errors occur, expose full stack traces, no try/catch to hide errors
- **Minimal Code:** Write the least code necessary to implement functionality, avoid redundancy and over-engineering
- **Type Annotations:** All functions must have complete type hints for parameters and return values
- **Pure Functions:** Prefer functions without side effects when possible, easier to test and reason about
- **Dependency Injection:** Avoid hardcoded dependencies, pass them as parameters for better testability

### Error Handling Philosophy
```python
# Good - fail fast with clear error
def calculate_max_profit(strategy: Strategy) -> float:
    if not strategy.legs:
        raise ValueError("Strategy must have at least one leg")
    # calculation logic...

# Bad - hiding errors with fallbacks
def calculate_max_profit(strategy: Strategy) -> float:
    try:
        # calculation logic...
    except Exception:
        return 0.0  # Don't do this!
```

### Data Integrity & Validation
- **Input Validation:** All external inputs must be strictly validated (stock symbols, price ranges, dates)
- **Financial Data Validation:** Validate bid/ask spreads, option prices, and expiration dates for reasonableness
- **Idempotency:** Same inputs should always produce identical outputs, no random behavior in calculations
- **Data Consistency:** Ensure options chain data is internally consistent (bid <= ask, valid strikes, etc.)

### Logging & Debugging
- **Structured Logging:** Use structured logs with consistent format for all operations
- **Critical Path Logging:** Log all API calls, calculations, and user actions with timestamps
- **Error Context:** Include full context in error messages (input values, operation being performed)
- **Performance Logging:** Track API response times and calculation performance

### Financial Calculation Standards
```python
# Good - explicit validation and clear error messages
def validate_option_price(bid: float, ask: float, strike: float) -> None:
    if bid < 0:
        raise ValueError(f"Bid price {bid} cannot be negative")
    if ask < bid:
        raise ValueError(f"Ask price {ask} cannot be less than bid {bid}")
    if strike <= 0:
        raise ValueError(f"Strike price {strike} must be positive")

# Good - immutable calculations with clear inputs/outputs
def calculate_breakeven(net_premium: float, strike_diff: float) -> float:
    if strike_diff == 0:
        raise ValueError("Strike difference cannot be zero")
    return net_premium / strike_diff
```

### Technical Standards
- **API Integration:** Use exponential backoff for rate limiting and proper timeout handling
- **Testing:** Write unit tests for all core functionality with mocked external dependencies
- **Documentation:** Include docstrings for all methods and maintain README with setup instructions
- **Configuration:** Store sensitive data (API keys) in .env files, never commit to version control
- **Magic Numbers:** All constants should be named and configurable, no hardcoded values in business logic