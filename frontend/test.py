from dotenv import load_dotenv
from streamlit_supabase_auth import login_form, logout_button
from supabase import create_client
import streamlit as st
import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from streamlit_local_storage import LocalStorage
from onboarding import show_onboarding, check_onboarding_status, reset_onboarding
import requests

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from cleanData import load_etf_data, load_crypto_data, load_index_data, calculate_returns, get_performance_metrics, filter_by_date_range


load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")
supabase = create_client(supabase_key=SUPABASE_KEY, supabase_url=SUPABASE_URL)
storage = LocalStorage()

ASSETS = {
    # Stock ETFs
    'stock': {
        'VOO': {'name': 'Vanguard S&P 500 ETF', 'icon': '🇺🇸', 'category': 'Stock'},
    },
    # Crypto
    'crypto': {
        'BTC': {'name': 'Bitcoin', 'icon': '₿', 'category': 'Cryptocurrency'},
    }
}

# Initialize session state
if 'right_panel_visible' not in st.session_state:
    st.session_state.right_panel_visible = True

if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

if 'investment_amount' not in st.session_state:
    st.session_state.investment_amount = 10000

if 'risk_scale' not in st.session_state:
    st.session_state.risk_scale = 5

if 'selected_assets' not in st.session_state:
    st.session_state.selected_assets = {'VOO': 50, 'BTC': 50}  # Default allocation

if 'last_edited_asset' not in st.session_state:
    st.session_state.last_edited_asset = None

if 'last_total_allocation' not in st.session_state:
    st.session_state.last_total_allocation = 100

