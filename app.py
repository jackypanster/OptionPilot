"""
OptionPilot - Streamlit Web Interface

AI-powered options strategy analyzer with interactive web interface.
Provides stock selection, strategy building, metrics calculation, and payoff visualization.
"""

import streamlit as st
from src.web_utils import (
    initialize_session_state, 
    setup_page_config, 
    render_page_header, 
    render_page_footer,
    render_strategy_builder_tab
)
from src.web_components import render_trading_journal_page

# Setup page configuration
setup_page_config()

# Initialize session state
initialize_session_state()

# Render page header
render_page_header()

# Create tabs for different pages
tab1, tab2 = st.tabs(["🏗️ Strategy Builder", "📋 Trading Journal"])

with tab1:
    render_strategy_builder_tab()

with tab2:
    render_trading_journal_page()

# Render page footer
render_page_footer()