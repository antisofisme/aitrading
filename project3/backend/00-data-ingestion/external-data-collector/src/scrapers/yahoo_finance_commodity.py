"""
Yahoo Finance Commodity Collector
Fetches commodity prices from Yahoo Finance
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


class YahooFinanceCommodityCollector:
    """
    Yahoo Finance Commodity Collector

    Fetches commodity futures prices:
    - Gold (GC=F)
    - Crude Oil (CL=F)
    - Silver (SI=F)
    - Copper (HG=F)
    - Natural Gas (NG=F)
    """

    def __init__(
        self,
        symbols: list = None,
        publisher: Optional[ExternalDataPublisher] = None
    ):
        """
        Initialize Yahoo Finance collector

        Args:
            symbols: List of Yahoo Finance commodity symbols
            publisher: Optional NATS+Kafka publisher
        """
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        self.session: Optional[aiohttp.ClientSession] = None
        self.publisher = publisher

        # Commodity symbols
        self.symbols = symbols or [
            'GC=F',   # Gold Futures
            'CL=F',   # Crude Oil Futures
            'SI=F',   # Silver Futures
            'HG=F',   # Copper Futures
            'NG=F'    # Natural Gas Futures
        ]

        logger.info(f"✅ Yahoo Finance collector initialized | Commodities: {len(self.symbols)}")

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
        Collect commodity prices from Yahoo Finance

        Returns: Dictionary with commodity prices
        """
        if not self.session:
            await self.initialize()

        logger.info(f"📊 Fetching Yahoo Finance commodities...")

        try:
            commodity_data = []

            for symbol in self.symbols:
                try:
                    data = await self._fetch_commodity(symbol)
                    if data:
                        commodity_data.append(data)

                        # Publish individual commodity
                        if self.publisher:
                            await self.publisher.publish(
                                data=data,
                                data_type=DataType.COMMODITY_PRICES,
                                metadata={
                                    'source': 'finance.yahoo.com',
                                    'symbol': symbol
                                }
                            )

                except Exception as e:
                    logger.warning(f"⚠️  Failed to fetch {symbol}: {e}")
                    continue

            result = {
                'source': 'finance.yahoo.com',
                'collected_at': datetime.utcnow().isoformat(),
                'commodities_count': len(commodity_data),
                'commodities': commodity_data
            }

            logger.info(f"✅ Yahoo Finance: Collected {len(commodity_data)} commodities")

            return result

        except Exception as e:
            logger.error(f"❌ Yahoo Finance collection error: {e}")
            raise

    async def _fetch_commodity(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch single commodity price

        Args:
            symbol: Yahoo Finance symbol (e.g., 'GC=F')

        Returns: Commodity price data
        """
        try:
            url = f"{self.base_url}/{symbol}"
            params = {
                'interval': '1d',
                'range': '1d'
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} for {symbol}")
                    return None

                result = await response.json()

                # Extract quote data
                chart = result.get('chart', {})
                chart_result = chart.get('result', [])

                if not chart_result:
                    return None

                quote_data = chart_result[0]
                meta = quote_data.get('meta', {})
                indicators = quote_data.get('indicators', {})
                quote = indicators.get('quote', [{}])[0]

                # Get latest price
                close_prices = quote.get('close', [])
                latest_price = close_prices[-1] if close_prices else None

                # Get volume
                volumes = quote.get('volume', [])
                latest_volume = volumes[-1] if volumes else None

                previous_close = meta.get('previousClose')

                return {
                    'symbol': symbol,
                    'name': self._get_commodity_name(symbol),
                    'currency': meta.get('currency', 'USD'),
                    'price': latest_price,
                    'previous_close': previous_close,
                    'change': latest_price - previous_close if latest_price and previous_close else None,
                    'change_percent': ((latest_price - previous_close) / previous_close * 100) if latest_price and previous_close else None,
                    'volume': latest_volume,
                    'updated_at': datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Failed to fetch {symbol}: {e}")
            return None

    def _get_commodity_name(self, symbol: str) -> str:
        """Get human-readable commodity name"""
        names = {
            'GC=F': 'Gold',
            'CL=F': 'Crude Oil',
            'SI=F': 'Silver',
            'HG=F': 'Copper',
            'NG=F': 'Natural Gas'
        }
        return names.get(symbol, symbol)
