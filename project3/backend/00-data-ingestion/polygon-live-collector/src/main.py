#!/usr/bin/env python3
"""
Polygon.io Live Collector
Real-time forex data collection via WebSocket + REST API
Integrated with Central Hub for service coordination
"""
import asyncio
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from websocket_client import PolygonWebSocketClient
from rest_poller import PolygonRESTPoller
from aggregate_client import PolygonAggregateClient
from nats_publisher import NATSPublisher

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class PolygonLiveCollector:
    def __init__(self):
        self.config = Config()
        self.publisher: NATSPublisher = None
        self.websocket_client: PolygonWebSocketClient = None
        self.rest_poller: PolygonRESTPoller = None
        self.aggregate_client: PolygonAggregateClient = None

        self.start_time = datetime.now()
        self.is_running = False

        logger.info("=" * 80)
        logger.info("POLYGON.IO LIVE COLLECTOR")
        logger.info("=" * 80)
        logger.info(f"Instance ID: {self.config.instance_id}")
        logger.info(f"Log Level: {self.config.log_level}")

    async def start(self):
        """Start the collector"""
        try:
            logger.info("🚀 Starting Polygon.io Live Collector...")

            # Get NATS config from environment variables
            nats_config = self.config.nats_config
            logger.info(f"✅ Configuration loaded from environment variables")

            # Initialize NATS publisher (market data streaming)
            self.publisher = NATSPublisher(nats_config=nats_config)
            await self.publisher.connect()

            # Message handlers
            async def handle_tick(tick_data: dict, is_confirmation: bool = False):
                """Handle quote/tick messages"""
                await self.publisher.publish(tick_data, is_confirmation)

            async def handle_aggregate(aggregate_data: dict):
                """Handle OHLCV aggregate messages"""
                await self.publisher.publish_aggregate(aggregate_data)

            # Initialize WebSocket client for real-time pairs
            websocket_subscriptions = self.config.get_websocket_subscriptions()
            logger.info(f"📊 WebSocket subscriptions: {len(websocket_subscriptions)} pairs")

            self.websocket_client = PolygonWebSocketClient(
                api_key=self.config.polygon_api_key,
                subscriptions=websocket_subscriptions,
                message_handler=handle_tick,
                config=self.config.websocket_config
            )

            # Initialize REST poller for confirmation pairs
            confirmation_pairs = self.config.rest_confirmation_pairs
            logger.info(f"📊 REST confirmation pairs: {len(confirmation_pairs)} pairs")

            self.rest_poller = PolygonRESTPoller(
                api_key=self.config.polygon_api_key,
                pairs=confirmation_pairs,
                message_handler=handle_tick,
                config=self.config.rest_config
            )

            # Initialize aggregate client for OHLCV bars (like MT5)
            aggregate_subscriptions = self.config.get_aggregate_subscriptions()
            if aggregate_subscriptions:
                logger.info(f"📊 Aggregate subscriptions: {len(aggregate_subscriptions)} pairs")

                self.aggregate_client = PolygonAggregateClient(
                    api_key=self.config.polygon_api_key,
                    subscriptions=aggregate_subscriptions,
                    message_handler=handle_aggregate,
                    config=self.config.aggregate_config.get('websocket', {})
                )
            else:
                logger.info("⚠️ Aggregate collection disabled")

            self.is_running = True

            # Start WebSocket, REST poller, and Aggregate client concurrently
            logger.info("✅ Starting data collection...")

            tasks = [
                self.websocket_client.connect(),
                self.rest_poller.start(),
                self._heartbeat_reporter()
            ]

            # Add aggregate client if enabled
            if self.aggregate_client:
                tasks.append(self.aggregate_client.connect())

            await asyncio.gather(*tasks)

        except Exception as e:
            logger.error(f"❌ Error starting collector: {e}", exc_info=True)
            await self.stop()

    async def _heartbeat_reporter(self):
        """Heartbeat reporter with standard logging"""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Log every 30 seconds

                # Collect stats
                ws_stats = self.websocket_client.get_stats() if self.websocket_client else {}
                rest_stats = self.rest_poller.get_stats() if self.rest_poller else {}
                agg_stats = self.aggregate_client.get_stats() if self.aggregate_client else {}
                pub_stats = self.publisher.get_stats() if self.publisher else {}

                # Calculate total processed
                total_messages = (
                    ws_stats.get('message_count', 0) +
                    rest_stats.get('poll_count', 0) +
                    agg_stats.get('aggregate_count', 0)
                )

                # Log heartbeat metrics
                logger.info(
                    f"📊 Heartbeat | "
                    f"Total: {total_messages:,} | "
                    f"WS: {ws_stats.get('message_count', 0):,} | "
                    f"REST: {rest_stats.get('poll_count', 0):,} | "
                    f"Agg: {agg_stats.get('aggregate_count', 0):,} | "
                    f"NATS: {pub_stats.get('nats_publish_count', 0):,}"
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat reporter: {e}")

    async def stop(self):
        """Stop the collector"""
        logger.info("🛑 Stopping Polygon.io Live Collector...")
        self.is_running = False

        # Stop components
        if self.websocket_client:
            await self.websocket_client.close()

        if self.rest_poller:
            await self.rest_poller.stop()

        if self.aggregate_client:
            await self.aggregate_client.close()

        if self.publisher:
            await self.publisher.close()

        logger.info("✅ Collector stopped")

    def handle_signal(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}. Shutting down...")
        asyncio.create_task(self.stop())

async def main():
    """Main entry point"""
    collector = PolygonLiveCollector()

    # Register signal handlers
    signal.signal(signal.SIGINT, collector.handle_signal)
    signal.signal(signal.SIGTERM, collector.handle_signal)

    try:
        await collector.start()

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        await collector.stop()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        await collector.stop()
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
