"""
Direct Bloomberg API Client
Connects directly to Bloomberg Terminal using blpapi (no MCP server needed)
"""

import pandas as pd
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

# Try to import blpapi
try:
    import blpapi
    BLPAPI_AVAILABLE = True
except ImportError:
    BLPAPI_AVAILABLE = False


@dataclass
class BloombergSession:
    """Manages Bloomberg API session"""

    def __init__(self):
        self._session = None
        self._connected = False

    def connect(self) -> bool:
        """Connect to Bloomberg Terminal"""
        if not BLPAPI_AVAILABLE:
            return False

        try:
            sessionOptions = blpapi.SessionOptions()
            sessionOptions.setServerHost("localhost")
            sessionOptions.setServerPort(8194)  # Default Bloomberg port

            self._session = blpapi.Session(sessionOptions)

            if not self._session.start():
                return False

            if not self._session.openService("//blp/refdata"):
                return False

            self._connected = True
            return True

        except Exception as e:
            print(f"Bloomberg connection error: {e}")
            self._connected = False
            return False

    def disconnect(self):
        """Disconnect from Bloomberg"""
        if self._session:
            self._session.stop()
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected and self._session is not None

    def get_reference_data(self, securities: List[str], fields: List[str]) -> Optional[pd.DataFrame]:
        """
        Get reference data for securities.

        Args:
            securities: List of Bloomberg tickers
            fields: List of fields to retrieve

        Returns:
            DataFrame with results
        """
        if not self.is_connected:
            return None

        try:
            refDataService = self._session.getService("//blp/refdata")
            request = refDataService.createRequest("ReferenceDataRequest")

            for sec in securities:
                request.append("securities", sec)
            for field in fields:
                request.append("fields", field)

            self._session.sendRequest(request)

            data = []
            while True:
                event = self._session.nextEvent(500)

                if event.eventType() == blpapi.Event.RESPONSE or \
                   event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                    for msg in event:
                        securityDataArray = msg.getElement("securityData")
                        for i in range(securityDataArray.numValues()):
                            securityData = securityDataArray.getValueAsElement(i)
                            security = securityData.getElementAsString("security")
                            fieldData = securityData.getElement("fieldData")

                            row = {"security": security}
                            for field in fields:
                                if fieldData.hasElement(field):
                                    row[field] = fieldData.getElementValue(field)
                                else:
                                    row[field] = None
                            data.append(row)

                if event.eventType() == blpapi.Event.RESPONSE:
                    break

            return pd.DataFrame(data) if data else None

        except Exception as e:
            print(f"Reference data error: {e}")
            return None

    def get_historical_data(self, security: str, fields: List[str],
                           start_date: str, end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Get historical data for a security.

        Args:
            security: Bloomberg ticker
            fields: List of fields
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with date index
        """
        if not self.is_connected:
            return None

        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        else:
            end_date = end_date.replace('-', '')
        start_date = start_date.replace('-', '')

        try:
            refDataService = self._session.getService("//blp/refdata")
            request = refDataService.createRequest("HistoricalDataRequest")

            request.append("securities", security)
            for field in fields:
                request.append("fields", field)
            request.set("startDate", start_date)
            request.set("endDate", end_date)
            request.set("periodicitySelection", "DAILY")

            self._session.sendRequest(request)

            data = []
            while True:
                event = self._session.nextEvent(500)

                if event.eventType() == blpapi.Event.RESPONSE or \
                   event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                    for msg in event:
                        securityData = msg.getElement("securityData")
                        fieldDataArray = securityData.getElement("fieldData")

                        for i in range(fieldDataArray.numValues()):
                            fieldData = fieldDataArray.getValueAsElement(i)
                            row = {"date": fieldData.getElementAsDatetime("date").date()}
                            for field in fields:
                                if fieldData.hasElement(field):
                                    row[field] = fieldData.getElementValue(field)
                            data.append(row)

                if event.eventType() == blpapi.Event.RESPONSE:
                    break

            if data:
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                return df
            return None

        except Exception as e:
            print(f"Historical data error: {e}")
            return None


# ============================================================================
# STRUCTURED CREDIT DATA
# ============================================================================

# Bloomberg tickers for structured credit
TICKERS = {
    # Rates
    'SOFR': 'SOFRRATE Index',
    'SOFR_1M': 'USOSFR1M Index',
    'SOFR_3M': 'USOSFR3M Index',

    # Treasuries
    'UST_2Y': 'USGG2YR Index',
    'UST_5Y': 'USGG5YR Index',
    'UST_10Y': 'USGG10YR Index',

    # Credit indices
    'CDX_IG': 'CDX IG CDSI GEN 5Y PRC Corp',
    'CDX_HY': 'CDX HY CDSI GEN 5Y PRC Corp',

    # CLO indices (Palmer Square)
    'PS_CLO_AAA': 'PSCLOAAA Index',
    'PS_CLO_AA': 'PSCLOAA Index',
    'PS_CLO_A': 'PSCLOA Index',
    'PS_CLO_BBB': 'PSCLOBBB Index',
    'PS_CLO_BB': 'PSCLOBB Index',
}


class BloombergDataProvider:
    """High-level provider for structured credit data from Bloomberg"""

    def __init__(self):
        self._session = BloombergSession()
        self._connected = False

    def connect(self) -> bool:
        """Connect to Bloomberg Terminal"""
        self._connected = self._session.connect()
        return self._connected

    def disconnect(self):
        """Disconnect from Bloomberg"""
        self._session.disconnect()
        self._connected = False

    @property
    def is_available(self) -> bool:
        """Check if Bloomberg is available"""
        if not BLPAPI_AVAILABLE:
            return False
        if not self._connected:
            self.connect()
        return self._connected

    def get_sofr(self) -> Optional[float]:
        """Get current SOFR rate"""
        if not self.is_available:
            return None

        df = self._session.get_reference_data([TICKERS['SOFR']], ['PX_LAST'])
        if df is not None and not df.empty:
            return df['PX_LAST'].iloc[0]
        return None

    def get_credit_indices(self) -> Optional[Dict[str, float]]:
        """Get CDX levels"""
        if not self.is_available:
            return None

        tickers = [TICKERS['CDX_IG'], TICKERS['CDX_HY']]
        df = self._session.get_reference_data(tickers, ['PX_LAST'])

        if df is not None and not df.empty:
            result = {}
            for _, row in df.iterrows():
                if 'CDX IG' in row['security']:
                    result['CDX IG'] = row['PX_LAST']
                elif 'CDX HY' in row['security']:
                    result['CDX HY'] = row['PX_LAST']
            return result
        return None

    def get_clo_spreads(self) -> Optional[Dict[str, float]]:
        """Get CLO spreads from Palmer Square indices"""
        if not self.is_available:
            return None

        tickers = [
            TICKERS['PS_CLO_AAA'],
            TICKERS['PS_CLO_AA'],
            TICKERS['PS_CLO_A'],
            TICKERS['PS_CLO_BBB'],
            TICKERS['PS_CLO_BB'],
        ]

        df = self._session.get_reference_data(tickers, ['PX_LAST'])

        if df is not None and not df.empty:
            result = {}
            for _, row in df.iterrows():
                sec = row['security']
                if 'PSCLOAAA' in sec:
                    result['CLO AAA'] = row['PX_LAST']
                elif 'PSCLOAA' in sec and 'AAA' not in sec:
                    result['CLO AA'] = row['PX_LAST']
                elif 'PSCLOA' in sec and 'AA' not in sec:
                    result['CLO A'] = row['PX_LAST']
                elif 'PSCLOBBB' in sec:
                    result['CLO BBB'] = row['PX_LAST']
                elif 'PSCLOBB' in sec and 'BBB' not in sec:
                    result['CLO BB'] = row['PX_LAST']
            return result
        return None

    def get_treasury_curve(self) -> Optional[Dict[str, float]]:
        """Get Treasury yields"""
        if not self.is_available:
            return None

        tickers = [TICKERS['UST_2Y'], TICKERS['UST_5Y'], TICKERS['UST_10Y']]
        df = self._session.get_reference_data(tickers, ['PX_LAST'])

        if df is not None and not df.empty:
            result = {}
            for _, row in df.iterrows():
                sec = row['security']
                if '2YR' in sec:
                    result['2Y'] = row['PX_LAST']
                elif '5YR' in sec:
                    result['5Y'] = row['PX_LAST']
                elif '10YR' in sec:
                    result['10Y'] = row['PX_LAST']
            return result
        return None

    def get_deal_pricing(self, cusip: str) -> Optional[Dict]:
        """Get BVAL pricing for a specific ABS tranche"""
        if not self.is_available:
            return None

        ticker = f"{cusip} Mtge"
        fields = ['BVAL_MID_PRICE', 'BVAL_OAS', 'BVAL_DM', 'BVAL_YIELD', 'BVAL_WAL']

        df = self._session.get_reference_data([ticker], fields)
        if df is not None and not df.empty:
            return df.iloc[0].to_dict()
        return None


# Singleton instance
_provider = None

def get_bloomberg_provider() -> BloombergDataProvider:
    """Get the Bloomberg data provider singleton"""
    global _provider
    if _provider is None:
        _provider = BloombergDataProvider()
    return _provider
