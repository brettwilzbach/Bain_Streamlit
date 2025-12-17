"""
Deal Structure Models
Proper data classes for ABS/CLO deal structures with validation
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal
from enum import Enum
import json


class CollateralType(Enum):
    PRIME_AUTO = "Prime Auto"
    SUBPRIME_AUTO = "Subprime Auto"
    CONSUMER = "Consumer"
    EQUIPMENT = "Equipment"
    CLO = "CLO"
    ESOTERIC = "Esoteric"
    CUSTOM = "Custom"


class PaymentPriority(Enum):
    SEQUENTIAL = "Sequential"  # Senior paid first, then mezz, then sub
    PRO_RATA = "Pro Rata"      # All tranches paid proportionally
    MODIFIED_PRO_RATA = "Modified Pro Rata"  # Pro rata until trigger, then sequential


class RatingAgency(Enum):
    SP = "S&P"
    MOODYS = "Moody's"
    FITCH = "Fitch"
    KBRA = "KBRA"
    DBRS = "DBRS"


@dataclass
class Rating:
    """Credit rating with agency"""
    agency: RatingAgency
    rating: str  # AAA, Aa1, BBB+, etc.

    def numeric_score(self) -> int:
        """Convert rating to numeric score for comparison (higher = better)"""
        sp_scale = {
            'AAA': 21, 'AA+': 20, 'AA': 19, 'AA-': 18,
            'A+': 17, 'A': 16, 'A-': 15,
            'BBB+': 14, 'BBB': 13, 'BBB-': 12,
            'BB+': 11, 'BB': 10, 'BB-': 9,
            'B+': 8, 'B': 7, 'B-': 6,
            'CCC+': 5, 'CCC': 4, 'CCC-': 3,
            'CC': 2, 'C': 1, 'D': 0, 'NR': -1
        }
        return sp_scale.get(self.rating, -1)


@dataclass
class Tranche:
    """Individual tranche in an ABS/CLO structure"""
    name: str                           # Class A-1, Class B, etc.
    original_balance: float             # Initial balance at closing
    current_balance: float              # Current outstanding balance
    coupon_type: Literal["floating", "fixed"]
    spread: float                       # Spread over index (for floating) or fixed coupon
    index: str = "SOFR"                 # Reference rate
    floor: float = 0.0                  # Interest rate floor
    ratings: List[Rating] = field(default_factory=list)
    payment_frequency: int = 12         # Payments per year (12 = monthly)
    is_io: bool = False                 # Interest-only tranche
    is_po: bool = False                 # Principal-only tranche

    @property
    def factor(self) -> float:
        """Current factor (current/original balance)"""
        return self.current_balance / self.original_balance if self.original_balance > 0 else 0

    def all_in_rate(self, index_rate: float) -> float:
        """Calculate all-in coupon rate"""
        if self.coupon_type == "fixed":
            return self.spread
        else:
            return max(index_rate, self.floor) + self.spread

    def period_interest(self, index_rate: float) -> float:
        """Calculate interest due for one period"""
        rate = self.all_in_rate(index_rate)
        return self.current_balance * rate / self.payment_frequency


@dataclass
class TriggerTest:
    """Structural trigger/test definition"""
    name: str
    test_type: Literal["oc", "ic", "cnl", "dscr", "delinquency", "excess_spread"]
    threshold: float
    comparison: Literal[">=", "<=", ">", "<"]
    consequence: str  # What happens when breached
    cure_periods: int = 0  # Periods to cure before consequence
    currently_breached: bool = False
    periods_in_breach: int = 0

    def evaluate(self, current_value: float) -> bool:
        """Check if test passes (True) or fails (False)"""
        if self.comparison == ">=":
            return current_value >= self.threshold
        elif self.comparison == "<=":
            return current_value <= self.threshold
        elif self.comparison == ">":
            return current_value > self.threshold
        elif self.comparison == "<":
            return current_value < self.threshold
        return False


@dataclass
class CollateralPool:
    """Collateral pool characteristics"""
    original_balance: float
    current_balance: float
    collateral_type: CollateralType
    weighted_average_coupon: float      # WAC
    weighted_average_maturity: float    # WAM in months
    weighted_average_life: float        # WAL in years
    weighted_average_fico: Optional[float] = None  # For consumer/auto
    weighted_average_ltv: Optional[float] = None   # For auto/mortgage
    geographic_concentration: Dict[str, float] = field(default_factory=dict)
    obligor_concentration: Dict[str, float] = field(default_factory=dict)

    # Performance metrics
    current_delinquency_30: float = 0.0
    current_delinquency_60: float = 0.0
    current_delinquency_90: float = 0.0
    cumulative_net_loss: float = 0.0
    cumulative_gross_loss: float = 0.0
    cumulative_recoveries: float = 0.0

    @property
    def factor(self) -> float:
        return self.current_balance / self.original_balance if self.original_balance > 0 else 0

    @property
    def cnl_rate(self) -> float:
        """CNL as percentage of original balance"""
        return (self.cumulative_net_loss / self.original_balance * 100) if self.original_balance > 0 else 0


@dataclass
class ReserveAccount:
    """Reserve/liquidity account"""
    name: str
    target_balance: float               # Required amount
    current_balance: float
    floor: float = 0.0                  # Minimum balance
    funded_at_close: bool = True
    replenishment_priority: int = 99    # Where in waterfall to replenish

    @property
    def is_at_target(self) -> bool:
        return self.current_balance >= self.target_balance


@dataclass
class Fee:
    """Fee in the waterfall"""
    name: str
    rate: float                         # Annual rate as decimal
    basis: Literal["collateral", "notes", "fixed"]
    fixed_amount: float = 0.0           # If basis is "fixed"
    priority: int = 1                   # Payment priority (lower = higher priority)
    is_subordinated: bool = False       # Senior vs. subordinated fee

    def calculate(self, collateral_balance: float, notes_balance: float, periods_per_year: int = 12) -> float:
        """Calculate fee for one period"""
        if self.basis == "collateral":
            return collateral_balance * self.rate / periods_per_year
        elif self.basis == "notes":
            return notes_balance * self.rate / periods_per_year
        else:
            return self.fixed_amount / periods_per_year


@dataclass
class DealStructure:
    """Complete ABS/CLO deal structure"""
    deal_name: str
    issuer: str
    pricing_date: str
    closing_date: str
    collateral: CollateralPool
    tranches: List[Tranche]
    triggers: List[TriggerTest]
    fees: List[Fee]
    reserve_accounts: List[ReserveAccount] = field(default_factory=list)

    # Structural features
    payment_priority: PaymentPriority = PaymentPriority.SEQUENTIAL
    payment_frequency: int = 12         # Monthly
    reinvestment_period: int = 0        # Months (CLOs have reinvestment periods)
    call_date: Optional[str] = None
    legal_final: Optional[str] = None

    # Deal metadata
    bookrunner: str = ""
    format: str = "144A"
    shelf: str = ""
    series: str = ""

    @property
    def total_notes(self) -> float:
        """Sum of all tranche balances"""
        return sum(t.current_balance for t in self.tranches)

    @property
    def rated_notes(self) -> float:
        """Sum of rated tranches (excludes residual/equity)"""
        return sum(t.current_balance for t in self.tranches
                   if t.ratings and t.ratings[0].rating != "NR")

    def credit_enhancement(self, tranche_name: str) -> float:
        """Calculate credit enhancement for a specific tranche"""
        # Find tranche index
        tranche_idx = None
        for i, t in enumerate(self.tranches):
            if t.name == tranche_name:
                tranche_idx = i
                break

        if tranche_idx is None:
            return 0.0

        # CE = subordination below + OC
        subordination = sum(t.current_balance for t in self.tranches[tranche_idx + 1:])
        excess_collateral = self.collateral.current_balance - self.total_notes

        ce = (subordination + excess_collateral) / self.collateral.current_balance * 100
        return ce

    def overcollateralization(self, through_tranche: Optional[str] = None) -> float:
        """Calculate OC ratio"""
        if through_tranche:
            # OC through specific tranche
            notes_through = 0
            for t in self.tranches:
                notes_through += t.current_balance
                if t.name == through_tranche:
                    break
            return (self.collateral.current_balance / notes_through * 100) if notes_through > 0 else 0
        else:
            # OC for all rated notes
            return (self.collateral.current_balance / self.rated_notes * 100) if self.rated_notes > 0 else 0

    def interest_coverage(self, index_rate: float) -> float:
        """Calculate interest coverage ratio"""
        # Interest income from collateral
        interest_income = self.collateral.current_balance * self.collateral.weighted_average_coupon / self.payment_frequency

        # Interest expense on notes
        interest_expense = sum(t.period_interest(index_rate) for t in self.tranches if not t.is_po)

        return (interest_income / interest_expense) if interest_expense > 0 else 0

    def dscr(self, index_rate: float, scheduled_principal: float) -> float:
        """Calculate debt service coverage ratio"""
        # Income available for debt service
        interest_income = self.collateral.current_balance * self.collateral.weighted_average_coupon / self.payment_frequency

        # Total debt service
        interest_expense = sum(t.period_interest(index_rate) for t in self.tranches if not t.is_po)
        debt_service = interest_expense + scheduled_principal

        return (interest_income / debt_service) if debt_service > 0 else 0

    def evaluate_triggers(self, index_rate: float, scheduled_principal: float = 0) -> Dict[str, bool]:
        """Evaluate all triggers and return pass/fail status"""
        results = {}

        for trigger in self.triggers:
            if trigger.test_type == "oc":
                current_value = self.overcollateralization()
            elif trigger.test_type == "ic":
                current_value = self.interest_coverage(index_rate)
            elif trigger.test_type == "cnl":
                current_value = self.collateral.cnl_rate
            elif trigger.test_type == "dscr":
                current_value = self.dscr(index_rate, scheduled_principal)
            elif trigger.test_type == "delinquency":
                current_value = self.collateral.current_delinquency_60
            elif trigger.test_type == "excess_spread":
                # Simplified - would need more detailed calc
                current_value = (self.collateral.weighted_average_coupon -
                                sum(t.spread for t in self.tranches) / len(self.tranches)) * 100
            else:
                current_value = 0

            passed = trigger.evaluate(current_value)
            results[trigger.name] = {
                'passed': passed,
                'current_value': current_value,
                'threshold': trigger.threshold,
                'consequence': trigger.consequence if not passed else None
            }

        return results

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage"""
        return {
            'deal_name': self.deal_name,
            'issuer': self.issuer,
            'pricing_date': self.pricing_date,
            'closing_date': self.closing_date,
            'collateral': {
                'original_balance': self.collateral.original_balance,
                'current_balance': self.collateral.current_balance,
                'collateral_type': self.collateral.collateral_type.value,
                'wac': self.collateral.weighted_average_coupon,
                'wam': self.collateral.weighted_average_maturity,
                'wal': self.collateral.weighted_average_life,
            },
            'tranches': [
                {
                    'name': t.name,
                    'original_balance': t.original_balance,
                    'current_balance': t.current_balance,
                    'coupon_type': t.coupon_type,
                    'spread': t.spread,
                    'ratings': [{'agency': r.agency.value, 'rating': r.rating} for r in t.ratings]
                }
                for t in self.tranches
            ],
            'triggers': [
                {
                    'name': tr.name,
                    'test_type': tr.test_type,
                    'threshold': tr.threshold,
                    'comparison': tr.comparison,
                    'consequence': tr.consequence
                }
                for tr in self.triggers
            ],
            'bookrunner': self.bookrunner,
            'format': self.format
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DealStructure':
        """Deserialize from dictionary"""
        collateral = CollateralPool(
            original_balance=data['collateral']['original_balance'],
            current_balance=data['collateral']['current_balance'],
            collateral_type=CollateralType(data['collateral']['collateral_type']),
            weighted_average_coupon=data['collateral']['wac'],
            weighted_average_maturity=data['collateral']['wam'],
            weighted_average_life=data['collateral']['wal']
        )

        tranches = []
        for t in data['tranches']:
            ratings = [Rating(RatingAgency(r['agency']), r['rating']) for r in t.get('ratings', [])]
            tranches.append(Tranche(
                name=t['name'],
                original_balance=t['original_balance'],
                current_balance=t['current_balance'],
                coupon_type=t['coupon_type'],
                spread=t['spread'],
                ratings=ratings
            ))

        triggers = []
        for tr in data.get('triggers', []):
            triggers.append(TriggerTest(
                name=tr['name'],
                test_type=tr['test_type'],
                threshold=tr['threshold'],
                comparison=tr['comparison'],
                consequence=tr['consequence']
            ))

        fees = []  # Would need to be in data

        return cls(
            deal_name=data['deal_name'],
            issuer=data['issuer'],
            pricing_date=data['pricing_date'],
            closing_date=data.get('closing_date', data['pricing_date']),
            collateral=collateral,
            tranches=tranches,
            triggers=triggers,
            fees=fees,
            bookrunner=data.get('bookrunner', ''),
            format=data.get('format', '144A')
        )


# ============================================================================
# PRE-BUILT DEAL TEMPLATES
# ============================================================================

def create_acmat_2025_4() -> DealStructure:
    """Create the actual ACMAT 2025-4 deal structure"""
    collateral = CollateralPool(
        original_balance=161_300_000,
        current_balance=161_300_000,
        collateral_type=CollateralType.SUBPRIME_AUTO,
        weighted_average_coupon=0.24,  # ~24% APR typical for BHPH
        weighted_average_maturity=42,   # ~3.5 years
        weighted_average_life=2.5,
        weighted_average_fico=550,      # Deep subprime
        weighted_average_ltv=1.15       # Negative equity common
    )

    tranches = [
        Tranche(
            name="Class A",
            original_balance=128_200_000,
            current_balance=128_200_000,
            coupon_type="floating",
            spread=0.0240,  # +240bps
            index="SOFR",
            ratings=[Rating(RatingAgency.SP, "A")]
        ),
        Tranche(
            name="Class B",
            original_balance=33_100_000,
            current_balance=33_100_000,
            coupon_type="floating",
            spread=0.0600,  # +600bps
            index="SOFR",
            ratings=[Rating(RatingAgency.SP, "BBB")]
        ),
    ]

    triggers = [
        TriggerTest(
            name="OC Test",
            test_type="oc",
            threshold=110.0,
            comparison=">=",
            consequence="Trap cash to pay down Class A"
        ),
        TriggerTest(
            name="CNL Trigger",
            test_type="cnl",
            threshold=25.0,  # Estimated
            comparison="<=",
            consequence="Switch to sequential pay, turbo Class A"
        ),
        TriggerTest(
            name="Delinquency Trigger",
            test_type="delinquency",
            threshold=10.0,
            comparison="<=",
            consequence="Increase reserve account target"
        ),
    ]

    fees = [
        Fee(name="Servicer Fee", rate=0.04, basis="collateral", priority=1),  # 4% typical for BHPH
        Fee(name="Trustee Fee", rate=0.0002, basis="collateral", priority=2),
        Fee(name="Admin Fee", rate=0.0005, basis="collateral", priority=3),
    ]

    reserve = ReserveAccount(
        name="Reserve Account",
        target_balance=1_613_000,  # ~1% of deal
        current_balance=1_613_000
    )

    return DealStructure(
        deal_name="ACMAT 2025-4",
        issuer="America's Car-Mart",
        pricing_date="2025-12-10",
        closing_date="2025-12-17",
        collateral=collateral,
        tranches=tranches,
        triggers=triggers,
        fees=fees,
        reserve_accounts=[reserve],
        payment_priority=PaymentPriority.SEQUENTIAL,
        bookrunner="Deutsche Bank",
        format="144A",
        shelf="ACM Auto Trust",
        series="2025-4"
    )


def create_subprime_auto_template() -> DealStructure:
    """Generic subprime auto ABS template"""
    collateral = CollateralPool(
        original_balance=500_000_000,
        current_balance=500_000_000,
        collateral_type=CollateralType.SUBPRIME_AUTO,
        weighted_average_coupon=0.18,
        weighted_average_maturity=48,
        weighted_average_life=2.8,
        weighted_average_fico=580,
        weighted_average_ltv=1.05
    )

    tranches = [
        Tranche(
            name="Class A-1",
            original_balance=100_000_000,
            current_balance=100_000_000,
            coupon_type="floating",
            spread=0.0065,
            ratings=[Rating(RatingAgency.SP, "AAA")]
        ),
        Tranche(
            name="Class A-2",
            original_balance=200_000_000,
            current_balance=200_000_000,
            coupon_type="floating",
            spread=0.0085,
            ratings=[Rating(RatingAgency.SP, "AAA")]
        ),
        Tranche(
            name="Class B",
            original_balance=75_000_000,
            current_balance=75_000_000,
            coupon_type="floating",
            spread=0.0150,
            ratings=[Rating(RatingAgency.SP, "AA")]
        ),
        Tranche(
            name="Class C",
            original_balance=50_000_000,
            current_balance=50_000_000,
            coupon_type="floating",
            spread=0.0225,
            ratings=[Rating(RatingAgency.SP, "A")]
        ),
        Tranche(
            name="Class D",
            original_balance=37_500_000,
            current_balance=37_500_000,
            coupon_type="floating",
            spread=0.0350,
            ratings=[Rating(RatingAgency.SP, "BBB")]
        ),
        Tranche(
            name="Class E",
            original_balance=25_000_000,
            current_balance=25_000_000,
            coupon_type="floating",
            spread=0.0550,
            ratings=[Rating(RatingAgency.SP, "BB")]
        ),
        Tranche(
            name="Residual",
            original_balance=12_500_000,
            current_balance=12_500_000,
            coupon_type="floating",
            spread=0.0,
            ratings=[Rating(RatingAgency.SP, "NR")]
        ),
    ]

    triggers = [
        TriggerTest(name="Senior OC Test", test_type="oc", threshold=115.0, comparison=">=",
                   consequence="Trap cash, pay down senior"),
        TriggerTest(name="Mezz OC Test", test_type="oc", threshold=108.0, comparison=">=",
                   consequence="Trap cash, pay down through Class D"),
        TriggerTest(name="IC Test", test_type="ic", threshold=1.50, comparison=">=",
                   consequence="Redirect interest to senior"),
        TriggerTest(name="CNL Trigger - Step 1", test_type="cnl", threshold=12.0, comparison="<=",
                   consequence="Switch to sequential pay"),
        TriggerTest(name="CNL Trigger - Step 2", test_type="cnl", threshold=18.0, comparison="<=",
                   consequence="Turbo senior amortization"),
        TriggerTest(name="60+ Day Delinquency", test_type="delinquency", threshold=8.0, comparison="<=",
                   consequence="Increase reserve target"),
    ]

    fees = [
        Fee(name="Servicer Fee", rate=0.0100, basis="collateral", priority=1),
        Fee(name="Backup Servicer Fee", rate=0.0005, basis="collateral", priority=2),
        Fee(name="Trustee Fee", rate=0.0002, basis="notes", priority=3),
        Fee(name="Admin Fee", rate=0.0003, basis="notes", priority=4),
    ]

    return DealStructure(
        deal_name="Subprime Auto Template",
        issuer="[Issuer]",
        pricing_date="",
        closing_date="",
        collateral=collateral,
        tranches=tranches,
        triggers=triggers,
        fees=fees,
        payment_priority=PaymentPriority.SEQUENTIAL
    )


def create_clo_template() -> DealStructure:
    """Generic CLO template"""
    collateral = CollateralPool(
        original_balance=400_000_000,
        current_balance=400_000_000,
        collateral_type=CollateralType.CLO,
        weighted_average_coupon=0.0950,  # SOFR + ~400bps average
        weighted_average_maturity=60,     # 5 year WAM
        weighted_average_life=4.5,
    )

    tranches = [
        Tranche(
            name="Class A",
            original_balance=248_000_000,  # 62%
            current_balance=248_000_000,
            coupon_type="floating",
            spread=0.0138,
            ratings=[Rating(RatingAgency.SP, "AAA"), Rating(RatingAgency.MOODYS, "Aaa")]
        ),
        Tranche(
            name="Class B",
            original_balance=40_000_000,   # 10%
            current_balance=40_000_000,
            coupon_type="floating",
            spread=0.0190,
            ratings=[Rating(RatingAgency.SP, "AA")]
        ),
        Tranche(
            name="Class C",
            original_balance=28_000_000,   # 7%
            current_balance=28_000_000,
            coupon_type="floating",
            spread=0.0260,
            ratings=[Rating(RatingAgency.SP, "A")]
        ),
        Tranche(
            name="Class D",
            original_balance=24_000_000,   # 6%
            current_balance=24_000_000,
            coupon_type="floating",
            spread=0.0385,
            ratings=[Rating(RatingAgency.SP, "BBB")]
        ),
        Tranche(
            name="Class E",
            original_balance=20_000_000,   # 5%
            current_balance=20_000_000,
            coupon_type="floating",
            spread=0.0675,
            ratings=[Rating(RatingAgency.SP, "BB")]
        ),
        Tranche(
            name="Equity",
            original_balance=40_000_000,   # 10%
            current_balance=40_000_000,
            coupon_type="floating",
            spread=0.0,
            ratings=[Rating(RatingAgency.SP, "NR")]
        ),
    ]

    triggers = [
        TriggerTest(name="Class A/B OC Test", test_type="oc", threshold=120.0, comparison=">=",
                   consequence="Trap excess interest, pay down Class A"),
        TriggerTest(name="Class C OC Test", test_type="oc", threshold=112.0, comparison=">=",
                   consequence="Trap excess interest"),
        TriggerTest(name="Class D OC Test", test_type="oc", threshold=107.0, comparison=">=",
                   consequence="Trap excess interest"),
        TriggerTest(name="Class A/B IC Test", test_type="ic", threshold=1.20, comparison=">=",
                   consequence="Redirect interest to senior"),
        TriggerTest(name="Class C IC Test", test_type="ic", threshold=1.15, comparison=">=",
                   consequence="Redirect interest"),
        TriggerTest(name="Class D IC Test", test_type="ic", threshold=1.10, comparison=">=",
                   consequence="Redirect interest"),
    ]

    fees = [
        Fee(name="Senior Management Fee", rate=0.0015, basis="collateral", priority=1),
        Fee(name="Trustee Fee", rate=0.0002, basis="collateral", priority=2),
        Fee(name="Admin Fee", rate=0.0003, basis="collateral", priority=3),
        Fee(name="Subordinated Management Fee", rate=0.0035, basis="collateral", priority=99, is_subordinated=True),
    ]

    return DealStructure(
        deal_name="CLO Template",
        issuer="[Manager]",
        pricing_date="",
        closing_date="",
        collateral=collateral,
        tranches=tranches,
        triggers=triggers,
        fees=fees,
        payment_priority=PaymentPriority.SEQUENTIAL,
        reinvestment_period=48  # 4 year reinvestment period
    )


DEAL_TEMPLATES = {
    "ACMAT 2025-4": create_acmat_2025_4,
    "Subprime Auto": create_subprime_auto_template,
    "CLO": create_clo_template,
}
