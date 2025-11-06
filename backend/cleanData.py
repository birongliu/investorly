import pandas as pd
import os


def load_etf_data(ticker: str, dataset_dir: str = "./dataset") -> pd.DataFrame:
    """
    Load ETF/stock data from CSV file.
    
    Args:
        ticker: Ticker symbol (e.g., 'VOO', 'SPY')
        dataset_dir: Directory containing the CSV files
        
    Returns:
        DataFrame with the ticker's historical data
    """
    filename = f"df_{ticker.lower()}.csv"
    filepath = os.path.join(dataset_dir, filename)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    
    return df


def load_index_data(index_symbol: str, dataset_dir: str = "./dataset") -> pd.DataFrame:
    """
    Load market index data from CSV file.
    
    Args:
        index_symbol: Index symbol (e.g., 'GSPC' for S&P 500, 'DJI' for Dow Jones)
        dataset_dir: Directory containing the CSV files
        
    Returns:
        DataFrame with the index's historical data
    """
    filename = f"index_{index_symbol.lower()}.csv"
    filepath = os.path.join(dataset_dir, filename)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    
    return df


def load_crypto_data(crypto_symbol: str, dataset_dir: str = "./dataset") -> pd.DataFrame:
    """
    Load cryptocurrency data from CSV file.
    
    Args:
        crypto_symbol: Crypto symbol (e.g., 'BTC' for Bitcoin, 'ETH' for Ethereum)
        dataset_dir: Directory containing the CSV files
        
    Returns:
        DataFrame with the crypto's historical data
    """
    filename = f"crypto_{crypto_symbol.lower()}.csv"
    filepath = os.path.join(dataset_dir, filename)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    
    return df


def calculate_returns(df: pd.DataFrame, initial_investment: float = 10000) -> pd.DataFrame:
    """
    Calculate investment returns over time.
    
    Args:
        df: DataFrame with historical price data
        initial_investment: Initial investment amount in dollars
        
    Returns:
        DataFrame with additional columns for returns and portfolio value
    """
    df = df.copy()
    
    # Calculate daily returns
    df['Daily_Return'] = df['Adj Close'].pct_change()
    
    # Calculate cumulative returns
    df['Cumulative_Return'] = (1 + df['Daily_Return']).cumprod()
    
    # Calculate portfolio value
    starting_price = df['Adj Close'].iloc[0]
    df['Portfolio_Value'] = (df['Adj Close'] / starting_price) * initial_investment
    
    # Calculate dollar gain/loss
    df['Gain_Loss'] = df['Portfolio_Value'] - initial_investment
    
    # Calculate percentage gain/loss
    df['Gain_Loss_Pct'] = ((df['Portfolio_Value'] - initial_investment) / initial_investment) * 100
    
    return df


def filter_by_date_range(df: pd.DataFrame, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    Filter DataFrame by date range.
    
    Args:
        df: DataFrame with Date column
        start_date: Start date (YYYY-MM-DD format)
        end_date: End date (YYYY-MM-DD format)
        
    Returns:
        Filtered DataFrame
    """
    df = df.copy()
    
    if start_date:
        df = df[df['Date'] >= pd.to_datetime(start_date)]
    
    if end_date:
        df = df[df['Date'] <= pd.to_datetime(end_date)]
    
    return df


def get_performance_metrics(df: pd.DataFrame) -> dict:
    """
    Calculate performance metrics for an investment.
    
    Args:
        df: DataFrame with returns data
        
    Returns:
        Dictionary with performance metrics
    """
    if 'Daily_Return' not in df.columns:
        df = calculate_returns(df)
    
    metrics = {
        'total_return_pct': df['Gain_Loss_Pct'].iloc[-1],
        'total_return_dollar': df['Gain_Loss'].iloc[-1],
        'final_value': df['Portfolio_Value'].iloc[-1],
        'avg_daily_return': df['Daily_Return'].mean() * 100,
        'volatility': df['Daily_Return'].std() * 100,
        'max_price': df['Adj Close'].max(),
        'min_price': df['Adj Close'].min(),
        'current_price': df['Adj Close'].iloc[-1],
    }
    
    return metrics


# Example usage
if __name__ == "__main__":
    # Load VOO data
    df = load_etf_data('VOO')
    print(f"Loaded {len(df)} records for VOO")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}\n")
    
    # Calculate returns for $10,000 investment
    df_with_returns = calculate_returns(df, initial_investment=10000)
    
    # Get performance metrics
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

