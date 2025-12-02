"""
Fetch Historical Financial Data using yfinance

Usage:
    python fetch_financial_data.py                  # Fetch VOO and BTC
    python fetch_financial_data.py --single VOO     # Fetch single ticker
"""

import yfinance as yf
import pandas as pd
import os
import sys
from datetime import datetime, timedelta
import numpy as np

# Create dataset directory if it doesn't exist
DATASET_DIR = "/dataset"
os.makedirs(DATASET_DIR, exist_ok=True)

def generate_savings_data(apy: float, name: str, filename: str, years: int = 10):
    """
    Generate simulated savings account data with compound interest.

    Args:
        apy: Annual Percentage Yield (e.g., 0.034 for 3.4%)
        name: Name of the savings product (e.g., 'High Yield Savings')
        filename: Output CSV filename
        years: Number of years of historical data to generate (default 10)
    """
    try:
        # Calculate the date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=365 * years)

        # Generate daily dates
        dates = pd.date_range(start=start_date, end=end_date, freq='D')

        # For savings, the "price" is the account value growth
        # Daily compounding: daily_rate = (1 + APY)^(1/365)
        daily_rate = (1 + apy) ** (1/365)

        # Start with $100 (base unit price)
        prices = []
        for i in range(len(dates)):
            price = 100 * (daily_rate ** i)
            prices.append(price)

        # Create DataFrame
        data = pd.DataFrame({
            'Date': dates,
            'Open': prices,
            'High': prices,
            'Low': prices,
            'Close': prices,
            'Adj Close': prices,
            'Volume': [0] * len(dates),  # No volume for savings
            'Ticker': name
        })

        # Reorder columns
        data = data[['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume', 'Ticker', 'Date']]

        # Save to CSV
        filepath = os.path.join(DATASET_DIR, filename)
        data.to_csv(filepath, index=False)

        print(f"  Generated {len(data)} records for {name} ({apy*100:.2f}% APY)")
        print(f"  Saved to {filepath}")
        return True

    except Exception as e:
        print(f"  Error generating {name}: {str(e)}")
        return False


def generate_savings_accounts():
    """
    Generate historical data for HY Savings and CD (Capital One rates).
    Capital One rates: HY 3.40% APY, CD 3.50% APY
    """
    print("\n" + "="*80)
    print("INVESTORLY - Generating Savings Account Data")
    print("="*80 + "\n")

    savings_products = [
        (0.034, 'High Yield Savings', 'savings_hy.csv'),
        (0.035, 'Certificate of Deposit', 'savings_cd.csv'),
    ]

    print("Savings products to generate:\n")
    for apy, name, _ in savings_products:
        print(f"  - {name}: {apy*100:.2f}% APY")

    print("\n" + "="*80)
    response = input("\nGenerate savings data? (y/n): ").strip().lower()

    if response != 'y':
        print("Cancelled by user.")
        return

    print("\nGenerating data...\n")

    successful = 0
    total = len(savings_products)

    for apy, name, filename in savings_products:
        print(f"Generating {name}...")
        if generate_savings_data(apy, name, filename):
            successful += 1
        print()

    print("="*80)
    print("GENERATION SUMMARY")
    print("="*80)
    print(f"\nSuccessfully generated: {successful}/{total}\n")
    print("="*80 + "\n")


def fetch_and_save_ticker(ticker: str, period: str = "10y", filename: str = None, start_date: str = None):
    """
    Fetch historical data for a single ticker and save to CSV.

    Args:
        ticker: Stock/ETF ticker symbol (e.g., 'VOO', 'SPY')
        period: Time period to fetch (e.g., '1y', '5y', '10y', 'max')
        filename: Custom filename (optional, defaults to ticker name)
        start_date: Specific start date (e.g., '2015-11-25') - overrides period
    """
    try:
        print(f"Fetching data for {ticker}...")

        if start_date:
            data = yf.download(ticker, start=start_date, progress=False, auto_adjust=False)
        else:
            data = yf.download(ticker, period=period, progress=False, auto_adjust=False)

        if data.empty:
            print(f"  No data found for {ticker}")
            return False

        data.reset_index(inplace=True)

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data['Ticker'] = ticker

        required_cols = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in data.columns]

        if missing_cols:
            print(f"  Missing columns for {ticker}: {missing_cols}")
            return False

        columns = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume', 'Ticker', 'Date']
        data = data[columns]

        # Save to CSV
        if filename is None:
            filename = f"{ticker.lower()}.csv"

        filepath = os.path.join(DATASET_DIR, filename)
        data.to_csv(filepath, index=False)

        print(f"  Saved {len(data)} records to {filepath}")
        return True

    except Exception as e:
        print(f"  Error fetching {ticker}: {str(e)}")
        return False




