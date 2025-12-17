"""
Deal Database Module
Store and manage ABS/CLO deal data with persistence
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd
from pathlib import Path


@dataclass
class DealTranche:
    """Individual tranche in a deal"""
    tranche_class: str
    size: float          # $M
    rating: str
    spread: int          # bps
    wal: float           # years
    credit_enhancement: float  # %
    coupon: Optional[float] = None  # Fixed coupon if applicable
    yield_val: Optional[float] = None


@dataclass
class DealRecord:
    """Complete deal record"""
    deal_name: str
    issuer: str
    collateral_type: str
    total_size: float     # $M
    pricing_date: str     # YYYY-MM-DD
    bookrunner: str
    format: str           # 144A, Reg S, etc.
    tranches: List[DealTranche]

    # Optional metadata
    shelf: str = ""
    series: str = ""
    closing_date: str = ""
    notes: str = ""
    source: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'deal_name': self.deal_name,
            'issuer': self.issuer,
            'collateral_type': self.collateral_type,
            'total_size': self.total_size,
            'pricing_date': self.pricing_date,
            'bookrunner': self.bookrunner,
            'format': self.format,
            'shelf': self.shelf,
            'series': self.series,
            'closing_date': self.closing_date,
            'notes': self.notes,
            'source': self.source,
            'tranches': [asdict(t) for t in self.tranches]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DealRecord':
        """Create from dictionary"""
        tranches = [DealTranche(**t) for t in data.get('tranches', [])]
        return cls(
            deal_name=data['deal_name'],
            issuer=data['issuer'],
            collateral_type=data['collateral_type'],
            total_size=data['total_size'],
            pricing_date=data['pricing_date'],
            bookrunner=data['bookrunner'],
            format=data['format'],
            shelf=data.get('shelf', ''),
            series=data.get('series', ''),
            closing_date=data.get('closing_date', ''),
            notes=data.get('notes', ''),
            source=data.get('source', ''),
            tranches=tranches
        )


class DealDatabase:
    """Simple JSON-based deal database"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default to data folder in portal directory
            db_path = Path(__file__).parent.parent / "data" / "deals.json"

        self.db_path = Path(db_path)
        self.deals: Dict[str, DealRecord] = {}
        self._load()

    def _load(self):
        """Load deals from JSON file"""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r') as f:
                    data = json.load(f)
                    self.deals = {k: DealRecord.from_dict(v) for k, v in data.items()}
            except Exception as e:
                print(f"Error loading database: {e}")
                self.deals = {}
        else:
            self.deals = {}
            self._init_sample_data()

    def _save(self):
        """Save deals to JSON file"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.db_path, 'w') as f:
            data = {k: v.to_dict() for k, v in self.deals.items()}
            json.dump(data, f, indent=2)

    def _init_sample_data(self):
        """Initialize with sample deal data"""
        sample_deals = [
            DealRecord(
                deal_name="ACMAT 2025-4",
                issuer="America's Car-Mart",
                collateral_type="Subprime Auto",
                total_size=161.3,
                pricing_date="2025-12-10",
                bookrunner="Deutsche Bank",
                format="144A",
                shelf="ACM Auto Trust",
                series="2025-4",
                notes="BHPH originator, 9th ABS issuance",
                tranches=[
                    DealTranche("A", 128.2, "A", 240, 1.13, 57.1, 5.87, 5.944),
                    DealTranche("B", 33.1, "BBB", 600, 3.14, 45.5, 8.42, 9.575),
                ]
            ),
            DealRecord(
                deal_name="DRIVE 2025-5",
                issuer="Santander Drive",
                collateral_type="Subprime Auto",
                total_size=1250.0,
                pricing_date="2025-12-08",
                bookrunner="Santander",
                format="144A",
                shelf="Santander Drive Auto",
                series="2025-5",
                tranches=[
                    DealTranche("A-1", 350.0, "AAA", 65, 0.52, 52.0),
                    DealTranche("A-2", 500.0, "AAA", 85, 1.85, 52.0),
                    DealTranche("B", 150.0, "AA", 125, 2.50, 40.0),
                    DealTranche("C", 100.0, "A", 175, 3.20, 32.0),
                    DealTranche("D", 75.0, "BBB", 300, 3.80, 26.0),
                    DealTranche("E", 75.0, "BB", 500, 4.10, 20.0),
                ]
            ),
            DealRecord(
                deal_name="WLAKE 2025-4",
                issuer="Westlake Financial",
                collateral_type="Subprime Auto",
                total_size=987.5,
                pricing_date="2025-12-05",
                bookrunner="J.P. Morgan",
                format="144A",
                shelf="Westlake Auto Receivables",
                series="2025-4",
                tranches=[
                    DealTranche("A-1", 275.0, "AAA", 60, 0.48, 54.0),
                    DealTranche("A-2", 400.0, "AAA", 80, 1.75, 54.0),
                    DealTranche("B", 125.0, "AA", 115, 2.40, 41.0),
                    DealTranche("C", 87.5, "A", 165, 3.10, 32.0),
                    DealTranche("D", 62.5, "BBB", 275, 3.70, 26.0),
                    DealTranche("E", 37.5, "BB", 475, 4.00, 22.0),
                ]
            ),
            DealRecord(
                deal_name="CARMX 2025-4",
                issuer="CarMax Auto",
                collateral_type="Prime Auto",
                total_size=1500.0,
                pricing_date="2025-12-03",
                bookrunner="BofA Securities",
                format="144A",
                shelf="CarMax Auto Owner Trust",
                series="2025-4",
                tranches=[
                    DealTranche("A-1", 450.0, "AAA", 35, 0.45, 8.0),
                    DealTranche("A-2", 750.0, "AAA", 50, 1.65, 8.0),
                    DealTranche("A-3", 200.0, "AAA", 55, 2.80, 8.0),
                    DealTranche("B", 50.0, "AA", 85, 3.20, 5.0),
                    DealTranche("C", 50.0, "A", 110, 3.50, 2.0),
                ]
            ),
            DealRecord(
                deal_name="DLLMT 2025-3",
                issuer="De Lage Landen",
                collateral_type="Equipment",
                total_size=650.0,
                pricing_date="2025-11-28",
                bookrunner="Citi",
                format="144A",
                shelf="DLL Trust",
                series="2025-3",
                notes="Agricultural and construction equipment",
                tranches=[
                    DealTranche("A-1", 200.0, "AAA", 45, 0.55, 12.0),
                    DealTranche("A-2", 350.0, "AAA", 60, 2.10, 12.0),
                    DealTranche("B", 60.0, "AA", 95, 2.80, 7.0),
                    DealTranche("C", 40.0, "A", 135, 3.20, 3.0),
                ]
            ),
            DealRecord(
                deal_name="MFGLN 2025-2",
                issuer="Marlette Funding",
                collateral_type="Consumer",
                total_size=425.0,
                pricing_date="2025-11-25",
                bookrunner="Goldman Sachs",
                format="144A",
                shelf="Marlette Funding Trust",
                series="2025-2",
                notes="Personal loans originated via Best Egg",
                tranches=[
                    DealTranche("A", 300.0, "AAA", 95, 0.85, 35.0),
                    DealTranche("B", 60.0, "A", 185, 1.20, 21.0),
                    DealTranche("C", 40.0, "BBB", 350, 1.45, 12.0),
                    DealTranche("D", 25.0, "BB", 575, 1.65, 6.0),
                ]
            ),
            DealRecord(
                deal_name="OAKCL 2025-4",
                issuer="Oak Hill Advisors",
                collateral_type="CLO",
                total_size=500.0,
                pricing_date="2025-12-01",
                bookrunner="Morgan Stanley",
                format="144A",
                shelf="Oak Hill CLO",
                series="2025-4",
                notes="4-year reinvestment period",
                tranches=[
                    DealTranche("A", 310.0, "AAA", 135, 5.20, 38.0),
                    DealTranche("B", 50.0, "AA", 185, 6.10, 28.0),
                    DealTranche("C", 35.0, "A", 245, 6.80, 21.0),
                    DealTranche("D", 30.0, "BBB", 380, 7.20, 15.0),
                    DealTranche("E", 25.0, "BB", 650, 7.50, 10.0),
                    DealTranche("Equity", 50.0, "NR", 0, 8.00, 0.0),
                ]
            ),
            DealRecord(
                deal_name="AMCAR 2025-3",
                issuer="AmeriCredit",
                collateral_type="Subprime Auto",
                total_size=1100.0,
                pricing_date="2025-11-20",
                bookrunner="Barclays",
                format="144A",
                shelf="AmeriCredit Automobile Receivables",
                series="2025-3",
                tranches=[
                    DealTranche("A-1", 300.0, "AAA", 55, 0.50, 50.0),
                    DealTranche("A-2", 450.0, "AAA", 75, 1.70, 50.0),
                    DealTranche("B", 130.0, "AA", 110, 2.35, 38.0),
                    DealTranche("C", 95.0, "A", 155, 3.00, 30.0),
                    DealTranche("D", 70.0, "BBB", 260, 3.55, 23.5),
                    DealTranche("E", 55.0, "BB", 450, 3.90, 18.5),
                ]
            ),
        ]

        for deal in sample_deals:
            self.deals[deal.deal_name] = deal

        self._save()

    def add_deal(self, deal: DealRecord) -> bool:
        """Add a deal to the database"""
        self.deals[deal.deal_name] = deal
        self._save()
        return True

    def get_deal(self, deal_name: str) -> Optional[DealRecord]:
        """Get a deal by name"""
        return self.deals.get(deal_name)

    def delete_deal(self, deal_name: str) -> bool:
        """Delete a deal"""
        if deal_name in self.deals:
            del self.deals[deal_name]
            self._save()
            return True
        return False

    def list_deals(self, collateral_type: Optional[str] = None,
                   min_size: float = 0,
                   date_from: Optional[str] = None,
                   date_to: Optional[str] = None) -> List[DealRecord]:
        """List deals with optional filters"""
        result = []
        for deal in self.deals.values():
            # Apply filters
            if collateral_type and deal.collateral_type != collateral_type:
                continue
            if deal.total_size < min_size:
                continue
            if date_from and deal.pricing_date < date_from:
                continue
            if date_to and deal.pricing_date > date_to:
                continue
            result.append(deal)

        # Sort by pricing date descending
        result.sort(key=lambda x: x.pricing_date, reverse=True)
        return result

    def to_dataframe(self) -> pd.DataFrame:
        """Convert all deals to a DataFrame"""
        data = []
        for deal in self.deals.values():
            for tranche in deal.tranches:
                data.append({
                    'Deal': deal.deal_name,
                    'Issuer': deal.issuer,
                    'Collateral': deal.collateral_type,
                    'Deal Size ($M)': deal.total_size,
                    'Pricing Date': deal.pricing_date,
                    'Bookrunner': deal.bookrunner,
                    'Tranche': tranche.tranche_class,
                    'Tranche Size ($M)': tranche.size,
                    'Rating': tranche.rating,
                    'Spread (bps)': tranche.spread,
                    'WAL (yrs)': tranche.wal,
                    'CE (%)': tranche.credit_enhancement,
                })
        return pd.DataFrame(data)

    def get_summary_stats(self) -> Dict:
        """Get summary statistics"""
        df = self.to_dataframe()
        if df.empty:
            return {}

        return {
            'total_deals': len(self.deals),
            'total_volume': df.groupby('Deal')['Deal Size ($M)'].first().sum(),
            'avg_deal_size': df.groupby('Deal')['Deal Size ($M)'].first().mean(),
            'by_collateral': df.groupby('Collateral')['Deal Size ($M)'].sum().to_dict(),
            'by_bookrunner': df.groupby('Bookrunner')['Deal Size ($M)'].sum().to_dict(),
            'avg_spread_by_rating': df.groupby('Rating')['Spread (bps)'].mean().to_dict(),
        }

    def get_collateral_types(self) -> List[str]:
        """Get list of unique collateral types"""
        return list(set(d.collateral_type for d in self.deals.values()))

    def get_bookrunners(self) -> List[str]:
        """Get list of unique bookrunners"""
        return list(set(d.bookrunner for d in self.deals.values()))


# Export functions
def export_to_csv(deals: List[DealRecord], filepath: str):
    """Export deals to CSV"""
    data = []
    for deal in deals:
        for tranche in deal.tranches:
            data.append({
                'Deal Name': deal.deal_name,
                'Issuer': deal.issuer,
                'Collateral Type': deal.collateral_type,
                'Total Size ($M)': deal.total_size,
                'Pricing Date': deal.pricing_date,
                'Bookrunner': deal.bookrunner,
                'Format': deal.format,
                'Tranche': tranche.tranche_class,
                'Tranche Size ($M)': tranche.size,
                'Rating': tranche.rating,
                'Spread (bps)': tranche.spread,
                'WAL (yrs)': tranche.wal,
                'Credit Enhancement (%)': tranche.credit_enhancement,
            })

    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False)


def export_to_excel(deals: List[DealRecord], filepath: str):
    """Export deals to Excel with multiple sheets"""
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        # Summary sheet
        summary_data = []
        for deal in deals:
            summary_data.append({
                'Deal Name': deal.deal_name,
                'Issuer': deal.issuer,
                'Collateral': deal.collateral_type,
                'Size ($M)': deal.total_size,
                'Pricing Date': deal.pricing_date,
                'Bookrunner': deal.bookrunner,
                '# Tranches': len(deal.tranches),
            })
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)

        # Detail sheet
        detail_data = []
        for deal in deals:
            for tranche in deal.tranches:
                detail_data.append({
                    'Deal': deal.deal_name,
                    'Tranche': tranche.tranche_class,
                    'Size ($M)': tranche.size,
                    'Rating': tranche.rating,
                    'Spread (bps)': tranche.spread,
                    'WAL': tranche.wal,
                    'CE (%)': tranche.credit_enhancement,
                })
        pd.DataFrame(detail_data).to_excel(writer, sheet_name='Tranches', index=False)
