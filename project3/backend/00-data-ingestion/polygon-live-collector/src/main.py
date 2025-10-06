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

# Central Hub SDK (installed via pip)
from central_hub_sdk import CentralHubClient

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

        # Central Hub integration
        self.central_hub = CentralHubClient(
            service_name="polygon-live-collector",
            service_type="data-collector",
            version="1.0.0",
            capabilities=[
                "forex-data-collection",
                "real-time-streaming",
                "websocket-ingestion",
                "rest-polling",
                "aggregate-bars",
                "nats-publishing",
                "kafka-publishing"
            ],
            metadata={
                "source": "polygon.io",
                "mode": "live",
                "data_types": ["quotes", "aggregates"],
                "transport": ["nats", "kafka"]
            }
        )

        self.start_time = datetime.now()
        self.is_running = False

        logger.info("=" * 80)
        logger.info("POLYGON.IO LIVE COLLECTOR + CENTRAL HUB")
        logger.info("=" * 80)
        logger.info(f"Instance ID: {self.config.instance_id}")
        logger.info(f"Log Level: {self.config.log_level}")

    async def start(self):
        """Start the collector"""
        try:
            logger.info("🚀 Starting Polygon.io Live Collector...")

            # Register with Central Hub
            await self.central_hub.register()

            # Link config to Central Hub client for later use
            self.config.central_hub = self.central_hub

            # Get messaging configs from Central Hub
            try:
                logger.info("⚙️  Fetching messaging configs from Central Hub...")

                # Fetch and store in config object
                await self.config.fetch_messaging_configs_from_central_hub()

                # Use the fetched configs
                nats_config = self.config.nats_config
                kafka_config = self.config.kafka_config

                logger.info(f"✅ Messaging configs loaded from Central Hub")

            except Exception as e:
                # Fallback already handled by config.py
                logger.warning(f"⚠️  Using fallback configuration")
                nats_config = self.config.nats_config
                kafka_config = self.config.kafka_config

            # Initialize NATS/Kafka publisher with config from Central Hub
            self.publisher = NATSPublisher(
                nats_config=nats_config,
                kafka_config=kafka_config
            )
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
                self._status_reporter()
            ]

            # Add aggregate client if enabled
            if self.aggregate_client:
                tasks.append(self.aggregate_client.connect())

            # Start Central Hub heartbeat if registered
            if self.central_hub.registered:
                tasks.append(self.central_hub.start_heartbeat_loop())

            await asyncio.gather(*tasks)

        except Exception as e:
            logger.error(f"❌ Error starting collector: {e}", exc_info=True)
            await self.stop()

    async def _status_reporter(self):
        """Report status every minute"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Every minute

                # Collect stats
                ws_stats = self.websocket_client.get_stats() if self.websocket_client else {}
                rest_stats = self.rest_poller.get_stats() if self.rest_poller else {}
                agg_stats = self.aggregate_client.get_stats() if self.aggregate_client else {}
                pub_stats = self.publisher.get_stats() if self.publisher else {}

                uptime = datetime.now() - self.start_time

                status_data = {
                    'instance_id': self.config.instance_id,
                    'uptime_seconds': int(uptime.total_seconds()),
                    'websocket': ws_stats,
                    'rest_poller': rest_stats,
                    'aggregate': agg_stats,
                    'publisher': pub_stats,
                    'timestamp': datetime.now().isoformat()
                }

                # Log status
                logger.info("=" * 80)
                logger.info(f"📊 STATUS REPORT - Uptime: {uptime}")
                logger.info(f"WebSocket Quotes: {ws_stats.get('message_count', 0)} messages | Running: {ws_stats.get('is_running', False)}")
                logger.info(f"REST Poller: {rest_stats.get('poll_count', 0)} polls | Running: {rest_stats.get('is_running', False)}")
                logger.info(f"Aggregate Bars: {agg_stats.get('aggregate_count', 0)} bars | Running: {agg_stats.get('is_running', False)}")
                logger.info(f"NATS: {pub_stats.get('nats_publish_count', 0)} published | Connected: {pub_stats.get('nats_connected', False)}")
                logger.info(f"Kafka: {pub_stats.get('kafka_publish_count', 0)} published | Connected: {pub_stats.get('kafka_connected', False)}")
                logger.info("=" * 80)

                # Publish status to NATS
                await self.publisher.publish_status(status_data)

                # Send heartbeat to Central Hub with metrics
                if self.central_hub.registered:
                    await self.central_hub.send_heartbeat(metrics=status_data)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in status reporter: {e}")

    async def stop(self):
        """Stop the collector"""
        logger.info("🛑 Stopping Polygon.io Live Collector...")
        self.is_running = False

        # Deregister from Central Hub
        await self.central_hub.deregister()

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
