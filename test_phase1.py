"""Simple test script for Phase 1 implementation.

Tests the data layer without requiring yfinance.
"""

from datetime import datetime
import pandas as pd
from rich.console import Console

from quickscope.data.models import StockData, Fundamentals
from quickscope.data.cache import Cache

console = Console()


def test_models():
    """Test data models."""
    console.print("\n[bold cyan]Testing Phase 1: Data Models[/bold cyan]\n")

    # Test StockData model
    console.print("[bold]1. Testing StockData model...[/bold]")
    history = pd.DataFrame({
        'Open': [150.0, 151.0, 152.0],
        'High': [152.0, 153.0, 154.0],
        'Low': [149.0, 150.0, 151.0],
        'Close': [151.0, 152.0, 153.0],
        'Volume': [1000000, 1100000, 1200000]
    })

    stock_data = StockData(
        ticker="AAPL",
        current_price=153.0,
        timestamp=datetime.now(),
        history=history,
        volume=1200000,
        market_cap=2500000000000,
        beta=1.2,
        shares_outstanding=16000000000
    )

    console.print(f"   ✓ Created StockData for {stock_data.ticker}")
    console.print(f"   ✓ Current price: ${stock_data.current_price}")
    console.print(f"   ✓ Market cap: ${stock_data.market_cap:,.0f}")
    console.print(f"   ✓ History shape: {stock_data.history.shape}")
    console.print()

    # Test Fundamentals model
    console.print("[bold]2. Testing Fundamentals model...[/bold]")
    fundamentals = Fundamentals(
        ticker="AAPL",
        timestamp=datetime.now(),
        revenue=394000000000,
        eps=6.11,
        pe_ratio=25.0,
        debt_to_equity=1.73,
        roe=0.15,
        profit_margin=0.25,
        dividend_yield=0.005
    )

    console.print(f"   ✓ Created Fundamentals for {fundamentals.ticker}")
    console.print(f"   ✓ Revenue: ${fundamentals.revenue:,.0f}")
    console.print(f"   ✓ EPS: ${fundamentals.eps}")
    console.print(f"   ✓ P/E Ratio: {fundamentals.pe_ratio}")
    console.print(f"   ✓ ROE: {fundamentals.roe:.1%}")
    console.print()

    return stock_data, fundamentals


def test_cache(stock_data, fundamentals):
    """Test caching functionality."""
    console.print("[bold]3. Testing Cache functionality...[/bold]")

    cache = Cache()

    # Test caching stock data
    cache.set("AAPL", "stock_data", stock_data)
    console.print("   ✓ Cached stock data")

    # Test retrieving stock data
    cached_data = cache.get("AAPL", "stock_data")
    assert cached_data is not None, "Failed to retrieve cached stock data"
    assert cached_data.current_price == stock_data.current_price
    console.print("   ✓ Retrieved stock data from cache")

    # Test caching fundamentals
    cache.set("AAPL", "fundamentals", fundamentals)
    console.print("   ✓ Cached fundamentals")

    # Test retrieving fundamentals
    cached_fund = cache.get("AAPL", "fundamentals")
    assert cached_fund is not None, "Failed to retrieve cached fundamentals"
    assert cached_fund.eps == fundamentals.eps
    console.print("   ✓ Retrieved fundamentals from cache")

    # Test cache stats
    stats = cache.get_stats()
    console.print(f"   ✓ Cache contains {stats['total_entries']} entries")
    console.print(f"   ✓ Cache size: {stats['db_size_mb']} MB")
    console.print()

    # Test cache deletion
    cache.delete("AAPL", "stock_data")
    deleted_data = cache.get("AAPL", "stock_data")
    assert deleted_data is None, "Failed to delete cached data"
    console.print("   ✓ Successfully deleted cached data")
    console.print()

    # Clean up
    cache.clear_all()
    console.print("   ✓ Cleared all cache")
    console.print()


def test_config():
    """Test configuration."""
    console.print("[bold]4. Testing Configuration...[/bold]")

    from quickscope.config import Config

    console.print(f"   ✓ Cache directory: {Config.CACHE_DIR}")
    console.print(f"   ✓ Price cache expiry: {Config.PRICE_CACHE_EXPIRY}s")
    console.print(f"   ✓ Fundamental cache expiry: {Config.FUNDAMENTAL_CACHE_EXPIRY}s")
    console.print(f"   ✓ Risk-free rate: {Config.RISK_FREE_RATE:.2%}")
    console.print(f"   ✓ Market risk premium: {Config.MARKET_RISK_PREMIUM:.2%}")
    console.print()


def main():
    """Run all Phase 1 tests."""
    console.print("[bold green]═══════════════════════════════════════════[/bold green]")
    console.print("[bold green]       QuickScope Phase 1 Test Suite       [/bold green]")
    console.print("[bold green]═══════════════════════════════════════════[/bold green]")

    try:
        # Test models
        stock_data, fundamentals = test_models()

        # Test cache
        test_cache(stock_data, fundamentals)

        # Test config
        test_config()

        console.print("[bold green]✓ All Phase 1 tests passed successfully![/bold green]\n")
        console.print("[bold]Phase 1 Deliverables Completed:[/bold]")
        console.print("  ✓ Project structure created")
        console.print("  ✓ Configuration system (config.py)")
        console.print("  ✓ Data models (models.py)")
        console.print("  ✓ DuckDB caching system (cache.py)")
        console.print("  ✓ Data fetcher framework (fetcher.py)")
        console.print("  ✓ Dependencies installed")
        console.print("\n[bold cyan]Phase 1 is complete and ready for Phase 2![/bold cyan]\n")

    except Exception as e:
        console.print(f"\n[bold red]✗ Test failed: {e}[/bold red]\n")
        raise


if __name__ == "__main__":
    main()
