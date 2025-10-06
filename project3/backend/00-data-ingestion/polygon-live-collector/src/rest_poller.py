"""
Polygon.io REST API Poller
For confirmation pairs (3-minute interval)
"""
import asyncio
import logging
from typing import Callable, List, Optional
from datetime import datetime
import aiohttp
from config import PairConfig

logger = logging.getLogger(__name__)

class PolygonRESTPoller:
    def __init__(
        self,
        api_key: str,
        pairs: List[PairConfig],
        message_handler: Callable,
        config: dict
    ):
        self.api_key = api_key
        self.pairs = pairs
        self.message_handler = message_handler
        self.config = config

        self.base_url = config.get('base_url', 'https://api.polygon.io/v2')
        self.is_running = False
        self.poll_count = 0

        logger.info(f"Initialized REST poller for {len(pairs)} confirmation pairs")

    async def start(self):
        """Start polling confirmation pairs"""
        self.is_running = True
        logger.info("🔄 Starting REST API poller...")

        # Create polling tasks for each pair
        tasks = []
        for pair in self.pairs:
            task = asyncio.create_task(self._poll_pair(pair))
            tasks.append(task)

        # Wait for all tasks
        await asyncio.gather(*tasks)

    async def _poll_pair(self, pair: PairConfig):
        """Poll a single pair at configured interval"""
        interval = pair.poll_interval or 180  # Default 3 minutes

        logger.info(f"📊 Polling {pair.symbol} every {interval}s")

        while self.is_running:
            try:
                # Fetch latest quote
                quote_data = await self._fetch_latest_quote(pair)

                if quote_data:
                    # Send to message handler
                    await self.message_handler(quote_data, is_confirmation=True)
                    self.poll_count += 1

                # Wait for next interval
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error polling {pair.symbol}: {e}")
                await asyncio.sleep(10)  # Wait 10s on error

    async def _fetch_latest_quote(self, pair: PairConfig) -> Optional[dict]:
        """
        Fetch latest quote from Polygon.io REST API

        Endpoint: GET /v1/last_quote/currencies/{from}/{to}
        Example: /v1/last_quote/currencies/NZD/USD
        """
        try:
            # Parse symbol (NZD/USD → NZD, USD)
            parts = pair.symbol.split('/')
            if len(parts) != 2:
                logger.error(f"Invalid symbol format: {pair.symbol}")
                return None

            from_currency, to_currency = parts

            # Build URL
            url = f"https://api.polygon.io/v1/last_quote/currencies/{from_currency}/{to_currency}"

            params = {
                'apiKey': self.api_key
            }

            # Fetch data
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=30) as response:
                    if response.status != 200:
                        logger.error(f"API error {response.status} for {pair.symbol}")
                        return None

                    data = await response.json()

                    # Parse response
                    if data.get('status') != 'success':
                        logger.warning(f"API returned non-success status for {pair.symbol}")
                        return None

                    last_quote = data.get('last', {})

                    # Extract prices
                    bid = float(last_quote.get('bid', 0))
                    ask = float(last_quote.get('ask', 0))

                    if bid == 0 or ask == 0:
                        logger.warning(f"Zero prices for {pair.symbol}")
                        return None

                    # Calculate spread and mid
                    spread = round((ask - bid) * 10000, 2)  # pips
                    mid = round((ask + bid) / 2, 5)

                    # Timestamp (keep as Unix milliseconds for Data Bridge)
                    timestamp_ms = last_quote.get('timestamp', int(datetime.now().timestamp() * 1000))
                    timestamp = timestamp_ms  # Data Bridge expects Unix milliseconds

                    return {
                        'symbol': pair.symbol,
                        'bid': bid,
                        'ask': ask,
                        'mid': mid,
                        'spread': spread,
                        'timestamp': timestamp,
                        'timestamp_ms': timestamp_ms,
                        'source': 'polygon_rest',
                        'event_type': 'confirmation',
                        'use_case': pair.use_case
                    }

        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {pair.symbol}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {pair.symbol}: {e}")
            return None

    async def stop(self):
        """Stop polling"""
        logger.info("Stopping REST poller...")
        self.is_running = False

    def get_stats(self) -> dict:
        """Get poller statistics"""
        return {
            'is_running': self.is_running,
            'poll_count': self.poll_count,
            'pairs': len(self.pairs)
        }
