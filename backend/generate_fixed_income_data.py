"""
Generate simulated historical data for High-Yield Savings Account and Certificate of Deposit (CD)
with realistic daily compounding interest rates.
"""

import pandas as pd
from datetime import datetime, timedelta
import os

def generate_daily_compound_data(start_date, end_date, apy, initial_value=10000):
    """
    Generate daily compounded interest data for fixed-income products.

    Args:
        start_date: Start date for data generation
        end_date: End date for data generation
        apy: Annual Percentage Yield (as decimal, e.g., 0.034 for 3.4%)
        initial_value: Starting principal amount

    Returns:
        DataFrame with Date and Close columns representing account value over time
    """
    dates = []
    values = []

    current_date = start_date
    current_value = initial_value

    # Daily interest rate (APY to daily rate with 365 compounding periods)
    daily_rate = (1 + apy) ** (1/365) - 1

    while current_date <= end_date:
        dates.append(current_date)
        values.append(current_value)

        current_value = current_value * (1 + daily_rate)
        current_date += timedelta(days=1)

    df = pd.DataFrame({
        'Date': dates,
        'Close': values
    })

    return df

def main():
    # Set date range: 10 years of data (11/25/2015 to 11/24/2025)
    start_date = datetime(2015, 11, 25)
    end_date = datetime(2025, 11, 24)

    # Generate HY Savings data (3.40% APY)
    print("Generating High-Yield Savings Account data (3.40% APY)...")
    hy_savings_df = generate_daily_compound_data(
        start_date=start_date,
        end_date=end_date,
        apy=0.034,  # 3.40%
        initial_value=10000
    )

    # Generate CD data (3.50% APY)
    print("Generating Certificate of Deposit data (3.50% APY)...")
    cd_df = generate_daily_compound_data(
        start_date=start_date,
        end_date=end_date,
        apy=0.035,  # 3.50%
        initial_value=10000
    )

    # Save to dataset directory
    dataset_dir = os.path.join(os.path.dirname(__file__), 'dataset')
    os.makedirs(dataset_dir, exist_ok=True)

    hy_savings_path = os.path.join(dataset_dir, 'df_hy_savings.csv')
    cd_path = os.path.join(dataset_dir, 'df_cd.csv')

    hy_savings_df.to_csv(hy_savings_path, index=False)
    cd_df.to_csv(cd_path, index=False)

    # print(f"\nHY Savings data saved to: {hy_savings_path}")
    # print(f"CD data saved to: {cd_path}")

    # print(f"\nHY Savings Summary:")
    # print(f"  Start Date: {hy_savings_df['Date'].min()}")
    # print(f"  End Date: {hy_savings_df['Date'].max()}")
    # print(f"  Initial Value: ${hy_savings_df['Close'].iloc[0]:,.2f}")
    # print(f"  Final Value: ${hy_savings_df['Close'].iloc[-1]:,.2f}")
    # print(f"  Total Return: {((hy_savings_df['Close'].iloc[-1] / hy_savings_df['Close'].iloc[0]) - 1) * 100:.2f}%")

    # print(f"\nCD Summary:")
    # print(f"  Start Date: {cd_df['Date'].min()}")
    # print(f"  End Date: {cd_df['Date'].max()}")
    # print(f"  Initial Value: ${cd_df['Close'].iloc[0]:,.2f}")
    # print(f"  Final Value: ${cd_df['Close'].iloc[-1]:,.2f}")
    # print(f"  Total Return: {((cd_df['Close'].iloc[-1] / cd_df['Close'].iloc[0]) - 1) * 100:.2f}%")

if __name__ == "__main__":
    main()