# Configure page
st.set_page_config(
    page_title="Investorly Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def get_asset_type(ticker):
    """Determine asset type"""
    for category, assets in ASSETS.items():
        if ticker in assets:
            if category == 'crypto':
                return 'crypto'
            elif category == 'indices':
                return 'index'
            else:
                return 'etf'
    return 'etf'

@st.cache_data(ttl=3600)
def load_data_safe(ticker):
    """Safely load data with caching - auto-detects asset type"""
    try:
        dataset_dir = os.path.join(os.path.dirname(__file__), '..', 'backend', 'dataset')
        asset_type = get_asset_type(ticker)

        if asset_type == 'crypto':
            return load_crypto_data(ticker, dataset_dir)
        elif asset_type == 'index':
            return load_index_data(ticker, dataset_dir)
        else:
            return load_etf_data(ticker, dataset_dir)
    except Exception as e:
        return None

def calculate_portfolio_returns(investment_amount, investment_date, allocations):
    """Calculate returns for a portfolio with multiple allocations"""
    try:
        total_current_value = 0
        total_gain_loss = 0
        breakdown = {}
        errors = []

        for asset, percentage in allocations.items():
            if percentage <= 0:
                continue

            dollar_amount = (percentage / 100) * investment_amount

            # Load data
            df = load_data_safe(asset)
            if df is None:
                errors.append(f"Could not load data for {asset}")
                continue

            # Filter from investment date
            df_filtered = filter_by_date_range(df, start_date=str(investment_date))
            if df_filtered.empty:
                errors.append(f"No data available for {asset} from {investment_date}")
                continue

            # Calculate returns
            df_returns = calculate_returns(df_filtered, initial_investment=dollar_amount)
            metrics = get_performance_metrics(df_returns)

            # Get asset display info
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
    """Get all available tickers"""
    tickers = []
    for category, assets in ASSETS.items():
        tickers.extend(list(assets.keys()))
    return sorted(tickers)

def get_ai_response(messages):
    """
    Call the Flask backend to get AI chatbot response
    
    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
    
    Returns:
        String response from the AI or fallback response on error
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/llm",
            json={"messages": messages},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        st.write(response)
        if response.status_code == 200:
            data = response.json()
            messageAI = data.get("response", "I'm having trouble responding right now.")
            return messageAI
        
    except Exception as e:
        print(e)
        # Fallback to keyword-based responses if backend is unreachable
        return get_fallback_response(messages[-1]["content"])

def get_fallback_response(user_input):
    """Fallback keyword-based responses when backend is unavailable"""
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


def getUser():
    session = login_form(
        url=SUPABASE_URL,
        apiKey=SUPABASE_KEY,
        providers=["google"],
    )

    if session:
        return session

    return None


user = getUser()


if user:
    # Check if user has completed onboarding
    if not check_onboarding_status():
        # Show onboarding flow
        show_onboarding()
    else:
        # Add custom CSS for better styling
        st.markdown("""
        <style>
        .stButton button {
            width: 100%;
        }
        .main {
            padding: 1rem;
        }
        [data-testid="stVerticalBlock"] {
            gap: 1rem;
        }
        .asset-selector {
            padding: 0.5rem;
            border-radius: 0.5rem;
            margin-bottom: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)

        # Header with sign up/log in buttons
        header_cols = st.columns([4, 1, 1])
        with header_cols[0]:
            st.title("📈 Investorly Dashboard")
        with header_cols[2]:
            if logout_button("log in"):
                st.rerun()

        st.divider()

        # Create main layout: Left selector | Middle dashboard | Right panel
        if st.session_state.right_panel_visible:
            left_col, middle_col, right_col = st.columns([2.2, 3.8, 2])
        else:
            left_col, middle_col, right_col = st.columns([2.2, 5.8, 0.1])
        # LEFT PANEL - Investment Settings & Asset Allocation
        with left_col:
            with st.container(border=True):
                st.subheader("💼 Investment Settings")

                # Investment Amount
                st.write("**Investment Amount**")
                investment_amount = st.number_input(
                    "Investment Amount",
                    min_value=100,
                    value=st.session_state.investment_amount,
                    step=1000,
                    label_visibility="collapsed"
                )
                st.session_state.investment_amount = investment_amount

                # Investment Date
                st.write("**When you wish you invested**")
                investment_date = st.date_input(
                    "Investment Date",
                    value=datetime.now() - timedelta(days=365),
                    label_visibility="collapsed"
                )
                st.caption(f"📅 Simulates returns from {investment_date} to today")

                # Risk Scale
                st.write("**Risk Tolerance**")
                risk_scale = st.slider(
                    "Risk Scale",
                    min_value=1,
                    max_value=10,
                    value=st.session_state.risk_scale,
                    label_visibility="collapsed"
                )
                st.session_state.risk_scale = risk_scale

                st.divider()

                # Asset Allocation with Smart Auto-Adjustment
                st.write("**📊 Asset Allocation**")
                st.caption("Drag sliders - they auto-adjust to stay at 100%")

                # Display asset selection with allocation
                allocations = {}

                for category_name, category_assets in ASSETS.items():
                    with st.expander(f"{category_name.title()}", expanded=True):
                        for ticker, asset_info in category_assets.items():
                            # Get current allocation from session state
                            current_alloc = st.session_state.selected_assets.get(ticker, 0)

                            # Display asset info with columns
                            col1, col2 = st.columns([2.5, 1])

                            with col1:
                                # Show asset label clearly
                                st.markdown(f"<div style='padding: 8px 0'><b>{asset_info['icon']} {ticker}</b><br/><span style='font-size: 0.85em; color: #666'>{asset_info['name']}</span></div>", unsafe_allow_html=True)

                            with col2:
                                # Show current percentage
                                st.markdown(f"<div style='padding: 12px 0; text-align: right'><b>{current_alloc}%</b></div>", unsafe_allow_html=True)

                            # Slider with full range
                            alloc_pct = st.slider(
                                f"{ticker}",
                                min_value=0,
                                max_value=100,
                                value=current_alloc,
                                step=1,
                                label_visibility="collapsed",
                                key=f"alloc_{ticker}"
                            )

                            allocations[ticker] = alloc_pct

                # Calculate total allocation
                total_allocation = sum(allocations.values())

                # Smart auto-adjustment: If total exceeds 100%, scale all proportionally
                if total_allocation > 100:
                    # Scale all allocations proportionally without rerunning
                    scale_factor = 100.0 / total_allocation
                    for ticker in allocations:
                        scaled_value = max(0, round(allocations[ticker] * scale_factor))
                        allocations[ticker] = scaled_value
                    total_allocation = sum(allocations.values())

                # Update session state with final allocations (for next render)
                for ticker, pct in allocations.items():
                    st.session_state.selected_assets[ticker] = pct

                # Get only assets with > 0 allocation
                normalized_allocations = {k: v for k, v in allocations.items() if v > 0}

                st.divider()

                # Show allocation status
                if total_allocation > 100:
                    st.warning(f"⚠️ Total: {total_allocation}% (exceeds 100%)")
                elif total_allocation < 100:
                    st.info(f"💡 {100 - total_allocation}% unallocated (cash)")
                else:
                    st.success(f"✅ 100% Allocated")

                # Display allocation summary
                if total_allocation > 0:
                    st.write("**Allocation Summary:**")
                    for ticker, pct in sorted(normalized_allocations.items(), key=lambda x: x[1], reverse=True):
                        if pct > 0:
                            asset_info = None
                            for cat, assets in ASSETS.items():
                                if ticker in assets:
                                    asset_info = assets[ticker]
                                    break
                            if asset_info:
                                # Progress bar for visual allocation
                                st.write(f"{asset_info['icon']} {ticker}: {pct}%")
                                st.progress(pct / 100, text=f"{pct}%")
                else:
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
                    # Key Metrics
                    metrics_cols = st.columns(4)

                    with metrics_cols[0]:
                        st.metric(
                            label="Initial Investment",
                            value=f"${portfolio_results['total_initial']:,.0f}",
                        )

                    with metrics_cols[1]:
                        st.metric(
                            label="Current Value",
                            value=f"${portfolio_results['total_current']:,.0f}",
                            delta=f"${portfolio_results['total_gain_loss']:,.0f}"
                        )

                    with metrics_cols[2]:
                        st.metric(
                            label="Total Return",
                            value=f"{portfolio_results['total_gain_loss_pct']:.2f}%"
                        )

                    with metrics_cols[3]:
                        # Calculate after-tax (15% capital gains)
                        after_tax_gain = portfolio_results['total_gain_loss'] * 0.85
                        st.metric(
                            label="After Taxes (15%)",
                            value=f"${after_tax_gain:,.0f}"
                        )

                    st.divider()

                    # Asset Breakdown
                    st.write("**Asset Breakdown:**")
                    breakdown_cols = st.columns(min(len(portfolio_results['breakdown']), 4))

                    for idx, (asset, data) in enumerate(sorted(portfolio_results['breakdown'].items(), key=lambda x: x[1]['current'], reverse=True)):
                        with breakdown_cols[idx % len(breakdown_cols)]:
                            asset_info = data.get('info', {})
                            st.write(f"**{asset_info.get('icon', '📊')} {asset}**")
                            st.write(f"Initial: ${data['initial']:,.0f}")
                            st.write(f"Current: ${data['current']:,.0f}")
                            st.write(f"Gain/Loss: ${data['gain_loss']:,.0f}")
                            st.write(f"Return: {data['gain_loss_pct']:.2f}%")

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
                                st.line_chart(chart_data, use_container_width=True, height=200)

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
                                    st.line_chart(chart_data, use_container_width=True, height=200)

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
                            combined_data = combined_data.fillna(method='ffill').fillna(0)
                            combined_data['Total'] = combined_data.sum(axis=1)

                            st.line_chart(combined_data[['Total']], use_container_width=True, height=300)

                else:
                    if errors:
                        for error in errors:
                            st.warning(f"⚠️ {error}")
                    st.info("💡 Select at least one asset and a valid investment date to see results")

        # RIGHT PANEL - AI Chat & Education
        with right_col:
            if st.session_state.right_panel_visible:
                # AI Chatbot with Terms Explanation
                with st.container(border=True):
                    # Header with hide button
                    header_col1, header_col2 = st.columns([1, 3])
                    with header_col2:
                        st.subheader("🤖 Assistant")
                    with header_col1:
                        st.write("")
                        if st.button("◀", key="hide_panel", use_container_width=True):
                            st.session_state.right_panel_visible = False
                            st.rerun()

                    # Terms Explanation Section
                    with st.expander("📚 Investment Terms", expanded=False):
                        terms = {
                            "ETF": "Exchange-Traded Fund - like VOO, it tracks an index and trades like a stock",
                            "S&P 500": "An index of 500 large-cap U.S. companies - what VOO tracks",
                            "Crypto": "Digital currency secured by cryptography - Bitcoin (BTC) is the largest",
                            "Volatility": "Measure of price fluctuations - Bitcoin is more volatile than VOO",
                            "Return %": "Percentage gain/loss on your investment",
                            "Portfolio": "Your collection of VOO and BTC investments",
                            "Diversification": "Mixing different assets (VOO + BTC) to reduce overall risk",
                            "Allocation": "How you split your investment between VOO and BTC",
                        }

                        for term, definition in terms.items():
                            with st.expander(term):
                                st.write(definition)

                    st.divider()

                    # Chat container
                    chat_container = st.container(height=300)
                    with chat_container:
                        for message in st.session_state.chat_messages:
                            with st.chat_message(message["role"]):
                                st.write(message["content"])

                    # Chat input
                    user_input = st.chat_input("Ask about investing...")

                    if user_input:
                        # Add user message to chat history
                        st.session_state.chat_messages.append({
                            "role": "user",
                            "content": user_input
                        })

                        # Show loading spinner while getting AI response
                        with st.spinner("🤔 Thinking..."):
                            # Get AI response from backend
                            ai_response = get_ai_response(st.session_state.chat_messages)

                        # Add AI response to chat history
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "content": ai_response
                        })

                        st.rerun()

                    if st.button("Clear Chat", use_container_width=True, key="clear_chat"):
                        st.session_state.chat_messages = []
                        st.rerun()
            else:
                # Show button when panel is hidden
                if st.button("▶", key="show_panel", use_container_width=True):
                    st.session_state.right_panel_visible = True
                    st.rerun()
