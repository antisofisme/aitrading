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
from clickhouse_writer import ClickHouseWriter
from external_data_writer import ExternalDataWriter

# Import Database Manager from Central Hub
from components.data_manager import DataRouter, TickData, CandleData

# Central Hub SDK for heartbeat logging
from central_hub_sdk import HeartbeatLogger

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

        # Database Manager (for Live data → TimescaleDB + DragonflyDB)
        self.db_router = None

        # ClickHouse Writer (for Historical data → ClickHouse)
        self.clickhouse_writer = None

        # External Data Writer (for External data → ClickHouse)
        self.external_data_writer = None

        self.deduplicator = None
        self.nats_subscriber = None
        self.kafka_subscriber = None

        self.start_time = datetime.utcnow()
        self.is_running = False

        # Statistics
        self.ticks_saved = 0
        self.candles_saved_timescale = 0
        self.candles_saved_clickhouse = 0
        self.external_data_saved = 0

        # HeartbeatLogger for live service monitoring
        self.heartbeat_logger = None

        logger.info("=" * 80)
        logger.info("DATA BRIDGE - INTELLIGENT ROUTING")
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

            # Initialize Database Manager with Central Hub configs (Live → TimescaleDB)
            logger.info("📦 Initializing Database Manager for Live data...")
            from components.data_manager.pools import get_pool_manager

            # Get database configs from Central Hub
            db_configs = self.config.database_configs

            # Initialize pool manager with Central Hub configs
            pool_manager = await get_pool_manager(configs=db_configs)

            # Initialize DataRouter (will use the pool manager we just created)
            self.db_router = DataRouter()
            await self.db_router.initialize()
            logger.info("✅ Database Manager ready (TimescaleDB + DragonflyDB)")

            # Initialize ClickHouse Writer (Historical → ClickHouse)
            logger.info("📦 Initializing ClickHouse Writer for Historical data...")
            clickhouse_config = self.config.database_configs.get('clickhouse')
            if clickhouse_config:
                self.clickhouse_writer = ClickHouseWriter(
                    config=clickhouse_config,
                    batch_size=1000,  # Larger batches for historical data
                    batch_timeout=10.0  # 10 seconds
                )
                await self.clickhouse_writer.connect()
                logger.info("✅ ClickHouse Writer ready")

                # Initialize External Data Writer (External → ClickHouse)
                logger.info("📦 Initializing External Data Writer...")
                self.external_data_writer = ExternalDataWriter(clickhouse_config)
                await self.external_data_writer.connect()
                logger.info("✅ External Data Writer ready")
            else:
                logger.warning("⚠️  ClickHouse config not found, historical/external data will not be saved")

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

                # DEBUG: Log flow for first 10 messages
                if self.ticks_saved < 10 or self.ticks_saved % 100 == 0:
                    logger.info(f"🔍 handle_message | type={data_type} | source={source} | msg_id={message_id[:30]}")

                # Check for duplicates
                if self.deduplicator.is_duplicate(message_id, source):
                    # Skip duplicate (already processed from other source)
                    logger.debug(f"⏭️  Skipped duplicate {data_type} from {source}")
                    return

                # Process message based on type
                try:
                    logger.info(f"💾 Processing {data_type} from {source}...")

                    if data_type == 'tick':
                        # Tick data → TimescaleDB.market_ticks
                        await self._save_tick(data)
                        logger.info(f"✅ Tick saved successfully")
                    elif data_type == 'aggregate':
                        # Aggregate data → ClickHouse.aggregates (live_aggregated or historical)
                        await self._save_candle(data)
                        logger.info(f"✅ Candle saved successfully")
                    elif data_type == 'external':
                        # External data → ClickHouse.external_* tables
                        await self._save_external_data(data)
                        logger.info(f"✅ External data saved successfully")
                    else:
                        logger.warning(f"⚠️  Unknown data type: {data_type}")

                    # Mark as processed
                    self.deduplicator.mark_processed(data, source)

                except Exception as e:
                    logger.error(f"❌ Error processing {data_type} from {source}: {e}", exc_info=True)
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

            # Initialize HeartbeatLogger for live service monitoring
            self.heartbeat_logger = HeartbeatLogger(
                service_name="data-bridge",
                task_name="Message routing and deduplication",
                heartbeat_interval=30  # Log every 30 seconds
            )
            self.heartbeat_logger.start()

            logger.info("=" * 80)
            logger.info("✅ DATA BRIDGE STARTED - INTELLIGENT ROUTING")
            logger.info("📊 NATS: Real-time data path (PRIMARY)")
            logger.info("📊 Kafka: Backup + gap-filling (COMPLEMENTARY)")
            logger.info("🔍 Deduplication: ENABLED")
            logger.info("💾 Live Ticks (polygon_websocket) → TimescaleDB.market_ticks")
            logger.info("💾 Live Aggregates (live_aggregated) → ClickHouse.aggregates")
            logger.info("💾 Historical (polygon_historical) → ClickHouse.aggregates")
            logger.info("=" * 80)

            # Run Kafka poller and heartbeat reporter concurrently
            await asyncio.gather(
                self.kafka_subscriber.poll_messages(),
                self._heartbeat_reporter()
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
            logger.info(f"🔧 _save_tick called | symbol={data.get('pair', data.get('symbol'))}")

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

            logger.info(f"📦 TickData created: {tick_data.symbol} at {tick_data.timestamp}")

            # Save via Database Manager → TimescaleDB + DragonflyDB cache
            logger.info(f"💾 Calling db_router.save_tick()...")
            await self.db_router.save_tick(tick_data)
            logger.info(f"✅ db_router.save_tick() completed")

            self.ticks_saved += 1

            if self.ticks_saved % 100 == 0:
                logger.info(f"📊 Progress: Saved {self.ticks_saved} ticks to TimescaleDB")

        except Exception as e:
            logger.error(f"❌ Error in _save_tick: {e}", exc_info=True)
            logger.error(f"📋 Raw data: {data}")
            raise

    async def _save_candle(self, data: dict):
        """
        Save candle/aggregate data with intelligent routing

        Routing Logic:
        - Live data (source != 'historical') → TimescaleDB (via Database Manager)
        - Historical data (source == 'historical') → ClickHouse (direct write)

        This ensures:
        - Live 1s bars → TimescaleDB.market_candles (90 days retention)
        - Historical M5-W1 → ClickHouse.aggregates (10 years retention)
        """
        try:
            # Determine source
            source = data.get('_source', 'unknown')

            # Determine timeframe from subject/topic
            timeframe = data.get('timeframe', '1s')
            if not timeframe and '_subject' in data:
                # Extract from NATS subject: bars.EURUSD.1m → 1m
                parts = data['_subject'].split('.')
                if len(parts) >= 3:
                    timeframe = parts[2]

            # ROUTING DECISION based on source
            # ALL aggregates (live_aggregated + historical) → ClickHouse
            if source in ['historical', 'polygon_historical', 'live_aggregated']:
                # Aggregated data → ClickHouse (from Aggregator Service or Historical Downloader)
                await self._save_to_clickhouse(data, timeframe)
                self.candles_saved_clickhouse += 1

                if self.candles_saved_clickhouse % 100 == 0:
                    logger.debug(f"Saved {self.candles_saved_clickhouse} aggregates to ClickHouse (source: {source})")

            else:
                # Legacy: OLD flow if any live 1s bars still come through
                # This should NOT happen after disabling aggregate_client
                logger.warning(f"⚠️  Unexpected aggregate data with source '{source}' - should be tick data!")
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
                    source=source,
                    event_type=data.get('ev', 'ohlcv')
                )
                await self.db_router.save_candle(candle_data)
                self.candles_saved_timescale += 1

        except Exception as e:
            logger.error(f"Error saving candle: {e}")
            logger.debug(f"Candle data: {data}")
            raise

    async def _save_to_clickhouse(self, data: dict, timeframe: str):
        """
        Save historical data to ClickHouse

        Args:
            data: Historical aggregate data from Polygon
            timeframe: Timeframe (5m, 15m, 30m, 1h, 4h, 1d, 1w)
        """
        if not self.clickhouse_writer:
            logger.warning("⚠️  ClickHouse Writer not initialized, skipping historical data")
            return

        try:
            # Prepare data for ClickHouse
            aggregate_data = {
                'symbol': data.get('pair', data.get('symbol', '')),
                'timeframe': timeframe,
                'timestamp_ms': data.get('s', data.get('timestamp_ms', data.get('timestamp', 0))),
                'open': data.get('o', data.get('open', 0)),
                'high': data.get('h', data.get('high', 0)),
                'low': data.get('l', data.get('low', 0)),
                'close': data.get('c', data.get('close', 0)),
                'volume': data.get('v', data.get('volume', 0)),
                'vwap': data.get('vw', data.get('vwap', 0)),
                'range_pips': data.get('range_pips', 0),
                'body_pips': data.get('body_pips', 0),
                'start_time': data.get('start_time', ''),
                'end_time': data.get('end_time', ''),
                'source': data.get('source', 'polygon_historical'),
                'event_type': data.get('ev', data.get('event_type', 'ohlcv')),
                'indicators': data.get('indicators', {})  # Technical indicators (from Tick Aggregator)
            }

            # Add to ClickHouse batch buffer
            await self.clickhouse_writer.add_aggregate(aggregate_data)

        except Exception as e:
            logger.error(f"Error preparing data for ClickHouse: {e}")
            logger.debug(f"Data: {data}")
            raise

    async def _save_external_data(self, data: dict):
        """
        Save external data to ClickHouse

        External data types:
        - economic_calendar
        - fred_economic
        - crypto_sentiment
        - fear_greed_index
        - commodity_prices
        - market_sessions

        Args:
            data: External data message from NATS/Kafka
        """
        # EXPLICIT DEBUG: Entry point
        logger.info(f"🔍 _save_external_data CALLED | _source={data.get('_source')} | _external_type={data.get('_external_type', 'MISSING!')}")

        if not self.external_data_writer:
            logger.warning("⚠️  External Data Writer not initialized, skipping external data")
            return

        try:
            external_type = data.get('_external_type', 'unknown')
            logger.info(f"🔍 About to call write_external_data | type={external_type}")

            # Save to ClickHouse
            await self.external_data_writer.write_external_data(data)

            logger.info(f"🔍 write_external_data RETURNED | type={external_type}")

            self.external_data_saved += 1

            if self.external_data_saved % 10 == 0:
                logger.debug(f"Saved {self.external_data_saved} external data records (type: {external_type})")

        except Exception as e:
            logger.error(f"Error saving external data: {e}")
            logger.debug(f"External data: {data}")
            raise

    async def _heartbeat_reporter(self):
        """Lightweight heartbeat reporter using HeartbeatLogger"""
        while self.is_running:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds (logger decides when to log)

                # Collect stats
                nats_stats = self.nats_subscriber.get_stats() if self.nats_subscriber else {}
                kafka_stats = self.kafka_subscriber.get_stats() if self.kafka_subscriber else {}
                dedup_stats = self.deduplicator.get_stats() if self.deduplicator else {}
                clickhouse_stats = self.clickhouse_writer.get_stats() if self.clickhouse_writer else {}

                # Calculate total processed
                total_processed = (
                    self.ticks_saved +
                    self.candles_saved_timescale +
                    self.candles_saved_clickhouse +
                    self.external_data_saved
                )

                # Update heartbeat logger (will auto-log when interval reached)
                self.heartbeat_logger.update(
                    processed_count=0,  # Don't increment, just update metrics
                    additional_metrics={
                        'ticks': self.ticks_saved,
                        'ch_candles': self.candles_saved_clickhouse,
                        'external': self.external_data_saved,
                        'duplicates': dedup_stats.get('total_duplicates', 0),
                        'ch_buffer': clickhouse_stats.get('buffer_size', 0)
                    }
                )

                # Prepare metrics for Central Hub (sent every 30s with heartbeat log)
                if hasattr(self.config, 'central_hub') and self.config.central_hub:
                    metrics = {
                        'ticks_saved': self.ticks_saved,
                        'candles_saved_timescale': self.candles_saved_timescale,
                        'candles_saved_clickhouse': self.candles_saved_clickhouse,
                        'external_data_saved': self.external_data_saved,
                        'duplicates': dedup_stats.get('total_duplicates', 0),
                        'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds()
                    }

                    try:
                        await self.config.central_hub.send_heartbeat(metrics=metrics)
                    except Exception as hb_err:
                        logger.warning(f"⚠️  Failed to send heartbeat: {hb_err}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat reporter: {e}")

    async def stop(self):
        """Stop the Data Bridge"""
        logger.info("🛑 Stopping Data Bridge...")
        self.is_running = False

        # Stop subscribers
        if self.nats_subscriber:
            await self.nats_subscriber.close()

        if self.kafka_subscriber:
            await self.kafka_subscriber.close()

        # Flush and close ClickHouse writer
        if self.clickhouse_writer:
            await self.clickhouse_writer.close()

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
