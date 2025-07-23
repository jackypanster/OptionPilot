# Options Strategy Calculations

This document explains all financial formulas and calculations used in the OptionPilot strategy calculator.

## Core Financial Metrics

### 1. Net Premium Calculation

The net premium determines whether a strategy is a credit (receive money) or debit (pay money) spread.

**Formula:**
```
Net Premium = Σ(Premium × Action × Quantity)
Where Action: +1 for sell, -1 for buy
```

**Examples:**
- **Long Call:** Buy 1 NVDA 150 Call @ $8.70 → Net Premium = -$8.70 (debit)
- **Short Call:** Sell 1 NVDA 150 Call @ $8.50 → Net Premium = +$8.50 (credit)
- **Bull Call Spread:** Buy 145 Call @ $12.20, Sell 155 Call @ $6.80 → Net Premium = -$5.40 (debit)

### 2. Maximum Profit Calculation

**Single Leg Strategies:**
- **Long Call/Put:** Unlimited (for calls) or Strike Price (for puts)
- **Short Call/Put:** Premium received

**Two-Leg Spreads:**
- **Credit Spreads:** Net Premium received
- **Debit Spreads:** Spread Width - Net Premium paid

**Formula for Spreads:**
```
Max Profit = |Strike₁ - Strike₂| × 100 - |Net Premium| (for debit spreads)
Max Profit = Net Premium (for credit spreads)
```

**Example - Bull Call Spread:**
- Buy 145 Call @ $12.20, Sell 155 Call @ $6.80
- Net Premium = -$5.40 (debit)
- Max Profit = (155 - 145) × 100 - 5.40 = $994.60

### 3. Maximum Loss Calculation

**Single Leg Strategies:**
- **Long Options:** Premium paid
- **Short Options:** Unlimited (theoretically)

**Two-Leg Spreads:**
- **Credit Spreads:** Spread Width - Net Premium received
- **Debit Spreads:** Net Premium paid

**Example - Bull Call Spread:**
- Max Loss = Premium paid = $5.40

### 4. Breakeven Point Calculation

The stock price at expiration where the strategy neither profits nor loses money.

**Single Leg:**
- **Long Call:** Strike + Premium per share
- **Long Put:** Strike - Premium per share
- **Short Call:** Strike + Premium per share
- **Short Put:** Strike - Premium per share

**Two-Leg Spreads:**
```
Breakeven = Lower Strike + Net Premium per share (for call spreads)
Breakeven = Upper Strike - Net Premium per share (for put spreads)
```

**Example - Bull Call Spread:**
- Lower Strike = 145, Net Premium = -$5.40
- Breakeven = 145 + (-5.40/100) = $144.95

### 5. Margin Requirement

The capital required to hold the position.

**Rules:**
- **Credit Spreads:** Maximum possible loss
- **Debit Spreads:** Net premium paid
- **Single Long Options:** Premium paid
- **Single Short Options:** Unlimited (margin call risk)

### 6. Return on Margin

Percentage return based on capital at risk.

**Formula:**
```
Return on Margin = (Max Profit / Margin Requirement) × 100%
```

**Example - Bull Call Spread:**
- Max Profit = $994.60
- Margin Requirement = $5.40
- Return on Margin = (994.60 / 5.40) × 100% = 18,418.52%

## Common Strategy Examples

### Bull Call Spread
- **Setup:** Buy lower strike call, sell higher strike call
- **Market View:** Moderately bullish
- **Max Profit:** Spread width - net premium
- **Max Loss:** Net premium paid
- **Breakeven:** Lower strike + net premium per share

### Bear Put Spread
- **Setup:** Buy higher strike put, sell lower strike put
- **Market View:** Moderately bearish
- **Max Profit:** Spread width - net premium
- **Max Loss:** Net premium paid
- **Breakeven:** Higher strike - net premium per share

### Bull Put Spread (Credit Spread)
- **Setup:** Sell higher strike put, buy lower strike put
- **Market View:** Moderately bullish
- **Max Profit:** Net premium received
- **Max Loss:** Spread width - net premium
- **Breakeven:** Higher strike - net premium per share

### Bear Call Spread (Credit Spread)
- **Setup:** Sell lower strike call, buy higher strike call
- **Market View:** Moderately bearish
- **Max Profit:** Net premium received
- **Max Loss:** Spread width - net premium
- **Breakeven:** Lower strike + net premium per share

## Precision and Rounding

All calculations use Python's `Decimal` class for financial precision:
- Premiums rounded to 2 decimal places
- Breakeven points rounded to 2 decimal places
- Return percentages rounded to 2 decimal places

## Validation Rules

The calculator validates:
- Strike prices must be positive
- Bid prices cannot be negative
- Ask prices must be >= bid prices
- Option types must be 'call' or 'put'
- Actions must be 'buy' or 'sell'
- Quantities must be positive integers

## Payoff Diagram Generation

The StrategyCalculator includes basic payoff diagram generation to visualize strategy profit/loss at expiration.

### Usage

```python
from src.strategy_calculator import StrategyCalculator

calculator = StrategyCalculator()
figure = calculator.generate_payoff_diagram(strategy, current_stock_price)
```

### Features

- **Price Range**: ±50% of current stock price (51 data points)
- **Payoff Calculation**: Intrinsic value minus premium for each leg
- **Basic Visualization**: Blue line for strategy P&L, red breakeven line, green current price line
- **Simple Formatting**: Grid, labels, legend, and title

### Example Output

For a bull call spread (buy 145 call, sell 155 call):
- X-axis: Stock prices from $75 to $225 (if current price is $150)
- Y-axis: Profit/loss in dollars
- Shows maximum profit at prices above $155
- Shows maximum loss at prices below $145
- Shows breakeven point around $150.54

### Calculation Logic

**Single Leg Options:**
- Long Call: `max(0, stock_price - strike) * 100 - premium_paid`
- Long Put: `max(0, strike - stock_price) * 100 - premium_paid`
- Short Call: `premium_received - max(0, stock_price - strike) * 100`
- Short Put: `premium_received - max(0, strike - stock_price) * 100`

**Two-Leg Spreads:**
- Sum the payoffs of both legs at each price point
- Each leg calculated independently using single leg formulas

## Testing

All calculations are tested with known inputs and expected outputs:
- Single leg positions (long/short calls and puts)
- Two-leg spreads (bull/bear, call/put combinations)
- Payoff diagram generation and accuracy
- Edge cases and precision handling
- Invalid input validation

See `tests/test_strategy_calculator.py` and `tests/test_payoff_diagram.py` for comprehensive test cases.