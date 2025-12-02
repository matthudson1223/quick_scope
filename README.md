# QuickScope: Fundamental Analysis & Strategy Engine

A Python CLI tool that evaluates stock fundamentals, performs sentiment analysis, and generates trading strategies across multiple risk profiles.

## Project Goals

Build a modular, extensible stock analysis tool that:

1. Pulls fundamental data for any given ticker
2. Calculates intrinsic value using multiple valuation methods
3. Analyzes market sentiment from news and social sources
4. Generates actionable trading strategies with varying risk/reward profiles
5. Outputs clear, formatted reports to the terminal

## Architecture Overview

```
stockscope/
├── main.py                 # CLI entry point
├── config.py               # API keys, settings
├── data/
│   ├── fetcher.py          # Data ingestion from APIs
│   ├── cache.py            # Local SQLite caching
│   └── models.py           # Data classes/schemas
├── analysis/
│   ├── fundamental.py      # Valuation calculations
│   ├── sentiment.py        # NLP sentiment scoring
│   └── technicals.py       # Basic technical indicators
├── strategy/
│   ├── generator.py        # Strategy construction logic
│   ├── risk.py             # Risk/reward calculations
│   └── options.py          # Options strategy helpers
├── output/
│   ├── formatter.py        # Rich terminal formatting
│   └── reports.py          # Report generation
└── tests/
    └── ...
```

## Implementation Order

Complete these phases sequentially. Each phase should be functional before moving to the next.

### Phase 1: Project Setup & Data Layer

1. Initialize the project structure as shown above
2. Create `requirements.txt` with dependencies:
   - yfinance
   - pandas
   - numpy
   - requests
   - python-dotenv
   - rich
   - typer
   - transformers
   - torch
   - scipy
   - duckdb
3. Create `config.py` to load API keys from environment variables (.env file)
4. Implement `data/fetcher.py`:
   - Function to fetch stock price history (yfinance)
   - Function to fetch fundamental data (income statement, balance sheet, cash flow)
   - Function to fetch current options chain
   - Function to fetch analyst recommendations
   - Function to fetch news headlines (via yfinance initially)
5. Implement `data/cache.py`:
   - DuckDB-based caching to avoid redundant API calls
   - Cache expiration logic (prices: 15 min, fundamentals: 24 hrs)
6. Create `data/models.py`:
   - Dataclasses for StockData, Fundamentals, OptionsChain, NewsItem

### Phase 2: Fundamental Analysis Engine

Implement `analysis/fundamental.py` with these valuation methods:

1. **Discounted Cash Flow (DCF)**
   - Project free cash flow 5-10 years
   - Use WACC as discount rate (calculate from beta, risk-free rate, market premium)
   - Terminal value using perpetuity growth method
   - Output: intrinsic value per share

2. **Comparable Company Analysis**
   - Calculate P/E, P/S, P/B, EV/EBITDA ratios
   - Compare to sector/industry medians (hardcode reasonable defaults initially)
   - Output: relative valuation score (-2 to +2 scale: very undervalued to very overvalued)

3. **Dividend Discount Model** (if applicable)
   - Gordon Growth Model for dividend payers
   - Skip for non-dividend stocks

4. **Financial Health Scoring**
   - Current ratio, quick ratio
   - Debt-to-equity, interest coverage
   - ROE, ROA, profit margins
   - Output: health score (0-100)

5. **Growth Analysis**
   - Revenue growth (3yr, 5yr CAGR)
   - Earnings growth
   - Compare to analyst estimates if available

Create a `FundamentalReport` dataclass that aggregates all outputs.

### Phase 3: Sentiment Analysis

Implement `analysis/sentiment.py`:

1. **News Sentiment**
   - Fetch recent news headlines for ticker
   - Use FinBERT model (ProsusAI/finbert) for financial sentiment
   - Score each headline: positive, negative, neutral with confidence
   - Aggregate into overall news sentiment score (-1 to +1)

2. **Analyst Sentiment**
   - Parse analyst recommendations from yfinance
   - Weight recent recommendations more heavily
   - Output: analyst sentiment score (-1 to +1)

3. **Combined Sentiment Score**
   - Weighted average of news (40%) and analyst (60%) sentiment
   - Include trend direction (improving/deteriorating)

Create a `SentimentReport` dataclass for outputs.

### Phase 4: Strategy Generator

Implement `strategy/generator.py`:

Define strategy profiles based on inputs:

```python
class RiskProfile(Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

class StrategyType(Enum):
    LONG_ONLY = "long_only"
    HEDGED = "hedged"
    LEVERAGED = "leveraged"
    OPTIONS_BASED = "options_based"
```

