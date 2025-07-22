# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

All Python commands must be run using `uv`:
- Run Python scripts: `uv run python script.py`
- Install dependencies: `uv pip install -r requirements.txt`
- Test configuration: `uv run python -c "from src.config import validate_config; validate_config(); print('Configuration valid')"`
- Test models: `uv run python -c "from src.models import StockQuote, OptionContract; print('Models imported successfully')"`
- Run tests: `uv run python -m pytest tests/ -v`
- CLI interface: `uv run python cli.py` (when implemented)
- Web interface: `uv run streamlit run app.py` (when implemented)

## Project Architecture

**OptionPilot** is an AI-powered options trading analysis MVP with a modular architecture:

### Core Components
- `src/models.py` - Validated data structures (StockQuote, OptionContract, OptionLeg, Strategy, StrategyMetrics, TradeRecord)
- `src/config.py` - Environment-based configuration management with fail-fast validation
- `src/market_data.py` - Alpha Vantage API integration (simplified single-file, 100 lines)
- Built around two-leg spread strategies only (MVP limitation)

### API Integration Strategy
- **Alpha Vantage API**: Stock quotes and options chain data for symbols (NVDA, TSLA, HOOD, CRCL)
- **OpenRouter API**: AI analysis using Claude 4 Sonnet for strategy interpretation and risk assessment
- All API keys managed through environment variables with validation

### Data Flow Architecture
1. **Market Data Layer**: Alpha Vantage integration (planned in `market_data.py`)
2. **Strategy Calculator**: Financial calculations engine (planned in `strategy_calculator.py`)
3. **AI Analysis Layer**: OpenRouter integration for strategy insights (planned in `ai_analyzer.py`)
4. **Persistence Layer**: SQLite-based trading journal (planned in `trading_journal.py`)

### Interface Architecture
- **Phase 1 (CLI)**: Command-line interface in `cli.py`
- **Phase 2 (Web)**: Streamlit web application in `app.py`

## Configuration Requirements

Environment setup requires `.env` file with:
```
ALPHA_VANTAGE_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
```

Use `config.validate_config()` to verify all required configuration before running main application logic.

## Development Constraints

- **Two-leg strategies only**: MVP scope limits strategies to maximum 2 legs
- **Predefined symbols**: Only NVDA, TSLA, HOOD, CRCL supported initially
- **Manual paper trading**: No real broker integration, manual position closing
- **Python 3.11+ required**: Uses modern Python features and type hints
- **File size limit**: Each source file must be <100 lines (MVP simplicity principle)

## Key Dependencies

- `httpx`: Async HTTP for API calls
- `pandas`: Options chain data manipulation
- `matplotlib`: Payoff diagram visualization
- `streamlit`: Web interface framework
- `python-dotenv`: Environment variable management