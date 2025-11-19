from dotenv import load_dotenv
from streamlit_supabase_auth import login_form, logout_button
from supabase import create_client
import streamlit as st
import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from streamlit_local_storage import LocalStorage
from questionnaire import show_questionnaire, check_questionnaire_status, reset_questionnaire
import requests

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from cleanData import load_etf_data, load_crypto_data, load_index_data, calculate_returns, get_performance_metrics, filter_by_date_range

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")
supabase = create_client(supabase_key=SUPABASE_KEY, supabase_url=SUPABASE_URL)
storage = LocalStorage()

investment_map = {
    "$0 - $1,000": 500,
    "$1,000 - $5,000": 3000,
    "$5,000 - $10,000": 7500,
    "$10,000 - $50,000": 30000,
    "$50,000+": 50000
}

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

if 'last_risk_scale' not in st.session_state:
    st.session_state.last_risk_scale = 5

st.set_page_config(
    page_title="Investorly Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def get_asset_type(ticker):
    for category, assets in ASSETS.items():
        if ticker in assets:
            if category == 'crypto':
                return 'crypto'
            elif category == 'indices':
                return 'index'
            else:
                return 'etf'
    return 'etf'

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
    # Calculate returns for a portfolio with multiple allocations
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

def get_risk_from_allocation(voo_pct, btc_pct):
    """
    Calculate the implied risk level (1-10) from the current allocation.

    Logic:
    - High VOO, Low BTC → Conservative (1-3)
    - Balanced VOO/BTC → Moderate (4-6)
    - Low VOO, High BTC → Aggressive (7-10)

    Args:
        voo_pct: VOO allocation percentage (0-100)
        btc_pct: BTC allocation percentage (0-100)

    Returns:
        int: Risk level (1-10)
    """
    # Calculate the ratio: higher BTC % means higher risk
    total_invested = voo_pct + btc_pct

    if total_invested == 0:
        return 5  # Default to moderate if no allocation

    btc_ratio = btc_pct / total_invested  # 0 to 1

    # Map BTC ratio to risk level
    # 0% BTC → Risk 1
    # 25% BTC → Risk 4
    # 50% BTC → Risk 5
    # 75% BTC → Risk 8
    # 100% BTC → Risk 10

    if btc_ratio <= 0.1:
        return 1
    elif btc_ratio <= 0.2:
        return 2
    elif btc_ratio <= 0.3:
        return 3
    elif btc_ratio <= 0.4:
        return 4
    elif btc_ratio <= 0.5:
        return 5
    elif btc_ratio <= 0.6:
        return 6
    elif btc_ratio <= 0.7:
        return 7
    elif btc_ratio <= 0.8:
        return 8
    elif btc_ratio <= 0.9:
        return 9
    else:
        return 10

def get_risk_based_allocation(risk_level):
    """
    Calculate suggested asset allocations based on risk tolerance (1-10 scale).

    Risk Level Logic:
    - 1-3 (Conservative): High VOO, Low BTC, High Cash
    - 4-6 (Moderate): Balanced VOO/BTC, Some Cash
    - 7-10 (Aggressive): Low VOO, High BTC, Minimal Cash

    Returns:
        dict: {'VOO': %, 'BTC': %, 'cash': %} based on risk level
    """
    if risk_level <= 2:
        # Very Conservative: 70% VOO, 10% BTC, 20% Cash
        return {'VOO': 70, 'BTC': 10, 'cash': 20}
    elif risk_level == 3:
        # Conservative: 60% VOO, 20% BTC, 20% Cash
        return {'VOO': 60, 'BTC': 20, 'cash': 20}
    elif risk_level == 4:
        # Moderate-Conservative: 50% VOO, 30% BTC, 20% Cash
        return {'VOO': 50, 'BTC': 30, 'cash': 20}
    elif risk_level == 5:
        # Moderate: 50% VOO, 40% BTC, 10% Cash
        return {'VOO': 50, 'BTC': 40, 'cash': 10}
    elif risk_level == 6:
        # Moderate-Aggressive: 40% VOO, 50% BTC, 10% Cash
        return {'VOO': 40, 'BTC': 50, 'cash': 10}
    elif risk_level == 7:
        # Aggressive: 30% VOO, 60% BTC, 10% Cash
        return {'VOO': 30, 'BTC': 60, 'cash': 10}
    elif risk_level == 8:
        # Very Aggressive: 20% VOO, 70% BTC, 10% Cash
        return {'VOO': 20, 'BTC': 70, 'cash': 10}
    else:  # 9-10
        # Extremely Aggressive: 10% VOO, 80% BTC, 10% Cash (min cash for safety)
        return {'VOO': 10, 'BTC': 80, 'cash': 10}

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


# def getUser():
#     session = login_form(
#         url=SUPABASE_URL,
#         apiKey=SUPABASE_KEY,
#         providers=["google"],
#     )

#     if session:
#         return session

#     return None


# user = getUser()



# Check if user has completed questionnaire
if not check_questionnaire_status():
    show_questionnaire()
else:
    # custom CSS 
    st.markdown("""
    <style>
    .stButton button {
        width: 100%;
    }
    .main {
        padding: 0.5rem 0.5rem 0.5rem 0.5rem;
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
    /* Reduce header padding */
    .stMarkdownContainer {
        padding: 0 !important;
    }
    /* Reduce container padding */
    [data-testid="stAppViewContainer"] {
        padding-top: 0.1rem;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }
    /* Reduce divider spacing */
    hr {
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # sign up/log in buttons
    header_cols = st.columns([4, 1, 1])
    with header_cols[0]:
        st.title("📈 Investorly Dashboard")
    with header_cols[2]:
        if logout_button("log in"):
            st.rerun()

    st.divider()

    # main layout: Left selector | Middle dashboard | Right panel
    if st.session_state.right_panel_visible:
        left_col, middle_col, right_col = st.columns([2.2, 3.8, 2])
    else:
        left_col, middle_col, right_col = st.columns([2.2, 5.8, 0.1])
    # LEFT PANEL -> Investment Settings & Asset Allocation
    with left_col:
        with st.container(border=True):
            st.subheader("💼 Investment Settings")

            st.write("**Investment Amount**")
            # Ensure investment_amount is an integer
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
            investment_date = st.date_input(
                "Investment Date",
                value=datetime.now() - timedelta(days=365),
                label_visibility="collapsed"
            )
            st.caption(f"📅 Simulates returns from {investment_date} to today")

            st.write("**Risk Tolerance**")
            risk_scale = st.slider(
                "Risk Scale",
                min_value=1,
                max_value=10,
                value=st.session_state.risk_scale,
                label_visibility="collapsed"
            )

            st.session_state.risk_scale = risk_scale

            # Check if risk scale changed and auto-apply new allocation
            if risk_scale != st.session_state.last_risk_scale:
                st.session_state.last_risk_scale = risk_scale
                # Auto-apply the risk-based allocation
                risk_alloc = get_risk_based_allocation(risk_scale)
                st.session_state.selected_assets['VOO'] = risk_alloc['VOO']
                st.session_state.selected_assets['BTC'] = risk_alloc['BTC']
                # Force rerun to update all dependent values
                st.rerun()

            risk_descriptions = {
                1: "🛡️ Very Conservative - Prioritize stability",
                2: "🛡️ Conservative - Lower volatility",
                3: "🛡️ Conservative - Moderate VOO focus",
                4: "⚖️ Moderate-Conservative - Balanced approach",
                5: "⚖️ Moderate - Even VOO/BTC split",
                6: "⚖️ Moderate-Aggressive - Crypto lean",
                7: "🚀 Aggressive - Higher volatility",
                8: "🚀 Very Aggressive - Crypto focus",
                9: "🚀 Extremely Aggressive - Maximum volatility",
                10: "🚀 Extremely Aggressive - Max volatility"
            }
            st.caption(risk_descriptions.get(risk_scale, "Unknown risk level"))

            st.divider()

            # Asset Allocation -> Independent sliders
            st.write("**📊 Asset Allocation**")
            st.caption("Set allocations independently - remaining % will be held as cash")

            # Placeholder for Current Allocation display (will be updated after sliders)
            allocation_display_placeholder = st.empty()

            suggested_alloc = get_risk_based_allocation(risk_scale)

            allocations = {}

            st.write("**Adjust Allocations (Optional)**")
            st.caption("Override risk-based suggestions by adjusting sliders below")

            for category_name, category_assets in ASSETS.items():
                with st.expander(f"{category_name.title()}", expanded=True):
                    for ticker, asset_info in category_assets.items():
                        current_alloc = st.session_state.selected_assets.get(ticker, 0)
                        if isinstance(current_alloc, str):
                            current_alloc = int(current_alloc) if current_alloc else 0

                        # Slider with full range - user can override risk-based allocation
                        # include risk_scale in key so sliders reset when risk changes
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
                            st.markdown(f"<div style='padding: 8px 0'><b>{asset_info['icon']} {ticker}</b><br/><span style='font-size: 0.85em; color: #666'>{asset_info['name']}</span></div>", unsafe_allow_html=True)

                        with col2:
                            risk_based_pct = suggested_alloc.get(ticker, 0)
                            if alloc_pct != risk_based_pct and risk_based_pct > 0:
                                st.markdown(f"<div style='padding: 12px 0; text-align: right'><b style='color: #FFA500'>{alloc_pct}%</b><br/><span style='font-size: 0.75em; color: #999'>Risk: {risk_based_pct}%</span></div>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<div style='padding: 12px 0; text-align: right'><b>{alloc_pct}%</b></div>", unsafe_allow_html=True)

            total_allocation = sum(allocations.values())

            normalized_allocations = {k: v for k, v in allocations.items() if v > 0}

            # update the Current Allocation display with actual slider values
            current_voo = allocations.get('VOO', 0)
            current_btc = allocations.get('BTC', 0)
            current_cash = 100 - total_allocation

            with allocation_display_placeholder.container():
                with st.expander(f"📊 Current Allocation (Auto-adjusted by Risk Level)", expanded=True):
                    st.markdown("**Your allocations automatically adjust based on your risk tolerance:**")
                    alloc_display_cols = st.columns(3)

                    with alloc_display_cols[0]:
                        st.metric("VOO", f"{current_voo}%")
                    with alloc_display_cols[1]:
                        st.metric("BTC", f"{current_btc}%")
                    with alloc_display_cols[2]:
                        st.metric("Cash", f"{current_cash}%")

                    st.caption("💡 Adjust sliders below to update allocations")

            # Detect manual slider changes and update risk level accordingly
            current_risk = get_risk_from_allocation(allocations.get('VOO', 0), allocations.get('BTC', 0))

            # Check if allocations differ from risk-based suggestion
            risk_based_voo = suggested_alloc['VOO']
            risk_based_btc = suggested_alloc['BTC']
            user_overrode = (allocations.get('VOO', 0) != risk_based_voo) or (allocations.get('BTC', 0) != risk_based_btc)

            # If user manually changed allocations, update the risk slider
            if user_overrode and current_risk != risk_scale:
                st.session_state.risk_scale = current_risk
                st.session_state.last_risk_scale = current_risk

            st.divider()

            # Show allocation status with validation
            if total_allocation > 100:
                st.error(f"❌ Total: {total_allocation}% (exceeds 100%! Please adjust.)")
            elif total_allocation == 100:
                st.success(f"✅ 100% Allocated (no cash)")
            else:
                unallocated = 100 - total_allocation
                st.info(f"💡 {unallocated}% in Cash (unallocated)")

            # Ensure normalized_allocations is set for calculations
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
                    if st.button("◀", key="hide_panel", use_container_width=True):
                        st.session_state.right_panel_visible = False
                        st.rerun()

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