For each combination, generate specific recommendations:

1. **Conservative + Long Only**
   - Position sizing: max 5% of portfolio
   - Entry: only if 20%+ undervalued with positive sentiment
   - Stop loss: 8-10%
   - Take profit: at fair value

2. **Moderate + Hedged**
   - Position sizing: max 10% of portfolio
   - Entry: if 10%+ undervalued
   - Hedge: protective put or collar strategy
   - Include specific options recommendations with strikes/expirations

3. **Aggressive + Leveraged**
   - Position sizing: up to 20% of portfolio
   - Entry: based on momentum + value confluence
   - Leverage: LEAPS calls or margin (with warnings)
   - Higher risk tolerance on stops

4. **Options Strategies** (implement in `strategy/options.py`)
   - Covered calls for income
   - Cash-secured puts for entry
   - Spreads (bull call, bear put) for defined risk
   - Calculate max profit, max loss, breakeven for each

Each strategy output should include:
- Recommended action (buy/sell/hold/wait)
- Position size suggestion
- Entry price targets
- Stop loss level
- Take profit targets
- Hedging instruments if applicable
- Risk/reward ratio
- Probability assessment (based on historical data)

### Phase 5: CLI Interface & Output

Implement `main.py` using Typer:

```
stockscope analyze TICKER [OPTIONS]

Options:
  --risk [conservative|moderate|aggressive]
  --strategy [long_only|hedged|leveraged|options_based]
  --portfolio-size FLOAT  (total portfolio value for position sizing)
  --output [terminal|json|markdown]
  --no-cache  (force fresh data fetch)
```

Implement `output/formatter.py` using Rich:
- Color-coded sentiment (green positive, red negative)
- Tables for financial metrics
- Clear section headers
- Warning boxes for high-risk strategies

Sample output structure:
```
═══════════════════════════════════════════════════════
                    AAPL Analysis
═══════════════════════════════════════════════════════

FUNDAMENTAL VALUATION
├── DCF Intrinsic Value:     $198.45
├── Current Price:           $185.20
├── Upside/Downside:         +7.2%
├── Relative Valuation:      Fairly Valued (P/E: 28x vs sector 25x)
└── Financial Health:        92/100 (Excellent)

SENTIMENT ANALYSIS
├── News Sentiment:          +0.42 (Positive)
├── Analyst Consensus:       +0.65 (Bullish)
├── Trend:                   Improving ↑
└── Overall:                 +0.55 (Bullish)

RECOMMENDED STRATEGY: Moderate Hedged
├── Action:                  BUY with protective put
├── Position Size:           $10,000 (10% of portfolio)
├── Entry Target:            $183.00 - $186.00
├── Stop Loss:               $172.00 (-7.1%)
├── Take Profit:             $198.00 (+7.0%)
├── Hedge:                   Buy 1x APR $180 Put @ $4.50
├── Max Loss (hedged):       $850 (8.5%)
├── Risk/Reward:             1:1.2
└── Confidence:              Medium-High

⚠️  Note: Options strategies involve significant risk...
═══════════════════════════════════════════════════════
```

### Phase 6: Testing & Refinement

1. Add unit tests for valuation calculations
2. Add integration tests with mocked API responses
3. Test edge cases: no dividend stocks, negative earnings, missing data
4. Add input validation and helpful error messages

## API Keys Required

Create a `.env` file (do not commit):

```
ALPHA_VANTAGE_KEY=your_key_here
FINNHUB_KEY=your_key_here
NEWS_API_KEY=your_key_here
FRED_API_KEY=your_key_here
```

Note: The core functionality works with just yfinance (no API key needed). Additional keys enhance data quality but are optional.

## Usage Examples

```bash
# Basic analysis with defaults
stockscope analyze AAPL

# Aggressive options-based strategy
stockscope analyze TSLA --risk aggressive --strategy options_based

# Conservative analysis with specific portfolio size
stockscope analyze MSFT --risk conservative --portfolio-size 50000

# Output as JSON for further processing
stockscope analyze NVDA --output json > nvda_analysis.json
```

## Development Notes

- Prioritize correctness over speed in calculations
- Cache aggressively to respect API rate limits
- All financial calculations should be auditable (show your work in verbose mode)
- Handle missing data gracefully with clear warnings
- Never store API keys in code

## Future Enhancements (Out of Scope for Initial Build)

- Web interface
- Portfolio tracking
- Backtesting engine
- Real-time alerts
- Multi-stock screening
