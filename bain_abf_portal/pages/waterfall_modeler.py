"""
Waterfall Modeler - Page 1 (Rebuilt)
Interactive ABS/CLO waterfall and trigger modeling with proper cash flow engine
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.deal_structure import (
    DealStructure, Tranche, CollateralPool, TriggerTest, Fee, ReserveAccount,
    Rating, RatingAgency, CollateralType, PaymentPriority,
    DEAL_TEMPLATES, create_acmat_2025_4, create_subprime_auto_template, create_clo_template
)
from models.cashflow_engine import (
    CashFlowEngine, ScenarioAssumptions, PrepaymentAssumption, DefaultAssumption,
    PrepaymentModel, DefaultModel, create_base_scenario, create_stress_scenario,
    calculate_breakeven_cdr
)

st.markdown('<p class="main-header">📈 Waterfall / Trigger Modeler</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Model cash flow waterfalls, triggers, and run scenario analysis</p>', unsafe_allow_html=True)

# ============================================================================
# SESSION STATE
# ============================================================================

if 'deal' not in st.session_state:
    st.session_state.deal = None
if 'projection_results' not in st.session_state:
    st.session_state.projection_results = None


# ============================================================================
# SIDEBAR - DEAL INPUT
# ============================================================================

st.sidebar.markdown("### 📋 Deal Input")

input_method = st.sidebar.radio(
    "Input Method",
    ["Use Template", "Enter Deal Terms", "Paste JSON"],
    index=0
)

if input_method == "Use Template":
    template_names = list(DEAL_TEMPLATES.keys())
    selected_template = st.sidebar.selectbox("Select Template", template_names, index=0)

    if st.sidebar.button("Load Template"):
        template_func = DEAL_TEMPLATES[selected_template]
        st.session_state.deal = template_func()
        st.sidebar.success(f"Loaded {selected_template}")

elif input_method == "Enter Deal Terms":
    st.sidebar.markdown("#### Collateral")
    coll_balance = st.sidebar.number_input("Collateral Balance ($M)", value=300.0, step=10.0) * 1_000_000
    coll_wac = st.sidebar.slider("WAC (%)", 5.0, 30.0, 18.0, 0.5) / 100
    coll_wal = st.sidebar.slider("WAL (years)", 1.0, 7.0, 2.5, 0.25)
    coll_type = st.sidebar.selectbox("Collateral Type",
                                     [ct.value for ct in CollateralType],
                                     index=1)

    st.sidebar.markdown("#### Capital Structure")
    st.sidebar.caption("Enter tranches (name, size $M, spread bps, rating)")

    # Dynamic tranche input
    num_tranches = st.sidebar.number_input("Number of Tranches", 2, 8, 4)

    tranches_input = []
    for i in range(int(num_tranches)):
        col1, col2 = st.sidebar.columns(2)
        with col1:
            name = st.text_input(f"Name {i+1}", f"Class {'ABCDEFGH'[i]}", key=f"tr_name_{i}")
            spread = st.number_input(f"Spread (bps)", 0, 1000, 100 + i*100, key=f"tr_spread_{i}")
        with col2:
            size = st.number_input(f"Size ($M)", 0.0, 1000.0, 50.0, key=f"tr_size_{i}")
            rating = st.selectbox(f"Rating", ["AAA", "AA", "A", "BBB", "BB", "B", "NR"],
                                  index=min(i, 6), key=f"tr_rating_{i}")
        tranches_input.append((name, size * 1_000_000, spread / 10000, rating))

    st.sidebar.markdown("#### Triggers")
    oc_trigger = st.sidebar.slider("OC Test Threshold (%)", 100.0, 130.0, 110.0, 1.0)
    ic_trigger = st.sidebar.slider("IC Test Threshold (x)", 1.0, 2.5, 1.5, 0.05)
    cnl_trigger = st.sidebar.slider("CNL Trigger (%)", 5.0, 40.0, 20.0, 1.0)

    if st.sidebar.button("Create Deal"):
        # Build collateral pool
        collateral = CollateralPool(
            original_balance=coll_balance,
            current_balance=coll_balance,
            collateral_type=CollateralType(coll_type),
            weighted_average_coupon=coll_wac,
            weighted_average_maturity=coll_wal * 12,
            weighted_average_life=coll_wal
        )

        # Build tranches
        tranches = []
        for name, size, spread, rating in tranches_input:
            tranches.append(Tranche(
                name=name,
                original_balance=size,
                current_balance=size,
                coupon_type="floating",
                spread=spread,
                ratings=[Rating(RatingAgency.SP, rating)]
            ))

        # Build triggers
        triggers = [
            TriggerTest("OC Test", "oc", oc_trigger, ">=", "Redirect cash to seniors"),
            TriggerTest("IC Test", "ic", ic_trigger, ">=", "Redirect interest to seniors"),
            TriggerTest("CNL Trigger", "cnl", cnl_trigger, "<=", "Switch to sequential pay"),
        ]

        # Build fees
        fees = [
            Fee("Servicer Fee", 0.01, "collateral", priority=1),
            Fee("Trustee Fee", 0.0002, "collateral", priority=2),
        ]

        st.session_state.deal = DealStructure(
            deal_name="Custom Deal",
            issuer="Custom",
            pricing_date="",
            closing_date="",
            collateral=collateral,
            tranches=tranches,
            triggers=triggers,
            fees=fees
        )
        st.sidebar.success("Deal created!")

elif input_method == "Paste JSON":
    json_input = st.sidebar.text_area("Paste Deal JSON", height=200,
                                       placeholder='{"deal_name": "...", "issuer": "...", ...}')

    if st.sidebar.button("Parse JSON"):
        try:
            data = json.loads(json_input)
            st.session_state.deal = DealStructure.from_dict(data)
            st.sidebar.success("Deal parsed successfully!")
        except Exception as e:
            st.sidebar.error(f"Error parsing JSON: {e}")

st.sidebar.markdown("---")

# ============================================================================
# SCENARIO ASSUMPTIONS
# ============================================================================

st.sidebar.markdown("### 📊 Scenario Assumptions")

scenario_type = st.sidebar.radio("Scenario", ["Base", "Stress", "Custom"], horizontal=True)

if scenario_type == "Custom":
    st.sidebar.markdown("#### Prepayment")
    prepay_model = st.sidebar.selectbox("Model",
                                         [pm.value for pm in PrepaymentModel],
                                         index=0)
    cpr = st.sidebar.slider("CPR (%)", 0.0, 50.0, 15.0, 1.0) / 100

    st.sidebar.markdown("#### Defaults")
    default_model = st.sidebar.selectbox("Default Model",
                                          [dm.value for dm in DefaultModel],
                                          index=0)
    cdr = st.sidebar.slider("CDR (%)", 0.0, 25.0, 5.0, 0.5) / 100
    recovery = st.sidebar.slider("Recovery Rate (%)", 0.0, 80.0, 40.0, 5.0) / 100

    st.sidebar.markdown("#### Rates")
    sofr = st.sidebar.slider("SOFR (%)", 0.0, 8.0, 4.33, 0.25) / 100
    projection_months = st.sidebar.slider("Projection (months)", 12, 120, 60, 6)

    scenario = ScenarioAssumptions(
        name="Custom",
        prepayment=PrepaymentAssumption(
            model=PrepaymentModel(prepay_model),
            base_cpr=cpr
        ),
        default=DefaultAssumption(
            model=DefaultModel(default_model),
            base_cdr=cdr,
            recovery_rate=recovery
        ),
        index_rate=sofr,
        projection_months=projection_months
    )
elif scenario_type == "Stress":
    scenario = create_stress_scenario()
    st.sidebar.info("Stress: CDR 10%, Recovery 30%, Front-loaded defaults")
else:
    scenario = create_base_scenario()
    st.sidebar.info("Base: CPR 15%, CDR 3%, Recovery 40%")

# Run button
run_projection = st.sidebar.button("🚀 Run Projection", type="primary", use_container_width=True)

# ============================================================================
# MAIN CONTENT
# ============================================================================

if st.session_state.deal is None:
    st.info("👈 Select a deal template or enter deal terms in the sidebar to get started.")
    st.stop()

deal = st.session_state.deal

# Run projection if button pressed or no results yet
if run_projection or st.session_state.projection_results is None:
    with st.spinner("Running cash flow projection..."):
        engine = CashFlowEngine(deal, scenario)
        results = engine.run_projection()
        st.session_state.projection_results = {
            'engine': engine,
            'flows': results,
            'scenario': scenario
        }

if st.session_state.projection_results is None:
    st.warning("Click 'Run Projection' to generate cash flows")
    st.stop()

engine = st.session_state.projection_results['engine']
flows = st.session_state.projection_results['flows']

# ============================================================================
# TABS
# ============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Deal Summary",
    "🌊 Cash Flows",
    "📈 Scenarios",
    "⚠️ Triggers",
    "📊 Tranche Analysis"
])

# ============================================================================
# TAB 1: DEAL SUMMARY
# ============================================================================

with tab1:
    st.markdown(f"### {deal.deal_name}")
    if deal.issuer:
        st.markdown(f"**Issuer:** {deal.issuer} | **Bookrunner:** {deal.bookrunner} | **Format:** {deal.format}")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Capital Structure")

        # Build structure table
        structure_data = []
        for t in deal.tranches:
            ce = deal.credit_enhancement(t.name)
            rating_str = t.ratings[0].rating if t.ratings else "NR"
            spread_bps = int(t.spread * 10000)

            structure_data.append({
                'Tranche': t.name,
                'Balance ($M)': f"${t.current_balance/1_000_000:,.1f}",
                'Rating': rating_str,
                'Spread': f"+{spread_bps}bps" if spread_bps > 0 else "Residual",
                'All-in Rate': f"{(scenario.index_rate + t.spread)*100:.2f}%" if spread_bps > 0 else "-",
                'Credit Enh': f"{ce:.1f}%",
                '% of Deal': f"{t.current_balance/deal.collateral.current_balance*100:.1f}%"
            })

        st.dataframe(pd.DataFrame(structure_data), use_container_width=True, hide_index=True)

        # Waterfall chart
        fig = go.Figure()
        colors = px.colors.sequential.Blues[::-1]

        for i, t in enumerate(deal.tranches):
            fig.add_trace(go.Bar(
                y=[t.name],
                x=[t.current_balance / 1_000_000],
                orientation='h',
                marker_color=colors[i % len(colors)],
                text=f"${t.current_balance/1_000_000:.0f}M",
                textposition='inside',
                name=t.name
            ))

        fig.update_layout(
            title="Capital Structure",
            xaxis_title="Balance ($M)",
            height=300,
            showlegend=False,
            barmode='stack'
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Collateral Summary")
        st.metric("Total Balance", f"${deal.collateral.current_balance/1_000_000:,.1f}M")
        st.metric("WAC", f"{deal.collateral.weighted_average_coupon*100:.1f}%")
        st.metric("WAL", f"{deal.collateral.weighted_average_life:.1f} years")
        st.metric("Collateral Type", deal.collateral.collateral_type.value)

        st.markdown("#### Current Tests")
        oc = deal.overcollateralization()
        ic = deal.interest_coverage(scenario.index_rate)
        st.metric("OC Ratio", f"{oc:.1f}%")
        st.metric("IC Ratio", f"{ic:.2f}x")

    # Triggers table
    st.markdown("#### Structural Triggers")
    trigger_data = []
    for tr in deal.triggers:
        trigger_data.append({
            'Trigger': tr.name,
            'Test': tr.test_type.upper(),
            'Threshold': f"{tr.threshold:.1f}{'%' if tr.test_type in ['oc', 'cnl'] else 'x'}",
            'Comparison': tr.comparison,
            'Consequence': tr.consequence
        })
    st.dataframe(pd.DataFrame(trigger_data), use_container_width=True, hide_index=True)

# ============================================================================
# TAB 2: CASH FLOWS
# ============================================================================

with tab2:
    st.markdown("### Cash Flow Projection")
    st.caption(f"Scenario: {scenario.name} | CPR: {scenario.prepayment.base_cpr*100:.0f}% | CDR: {scenario.default.base_cdr*100:.1f}% | Recovery: {scenario.default.recovery_rate*100:.0f}%")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    final_cnl = flows[-1].cnl_rate if flows else 0
    total_losses = flows[-1].cumulative_losses if flows else 0
    final_coll = flows[-1].ending_balance if flows else 0
    total_prin = flows[-1].cumulative_principal if flows else 0

    with col1:
        st.metric("Final CNL", f"{final_cnl:.2f}%")
    with col2:
        st.metric("Total Losses", f"${total_losses/1_000_000:.2f}M")
    with col3:
        st.metric("Final Collateral", f"${final_coll/1_000_000:.1f}M")
    with col4:
        coll_factor = final_coll / deal.collateral.original_balance * 100
        st.metric("Collateral Factor", f"{coll_factor:.1f}%")

    # Cash flow charts
    df = engine.get_summary_dataframe()

    # Collateral amortization
    fig = make_subplots(rows=2, cols=2,
                        subplot_titles=("Collateral Balance", "Cumulative Net Loss",
                                       "Monthly Cash Flows", "Trigger Tests"))

    # Collateral balance
    fig.add_trace(go.Scatter(
        x=df['Period'], y=df['Collateral_End']/1_000_000,
        name='Collateral', fill='tozeroy', line=dict(color='#1E3A5F')
    ), row=1, col=1)

    # CNL
    fig.add_trace(go.Scatter(
        x=df['Period'], y=df['CNL_%'],
        name='CNL %', line=dict(color='#C62828', width=2)
    ), row=1, col=2)

    # Add CNL trigger line
    cnl_trigger = next((tr.threshold for tr in deal.triggers if tr.test_type == 'cnl'), None)
    if cnl_trigger:
        fig.add_hline(y=cnl_trigger, line_dash="dash", line_color="orange",
                     annotation_text=f"Trigger: {cnl_trigger}%", row=1, col=2)

    # Monthly cash flows
    fig.add_trace(go.Bar(
        x=df['Period'], y=df['Scheduled_Prin']/1_000_000,
        name='Scheduled', marker_color='#2E7D32'
    ), row=2, col=1)
    fig.add_trace(go.Bar(
        x=df['Period'], y=df['Prepayments']/1_000_000,
        name='Prepays', marker_color='#1976D2'
    ), row=2, col=1)
    fig.add_trace(go.Bar(
        x=df['Period'], y=-df['Defaults']/1_000_000,
        name='Defaults', marker_color='#C62828'
    ), row=2, col=1)

    # OC/IC tests
    fig.add_trace(go.Scatter(
        x=df['Period'], y=df['OC_%'],
        name='OC %', line=dict(color='#1E3A5F')
    ), row=2, col=2)
    fig.add_trace(go.Scatter(
        x=df['Period'], y=df['IC_x'] * 50,  # Scale for visibility
        name='IC (scaled)', line=dict(color='#2E7D32', dash='dash')
    ), row=2, col=2)

    fig.update_layout(height=600, showlegend=True, barmode='relative')
    fig.update_xaxes(title_text="Month", row=2)
    fig.update_yaxes(title_text="$M", row=1, col=1)
    fig.update_yaxes(title_text="CNL %", row=1, col=2)
    fig.update_yaxes(title_text="$M", row=2, col=1)
    fig.update_yaxes(title_text="%", row=2, col=2)

    st.plotly_chart(fig, use_container_width=True)

    # Detailed cash flow table
    with st.expander("📊 Detailed Cash Flow Table"):
        display_df = df.copy()
        # Format for display
        for col in display_df.columns:
            if 'Balance' in col or 'Prin' in col or 'Interest' in col or col in ['Defaults', 'Recoveries', 'Losses', 'Excess_Spread']:
                display_df[col] = display_df[col].apply(lambda x: f"${x/1000:,.0f}K" if pd.notna(x) else "")

        st.dataframe(display_df, use_container_width=True, height=400)

# ============================================================================
# TAB 3: SCENARIOS
# ============================================================================

with tab3:
    st.markdown("### Scenario Comparison")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Base Case Assumptions")
        base_cpr = st.slider("Base CPR (%)", 0.0, 50.0, 15.0, 1.0, key="base_cpr") / 100
        base_cdr = st.slider("Base CDR (%)", 0.0, 20.0, 3.0, 0.5, key="base_cdr") / 100
        base_recovery = st.slider("Base Recovery (%)", 0.0, 80.0, 40.0, 5.0, key="base_rec") / 100

    with col2:
        st.markdown("#### Stress Case Assumptions")
        stress_cpr = st.slider("Stress CPR (%)", 0.0, 50.0, 8.0, 1.0, key="stress_cpr") / 100
        stress_cdr = st.slider("Stress CDR (%)", 0.0, 30.0, 10.0, 0.5, key="stress_cdr") / 100
        stress_recovery = st.slider("Stress Recovery (%)", 0.0, 80.0, 30.0, 5.0, key="stress_rec") / 100

    if st.button("Run Comparison", type="primary"):
        # Create fresh deal copies and run scenarios
        base_scenario = create_base_scenario(cpr=base_cpr, cdr=base_cdr, recovery=base_recovery)
        stress_scenario = create_stress_scenario(cpr=stress_cpr, cdr=stress_cdr, recovery=stress_recovery)

        # Reset deal balances for base
        base_deal = DEAL_TEMPLATES.get(deal.deal_name, create_subprime_auto_template)()
        stress_deal = DEAL_TEMPLATES.get(deal.deal_name, create_subprime_auto_template)()

        base_engine = CashFlowEngine(base_deal, base_scenario)
        base_flows = base_engine.run_projection()
        base_df = base_engine.get_summary_dataframe()

        stress_engine = CashFlowEngine(stress_deal, stress_scenario)
        stress_flows = stress_engine.run_projection()
        stress_df = stress_engine.get_summary_dataframe()

        # Comparison metrics
        st.markdown("---")
        st.markdown("### Results Comparison")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Metric**")
            st.markdown("Final CNL")
            st.markdown("Total Losses")
            st.markdown("Final Collateral Factor")

        with col2:
            st.markdown("**Base Case**")
            st.markdown(f"{base_flows[-1].cnl_rate:.2f}%")
            st.markdown(f"${base_flows[-1].cumulative_losses/1_000_000:.2f}M")
            st.markdown(f"{base_flows[-1].ending_balance/base_deal.collateral.original_balance*100:.1f}%")

        with col3:
            st.markdown("**Stress Case**")
            st.markdown(f"{stress_flows[-1].cnl_rate:.2f}%")
            st.markdown(f"${stress_flows[-1].cumulative_losses/1_000_000:.2f}M")
            st.markdown(f"{stress_flows[-1].ending_balance/stress_deal.collateral.original_balance*100:.1f}%")

        # CNL comparison chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=base_df['Period'], y=base_df['CNL_%'],
            name='Base Case', line=dict(color='#2E7D32', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=stress_df['Period'], y=stress_df['CNL_%'],
            name='Stress Case', line=dict(color='#C62828', width=2)
        ))

        # Add trigger
        cnl_trigger = next((tr.threshold for tr in deal.triggers if tr.test_type == 'cnl'), None)
        if cnl_trigger:
            fig.add_hline(y=cnl_trigger, line_dash="dash", line_color="orange",
                         annotation_text=f"CNL Trigger: {cnl_trigger}%")

        fig.update_layout(
            title="CNL Buildup: Base vs. Stress",
            xaxis_title="Month",
            yaxis_title="CNL (%)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # Collateral comparison
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=base_df['Period'], y=base_df['Collateral_End']/1_000_000,
            name='Base Case', fill='tozeroy', line=dict(color='#2E7D32')
        ))
        fig2.add_trace(go.Scatter(
            x=stress_df['Period'], y=stress_df['Collateral_End']/1_000_000,
            name='Stress Case', fill='tozeroy', line=dict(color='#C62828')
        ))
        fig2.update_layout(
            title="Collateral Amortization: Base vs. Stress",
            xaxis_title="Month",
            yaxis_title="Balance ($M)",
            height=400
        )
        st.plotly_chart(fig2, use_container_width=True)

# ============================================================================
# TAB 4: TRIGGERS
# ============================================================================

with tab4:
    st.markdown("### Trigger Analysis")

    # Current trigger status
    st.markdown("#### Current Trigger Status")

    trigger_results = deal.evaluate_triggers(scenario.index_rate)

    for trigger_name, result in trigger_results.items():
        status = "✅ Pass" if result['passed'] else "❌ Breach"
        threshold_str = f"{result['threshold']:.1f}" + ("%" if "oc" in trigger_name.lower() or "cnl" in trigger_name.lower() else "x")
        current_str = f"{result['current_value']:.2f}" + ("%" if "oc" in trigger_name.lower() or "cnl" in trigger_name.lower() else "x")

        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        col1.markdown(f"**{trigger_name}**")
        col2.markdown(f"Current: {current_str}")
        col3.markdown(f"Threshold: {threshold_str}")
        col4.markdown(status)

        if not result['passed'] and result['consequence']:
            st.warning(f"⚠️ {result['consequence']}")

    st.markdown("---")

    # Trigger breach timeline
    st.markdown("#### Trigger Breach Timeline (Projection)")

    df = engine.get_summary_dataframe()

    breach_data = []
    cnl_trigger = next((tr.threshold for tr in deal.triggers if tr.test_type == 'cnl'), 100)
    oc_trigger = next((tr.threshold for tr in deal.triggers if tr.test_type == 'oc'), 0)

    # Find CNL breach
    cnl_breach = df[df['CNL_%'] >= cnl_trigger]
    if len(cnl_breach) > 0:
        breach_data.append({
            'Trigger': 'CNL Trigger',
            'Breach Period': f"Month {cnl_breach['Period'].iloc[0]}",
            'Value at Breach': f"{cnl_breach['CNL_%'].iloc[0]:.2f}%",
            'Threshold': f"{cnl_trigger:.1f}%"
        })
    else:
        breach_data.append({
            'Trigger': 'CNL Trigger',
            'Breach Period': 'Not breached',
            'Value at Breach': f"Max: {df['CNL_%'].max():.2f}%",
            'Threshold': f"{cnl_trigger:.1f}%"
        })

    # Find OC breach
    oc_breach = df[df['OC_%'] < oc_trigger]
    if len(oc_breach) > 0:
        breach_data.append({
            'Trigger': 'OC Test',
            'Breach Period': f"Month {oc_breach['Period'].iloc[0]}",
            'Value at Breach': f"{oc_breach['OC_%'].iloc[0]:.1f}%",
            'Threshold': f"{oc_trigger:.1f}%"
        })
    else:
        breach_data.append({
            'Trigger': 'OC Test',
            'Breach Period': 'Not breached',
            'Value at Breach': f"Min: {df['OC_%'].min():.1f}%",
            'Threshold': f"{oc_trigger:.1f}%"
        })

    st.dataframe(pd.DataFrame(breach_data), use_container_width=True, hide_index=True)

    # Sensitivity heatmap
    st.markdown("---")
    st.markdown("#### CNL Sensitivity Analysis")
    st.caption("Final CNL under different CDR/Recovery combinations")

    # Run multiple scenarios
    cdr_range = [0.02, 0.04, 0.06, 0.08, 0.10, 0.12]
    recovery_range = [0.50, 0.40, 0.30, 0.20]

    sensitivity_matrix = []
    for cdr in cdr_range:
        row = []
        for rec in recovery_range:
            # Quick projection
            test_scenario = create_base_scenario(cdr=cdr, recovery=rec, months=48)
            test_deal = DEAL_TEMPLATES.get(deal.deal_name, create_subprime_auto_template)()
            test_engine = CashFlowEngine(test_deal, test_scenario)
            test_flows = test_engine.run_projection()
            final_cnl = test_flows[-1].cnl_rate if test_flows else 0
            row.append(final_cnl)
        sensitivity_matrix.append(row)

    sens_df = pd.DataFrame(
        sensitivity_matrix,
        index=[f"{cdr*100:.0f}%" for cdr in cdr_range],
        columns=[f"{rec*100:.0f}%" for rec in recovery_range]
    )

    fig = px.imshow(
        sens_df.values,
        labels=dict(x="Recovery Rate", y="CDR", color="Final CNL (%)"),
        x=sens_df.columns,
        y=sens_df.index,
        color_continuous_scale=['#2E7D32', '#FFC107', '#C62828'],
        aspect="auto",
        text_auto='.1f'
    )

    fig.update_layout(
        title="Final CNL Sensitivity (CDR vs Recovery)",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 5: TRANCHE ANALYSIS
# ============================================================================

with tab5:
    st.markdown("### Tranche Performance")

    # Tranche summary
    tranche_df = engine.get_tranche_summary()
    st.dataframe(tranche_df, use_container_width=True, hide_index=True)

    # Break-even CDR analysis
    st.markdown("---")
    st.markdown("#### Break-Even Default Rates")
    st.caption("CDR at which each tranche begins to experience principal loss")

    breakeven_data = []
    for t in deal.tranches:
        if t.ratings and t.ratings[0].rating != "NR":
            ce = deal.credit_enhancement(t.name)
            # Simplified breakeven estimate: CE / (1 - Recovery) / WAL
            wal = deal.collateral.weighted_average_life
            recovery = scenario.default.recovery_rate
            be_cdr = (ce / 100) / ((1 - recovery) * wal) if wal > 0 else 0

            breakeven_data.append({
                'Tranche': t.name,
                'Rating': t.ratings[0].rating,
                'Credit Enhancement': f"{ce:.1f}%",
                'Est. Break-Even CDR': f"{be_cdr*100:.1f}%",
                'Cushion vs Base': f"+{(be_cdr - scenario.default.base_cdr)*100:.1f}%"
            })

    be_df = pd.DataFrame(breakeven_data)
    st.dataframe(be_df, use_container_width=True, hide_index=True)

    # Tranche paydown chart
    st.markdown("---")
    st.markdown("#### Tranche Paydown Over Time")

    df = engine.get_summary_dataframe()

    fig = go.Figure()
    colors = px.colors.sequential.Blues[::-1]

    for i, t in enumerate(deal.tranches):
        col_name = f'{t.name}_Balance'
        if col_name in df.columns:
            fig.add_trace(go.Scatter(
                x=df['Period'],
                y=df[col_name] / 1_000_000,
                name=t.name,
                stackgroup='one',
                line=dict(color=colors[i % len(colors)])
            ))

    fig.update_layout(
        title="Tranche Balances Over Time",
        xaxis_title="Month",
        yaxis_title="Balance ($M)",
        height=400,
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Interest distribution
    st.markdown("#### Interest Distribution")

    interest_cols = [c for c in df.columns if '_Interest' in c]
    if interest_cols:
        interest_totals = {col.replace('_Interest', ''): df[col].sum() for col in interest_cols}

        fig = go.Figure(data=[go.Pie(
            labels=list(interest_totals.keys()),
            values=list(interest_totals.values()),
            hole=0.4
        )])
        fig.update_layout(
            title="Total Interest Distribution by Tranche",
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)
