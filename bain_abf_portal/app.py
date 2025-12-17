"""
Bain Capital Credit - ABF/Structured Credit Analytics Portal
Main Application Entry Point (Rebuilt)
"""

import streamlit as st
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

st.set_page_config(
    page_title="ABF Analytics Portal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for clean styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        border-left: 4px solid #1E3A5F;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1rem;
        font-weight: 600;
    }
    /* Clean sidebar */
    .css-1d391kg {
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

st.sidebar.title("📊 ABF Portal")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["🏠 Home", "🎓 Deal Analyzer", "📈 Waterfall Modeler", "📉 Spread Monitor", "📰 Market Tracker"],
    index=0
)

st.sidebar.markdown("---")

# Quick links (only on home page)
if page == "🏠 Home":
    st.sidebar.markdown("### 🔗 Resources")
    st.sidebar.markdown("- [EDGAR ABS Filings](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=ABS-15G)")
    st.sidebar.markdown("- [FRED Economic Data](https://fred.stlouisfed.org/)")
    st.sidebar.markdown("- [Manheim Index](https://publish.manheim.com/en/services/consulting/used-vehicle-value-index.html)")
    st.sidebar.markdown("- [LCD CLO News](https://www.lcdcomps.com/)")

st.sidebar.markdown("---")
st.sidebar.caption("Built for Bain Capital Credit")
st.sidebar.caption("ABF/Structured Credit Initiatives")

# ============================================================================
# PAGE ROUTING
# ============================================================================

if page == "🏠 Home":
    # HOME PAGE
    st.markdown('<p class="main-header">ABF/Structured Credit Analytics Portal</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Interactive tools for analyzing Asset-Based Finance and Structured Credit products</p>', unsafe_allow_html=True)

    st.markdown("---")

    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total ABF Market", "$20T+", help="Total addressable ABF market")
    with col2:
        st.metric("Private ABF", "~$6T", help="Private ABF market size")
    with col3:
        st.metric("2024 Private ABS", "$130B", help="Private ABS issuance in 2024")
    with col4:
        st.metric("SOFR", "4.33%", help="Current SOFR rate (fetch live in Spread Monitor)")

    st.markdown("---")

    # Module descriptions
    st.markdown("### 🔧 Portal Modules")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        #### 🎓 Deal Analyzer
        **Educational ABS Explorer**
        - Interactive scenario sliders
        - See how CPR/CDR/severity affect returns
        - OC trigger visualization
        - Bond returns dashboard (MOIC, WAL)
        - Waterfall flow explanation
        - Perfect for learning how structures work
        """)

    with col2:
        st.markdown("""
        #### 📈 Waterfall Modeler
        **Advanced deal modeling**
        - Pre-built templates (Auto, CLO, Equipment)
        - Custom deal input or JSON paste
        - OC, IC, CNL, DSCR triggers
        - Break-even CDR by tranche
        """)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("""
        #### 📉 Spread Monitor
        **Track relative value**
        - Bloomberg/FRED market data
        - Corporate spread benchmarks (IG, HY)
        - Estimated ABS/CLO spreads
        - Historical trends
        """)

    with col4:
        st.markdown("""
        #### 📰 Market Tracker
        **Monitor new issuance**
        - Deal database
        - Filter by collateral, date, size
        - Issuance analytics
        - Export to CSV/Excel
        """)

    st.markdown("---")

    # ABF Collateral Overview
    st.markdown("### 📦 ABF Collateral Universe")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Consumer Assets**
        - Prime/Subprime Auto Loans
        - Credit Card Receivables
        - Personal Loans / BNPL
        - Student Loans (Private)

        **Commercial Assets**
        - Equipment Leases
        - Fleet/Vehicle Leases
        - Small Business Loans
        - Franchise Loans
        """)

    with col2:
        st.markdown("""
        **Hard Assets**
        - Aircraft (Leases/Loans)
        - Railcar / Shipping
        - Solar / PACE
        - Data Centers

        **Esoteric / Financial**
        - Music/Pharma Royalties
        - Litigation Finance
        - Sports Finance
        - Subscription/SaaS Revenue
        """)

    st.markdown("---")

    # Key concepts
    st.markdown("### 📚 Key Concepts")

    with st.expander("OC Test (Overcollateralization)"):
        st.markdown("""
        **Formula:** Collateral Value / Outstanding Notes

        **Purpose:** Ensures there's enough collateral to cover the debt.

        **Example:** If OC test is 110%, a $100M deal needs at least $110M of collateral.

        **When Breached:** Cash is trapped and redirected to pay down senior notes faster.
        """)

    with st.expander("IC Test (Interest Coverage)"):
        st.markdown("""
        **Formula:** Interest Income / Interest Expense

        **Purpose:** Ensures interest income covers interest payments on notes.

        **Example:** If IC test is 1.5x, need $1.50 of income for every $1.00 of interest due.

        **When Breached:** Similar to OC - cash redirected up the waterfall.
        """)

    with st.expander("CNL Trigger (Cumulative Net Loss)"):
        st.markdown("""
        **Formula:** (Cumulative Defaults - Recoveries) / Original Pool Balance

        **Purpose:** Caps total losses the deal can absorb before structural changes.

        **Example:** 20% CNL trigger means if losses hit 20% of original pool, trigger fires.

        **When Breached:** May switch from pro-rata to sequential pay, protecting seniors.
        """)

    with st.expander("Sequential vs. Pro-Rata Pay"):
        st.markdown("""
        **Sequential:** Senior tranches paid first, then mezz, then sub. Protects seniors.

        **Pro-Rata:** All tranches paid proportionally. Returns capital to all investors.

        **Typical Structure:** Pro-rata during normal times, switches to sequential when triggers breach.

        **Why It Matters:** Sequential pay extends WAL for junior tranches but protects senior holders.
        """)

elif page == "🎓 Deal Analyzer":
    # Import and run deal analyzer (educational tool)
    from pages.deal_analyzer import *

elif page == "📈 Waterfall Modeler":
    # Import and run waterfall modeler
    from pages.waterfall_modeler import *

elif page == "📉 Spread Monitor":
    # Import and run spread monitor
    from pages.spread_monitor import *

elif page == "📰 Market Tracker":
    # Import and run market tracker
    from pages.market_tracker import *
