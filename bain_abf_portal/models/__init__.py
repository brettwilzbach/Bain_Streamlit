"""
ABF Portal Models
"""

from .deal_structure import (
    DealStructure,
    Tranche,
    CollateralPool,
    TriggerTest,
    Fee,
    ReserveAccount,
    Rating,
    RatingAgency,
    CollateralType,
    PaymentPriority,
    DEAL_TEMPLATES,
    create_acmat_2025_4,
    create_subprime_auto_template,
    create_clo_template,
)

from .cashflow_engine import (
    CashFlowEngine,
    ScenarioAssumptions,
    PrepaymentAssumption,
    DefaultAssumption,
    PrepaymentModel,
    DefaultModel,
    PeriodCashFlow,
    TrancheCashFlow,
    create_base_scenario,
    create_stress_scenario,
    calculate_breakeven_cdr,
)

from .bloomberg_client import (
    BloombergMCPClient,
    BloombergConfig,
    BloombergSpreadProvider,
    get_bloomberg_client,
    get_spread_provider,
)

from .data_fetcher import (
    FREDClient,
    SpreadEstimator,
    SpreadData,
    UnifiedDataProvider,
    get_unified_provider,
    get_current_sofr,
    get_treasury_curve,
    get_corporate_spreads,
)

__all__ = [
    # Deal structure
    'DealStructure',
    'Tranche',
    'CollateralPool',
    'TriggerTest',
    'Fee',
    'ReserveAccount',
    'Rating',
    'RatingAgency',
    'CollateralType',
    'PaymentPriority',
    'DEAL_TEMPLATES',
    # Cash flow engine
    'CashFlowEngine',
    'ScenarioAssumptions',
    'PrepaymentAssumption',
    'DefaultAssumption',
    'PrepaymentModel',
    'DefaultModel',
    'create_base_scenario',
    'create_stress_scenario',
    'calculate_breakeven_cdr',
    # Bloomberg integration
    'BloombergMCPClient',
    'BloombergConfig',
    'BloombergSpreadProvider',
    'get_bloomberg_client',
    'get_spread_provider',
    # Data fetching
    'FREDClient',
    'SpreadEstimator',
    'SpreadData',
    'UnifiedDataProvider',
    'get_unified_provider',
    'get_current_sofr',
    'get_treasury_curve',
    'get_corporate_spreads',
]
