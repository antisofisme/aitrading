#!/usr/bin/env python3
"""
Data Bridge - NATS+Kafka Consumer with Database Manager Integration
Implements dual-subscribe pattern with Database Manager for storage
Phase 1: TimescaleDB + DragonflyDB via Database Manager
"""
import asyncio
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, '/app/central-hub/shared')  # Access to Database Manager

from config import Config
from deduplicator import Deduplicator
from nats_subscriber import NATSSubscriber
from kafka_subscriber import KafkaSubscriber

# Import Database Manager from Central Hub
from components.data_manager import DataRouter, TickData, CandleData

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class DataBridge:
    """
    Main orchestrator for Data Bridge

    Architecture:
    1. Subscribe to BOTH NATS (fast) and Kafka (reliable)
    2. Deduplicate messages (same message from both sources)
    3. Use Database Manager to route data to optimal databases

    Data Flow:
    NATS/Kafka → Data Bridge → Database Manager → [TimescaleDB + DragonflyDB]

    Result: ZERO data loss, high performance, smart routing
    """

    def __init__(self):
        self.config = Config()

        # Database Manager (replaces ClickHouseClient)
        self.db_router = None

        self.deduplicator = None
        self.nats_subscriber = None
        self.kafka_subscriber = None

        self.start_time = datetime.utcnow()
        self.is_running = False

        # Statistics
        self.ticks_saved = 0
        self.candles_saved = 0

        logger.info("=" * 80)
        logger.info("DATA BRIDGE - NATS+KAFKA → DATABASE MANAGER")
        logger.info("=" * 80)
        logger.info(f"Instance ID: {self.config.instance_id}")
        logger.info(f"Log Level: {self.config.log_level}")

    async def start(self):
        """Start the Data Bridge"""
        try:
            logger.info("🚀 Starting Data Bridge...")

            # Initialize Central Hub client and fetch configs
            logger.info("📡 Connecting to Central Hub...")
            await self.config.initialize_central_hub()
            logger.info("✅ Central Hub configuration loaded")

            # Initialize Database Manager
            logger.info("📦 Initializing Database Manager...")
            self.db_router = DataRouter()
            await self.db_router.initialize()
            logger.info("✅ Database Manager ready (TimescaleDB + DragonflyDB)")

            # Initialize deduplicator
            self.deduplicator = Deduplicator(self.config.dedup_config)

            # Message handler (called by both NATS and Kafka)
            async def handle_message(data: dict, data_type: str):
                """
                Central message handler

                Args:
                    data: Message data
                    data_type: "tick" or "aggregate"
                """
                source = data.get('_source', 'unknown')

                # Generate message ID for deduplication
                message_id = self.deduplicator.generate_message_id(data)

                # Check for duplicates
                if self.deduplicator.is_duplicate(message_id, source):
                    # Skip duplicate (already processed from other source)
                    logger.debug(f"Skipped duplicate {data_type} from {source}: {message_id}")
                    return

                # Process message based on type
                try:
                    if data_type == 'tick':
                        await self._save_tick(data)
                    elif data_type == 'aggregate':
                        await self._save_candle(data)
                    else:
                        logger.warning(f"Unknown data type: {data_type}")

                    # Mark as processed
                    self.deduplicator.mark_processed(data, source)

                except Exception as e:
                    logger.error(f"Error processing {data_type}: {e}")
                    # Don't mark as processed if save failed
                    # Will be retried from Kafka backup

            # Initialize NATS subscriber (PRIMARY path)
            self.nats_subscriber = NATSSubscriber(
                config=self.config.nats_config,
                message_handler=handle_message
            )
            await self.nats_subscriber.connect()
            await self.nats_subscriber.subscribe_all()

            # Initialize Kafka subscriber (BACKUP path)
            self.kafka_subscriber = KafkaSubscriber(
                config=self.config.kafka_config,
                message_handler=handle_message
            )
            await self.kafka_subscriber.connect()

            self.is_running = True

            logger.info("=" * 80)
            logger.info("✅ DATA BRIDGE STARTED")
            logger.info("📊 NATS: Real-time data path (PRIMARY)")
            logger.info("📊 Kafka: Backup + gap-filling (COMPLEMENTARY)")
            logger.info("🔍 Deduplication: ENABLED")
            logger.info("💾 Storage: Database Manager (TimescaleDB + DragonflyDB)")
            logger.info("=" * 80)

            # Run Kafka poller and status reporter concurrently
            await asyncio.gather(
                self.kafka_subscriber.poll_messages(),
                self._status_reporter()
            )

        except Exception as e:
            logger.error(f"❌ Error starting Data Bridge: {e}", exc_info=True)
            await self.stop()

    async def _save_tick(self, data: dict):
        """
        Save tick data via Database Manager

        Maps Polygon data → TickData model
        """
        try:
            # Map Polygon data to TickData
            tick_data = TickData(
                symbol=data.get('pair', data.get('symbol', '')),
                timestamp=data.get('t', data.get('timestamp', 0)),
                timestamp_ms=data.get('t', data.get('timestamp_ms', 0)),
                bid=data.get('b', data.get('bid', 0)),
                ask=data.get('a', data.get('ask', 0)),
                volume=data.get('s', data.get('volume')),
                source=data.get('_source', 'unknown'),
                exchange=data.get('x', data.get('exchange')),
                event_type=data.get('ev', 'quote')
            )

            # Save via Database Manager
            # → Auto-routes to TimescaleDB + DragonflyDB cache
            await self.db_router.save_tick(tick_data)

            self.ticks_saved += 1

            if self.ticks_saved % 100 == 0:
                logger.debug(f"Saved {self.ticks_saved} ticks")

        except Exception as e:
            logger.error(f"Error saving tick: {e}")
            logger.debug(f"Tick data: {data}")
            raise

    async def _save_candle(self, data: dict):
        """
        Save candle/aggregate data via Database Manager

        Maps Polygon aggregate → CandleData model
        """
        try:
            # Determine timeframe from subject/topic
            timeframe = data.get('timeframe', '1s')
            if not timeframe and '_subject' in data:
                # Extract from NATS subject: bars.EURUSD.1m → 1m
                parts = data['_subject'].split('.')
                if len(parts) >= 3:
                    timeframe = parts[2]

            # Map Polygon aggregate to CandleData
            candle_data = CandleData(
                symbol=data.get('pair', data.get('symbol', '')),
                timeframe=timeframe,
                timestamp=data.get('s', data.get('timestamp', 0)),
                timestamp_ms=data.get('s', data.get('timestamp_ms', 0)),
                open=data.get('o', data.get('open', 0)),
                high=data.get('h', data.get('high', 0)),
                low=data.get('l', data.get('low', 0)),
                close=data.get('c', data.get('close', 0)),
                volume=data.get('v', data.get('volume')),
                vwap=data.get('vw', data.get('vwap')),
                num_trades=data.get('n', data.get('num_trades')),
                source=data.get('_source', 'unknown'),
                event_type=data.get('ev', 'ohlcv')
            )

            # Save via Database Manager
            # → Auto-routes to TimescaleDB + DragonflyDB cache
            await self.db_router.save_candle(candle_data)

            self.candles_saved += 1

            if self.candles_saved % 100 == 0:
                logger.debug(f"Saved {self.candles_saved} candles")

        except Exception as e:
            logger.error(f"Error saving candle: {e}")
            logger.debug(f"Candle data: {data}")
            raise

    async def _status_reporter(self):
        """Report status periodically"""
        interval = self.config.monitoring_config.get('report_interval_seconds', 60)

        while self.is_running:
            try:
                await asyncio.sleep(interval)

                # Collect statistics
                uptime = datetime.utcnow() - self.start_time

                nats_stats = self.nats_subscriber.get_stats() if self.nats_subscriber else {}
                kafka_stats = self.kafka_subscriber.get_stats() if self.kafka_subscriber else {}
                dedup_stats = self.deduplicator.get_stats() if self.deduplicator else {}

                # Log status
                logger.info("=" * 80)
                logger.info(f"📊 STATUS REPORT - Uptime: {uptime}")
                logger.info(f"NATS Messages: {nats_stats.get('total_messages', 0)} | "
                           f"Ticks: {nats_stats.get('tick_messages', 0)} | "
                           f"Aggregates: {nats_stats.get('aggregate_messages', 0)}")
                logger.info(f"Kafka Messages: {kafka_stats.get('total_messages', 0)} | "
                           f"Ticks: {kafka_stats.get('tick_messages', 0)} | "
                           f"Aggregates: {kafka_stats.get('aggregate_messages', 0)}")
                logger.info(f"Deduplication: {dedup_stats.get('total_duplicates', 0)} duplicates | "
                           f"Rate: {dedup_stats.get('duplicate_rate', 0):.2%} | "
                           f"Cache size: {dedup_stats.get('cache_size', 0)}")
                logger.info(f"Database: {self.ticks_saved} ticks saved | "
                           f"{self.candles_saved} candles saved")
                logger.info("=" * 80)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in status reporter: {e}")

    async def stop(self):
        """Stop the Data Bridge"""
        logger.info("🛑 Stopping Data Bridge...")
        self.is_running = False

        # Stop subscribers
        if self.nats_subscriber:
            await self.nats_subscriber.close()

        if self.kafka_subscriber:
            await self.kafka_subscriber.close()

        logger.info("✅ Data Bridge stopped")

    def handle_signal(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}. Shutting down...")
        asyncio.create_task(self.stop())

async def main():
    """Main entry point"""
    bridge = DataBridge()

    # Register signal handlers
    signal.signal(signal.SIGINT, bridge.handle_signal)
    signal.signal(signal.SIGTERM, bridge.handle_signal)

    try:
        await bridge.start()

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        await bridge.stop()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        await bridge.stop()
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
