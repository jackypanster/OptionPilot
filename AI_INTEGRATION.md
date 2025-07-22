# AI Integration Guide

This document explains the AI-powered strategy analysis feature using OpenRouter API integration.

## Overview

The AIAnalyzer provides intelligent interpretation of options strategies using Claude 3.5 Sonnet via OpenRouter API. It analyzes strategy composition and provides three key insights:

1. **Strategy Interpretation**: What type of strategy this is
2. **Market Outlook**: Implied market expectations 
3. **Risk Warning**: Primary risks if market moves against position

## OpenRouter API Setup

### 1. Get API Key

1. **Create Account:**
   - Visit [OpenRouter](https://openrouter.ai/keys)
   - Sign up for an account
   - Navigate to API Keys section

2. **Generate Key:**
   - Click "Create Key"
   - Name your key (e.g., "OptionPilot")
   - Copy the generated API key

### 2. Configure Environment

Add your API key to the `.env` file:
```bash
# Add to your .env file
OPENROUTER_API_KEY=your_actual_openrouter_api_key_here
```

### 3. Test Configuration

Verify your setup works:
```bash
uv run python -c "from src.config import validate_config; validate_config(); print('Configuration valid')"
```

## Usage Examples

### Basic Analysis

```python
from src.ai_analyzer import AIAnalyzer
from src.strategy_calculator import StrategyCalculator
from src.models import Strategy, OptionLeg, OptionContract

# Create analyzer
analyzer = AIAnalyzer()
calculator = StrategyCalculator()

# Analyze a bull call spread
strategy = # ... your strategy object
metrics = calculator.calculate_strategy_metrics(strategy)
current_price = 150.25

# Get AI analysis
analysis = analyzer.analyze_strategy(strategy, metrics, current_price)

print(f"Strategy: {analysis['interpretation']}")
print(f"Market View: {analysis['market_outlook']}")
print(f"Risk Warning: {analysis['risk_warning']}")
```

### Expected Output

For a bull call spread (Buy $145 Call, Sell $155 Call):
```
Strategy: This is a bull call spread strategy that profits from moderate upward movement.
Market View: Strategy expects NVDA to rise moderately and stay above $150.54 by expiration.
Risk Warning: Maximum loss of $5.40 occurs if stock closes below $145 at expiration.
```

## Prompt Engineering

### Input Format

The AI analyzer formats strategy data into a structured prompt:

```
Analyze this options strategy:

Stock: NVDA at $150.25
Strategy: buy call $145.0 (bid: $11.80, ask: $12.20) | sell call $155.0 (bid: $6.80, ask: $7.20)
Net Premium: $-5.40
Max Profit: $994.60
Max Loss: $5.40
Breakeven: [150.54]

Provide exactly 3 responses:
1. INTERPRETATION: One sentence explaining what strategy this is
2. MARKET_OUTLOOK: What market expectation this strategy implies
3. RISK_WARNING: Primary risk if market moves against position

Format: JSON with keys "interpretation", "market_outlook", "risk_warning".
```

### Response Format

The AI returns structured JSON:
```json
{
  "interpretation": "This is a bull call spread strategy that profits from moderate upward movement.",
  "market_outlook": "Strategy expects NVDA to rise moderately and stay above $150.54 by expiration.",
  "risk_warning": "Maximum loss of $5.40 occurs if stock closes below $145 at expiration."
}
```

## Error Handling

### Common Errors

1. **Missing API Key:**
   ```
   ConfigError: Missing OPENROUTER_API_KEY in environment variables
   ```

2. **Rate Limit Exceeded:**
   ```
   AIAnalysisError: API error: Rate limit exceeded
   ```

3. **Invalid Response Format:**
   ```
   AIAnalysisError: Invalid response format: Missing required key: interpretation
   ```

### Retry Strategy

The AI analyzer follows fail-fast principles - no automatic retries. If an error occurs:
1. Check your API key configuration
2. Verify your OpenRouter account has credits
3. Ensure network connectivity

## Rate Limits & Costs

### OpenRouter Limits
- Varies by model and account tier
- Claude 3.5 Sonnet: ~$0.003 per request (typical strategy analysis)
- Monitor usage at [OpenRouter Dashboard](https://openrouter.ai/activity)

### Best Practices
1. **Cache Results**: Store analysis results to avoid repeated API calls
2. **Validate Inputs**: Ensure strategy data is complete before analysis
3. **Monitor Costs**: Track API usage in production deployments

## Model Selection

Current configuration uses `anthropic/claude-3.5-sonnet` for:
- **High Accuracy**: Best understanding of financial concepts
- **Structured Output**: Reliable JSON response formatting
- **Cost Efficiency**: Good balance of quality and price

Alternative models available through OpenRouter:
- `openai/gpt-4o`: Similar quality, different pricing
- `anthropic/claude-3-haiku`: Faster, lower cost option

## Integration with CLI

The AI analyzer integrates with the CLI interface:
```bash
# Analyze strategy (future CLI command)
uv run python cli.py analyze-strategy --symbol NVDA --strategy bull-call-spread
```

## Troubleshooting

### API Connection Issues
```bash
# Test API connectivity
uv run python -c "from src.ai_analyzer import AIAnalyzer; analyzer = AIAnalyzer(); print('AI analyzer ready')"
```

### Response Validation
The analyzer validates all AI responses for required fields and proper JSON format. Invalid responses raise `AIAnalysisError` with descriptive messages.

### Development Testing
Use pytest with mocked responses for development:
```bash
uv run python -m pytest tests/test_ai_analyzer.py -v
```