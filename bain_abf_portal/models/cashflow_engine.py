"""
Cash Flow Engine
Proper ABS/CLO cash flow projection with realistic prepayment and default curves
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import numpy as np
import pandas as pd
from enum import Enum


class PrepaymentModel(Enum):
    CONSTANT = "Constant CPR"
    RAMP = "PSA-Style Ramp"
    VECTOR = "Custom Vector"
    SEASONAL = "Seasonal Adjusted"


class DefaultModel(Enum):
    CONSTANT = "Constant CDR"
    FRONT_LOADED = "Front-Loaded"
    BACK_LOADED = "Back-Loaded"
    SDA = "SDA Curve"
    VECTOR = "Custom Vector"


@dataclass
class PrepaymentAssumption:
    """Prepayment speed assumption"""
    model: PrepaymentModel
    base_cpr: float              # Annual CPR as decimal (0.15 = 15%)
    ramp_months: int = 24        # Months to reach full speed (for ramp models)
    vector: List[float] = field(default_factory=list)  # Monthly CPR vector
    seasonal_factors: Dict[int, float] = field(default_factory=dict)  # Month -> factor

    def get_monthly_cpr(self, period: int, seasoning: int = 0) -> float:
        """Get CPR for a specific period"""
        if self.model == PrepaymentModel.CONSTANT:
            annual_cpr = self.base_cpr
        elif self.model == PrepaymentModel.RAMP:
            # PSA-style ramp: 0.2% CPR per month until ramp_months, then flat
            effective_month = seasoning + period
            if effective_month <= self.ramp_months:
                annual_cpr = self.base_cpr * (effective_month / self.ramp_months)
            else:
                annual_cpr = self.base_cpr
        elif self.model == PrepaymentModel.VECTOR:
            if period < len(self.vector):
                annual_cpr = self.vector[period]
            else:
                annual_cpr = self.vector[-1] if self.vector else self.base_cpr
        elif self.model == PrepaymentModel.SEASONAL:
            month_of_year = ((seasoning + period) % 12) + 1
            factor = self.seasonal_factors.get(month_of_year, 1.0)
            annual_cpr = self.base_cpr * factor
        else:
            annual_cpr = self.base_cpr

        # Convert annual CPR to monthly SMM
        # SMM = 1 - (1 - CPR)^(1/12)
        monthly_smm = 1 - (1 - annual_cpr) ** (1/12)
        return monthly_smm


@dataclass
class DefaultAssumption:
    """Default/loss assumption"""
    model: DefaultModel
    base_cdr: float              # Annual CDR as decimal
    recovery_rate: float         # Recovery rate as decimal (0.40 = 40%)
    recovery_lag: int = 6        # Months between default and recovery
    loss_severity: float = None  # Override (1 - recovery_rate)
    peak_month: int = 24         # For front/back loaded models
    vector: List[float] = field(default_factory=list)

    def __post_init__(self):
        if self.loss_severity is None:
            self.loss_severity = 1 - self.recovery_rate

    def get_monthly_cdr(self, period: int, seasoning: int = 0) -> float:
        """Get CDR for a specific period"""
        if self.model == DefaultModel.CONSTANT:
            annual_cdr = self.base_cdr
        elif self.model == DefaultModel.FRONT_LOADED:
            # Peak early, decline over time
            effective_month = seasoning + period
            if effective_month <= self.peak_month:
                # Ramp up to peak
                annual_cdr = self.base_cdr * (effective_month / self.peak_month) * 1.5
            else:
                # Decline after peak
                decay = np.exp(-0.03 * (effective_month - self.peak_month))
                annual_cdr = self.base_cdr * decay
        elif self.model == DefaultModel.BACK_LOADED:
            # Low early, increase over time
            effective_month = seasoning + period
            growth = 1 - np.exp(-0.05 * effective_month)
            annual_cdr = self.base_cdr * growth
        elif self.model == DefaultModel.SDA:
            # Standard Default Assumption (SDA) curve
            # Ramps to 100% at month 30, then declines
            effective_month = seasoning + period
            if effective_month <= 30:
                sda_factor = effective_month / 30
            elif effective_month <= 60:
                sda_factor = 1.0
            elif effective_month <= 120:
                sda_factor = 1.0 - (effective_month - 60) / 120
            else:
                sda_factor = 0.5
            annual_cdr = self.base_cdr * sda_factor
        elif self.model == DefaultModel.VECTOR:
            if period < len(self.vector):
                annual_cdr = self.vector[period]
            else:
                annual_cdr = self.vector[-1] if self.vector else self.base_cdr
        else:
            annual_cdr = self.base_cdr

        # Convert annual CDR to monthly MDR
        monthly_mdr = 1 - (1 - annual_cdr) ** (1/12)
        return monthly_mdr


@dataclass
class ScenarioAssumptions:
    """Complete scenario assumptions"""
    name: str
    prepayment: PrepaymentAssumption
    default: DefaultAssumption
    index_rate: float = 0.0433       # SOFR
    index_path: List[float] = field(default_factory=list)  # Rate path over time
    projection_months: int = 60

    def get_index_rate(self, period: int) -> float:
        """Get index rate for a specific period"""
        if self.index_path and period < len(self.index_path):
            return self.index_path[period]
        return self.index_rate


@dataclass
class PeriodCashFlow:
    """Cash flow for a single period"""
    period: int
    date: Optional[str] = None

    # Collateral
    beginning_balance: float = 0.0
    scheduled_principal: float = 0.0
    prepayments: float = 0.0
    defaults: float = 0.0
    recoveries: float = 0.0
    losses: float = 0.0
    ending_balance: float = 0.0
    interest_income: float = 0.0

    # Cumulative
    cumulative_losses: float = 0.0
    cumulative_principal: float = 0.0
    cnl_rate: float = 0.0

    # Waterfall
    fees_paid: float = 0.0
    tranche_interest: Dict[str, float] = field(default_factory=dict)
    tranche_principal: Dict[str, float] = field(default_factory=dict)
    tranche_balance: Dict[str, float] = field(default_factory=dict)
    excess_spread: float = 0.0
    residual: float = 0.0

    # Triggers
    oc_ratio: float = 0.0
    ic_ratio: float = 0.0
    trigger_status: Dict[str, bool] = field(default_factory=dict)


@dataclass
class TrancheCashFlow:
    """Cash flows for a specific tranche"""
    tranche_name: str
    periods: List[Dict] = field(default_factory=list)

    # Summary metrics
    total_interest: float = 0.0
    total_principal: float = 0.0
    average_life: float = 0.0
    yield_at_price: float = 0.0
    duration: float = 0.0
    loss_amount: float = 0.0

    def calculate_metrics(self, price: float = 100.0):
        """Calculate summary metrics from cash flows"""
        if not self.periods:
            return

        # Sum cash flows
        self.total_interest = sum(p.get('interest', 0) for p in self.periods)
        self.total_principal = sum(p.get('principal', 0) for p in self.periods)

        # Weighted average life
        weighted_time = sum(
            p.get('principal', 0) * p.get('period', i+1) / 12
            for i, p in enumerate(self.periods)
        )
        if self.total_principal > 0:
            self.average_life = weighted_time / self.total_principal

        # Simple yield calculation (IRR would be more accurate)
        if self.periods:
            original_balance = self.periods[0].get('beginning_balance', 0)
            if original_balance > 0:
                total_return = self.total_interest + self.total_principal
                avg_time = self.average_life if self.average_life > 0 else 1
                self.yield_at_price = ((total_return / (original_balance * price / 100)) ** (1/avg_time) - 1)


class CashFlowEngine:
    """Main cash flow projection engine"""

    def __init__(self, deal, scenario: ScenarioAssumptions):
        self.deal = deal
        self.scenario = scenario
        self.period_flows: List[PeriodCashFlow] = []
        self.tranche_flows: Dict[str, TrancheCashFlow] = {}

        # Track balances
        self.collateral_balance = deal.collateral.current_balance
        self.original_balance = deal.collateral.original_balance
        self.tranche_balances = {t.name: t.current_balance for t in deal.tranches}
        self.cumulative_losses = 0.0
        self.cumulative_principal = 0.0

        # Recovery queue (recoveries lag defaults)
        self.recovery_queue: List[Tuple[int, float]] = []  # (period_due, amount)

        # Initialize tranche flow trackers
        for t in deal.tranches:
            self.tranche_flows[t.name] = TrancheCashFlow(tranche_name=t.name)

    def run_projection(self) -> List[PeriodCashFlow]:
        """Run full cash flow projection"""
        self.period_flows = []

        for period in range(1, self.scenario.projection_months + 1):
            if self.collateral_balance <= 0:
                break

            cf = self._project_period(period)
            self.period_flows.append(cf)

        # Calculate tranche metrics
        for name, tf in self.tranche_flows.items():
            tf.calculate_metrics()

        return self.period_flows

    def _project_period(self, period: int) -> PeriodCashFlow:
        """Project cash flow for a single period"""
        cf = PeriodCashFlow(period=period, beginning_balance=self.collateral_balance)

        # Get assumptions for this period
        smm = self.scenario.prepayment.get_monthly_cpr(period, seasoning=0)
        mdr = self.scenario.default.get_monthly_cdr(period, seasoning=0)
        index_rate = self.scenario.get_index_rate(period)
        recovery_rate = self.scenario.default.recovery_rate
        recovery_lag = self.scenario.default.recovery_lag

        # =====================================================================
        # COLLATERAL CASH FLOWS
        # =====================================================================

        # Scheduled amortization (simplified - constant WAM decline)
        wam = max(1, self.deal.collateral.weighted_average_maturity - period)
        scheduled_factor = 1 / wam
        cf.scheduled_principal = self.collateral_balance * scheduled_factor * 0.5  # Conservative

        # Prepayments (SMM applied to remaining balance after scheduled)
        remaining_after_sched = self.collateral_balance - cf.scheduled_principal
        cf.prepayments = remaining_after_sched * smm

        # Defaults (MDR applied to balance before prepays)
        cf.defaults = self.collateral_balance * mdr

        # Queue recoveries
        if cf.defaults > 0:
            recovery_amount = cf.defaults * recovery_rate
            recovery_period = period + recovery_lag
            self.recovery_queue.append((recovery_period, recovery_amount))

        # Process recoveries due this period
        cf.recoveries = sum(amt for per, amt in self.recovery_queue if per == period)
        self.recovery_queue = [(p, a) for p, a in self.recovery_queue if p != period]

        # Losses
        cf.losses = cf.defaults * (1 - recovery_rate)
        self.cumulative_losses += cf.losses
        cf.cumulative_losses = self.cumulative_losses
        cf.cnl_rate = (self.cumulative_losses / self.original_balance) * 100

        # Interest income
        wac = self.deal.collateral.weighted_average_coupon
        cf.interest_income = self.collateral_balance * wac / 12

        # Update collateral balance
        cf.ending_balance = (
            self.collateral_balance
            - cf.scheduled_principal
            - cf.prepayments
            - cf.defaults
            + cf.recoveries
        )
        cf.ending_balance = max(0, cf.ending_balance)
        self.collateral_balance = cf.ending_balance

        # Total principal available
        total_principal = cf.scheduled_principal + cf.prepayments + cf.recoveries
        self.cumulative_principal += total_principal
        cf.cumulative_principal = self.cumulative_principal

        # =====================================================================
        # WATERFALL
        # =====================================================================

        available_interest = cf.interest_income
        available_principal = total_principal

        # 1. Senior fees
        for fee in sorted(self.deal.fees, key=lambda f: f.priority):
            if not fee.is_subordinated:
                fee_amount = fee.calculate(
                    self.collateral_balance,
                    sum(self.tranche_balances.values()),
                    self.deal.payment_frequency
                )
                paid = min(available_interest, fee_amount)
                cf.fees_paid += paid
                available_interest -= paid

        # 2. Tranche interest (in order of seniority)
        for tranche in self.deal.tranches:
            if tranche.ratings and tranche.ratings[0].rating == "NR":
                continue  # Skip residual for interest

            interest_due = tranche.period_interest(index_rate)
            interest_paid = min(available_interest, interest_due)
            cf.tranche_interest[tranche.name] = interest_paid
            available_interest -= interest_paid

            # Track in tranche flows
            self.tranche_flows[tranche.name].periods.append({
                'period': period,
                'beginning_balance': self.tranche_balances[tranche.name],
                'interest': interest_paid,
                'principal': 0,  # Updated below
            })

        # 3. Check triggers
        total_rated = sum(
            bal for name, bal in self.tranche_balances.items()
            if any(t.name == name and t.ratings and t.ratings[0].rating != "NR" for t in self.deal.tranches)
        )
        cf.oc_ratio = (cf.ending_balance / total_rated * 100) if total_rated > 0 else 0

        total_interest_expense = sum(cf.tranche_interest.values())
        cf.ic_ratio = (cf.interest_income / total_interest_expense) if total_interest_expense > 0 else 0

        # Evaluate triggers
        triggers_breached = False
        for trigger in self.deal.triggers:
            if trigger.test_type == "oc":
                passed = cf.oc_ratio >= trigger.threshold
            elif trigger.test_type == "ic":
                passed = cf.ic_ratio >= trigger.threshold
            elif trigger.test_type == "cnl":
                passed = cf.cnl_rate <= trigger.threshold
            else:
                passed = True
            cf.trigger_status[trigger.name] = passed
            if not passed:
                triggers_breached = True

        # 4. Principal distribution (sequential if triggers breached or sequential deal)
        is_sequential = (
            self.deal.payment_priority == "Sequential" or
            triggers_breached
        )

        if is_sequential:
            # Pay tranches in order until each is paid off
            for tranche in self.deal.tranches:
                if available_principal <= 0:
                    break
                current_bal = self.tranche_balances[tranche.name]
                prin_paid = min(available_principal, current_bal)
                cf.tranche_principal[tranche.name] = prin_paid
                self.tranche_balances[tranche.name] -= prin_paid
                available_principal -= prin_paid

                # Update tranche flow
                if self.tranche_flows[tranche.name].periods:
                    self.tranche_flows[tranche.name].periods[-1]['principal'] = prin_paid
        else:
            # Pro-rata (simplified)
            total_balance = sum(self.tranche_balances.values())
            for tranche in self.deal.tranches:
                if total_balance <= 0:
                    break
                current_bal = self.tranche_balances[tranche.name]
                pro_rata_share = current_bal / total_balance
                prin_paid = min(available_principal * pro_rata_share, current_bal)
                cf.tranche_principal[tranche.name] = prin_paid
                self.tranche_balances[tranche.name] -= prin_paid

                if self.tranche_flows[tranche.name].periods:
                    self.tranche_flows[tranche.name].periods[-1]['principal'] = prin_paid

        # 5. Update tranche balances in flow
        for name, bal in self.tranche_balances.items():
            cf.tranche_balance[name] = bal

        # 6. Excess spread / residual
        cf.excess_spread = available_interest
        cf.residual = available_principal

        return cf

    def get_summary_dataframe(self) -> pd.DataFrame:
        """Convert projection to DataFrame"""
        data = []
        for cf in self.period_flows:
            row = {
                'Period': cf.period,
                'Collateral_Beg': cf.beginning_balance,
                'Scheduled_Prin': cf.scheduled_principal,
                'Prepayments': cf.prepayments,
                'Defaults': cf.defaults,
                'Recoveries': cf.recoveries,
                'Losses': cf.losses,
                'Collateral_End': cf.ending_balance,
                'Interest_Income': cf.interest_income,
                'CNL_%': cf.cnl_rate,
                'OC_%': cf.oc_ratio,
                'IC_x': cf.ic_ratio,
                'Excess_Spread': cf.excess_spread,
            }

            # Add tranche columns
            for name in self.tranche_balances.keys():
                row[f'{name}_Interest'] = cf.tranche_interest.get(name, 0)
                row[f'{name}_Principal'] = cf.tranche_principal.get(name, 0)
                row[f'{name}_Balance'] = cf.tranche_balance.get(name, 0)

            data.append(row)

        return pd.DataFrame(data)

    def get_tranche_summary(self) -> pd.DataFrame:
        """Get summary metrics for each tranche"""
        data = []
        for tranche in self.deal.tranches:
            tf = self.tranche_flows[tranche.name]
            initial_bal = tranche.current_balance
            final_bal = self.tranche_balances[tranche.name]

            # Calculate actual WAL
            weighted_time = 0
            total_prin = 0
            for p in tf.periods:
                prin = p.get('principal', 0)
                weighted_time += prin * p.get('period', 0) / 12
                total_prin += prin

            wal = weighted_time / total_prin if total_prin > 0 else 0

            data.append({
                'Tranche': tranche.name,
                'Original_Balance': initial_bal,
                'Final_Balance': final_bal,
                'Principal_Paid': initial_bal - final_bal,
                'Interest_Paid': tf.total_interest,
                'WAL': round(wal, 2),
                'Paid_Down_%': round((initial_bal - final_bal) / initial_bal * 100, 1) if initial_bal > 0 else 0,
            })

        return pd.DataFrame(data)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_base_scenario(cpr: float = 0.15, cdr: float = 0.03, recovery: float = 0.40,
                         index_rate: float = 0.0433, months: int = 60) -> ScenarioAssumptions:
    """Create a basic scenario with constant assumptions"""
    return ScenarioAssumptions(
        name="Base Case",
        prepayment=PrepaymentAssumption(
            model=PrepaymentModel.CONSTANT,
            base_cpr=cpr
        ),
        default=DefaultAssumption(
            model=DefaultModel.CONSTANT,
            base_cdr=cdr,
            recovery_rate=recovery
        ),
        index_rate=index_rate,
        projection_months=months
    )


def create_stress_scenario(cpr: float = 0.08, cdr: float = 0.10, recovery: float = 0.30,
                           index_rate: float = 0.0550, months: int = 60) -> ScenarioAssumptions:
    """Create a stress scenario"""
    return ScenarioAssumptions(
        name="Stress Case",
        prepayment=PrepaymentAssumption(
            model=PrepaymentModel.CONSTANT,
            base_cpr=cpr
        ),
        default=DefaultAssumption(
            model=DefaultModel.FRONT_LOADED,  # Defaults come faster in stress
            base_cdr=cdr,
            recovery_rate=recovery,
            peak_month=18
        ),
        index_rate=index_rate,
        projection_months=months
    )


def calculate_breakeven_cdr(deal, target_tranche: str, recovery: float = 0.40,
                            max_cdr: float = 0.50, tolerance: float = 0.001) -> float:
    """Binary search for break-even CDR where tranche takes first loss"""
    low, high = 0.0, max_cdr

    while high - low > tolerance:
        mid = (low + high) / 2

        scenario = create_base_scenario(cdr=mid, recovery=recovery)
        engine = CashFlowEngine(deal, scenario)
        engine.run_projection()

        # Check if tranche got full principal
        original = next(t.current_balance for t in deal.tranches if t.name == target_tranche)
        final = engine.tranche_balances[target_tranche]
        principal_loss = original - (original - final) - engine.tranche_flows[target_tranche].total_principal

        # If tranche didn't get all principal back, CDR too high
        if final > 0.01 * original:  # Some principal remains unpaid
            high = mid
        else:
            low = mid

    return round((low + high) / 2, 4)
