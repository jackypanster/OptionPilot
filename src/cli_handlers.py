"""
CLI command handlers for OptionPilot.

Contains the implementation logic for CLI commands to keep cli.py under 100 lines.
"""

import click
from datetime import datetime
from .market_data import MarketDataService, MarketDataError
from .strategy_calculator import StrategyCalculator
from .ai_analyzer import AIAnalyzer, AIAnalysisError
from .trading_journal import TradingJournal, TradingJournalError
from .models import Strategy, OptionLeg, OptionContract
from .config import ConfigError, get_supported_symbols


def validate_symbol(symbol):
    """Validate stock symbol is supported."""
    if symbol.upper() not in get_supported_symbols():
        raise ValueError(f"Unsupported symbol: {symbol.upper()}. Supported: {', '.join(get_supported_symbols())}")


def handle_get_quote(symbol):
    """Handle get-quote command."""
    validate_symbol(symbol)
    try:
        quote = MarketDataService().get_stock_quote(symbol.upper())
        click.echo(f"📊 {quote.symbol}: ${quote.price:.2f}")
    except (MarketDataError, ConfigError) as e:
        click.echo(f"❌ {e}", err=True)


def handle_get_options(symbol, date):
    """Handle get-options command."""
    validate_symbol(symbol)
    try:
        exp_date = datetime.strptime(date, '%Y-%m-%d').date()
        options = MarketDataService().get_options_chain(symbol.upper(), exp_date)
        click.echo(f"📈 {symbol.upper()} {date}:")
        for opt in options[:6]:
            click.echo(f"  {opt.option_type.upper()} ${opt.strike}: ${opt.bid}-${opt.ask}")
    except (MarketDataError, ConfigError, ValueError) as e:
        click.echo(f"❌ {e}", err=True)


def handle_build_strategy():
    """Handle build-strategy command."""
    click.echo("🔧 Strategy Builder")
    symbol = click.prompt("Symbol").upper()
    validate_symbol(symbol)
    
    try:
        expiration = datetime.strptime(click.prompt("Expiration (YYYY-MM-DD)"), '%Y-%m-%d').date()
    except ValueError:
        return click.echo("❌ Invalid date")
    
    legs = []
    for i in range(2):
        if i == 1 and not click.confirm("Add second leg?"):
            break
        click.echo(f"--- Leg {i + 1} ---")
        legs.append(OptionLeg(
            action=click.prompt("Action", type=click.Choice(['buy', 'sell'])),
            contract=OptionContract(
                symbol=symbol, expiration=expiration,
                option_type=click.prompt("Type", type=click.Choice(['call', 'put'])),
                strike=click.prompt("Strike", type=float),
                bid=click.prompt("Bid", type=float),
                ask=click.prompt("Ask", type=float)
            )
        ))
    
    global current_strategy, current_metrics
    current_strategy = Strategy(legs=legs, underlying_symbol=symbol, created_at=datetime.now())
    current_metrics = StrategyCalculator().calculate_strategy_metrics(current_strategy)
    click.echo(f"📊 Premium: ${current_metrics.net_premium:.2f} | P/L: ${current_metrics.max_profit:.2f}/${current_metrics.max_loss:.2f}")
    click.echo("✅ Built! Use 'analyze-strategy' or 'save-trade'")


def handle_analyze_strategy():
    """Handle analyze-strategy command."""
    global current_strategy, current_metrics
    if not current_strategy:
        return click.echo("❌ Build strategy first")
    try:
        price = click.prompt("Current stock price", type=float)
        analysis = AIAnalyzer().analyze_strategy(current_strategy, current_metrics, price)
        click.echo(f"🤖 {analysis['interpretation']}")
        click.echo(f"📈 {analysis['market_outlook']}")
        click.echo(f"⚠️ {analysis['risk_warning']}")
    except (AIAnalysisError, ConfigError) as e:
        click.echo(f"❌ {e}", err=True)


def handle_save_trade():
    """Handle save-trade command."""
    global current_strategy, current_metrics
    if not current_strategy:
        return click.echo("❌ Build strategy first")
    try:
        trade = TradingJournal().save_trade(current_strategy, current_metrics)
        click.echo(f"💾 Saved! ID: {trade.id}")
    except TradingJournalError as e:
        click.echo(f"❌ {e}", err=True)


def handle_list_trades():
    """Handle list-trades command."""
    try:
        trades = TradingJournal().get_all_trades()
        if not trades:
            return click.echo("📝 No trades found")
        click.echo("📋 Trading Journal:")
        for t in trades:
            status = "🔴" if t.status == 'closed' else "🟢"
            pnl = f"${t.final_pnl:.2f}" if t.final_pnl else "Open"
            click.echo(f"  {status} {t.id} {t.strategy.underlying_symbol} {t.entry_date} - {pnl}")
    except TradingJournalError as e:
        click.echo(f"❌ {e}", err=True)


def handle_close_trade(trade_id, price):
    """Handle close-trade command."""
    try:
        trade = TradingJournal().close_trade(trade_id, price)
        click.echo(f"🔒 Closed! P&L: ${trade.final_pnl:.2f}")
    except TradingJournalError as e:
        click.echo(f"❌ {e}", err=True)


# Global variables to store current strategy state
current_strategy = None
current_metrics = None