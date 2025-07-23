"""
OptionPilot - Streamlit Web Interface

AI-powered options strategy analyzer with interactive web interface.
Provides stock selection, strategy building, metrics calculation, and payoff visualization.
"""

import streamlit as st
from datetime import datetime, date
import matplotlib.pyplot as plt
from src.market_data import MarketDataService, MarketDataError
from src.strategy_calculator import StrategyCalculator
from src.ai_analyzer import AIAnalyzer, AIAnalysisError
from src.trading_journal import TradingJournal, TradingJournalError
from src.models import Strategy, OptionLeg, OptionContract
from src.config import ConfigError, get_supported_symbols


# Page configuration
st.set_page_config(
    page_title="OptionPilot - AI Options Strategy Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'current_strategy' not in st.session_state:
    st.session_state.current_strategy = None
if 'current_metrics' not in st.session_state:
    st.session_state.current_metrics = None
if 'current_stock_price' not in st.session_state:
    st.session_state.current_stock_price = 0.0

# Title and header
st.title("📊 OptionPilot - AI Options Strategy Analyzer")
st.markdown("**Analyze options strategies with AI-powered insights and payoff visualization**")

# Sidebar for controls
with st.sidebar:
    st.header("🔧 Strategy Configuration")
    
    # Stock selection
    st.subheader("📈 Stock Selection")
    supported_symbols = get_supported_symbols()
    selected_symbol = st.selectbox(
        "Choose a stock symbol:",
        supported_symbols,
        index=0,
        help="Select from supported symbols for options analysis"
    )
    
    # Get stock quote button
    if st.button("Get Stock Quote", type="primary"):
        try:
            with st.spinner("Fetching stock data..."):
                market_service = MarketDataService()
                quote = market_service.get_stock_quote(selected_symbol)
                st.session_state.current_stock_price = quote.price
                st.success(f"✅ {quote.symbol}: ${quote.price:.2f}")
        except (MarketDataError, ConfigError) as e:
            st.error(f"❌ Error fetching quote: {e}")
    
    # Display current stock price if available
    if st.session_state.current_stock_price > 0:
        st.info(f"Current Price: ${st.session_state.current_stock_price:.2f}")

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.header("🏗️ Strategy Builder")
    
    # Strategy form
    with st.form("strategy_form"):
        st.subheader("Configure Strategy Legs")
        
        # Expiration date  
        from datetime import timedelta
        default_expiration = date.today() + timedelta(days=30)  # 30 days from today
        expiration_date = st.date_input(
            "Expiration Date:",
            value=default_expiration,
            min_value=date.today(),
            help="Select option expiration date"
        )
        
        # Leg 1 configuration
        st.markdown("**Leg 1 (Required)**")
        leg1_col1, leg1_col2 = st.columns(2)
        
        with leg1_col1:
            leg1_action = st.selectbox("Action:", ["buy", "sell"], key="leg1_action")
            leg1_type = st.selectbox("Option Type:", ["call", "put"], key="leg1_type")
        
        with leg1_col2:
            leg1_strike = st.number_input("Strike Price:", min_value=0.01, value=150.0, step=0.5, key="leg1_strike")
            leg1_col3, leg1_col4 = st.columns(2)
            with leg1_col3:
                leg1_bid = st.number_input("Bid:", min_value=0.0, value=8.50, step=0.05, key="leg1_bid")
            with leg1_col4:
                leg1_ask = st.number_input("Ask:", min_value=0.0, value=8.70, step=0.05, key="leg1_ask")
        
        # Leg 2 configuration (optional)
        add_leg2 = st.checkbox("Add Second Leg (for spreads)")
        
        leg2_action = leg2_type = leg2_strike = leg2_bid = leg2_ask = None
        if add_leg2:
            st.markdown("**Leg 2 (Optional)**")
            leg2_col1, leg2_col2 = st.columns(2)
            
            with leg2_col1:
                leg2_action = st.selectbox("Action:", ["buy", "sell"], key="leg2_action")
                leg2_type = st.selectbox("Option Type:", ["call", "put"], key="leg2_type")
            
            with leg2_col2:
                leg2_strike = st.number_input("Strike Price:", min_value=0.01, value=155.0, step=0.5, key="leg2_strike")
                leg2_col3, leg2_col4 = st.columns(2)
                with leg2_col3:
                    leg2_bid = st.number_input("Bid:", min_value=0.0, value=6.80, step=0.05, key="leg2_bid")
                with leg2_col4:
                    leg2_ask = st.number_input("Ask:", min_value=0.0, value=7.20, step=0.05, key="leg2_ask")
        
        # Build strategy button
        submitted = st.form_submit_button("Build Strategy", type="primary")
        
        if submitted:
            try:
                # Create strategy legs
                legs = []
                
                # Leg 1
                contract1 = OptionContract(
                    symbol=selected_symbol,
                    strike=leg1_strike,
                    expiration=expiration_date,
                    option_type=leg1_type,
                    bid=leg1_bid,
                    ask=leg1_ask
                )
                legs.append(OptionLeg(action=leg1_action, contract=contract1))
                
                # Leg 2 (if enabled)
                if add_leg2 and leg2_action:
                    contract2 = OptionContract(
                        symbol=selected_symbol,
                        strike=leg2_strike,
                        expiration=expiration_date,
                        option_type=leg2_type,
                        bid=leg2_bid,
                        ask=leg2_ask
                    )
                    legs.append(OptionLeg(action=leg2_action, contract=contract2))
                
                # Create strategy
                strategy = Strategy(
                    legs=legs,
                    underlying_symbol=selected_symbol,
                    created_at=datetime.now()
                )
                
                # Calculate metrics
                calculator = StrategyCalculator()
                metrics = calculator.calculate_strategy_metrics(strategy)
                
                # Store in session state
                st.session_state.current_strategy = strategy
                st.session_state.current_metrics = metrics
                
                st.success("✅ Strategy built successfully!")
                
            except Exception as e:
                st.error(f"❌ Error building strategy: {e}")

with col2:
    st.header("📊 Strategy Analysis")
    
    # Display metrics if strategy is built
    if st.session_state.current_strategy and st.session_state.current_metrics:
        metrics = st.session_state.current_metrics
        
        st.subheader("💰 Financial Metrics")
        
        # Metrics table
        metrics_data = {
            "Metric": ["Net Premium", "Max Profit", "Max Loss", "Breakeven Points", "Margin Requirement", "Return on Margin"],
            "Value": [
                f"${metrics.net_premium:.2f}",
                f"${metrics.max_profit:.2f}",
                f"${metrics.max_loss:.2f}",
                f"${metrics.breakeven_points[0]:.2f}" if metrics.breakeven_points else "N/A",
                f"${metrics.margin_requirement:.2f}",
                f"{metrics.return_on_margin:.2f}%"
            ]
        }
        
        st.table(metrics_data)
        
        # Payoff diagram
        if st.session_state.current_stock_price > 0:
            st.subheader("📈 Payoff Diagram")
            
            try:
                calculator = StrategyCalculator()
                fig = calculator.generate_payoff_diagram(
                    st.session_state.current_strategy,
                    st.session_state.current_stock_price
                )
                st.pyplot(fig, clear_figure=True)
            except Exception as e:
                st.error(f"❌ Error generating payoff diagram: {e}")
        else:
            st.info("💡 Get a stock quote first to see the payoff diagram")
    else:
        st.info("💡 Build a strategy using the form on the left to see analysis results")

# Footer
st.markdown("---")
st.markdown("**OptionPilot MVP** - AI-powered options strategy analyzer for educational purposes only")