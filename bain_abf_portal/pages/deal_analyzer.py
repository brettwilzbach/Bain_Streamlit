"""
Deal Analyzer - Interactive ABS Waterfall Explorer
Educational tool for understanding how ABS structures respond to different scenarios

Designed for marketing and product manager types to get a real flavor
for what goes on during the investment process.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from dataclasses import dataclass
from typing import List, Dict, Tuple
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

st.markdown('<p class="main-header">Deal Analyzer</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Interactive tool to understand how ABS structures work</p>', unsafe_allow_html=True)

# ============================================================================
# SIMPLIFIED WATERFALL MODEL
# ============================================================================

@dataclass
class SimpleTranche:
    """Simple tranche representation"""
    name: str
    original_balance: float
    coupon: float  # Annual rate
    oc_target: float  # OC test target (e.g., 1.05 = 105%)
    is_equity: bool = False

@dataclass
class SimplePool:
    """Simple collateral pool"""
    balance: float
    wac: float  # Weighted average coupon
    wam: int  # Weighted average maturity (months)

def run_simple_waterfall(
    pool: SimplePool,
    tranches: List[SimpleTranche],
    cpr: float,
    cdr: float,
    severity: float,
    sofr: float = 0.0433
) -> Tuple[pd.DataFrame, Dict]:
    """
    Run a simplified waterfall projection.
    Returns monthly cash flows and bond metrics.
    """
    months = pool.wam

    # Initialize tracking
    pool_balance = pool.balance
    tranche_balances = {t.name: t.original_balance for t in tranches}

    # Results storage
    results = []
    cumulative_losses = 0
    cumulative_principal = 0

    # Monthly factors
    smm = 1 - (1 - cpr) ** (1/12)  # Single monthly mortality (prepay)
    mdr = 1 - (1 - cdr) ** (1/12)  # Monthly default rate

    for month in range(1, months + 1):
        if pool_balance <= 0:
            break

        # === ASSET SIDE: Generate Cash ===

        # Interest from pool
        interest_income = pool_balance * (pool.wac / 12)

        # Scheduled principal (simplified - assume level amort)
        scheduled_prin = pool.balance / pool.wam

        # Prepayments
        prepayments = (pool_balance - scheduled_prin) * smm

        # Defaults
        defaults = pool_balance * mdr
        recoveries = defaults * (1 - severity)
        losses = defaults - recoveries

        # Update pool balance
        principal_collected = scheduled_prin + prepayments + recoveries
        pool_balance = max(0, pool_balance - scheduled_prin - prepayments - defaults)

        cumulative_losses += losses
        cumulative_principal += principal_collected

        # CNL
        cnl = (cumulative_losses / pool.balance) * 100

        # === LIABILITY SIDE: Pay the Waterfall ===

        available_interest = interest_income
        available_principal = principal_collected

        # Calculate total debt and OC ratio
        total_debt = sum(tranche_balances[t.name] for t in tranches if not t.is_equity)
        oc_ratio = pool_balance / total_debt if total_debt > 0 else float('inf')

        # Track OC test results for each tranche
        oc_tests = {}
        tranche_results = {}

        # Pay tranches in order (senior to junior)
        for t in tranches:
            if t.is_equity:
                continue

            bal = tranche_balances[t.name]
            if bal <= 0:
                tranche_results[t.name] = {'interest': 0, 'principal': 0}
                oc_tests[t.name] = True
                continue

            # Interest payment
            coupon_rate = t.coupon + sofr if t.coupon < 0.05 else t.coupon  # Floating vs fixed
            interest_due = bal * (coupon_rate / 12)
            interest_paid = min(interest_due, available_interest)
            available_interest -= interest_paid

            # Calculate subordination below this tranche
            junior_debt = sum(tranche_balances[t2.name] for t2 in tranches
                            if tranches.index(t2) > tranches.index(t) and not t2.is_equity)
            debt_at_or_above = total_debt - junior_debt
            tranche_oc = pool_balance / debt_at_or_above if debt_at_or_above > 0 else float('inf')

            # OC test
            oc_pass = tranche_oc >= t.oc_target
            oc_tests[t.name] = oc_pass

            # Principal payment
            principal_paid = 0
            if oc_pass:
                # Normal sequential pay
                principal_paid = min(bal, available_principal)
                available_principal -= principal_paid
            else:
                # OC fail - turbo pay seniors (redirect cash)
                principal_paid = min(bal, available_principal + available_interest * 0.5)
                available_principal = max(0, available_principal - principal_paid)
                available_interest = max(0, available_interest - max(0, principal_paid - available_principal))

            tranche_balances[t.name] = max(0, bal - principal_paid)
            tranche_results[t.name] = {
                'interest': interest_paid,
                'principal': principal_paid,
                'oc_ratio': tranche_oc,
                'oc_pass': oc_pass
            }

        # Equity gets residual
        equity_tranche = next((t for t in tranches if t.is_equity), None)
        if equity_tranche:
            residual = available_interest + available_principal
            tranche_results[equity_tranche.name] = {
                'interest': residual,
                'principal': 0,
                'oc_ratio': 0,
                'oc_pass': True
            }

        # Store results
        results.append({
            'Month': month,
            'Pool_Balance': pool_balance,
            'Interest_Income': interest_income,
            'Principal': principal_collected,
            'Prepayments': prepayments,
            'Defaults': defaults,
            'Losses': losses,
            'CNL': cnl,
            'OC_Ratio': oc_ratio * 100,
            **{f'{t.name}_Balance': tranche_balances[t.name] for t in tranches},
            **{f'{t.name}_Interest': tranche_results.get(t.name, {}).get('interest', 0) for t in tranches},
            **{f'{t.name}_Principal': tranche_results.get(t.name, {}).get('principal', 0) for t in tranches},
            **{f'{t.name}_OC_Pass': tranche_results.get(t.name, {}).get('oc_pass', True) for t in tranches},
        })

    df = pd.DataFrame(results)

    # Calculate bond metrics
    metrics = {}
    for t in tranches:
        bal = t.original_balance
        cf_interest = df[f'{t.name}_Interest'].sum()
        cf_principal = df[f'{t.name}_Principal'].sum() if not t.is_equity else 0
        final_balance = df[f'{t.name}_Balance'].iloc[-1] if len(df) > 0 else bal

        # Total cash received
        total_cash = cf_interest + cf_principal

        # Principal loss
        prin_loss = max(0, bal - cf_principal) if not t.is_equity else 0

        # MOIC (Multiple on Invested Capital)
        moic = total_cash / bal if bal > 0 else 0

        # WAL (Weighted Average Life)
        if not t.is_equity:
            wal_num = sum(df['Month'] * df[f'{t.name}_Principal'])
            wal_den = df[f'{t.name}_Principal'].sum()
            wal = wal_num / wal_den / 12 if wal_den > 0 else 0
        else:
            wal = 0

        # Simple yield estimate (annualized)
        avg_life = wal if wal > 0 else pool.wam / 12 / 2
        simple_yield = ((moic - 1) / avg_life) if avg_life > 0 else 0

        # OC fail count
        oc_fail_months = len(df[df[f'{t.name}_OC_Pass'] == False]) if f'{t.name}_OC_Pass' in df.columns else 0

        metrics[t.name] = {
            'Original_Balance': bal,
            'Total_Interest': cf_interest,
            'Total_Principal': cf_principal,
            'Final_Balance': final_balance,
            'Principal_Loss': prin_loss,
            'MOIC': moic,
            'WAL': wal,
            'Simple_Yield': simple_yield,
            'OC_Fail_Months': oc_fail_months
        }

    # Pool CNL
    metrics['Pool'] = {
        'Final_CNL': df['CNL'].iloc[-1] if len(df) > 0 else 0,
        'Total_Losses': cumulative_losses,
        'Final_Balance': df['Pool_Balance'].iloc[-1] if len(df) > 0 else pool.balance
    }

    return df, metrics

# ============================================================================
# DEFAULT DEAL STRUCTURE (matching Excel model)
# ============================================================================

DEFAULT_POOL = SimplePool(
    balance=100_000_000,  # $100M
    wac=0.08,  # 8%
    wam=60  # 60 months
)

DEFAULT_TRANCHES = [
    SimpleTranche("Class A", 80_000_000, 0.05, 1.00),   # 80%, 5% coupon, 100% OC
    SimpleTranche("Class B", 12_000_000, 0.07, 1.05),   # 12%, 7% coupon, 105% OC
    SimpleTranche("Class C", 5_000_000, 0.10, 1.15),    # 5%, 10% coupon, 115% OC
    SimpleTranche("Equity", 3_000_000, 0.0, 1.0, is_equity=True),  # 3% equity
]

# ============================================================================
# SIDEBAR - SCENARIO CONTROLS
# ============================================================================

st.sidebar.markdown("### Scenario Controls")
st.sidebar.markdown("Adjust these inputs to see how the structure responds")

st.sidebar.markdown("---")
st.sidebar.markdown("#### Performance Assumptions")

cpr = st.sidebar.slider(
    "CPR (Prepayment Speed)",
    min_value=0.0, max_value=40.0, value=10.0, step=1.0,
    help="Conditional Prepayment Rate - how fast borrowers pay off early"
) / 100

cdr = st.sidebar.slider(
    "CDR (Default Rate)",
    min_value=0.0, max_value=15.0, value=2.0, step=0.5,
    help="Conditional Default Rate - annual rate of defaults"
) / 100

severity = st.sidebar.slider(
    "Loss Severity",
    min_value=20.0, max_value=100.0, value=80.0, step=5.0,
    help="Loss given default - what % of defaulted balance is lost"
) / 100

st.sidebar.markdown("---")
st.sidebar.markdown("#### Market Rate")

sofr = st.sidebar.slider(
    "SOFR Rate",
    min_value=0.0, max_value=8.0, value=4.33, step=0.25,
    help="Reference rate for floating coupons"
) / 100

st.sidebar.markdown("---")

# Quick scenario buttons
st.sidebar.markdown("#### Quick Scenarios")
col1, col2 = st.sidebar.columns(2)

if col1.button("Base Case", use_container_width=True):
    st.session_state.cpr = 10.0
    st.session_state.cdr = 2.0
    st.session_state.severity = 80.0
    st.rerun()

if col2.button("Stress", use_container_width=True):
    st.session_state.cpr = 5.0
    st.session_state.cdr = 8.0
    st.session_state.severity = 90.0
    st.rerun()

# ============================================================================
# RUN MODEL
# ============================================================================

df, metrics = run_simple_waterfall(
    pool=DEFAULT_POOL,
    tranches=DEFAULT_TRANCHES,
    cpr=cpr,
    cdr=cdr,
    severity=severity,
    sofr=sofr
)

# ============================================================================
# MAIN CONTENT - EDUCATIONAL LAYOUT
# ============================================================================

# Overview section
st.markdown("### How This Deal Works")

with st.expander("The Basics (click to expand)", expanded=False):
    st.markdown("""
    **What is this?**

    This is a simplified ABS (Asset-Backed Security) structure. Think of it like this:

    1. **The Pool** - A collection of loans (like auto loans) worth $100M
    2. **The Tranches** - Different slices of risk/return sold to investors
    3. **The Waterfall** - Rules for how cash flows from the loans get distributed

    **Who gets paid first?**

    Senior tranches (Class A) get paid before junior tranches (Class B, C).
    The Equity tranche only gets paid after everyone else - but they keep any excess profit.

    **What are the triggers?**

    OC (Overcollateralization) tests check if there's enough collateral supporting each tranche.
    If a test fails, cash gets redirected to pay down senior tranches faster.
    """)

st.markdown("---")

# Key metrics at a glance
st.markdown("### Scenario Results")

col1, col2, col3, col4 = st.columns(4)

pool_cnl = metrics['Pool']['Final_CNL']
total_losses = metrics['Pool']['Total_Losses']

with col1:
    st.metric(
        "Pool CNL",
        f"{pool_cnl:.1f}%",
        delta=f"vs 5% trigger" if pool_cnl < 5 else None,
        delta_color="normal" if pool_cnl < 5 else "off"
    )

with col2:
    st.metric(
        "Total Losses",
        f"${total_losses/1_000_000:.2f}M",
        help="Cumulative losses from defaults"
    )

equity_moic = metrics['Equity']['MOIC']
with col3:
    st.metric(
        "Equity Return",
        f"{equity_moic:.2f}x",
        delta=f"{(equity_moic-1)*100:.0f}% profit" if equity_moic > 1 else f"{(equity_moic-1)*100:.0f}%",
        delta_color="normal" if equity_moic >= 1 else "inverse"
    )

# Check if any tranche has losses
any_losses = any(metrics[t.name]['Principal_Loss'] > 0 for t in DEFAULT_TRANCHES if not t.is_equity)
with col4:
    if any_losses:
        st.metric("Bond Losses", "YES", delta="Tranches impaired", delta_color="inverse")
    else:
        st.metric("Bond Losses", "NO", delta="All tranches whole", delta_color="normal")

st.markdown("---")

# ============================================================================
# TABS FOR DETAILED VIEW
# ============================================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "Bond Returns",
    "Waterfall Flow",
    "OC Tests",
    "Cash Flows"
])

# TAB 1: Bond Returns
with tab1:
    st.markdown("### Tranche Performance Summary")
    st.caption("How each tranche performed under this scenario")

    # Build summary table
    summary_data = []
    for t in DEFAULT_TRANCHES:
        m = metrics[t.name]

        if t.is_equity:
            summary_data.append({
                'Tranche': t.name,
                'Original ($M)': f"${t.original_balance/1_000_000:.1f}",
                'Coupon': 'Residual',
                'Total Cash ($M)': f"${m['Total_Interest']/1_000_000:.2f}",
                'MOIC': f"{m['MOIC']:.2f}x",
                'Est. Yield': f"{m['Simple_Yield']*100:.1f}%" if m['Simple_Yield'] > 0 else 'N/A',
                'Loss': '-'
            })
        else:
            coupon_display = f"{(t.coupon + sofr)*100:.2f}%" if t.coupon < 0.05 else f"{t.coupon*100:.1f}%"
            summary_data.append({
                'Tranche': t.name,
                'Original ($M)': f"${t.original_balance/1_000_000:.1f}",
                'Coupon': coupon_display,
                'Total Cash ($M)': f"${(m['Total_Interest'] + m['Total_Principal'])/1_000_000:.2f}",
                'MOIC': f"{m['MOIC']:.2f}x",
                'Est. Yield': f"{m['Simple_Yield']*100:.1f}%",
                'Loss': f"${m['Principal_Loss']/1_000_000:.2f}M" if m['Principal_Loss'] > 0 else '-'
            })

    st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

    # Visual comparison
    st.markdown("#### Return Comparison")

    moic_values = [metrics[t.name]['MOIC'] for t in DEFAULT_TRANCHES]
    tranche_names = [t.name for t in DEFAULT_TRANCHES]
    colors = ['#1E3A5F', '#2E5A8F', '#4A7AB0', '#8BC34A']

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=tranche_names,
        y=moic_values,
        marker_color=colors,
        text=[f"{v:.2f}x" for v in moic_values],
        textposition='outside'
    ))

    fig.add_hline(y=1.0, line_dash="dash", line_color="red",
                  annotation_text="1.0x (Break-even)")

    fig.update_layout(
        title="MOIC by Tranche",
        yaxis_title="Multiple on Invested Capital",
        height=350,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

    # Explain the results
    st.markdown("#### What This Means")

    if pool_cnl < 3:
        st.success(f"""
        **Healthy Scenario**: With only {pool_cnl:.1f}% cumulative losses, all tranches
        are performing well. The equity tranche earns {(equity_moic-1)*100:.0f}% return
        from excess spread.
        """)
    elif pool_cnl < 8:
        st.warning(f"""
        **Moderate Stress**: Losses of {pool_cnl:.1f}% are elevated but still within
        the structure's capacity. Credit enhancement is being consumed.
        """)
    else:
        st.error(f"""
        **High Stress**: Losses of {pool_cnl:.1f}% are severe.
        {"Rated tranches are experiencing principal loss." if any_losses else "The equity cushion is largely wiped out."}
        """)

# TAB 2: Waterfall Flow
with tab2:
    st.markdown("### The Waterfall")
    st.caption("How cash flows from top to bottom each month")

    # Visual waterfall
    st.markdown("#### Payment Priority (Senior to Junior)")

    # Create waterfall diagram
    fig = go.Figure()

    total_interest = sum(metrics[t.name]['Total_Interest'] for t in DEFAULT_TRANCHES)

    y_pos = 4
    for i, t in enumerate(DEFAULT_TRANCHES):
        m = metrics[t.name]
        width = m['Total_Interest'] / total_interest * 0.8 if total_interest > 0 else 0.1

        color = colors[i]

        fig.add_trace(go.Bar(
            y=[t.name],
            x=[m['Total_Interest']/1_000_000],
            orientation='h',
            marker_color=color,
            text=f"${m['Total_Interest']/1_000_000:.2f}M",
            textposition='inside',
            name=t.name
        ))

    fig.update_layout(
        title="Total Interest Received by Tranche ($M)",
        xaxis_title="Interest ($M)",
        height=300,
        showlegend=False,
        barmode='stack'
    )
    st.plotly_chart(fig, use_container_width=True)

    # Credit enhancement visual
    st.markdown("#### Credit Enhancement Structure")

    ce_data = []
    running_ce = 0
    for t in reversed(DEFAULT_TRANCHES):
        if t.is_equity:
            ce_data.append({'Tranche': t.name, 'Size': t.original_balance/1_000_000, 'CE': 0})
        else:
            running_ce += DEFAULT_TRANCHES[-1].original_balance if len(ce_data) == 1 else 0
            for prev in DEFAULT_TRANCHES[DEFAULT_TRANCHES.index(t)+1:]:
                if not prev.is_equity:
                    running_ce += prev.original_balance
            ce = running_ce / DEFAULT_POOL.balance * 100
            ce_data.append({'Tranche': t.name, 'Size': t.original_balance/1_000_000, 'CE': ce})

    ce_data.reverse()

    fig2 = go.Figure()

    cumulative = 0
    for i, t in enumerate(DEFAULT_TRANCHES):
        size = t.original_balance / 1_000_000
        fig2.add_trace(go.Bar(
            name=t.name,
            x=[size],
            y=['Deal Structure'],
            orientation='h',
            marker_color=colors[i],
            text=f"{t.name}<br>${size:.0f}M ({size}%)",
            textposition='inside'
        ))

    fig2.update_layout(
        title="Capital Structure (Senior to Junior)",
        barmode='stack',
        height=200,
        showlegend=False
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("""
    **How Credit Enhancement Works:**

    - Class A has 20% credit enhancement (Class B + C + Equity below it)
    - Class B has 8% credit enhancement (Class C + Equity below it)
    - Class C has 3% credit enhancement (Equity only)
    - Equity has 0% - it takes the first loss

    This means Class A can absorb 20% pool losses before seeing any principal loss.
    """)

# TAB 3: OC Tests
with tab3:
    st.markdown("### Overcollateralization Tests")
    st.caption("Are there enough assets backing each tranche?")

    # OC test summary
    st.markdown("#### Current OC Test Status")

    for t in DEFAULT_TRANCHES:
        if t.is_equity:
            continue

        fail_months = metrics[t.name]['OC_Fail_Months']
        total_months = len(df)

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown(f"**{t.name}** - Target: {t.oc_target*100:.0f}%")

        with col2:
            if fail_months == 0:
                st.success("PASS")
            else:
                st.error(f"FAIL ({fail_months} months)")

        with col3:
            if fail_months > 0:
                st.caption(f"Failed {fail_months}/{total_months} months")
            else:
                st.caption("Never breached")

    st.markdown("---")

    # OC ratio over time
    st.markdown("#### OC Ratio Over Time")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['Month'],
        y=df['OC_Ratio'],
        mode='lines',
        name='OC Ratio',
        line=dict(color='#1E3A5F', width=2)
    ))

    # Add trigger lines
    for t in DEFAULT_TRANCHES:
        if not t.is_equity:
            fig.add_hline(
                y=t.oc_target * 100,
                line_dash="dash",
                line_color="orange",
                annotation_text=f"{t.name} Target ({t.oc_target*100:.0f}%)"
            )

    fig.update_layout(
        title="Pool OC Ratio vs Trigger Levels",
        xaxis_title="Month",
        yaxis_title="OC Ratio (%)",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    **What happens when OC fails?**

    When a tranche's OC test fails, it means there isn't enough collateral cushion.
    The waterfall responds by:

    1. **Redirecting cash** - Interest that would go to junior tranches gets
       redirected to pay down senior principal faster
    2. **Turbo pay** - Seniors get paid down quickly to restore the OC ratio
    3. **Junior deferral** - Junior tranches may have interest deferred

    This is how the structure protects senior investors during stress.
    """)

