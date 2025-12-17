"""
Market Tracker - Page 3 (Rebuilt)
Track new issuance, deal flow, and market developments
Uses Bloomberg MCAL for live deal data
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
from pathlib import Path
import io

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import Bloomberg MCAL
try:
    from models.bloomberg_client import BloombergMCAL, BloombergClient, get_bloomberg_client
    BLOOMBERG_AVAILABLE = True
except ImportError:
    BLOOMBERG_AVAILABLE = False

st.markdown('<p class="main-header">Market Tracker</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Track new issuance and deal flow from Bloomberg MCAL</p>', unsafe_allow_html=True)

# ============================================================================
# BLOOMBERG CONNECTION
# ============================================================================

@st.cache_resource
def get_mcal_client():
    """Get Bloomberg MCAL client (cached)"""
    if BLOOMBERG_AVAILABLE:
        try:
            client = get_bloomberg_client()
            if client.is_available():
                return BloombergMCAL(client)
        except Exception as e:
            print(f"Bloomberg MCAL connection error: {e}")
    return None

mcal = get_mcal_client()

# Show connection status
if mcal and mcal.is_available():
    st.sidebar.success("Bloomberg MCAL Connected")
else:
    st.sidebar.warning("Bloomberg Offline - Use Search")

# ============================================================================
# SIDEBAR - SEARCH CONTROLS
# ============================================================================

st.sidebar.markdown("### Deal Search")

# Search by shelf/issuer
search_term = st.sidebar.text_input(
    "Search Shelf/Issuer",
    placeholder="e.g., ACMAT, DRIVE, CARMX",
    help="Enter deal shelf prefix (e.g., ACMAT, DRIVE, ALLY)"
)

# Or search specific deal
st.sidebar.markdown("#### Or Lookup Specific Deal")
col1, col2 = st.sidebar.columns(2)
with col1:
    deal_prefix = st.text_input("Shelf", placeholder="ACMAT")
with col2:
    deal_year = st.number_input("Year", min_value=2020, max_value=2030, value=2025)
deal_series = st.sidebar.number_input("Series #", min_value=1, max_value=20, value=1)

search_button = st.sidebar.button("Search Bloomberg", type="primary", use_container_width=True)

st.sidebar.markdown("---")

# Recent deals lookup
st.sidebar.markdown("### Quick Lookups")
days_back = st.sidebar.slider("Days to look back", 7, 90, 30)

if st.sidebar.button("Fetch Recent Deals", use_container_width=True):
    st.session_state['fetch_recent'] = True

# ============================================================================
# MAIN CONTENT
# ============================================================================

# Initialize session state for results
if 'deal_results' not in st.session_state:
    st.session_state['deal_results'] = None
if 'selected_deal' not in st.session_state:
    st.session_state['selected_deal'] = None

# Handle search
if search_button:
    if not mcal or not mcal.is_available():
        st.error("Bloomberg is not connected. Please ensure Bloomberg Terminal is running.")
    else:
        with st.spinner("Searching Bloomberg..."):
            if search_term:
                # Search by shelf prefix
                results = mcal.search_abs_deals(search_term)
                if results is not None and not results.empty:
                    st.session_state['deal_results'] = results
                    st.success(f"Found {len(results)} tranches")
                else:
                    st.warning(f"No deals found for '{search_term}'")
                    st.session_state['deal_results'] = None
            elif deal_prefix:
                # Lookup specific deal
                deal_info = mcal.get_deal_details(deal_prefix, deal_year, deal_series)
                if deal_info and deal_info.get('tranches'):
                    st.session_state['selected_deal'] = deal_info
                    st.success(f"Found {deal_info['deal_name']}")
                else:
                    st.warning(f"Deal {deal_prefix} {deal_year}-{deal_series} not found")
                    st.session_state['selected_deal'] = None

# Handle recent deals fetch
if st.session_state.get('fetch_recent'):
    st.session_state['fetch_recent'] = False
    if mcal and mcal.is_available():
        with st.spinner(f"Fetching deals from last {days_back} days..."):
            results = mcal.get_recent_abs_deals(days=days_back)
            if results is not None and not results.empty:
                st.session_state['deal_results'] = results
                st.success(f"Found {len(results)} tranches from recent deals")
            else:
                st.info("No recent deals found. Try expanding the date range or searching by shelf.")
    else:
        st.error("Bloomberg is not connected.")

# ============================================================================
# DISPLAY RESULTS
# ============================================================================

tab1, tab2, tab3 = st.tabs(["Search Results", "Deal Details", "Manual Entry"])

# TAB 1: Search Results
with tab1:
    st.markdown("### Search Results")

    if st.session_state.get('deal_results') is not None:
        df = st.session_state['deal_results']

        # Display summary metrics
        if not df.empty:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                total_size = df['AMT_ISSUED'].sum() / 1_000_000 if 'AMT_ISSUED' in df.columns else 0
                st.metric("Total Volume", f"${total_size:,.0f}M")

            with col2:
                unique_deals = df['ticker'].apply(lambda x: ' '.join(x.split()[:2])).nunique() if 'ticker' in df.columns else 0
                st.metric("Deals", unique_deals)

            with col3:
                if 'SPREAD_TO_BENCHMARK' in df.columns:
                    avg_spread = df['SPREAD_TO_BENCHMARK'].mean()
                    st.metric("Avg Spread", f"+{avg_spread:.0f}bps" if pd.notna(avg_spread) else "N/A")
                else:
                    st.metric("Avg Spread", "N/A")

            with col4:
                if 'ISSUE_DT' in df.columns:
                    latest = pd.to_datetime(df['ISSUE_DT']).max()
                    st.metric("Latest", latest.strftime('%Y-%m-%d') if pd.notna(latest) else "N/A")
                else:
                    st.metric("Latest", "N/A")

            st.markdown("---")

            # Format display columns
            display_cols = ['ticker', 'NAME', 'ISSUER', 'ISSUE_DT', 'AMT_ISSUED', 'CPN',
                          'SPREAD_TO_BENCHMARK', 'RTG_SP', 'WAL_TO_MAT', 'MTG_COLLATERAL_TYP']
            available_cols = [c for c in display_cols if c in df.columns]

            display_df = df[available_cols].copy()

            # Format columns for display
            if 'AMT_ISSUED' in display_df.columns:
                display_df['AMT_ISSUED'] = display_df['AMT_ISSUED'].apply(
                    lambda x: f"${x/1_000_000:.1f}M" if pd.notna(x) else ""
                )
            if 'SPREAD_TO_BENCHMARK' in display_df.columns:
                display_df['SPREAD_TO_BENCHMARK'] = display_df['SPREAD_TO_BENCHMARK'].apply(
                    lambda x: f"+{x:.0f}bps" if pd.notna(x) else ""
                )
            if 'CPN' in display_df.columns:
                display_df['CPN'] = display_df['CPN'].apply(
                    lambda x: f"{x:.2f}%" if pd.notna(x) else ""
                )
            if 'WAL_TO_MAT' in display_df.columns:
                display_df['WAL_TO_MAT'] = display_df['WAL_TO_MAT'].apply(
                    lambda x: f"{x:.2f}yr" if pd.notna(x) else ""
                )

            # Rename columns for display
            column_names = {
                'ticker': 'Ticker',
                'NAME': 'Name',
                'ISSUER': 'Issuer',
                'ISSUE_DT': 'Issue Date',
                'AMT_ISSUED': 'Size',
                'CPN': 'Coupon',
                'SPREAD_TO_BENCHMARK': 'Spread',
                'RTG_SP': 'S&P',
                'WAL_TO_MAT': 'WAL',
                'MTG_COLLATERAL_TYP': 'Collateral'
            }
            display_df = display_df.rename(columns=column_names)

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Export option
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    "bloomberg_deals.csv",
                    "text/csv",
                    use_container_width=True
                )
    else:
        st.info("Enter a search term or fetch recent deals to see results.")
        st.markdown("""
        **How to search:**
        - Enter a deal shelf prefix (e.g., `ACMAT`, `DRIVE`, `CARMX`, `ALLY`)
        - Or lookup a specific deal by shelf, year, and series number
        - Or click "Fetch Recent Deals" to pull recent issuance

        **Common ABS Shelves:**
        - `ACMAT` - America's Car-Mart (Subprime Auto)
        - `DRIVE` - Santander Drive (Subprime Auto)
        - `CARMX` - CarMax (Prime Auto)
        - `ALLY` - Ally Financial (Auto)
        - `FORDO` - Ford Credit (Auto)
        - `COPAR` - Capital One Prime (Auto)
        - `AMCAR` - AmeriCredit (Subprime Auto)
        """)

# TAB 2: Deal Details
with tab2:
    st.markdown("### Deal Details")

    if st.session_state.get('selected_deal'):
        deal = st.session_state['selected_deal']

        # Deal header
        st.markdown(f"## {deal.get('deal_name', 'Unknown Deal')}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Issuer", deal.get('issuer', 'N/A'))
        with col2:
            st.metric("Total Size", f"${deal.get('total_size', 0):,.0f}M")
        with col3:
            issue_date = deal.get('issue_date')
            st.metric("Issue Date", str(issue_date) if issue_date else 'N/A')

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Collateral", deal.get('collateral_type', 'N/A'))
        with col2:
            st.metric("Bookrunner", deal.get('bookrunner', 'N/A'))

        st.markdown("---")
        st.markdown("#### Tranche Structure")

        # Build tranche table
        tranches = deal.get('tranches', [])
        if tranches:
            tranche_data = []
            for t in tranches:
                tranche_data.append({
                    'Class': t.get('tranche_class', t.get('ticker', '').split()[2] if len(t.get('ticker', '').split()) > 2 else 'N/A'),
                    'Size ($M)': f"${(t.get('AMT_ISSUED', 0) or 0)/1_000_000:.1f}",
                    'Coupon': f"{t.get('CPN', 0):.2f}%" if t.get('CPN') else 'N/A',
                    'Spread': f"+{t.get('SPREAD_TO_BENCHMARK', 0):.0f}bps" if t.get('SPREAD_TO_BENCHMARK') else 'N/A',
                    'S&P': t.get('RTG_SP', 'N/A'),
                    "Moody's": t.get('RTG_MOODY', 'N/A'),
                    'WAL': f"{t.get('WAL_TO_MAT', 0):.2f}yr" if t.get('WAL_TO_MAT') else 'N/A',
                    'Yield': f"{t.get('YLD_YTM_MID', 0):.3f}%" if t.get('YLD_YTM_MID') else 'N/A',
                })

            st.dataframe(pd.DataFrame(tranche_data), use_container_width=True, hide_index=True)

            # Capital structure chart
            st.markdown("#### Capital Structure")

            fig = go.Figure()
            colors = {
                'AAA': '#1E3A5F', 'Aaa': '#1E3A5F',
                'AA': '#2E5A8F', 'Aa': '#2E5A8F',
                'A': '#4A7AB0',
                'BBB': '#FF9800', 'Baa': '#FF9800',
                'BB': '#E65100', 'Ba': '#E65100',
                'B': '#C62828',
                'NR': '#9E9E9E'
            }

            for t in tranches:
                size = (t.get('AMT_ISSUED', 0) or 0) / 1_000_000
                rating = t.get('RTG_SP', 'NR')
                tranche_class = t.get('tranche_class', '?')

                fig.add_trace(go.Bar(
                    y=[tranche_class],
                    x=[size],
                    orientation='h',
                    marker_color=colors.get(rating, '#666666'),
                    text=f"${size:.0f}M ({rating})",
                    textposition='inside',
                    name=tranche_class
                ))

            fig.update_layout(
                title="Capital Structure",
                xaxis_title="Size ($M)",
                height=300,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No tranche data available")
    else:
        st.info("Search for a specific deal using the sidebar to see details.")
        st.markdown("""
        **To view deal details:**
        1. Enter the shelf prefix (e.g., `ACMAT`)
        2. Enter the year (e.g., `2025`)
        3. Enter the series number (e.g., `4`)
        4. Click "Search Bloomberg"
        """)

# TAB 3: Manual Entry
with tab3:
    st.markdown("### Manual Deal Entry")
    st.caption("Add deals manually when Bloomberg is unavailable")

    col1, col2 = st.columns(2)

    with col1:
        manual_deal_name = st.text_input("Deal Name", placeholder="ISSUER 2025-X")
        manual_issuer = st.text_input("Issuer Name")
        manual_collateral = st.selectbox(
            "Collateral Type",
            ['Subprime Auto', 'Prime Auto', 'CLO', 'Consumer', 'Equipment', 'Credit Card', 'Esoteric']
        )
        manual_size = st.number_input("Total Size ($M)", min_value=0.0, value=100.0)

    with col2:
        manual_date = st.date_input("Pricing Date", value=datetime.now())
        manual_bookrunner = st.text_input("Bookrunner")
        manual_format = st.selectbox("Format", ['144A', 'Reg S', 'Reg AB', 'Private'])

    st.markdown("#### Tranches")

    # Simple tranche entry
    num_tranches = st.number_input("Number of Tranches", 1, 10, 3)

    manual_tranches = []
    cols = st.columns(5)
    cols[0].markdown("**Class**")
    cols[1].markdown("**Size ($M)**")
    cols[2].markdown("**Rating**")
    cols[3].markdown("**Spread (bps)**")
    cols[4].markdown("**WAL (yr)**")

    for i in range(int(num_tranches)):
        cols = st.columns(5)
        t_class = cols[0].text_input(f"Class {i+1}", value=['A', 'B', 'C', 'D', 'E'][min(i, 4)], key=f"t_class_{i}", label_visibility="collapsed")
        t_size = cols[1].number_input(f"Size {i+1}", value=50.0, key=f"t_size_{i}", label_visibility="collapsed")
        t_rating = cols[2].selectbox(f"Rating {i+1}", ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'NR'], key=f"t_rating_{i}", label_visibility="collapsed")
        t_spread = cols[3].number_input(f"Spread {i+1}", value=100 + i*100, key=f"t_spread_{i}", label_visibility="collapsed")
        t_wal = cols[4].number_input(f"WAL {i+1}", value=1.0 + i*0.5, key=f"t_wal_{i}", label_visibility="collapsed")

        manual_tranches.append({
            'tranche_class': t_class,
            'AMT_ISSUED': t_size * 1_000_000,
            'RTG_SP': t_rating,
            'SPREAD_TO_BENCHMARK': t_spread,
            'WAL_TO_MAT': t_wal
        })

    if st.button("Save Deal", type="primary"):
        if manual_deal_name and manual_issuer:
            # Store in session state
            manual_deal = {
                'deal_name': manual_deal_name,
                'issuer': manual_issuer,
                'collateral_type': manual_collateral,
                'total_size': manual_size,
                'issue_date': manual_date.strftime('%Y-%m-%d'),
                'bookrunner': manual_bookrunner,
                'tranches': manual_tranches
            }
            st.session_state['selected_deal'] = manual_deal
            st.success(f"Deal {manual_deal_name} saved. View in 'Deal Details' tab.")
        else:
            st.error("Deal name and issuer are required")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
if mcal and mcal.is_available():
    st.caption("Data Source: Bloomberg Terminal (MCAL)")
else:
    st.caption("Bloomberg Offline - Connect Bloomberg Terminal for live data")
