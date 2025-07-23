"""
Web utility functions for OptionPilot Streamlit interface.

Contains helper functions for session state management and strategy building.
"""

import streamlit as st
from datetime import datetime
from .models import Strategy, OptionLeg, OptionContract


def initialize_session_state():
    """Initialize all required session state variables."""
    if 'current_strategy' not in st.session_state:
        st.session_state.current_strategy = None
    if 'current_metrics' not in st.session_state:
        st.session_state.current_metrics = None
    if 'current_stock_price' not in st.session_state:
        st.session_state.current_stock_price = 0.0
    if 'ai_analysis' not in st.session_state:
        st.session_state.ai_analysis = None


def create_strategy_from_form_data(selected_symbol, expiration_date, leg1_data, leg2_data=None):
    """
    Create Strategy object from form data.
    
    Args:
        selected_symbol: Stock symbol
        expiration_date: Option expiration date
        leg1_data: Tuple of (action, type, strike, bid, ask) for leg 1
        leg2_data: Optional tuple for leg 2
        
    Returns:
        Strategy object
    """
    legs = []
    
    # Create leg 1
    action, option_type, strike, bid, ask = leg1_data
    contract1 = OptionContract(
        symbol=selected_symbol,
        strike=strike,
        expiration=expiration_date,
        option_type=option_type,
        bid=bid,
        ask=ask
    )
    legs.append(OptionLeg(action=action, contract=contract1))
    
    # Create leg 2 if provided
    if leg2_data:
        action, option_type, strike, bid, ask = leg2_data
        contract2 = OptionContract(
            symbol=selected_symbol,
            strike=strike,
            expiration=expiration_date,
            option_type=option_type,
            bid=bid,
            ask=ask
        )
        legs.append(OptionLeg(action=action, contract=contract2))
    
    return Strategy(
        legs=legs,
        underlying_symbol=selected_symbol,
        created_at=datetime.now()
    )


def calculate_strategy_metrics(strategy):
    """Calculate metrics for given strategy and update session state."""
    from .strategy_calculator import StrategyCalculator
    
    calculator = StrategyCalculator()
    metrics = calculator.calculate_strategy_metrics(strategy)
    
    # Update session state
    st.session_state.current_strategy = strategy
    st.session_state.current_metrics = metrics
    
    return metrics


def setup_page_config():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="OptionPilot - AI Options Strategy Analyzer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def render_page_header():
    """Render the main page title and description."""
    st.title("📊 OptionPilot - AI Options Strategy Analyzer")
    st.markdown("**Analyze options strategies with AI-powered insights and payoff visualization**")


def render_page_footer():
    """Render the page footer with disclaimer."""
    st.markdown("---")
    st.markdown("**OptionPilot MVP** - AI-powered options strategy analyzer for educational purposes only")


def render_strategy_builder_tab():
    """Render the complete strategy builder tab content."""
    from .web_components import (
        render_stock_selection_sidebar,
        render_stock_quote_section,
        render_strategy_form,
        render_metrics_table,
        render_payoff_diagram,
        render_ai_analysis_section,
        render_save_strategy_button
    )
    
    # Sidebar for controls
    with st.sidebar:
        st.header("🔧 Strategy Configuration")
        selected_symbol = render_stock_selection_sidebar()
        render_stock_quote_section(selected_symbol)

    # Main content area
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("🏗️ Strategy Builder")
        submitted, expiration_date, leg1_data, leg2_data = render_strategy_form(selected_symbol)
        
        if submitted:
            try:
                strategy = create_strategy_from_form_data(selected_symbol, expiration_date, leg1_data, leg2_data)
                calculate_strategy_metrics(strategy)
                st.success("✅ Strategy built successfully!")
            except Exception as e:
                st.error(f"❌ Error building strategy: {e}")

    with col2:
        st.header("📊 Strategy Analysis")
        
        if st.session_state.current_strategy and st.session_state.current_metrics:
            metrics = st.session_state.current_metrics
            render_metrics_table(metrics)
            render_payoff_diagram(st.session_state.current_strategy, st.session_state.current_stock_price)
            render_ai_analysis_section(st.session_state.current_strategy, st.session_state.current_metrics, st.session_state.current_stock_price)
            render_save_strategy_button(st.session_state.current_strategy, st.session_state.current_metrics)
        else:
            st.info("💡 Build a strategy using the form on the left to see analysis results")