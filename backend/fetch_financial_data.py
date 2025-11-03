"""
Fetch Historical Financial Data using yfinance - Investorly Dashboard

This script fetches ETF, stock, and index data for building personalized 
investment portfolios based on user risk profiles.

Usage:
    python fetch_financial_data.py                  # Full Investorly portfolio (23 ETFs + 3 indexes)
    python fetch_financial_data.py --quick          # Quick mode (5 essential ETFs)
    python fetch_financial_data.py --single VOO     # Fetch single ticker
    python fetch_financial_data.py --indices        # Fetch market indices only
    python fetch_financial_data.py --crypto         # Fetch cryptocurrency data
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

# Create dataset directory if it doesn't exist
DATASET_DIR = "./dataset"
os.makedirs(DATASET_DIR, exist_ok=True)


def fetch_and_save_ticker(ticker: str, period: str = "10y", filename: str = None):
    """
    Fetch historical data for a single ticker and save to CSV.
    
    Args:
        ticker: Stock/ETF ticker symbol (e.g., 'VOO', 'SPY')
        period: Time period to fetch (e.g., '1y', '5y', '10y', 'max')
        filename: Custom filename (optional, defaults to ticker name)
    """
    try:
        print(f"Fetching data for {ticker}...")
        
        # Download data - set auto_adjust=False to get 'Adj Close' column
        data = yf.download(ticker, period=period, progress=False, auto_adjust=False)
        
        if data.empty:
            print(f"  ⚠️  No data found for {ticker}")
            return False
        
        # Reset index to make Date a column
        data.reset_index(inplace=True)
        
        # Handle multi-level columns (when downloading single ticker, columns might be multi-index)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        # Add ticker column
        data['Ticker'] = ticker
        
        # Ensure all required columns exist
        required_cols = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in data.columns]
        
        if missing_cols:
            print(f"  ⚠️  Missing columns for {ticker}: {missing_cols}")
            return False
        
        # Reorder columns to match your existing format
        columns = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume', 'Ticker', 'Date']
        data = data[columns]
        
        # Save to CSV
        if filename is None:
            filename = f"{ticker.lower()}.csv"
        
        filepath = os.path.join(DATASET_DIR, filename)
        data.to_csv(filepath, index=False)
        
        print(f"  ✓ Saved {len(data)} records to {filepath}")
        return True
        
    except Exception as e:
        print(f"  ✗ Error fetching {ticker}: {str(e)}")
        return False


def fetch_multiple_tickers(tickers: list, period: str = "10y"):
    """
    Fetch historical data for multiple tickers.
    
    Args:
        tickers: List of ticker symbols
        period: Time period to fetch
    """
    successful = 0
    failed = 0
    
    for ticker in tickers:
        if fetch_and_save_ticker(ticker, period):
            successful += 1
        else:
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Summary: {successful} successful, {failed} failed")
    print(f"{'='*50}\n")


def fetch_etf_portfolio(period: str = "10y"):
    """
    Fetch data for a comprehensive portfolio of ETFs and index funds.
    """
    print("Fetching ETF Portfolio Data...\n")
    
    etfs = {
        # S&P 500 ETFs
        'VOO': 'Vanguard S&P 500 ETF',
        'SPY': 'SPDR S&P 500 ETF Trust',
        'IVV': 'iShares Core S&P 500 ETF',
        
        # Total Market ETFs
        'VTI': 'Vanguard Total Stock Market ETF',
        'ITOT': 'iShares Core S&P Total US Stock Market ETF',
        
        # International ETFs
        'VXUS': 'Vanguard Total International Stock ETF',
        'VEA': 'Vanguard FTSE Developed Markets ETF',
        'VWO': 'Vanguard FTSE Emerging Markets ETF',
        
        # Bond ETFs
        'BND': 'Vanguard Total Bond Market ETF',
        'AGG': 'iShares Core US Aggregate Bond ETF',
        'TLT': 'iShares 20+ Year Treasury Bond ETF',
        
        # Sector ETFs
        'VGT': 'Vanguard Information Technology ETF',
        'VHT': 'Vanguard Health Care ETF',
        'VFH': 'Vanguard Financials ETF',
        'VDE': 'Vanguard Energy ETF',
        
        # Dividend ETFs
        'VYM': 'Vanguard High Dividend Yield ETF',
        'SCHD': 'Schwab US Dividend Equity ETF',
        
        # Growth ETFs
        'VUG': 'Vanguard Growth ETF',
        'VONG': 'Vanguard Russell 1000 Growth ETF',
        
        # Small Cap
        'VB': 'Vanguard Small-Cap ETF',
        'IJR': 'iShares Core S&P Small-Cap ETF',
    }
    
    print("ETFs to fetch:")
    for ticker, name in etfs.items():
        print(f"  • {ticker} - {name}")
    print()
    
    fetch_multiple_tickers(list(etfs.keys()), period)


def fetch_crypto_data(period: str = "5y"):
    """
    Fetch cryptocurrency data (Bitcoin, Ethereum).
    Note: Crypto data availability may vary.
    """
    print("Fetching Cryptocurrency Data...\n")
    
    cryptos = ['BTC-USD', 'ETH-USD']
    
    for crypto in cryptos:
        fetch_and_save_ticker(crypto, period)


def fetch_market_indices(period: str = "10y"):
    """
    Fetch major market indices data.
    """
    print("Fetching Market Indices Data...\n")
    
    indices = {
        '^GSPC': 'S&P 500 Index',
        '^DJI': 'Dow Jones Industrial Average',
        '^IXIC': 'NASDAQ Composite',
        '^RUT': 'Russell 2000',
        '^VIX': 'CBOE Volatility Index',
    }
    
    print("Indices to fetch:")
    for ticker, name in indices.items():
        print(f"  • {ticker} - {name}")
    print()
    
    for ticker, name in indices.items():
        # Remove ^ from filename
        filename = f"index_{ticker.replace('^', '').lower()}.csv"
        fetch_and_save_ticker(ticker, period, filename)


def fetch_custom_tickers(tickers: list, period: str = "10y"):
    """
    Fetch data for custom list of tickers.
    
    Args:
        tickers: List of ticker symbols
        period: Time period
    """
    print(f"Fetching Custom Tickers: {', '.join(tickers)}\n")
    fetch_multiple_tickers(tickers, period)


def get_ticker_info(ticker: str):
    """
    Get detailed information about a ticker.
    
    Args:
        ticker: Ticker symbol
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        print(f"\nInformation for {ticker}:")
        print(f"{'='*50}")
        print(f"Name: {info.get('longName', 'N/A')}")
        print(f"Sector: {info.get('sector', 'N/A')}")
        print(f"Industry: {info.get('industry', 'N/A')}")
        print(f"Market Cap: ${info.get('marketCap', 0):,.0f}")
        print(f"52 Week High: ${info.get('fiftyTwoWeekHigh', 'N/A')}")
        print(f"52 Week Low: ${info.get('fiftyTwoWeekLow', 'N/A')}")
        print(f"Average Volume: {info.get('averageVolume', 'N/A'):,}")
        print(f"{'='*50}\n")
        
    except Exception as e:
        print(f"Error getting info for {ticker}: {str(e)}")


