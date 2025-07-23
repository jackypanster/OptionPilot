#!/usr/bin/env python3
"""CLI interface for OptionPilot - AI-powered options strategy analyzer."""

import click
from datetime import datetime
from src.market_data import MarketDataService, MarketDataError
from src.strategy_calculator import StrategyCalculator
from src.ai_analyzer import AIAnalyzer, AIAnalysisError
from src.trading_journal import TradingJournal, TradingJournalError
from src.models import Strategy, OptionLeg, OptionContract
from src.config import ConfigError, get_supported_symbols

current_strategy = None
current_metrics = None

@click.group()
@click.version_option()
def cli():
    """OptionPilot - AI-powered options strategy analyzer."""
    pass

@cli.command()
@click.argument('symbol')
def get_quote(symbol):
    """Get real-time stock quote for SYMBOL."""
    if symbol.upper() not in get_supported_symbols():
        raise ValueError(f"Unsupported symbol: {symbol.upper()}. Supported: {', '.join(get_supported_symbols())}")
    try:
        quote = MarketDataService().get_stock_quote(symbol.upper())
        click.echo(f"📊 {quote.symbol}: ${quote.price:.2f}")
    except (MarketDataError, ConfigError) as e:
        click.echo(f"❌ {e}", err=True)

@cli.command()
@click.argument('symbol')
@click.argument('date')
def get_options(symbol, date):
    """Get options chain for SYMBOL and DATE (YYYY-MM-DD)."""
    if symbol.upper() not in get_supported_symbols():
        raise ValueError(f"Unsupported symbol: {symbol.upper()}. Supported: {', '.join(get_supported_symbols())}")
    try:
        exp_date = datetime.strptime(date, '%Y-%m-%d').date()
        options = MarketDataService().get_options_chain(symbol.upper(), exp_date)
        click.echo(f"📈 {symbol.upper()} {date}:")
        for opt in options[:6]:
            click.echo(f"  {opt.option_type.upper()} ${opt.strike}: ${opt.bid}-${opt.ask}")
    except (MarketDataError, ConfigError, ValueError) as e:
        click.echo(f"❌ {e}", err=True)

@cli.command()
def build_strategy():
    """Interactive strategy builder."""
    global current_strategy, current_metrics
    click.echo("🔧 Strategy Builder")
    symbol = click.prompt("Symbol").upper()
    if symbol not in get_supported_symbols():
        raise ValueError(f"Unsupported symbol: {symbol}. Supported: {', '.join(get_supported_symbols())}")
    try:
        expiration = datetime.strptime(click.prompt("Expiration (YYYY-MM-DD)"), '%Y-%m-%d').date()
    except ValueError:
        return click.echo("❌ Invalid date")
    
    legs = []
    for i in range(2):
        if i == 1 and not click.confirm("Add second leg?"):
            break
        click.echo(f"--- Leg {i + 1} ---")
        legs.append(OptionLeg(action=click.prompt("Action", type=click.Choice(['buy', 'sell'])),
                             contract=OptionContract(symbol=symbol, expiration=expiration,
                                                   option_type=click.prompt("Type", type=click.Choice(['call', 'put'])),
                                                   strike=click.prompt("Strike", type=float),
                                                   bid=click.prompt("Bid", type=float),
                                                   ask=click.prompt("Ask", type=float))))
    
    current_strategy = Strategy(legs=legs, underlying_symbol=symbol, created_at=datetime.now())
    current_metrics = StrategyCalculator().calculate_strategy_metrics(current_strategy)
    click.echo(f"📊 Premium: ${current_metrics.net_premium:.2f} | P/L: ${current_metrics.max_profit:.2f}/${current_metrics.max_loss:.2f}")
    click.echo("✅ Built! Use 'analyze-strategy' or 'save-trade'")

@cli.command()
def analyze_strategy():
    """Analyze current strategy with AI."""
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

@cli.command()
def save_trade():
    """Save current strategy to journal."""
    if not current_strategy:
        return click.echo("❌ Build strategy first")
    try:
        trade = TradingJournal().save_trade(current_strategy, current_metrics)
        click.echo(f"💾 Saved! ID: {trade.id}")
    except TradingJournalError as e:
        click.echo(f"❌ {e}", err=True)

@cli.command()
def list_trades():
    """List all trades in journal."""
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

@cli.command()
@click.option('--id', required=True, type=int)
@click.option('--price', required=True, type=float)
def close_trade(id, price):
    """Close trade with manual price."""
    try:
        trade = TradingJournal().close_trade(id, price)
        click.echo(f"🔒 Closed! P&L: ${trade.final_pnl:.2f}")
    except TradingJournalError as e:
        click.echo(f"❌ {e}", err=True)

if __name__ == '__main__':
    cli()