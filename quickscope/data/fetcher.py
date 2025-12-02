"""Data fetcher module for QuickScope.

Fetches stock data, fundamentals, options, and news from various APIs.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import yfinance as yf
import pandas as pd

from .models import (
    StockData,
    Fundamentals,
    OptionContract,
    OptionsChain,
    NewsItem,
    AnalystRecommendation,
    AnalystRatings,
    MarketData,
)

logger = logging.getLogger(__name__)


class DataFetcher:
    """Fetches financial data from various sources."""

    def __init__(self):
        """Initialize the data fetcher."""
        self._cache = {}

    def fetch_stock_price_history(
        self,
        ticker: str,
        period: str = "1y",
        interval: str = "1d"
    ) -> StockData:
        """Fetch stock price history using yfinance.

        Args:
            ticker: Stock ticker symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            StockData object with price history
        """
        logger.info(f"Fetching price history for {ticker}")

        try:
            stock = yf.Ticker(ticker)
            history = stock.history(period=period, interval=interval)

            if history.empty:
                raise ValueError(f"No price data available for {ticker}")

            # Get current price from most recent close
            current_price = float(history['Close'].iloc[-1])

            # Get additional info
            info = stock.info
            market_cap = info.get('marketCap')
            beta = info.get('beta')
            shares_outstanding = info.get('sharesOutstanding')
            volume = int(history['Volume'].iloc[-1])

            return StockData(
                ticker=ticker.upper(),
                current_price=current_price,
                timestamp=datetime.now(),
                history=history,
                volume=volume,
                market_cap=market_cap,
                beta=beta,
                shares_outstanding=shares_outstanding,
            )

        except Exception as e:
            logger.error(f"Error fetching stock data for {ticker}: {e}")
            raise

    def fetch_fundamental_data(self, ticker: str) -> Fundamentals:
        """Fetch fundamental data (income statement, balance sheet, cash flow).

        Args:
            ticker: Stock ticker symbol

        Returns:
            Fundamentals object with financial data
        """
        logger.info(f"Fetching fundamental data for {ticker}")

        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Get financial statements
            income_stmt = stock.financials
            balance_sheet = stock.balance_sheet
            cash_flow = stock.cashflow

            # Extract key metrics from info
            fundamentals = Fundamentals(
                ticker=ticker.upper(),
                timestamp=datetime.now(),
                # Income statement metrics
                revenue=info.get('totalRevenue'),
                revenue_growth=info.get('revenueGrowth'),
                gross_profit=info.get('grossProfits'),
                operating_income=info.get('operatingIncome'),
                net_income=info.get('netIncomeToCommon'),
                eps=info.get('trailingEps'),
                ebitda=info.get('ebitda'),
                # Balance sheet metrics
                total_assets=info.get('totalAssets'),
                total_liabilities=info.get('totalDebt'),
                total_equity=info.get('totalStockholderEquity'),
                cash=info.get('totalCash'),
                debt=info.get('totalDebt'),
                current_assets=info.get('currentAssets'),
                current_liabilities=info.get('currentLiabilities'),
                # Cash flow metrics
                operating_cash_flow=info.get('operatingCashflow'),
                free_cash_flow=info.get('freeCashflow'),
                # Ratios
                pe_ratio=info.get('trailingPE') or info.get('forwardPE'),
                ps_ratio=info.get('priceToSalesTrailing12Months'),
                pb_ratio=info.get('priceToBook'),
                debt_to_equity=info.get('debtToEquity'),
                current_ratio=info.get('currentRatio'),
                quick_ratio=info.get('quickRatio'),
                roe=info.get('returnOnEquity'),
                roa=info.get('returnOnAssets'),
                profit_margin=info.get('profitMargins'),
                operating_margin=info.get('operatingMargins'),
                # Dividend data
                dividend_yield=info.get('dividendYield'),
                payout_ratio=info.get('payoutRatio'),
                dividend_per_share=info.get('dividendRate'),
                # Full statements
                income_statement=income_stmt,
                balance_sheet=balance_sheet,
                cash_flow=cash_flow,
            )

            # Calculate derived metrics if not available
            if fundamentals.current_ratio is None and fundamentals.current_assets and fundamentals.current_liabilities:
                if fundamentals.current_liabilities > 0:
                    fundamentals.current_ratio = fundamentals.current_assets / fundamentals.current_liabilities

            if fundamentals.debt_to_equity is None and fundamentals.debt and fundamentals.total_equity:
                if fundamentals.total_equity > 0:
                    fundamentals.debt_to_equity = fundamentals.debt / fundamentals.total_equity

            return fundamentals

        except Exception as e:
            logger.error(f"Error fetching fundamental data for {ticker}: {e}")
            raise

    def fetch_options_chain(self, ticker: str) -> OptionsChain:
        """Fetch current options chain.

        Args:
            ticker: Stock ticker symbol

        Returns:
            OptionsChain object with options data
        """
        logger.info(f"Fetching options chain for {ticker}")

        try:
            stock = yf.Ticker(ticker)
            expirations = stock.options

            if not expirations:
                logger.warning(f"No options data available for {ticker}")
                return OptionsChain(
                    ticker=ticker.upper(),
                    timestamp=datetime.now(),
                    expirations=[],
                )

            # Convert expiration strings to datetime objects
            exp_dates = [datetime.strptime(exp, '%Y-%m-%d') for exp in expirations]

            calls_list = []
            puts_list = []

            # Fetch options for each expiration date (limit to first 3 to avoid too much data)
            for exp_str, exp_date in list(zip(expirations, exp_dates))[:3]:
                opt = stock.option_chain(exp_str)

                # Process calls
                for _, row in opt.calls.iterrows():
                    calls_list.append(OptionContract(
                        ticker=ticker.upper(),
                        contract_symbol=row.get('contractSymbol', ''),
                        strike=float(row['strike']),
                        expiration=exp_date,
                        option_type='call',
                        last_price=float(row.get('lastPrice', 0)),
                        bid=float(row.get('bid', 0)),
                        ask=float(row.get('ask', 0)),
                        volume=int(row.get('volume', 0)) if pd.notna(row.get('volume')) else 0,
                        open_interest=int(row.get('openInterest', 0)) if pd.notna(row.get('openInterest')) else 0,
                        implied_volatility=float(row.get('impliedVolatility', 0)) if pd.notna(row.get('impliedVolatility')) else None,
                        in_the_money=bool(row.get('inTheMoney', False)),
                    ))

                # Process puts
                for _, row in opt.puts.iterrows():
                    puts_list.append(OptionContract(
                        ticker=ticker.upper(),
                        contract_symbol=row.get('contractSymbol', ''),
                        strike=float(row['strike']),
                        expiration=exp_date,
                        option_type='put',
                        last_price=float(row.get('lastPrice', 0)),
                        bid=float(row.get('bid', 0)),
                        ask=float(row.get('ask', 0)),
                        volume=int(row.get('volume', 0)) if pd.notna(row.get('volume')) else 0,
                        open_interest=int(row.get('openInterest', 0)) if pd.notna(row.get('openInterest')) else 0,
                        implied_volatility=float(row.get('impliedVolatility', 0)) if pd.notna(row.get('impliedVolatility')) else None,
                        in_the_money=bool(row.get('inTheMoney', False)),
                    ))

            return OptionsChain(
                ticker=ticker.upper(),
                timestamp=datetime.now(),
                expirations=exp_dates,
                calls=calls_list,
                puts=puts_list,
            )

        except Exception as e:
            logger.error(f"Error fetching options chain for {ticker}: {e}")
            raise

    def fetch_analyst_recommendations(self, ticker: str) -> AnalystRatings:
        """Fetch analyst recommendations.

        Args:
            ticker: Stock ticker symbol

        Returns:
            AnalystRatings object with recommendation data
        """
        logger.info(f"Fetching analyst recommendations for {ticker}")

        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Get recommendation counts
            strong_buy = 0
            buy = 0
            hold = 0
            sell = 0
            strong_sell = 0

            # Try to get recommendations from info
            recommendation = info.get('recommendationKey', '').lower()
            if recommendation:
                if recommendation == 'strong_buy':
                    strong_buy = 1
                elif recommendation == 'buy':
                    buy = 1
                elif recommendation == 'hold':
                    hold = 1
                elif recommendation == 'sell':
                    sell = 1
                elif recommendation == 'strong_sell':
                    strong_sell = 1

            # Get target price
            mean_target = info.get('targetMeanPrice')
            median_target = info.get('targetMedianPrice')

            # Try to get detailed recommendations
            recommendations = []
            try:
                rec_df = stock.recommendations
                if rec_df is not None and not rec_df.empty:
                    # Reset counts from actual data
                    strong_buy = 0
                    buy = 0
                    hold = 0
                    sell = 0
                    strong_sell = 0

                    # Get recent recommendations (last 30 days)
                    recent_date = datetime.now() - timedelta(days=30)
                    for idx, row in rec_df.iterrows():
                        rec_date = idx if isinstance(idx, datetime) else datetime.now()
                        if rec_date >= recent_date:
                            rating = row.get('To Grade', '').lower()
                            firm = row.get('Firm', 'Unknown')

                            # Map rating to our categories
                            if 'strong buy' in rating or 'outperform' in rating:
                                strong_buy += 1
                                rating_cat = 'strong buy'
                            elif 'buy' in rating:
                                buy += 1
                                rating_cat = 'buy'
                            elif 'sell' in rating and 'strong' not in rating:
                                sell += 1
                                rating_cat = 'sell'
                            elif 'strong sell' in rating or 'underperform' in rating:
                                strong_sell += 1
                                rating_cat = 'strong sell'
                            else:
                                hold += 1
                                rating_cat = 'hold'

                            recommendations.append(AnalystRecommendation(
                                ticker=ticker.upper(),
                                date=rec_date,
                                firm=firm,
                                rating=rating_cat,
                            ))
            except Exception as e:
                logger.warning(f"Could not fetch detailed recommendations: {e}")

            return AnalystRatings(
                ticker=ticker.upper(),
                timestamp=datetime.now(),
                strong_buy=strong_buy,
                buy=buy,
                hold=hold,
                sell=sell,
                strong_sell=strong_sell,
                mean_target_price=mean_target,
                median_target_price=median_target,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error(f"Error fetching analyst recommendations for {ticker}: {e}")
            raise

    def fetch_news_headlines(self, ticker: str, max_items: int = 20) -> List[NewsItem]:
        """Fetch news headlines for a ticker.

        Args:
            ticker: Stock ticker symbol
            max_items: Maximum number of news items to return

        Returns:
            List of NewsItem objects
        """
        logger.info(f"Fetching news headlines for {ticker}")

        try:
            stock = yf.Ticker(ticker)
            news = stock.news

            if not news:
                logger.warning(f"No news available for {ticker}")
                return []

            news_items = []
            for item in news[:max_items]:
                # Parse timestamp
                timestamp = datetime.fromtimestamp(item.get('providerPublishTime', 0))

                news_items.append(NewsItem(
                    ticker=ticker.upper(),
                    title=item.get('title', ''),
                    source=item.get('publisher', 'Unknown'),
                    published_at=timestamp,
                    url=item.get('link'),
                    summary=item.get('summary'),
                ))

            return news_items

        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {e}")
            return []

    def fetch_all_data(self, ticker: str) -> MarketData:
        """Fetch all available data for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            MarketData object with all available data
        """
        logger.info(f"Fetching all data for {ticker}")

        market_data = MarketData(
            ticker=ticker.upper(),
            timestamp=datetime.now(),
        )

        try:
            # Fetch stock price data
            market_data.stock_data = self.fetch_stock_price_history(ticker)
        except Exception as e:
            logger.error(f"Failed to fetch stock data: {e}")

        try:
            # Fetch fundamental data
            market_data.fundamentals = self.fetch_fundamental_data(ticker)
        except Exception as e:
            logger.error(f"Failed to fetch fundamental data: {e}")

        try:
            # Fetch options chain
            market_data.options_chain = self.fetch_options_chain(ticker)
        except Exception as e:
            logger.warning(f"Failed to fetch options data: {e}")

        try:
            # Fetch news
            market_data.news = self.fetch_news_headlines(ticker)
        except Exception as e:
            logger.warning(f"Failed to fetch news: {e}")

        try:
            # Fetch analyst ratings
            market_data.analyst_ratings = self.fetch_analyst_recommendations(ticker)
        except Exception as e:
            logger.warning(f"Failed to fetch analyst ratings: {e}")

        return market_data
