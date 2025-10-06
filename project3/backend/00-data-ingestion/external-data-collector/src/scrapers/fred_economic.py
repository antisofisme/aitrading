"""
FRED Economic Data Collector
Fetches economic indicators from Federal Reserve Economic Data (FRED)
"""
import logging
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from publishers import ExternalDataPublisher, DataType

logger = logging.getLogger(__name__)


class FREDEconomicCollector:
    """
    FRED Economic Data Collector

    Fetches economic indicators like GDP, unemployment, CPI, interest rates, etc.
    """

    def __init__(
        self,
        api_key: str,
        indicators: list = None,
        publisher: Optional[ExternalDataPublisher] = None
    ):
        """
        Initialize FRED collector

        Args:
            api_key: FRED API key
            indicators: List of FRED series IDs to track
            publisher: Optional NATS+Kafka publisher
        """
        self.api_key = api_key
        self.base_url = "https://api.stlouisfed.org/fred"
        self.session: Optional[aiohttp.ClientSession] = None
        self.publisher = publisher

        # Economic indicators to track
        self.indicators = indicators or [
            'GDP',       # Gross Domestic Product
            'UNRATE',    # Unemployment Rate
            'CPIAUCSL',  # Consumer Price Index
            'DFF',       # Federal Funds Rate
            'DGS10',     # 10-Year Treasury Rate
            'DEXUSEU',   # USD/EUR Exchange Rate
            'DEXJPUS'    # JPY/USD Exchange Rate
        ]

        logger.info(f"✅ FRED collector initialized | Indicators: {len(self.indicators)}")

    async def initialize(self):
        """Initialize HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()

    async def collect(self) -> Dict[str, Any]:
        """
        Collect economic indicators from FRED

        Returns: Dictionary with all indicators
        """
        if not self.session:
            await self.initialize()

        logger.info(f"📊 Fetching FRED economic indicators...")

        try:
            all_indicators = {}

            for indicator in self.indicators:
                try:
                    data = await self._fetch_indicator(indicator)
                    if data:
                        all_indicators[indicator] = data

                        # Publish individual indicator
                        if self.publisher:
                            await self.publisher.publish(
                                data=data,
                                data_type=DataType.FRED_ECONOMIC,
                                metadata={
                                    'source': 'fred.stlouisfed.org',
                                    'indicator': indicator
                                }
                            )

                except Exception as e:
                    logger.warning(f"⚠️  Failed to fetch {indicator}: {e}")
                    continue

            result = {
                'source': 'fred.stlouisfed.org',
                'collected_at': datetime.utcnow().isoformat(),
                'indicators_count': len(all_indicators),
                'indicators': all_indicators
            }

            logger.info(f"✅ FRED: Collected {len(all_indicators)} indicators")

            return result

        except Exception as e:
            logger.error(f"❌ FRED collection error: {e}")
            raise

    async def _fetch_indicator(self, series_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch single indicator from FRED

        Args:
            series_id: FRED series ID (e.g., 'GDP', 'UNRATE')

        Returns: Latest value and metadata
        """
        try:
            url = f"{self.base_url}/series/observations"
            params = {
                'series_id': series_id,
                'api_key': self.api_key,
                'file_type': 'json',
                'sort_order': 'desc',  # Latest first
                'limit': 1
            }

            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} for {series_id}")
                    return None

                result = await response.json()

                if 'observations' not in result or not result['observations']:
                    return None

                latest = result['observations'][0]

                return {
                    'series_id': series_id,
                    'value': float(latest['value']) if latest['value'] != '.' else None,
                    'date': latest['date'],
                    'updated_at': datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Failed to fetch {series_id}: {e}")
            return None
