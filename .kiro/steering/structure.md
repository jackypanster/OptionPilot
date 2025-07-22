# Project Structure & Organization

## Directory Layout

```
OptionPilot/
├── README.md                    # Project overview and setup instructions
├── requirements.txt             # Python dependencies
├── .env.example                # Template for API configuration
├── .gitignore                  # Git ignore patterns
├── cli.py                      # CLI interface entry point (Milestone 1)
├── app.py                      # Streamlit web app entry point (Milestone 2)
├── models.py                   # Core data structures and models
├── market_data.py              # Alpha Vantage API integration
├── strategy_calculator.py      # Financial calculations engine
├── ai_analyzer.py              # OpenRouter AI integration
├── trading_journal.py          # SQLite persistence layer
├── config.py                   # Configuration management
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_market_data.py
│   ├── test_strategy_calculator.py
│   ├── test_ai_analyzer.py
│   ├── test_trading_journal.py
│   ├── test_cli.py
│   └── test_end_to_end.py
└── docs/                       # Additional documentation
    ├── CALCULATIONS.md
    ├── AI_INTEGRATION.md
    ├── TRADING_JOURNAL.md
    ├── CLI_USAGE.md
    ├── WEB_INTERFACE.md
    ├── USER_GUIDE.md
    └── DEPLOYMENT.md
```

## Core Modules

### Data Layer (`models.py`)
- `StockQuote`: Stock price and timestamp data
- `OptionContract`: Individual option contract details
- `OptionLeg`: Strategy leg with action and contract
- `Strategy`: Complete strategy with multiple legs
- `StrategyMetrics`: Calculated financial metrics
- `TradeRecord`: Trading journal entry

### Business Logic Layer
- `market_data.py`: External API data retrieval
- `strategy_calculator.py`: Financial calculations and payoff diagrams
- `ai_analyzer.py`: AI-powered strategy analysis
- `trading_journal.py`: Local data persistence

### Presentation Layer
- `cli.py`: Command-line interface for core functionality
- `app.py`: Streamlit web interface for enhanced UX

## File Naming Conventions

- **Python modules:** lowercase with underscores (`market_data.py`)
- **Classes:** PascalCase (`StrategyCalculator`)
- **Functions/methods:** lowercase with underscores (`calculate_max_profit`)
- **Constants:** UPPERCASE with underscores (`MAX_API_RETRIES`)
- **Test files:** prefix with `test_` (`test_strategy_calculator.py`)

## Import Organization

```python
# Standard library imports first
import datetime
from dataclasses import dataclass
from typing import List, Optional

# Third-party imports second
import httpx
import pandas as pd
import matplotlib.pyplot as plt

# Local imports last
from models import StockQuote, Strategy
from config import get_api_key
```

## Configuration Management

- **API Keys:** Store in `.env` file, load via `python-dotenv`
- **Default Settings:** Define in `config.py` with environment overrides
- **Database:** SQLite file location configurable via environment variables

## uv Project Management

**Important:** Always use `uv run` prefix for all Python commands to ensure proper virtual environment activation and dependency management.

```bash
# Correct way to run Python commands
uv run python cli.py
uv run streamlit run app.py
uv run python -m pytest tests/
uv run python -c "import models"

# Don't run Python directly without uv
python cli.py  # ❌ Wrong
streamlit run app.py  # ❌ Wrong
```

## Testing Structure

- **Unit Tests:** One test file per module (`test_market_data.py`)
- **Integration Tests:** Cross-module functionality testing
- **End-to-End Tests:** Complete user workflow validation (`uv run python -m pytest tests/test_end_to_end.py`)
- **Mock Data:** Consistent test data for API responses and calculations