def fetch_investorly_portfolio(period: str = "10y"):
    """
    Fetch popular ETFs and indexes for Investorly portfolio recommendations.
    Includes 23 ETFs covering different risk levels and strategies.
    """
    print("\n" + "="*80)
    print("INVESTORLY - Fetching Popular ETFs & Indexes")
    print("="*80 + "\n")
    
    # Define portfolio components by category
    portfolio_data = {
        "🎯 Core S&P 500 ETFs (Low-cost, diversified)": [
            ('VOO', 'Vanguard S&P 500 ETF', 'Expense Ratio: 0.03%'),
            ('SPY', 'SPDR S&P 500 ETF Trust', 'Most liquid ETF'),
            ('IVV', 'iShares Core S&P 500 ETF', 'Expense Ratio: 0.03%'),
        ],
        "📊 Total Market ETFs (Entire US stock market)": [
            ('VTI', 'Vanguard Total Stock Market ETF', 'All US stocks'),
            ('ITOT', 'iShares Core S&P Total US Stock Market', 'Low-cost alternative'),
        ],
        "🌍 International Exposure (Geographic diversification)": [
            ('VXUS', 'Vanguard Total International Stock', 'All non-US stocks'),
            ('VEA', 'Vanguard FTSE Developed Markets', 'Developed countries'),
            ('VWO', 'Vanguard FTSE Emerging Markets', 'Emerging markets'),
        ],
        "🛡️ Bond ETFs (Conservative/Risk management)": [
            ('BND', 'Vanguard Total Bond Market ETF', 'All US bonds'),
            ('AGG', 'iShares Core US Aggregate Bond', 'Investment grade bonds'),
            ('TLT', 'iShares 20+ Year Treasury Bond', 'Long-term treasuries'),
        ],
        "💼 Sector ETFs (Targeted exposure)": [
            ('VGT', 'Vanguard Information Technology', 'Tech sector'),
            ('VHT', 'Vanguard Health Care ETF', 'Healthcare sector'),
            ('VFH', 'Vanguard Financials ETF', 'Financial sector'),
        ],
        "💰 Dividend ETFs (Income generation)": [
            ('VYM', 'Vanguard High Dividend Yield', 'Dividend growth'),
            ('SCHD', 'Schwab US Dividend Equity', 'Quality dividends'),
        ],
        "🚀 Growth ETFs (Higher risk/reward)": [
            ('VUG', 'Vanguard Growth ETF', 'Large-cap growth'),
            ('QQQ', 'Invesco QQQ Trust', 'NASDAQ-100'),
        ],
        "📈 Market Indexes (Benchmarking)": [
            ('^GSPC', 'S&P 500 Index', 'Key benchmark'),
            ('^DJI', 'Dow Jones Industrial Average', 'Blue chip index'),
            ('^IXIC', 'NASDAQ Composite', 'Tech-heavy index'),
        ],
    }
    
    # Display what will be fetched
    print("📦 Data to be fetched:\n")
    total_assets = 0
    for category, assets in portfolio_data.items():
        print(f"{category}")
        for ticker, name, note in assets:
            print(f"  • {ticker:8} - {name:40} ({note})")
            total_assets += 1
        print()
    
    print(f"Total: {total_assets} assets")
    print("\n" + "="*80)
    
    # Ask for confirmation
    response = input("\n🚀 Start downloading data? (y/n): ").strip().lower()
    
    if response != 'y':
        print("❌ Cancelled by user.")
        return
    
    print("\n" + "="*80)
    print("📥 Starting download... (This may take a few minutes)")
    print("="*80 + "\n")
    
    # Track results
    successful = []
    failed = []
    
    # Fetch data for each category
    for category, assets in portfolio_data.items():
        print(f"\n{category}")
        print("-" * 80)
        
        for ticker, name, note in assets:
            # For indexes, use custom filename
            if ticker.startswith('^'):
                filename = f"index_{ticker.replace('^', '').lower()}.csv"
                success = fetch_and_save_ticker(ticker, period=period, filename=filename)
            else:
                success = fetch_and_save_ticker(ticker, period=period)
            
            if success:
                successful.append((ticker, name))
            else:
                failed.append((ticker, name))
            
            print()
    
    # Print summary
    print("\n" + "="*80)
    print("📊 DOWNLOAD SUMMARY")
    print("="*80)
    print(f"\n✅ Successfully fetched: {len(successful)}/{total_assets}")
    
    if successful:
        print("\nSuccessful downloads:")
        for ticker, name in successful:
            print(f"  ✓ {ticker} - {name}")
    
    if failed:
        print(f"\n❌ Failed downloads: {len(failed)}")
        for ticker, name in failed:
            print(f"  ✗ {ticker} - {name}")
        print("\n💡 Tip: Failed downloads are usually due to:")
        print("   - Network connectivity issues")
        print("   - Invalid ticker symbols")
        print("   - Data not available for the requested period")
    
    print("\n" + "="*80)
    
    if len(successful) > 0:
        print("\n🎉 SUCCESS! Your data is ready!")
        print("\n📋 Next steps:")
        print("   1. Test the data:")
        print("      python cleanData.py")
        print()
        print("   2. Run your Streamlit dashboard:")
        print("      streamlit run ../frontend/test.py")
        print()
        print("   3. Build AI-powered portfolios based on:")
        print("      • User risk tolerance (Conservative → Aggressive)")
        print("      • Age and investment timeline")
        print("      • Income and investment amount")
        print("      • Investment goals (retirement, growth, income)")
        print()
        
        # Show portfolio allocation examples
        print("📊 Example Portfolio Allocations:")
        print()
        print("   Conservative (Age 60+, Low Risk):")
        print("      • 50% BND (Bonds)")
        print("      • 30% VOO (S&P 500)")
        print("      • 20% VYM (Dividend stocks)")
        print()
        print("   Moderate (Age 35-50, Medium Risk):")
        print("      • 60% VOO (S&P 500)")
        print("      • 25% VXUS (International)")
        print("      • 15% BND (Bonds)")
        print()
        print("   Aggressive (Age 20-35, High Risk):")
        print("      • 50% VTI (Total Market)")
        print("      • 30% QQQ (Tech Growth)")
        print("      • 20% VWO (Emerging Markets)")
        print()
    else:
        print("\n❌ No data was fetched successfully.")
        print("\n🔧 Troubleshooting:")
        print("   • Check your internet connection")
        print("   • Verify yfinance is installed: pip install yfinance")
        print("   • Try running: pip install --upgrade yfinance")
        print("   • Check if Yahoo Finance is accessible from your network")
    
    print("="*80 + "\n")


