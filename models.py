"""
Core data models for the AI Options Strategy Analyzer.

This module defines all the fundamental data structures used throughout
the application, following the principle of keeping each file under 100 lines.
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import List, Optional


@dataclass
class StockQuote:
    """Stock price and timestamp data."""
    symbol: str
    price: float
    timestamp: datetime
    
    def __post_init__(self) -> None:
        if self.price <= 0:
            raise ValueError(f"Stock price {self.price} must be positive")
        if not self.symbol:
            raise ValueError("Stock symbol cannot be empty")


@dataclass
class OptionContract:
    """Individual option contract details."""
    symbol: str
    strike: float
    expiration: date
    option_type: str  # 'call' or 'put'
    bid: float
    ask: float
    
    def __post_init__(self) -> None:
        if self.strike <= 0:
            raise ValueError(f"Strike price {self.strike} must be positive")
        if self.option_type not in ['call', 'put']:
            raise ValueError(f"Option type must be 'call' or 'put', got {self.option_type}")
        if self.bid < 0:
            raise ValueError(f"Bid price {self.bid} cannot be negative")
        if self.ask < self.bid:
            raise ValueError(f"Ask price {self.ask} cannot be less than bid {self.bid}")


@dataclass
class OptionLeg:
    """Strategy leg with action and contract."""
    action: str  # 'buy' or 'sell'
    contract: OptionContract
    quantity: int = 1
    
    def __post_init__(self) -> None:
        if self.action not in ['buy', 'sell']:
            raise ValueError(f"Action must be 'buy' or 'sell', got {self.action}")
        if self.quantity <= 0:
            raise ValueError(f"Quantity {self.quantity} must be positive")


@dataclass
class Strategy:
    """Complete strategy with multiple legs."""
    legs: List[OptionLeg]
    underlying_symbol: str
    created_at: datetime
    
    def __post_init__(self) -> None:
        if not self.legs:
            raise ValueError("Strategy must have at least one leg")
        if len(self.legs) > 2:
            raise ValueError("MVP only supports two-leg strategies")


@dataclass
class StrategyMetrics:
    """Calculated financial metrics."""
    net_premium: float
    max_profit: float
    max_loss: float
    breakeven_points: List[float]
    margin_requirement: float
    return_on_margin: float


@dataclass
class TradeRecord:
    """Trading journal entry."""
    id: int
    strategy: Strategy
    metrics: StrategyMetrics
    entry_date: date
    status: str  # 'open' or 'closed'
    closing_price: Optional[float] = None
    final_pnl: Optional[float] = None
    
    def __post_init__(self) -> None:
        if self.status not in ['open', 'closed']:
            raise ValueError(f"Status must be 'open' or 'closed', got {self.status}")