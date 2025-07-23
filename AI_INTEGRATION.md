# AI Integration with OpenRouter

This document explains the AI-powered strategy analysis integration using OpenRouter API and Claude 4 Sonnet.

## Overview

The AI analyzer provides qualitative analysis of options strategies, translating complex financial metrics into plain-language insights for traders.

## Setup

### 1. Get OpenRouter API Key

1. Visit [OpenRouter.ai](https://openrouter.ai/keys)
2. Create an account and generate an API key
3. Add the key to your `.env` file:
   ```
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

### 2. Model Selection

We use **Claude 3.5 Sonnet** (`anthropic/claude-3.5-sonnet`) for analysis because:
- Excellent financial reasoning capabilities
- Structured output generation
- Reliable JSON formatting
- Good understanding of options trading concepts

## API Integration

### Configuration

```python
from src.ai_analyzer import AIAnalyzer

# Initialize analyzer (reads API key from environment)
analyzer = AIAnalyzer()
```

### Usage

```python
# Analyze a strategy
analysis = analyzer.analyze_strategy(strategy, metrics, current_stock_price)

# Returns dictionary with three components:
{
    "interpretation": "This is a bullish call credit spread strategy",
    "market_outlook": "This strategy profits when stock price rises moderately or stays above $150",
    "risk_warning": "Maximum loss occurs if stock falls below $145 at expiration"
}
```

## Prompt Engineering

### Structured Prompt Format

The AI analyzer uses a carefully crafted prompt that includes:

1. **Strategy Details:**
   - Stock symbol and current price
   - Each leg with action, type, strike, bid/ask
   - Net premium (credit/debit)

2. **Financial Metrics:**
   - Maximum profit and loss
   - Breakeven points
   - Return on margin

3. **Output Requirements:**
   - JSON format with specific keys
   - Concise, actionable insights
   - Plain language explanations

### Example Prompt

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

## Response Processing

### JSON Parsing

The analyzer expects structured JSON responses and validates:
- All required keys are present
- Content is meaningful (not empty strings)
- Response format is valid JSON

### Error Handling

Comprehensive error handling for:
- **Authentication errors:** Invalid API keys
- **Rate limiting:** API usage limits
- **Network issues:** Connection timeouts
- **Response parsing:** Invalid JSON format
- **Content validation:** Missing required fields

## Analysis Components

### 1. Strategy Interpretation

**Purpose:** One-sentence identification of the strategy type

**Examples:**
- "This is a bullish call debit spread strategy"
- "This is a bearish put credit spread strategy"
- "This is a long call position with unlimited upside potential"

### 2. Market Outlook

**Purpose:** Explain the implied market expectation and profit conditions

**Examples:**
- "This strategy profits when stock price rises moderately to $155 or stays above $150.54"
- "This strategy benefits from sideways to slightly bullish price movement"
- "Maximum profit occurs if stock price is above $155 at expiration"

### 3. Risk Warning

**Purpose:** Highlight the primary risk scenario

**Examples:**
- "Maximum loss of $540 occurs if stock falls below $145 at expiration"
- "Risk increases significantly if stock price moves against the position"
- "Time decay works against this position as expiration approaches"

## Testing

### Unit Tests

The AI analyzer includes comprehensive tests:
- Real API integration (no mocking)
- Multiple strategy types
- Error handling scenarios
- Response validation

### Test Examples

```python
def test_bull_call_spread_analysis(service, bull_call_spread, bull_call_metrics):
    analysis = service.analyze_strategy(bull_call_spread, bull_call_metrics, 150.25)
    
    # Verify structure
    assert 'interpretation' in analysis
    assert 'market_outlook' in analysis
    assert 'risk_warning' in analysis
    
    # Verify content quality
    assert len(analysis['interpretation']) > 10
    assert 'call' in analysis['interpretation'].lower()
```

## Best Practices

### 1. API Usage

- **Rate Limiting:** Implement exponential backoff
- **Timeout Handling:** Set reasonable request timeouts
- **Error Recovery:** Provide fallback responses
- **Cost Management:** Monitor API usage and costs

### 2. Prompt Design

- **Specificity:** Include all relevant strategy details
- **Consistency:** Use standardized format for all requests
- **Validation:** Require structured output format
- **Context:** Provide sufficient market context

### 3. Response Handling

- **Validation:** Always validate response structure
- **Sanitization:** Clean and format responses for display
- **Fallbacks:** Handle partial or malformed responses
- **Logging:** Track API performance and errors

## Configuration Options

### Environment Variables

```bash
# Required
OPENROUTER_API_KEY=your_api_key_here

# Optional
API_TIMEOUT=30                    # Request timeout in seconds
AI_MODEL=anthropic/claude-3.5-sonnet  # Model selection
AI_TEMPERATURE=0.3               # Response creativity (0.0-1.0)
AI_MAX_TOKENS=300               # Maximum response length
```

### Model Parameters

- **Temperature:** 0.3 (balanced creativity and consistency)
- **Max Tokens:** 300 (sufficient for concise analysis)
- **Model:** Claude 3.5 Sonnet (optimal for financial analysis)

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify API key is correct
   - Check environment variable name
   - Ensure key has sufficient credits

2. **Rate Limit Exceeded**
   - Implement request throttling
   - Add exponential backoff
   - Monitor usage patterns

3. **Invalid Response Format**
   - Check prompt formatting
   - Validate JSON parsing
   - Handle partial responses

4. **Network Timeouts**
   - Increase timeout values
   - Implement retry logic
   - Check network connectivity

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

analyzer = AIAnalyzer()
# Detailed request/response logging will be shown
```

## Future Enhancements

Potential improvements for the AI integration:
- Multi-model comparison (Claude vs GPT-4)
- Caching for repeated analyses
- Batch processing for multiple strategies
- Custom prompt templates for different user levels
- Integration with market sentiment data