#!/usr/bin/env python3
"""CLI interface for OptionPilot - AI-powered options strategy analyzer."""

import click
from src.cli_handlers import (
    handle_get_quote,
    handle_get_options,
    handle_build_strategy,
    handle_analyze_strategy,
    handle_save_trade,
    handle_list_trades,
    handle_close_trade
)


@click.group()
@click.version_option()
def cli():
    """OptionPilot - AI-powered options strategy analyzer."""
    pass


@cli.command()
@click.argument('symbol')
def get_quote(symbol):
    """Get real-time stock quote for SYMBOL."""
    handle_get_quote(symbol)


@cli.command()
@click.argument('symbol')
@click.argument('date')
def get_options(symbol, date):
    """Get options chain for SYMBOL and DATE (YYYY-MM-DD)."""
    handle_get_options(symbol, date)


@cli.command()
def build_strategy():
    """Interactive strategy builder."""
    handle_build_strategy()


@cli.command()
def analyze_strategy():
    """Analyze current strategy with AI."""
    handle_analyze_strategy()


@cli.command()
def save_trade():
    """Save current strategy to journal."""
    handle_save_trade()


@cli.command()
def list_trades():
    """List all trades in journal."""
    handle_list_trades()


@cli.command()
@click.option('--id', required=True, type=int)
@click.option('--price', required=True, type=float)
def close_trade(id, price):
    """Close trade with manual price."""
    handle_close_trade(id, price)


if __name__ == '__main__':
    cli()