# TAB 4: Cash Flows
with tab4:
    st.markdown("### Monthly Cash Flow Detail")

    # Pool cash flows chart
    st.markdown("#### Pool Performance")

    fig = make_subplots(rows=2, cols=2,
                        subplot_titles=("Pool Balance", "Monthly Collections",
                                       "Cumulative Net Loss", "Tranche Balances"))

    # Pool balance
    fig.add_trace(go.Scatter(
        x=df['Month'], y=df['Pool_Balance']/1_000_000,
        fill='tozeroy', name='Pool Balance',
        line=dict(color='#1E3A5F')
    ), row=1, col=1)

    # Monthly collections
    fig.add_trace(go.Bar(
        x=df['Month'], y=df['Principal']/1_000_000,
        name='Principal', marker_color='#2E7D32'
    ), row=1, col=2)
    fig.add_trace(go.Bar(
        x=df['Month'], y=df['Interest_Income']/1_000_000,
        name='Interest', marker_color='#1976D2'
    ), row=1, col=2)

    # CNL
    fig.add_trace(go.Scatter(
        x=df['Month'], y=df['CNL'],
        name='CNL %', line=dict(color='#C62828', width=2)
    ), row=2, col=1)

    # Tranche balances
    for i, t in enumerate(DEFAULT_TRANCHES):
        if not t.is_equity:
            fig.add_trace(go.Scatter(
                x=df['Month'], y=df[f'{t.name}_Balance']/1_000_000,
                name=t.name, line=dict(color=colors[i])
            ), row=2, col=2)

    fig.update_layout(height=600, showlegend=True, barmode='stack')
    fig.update_xaxes(title_text="Month")
    fig.update_yaxes(title_text="$M", row=1, col=1)
    fig.update_yaxes(title_text="$M", row=1, col=2)
    fig.update_yaxes(title_text="CNL %", row=2, col=1)
    fig.update_yaxes(title_text="$M", row=2, col=2)

    st.plotly_chart(fig, use_container_width=True)

    # Detailed table
    with st.expander("View Raw Data"):
        display_cols = ['Month', 'Pool_Balance', 'Interest_Income', 'Principal',
                       'Defaults', 'Losses', 'CNL', 'OC_Ratio']
        display_df = df[display_cols].copy()
        display_df['Pool_Balance'] = display_df['Pool_Balance'].apply(lambda x: f"${x/1_000_000:.2f}M")
        display_df['Interest_Income'] = display_df['Interest_Income'].apply(lambda x: f"${x/1_000:,.0f}K")
        display_df['Principal'] = display_df['Principal'].apply(lambda x: f"${x/1_000:,.0f}K")
        display_df['Defaults'] = display_df['Defaults'].apply(lambda x: f"${x/1_000:,.0f}K")
        display_df['Losses'] = display_df['Losses'].apply(lambda x: f"${x/1_000:,.0f}K")
        display_df['CNL'] = display_df['CNL'].apply(lambda x: f"{x:.2f}%")
        display_df['OC_Ratio'] = display_df['OC_Ratio'].apply(lambda x: f"{x:.1f}%")

        st.dataframe(display_df, use_container_width=True, height=400)