def fetch_essential_assets():
    """
    Fetch essential assets: VOO (stock) and BTC (crypto).
    """
    print("\n" + "="*80)
    print("INVESTORLY - Fetching Essential Assets")
    print("="*80 + "\n")

    assets = [
        ('VOO', 'Vanguard S&P 500 ETF'),
        ('BTC-USD', 'Bitcoin')
    ]

    print("Assets to fetch:\n")
    for ticker, name in assets:
        print(f"  - {ticker}: {name}")

    print("\n" + "="*80)
    response = input("\nStart downloading data? (y/n): ").strip().lower()

    if response != 'y':
        print("Cancelled by user.")
        return

    print("\nStarting download...\n")

    successful = 0
    total = len(assets)

    # Fetch VOO (ETF)
    print("Fetching VOO (Vanguard S&P 500 ETF)...")
    if fetch_and_save_ticker('VOO', period='10y'):
        successful += 1
    print()

    # Fetch BTC (Crypto)
    print("Fetching BTC-USD (Bitcoin)...")
    if fetch_and_save_ticker('BTC-USD', period='10y', filename='crypto_btc.csv'):
        successful += 1
    print()

    # summary
    print("="*80)
    print("DOWNLOAD SUMMARY")
    print("="*80)
    print(f"\nSuccessfully fetched: {successful}/{total}\n")

    if successful == total:
        print("SUCCESS! Your data is ready!")
        print("\nNext steps:")
        print("   1. Run your Streamlit dashboard:")
        print("      streamlit run ../frontend/app.py")
    else:
        print("Some downloads failed. Check your internet connection.")

    print("="*80 + "\n")


def show_help():
    """Display help information"""
    print("\n" + "="*80)
    print("INVESTORLY - Financial Data Fetcher")
    print("="*80 + "\n")
    print("Fetch historical data for VOO (stock) and BTC (crypto).\n")
    print("Usage:")
    print("  python fetch_financial_data.py              # Fetch VOO and BTC")
    print("  python fetch_financial_data.py --single VOO # Fetch single ticker")
    print("  python fetch_financial_data.py --help       # Show this help")
    print()
    print("Examples:")
    print("  python fetch_financial_data.py --single VOO")
    print("  python fetch_financial_data.py --single BTC-USD --period 5y")
    print()
    print("="*80 + "\n")


def main():
    """Main entry point with command-line argument handling"""

    # Parse command-line arguments
    if len(sys.argv) == 1:
        fetch_essential_assets()

    elif '--help' in sys.argv or '-h' in sys.argv:
        show_help()

    elif '--single' in sys.argv:
        try:
            idx = sys.argv.index('--single')
            ticker = sys.argv[idx + 1]

            period = '10y'
            if '--period' in sys.argv:
                period_idx = sys.argv.index('--period')
                period = sys.argv[period_idx + 1]

            start_date = None
            if '--start' in sys.argv:
                start_idx = sys.argv.index('--start')
                start_date = sys.argv[start_idx + 1]

            filename = None
            if '-USD' in ticker:
                crypto_symbol = ticker.replace('-USD', '').lower()
                filename = f"crypto_{crypto_symbol}.csv"

            if start_date:
                print(f"\nFetching {ticker} (from {start_date})...\n")
            else:
                print(f"\nFetching {ticker} ({period} period)...\n")

            if fetch_and_save_ticker(ticker, period=period, filename=filename, start_date=start_date):
                print(f"\nSuccessfully fetched {ticker}")
            else:
                print(f"\nFailed to fetch {ticker}")
        except (IndexError, ValueError):
            print("Error: Please provide a ticker symbol after --single")
            print("Example: python fetch_financial_data.py --single VOO")
            print("Example: python fetch_financial_data.py --single VOO --start 2015-11-25")

    else:
        print("Unknown command. Use --help for usage information.")
        show_help()


if __name__ == "__main__":
    main()

