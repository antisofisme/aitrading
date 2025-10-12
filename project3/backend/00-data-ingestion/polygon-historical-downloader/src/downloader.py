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
        Parse aggregate bar from Polygon.io with data quality validation

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

        Validation:
        - OHLC must not be None, 0, or NaN
        - Reject incomplete/invalid bars (don't insert bad data)
        """
        try:
            # Extract OHLC - DO NOT default to 0, use None to detect missing
            open_price = bar.get('o')
            high_price = bar.get('h')
            low_price = bar.get('l')
            close_price = bar.get('c')
            volume = bar.get('v', 0)
            vwap = bar.get('vw')
            num_trades = bar.get('n', 0)
            timestamp_ms = bar.get('t')

            # CRITICAL: Validate data completeness
            # Reject bars with missing or invalid OHLC
            if open_price is None or high_price is None or low_price is None or close_price is None:
                logger.warning(
                    f"⚠️ [DataQuality] {pair.symbol}: Skipping bar with NULL OHLC values "
                    f"(o={open_price}, h={high_price}, l={low_price}, c={close_price})"
                )
                return None

            if timestamp_ms is None or timestamp_ms == 0:
                logger.warning(f"⚠️ [DataQuality] {pair.symbol}: Skipping bar with invalid timestamp")
                return None

            # Convert to float and validate not 0
            try:
                open_price = float(open_price)
                high_price = float(high_price)
                low_price = float(low_price)
                close_price = float(close_price)
                volume = int(volume)
                timestamp_ms = int(timestamp_ms)
            except (ValueError, TypeError) as e:
                logger.warning(f"⚠️ [DataQuality] {pair.symbol}: Invalid numeric values: {e}")
                return None

            # Validate OHLC are positive (forex prices never 0)
            if open_price <= 0 or high_price <= 0 or low_price <= 0 or close_price <= 0:
                logger.warning(
                    f"⚠️ [DataQuality] {pair.symbol}: Skipping bar with zero/negative prices "
                    f"(o={open_price}, h={high_price}, l={low_price}, c={close_price})"
                )
                return None

            # Validate price logic (high >= low, open/close within range)
            if high_price < low_price:
                logger.warning(
                    f"⚠️ [DataQuality] {pair.symbol}: Invalid bar - high < low "
                    f"(h={high_price}, l={low_price})"
                )
                return None

            if open_price < low_price or open_price > high_price:
                logger.warning(
                    f"⚠️ [DataQuality] {pair.symbol}: Invalid bar - open outside range "
                    f"(o={open_price}, h={high_price}, l={low_price})"
                )
                return None

            if close_price < low_price or close_price > high_price:
                logger.warning(
                    f"⚠️ [DataQuality] {pair.symbol}: Invalid bar - close outside range "
                    f"(c={close_price}, h={high_price}, l={low_price})"
                )
                return None

            # Timestamp
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000.0)

            # VWAP optional (some bars may not have it)
            if vwap is not None:
                try:
                    vwap = float(vwap)
                except (ValueError, TypeError):
                    vwap = close_price  # Fallback to close

            else:
                vwap = close_price

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
            logger.error(f"❌ [DataQuality] Error parsing bar for {pair.symbol}: {e}")
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

    async def download_range(
        self,
        symbol: str,
        from_date: str,
        to_date: str,
        timeframe: str = "minute",
        multiplier: int = 1
    ) -> List[Dict]:
        """
        Download data for a specific symbol and date range (for gap filling)

        Args:
            symbol: Symbol name (e.g., 'EUR/USD')
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            timeframe: minute/hour/day/week
            multiplier: Interval multiplier (1, 5, 15, etc.)

        Returns:
            List of parsed bars
        """
        try:
            # Create a temporary PairConfig for this symbol
            # Convert symbol format: EUR/USD → C:EURUSD for Polygon API
            polygon_symbol = f"C:{symbol.replace('/', '')}"

            pair = PairConfig(
                symbol=symbol,
                polygon_symbol=polygon_symbol,
                priority=1  # Not used for gap filling
            )

            logger.info(f"📥 Gap filling: Downloading {symbol} from {from_date} to {to_date}")

            # Use existing download_pair_history method
            bars = await self.download_pair_history(
                pair=pair,
                start_date=from_date,
                end_date=to_date,
                timeframe=timeframe,
                multiplier=multiplier
            )

            return bars

        except Exception as e:
            logger.error(f"❌ Error in download_range for {symbol}: {e}")
            self.error_count += 1
            return []

    def get_stats(self) -> dict:
        """Get downloader statistics"""
        return {
            'download_count': self.download_count,
            'error_count': self.error_count
        }