# ============================================================================
# SCENARIO COMPARISON (optional)
# ============================================================================

st.markdown("---")
st.markdown("### Quick Scenario Comparison")

with st.expander("Compare Multiple Scenarios"):
    st.caption("See how different assumptions affect returns")

    scenarios = [
        ("Base", 0.10, 0.02, 0.80),
        ("Low Default", 0.10, 0.01, 0.80),
        ("High Default", 0.10, 0.06, 0.80),
        ("Stress", 0.05, 0.08, 0.90),
        ("Recession", 0.03, 0.12, 0.95),
    ]

    comparison_data = []
    for name, s_cpr, s_cdr, s_sev in scenarios:
        _, s_metrics = run_simple_waterfall(
            pool=DEFAULT_POOL,
            tranches=DEFAULT_TRANCHES,
            cpr=s_cpr,
            cdr=s_cdr,
            severity=s_sev,
            sofr=sofr
        )

        comparison_data.append({
            'Scenario': name,
            'CPR': f"{s_cpr*100:.0f}%",
            'CDR': f"{s_cdr*100:.0f}%",
            'Severity': f"{s_sev*100:.0f}%",
            'Pool CNL': f"{s_metrics['Pool']['Final_CNL']:.1f}%",
            'Class A MOIC': f"{s_metrics['Class A']['MOIC']:.2f}x",
            'Class B MOIC': f"{s_metrics['Class B']['MOIC']:.2f}x",
            'Class C MOIC': f"{s_metrics['Class C']['MOIC']:.2f}x",
            'Equity MOIC': f"{s_metrics['Equity']['MOIC']:.2f}x",
        })

    st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)

    st.markdown("""
    **Key Insight:** Notice how the senior tranches (Class A, B) maintain their 1.0x+ MOIC
    even in stress scenarios, while the equity absorbs the losses. This is the power of
    credit enhancement and structural subordination.
    """)

# Footer
st.markdown("---")
st.caption("Deal Analyzer - Educational tool for understanding ABS structures | Bain Capital Credit")
