from dotenv import load_dotenv
from streamlit_supabase_auth import login_form, logout_button
from supabase import create_client
import streamlit as st
import os
from streamlit_local_storage import LocalStorage
from onboarding import show_onboarding, check_onboarding_status, reset_onboarding


load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
supabase = create_client(supabase_key=SUPABASE_KEY, supabase_url=SUPABASE_URL)
storage = LocalStorage()

# Initialize session state
if 'right_panel_visible' not in st.session_state:
    st.session_state.right_panel_visible = True

if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

if 'investment_amount' not in st.session_state:
    st.session_state.investment_amount = 10000

if 'risk_scale' not in st.session_state:
    st.session_state.risk_scale = 5

if 'etf_percentage' not in st.session_state:
    st.session_state.etf_percentage = 50

if 'hy_saving_percentage' not in st.session_state:
    st.session_state.hy_saving_percentage = 20

if 'bitcoin_percentage' not in st.session_state:
    st.session_state.bitcoin_percentage = 5

# Configure page
st.set_page_config(
    page_title="Investorly Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)


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
        </style>
        """, unsafe_allow_html=True)
        
        # Header with sign up/log in buttons
        header_cols = st.columns([4, 1, 1])
        with header_cols[0]:
            st.title("Dashboard NAME")
        with header_cols[2]:
            if logout_button("log in"):
                st.rerun()
        
        st.divider()
        
        # Create main layout: Left selector | Middle dashboard | Right panel
        if st.session_state.right_panel_visible:
            left_col, middle_col, right_col = st.columns([2, 4, 2])
        else:
            left_col, middle_col, right_col = st.columns([2, 6, 0.1])
        
        # LEFT PANEL - Mock Investment Selector
        with left_col:
            with st.container(border=True):
                st.subheader("Mock Inverst")
                
                st.write("**How much you'll invest**")
                investment_amount = st.text_input(
                    "Investment Amount",
                    value=str(st.session_state.investment_amount),
                    label_visibility="collapsed"
                )
                
                st.write("**When you wish you've invested**")
                investment_date = st.date_input(
                    "Investment Date",
                    label_visibility="collapsed"
                )
                
                st.write("**Risk Scale**")
                risk_scale = st.slider(
                    "Risk Scale",
                    min_value=1,
                    max_value=10,
                    value=st.session_state.risk_scale,
                    label_visibility="collapsed"
                )
                st.caption("1-10")
                
                st.write("**Percentage of ETF (S&P500)**")
                etf_percentage = st.slider(
                    "ETF Percentage",
                    min_value=0,
                    max_value=100,
                    value=st.session_state.etf_percentage,
                    label_visibility="collapsed"
                )
                st.caption("50%")
                
                st.write("**Percentage of HY Saving**")
                hy_percentage = st.slider(
                    "HY Saving Percentage",
                    min_value=0,
                    max_value=100,
                    value=st.session_state.hy_saving_percentage,
                    label_visibility="collapsed"
                )
                st.caption("20%")
                
                st.write("**Percentage of Bitcoin**")
                bitcoin_percentage = st.slider(
                    "Bitcoin Percentage",
                    min_value=0,
                    max_value=100,
                    value=st.session_state.bitcoin_percentage,
                    label_visibility="collapsed"
                )
                st.caption("5%")
        
        # MIDDLE PANEL - Dashboard
        with middle_col:
            # Output Results
            with st.container(border=True):
                st.subheader("Output: Your return result")
                
                output_cols = st.columns(2)
                with output_cols[0]:
                    st.write("**Total return**")
                    st.write("- from ETF")
                    st.write("- from Mutual Fund")
                    st.write("- ....")
                
                with output_cols[1]:
                    st.write("**After taxes, ...**")
            
            st.write("")  # Spacing
            
            # Charts Grid
            chart_row1 = st.columns(2)
            with chart_row1[0]:
                with st.container(border=True, height=200):
                    st.write("**Chart: ETF (VOO)**")
                    st.area_chart({"data": [1, 2, 3, 4, 5]})
            
            with chart_row1[1]:
                with st.container(border=True, height=200):
                    st.write("**Chart: HY Saving**")
                    st.line_chart({"data": [2, 3, 2, 4, 3]})
            
            chart_row2 = st.columns(2)
            with chart_row2[0]:
                with st.container(border=True, height=200):
                    st.write("**Chart**")
            
            with chart_row2[1]:
                with st.container(border=True, height=200):
                    st.write("**Chart**")
        
        # RIGHT PANEL - AI Chat with Terms (Collapsible)
        with right_col:
            if st.session_state.right_panel_visible:
                # Toggle buttoN
                
                # AI Chatbot with Terms Explanation inside
                with st.container(border=True):
                    # Header with hide button on same line
                    header_col1, header_col2 = st.columns([1, 2])
                    with header_col2:
                        st.subheader("🤖 AI Chatbot")
                    with header_col1:
                        st.write("")  # Spacing for alignment
                        if st.button("◀", key="hide_panel", use_container_width=True):
                            st.session_state.right_panel_visible = False
                            st.rerun()
                    
                    # Terms Explanation Section
                    with st.expander("📚 Terms explanation", expanded=False):
                        st.write("**Purpose of this dashboard ˅**")
                        st.caption("Learn about investment options and tools available.")
                        
                        st.divider()
                        
                        st.write("**ETFs ˅**")
                        st.caption("Exchange-Traded Funds are investment funds traded on stock exchanges.")
                        
                        st.write("**Mutual Funds ˅**")
                        st.caption("Pooled investments managed by professionals.")
                        
                        st.write("**HY Savings ˅**")
                        st.caption("High-Yield Savings accounts offer better interest rates.")
                        
                        st.write("**CD (Certificate of Deposit)**")
                        st.caption("Time deposits with fixed interest rates and maturity dates.")
                        
                        st.write("**Crypto ˅**")
                        st.caption("Digital or virtual currencies using cryptography.")
                    
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
                        st.session_state.chat_messages.append({
                            "role": "user",
                            "content": user_input
                        })
                        
                        # Simulate AI response
                        ai_response = f"Thanks for your question! I'll help you with: '{user_input}'"
                        
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "content": ai_response
                        })
                        
                        st.rerun()
                    
                    if st.button("Clear Chat", use_container_width=True):
                        st.session_state.chat_messages = []
                        st.rerun()
            else:
                # Show button when panel is hidden
                if st.button("▶", key="show_panel"):
                    st.session_state.right_panel_visible = True
                    st.rerun()
