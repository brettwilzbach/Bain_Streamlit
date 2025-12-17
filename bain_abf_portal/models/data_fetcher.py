"""
Data Fetcher Module
Fetch real data from Bloomberg (via MCP) and FRED APIs

Priority:
1. Bloomberg MCP (if available) - live terminal data
2. FRED API (fallback) - free public data with estimates
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import json
from dataclasses import dataclass
from functools import lru_cache

# Import Bloomberg client (optional - won't fail if not configured)
try:
    from .bloomberg_client import (
        BloombergMCPClient, BloombergSpreadProvider,
        get_bloomberg_client, get_spread_provider
    )
    BLOOMBERG_AVAILABLE = True
except ImportError:
    BLOOMBERG_AVAILABLE = False


# ============================================================================
# FRED API (Federal Reserve Economic Data)
# ============================================================================

FRED_BASE_URL = "https://api.stlouisfed.org/fred"

# Common FRED series IDs
FRED_SERIES = {
    'SOFR': 'SOFR',                      # Secured Overnight Financing Rate
    'SOFR_30D': 'SOFR30DAYAVG',          # 30-Day Average SOFR
    'SOFR_90D': 'SOFR90DAYAVG',          # 90-Day Average SOFR
    'EFFR': 'EFFR',                      # Effective Federal Funds Rate
    'UST_3M': 'DGS3MO',                  # 3-Month Treasury
    'UST_2Y': 'DGS2',                    # 2-Year Treasury
    'UST_5Y': 'DGS5',                    # 5-Year Treasury
    'UST_10Y': 'DGS10',                  # 10-Year Treasury
    'UST_30Y': 'DGS30',                  # 30-Year Treasury
    'IG_SPREAD': 'BAMLC0A0CM',           # ICE BofA US Corporate Index OAS
    'HY_SPREAD': 'BAMLH0A0HYM2',         # ICE BofA US High Yield Index OAS
    'BBB_SPREAD': 'BAMLC0A4CBBB',        # ICE BofA BBB US Corporate Index OAS
    'AA_SPREAD': 'BAMLC0A2CAA',          # ICE BofA AA US Corporate Index OAS
    'A_SPREAD': 'BAMLC0A3CA',            # ICE BofA A US Corporate Index OAS
    'MORTGAGE_30Y': 'MORTGAGE30US',       # 30-Year Fixed Mortgage Rate
    'AUTO_LOANS': 'TERMCBAUTO48NS',      # 48-Month New Auto Loan Rate
}


class FREDClient:
    """Client for fetching data from FRED API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize FRED client.
        If no API key provided, will attempt to use public endpoints with rate limiting.
        Get free API key at: https://fred.stlouisfed.org/docs/api/api_key.html
        """
        self.api_key = api_key
        self.base_url = FRED_BASE_URL

    def get_series(self, series_id: str, start_date: Optional[str] = None,
                   end_date: Optional[str] = None, limit: int = 365) -> pd.DataFrame:
        """
        Fetch a data series from FRED.

        Args:
            series_id: FRED series ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Max observations to return

        Returns:
            DataFrame with date index and value column
        """
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=limit)).strftime('%Y-%m-%d')

        params = {
            'series_id': series_id,
            'observation_start': start_date,
            'observation_end': end_date,
            'file_type': 'json',
            'sort_order': 'desc',
            'limit': limit
        }

        if self.api_key:
            params['api_key'] = self.api_key

        try:
            response = requests.get(
                f"{self.base_url}/series/observations",
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            observations = data.get('observations', [])

            df = pd.DataFrame(observations)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                df = df[['date', 'value']].dropna()
                df = df.sort_values('date')
                df.set_index('date', inplace=True)

            return df

        except requests.RequestException as e:
            print(f"Error fetching {series_id}: {e}")
            return pd.DataFrame()

    def get_latest(self, series_id: str) -> Optional[float]:
        """Get the most recent value for a series"""
        df = self.get_series(series_id, limit=5)
        if not df.empty:
            return df['value'].iloc[-1]
        return None

    def get_multiple_series(self, series_ids: List[str],
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> pd.DataFrame:
        """Fetch multiple series and combine into a single DataFrame"""
        dfs = {}
        for series_id in series_ids:
            df = self.get_series(series_id, start_date, end_date)
            if not df.empty:
                dfs[series_id] = df['value']

        if dfs:
            return pd.DataFrame(dfs)
        return pd.DataFrame()


# ============================================================================
# SPREAD DATA (Estimated from public sources + premiums)
# ============================================================================

@dataclass
class SpreadData:
    """Spread data for a security or sector"""
    name: str
    current_spread: float       # bps
    benchmark: str
    ytd_change: float          # bps
    one_year_avg: float        # bps
    one_year_min: float        # bps
    one_year_max: float        # bps
    last_updated: str

    @property
    def z_score(self) -> float:
        """Calculate z-score vs 1-year average"""
        if self.one_year_max == self.one_year_min:
            return 0.0
        std_approx = (self.one_year_max - self.one_year_min) / 4  # Rough std estimate
        if std_approx > 0:
            return (self.current_spread - self.one_year_avg) / std_approx
        return 0.0


class SpreadEstimator:
    """
    Estimate structured credit spreads based on corporate benchmarks.

    Since live ABS/CLO spread data requires expensive subscriptions (Bloomberg, LCD),
    this class estimates spreads using:
    1. Public corporate spread data from FRED
    2. Historical spread relationships/premiums
    """

    # Historical spread premiums over benchmarks (based on market research)
    # These represent typical pickups for structured credit over corporate equivalents
    SPREAD_PREMIUMS = {
        # CLO spreads vs. corporate benchmarks
        'CLO AAA': {'benchmark': 'AA_SPREAD', 'premium': 45, 'vol_mult': 1.2},
        'CLO AA': {'benchmark': 'A_SPREAD', 'premium': 60, 'vol_mult': 1.3},
        'CLO A': {'benchmark': 'A_SPREAD', 'premium': 90, 'vol_mult': 1.4},
        'CLO BBB': {'benchmark': 'BBB_SPREAD', 'premium': 180, 'vol_mult': 1.5},
        'CLO BB': {'benchmark': 'HY_SPREAD', 'premium': 200, 'vol_mult': 1.3},

        # Prime Auto ABS spreads
        'Prime Auto AAA': {'benchmark': 'AA_SPREAD', 'premium': -15, 'vol_mult': 0.7},
        'Prime Auto AA': {'benchmark': 'AA_SPREAD', 'premium': 0, 'vol_mult': 0.8},
        'Prime Auto A': {'benchmark': 'A_SPREAD', 'premium': 0, 'vol_mult': 0.9},

        # Subprime Auto ABS spreads
        'Subprime Auto AAA': {'benchmark': 'AA_SPREAD', 'premium': 40, 'vol_mult': 1.0},
        'Subprime Auto AA': {'benchmark': 'A_SPREAD', 'premium': 50, 'vol_mult': 1.1},
        'Subprime Auto A': {'benchmark': 'A_SPREAD', 'premium': 90, 'vol_mult': 1.2},
        'Subprime Auto BBB': {'benchmark': 'BBB_SPREAD', 'premium': 250, 'vol_mult': 1.4},
        'Subprime Auto BB': {'benchmark': 'HY_SPREAD', 'premium': 150, 'vol_mult': 1.2},

        # Consumer ABS spreads
        'Consumer ABS AAA': {'benchmark': 'AA_SPREAD', 'premium': 10, 'vol_mult': 0.9},
        'Consumer ABS A': {'benchmark': 'A_SPREAD', 'premium': 30, 'vol_mult': 1.0},
        'Consumer ABS BBB': {'benchmark': 'BBB_SPREAD', 'premium': 150, 'vol_mult': 1.2},

        # Equipment ABS spreads
        'Equipment ABS AAA': {'benchmark': 'AA_SPREAD', 'premium': -10, 'vol_mult': 0.8},
        'Equipment ABS A': {'benchmark': 'A_SPREAD', 'premium': 10, 'vol_mult': 0.9},
    }

    def __init__(self, fred_client: Optional[FREDClient] = None):
        self.fred = fred_client or FREDClient()
        self._benchmark_cache: Dict[str, pd.DataFrame] = {}
        self._last_fetch: Optional[datetime] = None

    def _fetch_benchmarks(self, force: bool = False) -> Dict[str, float]:
        """Fetch corporate benchmark spreads from FRED"""
        # Cache for 1 hour
        if not force and self._last_fetch:
            if datetime.now() - self._last_fetch < timedelta(hours=1):
                return {k: df['value'].iloc[-1] for k, df in self._benchmark_cache.items() if not df.empty}

        benchmarks = {}
        series_to_fetch = ['AA_SPREAD', 'A_SPREAD', 'BBB_SPREAD', 'HY_SPREAD', 'IG_SPREAD']

        for series_name in series_to_fetch:
            series_id = FRED_SERIES.get(series_name)
            if series_id:
                df = self.fred.get_series(series_id, limit=365)
                if not df.empty:
                    self._benchmark_cache[series_name] = df
                    benchmarks[series_name] = df['value'].iloc[-1]

        self._last_fetch = datetime.now()
        return benchmarks

    def estimate_spread(self, sector: str) -> Optional[SpreadData]:
        """Estimate spread for a structured credit sector"""
        if sector not in self.SPREAD_PREMIUMS:
            return None

        params = self.SPREAD_PREMIUMS[sector]
        benchmark_name = params['benchmark']
        premium = params['premium']
        vol_mult = params['vol_mult']

        # Get benchmark data
        if benchmark_name not in self._benchmark_cache:
            series_id = FRED_SERIES.get(benchmark_name)
            if series_id:
                df = self.fred.get_series(series_id, limit=365)
                if not df.empty:
                    self._benchmark_cache[benchmark_name] = df

        if benchmark_name not in self._benchmark_cache:
            return None

        benchmark_df = self._benchmark_cache[benchmark_name]
        if benchmark_df.empty:
            return None

        # Calculate estimated spread
        current_benchmark = benchmark_df['value'].iloc[-1]
        current_spread = current_benchmark + premium

        # Calculate historical stats with volatility adjustment
        one_year_avg = benchmark_df['value'].mean() + premium
        one_year_min = benchmark_df['value'].min() + premium - (premium * 0.2)
        one_year_max = benchmark_df['value'].max() + premium + (premium * 0.2)

        # YTD change (approximate)
        year_start = benchmark_df[benchmark_df.index >= f'{datetime.now().year}-01-01']
        if not year_start.empty:
            ytd_change = current_benchmark - year_start['value'].iloc[0]
        else:
            ytd_change = 0

        return SpreadData(
            name=sector,
            current_spread=round(current_spread, 0),
            benchmark=benchmark_name.replace('_SPREAD', ' Corps'),
            ytd_change=round(ytd_change, 0),
            one_year_avg=round(one_year_avg, 0),
            one_year_min=round(one_year_min, 0),
            one_year_max=round(one_year_max, 0),
            last_updated=datetime.now().strftime('%Y-%m-%d %H:%M')
        )

    def get_all_spreads(self) -> Dict[str, SpreadData]:
        """Get estimated spreads for all sectors"""
        # First fetch benchmarks
        self._fetch_benchmarks()

        spreads = {}
        for sector in self.SPREAD_PREMIUMS.keys():
            spread_data = self.estimate_spread(sector)
            if spread_data:
                spreads[sector] = spread_data

        return spreads

    def get_spread_history(self, sector: str, days: int = 365) -> pd.DataFrame:
        """Get estimated historical spread for a sector"""
        if sector not in self.SPREAD_PREMIUMS:
            return pd.DataFrame()

        params = self.SPREAD_PREMIUMS[sector]
        benchmark_name = params['benchmark']
        premium = params['premium']

        series_id = FRED_SERIES.get(benchmark_name)
        if not series_id:
            return pd.DataFrame()

        df = self.fred.get_series(series_id, limit=days)
        if df.empty:
            return pd.DataFrame()

        # Apply premium to get estimated ABS/CLO spread
        df['estimated_spread'] = df['value'] + premium
        df = df.rename(columns={'value': 'benchmark_spread'})

        return df


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_current_sofr() -> Optional[float]:
    """Quick helper to get current SOFR rate"""
    client = FREDClient()
    return client.get_latest(FRED_SERIES['SOFR'])


def get_treasury_curve() -> Dict[str, float]:
    """Get current Treasury yield curve"""
    client = FREDClient()
    tenors = ['UST_3M', 'UST_2Y', 'UST_5Y', 'UST_10Y', 'UST_30Y']
    curve = {}

    for tenor in tenors:
        value = client.get_latest(FRED_SERIES[tenor])
        if value:
            curve[tenor.replace('UST_', '')] = value

    return curve


def get_corporate_spreads() -> Dict[str, float]:
    """Get current corporate bond spreads"""
    client = FREDClient()
    spreads = {}

    for name in ['IG_SPREAD', 'HY_SPREAD', 'AA_SPREAD', 'A_SPREAD', 'BBB_SPREAD']:
        value = client.get_latest(FRED_SERIES[name])
        if value:
            spreads[name] = value

    return spreads


# ============================================================================
# UNIFIED DATA PROVIDER (Bloomberg + FRED)
# ============================================================================

@dataclass
class MarketDataResult:
    """Result from market data fetch with source tracking"""
    data: Dict
    source: str  # 'bloomberg', 'fred', 'estimated'
    timestamp: datetime
    is_live: bool


class UnifiedDataProvider:
    """
    Unified provider that tries Bloomberg first, then falls back to FRED.

    Usage:
        provider = UnifiedDataProvider()
        if provider.bloomberg_available:
            # Using live Bloomberg data
        else:
            # Using FRED estimates

        spreads = provider.get_structured_spreads()
    """

    def __init__(self, bloomberg_host: str = "localhost", bloomberg_port: int = 8194):
        self.fred = FREDClient()
        self.spread_estimator = SpreadEstimator(self.fred)

        # Try to connect to Bloomberg (direct connection, no server needed)
        self._bloomberg_client = None
        self._bloomberg_spreads = None
        if BLOOMBERG_AVAILABLE:
            try:
                self._bloomberg_client = get_bloomberg_client(bloomberg_host, bloomberg_port)
                # Share the same client with spread provider
                self._bloomberg_spreads = BloombergSpreadProvider(self._bloomberg_client)
            except Exception:
                pass

    @property
    def bloomberg_available(self) -> bool:
        """Check if Bloomberg Terminal is available"""
        if self._bloomberg_client:
            return self._bloomberg_client.is_available()
        return False

    @property
    def data_source(self) -> str:
        """Get current data source"""
        if self.bloomberg_available:
            return "Bloomberg Terminal (Live)"
        return "FRED API (Estimated)"

    def get_sofr(self) -> Tuple[Optional[float], str]:
        """
        Get current SOFR rate.

        Returns:
            Tuple of (rate, source)
        """
        # Try Bloomberg first
        if self._bloomberg_spreads and self._bloomberg_spreads.is_available():
            rate = self._bloomberg_spreads.get_sofr()
            if rate is not None:
                return rate, "Bloomberg"

        # Fall back to FRED
        rate = get_current_sofr()
        return rate, "FRED"

    def get_clo_spreads(self) -> Tuple[Optional[Dict[str, float]], str]:
        """
        Get CLO spreads by rating.

        Returns:
            Tuple of (spreads_dict, source)
        """
        # Try Bloomberg (Palmer Square indices)
        if self._bloomberg_spreads and self._bloomberg_spreads.is_available():
            spreads = self._bloomberg_spreads.get_clo_spreads()
            if spreads:
                return spreads, "Bloomberg (Palmer Square)"

        # Fall back to FRED estimates
        all_spreads = self.spread_estimator.get_all_spreads()
        clo_spreads = {
            k: v.current_spread
            for k, v in all_spreads.items()
            if k.startswith('CLO')
        }
        return clo_spreads if clo_spreads else None, "FRED (Estimated)"

    def get_credit_indices(self) -> Tuple[Optional[Dict[str, float]], str]:
        """
        Get CDX and LCDX levels.

        Returns:
            Tuple of (indices_dict, source)
        """
        # Try Bloomberg
        if self._bloomberg_spreads and self._bloomberg_spreads.is_available():
            indices = self._bloomberg_spreads.get_credit_indices()
            if indices:
                return indices, "Bloomberg"

        # Fall back to FRED (only have IG/HY OAS, not CDX)
        corp_spreads = get_corporate_spreads()
        return {
            'IG OAS': corp_spreads.get('IG_SPREAD'),
            'HY OAS': corp_spreads.get('HY_SPREAD'),
        }, "FRED (OAS, not CDX)"

    def get_structured_spreads(self) -> MarketDataResult:
        """
        Get all structured credit spreads.

        Returns comprehensive spread data with source tracking.
        """
        timestamp = datetime.now()

        # Try Bloomberg first
        if self._bloomberg_spreads and self._bloomberg_spreads.is_available():
            data = self._bloomberg_spreads.get_all_structured_spreads()
            if data:
                return MarketDataResult(
                    data=data,
                    source="Bloomberg Terminal",
                    timestamp=timestamp,
                    is_live=True
                )

        # Fall back to FRED estimates
        all_spreads = self.spread_estimator.get_all_spreads()
        corp_spreads = get_corporate_spreads()
        sofr = get_current_sofr()

        data = {
            'abs_spreads': {k: {
                'current': v.current_spread,
                'ytd_change': v.ytd_change,
                'z_score': v.z_score,
                'one_year_avg': v.one_year_avg,
                'one_year_min': v.one_year_min,
                'one_year_max': v.one_year_max,
            } for k, v in all_spreads.items()},
            'corporate': corp_spreads,
            'sofr': sofr,
            'source': 'estimated',
        }

        return MarketDataResult(
            data=data,
            source="FRED API (Estimated)",
            timestamp=timestamp,
            is_live=False
        )

    def get_deal_pricing(self, deal_ticker: str) -> Tuple[Optional[Dict], str]:
        """
        Get pricing for a specific ABS deal.

        Args:
            deal_ticker: Bloomberg ticker or CUSIP

        Returns:
            Tuple of (pricing_dict, source)
        """
        if self._bloomberg_spreads and self._bloomberg_spreads.is_available():
            pricing = self._bloomberg_spreads.get_abs_new_issue_pricing(deal_ticker)
            if pricing:
                return pricing, "Bloomberg (BVAL)"

        return None, "Not available (requires Bloomberg)"


# Convenience function
def get_unified_provider(bloomberg_host: str = "localhost",
                         bloomberg_port: int = 8194) -> UnifiedDataProvider:
    """Get a unified data provider instance (connects directly to Bloomberg Terminal)"""
    return UnifiedDataProvider(bloomberg_host, bloomberg_port)
