"""
Web UI components for OptionPilot Streamlit interface.

Contains reusable UI components and form builders to keep the main app.py under 100 lines.
"""

import streamlit as st
from datetime import date, timedelta
from .models import OptionContract, OptionLeg, Strategy
from .config import get_supported_symbols


def render_stock_selection_sidebar():
    """Render stock selection section in sidebar."""
    st.subheader("📈 Stock Selection")
    supported_symbols = get_supported_symbols()
    selected_symbol = st.selectbox(
        "Choose a stock symbol:",
        supported_symbols,
        index=0,
        help="Select from supported symbols for options analysis"
    )
    return selected_symbol


def render_stock_quote_section(selected_symbol):
    """Render stock quote button and display current price."""
    if st.button("Get Stock Quote", type="primary"):
        try:
            from .market_data import MarketDataService, MarketDataError
            from .config import ConfigError
            
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


def render_leg_configuration(leg_number, default_strike=150.0, default_bid=8.50, default_ask=8.70):
    """Render option leg configuration UI."""
    # Use different defaults for leg 2
    if leg_number == 2:
        default_strike = 155.0
        default_bid = 6.80
        default_ask = 7.20
    
    st.markdown(f"**Leg {leg_number}**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        action = st.selectbox("Action:", ["buy", "sell"], key=f"leg{leg_number}_action")
        option_type = st.selectbox("Option Type:", ["call", "put"], key=f"leg{leg_number}_type")
    
    with col2:
        strike = st.number_input("Strike Price:", min_value=0.01, value=default_strike, step=0.5, key=f"leg{leg_number}_strike")
        col3, col4 = st.columns(2)
        with col3:
            bid = st.number_input("Bid:", min_value=0.0, value=default_bid, step=0.05, key=f"leg{leg_number}_bid")
        with col4:
            ask = st.number_input("Ask:", min_value=0.0, value=default_ask, step=0.05, key=f"leg{leg_number}_ask")
    
    return action, option_type, strike, bid, ask


def render_strategy_form(selected_symbol):
    """Render the complete strategy building form."""
    with st.form("strategy_form"):
        st.subheader("Configure Strategy Legs")
        
        # Expiration date
        default_expiration = date.today() + timedelta(days=30)
        expiration_date = st.date_input(
            "Expiration Date:",
            value=default_expiration,
            min_value=date.today(),
            help="Select option expiration date"
        )
        
        # Leg 1 configuration (required)
        st.markdown("**Leg 1 (Required)**")
        leg1_action, leg1_type, leg1_strike, leg1_bid, leg1_ask = render_leg_configuration(1)
        
        # Leg 2 configuration (optional)
        add_leg2 = st.checkbox("Add Second Leg (for spreads)")
        leg2_data = None
        
        if add_leg2:
            st.markdown("**Leg 2 (Optional)**")
            leg2_action, leg2_type, leg2_strike, leg2_bid, leg2_ask = render_leg_configuration(2)
            leg2_data = (leg2_action, leg2_type, leg2_strike, leg2_bid, leg2_ask)
        
        # Build strategy button
        submitted = st.form_submit_button("Build Strategy", type="primary")
        
        return submitted, expiration_date, (leg1_action, leg1_type, leg1_strike, leg1_bid, leg1_ask), leg2_data


def render_metrics_table(metrics):
    """Render financial metrics in a table format."""
    st.subheader("💰 Financial Metrics")
    
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


def render_payoff_diagram(strategy, current_stock_price):
    """Render payoff diagram if stock price is available."""
    if current_stock_price > 0:
        st.subheader("📈 Payoff Diagram")
        
        try:
            from .strategy_calculator import StrategyCalculator
            calculator = StrategyCalculator()
            fig = calculator.generate_payoff_diagram(strategy, current_stock_price)
            st.pyplot(fig, clear_figure=True)
        except Exception as e:
            st.error(f"❌ Error generating payoff diagram: {e}")
    else:
        st.info("💡 Get a stock quote first to see the payoff diagram")


def render_ai_analysis_section(strategy, metrics, current_stock_price):
    """Render AI analysis section with analysis button and results."""
    st.subheader("🤖 AI Strategy Analysis")
    
    if current_stock_price <= 0:
        st.info("💡 Get a stock quote first to enable AI analysis")
        return
    
    if st.button("Analyze Strategy with AI", type="secondary"):
        try:
            from .ai_analyzer import AIAnalyzer, AIAnalysisError
            from .config import ConfigError
            
            with st.spinner("Analyzing strategy with AI..."):
                analyzer = AIAnalyzer()
                analysis = analyzer.analyze_strategy(strategy, metrics, current_stock_price)
                
                # Store analysis results in session state
                st.session_state.ai_analysis = analysis
                
                st.success("✅ AI analysis completed!")
                
        except (AIAnalysisError, ConfigError) as e:
            st.error(f"❌ AI analysis failed: {e}")
    
    # Display analysis results if available
    if hasattr(st.session_state, 'ai_analysis') and st.session_state.ai_analysis:
        analysis = st.session_state.ai_analysis
        
        st.markdown("**🔍 Strategy Interpretation:**")
        st.info(analysis['interpretation'])
        
        st.markdown("**📈 Market Outlook:**")
        st.info(analysis['market_outlook'])
        
        st.markdown("**⚠️ Risk Warning:**")
        st.warning(analysis['risk_warning'])


def render_save_strategy_button(strategy, metrics):
    """Render save strategy to journal button."""
    if st.button("💾 Save Strategy to Journal", type="primary"):
        try:
            from .trading_journal import TradingJournal, TradingJournalError
            
            with st.spinner("Saving strategy to journal..."):
                journal = TradingJournal()
                trade = journal.save_trade(strategy, metrics)
                st.success(f"✅ Strategy saved! Trade ID: {trade.id}")
                
                # Refresh journal data in session state
                if 'journal_data' in st.session_state:
                    del st.session_state.journal_data
                    
        except TradingJournalError as e:
            st.error(f"❌ Failed to save strategy: {e}")


def render_trading_journal_page():
    """Render the complete trading journal page."""
    st.title("📋 Trading Journal")
    st.markdown("**Track and manage your paper trading strategies**")
    
    # Load journal data if not already loaded
    if 'journal_data' not in st.session_state:
        try:
            from .trading_journal import TradingJournal, TradingJournalError
            journal = TradingJournal()
            st.session_state.journal_data = journal.get_all_trades()
        except TradingJournalError as e:
            st.error(f"❌ Failed to load journal: {e}")
            return
    
    trades = st.session_state.journal_data
    
    if not trades:
        st.info("📝 No trades found. Build and save a strategy first!")
        return
    
    st.subheader("📊 Trade Summary")
    
    # Summary metrics
    total_trades = len(trades)
    open_trades = len([t for t in trades if t.status == 'open'])
    closed_trades = len([t for t in trades if t.status == 'closed'])
    total_pnl = sum([t.final_pnl for t in trades if t.final_pnl is not None])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Trades", total_trades)
    with col2:
        st.metric("Open Trades", open_trades)
    with col3:
        st.metric("Closed Trades", closed_trades)
    with col4:
        st.metric("Total P&L", f"${total_pnl:.2f}")
    
    st.subheader("📈 Trade History")
    
    # Trade list
    for trade in trades:
        with st.expander(f"{'🟢' if trade.status == 'open' else '🔴'} Trade #{trade.id} - {trade.strategy.underlying_symbol} ({trade.entry_date})"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Symbol:** {trade.strategy.underlying_symbol}")
                st.write(f"**Entry Date:** {trade.entry_date}")
                st.write(f"**Status:** {trade.status.title()}")
                st.write(f"**Net Premium:** ${trade.metrics.net_premium:.2f}")
                st.write(f"**Max Profit:** ${trade.metrics.max_profit:.2f}")
                st.write(f"**Max Loss:** ${trade.metrics.max_loss:.2f}")
                
                # Strategy legs
                st.write("**Strategy Legs:**")
                for i, leg in enumerate(trade.strategy.legs, 1):
                    st.write(f"  Leg {i}: {leg.action.title()} {leg.contract.option_type.title()} ${leg.contract.strike}")
            
            with col2:
                if trade.status == 'open':
                    st.write("**Close Trade**")
                    closing_price = st.number_input(f"Closing Price", key=f"close_price_{trade.id}", min_value=0.01, value=150.0, step=0.5)
                    
                    if st.button(f"Close Trade #{trade.id}", key=f"close_btn_{trade.id}"):
                        try:
                            from .trading_journal import TradingJournal, TradingJournalError
                            journal = TradingJournal()
                            updated_trade = journal.close_trade(trade.id, closing_price)
                            st.success(f"✅ Trade closed! P&L: ${updated_trade.final_pnl:.2f}")
                            
                            # Refresh journal data
                            del st.session_state.journal_data
                            st.rerun()
                            
                        except TradingJournalError as e:
                            st.error(f"❌ Failed to close trade: {e}")
                else:
                    st.write(f"**Final P&L:** ${trade.final_pnl:.2f}")
                    st.write(f"**Closing Price:** ${trade.closing_price:.2f}")
    
    # Refresh button
    if st.button("🔄 Refresh Journal"):
        if 'journal_data' in st.session_state:
            del st.session_state.journal_data
        st.rerun()