"""Data models for QuickScope.

Defines dataclasses for stock data, fundamentals, options, and news.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List
import pandas as pd


@dataclass
class StockData:
    """Stock price and market data."""

    ticker: str
    current_price: float
    timestamp: datetime
    history: pd.DataFrame  # OHLCV data
    volume: int
    market_cap: Optional[float] = None
    beta: Optional[float] = None
    shares_outstanding: Optional[int] = None

    def __post_init__(self):
        """Validate stock data."""
        if self.current_price <= 0:
            raise ValueError("Current price must be positive")


@dataclass
class Fundamentals:
    """Company fundamental data."""

    ticker: str
    timestamp: datetime

    # Income statement metrics
    revenue: Optional[float] = None
    revenue_growth: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    eps: Optional[float] = None
    ebitda: Optional[float] = None

    # Balance sheet metrics
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_equity: Optional[float] = None
    cash: Optional[float] = None
    debt: Optional[float] = None
    current_assets: Optional[float] = None
    current_liabilities: Optional[float] = None

    # Cash flow metrics
    operating_cash_flow: Optional[float] = None
    free_cash_flow: Optional[float] = None
    capital_expenditure: Optional[float] = None

    # Ratios and derived metrics
    pe_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    profit_margin: Optional[float] = None
    operating_margin: Optional[float] = None

    # Dividend data
    dividend_yield: Optional[float] = None
    payout_ratio: Optional[float] = None
    dividend_per_share: Optional[float] = None

    # Full financial statements (as dataframes)
    income_statement: Optional[pd.DataFrame] = None
    balance_sheet: Optional[pd.DataFrame] = None
    cash_flow: Optional[pd.DataFrame] = None


@dataclass
class OptionContract:
    """Single options contract data."""

    ticker: str
    contract_symbol: str
    strike: float
    expiration: datetime
    option_type: str  # 'call' or 'put'
    last_price: float
    bid: float
    ask: float
    volume: int
    open_interest: int
    implied_volatility: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    in_the_money: bool = False


@dataclass
class OptionsChain:
    """Full options chain data for a ticker."""

    ticker: str
    timestamp: datetime
    expirations: List[datetime]
    calls: List[OptionContract] = field(default_factory=list)
    puts: List[OptionContract] = field(default_factory=list)

    def get_calls_by_expiration(self, expiration: datetime) -> List[OptionContract]:
        """Get all call options for a specific expiration date."""
        return [c for c in self.calls if c.expiration == expiration]

    def get_puts_by_expiration(self, expiration: datetime) -> List[OptionContract]:
        """Get all put options for a specific expiration date."""
        return [p for p in self.puts if p.expiration == expiration]

    def get_nearest_expiration(self) -> Optional[datetime]:
        """Get the nearest expiration date."""
        return min(self.expirations) if self.expirations else None


@dataclass
class NewsItem:
    """Single news article or headline."""

    ticker: str
    title: str
    source: str
    published_at: datetime
    url: Optional[str] = None
    summary: Optional[str] = None
    sentiment_score: Optional[float] = None  # -1 to +1
    sentiment_label: Optional[str] = None  # 'positive', 'negative', 'neutral'
    sentiment_confidence: Optional[float] = None  # 0 to 1


@dataclass
class AnalystRecommendation:
    """Analyst recommendation data."""

    ticker: str
    date: datetime
    firm: str
    rating: str  # 'strong buy', 'buy', 'hold', 'sell', 'strong sell'
    target_price: Optional[float] = None


@dataclass
class AnalystRatings:
    """Aggregated analyst ratings."""

    ticker: str
    timestamp: datetime
    strong_buy: int = 0
    buy: int = 0
    hold: int = 0
    sell: int = 0
    strong_sell: int = 0
    mean_target_price: Optional[float] = None
    median_target_price: Optional[float] = None
    recommendations: List[AnalystRecommendation] = field(default_factory=list)

    @property
    def total_ratings(self) -> int:
        """Total number of ratings."""
        return self.strong_buy + self.buy + self.hold + self.sell + self.strong_sell

    @property
    def consensus_score(self) -> float:
        """Consensus score from -1 (bearish) to +1 (bullish)."""
        if self.total_ratings == 0:
            return 0.0

        # Weight: strong buy = +2, buy = +1, hold = 0, sell = -1, strong sell = -2
        weighted_sum = (
            self.strong_buy * 2 +
            self.buy * 1 +
            self.hold * 0 +
            self.sell * (-1) +
            self.strong_sell * (-2)
        )

        # Normalize to -1 to +1 range
        max_possible = self.total_ratings * 2
        return weighted_sum / max_possible if max_possible > 0 else 0.0


@dataclass
class MarketData:
    """Combined market data for a ticker."""

    ticker: str
    timestamp: datetime
    stock_data: Optional[StockData] = None
    fundamentals: Optional[Fundamentals] = None
    options_chain: Optional[OptionsChain] = None
    news: List[NewsItem] = field(default_factory=list)
    analyst_ratings: Optional[AnalystRatings] = None

    def is_complete(self) -> bool:
        """Check if all major data components are available."""
        return (
            self.stock_data is not None and
            self.fundamentals is not None
        )

    def has_options_data(self) -> bool:
        """Check if options chain data is available."""
        return (
            self.options_chain is not None and
            len(self.options_chain.calls) > 0
        )

    def has_news_data(self) -> bool:
        """Check if news data is available."""
        return len(self.news) > 0
