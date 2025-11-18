import streamlit as st
from streamlit_local_storage import LocalStorage


def show_questionnaire():
    """Display the questionnaire flow for new users"""
    
    # Initialize session state for questionnaire
    if 'questionnaire_step' not in st.session_state:
        st.session_state.questionnaire_step = 0
    
    if 'questionnaire_data' not in st.session_state:
        st.session_state.questionnaire_data = {}
    
    # Step 0: Welcome
    if st.session_state.questionnaire_step == 0:
        show_welcome_step()
    
    # Step 1: Investment Profile
    elif st.session_state.questionnaire_step == 1:
        show_investment_profile_step()
    
    # Step 2: Preferences
    elif st.session_state.questionnaire_step == 2:
        show_preferences_step()

def show_welcome_step():
    """Welcome screen for new users"""
    st.title("👋 Welcome to Investorly!")
    st.write("---")
    
    st.markdown("""
    ### Get Started with Smart Investing
    
    We're excited to help you on your investment journey! Let's take a few moments to 
    personalize your experience.
    
    **What you'll do:**
    - 📊 Set up your investment profile
    - 🎯 Define your investment goals
    - ⚙️ Customize your preferences
    
    This will only take a couple of minutes.
    """)
    
    st.write("")
    st.write("")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("Get Started →", use_container_width=True, type="primary"):
            st.session_state.questionnaire_step = 1
            st.rerun()


def show_investment_profile_step():
    """Investment profile setup for new users"""
    st.title("📊 Investment Profile")
    st.write("---")
    
    st.markdown("### Tell us about your investment experience")
    
    # Experience level
    experience = st.radio(
        "What's your investment experience level?",
        ["Beginner - Just starting out", 
         "Intermediate - Some experience", 
         "Advanced - Experienced investor"],
        key="experience_level"
    )
    
    st.write("")
    
    # Investment goals
    st.markdown("### What are your investment goals?")
    goals = st.multiselect(
        "Select all that apply:",
        ["Long-term wealth building",
         "Retirement planning",
         "Short-term gains",
         "Passive income",
         "Portfolio diversification",
         "Learning and education"],
        key="investment_goals"
    )
    
    st.write("")
    
    # Risk tolerance
    risk_tolerance = st.select_slider(
        "What's your risk tolerance?",
        options=["Very Conservative", "Conservative", "Moderate", "Aggressive", "Very Aggressive"],
        value="Moderate",
        key="risk_tolerance"
    )
    
    st.write("")
    st.write("")
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.questionnaire_step = 0
            st.rerun()

    with col3:
        if st.button("Next →", use_container_width=True, type="primary"):
            if goals:  # Ensure at least one goal is selected
                st.session_state.questionnaire_data['experience'] = experience
                st.session_state.questionnaire_data['goals'] = goals
                st.session_state.questionnaire_data['risk_tolerance'] = risk_tolerance
                st.session_state.questionnaire_step = 2
                st.rerun()
            else:
                st.error("Please select at least one investment goal")


def show_preferences_step():
    """User preferences"""
    st.title("⚙️ Customize Your Experience")
    st.write("---")
    
    st.markdown("### Set your preferences")
    
    # Investment amount
    investment_range = st.select_slider(
        "What's your typical investment amount?",
        options=["$0 - $1,000", "$1,000 - $5,000", "$5,000 - $10,000", 
                 "$10,000 - $50,000", "$50,000+"],
        value="$1,000 - $5,000",
        key="investment_amount"
    )
    
    st.write("")
    
    # Industries of interest
    industries = st.multiselect(
        "Which industries interest you?",
        ["Technology", "Healthcare", "Finance", "Energy", 
         "Consumer Goods", "Real Estate", "Manufacturing", "All"],
        default=["Technology", "Healthcare"],
        key="industries"
    )
    
    st.write("")
    
    # Notification preferences
    st.markdown("### Notification Preferences")
    
    col1, col2 = st.columns(2)
    with col1:
        email_notifications = st.checkbox("Email notifications", value=True, key="email_notif")
        market_updates = st.checkbox("Market updates", value=True, key="market_updates")
    
    with col2:
        portfolio_alerts = st.checkbox("Portfolio alerts", value=True, key="portfolio_alerts")
        news_digest = st.checkbox("Daily news digest", value=False, key="news_digest")
    
    st.write("")
    st.write("")
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.questionnaire_step = 1
            st.rerun()

    with col3:
        if st.button("Complete Setup ✓", use_container_width=True, type="primary"):
            # Save all preferences
            st.session_state.questionnaire_data['investment_amount'] = investment_range
            st.session_state.questionnaire_data['industries'] = industries
            st.session_state.questionnaire_data['email_notifications'] = email_notifications
            st.session_state.questionnaire_data['market_updates'] = market_updates
            st.session_state.questionnaire_data['portfolio_alerts'] = portfolio_alerts
            st.session_state.questionnaire_data['news_digest'] = news_digest

            # Mark questionnaire as complete
            st.session_state.questionnaire_complete = True

            # Store in local storage
            storage = LocalStorage()
            storage.setItem("questionnaire_complete", "true")

            st.success("🎉 Your profile is all set up!")
            st.balloons()
            st.rerun()


def check_questionnaire_status():
    """Check if user has completed questionnaire"""
    storage = LocalStorage()

    # Check session state first
    if 'questionnaire_complete' in st.session_state and st.session_state.questionnaire_complete:
        return True

    # Check local storage
    questionnaire_status = storage.getItem("questionnaire_complete")
    if questionnaire_status == "true":
        st.session_state.questionnaire_complete = True
        return True

    return False


def reset_questionnaire():
    """Reset questionnaire status (useful for testing or re-questionnaire)"""
    storage = LocalStorage()
    storage.deleteItem("questionnaire_complete")

    if 'questionnaire_complete' in st.session_state:
        del st.session_state.questionnaire_complete
    if 'questionnaire_step' in st.session_state:
        del st.session_state.questionnaire_step
    if 'questionnaire_data' in st.session_state:
        del st.session_state.questionnaire_data
