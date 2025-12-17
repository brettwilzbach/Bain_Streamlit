"""
Bloomberg API Client
Connects directly to Bloomberg Terminal via blpapi for live market data
No server required - uses blpapi Python library directly
"""

import blpapi
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import time


@dataclass
class BloombergConfig:
    """Configuration for Bloomberg API connection"""
    host: str = "localhost"
    port: int = 8194
    timeout: int = 30000  # milliseconds


class BloombergClient:
    """
    Direct Bloomberg API client using blpapi.
    
    Requires:
    1. Bloomberg Terminal running with BBComm accessible
    2. blpapi Python package installed
    
    No server required - connects directly to Bloomberg Terminal.
    """

    def __init__(self, config: Optional[BloombergConfig] = None):
        self.config = config or BloombergConfig()
        self.session: Optional[blpapi.Session] = None
        self._connected = False
        self._last_check = None

    def _ensure_session(self) -> bool:
        """Ensure Bloomberg session is active"""
        if self.session and self._connected:
            return True

        try:
            sessionOptions = blpapi.SessionOptions()
            sessionOptions.setServerHost(self.config.host)
            sessionOptions.setServerPort(self.config.port)
            
            self.session = blpapi.Session(sessionOptions)
            
            if not self.session.start():
                self._connected = False
                return False
            
            self._connected = True
            return True
        except Exception as e:
            print(f"Bloomberg connection error: {e}")
            self._connected = False
            return False

    def is_available(self) -> bool:
        """Check if Bloomberg Terminal is available"""
        # Cache check for 60 seconds
        if self._last_check and (datetime.now() - self._last_check).seconds < 60:
            return self._connected

        self._connected = self._ensure_session()
        self._last_check = datetime.now()
        return self._connected

    def get_reference_data(self, securities: List[str], fields: List[str]) -> Optional[pd.DataFrame]:
        """
        Get reference data for securities.

        Args:
            securities: List of Bloomberg tickers (e.g., ['SPY US Equity', 'AAPL US Equity'])
            fields: List of fields (e.g., ['PX_LAST', 'YLD_YTM_MID', 'OAS_SPREAD_MID'])

        Returns:
            DataFrame with securities as rows and fields as columns
        """
        if not self._ensure_session():
            return None

        try:
            # Wait for service to be available
            if not self.session.openService("//blp/refdata"):
                return None
            
            refDataService = self.session.getService("//blp/refdata")
            request = refDataService.createRequest("ReferenceDataRequest")
            
            # Add securities
            for security in securities:
                request.append("securities", security)
            
            # Add fields
            for field in fields:
                request.append("fields", field)
            
            # Send request
            self.session.sendRequest(request)
            
            # Process response
            data_rows = []
            security_list = []
            
            while True:
                event = self.session.nextEvent(self.config.timeout)
                
                if event.eventType() == blpapi.Event.RESPONSE or event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                    for msg in event:
                        securityDataArray = msg.getElement("securityData")
                        
                        for i in range(securityDataArray.numValues()):
                            securityData = securityDataArray.getValue(i)
                            security = securityData.getElementAsString("security")
                            security_list.append(security)
                            
                            fieldData = securityData.getElement("fieldData")
                            row_data = {"security": security}
                            
                            for field in fields:
                                try:
                                    if fieldData.hasElement(field):
                                        value = fieldData.getElement(field)
                                        # Handle different data types
                                        if value.isArray():
                                            # For array fields, take first value or convert to string
                                            if value.numValues() > 0:
                                                row_data[field] = value.getValue(0)
                                            else:
                                                row_data[field] = None
                                        else:
                                            row_data[field] = value.getValue()
                                    else:
                                        row_data[field] = None
                                except Exception as e:
                                    row_data[field] = None
                            
                            data_rows.append(row_data)
                    
                    if event.eventType() == blpapi.Event.RESPONSE:
                        break
                elif event.eventType() == blpapi.Event.TIMEOUT:
                    break
            
            if data_rows:
                # Create DataFrame - compatible with pandas 2.0+
                df = pd.DataFrame(data_rows)
                if 'security' in df.columns:
                    df.set_index('security', inplace=True)
                return df
            
            return None
            
        except Exception as e:
            print(f"Bloomberg reference data error: {e}")
            return None

    def get_historical_data(self, security: str, fields: List[str],
                           start_date: str, end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Get historical data for a security.

        Args:
            security: Bloomberg ticker
            fields: List of fields
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today

        Returns:
            DataFrame with date index and field columns
        """
        if not self._ensure_session():
            return None

        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        try:
            # Wait for service to be available
            if not self.session.openService("//blp/refdata"):
                return None
            
            refDataService = self.session.getService("//blp/refdata")
            request = refDataService.createRequest("HistoricalDataRequest")
            
            request.append("securities", security)
            
            for field in fields:
                request.append("fields", field)
            
            # Set date range
            request.set("startDate", start_date)
            request.set("endDate", end_date)
            request.set("periodicityAdjustment", "ACTUAL")
            request.set("periodicitySelection", "DAILY")
            
            # Send request
            self.session.sendRequest(request)
            
            # Process response
            data_rows = []
            
            while True:
                event = self.session.nextEvent(self.config.timeout)
                
                if event.eventType() == blpapi.Event.RESPONSE or event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                    for msg in event:
                        securityDataArray = msg.getElement("securityData")
                        
                        for i in range(securityDataArray.numValues()):
                            securityData = securityDataArray.getValue(i)
                            fieldData = securityData.getElement("fieldData")
                            
                            for j in range(fieldData.numValues()):
                                bar = fieldData.getValue(j)
                                row_data = {}
                                
                                # Get date
                                if bar.hasElement("date"):
                                    date_str = bar.getElementAsString("date")
                                    row_data['date'] = pd.to_datetime(date_str)
                                
                                # Get field values
                                for field in fields:
                                    try:
                                        if bar.hasElement(field):
                                            value = bar.getElement(field)
                                            row_data[field] = value.getValue()
                                        else:
                                            row_data[field] = None
                                    except Exception:
                                        row_data[field] = None
                                
                                if row_data:
                                    data_rows.append(row_data)
                    
                    if event.eventType() == blpapi.Event.RESPONSE:
                        break
                elif event.eventType() == blpapi.Event.TIMEOUT:
                    break
            
            if data_rows:
                df = pd.DataFrame(data_rows)
                if 'date' in df.columns:
                    df.set_index('date', inplace=True)
                return df
            
            return None
            
        except Exception as e:
            print(f"Bloomberg historical data error: {e}")
            return None

    def get_live_price(self, security: str) -> Optional[float]:
        """Get live price for a security"""
        df = self.get_reference_data([security], ["PX_LAST"])
        if df is not None and not df.empty and 'PX_LAST' in df.columns:
            return float(df.iloc[0]['PX_LAST'])
        return None

    def close(self):
        """Close Bloomberg session"""
        if self.session:
            try:
                self.session.stop()
            except Exception:
                pass
            self.session = None
            self._connected = False

    def __enter__(self):
        """Context manager entry"""
        self._ensure_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# ============================================================================
# STRUCTURED CREDIT SPECIFIC FUNCTIONS
# ============================================================================

# Bloomberg tickers for structured credit indices and benchmarks
BLOOMBERG_TICKERS = {
    # Credit indices
    'CDX_IG': 'CDX IG CDSI GEN 5Y Corp',
    'CDX_HY': 'CDX HY CDSI GEN 5Y Corp',
    'LCDX': 'LCDX CDSI GEN 5Y Corp',

    # CLO indices (Palmer Square)
    'PS_CLO_AAA': 'PSCLOAAA Index',
    'PS_CLO_AA': 'PSCLOAA Index',
    'PS_CLO_A': 'PSCLOA Index',
    'PS_CLO_BBB': 'PSCLOBBB Index',
    'PS_CLO_BB': 'PSCLOBB Index',

    # ABS indices (if available)
    'ABS_AUTO_AAA': 'ABSAAAUT Index',
    'ABS_AUTO_BBB': 'ABSBBAUT Index',

    # Rates
    'SOFR': 'SOFRRATE Index',
    'SOFR_1M': 'USOSFR1M Index',
    'SOFR_3M': 'USOSFR3M Index',

    # Treasuries
    'UST_2Y': 'USGG2YR Index',
    'UST_5Y': 'USGG5YR Index',
    'UST_10Y': 'USGG10YR Index',
}

# Fields for spread data
SPREAD_FIELDS = ['PX_LAST', 'OAS_SPREAD_MID', 'YLD_YTM_MID', 'DM_MID']


class BloombergSpreadProvider:
    """
    Provides live spread data from Bloomberg.
    Falls back to estimated data if Bloomberg unavailable.
    """

    def __init__(self, client: Optional[BloombergClient] = None):
        self.client = client or BloombergClient()
        self._cache: Dict[str, Dict] = {}
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=5)

    def is_available(self) -> bool:
        """Check if Bloomberg data is available"""
        return self.client.is_available()

    def get_clo_spreads(self) -> Optional[Dict[str, float]]:
        """Get live CLO spreads from Palmer Square indices"""
        if not self.is_available():
            return None

        tickers = [
            BLOOMBERG_TICKERS['PS_CLO_AAA'],
            BLOOMBERG_TICKERS['PS_CLO_AA'],
            BLOOMBERG_TICKERS['PS_CLO_A'],
            BLOOMBERG_TICKERS['PS_CLO_BBB'],
            BLOOMBERG_TICKERS['PS_CLO_BB'],
        ]

        df = self.client.get_reference_data(tickers, ['PX_LAST', 'DM_MID'])

        if df is not None and not df.empty:
            result = {}
            for i, ticker in enumerate(tickers):
                if i < len(df):
                    row = df.iloc[i]
                    spread_name = ['CLO AAA', 'CLO AA', 'CLO A', 'CLO BBB', 'CLO BB'][i]
                    dm_value = row.get('DM_MID')
                    if dm_value is not None:
                        try:
                            result[spread_name] = float(dm_value)
                        except (ValueError, TypeError):
                            result[spread_name] = None
                    else:
                        result[spread_name] = None
            return result
        return None

    def get_credit_indices(self) -> Optional[Dict[str, float]]:
        """Get CDX and LCDX levels"""
        if not self.is_available():
            return None

        tickers = [
            BLOOMBERG_TICKERS['CDX_IG'],
            BLOOMBERG_TICKERS['CDX_HY'],
            BLOOMBERG_TICKERS['LCDX'],
        ]

        df = self.client.get_reference_data(tickers, ['PX_LAST'])

        if df is not None and not df.empty:
            result = {}
            names = ['CDX IG', 'CDX HY', 'LCDX']
            for i, name in enumerate(names):
                if i < len(df):
                    row = df.iloc[i]
                    px_value = row.get('PX_LAST')
                    if px_value is not None:
                        try:
                            result[name] = float(px_value)
                        except (ValueError, TypeError):
                            result[name] = None
                    else:
                        result[name] = None
            return result
        return None

    def get_sofr(self) -> Optional[float]:
        """Get live SOFR rate"""
        if not self.is_available():
            return None

        return self.client.get_live_price(BLOOMBERG_TICKERS['SOFR'])

    def get_abs_new_issue_pricing(self, deal_ticker: str) -> Optional[Dict]:
        """
        Get new issue pricing for an ABS deal.

        Args:
            deal_ticker: Bloomberg deal ticker (e.g., 'ACMAT 2025-4 A Mtge')

        Returns:
            Dict with pricing details
        """
        if not self.is_available():
            return None

        fields = ['PX_LAST', 'OAS_SPREAD_MID', 'DM_MID', 'YLD_YTM_MID', 'WAL_TO_MAT']
        df = self.client.get_reference_data([deal_ticker], fields)

        if df is not None and not df.empty:
            return df.iloc[0].to_dict()
        return None

    def get_historical_spreads(self, ticker_key: str, days: int = 365) -> Optional[pd.DataFrame]:
        """Get historical spread data"""
        if not self.is_available():
            return None

        ticker = BLOOMBERG_TICKERS.get(ticker_key)
        if not ticker:
            return None

        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        return self.client.get_historical_data(ticker, ['PX_LAST', 'DM_MID'], start_date)

    def get_all_structured_spreads(self) -> Dict[str, Any]:
        """Get all available structured credit spreads"""
        result = {
            'source': 'bloomberg' if self.is_available() else 'estimated',
            'timestamp': datetime.now().isoformat(),
            'clo': self.get_clo_spreads(),
            'indices': self.get_credit_indices(),
            'sofr': self.get_sofr(),
        }
        return result

    def close(self):
        """Close Bloomberg connection"""
        if self.client:
            self.client.close()


# ============================================================================
# MCAL - STRUCTURED FINANCE CALENDAR
# ============================================================================

class BloombergMCAL:
    """
    Access Bloomberg's Structured Finance Calendar (MCAL).
    Pulls real new issue deal data.
    """

    def __init__(self, client: Optional[BloombergClient] = None):
        self.client = client or BloombergClient()

    def is_available(self) -> bool:
        """Check if Bloomberg is available"""
        return self.client.is_available()

    def get_recent_abs_deals(self, days: int = 30, asset_class: str = None) -> Optional[pd.DataFrame]:
        """
        Get recent ABS new issue deals from MCAL.

        Args:
            days: Number of days to look back
            asset_class: Filter by asset class (e.g., 'AUTO', 'CLO', 'CREDIT CARD')

        Returns:
            DataFrame with deal information
        """
        if not self.client._ensure_session():
            return None

        try:
            if not self.client.session.openService("//blp/refdata"):
                return None

            refDataService = self.client.session.getService("//blp/refdata")

            # Use SRCH to query MCAL data
            # Bloomberg MCAL uses specific search criteria
            request = refDataService.createRequest("ReferenceDataRequest")

            # Query the ABS new issue index/search
            # Use BSRCH service for structured search
            # Note: Exact implementation depends on Bloomberg entitlements

            # For MCAL, we typically query using BEQS (Bloomberg Equity Screening)
            # or by looking up specific indices that track new issuance

            # Alternative: Query known recent deals by shelf program
            known_shelves = [
                # Auto ABS shelves
                "CARMX",   # CarMax
                "DRIVE",   # Santander Drive
                "ALLY",    # Ally Auto
                "FORDO",   # Ford Credit Auto
                "COPAR",   # Capital One Prime
                "WOART",   # World Omni Auto
                "AMCAR",   # AmeriCredit
                "SDART",   # Santander Drive Auto
                "ACMAT",   # America's Car-Mart
                # CLO shelves
                "CLOIE",   # CLO new issues
                "TREST",   # Trinitas
                "OAKCL",   # Oaktree CLO
            ]

            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            end_date = datetime.now().strftime('%Y%m%d')

            # Build securities list - look for recent series
            securities = []
            current_year = datetime.now().year
            for shelf in known_shelves:
                # Try recent series numbers
                for series in range(1, 13):  # Up to 12 series per year
                    for tranche in ['A', 'A1', 'A2', 'B', 'C', 'D']:
                        ticker = f"{shelf} {current_year}-{series} {tranche} Mtge"
                        securities.append(ticker)

            # Query in batches to avoid timeout
            batch_size = 50
            all_data = []

            for i in range(0, min(len(securities), 200), batch_size):
                batch = securities[i:i + batch_size]

                request = refDataService.createRequest("ReferenceDataRequest")
                for sec in batch:
                    request.append("securities", sec)

                fields = [
                    "NAME",
                    "ISSUER",
                    "ISSUE_DT",
                    "MTG_DEAL_TYP",
                    "AMT_ISSUED",
                    "CPN",
                    "SPREAD_TO_BENCHMARK",
                    "RTG_SP",
                    "RTG_MOODY",
                    "RTG_FITCH",
                    "WAL_TO_MAT",
                    "MTG_COLLATERAL_TYP",
                    "LEAD_MGR",
                ]

                for field in fields:
                    request.append("fields", field)

                self.client.session.sendRequest(request)

                # Process response
                while True:
                    event = self.client.session.nextEvent(5000)

                    if event.eventType() == blpapi.Event.RESPONSE or event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                        for msg in event:
                            if msg.hasElement("securityData"):
                                securityDataArray = msg.getElement("securityData")

                                for j in range(securityDataArray.numValues()):
                                    securityData = securityDataArray.getValue(j)

                                    # Skip securities with errors
                                    if securityData.hasElement("securityError"):
                                        continue

                                    security = securityData.getElementAsString("security")
                                    fieldData = securityData.getElement("fieldData")

                                    row = {"ticker": security}
                                    for field in fields:
                                        try:
                                            if fieldData.hasElement(field):
                                                value = fieldData.getElement(field).getValue()
                                                row[field] = value
                                            else:
                                                row[field] = None
                                        except Exception:
                                            row[field] = None

                                    # Only include if we got valid data
                                    if row.get("NAME") or row.get("ISSUER"):
                                        all_data.append(row)

                        if event.eventType() == blpapi.Event.RESPONSE:
                            break
                    elif event.eventType() == blpapi.Event.TIMEOUT:
                        break

            if all_data:
                df = pd.DataFrame(all_data)
                # Filter by date if we have issue date
                if "ISSUE_DT" in df.columns:
                    df["ISSUE_DT"] = pd.to_datetime(df["ISSUE_DT"], errors='coerce')
                    cutoff = datetime.now() - timedelta(days=days)
                    df = df[df["ISSUE_DT"] >= cutoff]

                return df

            return None

        except Exception as e:
            print(f"MCAL query error: {e}")
            return None

    def search_abs_deals(self, search_term: str) -> Optional[pd.DataFrame]:
        """
        Search for ABS deals by name or issuer.

        Args:
            search_term: Search string (e.g., 'ACMAT', 'CarMax')

        Returns:
            DataFrame with matching deals
        """
        if not self.client._ensure_session():
            return None

        try:
            if not self.client.session.openService("//blp/refdata"):
                return None

            refDataService = self.client.session.getService("//blp/refdata")

            # Build search tickers
            current_year = datetime.now().year
            securities = []

            # Try variations
            for year in [current_year, current_year - 1]:
                for series in range(1, 13):
                    for tranche in ['A', 'A1', 'A2', 'A3', 'B', 'C', 'D', 'E']:
                        ticker = f"{search_term.upper()} {year}-{series} {tranche} Mtge"
                        securities.append(ticker)

            request = refDataService.createRequest("ReferenceDataRequest")
            for sec in securities[:100]:  # Limit to avoid timeout
                request.append("securities", sec)

            fields = [
                "NAME", "ISSUER", "ISSUE_DT", "AMT_ISSUED", "CPN",
                "SPREAD_TO_BENCHMARK", "RTG_SP", "WAL_TO_MAT", "MTG_COLLATERAL_TYP"
            ]
            for field in fields:
                request.append("fields", field)

            self.client.session.sendRequest(request)

            results = []
            while True:
                event = self.client.session.nextEvent(10000)

                if event.eventType() in [blpapi.Event.RESPONSE, blpapi.Event.PARTIAL_RESPONSE]:
                    for msg in event:
                        if msg.hasElement("securityData"):
                            securityDataArray = msg.getElement("securityData")

                            for j in range(securityDataArray.numValues()):
                                securityData = securityDataArray.getValue(j)

                                if securityData.hasElement("securityError"):
                                    continue

                                security = securityData.getElementAsString("security")
                                fieldData = securityData.getElement("fieldData")

                                row = {"ticker": security}
                                for field in fields:
                                    try:
                                        if fieldData.hasElement(field):
                                            row[field] = fieldData.getElement(field).getValue()
                                    except Exception:
                                        pass

                                if row.get("NAME") or row.get("ISSUER"):
                                    results.append(row)

                    if event.eventType() == blpapi.Event.RESPONSE:
                        break
                elif event.eventType() == blpapi.Event.TIMEOUT:
                    break

            return pd.DataFrame(results) if results else None

        except Exception as e:
            print(f"Deal search error: {e}")
            return None

    def get_deal_details(self, deal_prefix: str, year: int, series: int) -> Optional[Dict]:
        """
        Get full details for a specific deal.

        Args:
            deal_prefix: Deal shelf (e.g., 'ACMAT')
            year: Year (e.g., 2025)
            series: Series number (e.g., 4)

        Returns:
            Dict with deal and tranche information
        """
        if not self.client._ensure_session():
            return None

        try:
            if not self.client.session.openService("//blp/refdata"):
                return None

            refDataService = self.client.session.getService("//blp/refdata")

            # Query all possible tranches
            tranches = ['A', 'A1', 'A2', 'A3', 'A4', 'B', 'C', 'D', 'E', 'R', 'SUB']
            securities = [f"{deal_prefix} {year}-{series} {t} Mtge" for t in tranches]

            request = refDataService.createRequest("ReferenceDataRequest")
            for sec in securities:
                request.append("securities", sec)

            fields = [
                "NAME", "ISSUER", "ISSUE_DT", "MATURITY", "AMT_ISSUED", "CPN",
                "SPREAD_TO_BENCHMARK", "OAS_SPREAD_MID", "DM_MID",
                "RTG_SP", "RTG_MOODY", "RTG_FITCH",
                "WAL_TO_MAT", "MTG_COLLATERAL_TYP", "LEAD_MGR",
                "YLD_YTM_MID", "CRNCY"
            ]
            for field in fields:
                request.append("fields", field)

            self.client.session.sendRequest(request)

            deal_info = {
                "deal_name": f"{deal_prefix} {year}-{series}",
                "tranches": []
            }

            while True:
                event = self.client.session.nextEvent(10000)

                if event.eventType() in [blpapi.Event.RESPONSE, blpapi.Event.PARTIAL_RESPONSE]:
                    for msg in event:
                        if msg.hasElement("securityData"):
                            securityDataArray = msg.getElement("securityData")

                            for j in range(securityDataArray.numValues()):
                                securityData = securityDataArray.getValue(j)

                                if securityData.hasElement("securityError"):
                                    continue

                                security = securityData.getElementAsString("security")
                                fieldData = securityData.getElement("fieldData")

                                tranche_data = {"ticker": security}
                                for field in fields:
                                    try:
                                        if fieldData.hasElement(field):
                                            tranche_data[field] = fieldData.getElement(field).getValue()
                                    except Exception:
                                        pass

                                if tranche_data.get("NAME") or tranche_data.get("AMT_ISSUED"):
                                    # Extract tranche class from ticker
                                    parts = security.split()
                                    if len(parts) >= 3:
                                        tranche_data["tranche_class"] = parts[2]

                                    # Set deal-level info from first tranche
                                    if not deal_info.get("issuer"):
                                        deal_info["issuer"] = tranche_data.get("ISSUER")
                                        deal_info["issue_date"] = tranche_data.get("ISSUE_DT")
                                        deal_info["collateral_type"] = tranche_data.get("MTG_COLLATERAL_TYP")
                                        deal_info["bookrunner"] = tranche_data.get("LEAD_MGR")

                                    deal_info["tranches"].append(tranche_data)

                    if event.eventType() == blpapi.Event.RESPONSE:
                        break
                elif event.eventType() == blpapi.Event.TIMEOUT:
                    break

            # Calculate total deal size
            deal_info["total_size"] = sum(
                t.get("AMT_ISSUED", 0) or 0 for t in deal_info["tranches"]
            ) / 1_000_000  # Convert to millions

            return deal_info if deal_info["tranches"] else None

        except Exception as e:
            print(f"Deal details error: {e}")
            return None


def get_mcal_provider(client: Optional[BloombergClient] = None) -> BloombergMCAL:
    """Get MCAL provider instance"""
    return BloombergMCAL(client)


# ============================================================================
# DEAL-SPECIFIC LOOKUPS
# ============================================================================

def lookup_deal_bval(client: BloombergClient, cusip: str) -> Optional[Dict]:
    """
    Look up BVAL (Bloomberg Valuation) pricing for a specific security.

    Args:
        client: Bloomberg client
        cusip: CUSIP of the security

    Returns:
        Dict with BVAL pricing details
    """
    if not client.is_available():
        return None

    ticker = f"{cusip} Mtge"
    fields = [
        'BVAL_MID_PRICE',
        'BVAL_ASK_PRICE',
        'BVAL_BID_PRICE',
        'BVAL_OAS',
        'BVAL_DM',
        'BVAL_YIELD',
        'BVAL_WAL',
        'BVAL_CONFIDENCE',
    ]

    df = client.get_reference_data([ticker], fields)

    if df is not None and not df.empty:
        return df.iloc[0].to_dict()
    return None


def get_deal_tranches(client: BloombergClient, deal_name: str) -> Optional[List[Dict]]:
    """
    Get all tranches for a deal.

    Args:
        client: Bloomberg client
        deal_name: Deal name (e.g., 'ACMAT 2025-4')

    Returns:
        List of tranche data
    """
    # This would require SRCH function or specific deal lookups
    # Implementation depends on Bloomberg data access
    pass


# ============================================================================
# FACTORY FUNCTIONS (maintain compatibility with existing code)
# ============================================================================

# Alias for backward compatibility
BloombergMCPClient = BloombergClient

def get_bloomberg_client(host: str = "localhost", port: int = 8194) -> BloombergClient:
    """Create a Bloomberg client with specified configuration"""
    config = BloombergConfig(host=host, port=port)
    return BloombergClient(config)


def get_spread_provider() -> BloombergSpreadProvider:
    """Get a spread provider (uses Bloomberg if available)"""
    return BloombergSpreadProvider()