def fetch_quick_essentials():
    """
    Quick fetch of just the essential 5 ETFs for basic portfolio building.
    """
    print("\n" + "="*80)
    print("QUICK FETCH - Essential ETFs Only")
    print("="*80 + "\n")
    
    essentials = [
        ('VOO', 'Vanguard S&P 500 ETF'),
        ('BND', 'Vanguard Total Bond Market ETF'),
        ('VTI', 'Vanguard Total Stock Market ETF'),
        ('VXUS', 'Vanguard Total International Stock'),
        ('VYM', 'Vanguard High Dividend Yield'),
    ]
    
    print("These 5 ETFs cover all basic portfolio needs:\n")
    for ticker, name in essentials:
        print(f"  • {ticker} - {name}")
    
    print()
    response = input("Proceed? (y/n): ").strip().lower()
    
    if response != 'y':
        print("Cancelled.")
        return
    
    print("\nFetching data...\n")
    
    successful = 0
    for ticker, name in essentials:
        print(f"{name} ({ticker})")
        if fetch_and_save_ticker(ticker, period='10y'):
            successful += 1
        print()
    
    print("="*80)
    print(f"✅ Complete! {successful}/{len(essentials)} successful.")
    print("="*80 + "\n")


def show_help():
    """Display help information"""
    print("\n" + "="*80)
    print("INVESTORLY - Financial Data Fetcher")
    print("="*80 + "\n")
    print("Fetch historical ETF, stock, and index data for portfolio building.\n")
    print("Usage:")
    print("  python fetch_financial_data.py              # Full portfolio (23 ETFs + 3 indexes)")
    print("  python fetch_financial_data.py --quick      # Quick mode (5 essential ETFs)")
    print("  python fetch_financial_data.py --single VOO # Fetch single ticker")
    print("  python fetch_financial_data.py --indices    # Market indices only")
    print("  python fetch_financial_data.py --crypto     # Cryptocurrency data")
    print("  python fetch_financial_data.py --help       # Show this help")
    print()
    print("Examples:")
    print("  python fetch_financial_data.py --single AAPL")
    print("  python fetch_financial_data.py --single SPY --period 5y")
    print()
    print("="*80 + "\n")


