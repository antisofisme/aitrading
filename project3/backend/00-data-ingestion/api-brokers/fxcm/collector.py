"""
FXCM Native API Collector - REST API and SocketIO Integration
Handles direct FXCM API connection untuk serve 1000+ users with advanced features
"""

import asyncio
import time
import logging
import json
from datetime import datetime
from typing import List, Dict, Optional

import aiohttp
import socketio
from nats.aio.client import Client as NATS
import sys
import os

# Add shared path for proto imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../01-core-infrastructure/central-hub/shared/generated/python'))

from common.tick_data_pb2 import MarketTick, QualityMetrics, MarketDepth
from trading.broker_data_pb2 import BrokerTick, BrokerInfo

logger = logging.getLogger("fxcm_api_collector")

class FXCMAPICollector:
    """FXCM Native API Data Collector using REST API and SocketIO"""

    def __init__(self, config: Dict):
        self.config = config
        self.broker_name = "fxcm"
        self.broker_type = "native_api"
        self.nats_client: Optional[NATS] = None
        self.instruments = config.get('instruments', [])
        self.is_collecting = False

        # FXCM API specific settings
        self.api_endpoint = config['api_endpoint']
        self.stream_endpoint = config['stream_endpoint']
        self.access_token = config['access_token']
        self.account_id = config.get('account_id', '')

        # HTTP session for REST API calls
        self.session: Optional[aiohttp.ClientSession] = None

        # SocketIO client for real-time streaming
        self.sio = socketio.AsyncClient(
            reconnection=True,
            reconnection_attempts=5,
            reconnection_delay=1
        )

        # Performance tracking
        self.tick_count = 0
        self.last_performance_log = time.time()

        # FXCM API quality tracking
        self.api_metrics = {
            'total_ticks': 0,
            'valid_ticks': 0,
            'api_errors': 0,
            'connection_losses': 0,
            'rate_limits': 0
        }

        # Setup SocketIO event handlers
        self.setup_socketio_handlers()

    async def initialize(self):
        """Initialize FXCM API connection and NATS streaming"""
        try:
            # Create HTTP session for REST API
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
            )

            # Connect to NATS message bus
            self.nats_client = NATS()
            await self.nats_client.connect("nats://nats-server:4222")

            logger.info(f"FXCM API collector initialized successfully")

        except Exception as e:
            logger.error(f"FXCM API initialization failed: {e}")
            raise

    async def authenticate_fxcm_api(self):
        """Authenticate with FXCM API and verify connection"""
        try:
            # Test API connection with account info
            async with self.session.get(f"{self.api_endpoint}/trading/get_model?models=Account") as response:
                if response.status != 200:
                    raise Exception(f"FXCM API authentication failed: {response.status}")

                account_data = await response.json()

                logger.info(f"Connected to FXCM API")
                logger.info(f"Account ID: {self.account_id}")
                logger.info(f"Available instruments: {len(self.instruments)}")
                return True

        except Exception as e:
            logger.error(f"FXCM API authentication failed: {e}")
            return False

    def setup_socketio_handlers(self):
        """Setup SocketIO event handlers for real-time data"""

        @self.sio.event
        async def connect():
            logger.info("Connected to FXCM SocketIO streaming")
            # Subscribe to price updates for all instruments
            for instrument in self.instruments:
                await self.sio.emit('subscribe', {'pairs': [instrument]})

        @self.sio.event
        async def disconnect():
            logger.warning("Disconnected from FXCM SocketIO streaming")
            self.api_metrics['connection_losses'] += 1

        @self.sio.event
        async def price_update(data):
            """Handle real-time price updates from FXCM"""
            try:
                await self.process_fxcm_price_update(data)
            except Exception as e:
                logger.error(f"Error processing FXCM price update: {e}")

    async def connect_to_fxcm_stream(self):
        """Connect to FXCM real-time streaming via SocketIO"""
        try:
            await self.sio.connect(
                self.stream_endpoint,
                headers={'Authorization': f'Bearer {self.access_token}'}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to connect to FXCM streaming: {e}")
            return False

    async def process_fxcm_price_update(self, data):
        """Process real-time price update from FXCM SocketIO"""
        try:
            # FXCM price update format
            # {"Symbol": "EUR/USD", "Rates": [1.08945, 1.08948], "Updated": 1640995200.123}

            if not isinstance(data, dict) or 'Symbol' not in data:
                return

            symbol = data['Symbol'].replace('/', '')  # Convert EUR/USD to EURUSD
            rates = data.get('Rates', [])

            if len(rates) < 2:
                return

            # Convert FXCM data to Protocol Buffer format
            market_tick = MarketTick()
            market_tick.symbol = symbol
            market_tick.bid = float(rates[0])
            market_tick.ask = float(rates[1])
            market_tick.last = float(rates[0])  # Use bid as last for FXCM
            market_tick.volume = 1  # FXCM doesn't provide volume in price updates

            # Timestamp handling
            updated_time = data.get('Updated', time.time())
            market_tick.timestamp = int(updated_time * 1000)

            # Calculated fields
            market_tick.spread = market_tick.ask - market_tick.bid

            # Broker context
            market_tick.broker_source = self.broker_name
            market_tick.broker_type = self.broker_type
            market_tick.broker_timestamp = int(time.time() * 1000)

            # Quality metrics for FXCM API data
            quality = QualityMetrics()
            quality.latency_ms = (time.time() * 1000) - market_tick.timestamp
            quality.confidence = self.calculate_fxcm_tick_confidence(market_tick)
            market_tick.quality.CopyFrom(quality)

            # Stream to aggregator
            await self.stream_to_aggregator(market_tick)

        except Exception as e:
            logger.error(f"Error processing FXCM price update: {e}")
            self.api_metrics['api_errors'] += 1

    def calculate_fxcm_tick_confidence(self, tick: MarketTick) -> float:
        """Calculate FXCM tick data confidence score (0.0 - 1.0)"""
        confidence = 1.0

        # Check spread reasonableness for FXCM
        max_spread = self.config.get('api_settings', {}).get('max_spread', 0.005)
        if tick.spread > max_spread:
            confidence -= 0.3

        # Check timestamp freshness (API should be near real-time)
        age_ms = abs(int(time.time() * 1000) - tick.timestamp)
        if age_ms > 2000:  # 2 seconds tolerance for API
            confidence -= 0.2

        # Basic bid/ask validation
        if tick.bid <= 0 or tick.ask <= 0 or tick.bid >= tick.ask:
            confidence -= 0.5

        return max(0.0, confidence)

    async def get_fxcm_market_depth(self, instrument: str) -> Optional[Dict]:
        """Get FXCM market depth/order book data"""
        try:
            async with self.session.get(
                f"{self.api_endpoint}/trading/get_model",
                params={
                    'models': 'OrderBook',
                    'pairs': instrument
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', {}).get('OrderBook')
                else:
                    logger.warning(f"Failed to get market depth for {instrument}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting FXCM market depth: {e}")
            return None

    async def stream_to_aggregator(self, market_tick: MarketTick):
        """Stream FXCM tick data to Market Aggregator via NATS"""
        try:
            # Serialize protobuf
            binary_data = market_tick.SerializeToString()

            # NATS topic specifically for Native API broker data
            topic = f"api-broker.{self.broker_name}.{market_tick.symbol}.ticks"

            # Publish to NATS message bus
            await self.nats_client.publish(topic, binary_data)

            # Performance tracking
            self.tick_count += 1
            self.api_metrics['total_ticks'] += 1

            if market_tick.quality.confidence >= 0.7:
                self.api_metrics['valid_ticks'] += 1

        except Exception as e:
            logger.error(f"Failed to stream FXCM tick: {e}")

    async def start_api_collection(self):
        """Start main FXCM API data collection"""
        self.is_collecting = True
        logger.info("Starting FXCM API data collection...")

        try:
            # Connect to FXCM streaming
            await self.connect_to_fxcm_stream()

            # Keep connection alive and handle reconnections
            while self.is_collecting:
                # Check connection health
                if not self.sio.connected:
                    logger.warning("FXCM SocketIO disconnected, attempting reconnection...")
                    await self.connect_to_fxcm_stream()

                # Performance logging
                await self.log_api_performance()

                # Wait before next health check
                await asyncio.sleep(30)  # Check every 30 seconds

        except Exception as e:
            logger.error(f"FXCM API collection error: {e}")
        finally:
            self.is_collecting = False

    async def log_api_performance(self):
        """Log FXCM API performance metrics periodically"""
        current_time = time.time()
        if current_time - self.last_performance_log >= 300:  # Every 5 minutes
            ticks_per_5min = self.tick_count
            quality_rate = (self.api_metrics['valid_ticks'] /
                          max(1, self.api_metrics['total_ticks'])) * 100

            logger.info(f"FXCM API Performance - Ticks/5min: {ticks_per_5min}, "
                       f"Quality: {quality_rate:.1f}%, "
                       f"API Errors: {self.api_metrics['api_errors']}, "
                       f"Connected: {self.sio.connected}")

            # Reset counters
            self.tick_count = 0
            self.last_performance_log = current_time

    async def get_api_health_status(self) -> Dict:
        """Get FXCM API collector health status"""
        return {
            "collector": "fxcm",
            "broker_type": "native_api",
            "status": "healthy" if self.is_collecting else "stopped",
            "api_connected": self.session is not None and not self.session.closed,
            "socketio_connected": self.sio.connected,
            "api_endpoint": self.api_endpoint,
            "instruments_count": len(self.instruments),
            "ticks_per_5min": self.tick_count,
            "api_metrics": self.api_metrics.copy(),
            "uptime_seconds": time.time() - (self.last_performance_log - 300),
            "features": {
                "market_depth": True,
                "real_time_streaming": True,
                "order_book": True,
                "historical_data": True
            }
        }

    async def stop_api_collection(self):
        """Stop FXCM API data collection and cleanup"""
        logger.info("Stopping FXCM API collector...")
        self.is_collecting = False

        # Disconnect SocketIO
        if self.sio.connected:
            await self.sio.disconnect()

        # Close HTTP session
        if self.session and not self.session.closed:
            await self.session.close()

        # Close NATS connection
        if self.nats_client:
            await self.nats_client.close()

        logger.info("FXCM API collector stopped")

async def main():
    """Main FXCM API collector entry point"""
    # Load FXCM API configuration
    config = {
        'api_endpoint': 'https://api-demo.fxcm.com',
        'stream_endpoint': 'wss://api-demo.fxcm.com/socket.io/',
        'access_token': 'your_fxcm_access_token',  # Replace with actual token
        'account_id': 'demo_account_123',
        'instruments': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD'],
        'api_settings': {
            'rate_limit_per_minute': 300,
            'connection_timeout': 30,
            'max_spread': 0.005
        }
    }

    collector = FXCMAPICollector(config)

    try:
        await collector.initialize()
        await collector.authenticate_fxcm_api()
        await collector.start_api_collection()

    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"FXCM API collector error: {e}")
    finally:
        await collector.stop_api_collection()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())