"""Main CLI entry point for QuickScope.

Phase 1: Basic testing placeholder
Full implementation in Phase 5
"""

import logging
import sys
from rich.console import Console
from rich.table import Table

from .data.fetcher import DataFetcher
from .data.cache import CachedDataFetcher

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
console = Console()


def test_phase1(ticker: str = "AAPL"):
    """Test Phase 1 implementation.

    Args:
        ticker: Stock ticker to test with
    """
    console.print(f"\n[bold cyan]QuickScope Phase 1 Test[/bold cyan]")
    console.print(f"Testing data layer with ticker: [yellow]{ticker}[/yellow]\n")

    try:
        # Create data fetcher with caching
        fetcher = DataFetcher()
        cached_fetcher = CachedDataFetcher(fetcher)

        # Test fetching stock data
        console.print("[bold]1. Fetching stock price data...[/bold]")
        stock_data = cached_fetcher.fetch_stock_price_history(ticker)
        console.print(f"   ✓ Current price: ${stock_data.current_price:.2f}")
        console.print(f"   ✓ Market cap: ${stock_data.market_cap:,.0f}" if stock_data.market_cap else "   ✓ Market cap: N/A")
        console.print(f"   ✓ Beta: {stock_data.beta:.2f}" if stock_data.beta else "   ✓ Beta: N/A")
        console.print(f"   ✓ History shape: {stock_data.history.shape}\n")

        # Test fetching fundamentals
        console.print("[bold]2. Fetching fundamental data...[/bold]")
        fundamentals = cached_fetcher.fetch_fundamental_data(ticker)
        console.print(f"   ✓ Revenue: ${fundamentals.revenue:,.0f}" if fundamentals.revenue else "   ✓ Revenue: N/A")
        console.print(f"   ✓ EPS: ${fundamentals.eps:.2f}" if fundamentals.eps else "   ✓ EPS: N/A")
        console.print(f"   ✓ P/E Ratio: {fundamentals.pe_ratio:.2f}" if fundamentals.pe_ratio else "   ✓ P/E Ratio: N/A")
        console.print(f"   ✓ Debt/Equity: {fundamentals.debt_to_equity:.2f}" if fundamentals.debt_to_equity else "   ✓ Debt/Equity: N/A")
        console.print(f"   ✓ ROE: {fundamentals.roe:.2%}" if fundamentals.roe else "   ✓ ROE: N/A")
        console.print()

        # Test fetching news
        console.print("[bold]3. Fetching news headlines...[/bold]")
        news = cached_fetcher.fetch_news_headlines(ticker, max_items=5)
        console.print(f"   ✓ Retrieved {len(news)} news items")
        for i, item in enumerate(news[:3], 1):
            console.print(f"   {i}. {item.title[:60]}...")
        console.print()

        # Test fetching analyst ratings
        console.print("[bold]4. Fetching analyst ratings...[/bold]")
        ratings = cached_fetcher.fetch_analyst_recommendations(ticker)
        console.print(f"   ✓ Total ratings: {ratings.total_ratings}")
        console.print(f"   ✓ Strong Buy: {ratings.strong_buy}, Buy: {ratings.buy}, Hold: {ratings.hold}")
        console.print(f"   ✓ Consensus score: {ratings.consensus_score:.2f}")
        console.print(f"   ✓ Target price: ${ratings.mean_target_price:.2f}" if ratings.mean_target_price else "   ✓ Target price: N/A")
        console.print()

        # Test fetching options (optional, might not be available for all stocks)
        console.print("[bold]5. Fetching options chain...[/bold]")
        try:
            options = cached_fetcher.fetch_options_chain(ticker)
            console.print(f"   ✓ Expirations available: {len(options.expirations)}")
            console.print(f"   ✓ Total calls: {len(options.calls)}")
            console.print(f"   ✓ Total puts: {len(options.puts)}")
        except Exception as e:
            console.print(f"   ⚠ Options data not available: {e}")
        console.print()

        # Show cache stats
        console.print("[bold]6. Cache statistics...[/bold]")
        stats = cached_fetcher.cache.get_stats()
        console.print(f"   ✓ Total cache entries: {stats.get('total_entries', 0)}")
        console.print(f"   ✓ Valid entries: {stats.get('valid_entries', 0)}")
        console.print(f"   ✓ Cache size: {stats.get('db_size_mb', 0)} MB")
        console.print()

        console.print("[bold green]✓ Phase 1 test completed successfully![/bold green]\n")

    except Exception as e:
        console.print(f"[bold red]✗ Error during Phase 1 test: {e}[/bold red]")
        logger.exception("Phase 1 test failed")
        sys.exit(1)


if __name__ == "__main__":
    # For now, just run the test
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    test_phase1(ticker)
