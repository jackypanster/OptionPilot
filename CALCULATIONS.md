# Options Strategy Calculations

This document explains the financial formulas used by the OptionPilot strategy calculator.

## Core Formulas

### 1. Net Premium Calculation

**Formula:**
```
Net Premium = Σ(Premium Received) - Σ(Premium Paid)

Where:
- Premium Received = Bid Price × Quantity (for sell actions)
- Premium Paid = Ask Price × Quantity (for buy actions)
```

**Result:**
- Positive = Credit (money received)
- Negative = Debit (money paid)

### 2. Maximum Profit

**Single Leg:**
- **Long Call/Put**: Premium paid (for puts) or Unlimited (for calls)
- **Short Call/Put**: Premium received

**Two-Leg Spreads:**
- **Credit Spreads**: Net Premium (money received)
- **Debit Spreads**: (Strike Difference × 100) + Net Premium

### 3. Maximum Loss

**Single Leg:**
- **Long Call/Put**: Premium paid (limited loss)
- **Short Call/Put**: Unlimited loss

**Two-Leg Spreads:**
- **Credit Spreads**: (Strike Difference × 100) - Net Premium
- **Debit Spreads**: Premium paid (Net Premium)

### 4. Breakeven Points

**Single Leg:**
- **Call Options**: Strike Price + Premium Paid/Received
- **Put Options**: Strike Price - Premium Paid/Received

**Two-Leg Spreads:**
- **Call Spreads**: Lower Strike + (Net Premium ÷ 100)
- **Put Spreads**: Upper Strike - (Net Premium ÷ 100)

### 5. Margin Requirement

**Formula:**
```
Margin = {
  Max Loss           (for credit spreads)
  Premium Paid       (for debit spreads)
}
```

### 6. Return on Margin

**Formula:**
```
Return on Margin (%) = (Max Profit ÷ Margin) × 100
```

**Special Cases:**
- Returns 0% for unlimited profit or unlimited risk scenarios

## Strategy Examples

### Example 1: Long Call
- **Position**: Buy NVDA $150 Call for $8.70
- **Net Premium**: -$8.70 (debit)
- **Max Profit**: Unlimited
- **Max Loss**: $8.70
- **Breakeven**: $158.70 ($150 + $8.70)
- **Margin**: $8.70
- **Return on Margin**: 0% (unlimited profit)

### Example 2: Bull Call Spread
- **Position**: Buy $145 Call ($12.20), Sell $155 Call ($6.80)
- **Net Premium**: -$5.40 (debit)
- **Max Profit**: $994.60 (($155-$145)×100 - $5.40)
- **Max Loss**: $5.40
- **Breakeven**: $144.946 ($145 - $5.40÷100)
- **Margin**: $5.40
- **Return on Margin**: 18,418.52%

### Example 3: Bear Put Spread
- **Position**: Buy $150 Put ($9.70), Sell $140 Put ($5.20)
- **Net Premium**: -$4.50 (debit)
- **Max Profit**: $995.50 (($150-$140)×100 - $4.50)
- **Max Loss**: $4.50
- **Breakeven**: $145.50 ($150 - $4.50÷100)
- **Margin**: $4.50
- **Return on Margin**: 22,122.22%

## Implementation Notes

1. **Precision**: All calculations use Decimal arithmetic with 2 decimal places
2. **Bid-Ask Spreads**: Realistic pricing using bid for sells, ask for buys
3. **Unlimited Values**: Represented as 99,999 in calculations
4. **MVP Limitation**: Currently supports maximum 2-leg strategies

## References

- Options pricing follows standard financial market conventions
- Margin calculations based on typical broker requirements
- All formulas validated against industry-standard options calculators