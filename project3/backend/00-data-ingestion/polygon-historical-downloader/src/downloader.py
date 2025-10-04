"""
Polygon.io Historical Data Downloader
Downloads historical forex data via REST API
"""
import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import aiohttp
from tqdm import tqdm
import time

from config import PairConfig

logger = logging.getLogger(__name__)

class PolygonHistoricalDownloader:
    def __init__(self, api_key: str, config: dict):
        self.api_key = api_key
        self.config = config

        self.base_url = "https://api.polygon.io/v2"
        self.download_count = 0
        self.error_count = 0

    async def download_pair_history(
        self,
        pair: PairConfig,
        start_date: str,
        end_date: str,
        timeframe: str = "minute",
        multiplier: int = 1
    ) -> List[Dict]:
        """
        Download historical data for a pair

        API: GET /v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}
        Example: /v2/aggs/ticker/C:EURUSD/range/1/minute/2023-01-01/2023-01-31
        """
        all_data = []

        try:
            logger.info(f"📥 Downloading {pair.symbol} from {start_date} to {end_date} ({multiplier}{timeframe})")

            # Build URL
            ticker = pair.polygon_symbol
            url = f"{self.base_url}/aggs/ticker/{ticker}/range/{multiplier}/{timeframe}/{start_date}/{end_date}"

            params = {
                'apiKey': self.api_key,
                'adjusted': 'true',
                'sort': 'asc',
                'limit': self.config.get('batch_size', 50000)
            }

            # Fetch data with pagination
            async with aiohttp.ClientSession() as session:
                next_url = url

                while next_url:
                    # Rate limit
                    await asyncio.sleep(self.config.get('rate_limit_delay', 0.2))

                    # Always pass API key (Polygon next_url doesn't include it)
                    request_params = params if next_url == url else {'apiKey': self.api_key}
                    async with session.get(next_url, params=request_params) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"API error {response.status} for {pair.symbol}: {error_text}")
                            self.error_count += 1
                            break

                        data = await response.json()

                        # Check response
                        if data.get('status') != 'OK':
                            logger.warning(f"API returned non-OK status for {pair.symbol}: {data.get('status')}")
                            break

                        # Extract results
                        results = data.get('results', [])
                        if not results:
                            logger.info(f"No more data for {pair.symbol}")
                            break

                        # Parse results
                        for bar in results:
                            parsed = self._parse_aggregate(bar, pair)
                            if parsed:
                                all_data.append(parsed)

                        self.download_count += len(results)

                        logger.info(f"Downloaded {len(results)} bars for {pair.symbol} (Total: {len(all_data)})")

                        # Check for next page
                        next_url = data.get('next_url')

            logger.info(f"✅ Downloaded {len(all_data)} total bars for {pair.symbol}")

            return all_data

        except asyncio.TimeoutError:
            logger.error(f"Timeout downloading {pair.symbol}")
            self.error_count += 1
            return []

        except Exception as e:
            logger.error(f"Error downloading {pair.symbol}: {e}")
            self.error_count += 1
            return []

    def _parse_aggregate(self, bar: dict, pair: PairConfig) -> Optional[dict]:
        """
        Parse aggregate bar from Polygon.io

        Bar format:
        {
            "v": 1000,        # Volume
            "vw": 1.0850,     # Volume weighted average price
            "o": 1.0848,      # Open
            "c": 1.0852,      # Close
            "h": 1.0855,      # High
            "l": 1.0845,      # Low
            "t": 1577836800000, # Timestamp (Unix MS)
            "n": 100          # Number of transactions
        }
        """
        try:
            # Extract OHLC
            open_price = float(bar.get('o', 0))
            high_price = float(bar.get('h', 0))
            low_price = float(bar.get('l', 0))
            close_price = float(bar.get('c', 0))
            volume = int(bar.get('v', 0))
            vwap = float(bar.get('vw', 0))
            num_trades = int(bar.get('n', 0))

            # Timestamp
            timestamp_ms = int(bar.get('t', 0))
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000.0)

            # Calculate bid/ask estimates (use close as mid, spread ~0.0002)
            # This is an approximation since historical aggregates don't have bid/ask
            spread = 0.0001  # ~1 pip spread estimate
            bid = close_price - spread
            ask = close_price + spread

            return {
                'symbol': pair.symbol,
                'timestamp': timestamp.isoformat(),
                'timestamp_ms': timestamp_ms,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'bid': bid,  # Estimated
                'ask': ask,  # Estimated
                'mid': close_price,
                'volume': volume,
                'vwap': vwap,
                'num_trades': num_trades,
                'source': 'polygon_historical'
            }

        except Exception as e:
            logger.error(f"Error parsing bar: {e}")
            return None

    async def download_all_pairs(
        self,
        pairs: List[PairConfig],
        start_date: str,
        end_date: str,
        get_timeframe_func
    ) -> Dict[str, List[Dict]]:
        """
        Download historical data for all pairs

        Returns: Dict of {symbol: [bars]}
        """
        results = {}

        # Download in priority order
        sorted_pairs = sorted(pairs, key=lambda p: p.priority)

        for pair in sorted_pairs:
            timeframe, multiplier = get_timeframe_func(pair)

            logger.info(f"📊 Starting download for {pair.symbol} (Priority {pair.priority})")

            bars = await self.download_pair_history(
                pair=pair,
                start_date=start_date,
                end_date=end_date,
                timeframe=timeframe,
                multiplier=multiplier
            )

            results[pair.symbol] = bars

            logger.info(f"✅ Completed {pair.symbol}: {len(bars)} bars")

        return results

    def get_stats(self) -> dict:
        """Get downloader statistics"""
        return {
            'download_count': self.download_count,
            'error_count': self.error_count
        }
