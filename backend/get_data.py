import pandas as pd
import os


def load_etf_data(ticker: str, dataset_dir: str = "./dataset") -> pd.DataFrame:
    """Load ETF data - tries multiple filename patterns for compatibility"""
    patterns = [
        f"{ticker.lower()}.csv",      # New pattern: spy.csv, qqq.csv
        f"df_{ticker.lower()}.csv",   # Legacy pattern: df_voo.csv
    ]

    for filename in patterns:
        filepath = os.path.join(dataset_dir, filename)
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')
            return df

    raise FileNotFoundError(f"Data file not found for {ticker}. Tried: {patterns}")


def load_index_data(index_symbol: str, dataset_dir: str = "./dataset") -> pd.DataFrame:
    filename = f"index_{index_symbol.lower()}.csv"
    filepath = os.path.join(dataset_dir, filename)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    
    return df


def load_crypto_data(crypto_symbol: str, dataset_dir: str = "./dataset") -> pd.DataFrame:
    """Load crypto data - supports symbols like BTC, ETH, SOL, etc."""
    filename = f"crypto_{crypto_symbol.lower()}.csv"
    filepath = os.path.join(dataset_dir, filename)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")

    df = pd.read_csv(filepath)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')

    return df


def load_fixed_income_data(product_type: str, dataset_dir: str = "./dataset") -> pd.DataFrame:
    #Loads fixed-income product data from CSV file (HY Savings, CD).
    filename = f"df_{product_type.lower()}.csv"
    filepath = os.path.join(dataset_dir, filename)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")

    df = pd.read_csv(filepath)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')

    return df


def calculate_returns(df: pd.DataFrame, initial_investment: float = 10000) -> pd.DataFrame:
    # Calculate investment returns over time.
    df = df.copy()

    # Determine which price column to use (Adj Close for stocks/ETFs, Close for fixed-income)
    price_column = 'Adj Close' if 'Adj Close' in df.columns else 'Close'

    df['Daily_Return'] = df[price_column].pct_change()

    df['Cumulative_Return'] = (1 + df['Daily_Return']).cumprod()

    starting_price = df[price_column].iloc[0]
    df['Portfolio_Value'] = (df[price_column] / starting_price) * initial_investment

    df['Gain_Loss'] = df['Portfolio_Value'] - initial_investment

    df['Gain_Loss_Pct'] = ((df['Portfolio_Value'] - initial_investment) / initial_investment) * 100

    return df


def filter_by_date_range(df: pd.DataFrame, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    df = df.copy()
    
    if start_date:
        df = df[df['Date'] >= pd.to_datetime(start_date)]
    
    if end_date:
        df = df[df['Date'] <= pd.to_datetime(end_date)]
    
    return df


def get_performance_metrics(df: pd.DataFrame) -> dict:
    # Calculate performance metrics for an investment.
    if 'Daily_Return' not in df.columns:
        df = calculate_returns(df)

    price_column = 'Adj Close' if 'Adj Close' in df.columns else 'Close'

    metrics = {
        'total_return_pct': df['Gain_Loss_Pct'].iloc[-1],
        'total_return_dollar': df['Gain_Loss'].iloc[-1],
        'final_value': df['Portfolio_Value'].iloc[-1],
        'avg_daily_return': df['Daily_Return'].mean() * 100,
        'volatility': df['Daily_Return'].std() * 100,
        'max_price': df[price_column].max(),
        'min_price': df[price_column].min(),
        'current_price': df[price_column].iloc[-1],
    }

    return metrics


if __name__ == "__main__":
    # test
    df = load_etf_data('VOO')
    print(f"Loaded {len(df)} records for VOO")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}\n")
    
    df_with_returns = calculate_returns(df, initial_investment=10000)
    
    metrics = get_performance_metrics(df_with_returns)
    
    print("Performance Metrics:")
    print(f"  Total Return: {metrics['total_return_pct']:.2f}%")
    print(f"  Total Gain/Loss: ${metrics['total_return_dollar']:,.2f}")
    print(f"  Final Portfolio Value: ${metrics['final_value']:,.2f}")
    print(f"  Average Daily Return: {metrics['avg_daily_return']:.4f}%")
    print(f"  Volatility (Std Dev): {metrics['volatility']:.4f}%")
    print(f"  Current Price: ${metrics['current_price']:.2f}")
    print(f"  Max Price: ${metrics['max_price']:.2f}")
    print(f"  Min Price: ${metrics['min_price']:.2f}")

