"""
OANDA v20 API Live Tick Data Collector
High-performance real-time data streaming for AI trading system
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import aiohttp
import websockets
from oandapyV20 import API
from oandapyV20.endpoints import PricingStream, InstrumentsCandles
from oandapyV20.exceptions import V20Error

# Import from external-data schemas
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'external-data'))
from schemas.market_data_pb2 import UnifiedMarketData


@dataclass
class OandaConfig:
    """OANDA API configuration"""
    api_token: str
    account_id: str
    environment: str = "practice"  # "practice" or "live"
    instruments: List[str] = None
    stream_timeout: int = 30
    reconnect_attempts: int = 5

    def __post_init__(self):
        if self.instruments is None:
            self.instruments = [
                "EUR_USD", "GBP_USD", "USD_JPY", "USD_CHF",
                "AUD_USD", "USD_CAD", "NZD_USD", "XAU_USD"
            ]


class OandaLiveCollector:
    """
    OANDA v20 API Real-time Data Collector
    Streams live tick data untuk AI trading analysis
    """

    def __init__(self, config: OandaConfig):
        self.config = config
        self.api = API(
            access_token=config.api_token,
            environment=config.environment
        )

        # Connection management
        self.is_connected = False
        self.reconnect_count = 0
        self.session = None

        # Data buffers
        self.tick_buffer = asyncio.Queue()
        self.last_prices = {}

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def _get_api_url(self) -> str:
        """Get API URL based on environment"""
        if self.config.environment == "live":
            return "https://api-fxtrade.oanda.com"
        return "https://api-fxpractice.oanda.com"

    def _get_stream_url(self) -> str:
        """Get streaming URL based on environment"""
        if self.config.environment == "live":
            return "https://stream-fxtrade.oanda.com"
        return "https://stream-fxpractice.oanda.com"

    async def start_price_stream(self) -> None:
        """Start real-time price streaming from OANDA"""
        instruments = ",".join(self.config.instruments)

        stream_params = {
            "instruments": instruments,
            "snapshot": "true"
        }

        try:
            stream_request = PricingStream(
                accountID=self.config.account_id,
                params=stream_params
            )

            self.logger.info(f"Starting OANDA price stream for: {instruments}")

            # Start streaming with automatic reconnection
            while self.reconnect_count < self.config.reconnect_attempts:
                try:
                    async for response in self._stream_with_timeout(stream_request):
                        await self._process_price_update(response)

                except Exception as e:
                    self.logger.error(f"Stream error: {e}")
                    self.reconnect_count += 1

                    if self.reconnect_count < self.config.reconnect_attempts:
                        self.logger.info(f"Reconnecting... Attempt {self.reconnect_count}")
                        await asyncio.sleep(2 ** self.reconnect_count)  # Exponential backoff
                    else:
                        self.logger.error("Max reconnection attempts reached")
                        raise

        except Exception as e:
            self.logger.error(f"Failed to start price stream: {e}")
            raise

    async def _stream_with_timeout(self, stream_request):
        """Stream with timeout handling"""
        try:
            for response in self.api.request(stream_request):
                yield response

                # Reset reconnection counter on successful data
                self.reconnect_count = 0

        except V20Error as e:
            self.logger.error(f"OANDA API error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Stream connection error: {e}")
            raise

    async def _process_price_update(self, response: Dict[str, Any]) -> None:
        """Process incoming price update from OANDA stream"""
        try:
            if response.get("type") == "PRICE":
                # Extract price data
                instrument = response.get("instrument", "")
                time_str = response.get("time", "")
                bids = response.get("bids", [])
                asks = response.get("asks", [])

                if not instrument or not bids or not asks:
                    return

                # Get best bid/ask
                best_bid = float(bids[0]["price"])
                best_ask = float(asks[0]["price"])

                # Calculate spread
                spread = (best_ask - best_bid) * 10000  # In 0.1 pips

                # Parse timestamp
                timestamp = int(datetime.fromisoformat(
                    time_str.replace('Z', '+00:00')
                ).timestamp() * 1000)

                # Create unified market data
                unified_tick = UnifiedMarketData(
                    symbol=instrument.replace("_", ""),  # EUR_USD -> EURUSD
                    timestamp=timestamp,
                    source="OANDA_API",
                    data_type="market_price",

                    # Price data
                    price_close=best_bid,  # Use bid as close price
                    bid=best_bid,
                    ask=best_ask,
                    spread=spread,

                    # Session detection
                    session=self._detect_session(timestamp),

                    # Raw metadata
                    raw_metadata={
                        **response,
                        "collection_timestamp": datetime.now().isoformat(),
                        "collector": "oanda_api_v20"
                    }
                )

                # Buffer the tick for processing
                await self.tick_buffer.put(unified_tick)

                # Update last price cache
                self.last_prices[instrument] = {
                    "bid": best_bid,
                    "ask": best_ask,
                    "timestamp": timestamp
                }

                self.logger.debug(f"Processed {instrument}: {best_bid}/{best_ask}")

        except Exception as e:
            self.logger.error(f"Error processing price update: {e}")

    def _detect_session(self, timestamp: int) -> str:
        """Detect trading session based on timestamp"""
        from datetime import datetime, timezone

        dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
        hour = dt.hour

        # Simplified session detection (UTC time)
        if 22 <= hour or hour < 6:
            return "Sydney"
        elif 0 <= hour < 8:
            return "Tokyo"
        elif 7 <= hour < 16:
            return "London"
        elif 12 <= hour < 22:
            return "NewYork"
        else:
            return "Transition"

    async def get_historical_candles(
        self,
        instrument: str,
        granularity: str = "M1",
        count: int = 100
    ) -> List[UnifiedMarketData]:
        """Get historical OHLC data from OANDA"""
        try:
            params = {
                "granularity": granularity,
                "count": count
            }

            request = InstrumentsCandles(instrument=instrument, params=params)
            response = self.api.request(request)

            candles = []
            for candle_data in response["candles"]:
                if candle_data["complete"]:
                    # Extract OHLC data
                    mid = candle_data["mid"]
                    timestamp = int(datetime.fromisoformat(
                        candle_data["time"].replace('Z', '+00:00')
                    ).timestamp() * 1000)

                    unified_candle = UnifiedMarketData(
                        symbol=instrument.replace("_", ""),
                        timestamp=timestamp,
                        source="OANDA_API",
                        data_type="market_price",

                        # OHLC data
                        price_open=float(mid["o"]),
                        price_high=float(mid["h"]),
                        price_low=float(mid["l"]),
                        price_close=float(mid["c"]),
                        volume=int(candle_data["volume"]),

                        # Metadata
                        raw_metadata={
                            "granularity": granularity,
                            "complete": candle_data["complete"],
                            "collector": "oanda_api_v20"
                        }
                    )

                    candles.append(unified_candle)

            return candles

        except Exception as e:
            self.logger.error(f"Error fetching historical candles: {e}")
            return []

    async def get_latest_ticks(self, max_ticks: int = 100) -> List[UnifiedMarketData]:
        """Get latest ticks from buffer"""
        ticks = []

        try:
            while len(ticks) < max_ticks and not self.tick_buffer.empty():
                tick = await self.tick_buffer.get()
                ticks.append(tick)

        except asyncio.QueueEmpty:
            pass

        return ticks

    async def get_account_summary(self) -> Dict[str, Any]:
        """Get OANDA account summary"""
        try:
            from oandapyV20.endpoints import AccountSummary

            request = AccountSummary(accountID=self.config.account_id)
            response = self.api.request(request)

            return response["account"]

        except Exception as e:
            self.logger.error(f"Error fetching account summary: {e}")
            return {}

    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status"""
        return {
            "is_connected": self.is_connected,
            "reconnect_count": self.reconnect_count,
            "last_prices": self.last_prices,
            "buffer_size": self.tick_buffer.qsize(),
            "environment": self.config.environment,
            "instruments": self.config.instruments
        }


# Example usage and testing
async def main():
    """Example usage of OANDA collector"""
    config = OandaConfig(
        api_token="your_oanda_token",
        account_id="your_account_id",
        environment="practice",
        instruments=["EUR_USD", "GBP_USD", "USD_JPY"]
    )

    async with OandaLiveCollector(config) as collector:
        print("Starting OANDA live data collection...")

        # Start price streaming (this will run indefinitely)
        try:
            await collector.start_price_stream()
        except KeyboardInterrupt:
            print("Stopping data collection...")


if __name__ == "__main__":
    asyncio.run(main())