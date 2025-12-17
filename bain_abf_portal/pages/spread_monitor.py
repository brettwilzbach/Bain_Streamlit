"""
Spread Monitor - Page 2 (Rebuilt)
Track relative value across structured credit vs. corporates

Data Sources:
- Bloomberg Terminal (via MCP) - Live data when available
- FRED API (fallback) - Free public data with spread estimates
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

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.data_fetcher import (
    FREDClient, SpreadEstimator, FRED_SERIES,
    get_current_sofr, get_treasury_curve, get_corporate_spreads,
    get_unified_provider
)

st.markdown('<p class="main-header">📉 Spread Monitor</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Track spreads across structured credit sectors and compare to corporate benchmarks</p>', unsafe_allow_html=True)

# ============================================================================
# SESSION STATE & DATA LOADING
# ============================================================================

@st.cache_resource
def get_provider():
    """Get unified data provider (cached)"""
    return get_unified_provider()


@st.cache_data(ttl=300)  # Cache for 5 min (shorter for Bloomberg live data)
def load_market_data(_provider):
    """Load market data from Bloomberg (if available) or FRED"""
    fred = FREDClient()
    estimator = SpreadEstimator(fred)

    data = {
        'sofr': None,
        'treasury_curve': {},
        'corporate_spreads': {},
        'abs_spreads': {},
        'spread_history': {},
        'clo_spreads': {},
        'credit_indices': {},
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'source': 'FRED (Estimated)',
        'is_live': False
    }

    # Check Bloomberg first
    if _provider.bloomberg_available:
        data['source'] = 'Bloomberg Terminal (Live)'
        data['is_live'] = True

        # Get live CLO spreads from Palmer Square
        clo_spreads, clo_source = _provider.get_clo_spreads()
        if clo_spreads:
            data['clo_spreads'] = clo_spreads

        # Get CDX/LCDX
        indices, idx_source = _provider.get_credit_indices()
        if indices:
            data['credit_indices'] = indices

        # Get SOFR
        sofr_val, sofr_source = _provider.get_sofr()
        if sofr_val:
            data['sofr'] = sofr_val

    # Always get FRED data (for fallback and corporate benchmarks)
    try:
        if not data['sofr']:
            data['sofr'] = get_current_sofr()

        data['treasury_curve'] = get_treasury_curve()
        data['corporate_spreads'] = get_corporate_spreads()
        data['abs_spreads'] = estimator.get_all_spreads()

        # Get historical data for key series
        for series_name in ['IG_SPREAD', 'HY_SPREAD', 'BBB_SPREAD']:
            df = fred.get_series(FRED_SERIES.get(series_name, ''), limit=365)
            if not df.empty:
                data['spread_history'][series_name] = df

    except Exception as e:
        st.warning(f"Could not fetch data: {e}")

    return data


# Get provider and load data
provider = get_provider()
with st.spinner(f"Loading market data..."):
    market_data = load_market_data(provider)

# ============================================================================
# SIDEBAR - CONTROLS
# ============================================================================

st.sidebar.markdown("### 📊 Spread Monitor")

# Data source status - prominent display
if market_data['is_live']:
    st.sidebar.success("🟢 Bloomberg Terminal Connected")
    st.sidebar.caption(f"Live data as of {market_data['last_updated']}")
elif market_data['sofr']:
    st.sidebar.info("🔵 FRED API Connected")
    st.sidebar.caption(f"Updated: {market_data['last_updated']}")
    st.sidebar.caption("ABS/CLO spreads are estimated")
else:
    st.sidebar.warning("⚠️ Using sample data")
    st.sidebar.caption("API connections unavailable")

st.sidebar.markdown("---")

# Bloomberg connection settings (expandable)
with st.sidebar.expander("Bloomberg Terminal Settings"):
    bbg_host = st.text_input("Host", value="localhost")
    bbg_port = st.number_input("Port", value=8194, min_value=1, max_value=65535)
    st.caption("Requires Bloomberg Terminal running with BBComm enabled")
    st.caption("Connects directly via blpapi (no server needed)")

    if st.button("Test Connection"):
        test_provider = get_unified_provider(bbg_host, int(bbg_port))
        if test_provider.bloomberg_available:
            st.success("Bloomberg Terminal connected!")
        else:
            st.error("Connection failed - make sure Bloomberg Terminal is running")

st.sidebar.markdown("---")

# Sector filter
all_sectors = list(market_data['abs_spreads'].keys()) if market_data['abs_spreads'] else [
    'CLO AAA', 'CLO AA', 'CLO A', 'CLO BBB', 'CLO BB',
    'Prime Auto AAA', 'Prime Auto AA', 'Prime Auto A',
    'Subprime Auto AAA', 'Subprime Auto AA', 'Subprime Auto A', 'Subprime Auto BBB',
    'Consumer ABS AAA', 'Consumer ABS A',
    'Equipment ABS AAA', 'Equipment ABS A'
]

sector_groups = {
    'CLO': [s for s in all_sectors if 'CLO' in s],
    'Prime Auto': [s for s in all_sectors if 'Prime Auto' in s],
    'Subprime Auto': [s for s in all_sectors if 'Subprime Auto' in s],
    'Consumer': [s for s in all_sectors if 'Consumer' in s],
    'Equipment': [s for s in all_sectors if 'Equipment' in s],
}

selected_groups = st.sidebar.multiselect(
    "Select Sectors",
    list(sector_groups.keys()),
    default=['CLO', 'Subprime Auto']
)

# Flatten selected sectors
selected_sectors = []
for group in selected_groups:
    selected_sectors.extend(sector_groups.get(group, []))

# Time range
time_range = st.sidebar.selectbox(
    "Time Range",
    ['1M', '3M', '6M', 'YTD', '1Y'],
    index=4
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Data Sources")

if market_data['is_live']:
    st.sidebar.markdown("""
    **Bloomberg (Live):**
    - SOFR, Treasuries
    - CDX IG/HY, LCDX
    - CLO spreads (Palmer Square)
    - ABS new issue pricing
    """)
else:
    st.sidebar.markdown("""
    **FRED API:**
    - SOFR, Treasuries
    - Corporate OAS (ICE BofA)

    **Estimated:**
    - ABS/CLO spreads (benchmark + premium)

    *Connect Bloomberg for live ABS data*
    """)

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# ============================================================================
# MAIN CONTENT
# ============================================================================

# Summary metrics
col1, col2, col3, col4, col5 = st.columns(5)

sofr_val = market_data.get('sofr') or 4.33
ig_spread = market_data.get('corporate_spreads', {}).get('IG_SPREAD', 90)
hy_spread = market_data.get('corporate_spreads', {}).get('HY_SPREAD', 350)
bbb_spread = market_data.get('corporate_spreads', {}).get('BBB_SPREAD', 150)

with col1:
    st.metric("SOFR", f"{sofr_val:.2f}%")
with col2:
    st.metric("IG Corps OAS", f"{ig_spread:.0f}bps")
with col3:
    st.metric("HY Corps OAS", f"{hy_spread:.0f}bps")
with col4:
    st.metric("BBB Corps OAS", f"{bbb_spread:.0f}bps")
with col5:
    curve = market_data.get('treasury_curve', {})
    ust_5y = curve.get('5Y', 4.0)
    st.metric("5Y Treasury", f"{ust_5y:.2f}%")

st.markdown("---")

# Show Bloomberg-specific data when connected
if market_data['is_live']:
    st.markdown("### Bloomberg Live Data")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Credit Indices")
        if market_data['credit_indices']:
            for name, value in market_data['credit_indices'].items():
                if value is not None:
                    st.metric(name, f"{value:.0f}bps" if value > 10 else f"{value:.2f}")
        else:
            st.caption("CDX/LCDX data unavailable")

    with col2:
        st.markdown("#### CLO Spreads (Palmer Square)")
        if market_data['clo_spreads']:
            for name, value in market_data['clo_spreads'].items():
                if value is not None:
                    st.metric(name.replace('CLO ', ''), f"{value:.0f}bps")
        else:
            st.caption("CLO index data unavailable")

    st.markdown("---")

# ============================================================================
# TABS
# ============================================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Current Spreads",
    "📈 Historical Trends",
    "🔄 Relative Value",
    "📉 Z-Score Analysis"
])

# ============================================================================
# TAB 1: CURRENT SPREADS
# ============================================================================

with tab1:
    st.markdown("### Current Spread Levels")

    if not market_data['abs_spreads']:
        st.warning("No spread data available. Check FRED API connection.")
    else:
        # Filter to selected sectors
        filtered_spreads = {k: v for k, v in market_data['abs_spreads'].items()
                          if k in selected_sectors or not selected_sectors}

        # Build table
        spread_table = []
        for name, data in filtered_spreads.items():
            pickup = data.current_spread - bbb_spread if 'BBB' in name else data.current_spread - ig_spread
            spread_table.append({
                'Sector': name,
                'Spread (bps)': f"{data.current_spread:.0f}",
                'Benchmark': data.benchmark,
                'vs. IG Corp': f"+{data.current_spread - ig_spread:.0f}",
                'YTD Change': f"{data.ytd_change:+.0f}",
                'Z-Score': f"{data.z_score:.2f}",
                '1Y Range': f"{data.one_year_min:.0f} - {data.one_year_max:.0f}"
            })

        spread_df = pd.DataFrame(spread_table)
        st.dataframe(spread_df, use_container_width=True, hide_index=True)

        # Visualization
        col1, col2 = st.columns(2)

        with col1:
            # Bar chart of current spreads
            fig = go.Figure()

            sectors = [s['Sector'] for s in spread_table]
            spreads = [float(s['Spread (bps)']) for s in spread_table]

            # Color by rating implied by name
            colors = []
            for s in sectors:
                if 'AAA' in s:
                    colors.append('#1E3A5F')
                elif 'AA' in s:
                    colors.append('#2E5A8F')
                elif 'A' in s and 'AAA' not in s and 'AA' not in s:
                    colors.append('#4A7AB0')
                elif 'BBB' in s:
                    colors.append('#FF9800')
                elif 'BB' in s:
                    colors.append('#C62828')
                else:
                    colors.append('#666666')

            fig.add_trace(go.Bar(
                x=sectors,
                y=spreads,
                marker_color=colors
            ))

            # Add IG Corp line
            fig.add_hline(y=ig_spread, line_dash="dash", line_color="gray",
                         annotation_text=f"IG Corps: {ig_spread:.0f}bps")

            fig.update_layout(
                title="Current Spreads by Sector",
                yaxis_title="Spread (bps)",
                height=400,
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Spread pickup over corporates
            fig = go.Figure()

            pickups = [float(s['vs. IG Corp'].replace('+', '')) for s in spread_table]

            fig.add_trace(go.Bar(
                x=sectors,
                y=pickups,
                marker_color=['#2E7D32' if p > 50 else '#1976D2' for p in pickups]
            ))

            fig.add_hline(y=50, line_dash="dash", line_color="orange",
                         annotation_text="50bps pickup threshold")
            fig.add_hline(y=100, line_dash="dash", line_color="green",
                         annotation_text="100bps pickup")

            fig.update_layout(
                title="Spread Pickup vs. IG Corporates",
                yaxis_title="Pickup (bps)",
                height=400,
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 2: HISTORICAL TRENDS
# ============================================================================

with tab2:
    st.markdown("### Historical Spread Trends")

    # Corporate spread history (real data from FRED)
    st.markdown("#### Corporate Benchmark Spreads (FRED Data)")

    if market_data['spread_history']:
        fig = go.Figure()

        colors = {'IG_SPREAD': '#1E3A5F', 'HY_SPREAD': '#C62828', 'BBB_SPREAD': '#FF9800'}
        names = {'IG_SPREAD': 'IG Corps', 'HY_SPREAD': 'HY Corps', 'BBB_SPREAD': 'BBB Corps'}

        for series_name, df in market_data['spread_history'].items():
            if not df.empty:
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['value'],
                    name=names.get(series_name, series_name),
                    line=dict(color=colors.get(series_name, '#666666'), width=2)
                ))

        fig.update_layout(
            title="Corporate OAS Spreads (1 Year)",
            xaxis_title="Date",
            yaxis_title="OAS (bps)",
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Historical data not available. Check FRED API connection.")

    # Estimated ABS/CLO spreads
    st.markdown("#### Estimated Structured Credit Spreads")
    st.caption("Based on corporate benchmarks + historical spread premiums")

    # Allow user to select sectors to chart
    sectors_to_chart = st.multiselect(
        "Select sectors to compare",
        selected_sectors,
        default=selected_sectors[:3] if len(selected_sectors) >= 3 else selected_sectors
    )

    if sectors_to_chart and market_data['abs_spreads']:
        estimator = SpreadEstimator(FREDClient())

        fig = go.Figure()

        for sector in sectors_to_chart:
            history = estimator.get_spread_history(sector, days=365)
            if not history.empty:
                fig.add_trace(go.Scatter(
                    x=history.index,
                    y=history['estimated_spread'],
                    name=sector,
                    mode='lines'
                ))

        fig.update_layout(
            title="Estimated Spread History (1 Year)",
            xaxis_title="Date",
            yaxis_title="Spread (bps)",
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

    # Statistics table
    st.markdown("#### Period Statistics")

    if market_data['abs_spreads']:
        stats_data = []
        for name, data in market_data['abs_spreads'].items():
            if name in selected_sectors or not selected_sectors:
                stats_data.append({
                    'Sector': name,
                    'Current': f"{data.current_spread:.0f}",
                    '1Y Avg': f"{data.one_year_avg:.0f}",
                    '1Y Min': f"{data.one_year_min:.0f}",
                    '1Y Max': f"{data.one_year_max:.0f}",
                    'YTD Chg': f"{data.ytd_change:+.0f}",
                    'vs Avg': f"{data.current_spread - data.one_year_avg:+.0f}"
                })

        st.dataframe(pd.DataFrame(stats_data), use_container_width=True, hide_index=True)

# ============================================================================
# TAB 3: RELATIVE VALUE
# ============================================================================

with tab3:
    st.markdown("### Relative Value Analysis")

    if not market_data['abs_spreads']:
        st.warning("No spread data available")
    else:
        # Spread pickup analysis
        st.markdown("#### Spread Pickup vs. Benchmarks")

        # Create comparison matrix
        ratings = ['AAA', 'AA', 'A', 'BBB', 'BB']
        sectors_display = ['CLO', 'Prime Auto', 'Subprime Auto', 'Consumer', 'Equipment']

        matrix_data = []
        for rating in ratings:
            row = {'Rating': rating}
            for sector in sectors_display:
                key = f"{sector} {rating}" if sector != 'Consumer' else f"Consumer ABS {rating}"
                if sector == 'Equipment':
                    key = f"Equipment ABS {rating}"
                if sector == 'Prime Auto':
                    key = f"Prime Auto {rating}"
                if sector == 'Subprime Auto':
                    key = f"Subprime Auto {rating}"

                spread_data = market_data['abs_spreads'].get(key)
                if spread_data:
                    row[sector] = spread_data.current_spread
                else:
                    row[sector] = np.nan
            matrix_data.append(row)

        matrix_df = pd.DataFrame(matrix_data)
        matrix_df.set_index('Rating', inplace=True)

        # Heatmap
        fig = px.imshow(
            matrix_df.values,
            labels=dict(x="Sector", y="Rating", color="Spread (bps)"),
            x=matrix_df.columns,
            y=matrix_df.index,
            color_continuous_scale='RdYlGn_r',
            aspect="auto",
            text_auto='.0f'
        )

        fig.update_layout(
            title="Spread Matrix: Sector × Rating",
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)

        # Relative value scorecard
        st.markdown("---")
        st.markdown("#### Relative Value Scorecard")

        scorecard_data = []
        for name, data in market_data['abs_spreads'].items():
            if name in selected_sectors or not selected_sectors:
                # Calculate RV score
                # Higher pickup, negative z-score = more attractive
                pickup = data.current_spread - ig_spread
                z = data.z_score

                # Simple scoring
                score = (pickup / 100) * 0.5 + (-z) * 0.3 + (-data.ytd_change / 50) * 0.2

                if score > 1.0:
                    assessment = "🟢 Attractive"
                elif score > 0.5:
                    assessment = "🟡 Fair"
                elif score > 0:
                    assessment = "🟠 Neutral"
                else:
                    assessment = "🔴 Rich"

                scorecard_data.append({
                    'Sector': name,
                    'Spread': f"{data.current_spread:.0f}bps",
                    'Pickup': f"+{pickup:.0f}bps",
                    'Z-Score': f"{z:.2f}",
                    'YTD': f"{data.ytd_change:+.0f}",
                    'RV Score': f"{score:.2f}",
                    'Assessment': assessment
                })

        scorecard_df = pd.DataFrame(scorecard_data)
        scorecard_df = scorecard_df.sort_values('RV Score', key=lambda x: pd.to_numeric(x), ascending=False)

        st.dataframe(scorecard_df, use_container_width=True, hide_index=True)

        # Key takeaways
        st.markdown("---")
        st.markdown("#### Key Observations")

        attractive = [s for s in scorecard_data if '🟢' in s['Assessment']]
        rich = [s for s in scorecard_data if '🔴' in s['Assessment']]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Most Attractive:**")
            if attractive:
                for s in attractive[:3]:
                    st.markdown(f"- {s['Sector']}: {s['Spread']}, Z={s['Z-Score']}")
            else:
                st.markdown("*No sectors showing strong value*")

        with col2:
            st.markdown("**Least Attractive:**")
            if rich:
                for s in rich[:3]:
                    st.markdown(f"- {s['Sector']}: {s['Spread']}, Z={s['Z-Score']}")
            else:
                st.markdown("*No sectors showing rich valuations*")

# ============================================================================
# TAB 4: Z-SCORE ANALYSIS
# ============================================================================

with tab4:
    st.markdown("### Z-Score Analysis")
    st.markdown("Current spreads relative to 1-year average")

    if not market_data['abs_spreads']:
        st.warning("No spread data available")
    else:
        # Z-score bar chart
        z_data = []
        for name, data in market_data['abs_spreads'].items():
            if name in selected_sectors or not selected_sectors:
                z_data.append({'Sector': name, 'Z-Score': data.z_score})

        z_df = pd.DataFrame(z_data)
        z_df = z_df.sort_values('Z-Score')

        fig = go.Figure()

        colors = ['#C62828' if z < 0 else '#2E7D32' for z in z_df['Z-Score']]

        fig.add_trace(go.Bar(
            x=z_df['Z-Score'],
            y=z_df['Sector'],
            orientation='h',
            marker_color=colors
        ))

        fig.add_vline(x=0, line_color="black", line_width=2)
        fig.add_vline(x=-1, line_dash="dash", line_color="gray",
                     annotation_text="-1σ (Tight)")
        fig.add_vline(x=1, line_dash="dash", line_color="gray",
                     annotation_text="+1σ (Wide)")

        fig.update_layout(
            title="Z-Scores: Current vs. 1-Year Average",
            xaxis_title="Z-Score",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

        # Interpretation
        st.markdown("---")
        st.markdown("#### How to Read Z-Scores")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**🟢 Attractive (Z > 0.5)**")
            st.caption("Spreads wider than average")
            wide = [name for name, data in market_data['abs_spreads'].items()
                   if data.z_score > 0.5 and (name in selected_sectors or not selected_sectors)]
            if wide:
                for s in wide:
                    z = market_data['abs_spreads'][s].z_score
                    st.markdown(f"- {s} (Z={z:.2f})")
            else:
                st.markdown("*None*")

        with col2:
            st.markdown("**🟡 Fair (-0.5 < Z < 0.5)**")
            st.caption("Near historical average")
            fair = [name for name, data in market_data['abs_spreads'].items()
                   if -0.5 <= data.z_score <= 0.5 and (name in selected_sectors or not selected_sectors)]
            if fair:
                for s in fair[:5]:
                    z = market_data['abs_spreads'][s].z_score
                    st.markdown(f"- {s} (Z={z:.2f})")
            else:
                st.markdown("*None*")

        with col3:
            st.markdown("**🔴 Rich (Z < -0.5)**")
            st.caption("Spreads tighter than average")
            tight = [name for name, data in market_data['abs_spreads'].items()
                    if data.z_score < -0.5 and (name in selected_sectors or not selected_sectors)]
            if tight:
                for s in tight:
                    z = market_data['abs_spreads'][s].z_score
                    st.markdown(f"- {s} (Z={z:.2f})")
            else:
                st.markdown("*None*")

        # Caveat
        with st.expander("⚠️ Important Caveats"):
            st.markdown("""
            **Z-Score Limitations:**

            1. **Lookback Period**: 1-year window may miss longer cycles
            2. **Fundamentals**: Z-scores don't capture credit quality changes
            3. **Estimated Data**: ABS/CLO spreads are estimated from corporate benchmarks
            4. **Premium Assumptions**: Spread premiums are based on historical relationships

            **For Better Analysis:**
            - Integrate Bloomberg/LCD for live ABS pricing
            - Combine with fundamental credit metrics (delinquencies, CNL)
            - Consider technicals (supply/demand, fund flows)
            """)
