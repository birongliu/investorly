import os
import sys
from datetime import datetime, timedelta

import streamlit as st
import requests

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from get_data import load_etf_data, load_crypto_data, load_index_data, load_fixed_income_data, calculate_returns, get_performance_metrics, filter_by_date_range
from generate_fixed_income_data import generate_daily_compound_data

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:5000")

st.set_page_config(
    page_title="Investorly",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
.stMainBlockContainer {
    padding-top: 0rem !important;
}
div[data-testid="stMainBlockContainer"] {
    padding-top: 0rem !important;
}
.stButton button {
    width: 100%;
}
.main {
    padding: 0rem 0.5rem 0.5rem 0.5rem;
    max-width: 100%;
}
[data-testid="stVerticalBlock"] {
    gap: 0.5rem;
}
.asset-selector {
    padding: 0.5rem;
    border-radius: 0.5rem;
    margin-bottom: 0.5rem;
}
.stMarkdownContainer {
    padding: 0 !important;
}
[data-testid="stAppViewContainer"] {
    padding-top: 0rem;
    padding-left: 0.5rem;
    padding-right: 0.5rem;
}
header[data-testid="stHeader"] {
    padding-top: 0rem !important;
    margin-top: 0rem !important;
}
.main .block-container {
    padding-top: 0rem !important;
    padding-bottom: 1rem !important;
    margin-top: 0rem !important;
}
section.main > div {
    padding-top: 0rem !important;
}
section.main > div:first-child {
    padding-top: 0rem !important;
    margin-top: 0rem !important;
}
.stApp {
    padding-top: 0rem !important;
    margin-top: 0rem !important;
}
.st-emotion-cache-zyqvyx, .st-emotion-cache-z5fcl4 {
    padding-top: 0rem !important;
}
[data-testid="stAppViewContainer"] > section {
    padding-top: 0rem !important;
}
section[tabindex="0"] {
    padding-top: 0rem !important;
}
hr {
    margin: 0.5rem 0;
}
[data-testid="stMetricLabel"] {
    font-size: 0.85rem !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

[data-testid="stMetricValue"] {
    font-size: 1.1rem !important;
    white-space: nowrap;
    overflow: visible;
}

[data-testid="column"] {
    position: relative;
    border-right: 2px solid rgba(128, 128, 128, 0.15);
}

[data-testid="column"]:last-child {
    border-right: none;
}

[data-testid="column"]::before {
    content: '';
    position: absolute;
    right: -8px;
    top: 0;
    width: 16px;
    height: 100%;
    cursor: col-resize;
    z-index: 999;
    background: transparent;
    transition: all 0.2s ease;
}

[data-testid="column"]:hover::before {
    background: rgba(100, 149, 237, 0.2);
    box-shadow: 0 0 8px rgba(100, 149, 237, 0.3);
}

[data-testid="column"].resizing::before {
    background: rgba(100, 149, 237, 0.4);
    box-shadow: 0 0 12px rgba(100, 149, 237, 0.5);
}

[data-testid="column"]::after {
    content: '';
    position: absolute;
    right: -1px;
    top: 0;
    width: 2px;
    height: 100%;
    background: rgba(128, 128, 128, 0.15);
    z-index: 1000;
    pointer-events: none;
    transition: all 0.2s ease;
}

[data-testid="column"]:hover::after {
    background: rgba(100, 149, 237, 0.6);
    width: 3px;
    right: -1.5px;
}

[data-testid="column"].resizing::after {
    background: rgba(100, 149, 237, 0.8);
    width: 4px;
    right: -2px;
}
</style>
""", unsafe_allow_html=True)


header_cols = st.columns([4, 1, 1])
with header_cols[0]:
    st.title("📈 Investorly")
st.divider()

# Hide Streamlit header (stAppDeployButton, stMainMenu)
hide_streamlit_style = """
    <style>
    /* Hide the top header / toolbar */
    header[data-testid="stHeader"] {
        display: none;
    }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


investment_map = {
    "$0 - $1,000": 500,
    "$1,000 - $5,000": 3000,
    "$5,000 - $10,000": 7500,
    "$10,000 - $50,000": 30000,
    "$50,000+": 50000
}

ASSETS = {
    'stock': {
        'SPY': {'name': 'SPDR S&P 500 ETF Trust', 'icon': '🕷️', 'category': 'Stock', 'ticker_yf': 'SPY'},
        'VOO': {'name': 'Vanguard S&P 500 ETF', 'icon': '🏛️', 'category': 'Stock', 'ticker_yf': 'VOO'},
        'QQQ': {'name': 'Invesco QQQ (Nasdaq-100)', 'icon': '🚀', 'category': 'Stock', 'ticker_yf': 'QQQ'},
        'VTI': {'name': 'Vanguard Total Stock Market ETF', 'icon': '📊', 'category': 'Stock', 'ticker_yf': 'VTI'},
        'IVV': {'name': 'iShares Core S&P 500 ETF', 'icon': '🏢', 'category': 'Stock', 'ticker_yf': 'IVV'},
        'SCHD': {'name': 'Schwab US Dividend Equity ETF', 'icon': '💵', 'category': 'Stock', 'ticker_yf': 'SCHD'},
        'VUG': {'name': 'Vanguard Growth ETF', 'icon': '📈', 'category': 'Stock', 'ticker_yf': 'VUG'},
        'IWM': {'name': 'iShares Russell 2000 ETF', 'icon': '🏭', 'category': 'Stock', 'ticker_yf': 'IWM'},
        'VEA': {'name': 'Vanguard FTSE Developed Markets ETF', 'icon': '🌍', 'category': 'Stock', 'ticker_yf': 'VEA'},
        'AGG': {'name': 'iShares Core US Aggregate Bond ETF', 'icon': '📜', 'category': 'Stock', 'ticker_yf': 'AGG'},
    },
    'crypto': {
        'BTC': {'name': 'Bitcoin', 'icon': '₿', 'category': 'Cryptocurrency', 'ticker_yf': 'BTC-USD'},
        'ETH': {'name': 'Ethereum', 'icon': '⟠', 'category': 'Cryptocurrency', 'ticker_yf': 'ETH-USD'},
        'BNB': {'name': 'Binance Coin', 'icon': '🔶', 'category': 'Cryptocurrency', 'ticker_yf': 'BNB-USD'},
        'SOL': {'name': 'Solana', 'icon': '◎', 'category': 'Cryptocurrency', 'ticker_yf': 'SOL-USD'},
        'XRP': {'name': 'Ripple', 'icon': '💧', 'category': 'Cryptocurrency', 'ticker_yf': 'XRP-USD'},
        'ADA': {'name': 'Cardano', 'icon': '₳', 'category': 'Cryptocurrency', 'ticker_yf': 'ADA-USD'},
        'DOGE': {'name': 'Dogecoin', 'icon': '🐕', 'category': 'Cryptocurrency', 'ticker_yf': 'DOGE-USD'},
        'AVAX': {'name': 'Avalanche', 'icon': '🔺', 'category': 'Cryptocurrency', 'ticker_yf': 'AVAX-USD'},
    },
    'fixed_income': {
        'HY_SAVINGS': {'name': 'High-Yield Savings (Capital One 3.40% APY)', 'icon': '🏦', 'category': 'Fixed Income', 'ticker_yf': None},
        'CD': {'name': 'Certificate of Deposit (Capital One 3.50% APY)', 'icon': '💰', 'category': 'Fixed Income', 'ticker_yf': None},
    }
}

if 'right_panel_visible' not in st.session_state:
    st.session_state.right_panel_visible = True

if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

if 'investment_amount' not in st.session_state:
    st.session_state.investment_amount = 10000

if 'risk_scale' not in st.session_state:
    st.session_state.risk_scale = 5

if 'selected_assets' not in st.session_state:
    st.session_state.selected_assets = {'VOO': 40, 'BTC': 40, 'HY_SAVINGS': 10, 'CD': 10}  # Default allocation

if 'enabled_assets' not in st.session_state:
    st.session_state.enabled_assets = ['VOO', 'BTC', 'HY_SAVINGS', 'CD']

if 'last_edited_asset' not in st.session_state:
    st.session_state.last_edited_asset = None

if 'last_total_allocation' not in st.session_state:
    st.session_state.last_total_allocation = 100

if 'last_risk_scale' not in st.session_state:
    st.session_state.last_risk_scale = 5

if 'hy_savings_rate' not in st.session_state:
    st.session_state.hy_savings_rate = 3.40  # Default HY Savings APY

if 'cd_rate' not in st.session_state:
    st.session_state.cd_rate = 3.50  # Default CD APY

def get_asset_type(ticker):
    for category, assets in ASSETS.items():
        if ticker in assets:
            if category == 'crypto':
                return 'crypto'
            elif category == 'indices':
                return 'index'
            elif category == 'fixed_income':
                return 'fixed_income'
            else:
                return 'etf'
    return 'etf'

def load_data_safe(ticker):
    try:
        dataset_dir = os.path.join(os.path.dirname(__file__), '..', 'backend', 'dataset')
        asset_type = get_asset_type(ticker)

        if asset_type == 'crypto':
            return load_crypto_data(ticker, dataset_dir)
        elif asset_type == 'index':
            return load_index_data(ticker, dataset_dir)
        elif asset_type == 'fixed_income':
            # Generate data dynamically based on custom rates
            if ticker == 'HY_SAVINGS':
                rate = st.session_state.get('hy_savings_rate', 3.40)
            elif ticker == 'CD':
                rate = st.session_state.get('cd_rate', 3.50)
            else:
                return load_fixed_income_data(ticker.lower(), dataset_dir)

            # Generate data from 2015-11-25 to today
            start_date = datetime(2015, 11, 25)
            end_date = datetime.now()

            # Generate dynamic data with custom rate
            df = generate_daily_compound_data(
                start_date=start_date,
                end_date=end_date,
                apy=rate,  
                initial_value=10000
            )
            return df
        else:
            return load_etf_data(ticker, dataset_dir)
    except Exception as e:
        return None

def calculate_portfolio_returns(investment_amount, investment_date, allocations):
    try:
        total_current_value = 0
        total_gain_loss = 0
        breakdown = {}
        errors = []

        for asset, percentage in allocations.items():
            if percentage <= 0:
                continue

            dollar_amount = (percentage / 100) * investment_amount

            df = load_data_safe(asset)
            if df is None:
                errors.append(f"Could not load data for {asset}")
                continue

            df_filtered = filter_by_date_range(df, start_date=str(investment_date))
            if df_filtered.empty:
                errors.append(f"No data available for {asset} from {investment_date}")
                continue

            df_returns = calculate_returns(df_filtered, initial_investment=dollar_amount)
            metrics = get_performance_metrics(df_returns)

            asset_info = None
            for category, assets in ASSETS.items():
                if asset in assets:
                    asset_info = assets[asset]
                    break

            breakdown[asset] = {
                'initial': dollar_amount,
                'current': metrics['final_value'],
                'gain_loss': metrics['total_return_dollar'],
                'gain_loss_pct': metrics['total_return_pct'],
                'volatility': metrics['volatility'],
                'avg_daily_return': metrics['avg_daily_return'],
                'current_price': metrics['current_price'],
                'max_price': metrics['max_price'],
                'min_price': metrics['min_price'],
                'data': df_returns,
                'info': asset_info
            }

            total_current_value += metrics['final_value']
            total_gain_loss += metrics['total_return_dollar']

        if not breakdown:
            return None, errors

        return {
            'total_initial': investment_amount,
            'total_current': total_current_value,
            'total_gain_loss': total_gain_loss,
            'total_gain_loss_pct': (total_gain_loss / investment_amount) * 100 if investment_amount > 0 else 0,
            'breakdown': breakdown
        }, errors
    except Exception as e:
        return None, [str(e)]

def get_all_tickers():
    tickers = []
    for category, assets in ASSETS.items():
        tickers.extend(list(assets.keys()))
    return sorted(tickers)

def get_ai_response(messages, portfolio_results, investment_date, normalized_allocations):
    """
    Call the Flask backend to get AI chatbot response
    
    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
        portfolio_results: Portfolio performance data
        investment_date: Date of investment
        normalized_allocations: Current asset allocations
    
    Returns:
        String response from the AI or fallback response on error
    """
    try:
        settings = {
            "experience_level": "beginner",
            "risk_tolerance": st.session_state.risk_scale,
            "investment_amount": st.session_state.investment_amount,
            "current_allocation": normalized_allocations,
        }

        portfolio_performance = None
        if portfolio_results:
            unallocated_pct = 100 - sum(normalized_allocations.values())
            unallocated_cash = (unallocated_pct / 100) * st.session_state.investment_amount
            total_current_with_cash = portfolio_results['total_current'] + unallocated_cash
            total_gain_loss = total_current_with_cash - st.session_state.investment_amount
            total_gain_loss_pct = (total_gain_loss / st.session_state.investment_amount) * 100 if st.session_state.investment_amount > 0 else 0
            
            portfolio_performance = {
                "initial_investment": st.session_state.investment_amount,
                "current_value": total_current_with_cash,
                "total_gain_loss": total_gain_loss,
                "total_gain_loss_pct": total_gain_loss_pct,
                "unallocated_cash": unallocated_cash
            }

        asset_breakdown = []
        if portfolio_results:
            for asset, data in portfolio_results['breakdown'].items():
                asset_info = data.get('info', {})
                asset_breakdown.append({
                    "ticker": asset,
                    "name": asset_info.get('name', asset),
                    "category": asset_info.get('category', 'Unknown'),
                    "initial_investment": data['initial'],
                    "current_value": data['current'],
                    "gain_loss": data['gain_loss'],
                    "gain_loss_pct": data['gain_loss_pct'],
                    "volatility": data['volatility'],
                    "current_price": data['current_price']
                })

        context = {
            "user_settings": settings,
            "portfolio_performance": portfolio_performance,
            "asset_breakdown": asset_breakdown,
            "investment_dates": {
                "start_date": str(investment_date),
                "current_date": datetime.now().strftime("%Y-%m-%d")
            }
        }
        
        response = requests.post(
            f"{BACKEND_BASE_URL}/api/v1/llm",
            json={"messages": messages, "context": context},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            messageAI = data.get("response", "I'm having trouble responding right now.")
            return messageAI
        
    except Exception as e:
        print(e)
        # Fallback to keyword-based responses if backend is unreachable
        return get_fallback_response(messages[-1]["content"])

def get_risk_from_allocation(allocations):
    """
    Calculate the implied risk level (1-10) from the current allocation.
    Dynamically calculates based on stock vs crypto ratio.

    Logic:
    - High Stock, Low Crypto → Conservative (1-3)
    - Balanced Stock/Crypto → Moderate (4-6)
    - Low Stock, High Crypto → Aggressive (7-10)

    Args:
        allocations: Dictionary of asset allocations {ticker: percentage}

    Returns:
        int: Risk level (1-10)
    """
    stock_total = 0
    crypto_total = 0

    for ticker, pct in allocations.items():
        for category, assets in ASSETS.items():
            if ticker in assets:
                if category == 'stock':
                    stock_total += pct
                elif category == 'crypto':
                    crypto_total += pct
                break

    total_invested = stock_total + crypto_total

    if total_invested == 0:
        return 5  # Default 

    crypto_ratio = crypto_total / total_invested  

    # Map crypto ratio to risk level
    # 0-10% Crypto → Risk 1-2 (Very Conservative)
    # 10-30% Crypto → Risk 3-4 (Conservative)
    # 30-50% Crypto → Risk 5-6 (Moderate)
    # 50-70% Crypto → Risk 7-8 (Aggressive)
    # 70-100% Crypto → Risk 9-10 (Very Aggressive)

    if crypto_ratio <= 0.1:
        return 1
    elif crypto_ratio <= 0.2:
        return 2
    elif crypto_ratio <= 0.3:
        return 3
    elif crypto_ratio <= 0.4:
        return 4
    elif crypto_ratio <= 0.5:
        return 5
    elif crypto_ratio <= 0.6:
        return 6
    elif crypto_ratio <= 0.7:
        return 7
    elif crypto_ratio <= 0.8:
        return 8
    elif crypto_ratio <= 0.9:
        return 9
    else:
        return 10

def get_risk_based_allocation(risk_level, enabled_assets=None):
    """
    Calculate suggested asset allocations based on risk tolerance (1-10 scale).
    Dynamically distributes allocation across enabled assets.

    Risk Level Logic:
    - 1-3 (Conservative): High Fixed Income, Moderate Stocks, Low Crypto
    - 4-6 (Moderate): Balanced with some Fixed Income
    - 7-10 (Aggressive): Low Fixed Income, Low Stocks, High Crypto

    Args:
        risk_level: Risk tolerance (1-10)
        enabled_assets: List of enabled asset tickers (optional)

    Returns:
        dict: Asset allocations based on risk level
    """
    if enabled_assets is None:
        enabled_assets = st.session_state.get('enabled_assets', ['VOO', 'BTC', 'HY_SAVINGS', 'CD'])

    if risk_level <= 2:
        base = {'stock': 40, 'crypto': 5, 'fixed_income': 40, 'cash': 15}
    elif risk_level == 3:
        base = {'stock': 45, 'crypto': 10, 'fixed_income': 30, 'cash': 15}
    elif risk_level == 4:
        base = {'stock': 50, 'crypto': 20, 'fixed_income': 20, 'cash': 10}
    elif risk_level == 5:
        base = {'stock': 50, 'crypto': 30, 'fixed_income': 10, 'cash': 10}
    elif risk_level == 6:
        base = {'stock': 40, 'crypto': 40, 'fixed_income': 10, 'cash': 10}
    elif risk_level == 7:
        base = {'stock': 30, 'crypto': 55, 'fixed_income': 0, 'cash': 15}
    elif risk_level == 8:
        base = {'stock': 20, 'crypto': 65, 'fixed_income': 0, 'cash': 15}
    else:  # 9-10
        base = {'stock': 10, 'crypto': 75, 'fixed_income': 0, 'cash': 15}

    allocation = {}
    for category, category_pct in base.items():
        if category == 'cash':
            allocation['cash'] = category_pct
            continue

        enabled_in_category = [
            ticker for ticker in enabled_assets
            if any(ticker in assets for cat, assets in ASSETS.items() if cat.replace('_', ' ') == category.replace('_', ' ') or
                   (category == 'stock' and cat == 'stock') or
                   (category == 'crypto' and cat == 'crypto') or
                   (category == 'fixed_income' and cat == 'fixed_income'))
        ]

        if enabled_in_category:
            per_asset = category_pct / len(enabled_in_category)
            for ticker in enabled_in_category:
                allocation[ticker] = int(round(per_asset))

    return allocation

def get_fallback_response(user_input):
    user_lower = user_input.lower()
    if any(word in user_lower for word in ['etf', 'fund', 'voo', 's&p']):
        return "VOO is a great low-cost ETF that tracks the S&P 500! It offers excellent diversification across 500 large-cap companies with a very low expense ratio of 0.03%."
    elif any(word in user_lower for word in ['risk', 'safe', 'conservative']):
        return "VOO is considered lower risk due to its broad diversification, while Bitcoin is highly volatile and carries significant risk. Your allocation between VOO and BTC should match your risk tolerance!"
    elif any(word in user_lower for word in ['return', 'profit', 'gain']):
        return "Returns depend on your allocation and market performance. Use the dashboard to simulate different VOO/BTC allocations and see how they perform over time!"
    elif any(word in user_lower for word in ['crypto', 'bitcoin', 'btc']):
        return "Bitcoin (BTC) is a highly volatile but potentially rewarding digital asset. It's uncorrelated with stocks like VOO, which can provide diversification benefits. Consider your risk tolerance!"
    else:
        return f"That's a great question! I'd suggest exploring our investment terms or trying different VOO/BTC allocations in the dashboard to see how they perform over time."


if st.session_state.right_panel_visible:
    left_col, middle_col, right_col = st.columns([2.2, 3.8, 2.0])
else:
    left_col, middle_col, right_col = st.columns([2.2, 5.8, 0.1])

with left_col:
    with st.container(border=True):
        st.subheader("💼 Investment Settings")
        if not st.session_state.right_panel_visible:
            if st.button("Open Chat", key="open_panel", width="stretch"):
                    st.session_state.right_panel_visible = True
                    st.rerun()
        st.write("**Investment Amount**")
        current_amount = st.session_state.investment_amount
        if isinstance(current_amount, str):
            current_amount = investment_map.get(current_amount, 10000)

        investment_amount = st.number_input(
            "Investment Amount",
            min_value=100,
            value=current_amount,
            step=1000,
            label_visibility="collapsed"
        )
        st.session_state.investment_amount = int(investment_amount)

        st.write("**When you wish you invested**")
        min_date = datetime(2015, 11, 25).date()
        max_date = datetime.now().date()
        default_date = max(min_date, (datetime.now() - timedelta(days=365)).date())

        investment_date = st.date_input(
            "Investment Date",
            value=default_date,
            min_value=min_date,
            max_value=max_date,
            label_visibility="collapsed"
        )
        st.caption(f"📅 Simulates returns from {investment_date} to today")
        st.caption(f"💡 Data available from 2015-11-25 onwards")

        st.write("**Risk Tolerance**")
        risk_scale = st.slider(
            "Risk Scale",
            min_value=1,
            max_value=10,
            value=st.session_state.risk_scale,
            label_visibility="collapsed"
        )

        st.session_state.risk_scale = risk_scale

        if risk_scale != st.session_state.last_risk_scale:
            st.session_state.last_risk_scale = risk_scale
            risk_alloc = get_risk_based_allocation(risk_scale, st.session_state.enabled_assets)

            for category_assets in ASSETS.values():
                for ticker in category_assets.keys():
                    if ticker in st.session_state.enabled_assets:
                        st.session_state.selected_assets[ticker] = risk_alloc.get(ticker, 0)
                    else:
                        st.session_state.selected_assets[ticker] = 0
            st.rerun()

        risk_descriptions = {
            1: "🛡️ Very Conservative - Prioritize stability (90% Stocks, 10% Crypto)",
            2: "🛡️ Conservative - Lower volatility (80% Stocks, 20% Crypto)",
            3: "🛡️ Conservative - Moderate stock focus (70% Stocks, 30% Crypto)",
            4: "⚖️ Moderate-Conservative - Balanced approach (60% Stocks, 40% Crypto)",
            5: "⚖️ Moderate - Even stock/crypto split (50% Stocks, 50% Crypto)",
            6: "⚖️ Moderate-Aggressive - Crypto lean (40% Stocks, 60% Crypto)",
            7: "🚀 Aggressive - Higher volatility (30% Stocks, 70% Crypto)",
            8: "🚀 Very Aggressive - Crypto focus (20% Stocks, 80% Crypto)",
            9: "🚀 Extremely Aggressive - Maximum volatility (10% Stocks, 90% Crypto)",
            10: "🚀 Extremely Aggressive - Max crypto (0% Stocks, 100% Crypto)"
        }
        st.caption(risk_descriptions.get(risk_scale, "Unknown risk level"))

        st.divider()

        # Combined Asset Selection & Fixed Income Rates Section
        with st.expander("**🎯 Select Assets & Customize Rates**", expanded=False):
            st.caption("Choose which assets to include in your portfolio and set custom rates for fixed income products")

            # Asset Selection
            for category_name, category_assets in ASSETS.items():
                st.write(f"**{category_name.replace('_', ' ').title()}** ({len(category_assets)} assets)")
                cols = st.columns(2)
                for idx, (ticker, asset_info) in enumerate(category_assets.items()):
                    with cols[idx % 2]:
                        is_enabled = ticker in st.session_state.enabled_assets
                        checkbox_label = f"{asset_info['icon']} {ticker} - {asset_info['name'][:30]}{'...' if len(asset_info['name']) > 30 else ''}"

                        enabled = st.checkbox(
                            checkbox_label,
                            value=is_enabled,
                            key=f"enable_{ticker}"
                        )

                        if enabled and ticker not in st.session_state.enabled_assets:
                            st.session_state.enabled_assets.append(ticker)
                        elif not enabled and ticker in st.session_state.enabled_assets:
                            st.session_state.enabled_assets.remove(ticker)
                            if ticker in st.session_state.selected_assets:
                                st.session_state.selected_assets[ticker] = 0

                if category_name != list(ASSETS.keys())[-1]:
                    st.write("")

            # Fixed Income Rate Inputs (only show if fixed income assets are enabled)
            if 'HY_SAVINGS' in st.session_state.enabled_assets or 'CD' in st.session_state.enabled_assets:
                st.divider()
                st.write("**💰 Fixed Income Rates**")
                st.caption("Customize APY rates for your fixed income products")

                rate_cols = st.columns(2)

                if 'HY_SAVINGS' in st.session_state.enabled_assets:
                    with rate_cols[0]:
                        hy_rate = st.number_input(
                            "🏦 HY Savings APY (%)",
                            min_value=0.0,
                            max_value=10.0,
                            value=st.session_state.hy_savings_rate,
                            step=0.01,
                            format="%.2f",
                            key="hy_savings_rate_input",
                            help="Enter the annual percentage yield for your high-yield savings account"
                        )
                        st.session_state.hy_savings_rate = hy_rate

                if 'CD' in st.session_state.enabled_assets:
                    with rate_cols[1]:
                        cd_rate = st.number_input(
                            "💰 CD APY (%)",
                            min_value=0.0,
                            max_value=10.0,
                            value=st.session_state.cd_rate,
                            step=0.01,
                            format="%.2f",
                            key="cd_rate_input",
                            help="Enter the annual percentage yield for your certificate of deposit"
                        )
                        st.session_state.cd_rate = cd_rate

        st.divider()

        st.write("**📊 Asset Allocation**")
        st.caption("Set allocations independently - remaining % will be held as cash")

        allocation_display_placeholder = st.empty()

        suggested_alloc = get_risk_based_allocation(risk_scale, st.session_state.enabled_assets)

        allocations = {}

        st.write("**Adjust Allocations**")
        st.caption("Adjust allocations for your selected assets")

        for category_name, category_assets in ASSETS.items():
            enabled_in_category = {k: v for k, v in category_assets.items() if k in st.session_state.enabled_assets}

            if not enabled_in_category:
                continue

            with st.expander(f"{category_name.title()} ({len(enabled_in_category)} selected)", expanded=True):
                for ticker, asset_info in enabled_in_category.items():
                    current_alloc = st.session_state.selected_assets.get(ticker, 0)
                    if isinstance(current_alloc, str):
                        current_alloc = int(float(current_alloc)) if current_alloc else 0
                    elif isinstance(current_alloc, float):
                        current_alloc = int(current_alloc)
                    else:
                        current_alloc = int(current_alloc) if current_alloc else 0

                    alloc_pct = st.slider(
                        f"{ticker}",
                        min_value=0,
                        max_value=100,
                        value=current_alloc,
                        step=1,
                        label_visibility="collapsed",
                        key=f"alloc_{ticker}_{risk_scale}"
                    )

                    st.session_state.selected_assets[ticker] = alloc_pct
                    allocations[ticker] = alloc_pct

                    col1, col2 = st.columns([2.5, 1])

                    with col1:
                        # Display custom rate for fixed income products
                        asset_name = asset_info['name']
                        if ticker == 'HY_SAVINGS':
                            custom_rate = st.session_state.get('hy_savings_rate', 3.40)
                            asset_name = f"High-Yield Savings ({custom_rate:.2f}% APY)"
                        elif ticker == 'CD':
                            custom_rate = st.session_state.get('cd_rate', 3.50)
                            asset_name = f"Certificate of Deposit ({custom_rate:.2f}% APY)"

                        st.markdown(f"<div style='padding: 8px 0'><b>{asset_info['icon']} {ticker}</b><br/><span style='font-size: 0.85em; color: #666'>{asset_name}</span></div>", unsafe_allow_html=True)

                    with col2:
                        risk_based_pct = suggested_alloc.get(ticker, 0)
                        if alloc_pct != risk_based_pct and risk_based_pct > 0:
                            st.markdown(f"<div style='padding: 12px 0; text-align: right'><b style='color: #FFA500'>{alloc_pct}%</b><br/><span style='font-size: 0.75em; color: #999'>Risk: {risk_based_pct}%</span></div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div style='padding: 12px 0; text-align: right'><b>{alloc_pct}%</b></div>", unsafe_allow_html=True)

        total_allocation = sum(allocations.values())

        normalized_allocations = {k: v for k, v in allocations.items() if v > 0}

        current_cash = 100 - total_allocation

        with allocation_display_placeholder.container():
            with st.expander(f"📊 Current Allocation (Auto-adjusted by Risk Level)", expanded=True):
                st.markdown("**Your allocations automatically adjust based on your risk tolerance:**")

                category_totals = {
                    'stock': 0,
                    'crypto': 0,
                    'fixed_income': 0
                }

                for category_name, category_assets in ASSETS.items():
                    for ticker, asset_info in category_assets.items():
                        if ticker in st.session_state.enabled_assets:
                            alloc_value = allocations.get(ticker, 0)
                            if alloc_value > 0:
                                category_totals[category_name] += alloc_value

                display_items = []

                if category_totals['stock'] > 0:
                    display_items.append(("📊 Stocks", f"{category_totals['stock']}%"))

                if category_totals['crypto'] > 0:
                    display_items.append(("₿ Crypto", f"{category_totals['crypto']}%"))

                if category_totals['fixed_income'] > 0:
                    display_items.append(("🏦 Fixed Income", f"{category_totals['fixed_income']}%"))

                if current_cash > 0:
                    display_items.append(("💵 Cash", f"{current_cash}%"))

                if display_items:
                    cols = st.columns(len(display_items))
                    for col, (category_name, alloc_pct) in zip(cols, display_items):
                        with col:
                            st.markdown(f"**{category_name}**")
                            st.markdown(f"<div style='font-size: 1.2rem; font-weight: 600;'>{alloc_pct}</div>", unsafe_allow_html=True)

                st.caption("💡 Adjust sliders below to update allocations")

        current_risk = get_risk_from_allocation(allocations)

        user_overrode = False
        for ticker in st.session_state.enabled_assets:
            suggested_pct = suggested_alloc.get(ticker, 0)
            actual_pct = allocations.get(ticker, 0)
            if suggested_pct != actual_pct:
                user_overrode = True
                break

        if user_overrode and current_risk != risk_scale:
            st.session_state.risk_scale = current_risk
            st.session_state.last_risk_scale = current_risk

        st.divider()

        if total_allocation > 100:
            st.error(f"❌ Total: {total_allocation}% (exceeds 100%! Please adjust.)")
        elif total_allocation == 100:
            st.success(f"✅ 100% Allocated (no cash)")
        else:
            unallocated = 100 - total_allocation
            st.info(f"💡 {unallocated}% in Cash (unallocated)")

        if total_allocation == 0:
            st.warning("⚠️ Please select at least one asset")
            normalized_allocations = {}


# MIDDLE PANEL - Dashboard & Charts
with middle_col:
    # Calculate returns based on user inputs
    portfolio_results, errors = calculate_portfolio_returns(
        investment_amount,
        investment_date,
        normalized_allocations if total_allocation > 0 else {}
    )

    # Output Results
    with st.container(border=True):
        st.subheader("📊 Portfolio Performance")

        if portfolio_results:
            # Calculate unallocated cash (same as we show in left panel)
            unallocated_pct = 100 - total_allocation
            unallocated_cash = (unallocated_pct / 100) * investment_amount

            # Total current value = invested asset values + unallocated cash
            total_current_with_cash = portfolio_results['total_current'] + unallocated_cash

            # Total gain/loss on the entire portfolio
            total_gain_loss = total_current_with_cash - investment_amount
            total_gain_loss_pct = (total_gain_loss / investment_amount) * 100 if investment_amount > 0 else 0

            # Key Metrics
            metrics_cols = st.columns(4)

            with metrics_cols[0]:
                st.metric(
                    label="Initial Investment",
                    value=f"${investment_amount:,.0f}",
                )

            with metrics_cols[1]:
                st.metric(
                    label="Current Value",
                    value=f"${total_current_with_cash:,.0f}",
                    delta=f"${total_gain_loss:,.0f}"
                )

            with metrics_cols[2]:
                st.metric(
                    label="Total Return",
                    value=f"{total_gain_loss_pct:.2f}%"
                )

            with metrics_cols[3]:
                # Calculate after-tax value (15% capital gains tax on gains only)
                # After-tax gain = total gain * (1 - tax rate)
                after_tax_gain = total_gain_loss * (1 - 0.15)
                # After-tax portfolio value = initial + after-tax gain
                after_tax_value = investment_amount + after_tax_gain
                st.metric(
                    label="After Taxes (15%)",
                    value=f"${after_tax_value:,.0f}",
                    delta=f"${after_tax_gain:,.0f}"
                )

            st.divider()

            # Asset Breakdown
            st.write("**Asset Breakdown:**")

            # Count assets + cash if unallocated
            num_items = len(portfolio_results['breakdown'])
            if unallocated_cash > 0:
                num_items += 1

            breakdown_cols = st.columns(min(num_items, 4))

            for idx, (asset, data) in enumerate(sorted(portfolio_results['breakdown'].items(), key=lambda x: x[1]['current'], reverse=True)):
                with breakdown_cols[idx % len(breakdown_cols)]:
                    asset_info = data.get('info', {})
                    st.write(f"**{asset_info.get('icon', '📊')} {asset}**")
                    st.write(f"Initial: ${data['initial']:,.0f}")
                    st.write(f"Current: ${data['current']:,.0f}")
                    st.write(f"Gain/Loss: ${data['gain_loss']:,.0f}")
                    st.write(f"Return: {data['gain_loss_pct']:.2f}%")

            # Show unallocated cash if any
            if unallocated_cash > 0:
                with breakdown_cols[len(portfolio_results['breakdown']) % len(breakdown_cols)]:
                    st.write("**💰 Cash**")
                    st.write(f"Initial: ${unallocated_cash:,.0f}")
                    st.write(f"Current: ${unallocated_cash:,.0f}")
                    st.write(f"Gain/Loss: $0")
                    st.write(f"Return: 0.00%")

            st.divider()

            # Charts
            st.write("**Performance Charts**")

            # Create rows of charts (2 per row)
            assets_list = list(portfolio_results['breakdown'].items())

            # Row 1 - Individual asset charts
            chart_row1 = st.columns(2)
            for idx, (asset, data) in enumerate(assets_list[:2]):
                with chart_row1[idx]:
                    with st.container(border=True):
                        asset_info = data.get('info', {})
                        st.write(f"**{asset_info.get('icon', '📊')} {asset} Performance**")
                        chart_data = data['data'].set_index('Date')['Portfolio_Value']
                        st.line_chart(chart_data, width='stretch', height=200)

                        current = data['data']['Portfolio_Value'].iloc[-1]
                        gain = data['data']['Gain_Loss'].iloc[-1]
                        st.caption(f"Current: ${current:,.0f} | Gain: ${gain:,.0f}")

            # Row 2 - More individual assets if any
            if len(assets_list) > 2:
                chart_row2 = st.columns(2)
                for idx, (asset, data) in enumerate(assets_list[2:4]):
                    with chart_row2[idx]:
                        with st.container(border=True):
                            asset_info = data.get('info', {})
                            st.write(f"**{asset_info.get('icon', '📊')} {asset} Performance**")
                            chart_data = data['data'].set_index('Date')['Portfolio_Value']
                            st.line_chart(chart_data, width='stretch', height=200)

                            current = data['data']['Portfolio_Value'].iloc[-1]
                            gain = data['data']['Gain_Loss'].iloc[-1]
                            st.caption(f"Current: ${current:,.0f} | Gain: ${gain:,.0f}")

            # Combined Portfolio Chart
            st.write("")
            with st.container(border=True):
                st.write("**📈 Combined Portfolio Over Time**")

                # Combine all asset data by date
                combined_data = None
                for asset, data in portfolio_results['breakdown'].items():
                    df = data['data'][['Date', 'Portfolio_Value']].copy()
                    df = df.rename(columns={'Portfolio_Value': asset})
                    df = df.set_index('Date')

                    if combined_data is None:
                        combined_data = df
                    else:
                        combined_data = combined_data.join(df, how='outer')

                if combined_data is not None:
                    # Fill NaN appropriately
                    combined_data = combined_data.ffill().fillna(0)
                    combined_data['Total'] = combined_data.sum(axis=1)

                    st.line_chart(combined_data[['Total']], width='stretch', height=300)

        else:
            if errors:
                for error in errors:
                    st.warning(f"⚠️ {error}")
            st.info("💡 Select at least one asset and a valid investment date to see results")


# RIGHT PANEL - AI Chat 
with right_col:
    if st.session_state.right_panel_visible:
        # AI Chatbot with Terms Explanation
        with st.container(border=True):
            header_col1, header_col2 = st.columns([1, 3])
            with header_col2:
                st.subheader("🤖 Assistant")
            with header_col1:
                st.write("")
                if st.button("◀", key="hide_panel", width='stretch'):
                    st.session_state.right_panel_visible = False
                    st.rerun()

            with st.expander("Basics of Investing", expanded=False):
                basics_of_investing = {
                    "What Is Investing?": "Investing involves allocating money or resources into assets with the expectation of generating a profit or income over time. Unlike saving, which typically involves placing money into low-yield, low-risk accounts like savings accounts or certificates of deposit, investing aims for higher returns through various financial instruments.",
                    "Why Invest?": "- Build Wealth: Grow your savings exponentially over time.\n- Achieve Financial Goals: Save for retirement, education, or purchasing property.\n- Beat Inflation: Protect your purchasing power from erosion.\n- Create Passive Income: Generate income streams that require minimal ongoing effort.",
                    "The Power of Compound Growth": "One of the most compelling reasons to start investing early is the power of compound interest — earning returns on your returns. Over time, this exponential growth can significantly boost your wealth.\n\nExample:\n\nIf you invest 10,000 at an annual return of 10% (e.g., S&P 500 ETFs), after 30 years, your investment would grow to approximately $174,494, thanks to compound interest. Compound interest formula: A=P(1+r/n)^nt",
                    "Risk and Return": "All investments carry some level of risk. Generally, higher potential returns come with increased risk. Understanding your risk tolerance — how much risk you're willing and able to accept — is crucial to crafting an appropriate investment plan.\n\nRisk Spectrum:\n- Low Risk: Savings accounts, government bonds\n- Moderate Risk: Corporate bonds, index funds\n- High Risk: Individual stocks, cryptocurrencies, startups",
                    "Building a Diversified Portfolio": "Diversification is key to managing risk. Diversification helps mitigate risks because different assets often react differently to economic events. For example, when stocks decline, bonds may hold steady or even increase, balancing your portfolio.\n\nAsset allocation is key to balance. Asset allocation involves dividing your investments among different categories to align with your goals and risk appetite.\n\nSample Asset Allocation for a Moderate Investor:\n- 60% ETFs\n- 25% Bonds\n- 10% Real Estate\n- 5% Cash"
                }
                for topic, content in basics_of_investing.items():
                    with st.expander(topic):
                        st.write(content)

            with st.expander("Core Investment Vehicles", expanded=False):
                investment_vehicles = {
                    # can I do markdown inside expander?
                    "Stocks (Equities)": "- Ownership in companies.\n- Potential for high returns, and dividend income.\n- Volatile; prices fluctuate with market conditions.",
                    "Exchange-Traded Funds (ETFs)": "- Trade all day like stocks.\n- Usually passively managed, tracking indices, such as the S&P 500.\n- Cost-effective and flexible. Taxed only when you sell. Ideal for long-term investors seeking market-average returns.",
                    "Mutual Funds": "- Pooled investments managed by professionals.\n- Offer diversification across many securities, such as stocks and bonds.\n- Mutual funds create yearly taxable capital-gain distributions from the fund's internal trading.",
                    "Bonds (Fixed-Income Securities)": "- Loans to governments or corporations.\n- Usually offer steady income through interest payments.\n- Less risky than stocks but with lower returns.",
                    "Real Estate": "- Physical property investments. Options include direct property ownership or real estate investment trusts (REITs).\n- Generate rental income and appreciation.\n- Require significant capital and management.",
                    "Commodities": "- Physical goods like gold, oil, or agricultural products.\n- Often used for diversification and hedging.",
                    "Cryptocurrencies": "- Digital assets like Bitcoin and Ethereum.\n- High risk and volatility.\n- Suitable for a small portion of a diversified portfolio."
                }

                for vehicle, description in investment_vehicles.items():
                    with st.expander(vehicle):
                        st.write(description)

            with st.expander("Retirement Accounts (Tax-Advantaged Investing)", expanded=False):
                retirement_accounts = {
                    "401(k)": "Employer-sponsored plan with tax-deferred growth; often includes employer matching.",
                    "IRA": "Individual retirement accounts with tax advantages. Traditional (tax-deferred) or Roth (tax-free withdrawals).",
                    "SEP IRA & Solo 401(k)": "For self-employed individuals."
                }

                for retirement_account, description in retirement_accounts.items():
                    with st.expander(retirement_account):
                        st.write(description)

            with st.expander("Investment Strategies, Tips, and Pitfalls", expanded=False):
                strategies_tips_pitfalls = {
                    "Common Investment Strategies": "- Buy and Hold: Purchase investments and hold them over years regardless of short-term market changes. This strategy minimizes transaction costs and capitalizes on long-term growth.\n- Value Investing: Seek undervalued stocks or assets trading below their intrinsic value, aiming for appreciation when the market recognizes their true worth.\n- Growth Investing: Invest in companies with high growth potential, often in emerging industries, expecting rapid earnings expansion.\n- Passive Investing: Track market indices through ETFs or index funds, offering diversification and low fees.\n- Active Investing: Frequent buying and selling based on market analysis, aiming to outperform benchmarks but requiring more effort and expertise. Example: Quantitative Investing.",
                    "Tips for Successful Investing": "- Stay disciplined: Stick to your plan and avoid impulsive moves.\n- Be patient: Wealth accumulation takes time; avoid get-rich-quick schemes.\n- Keep learning: The investment landscape evolves; continuous education is vital.\n- Seek professional advice: Consider consulting with a financial advisor for personalized guidance.\n- Maintain a balanced lifestyle: Never invest money you cannot afford to lose, and keep a healthy emergency fund.",
                    "Common Investment Pitfalls to Avoid": "- Timing the Market: Predicting short-term moves is futile; focus on long-term growth.\n- Overtrading: Frequent buying and selling can erode returns through transaction costs and taxes.\n- Ignoring Costs: High fees and expense ratios reduce net gains. Choose low-cost funds and accounts.\n- Neglecting Diversification: Putting all funds into one asset class increases risk.\n- Emotional Investing: Decisions driven by fear or greed often lead to poor outcomes."
                }

                for topic, content in strategies_tips_pitfalls.items():
                    with st.expander(topic):
                        st.write(content)

            with st.expander("How to Invest", expanded=False):
                investment_guide = {
                    "Schwab": "https://www.schwab.com/how-to-invest",
                    "Fidelity": "https://www.fidelity.com/learning-center/trading-investing/investing-for-beginners",
                    "Vanguard": "https://investor.vanguard.com",
                    "Chase": "https://www.chase.com/personal/investments/online-investing",
                    "Robinhood": "https://robinhood.com/us/en/learn/investing-101/"
                }

                for company, url in investment_guide.items():
                    with st.expander(company):
                        st.write(url)

            st.divider()

            chat_container = st.container(height=300)
            with chat_container:
                for message in st.session_state.chat_messages:
                    with st.chat_message(message["role"]):
                        st.write(message["content"])

            user_input = st.chat_input("Ask about investing...")

            if user_input:
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": user_input
                })

                # Show loading spinner while getting AI response
                with st.spinner("🤔 Thinking..."):
                    # Get AI response from backend with full context
                    ai_response = get_ai_response(
                        st.session_state.chat_messages,
                        portfolio_results,
                        investment_date,
                        normalized_allocations
                    )

                # Add AI response to chat history
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": ai_response
                })

                st.rerun()

            if st.button("Clear Chat", width='stretch', key="clear_chat"):
                st.session_state.chat_messages = []
                st.rerun()