def main():
    """Main entry point with command-line argument handling"""
    
    # Parse command-line arguments
    if len(sys.argv) == 1:
        # No arguments - run full Investorly portfolio fetch
        fetch_investorly_portfolio()
    
    elif '--help' in sys.argv or '-h' in sys.argv:
        show_help()
    
    elif '--quick' in sys.argv:
        fetch_quick_essentials()
    
    elif '--single' in sys.argv:
        try:
            idx = sys.argv.index('--single')
            ticker = sys.argv[idx + 1]
            
            # Check for custom period
            period = '10y'
            if '--period' in sys.argv:
                period_idx = sys.argv.index('--period')
                period = sys.argv[period_idx + 1]
            
            print(f"\nFetching {ticker} ({period} period)...\n")
            if fetch_and_save_ticker(ticker, period=period):
                print(f"\n✅ Successfully fetched {ticker}")
            else:
                print(f"\n❌ Failed to fetch {ticker}")
        except (IndexError, ValueError):
            print("❌ Error: Please provide a ticker symbol after --single")
            print("Example: python fetch_financial_data.py --single VOO")
    
    elif '--indices' in sys.argv:
        period = '10y'
        if '--period' in sys.argv:
            period_idx = sys.argv.index('--period')
            period = sys.argv[period_idx + 1]
        fetch_market_indices(period=period)
    
    elif '--crypto' in sys.argv:
        period = '5y'
        if '--period' in sys.argv:
            period_idx = sys.argv.index('--period')
            period = sys.argv[period_idx + 1]
        fetch_crypto_data(period=period)
    
    else:
        print("❌ Unknown command. Use --help for usage information.")
        show_help()


if __name__ == "__main__":
    main()

