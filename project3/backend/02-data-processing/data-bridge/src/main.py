#!/usr/bin/env python3
"""
Data Bridge - NATS Consumer with Database Manager Integration
Subscribes to NATS for market data and saves to databases
Hybrid Architecture Phase 1: NATS-only for market data
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
from nats_subscriber import NATSSubscriber
from clickhouse_writer import ClickHouseWriter
from external_data_writer import ExternalDataWriter
from retry_queue import RetryQueue

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

    Hybrid Architecture - Phase 1:
    1. Subscribe to NATS for market data (ticks + candles)
    2. Route to appropriate database via Database Manager
    3. No deduplication needed (single source: NATS only)

    Data Flow:
    NATS → Data Bridge → Database Manager → [TimescaleDB / ClickHouse]

    Result: Simple, fast, no duplicate overhead
    """

    def __init__(self):
        self.config = Config()

        # Database Manager (for Live data → TimescaleDB + DragonflyDB)
        self.db_router = None

        # PostgreSQL connection pool (for RetryQueue DLQ)
        self.pg_pool = None

        # Retry Queue (for failed ClickHouse writes)
        self.retry_queue = None

        # ClickHouse Writer (for Historical data → ClickHouse)
        self.clickhouse_writer = None

        # External Data Writer (for External data → ClickHouse)
        self.external_data_writer = None

        self.nats_subscriber = None

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
        logger.info("DATA BRIDGE - INTELLIGENT ROUTING + RETRY QUEUE")
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

            # Import retry utility
            sys.path.insert(0, '/app')
            from shared.utils.connection_retry import connect_with_retry

            # Initialize Database Manager with Central Hub configs (Live → TimescaleDB)
            logger.info("📦 Initializing Database Manager for Live data...")
            from components.data_manager.pools import get_pool_manager

            # Get database configs from Central Hub
            db_configs = self.config.database_configs

            # Initialize pool manager with Central Hub configs with retry
            pool_manager = await connect_with_retry(
                lambda: get_pool_manager(configs=db_configs),
                "Database Pool Manager",
                max_retries=10
            )

            # Initialize DataRouter (will use the pool manager we just created)
            self.db_router = DataRouter()
            await connect_with_retry(
                self.db_router.initialize,
                "DataRouter (Database Manager)",
                max_retries=10
            )
            logger.info("✅ Database Manager ready (TimescaleDB + DragonflyDB)")

            # Initialize PostgreSQL pool for RetryQueue DLQ (uses same PostgreSQL connection)
            logger.info("📦 Initializing PostgreSQL pool for Retry Queue DLQ...")
            import asyncpg
            postgres_config = db_configs.get('postgresql', {}).get('connection', {})
            if postgres_config:
                try:
                    async def create_pg_pool():
                        return await asyncpg.create_pool(
                            host=postgres_config.get('host', 'localhost'),
                            port=postgres_config.get('port', 5432),
                            database=postgres_config.get('database', 'suho_analytics'),
                            user=postgres_config.get('user', 'postgres'),
                            password=postgres_config.get('password', ''),
                            min_size=2,
                            max_size=5,
                            command_timeout=30
                        )

                    self.pg_pool = await connect_with_retry(
                        create_pg_pool,
                        "PostgreSQL Pool (DLQ)",
                        max_retries=10
                    )
                    logger.info("✅ PostgreSQL pool created for DLQ")

                    # Initialize RetryQueue
                    self.retry_queue = RetryQueue(
                        pg_pool=self.pg_pool,
                        max_queue_size=10000
                    )
                    await self.retry_queue.start()
                    logger.info("✅ Retry Queue initialized and started")
                except Exception as pg_error:
                    logger.warning(f"⚠️ Failed to initialize PostgreSQL pool for DLQ: {pg_error}")
                    logger.warning("⚠️ Retry Queue DISABLED - data loss possible on ClickHouse failures!")
            else:
                logger.warning("⚠️ PostgreSQL config not found - Retry Queue DISABLED")

            # Initialize ClickHouse Writer (Historical → ClickHouse) with RetryQueue
            logger.info("📦 Initializing ClickHouse Writer for Historical data...")
            clickhouse_config = self.config.database_configs.get('clickhouse')
            if clickhouse_config:
                self.clickhouse_writer = ClickHouseWriter(
                    config=clickhouse_config,
                    batch_size=1000,  # Larger batches for historical data
                    batch_timeout=10.0,  # 10 seconds
                    retry_queue=self.retry_queue  # Enable retry queue
                )
                await connect_with_retry(
                    self.clickhouse_writer.connect,
                    "ClickHouse Writer",
                    max_retries=10
                )
                logger.info("✅ ClickHouse Writer ready (with Retry Queue)")

                # Initialize External Data Writer (External → ClickHouse)
                logger.info("📦 Initializing External Data Writer...")
                self.external_data_writer = ExternalDataWriter(clickhouse_config)
                await connect_with_retry(
                    self.external_data_writer.connect,
                    "External Data Writer (ClickHouse)",
                    max_retries=10
                )
                logger.info("✅ External Data Writer ready")
            else:
                logger.warning("⚠️  ClickHouse config not found, historical/external data will not be saved")

            # Message handler (called by NATS subscriber)
            async def handle_message(data: dict, data_type: str):
                """
                Central message handler

                Args:
                    data: Message data
                    data_type: "tick" or "aggregate" or "external"
                """
                source = data.get('_source', 'nats')

                # Process message based on type
                try:
                    logger.debug(f"💾 Processing {data_type} from {source}...")

                    if data_type == 'tick':
                        # Tick data → TimescaleDB.market_ticks
                        await self._save_tick(data)
                        logger.debug(f"✅ Tick saved successfully")

                    elif data_type == 'aggregate':
                        # Aggregate data → ClickHouse.aggregates
                        await self._save_candle(data)
                        logger.debug(f"✅ Candle saved successfully")

                    elif data_type == 'external':
                        # External data → ClickHouse.external_* tables
                        await self._save_external_data(data)
                        logger.debug(f"✅ External data saved successfully")

                    else:
                        logger.warning(f"⚠️  Unknown data type: {data_type}")

                except Exception as e:
                    logger.error(f"❌ Error processing {data_type} from {source}: {e}", exc_info=True)
                    # Log error but don't crash (next message will be processed)

            # Initialize NATS subscriber (market data source)
            self.nats_subscriber = NATSSubscriber(
                config=self.config.nats_config,
                message_handler=handle_message
            )
            await connect_with_retry(
                self.nats_subscriber.connect,
                "NATS Subscriber",
                max_retries=10
            )
            await self.nats_subscriber.subscribe_all()

            self.is_running = True

            # Initialize HeartbeatLogger for live service monitoring
            self.heartbeat_logger = HeartbeatLogger(
                service_name="data-bridge",
                task_name="Message routing and deduplication",
                heartbeat_interval=30  # Log every 30 seconds
            )
            self.heartbeat_logger.start()

            logger.info("=" * 80)
            logger.info("✅ DATA BRIDGE STARTED - HYBRID PHASE 1 + RETRY QUEUE")
            logger.info("📊 NATS: Market data streaming (ONLY SOURCE)")
            logger.info("💾 Live Ticks → TimescaleDB.market_ticks")
            logger.info("💾 Aggregates → ClickHouse.aggregates")
            logger.info("💾 External Data → ClickHouse.external_*")
            logger.info(f"🔄 Retry Queue: {'ENABLED' if self.retry_queue else 'DISABLED'}")
            if self.retry_queue:
                logger.info("   └─ Max retries: 6 (1s → 2s → 4s → 8s → 16s → 32s)")
                logger.info("   └─ DLQ: PostgreSQL data_bridge_dlq table")
            logger.info("=" * 80)

            # Run heartbeat reporter
            await self._heartbeat_reporter()

        except Exception as e:
            logger.error(f"❌ Error starting Data Bridge: {e}", exc_info=True)
            await self.stop()

    async def _save_tick(self, data: dict):
        """
        Save tick data via Database Manager

        Maps Polygon data → TickData model
        """
        try:
            logger.debug(f"🔧 _save_tick called | symbol={data.get('pair', data.get('symbol'))}")

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

            logger.debug(f"📦 TickData created: {tick_data.symbol} at {tick_data.timestamp}")

            # Save via Database Manager → TimescaleDB + DragonflyDB cache
            logger.debug(f"💾 Calling db_router.save_tick()...")
            await self.db_router.save_tick(tick_data)
            logger.debug(f"✅ db_router.save_tick() completed")

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
            # ALL aggregates (live_aggregated + historical + kafka/nats transport) → ClickHouse
            if source in ['historical', 'polygon_historical', 'live_aggregated', 'kafka', 'nats']:
                # Aggregated data → ClickHouse (from Aggregator Service or Historical Downloader)
                await self._save_to_clickhouse(data, timeframe)
                self.candles_saved_clickhouse += 1

                if self.candles_saved_clickhouse % 100 == 0:
                    logger.debug(f"Saved {self.candles_saved_clickhouse} aggregates to ClickHouse (source: {source})")

            else:
                # Legacy: OLD flow if any live 1s bars still come through
                # This should NOT happen after disabling aggregate_client
                logger.debug(f"⚠️  Unexpected aggregate data with source '{source}' - should be tick data!")
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
        logger.debug(f"🔍 _save_external_data CALLED | _source={data.get('_source')} | _external_type={data.get('_external_type', 'MISSING!')}")

        if not self.external_data_writer:
            logger.warning("⚠️  External Data Writer not initialized, skipping external data")
            return

        try:
            external_type = data.get('_external_type', 'unknown')
            logger.debug(f"🔍 About to call write_external_data | type={external_type}")

            # Save to ClickHouse
            await self.external_data_writer.write_external_data(data)

            logger.debug(f"🔍 write_external_data RETURNED | type={external_type}")

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
                clickhouse_stats = self.clickhouse_writer.get_stats() if self.clickhouse_writer else {}
                retry_stats = self.retry_queue.get_stats() if self.retry_queue else {}

                # Calculate total processed
                total_processed = (
                    self.ticks_saved +
                    self.candles_saved_clickhouse +
                    self.external_data_saved
                )

                # Update heartbeat logger (will auto-log when interval reached)
                metrics = {
                    'ticks': self.ticks_saved,
                    'ch_candles': self.candles_saved_clickhouse,
                    'external': self.external_data_saved,
                    'nats_msgs': nats_stats.get('total_messages', 0),
                    'ch_buffer': clickhouse_stats.get('buffer_size', 0)
                }

                # Add retry queue metrics if available
                if retry_stats:
                    metrics['retry_queue_size'] = retry_stats.get('queue_size', 0)
                    metrics['retry_success_rate'] = round(retry_stats.get('success_rate', 0), 2)
                    metrics['total_dlq'] = retry_stats.get('total_failed_to_dlq', 0)

                self.heartbeat_logger.update(
                    processed_count=0,  # Don't increment, just update metrics
                    additional_metrics=metrics
                )

                # Prepare metrics for Central Hub (sent every 30s with heartbeat log)
                if hasattr(self.config, 'central_hub') and self.config.central_hub:
                    metrics = {
                        'ticks_saved': self.ticks_saved,
                        'candles_saved_clickhouse': self.candles_saved_clickhouse,
                        'external_data_saved': self.external_data_saved,
                        'nats_messages': nats_stats.get('total_messages', 0),
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
        """
        Stop the Data Bridge with proper shutdown sequence

        CRITICAL: Flush buffers BEFORE closing subscribers to prevent data loss
        """
        logger.info("🛑 Stopping Data Bridge...")
        self.is_running = False

        # Step 1: Stop heartbeat logger
        if self.heartbeat_logger:
            logger.info("📊 Stopping heartbeat logger...")
            self.heartbeat_logger.stop()

        # Step 1.5: Stop retry queue worker (will flush remaining to DLQ)
        if self.retry_queue:
            logger.info("🔄 Stopping Retry Queue...")
            await self.retry_queue.stop()
            logger.info("✅ Retry Queue stopped")

        # Step 2: FLUSH all buffered data BEFORE closing connections
        logger.info("💾 Flushing buffered data...")

        # Flush ClickHouse buffer with timeout protection
        if self.clickhouse_writer:
            try:
                # Wait max 30 seconds for flush to complete
                logger.info(f"💾 Flushing ClickHouse buffer ({len(self.clickhouse_writer.aggregate_buffer)} items)...")
                await asyncio.wait_for(
                    self.clickhouse_writer.flush_all(),
                    timeout=30.0
                )
                logger.info("✅ ClickHouse buffer flushed successfully")
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ ClickHouse flush timeout (30s exceeded), buffer size: {len(self.clickhouse_writer.aggregate_buffer)}")
                logger.warning("⚠️ Some data may be lost!")
            except Exception as e:
                logger.error(f"❌ Error flushing ClickHouse buffer: {e}", exc_info=True)

        # Flush external data writer buffer
        if self.external_data_writer:
            try:
                logger.info("💾 Flushing external data buffer...")
                await asyncio.wait_for(
                    self.external_data_writer.flush_all(),
                    timeout=30.0
                )
                logger.info("✅ External data buffer flushed successfully")
            except asyncio.TimeoutError:
                logger.warning("⚠️ External data flush timeout (30s exceeded)")
            except Exception as e:
                logger.error(f"❌ Error flushing external data buffer: {e}", exc_info=True)

        # Step 3: Wait 1 second for any pending async operations
        logger.info("⏳ Waiting for pending operations to complete...")
        await asyncio.sleep(1)

        # Step 4: Close Database Manager (flush TimescaleDB writes)
        if self.db_router and self.db_router.pool_manager:
            try:
                logger.info("💾 Closing Database Manager connection pools...")
                await self.db_router.pool_manager.close_all()
                logger.info("✅ Database Manager connection pools closed")
            except Exception as e:
                logger.error(f"❌ Error closing Database Manager: {e}", exc_info=True)

        # Step 5: NOW close NATS subscriber (no more incoming messages)
        if self.nats_subscriber:
            logger.info("📡 Closing NATS subscriber...")
            await self.nats_subscriber.close()
            logger.info("✅ NATS subscriber closed")

        # Step 6: Close ClickHouse writer connection
        if self.clickhouse_writer:
            logger.info("🔌 Closing ClickHouse connection...")
            if self.clickhouse_writer.client:
                self.clickhouse_writer.client.close()
            logger.info("✅ ClickHouse connection closed")

        # Step 7: Close external data writer connection
        if self.external_data_writer:
            logger.info("🔌 Closing external data writer connection...")
            if self.external_data_writer.client:
                self.external_data_writer.client.close()
            logger.info("✅ External data writer connection closed")

        # Step 8: Close PostgreSQL pool
        if self.pg_pool:
            logger.info("🔌 Closing PostgreSQL pool...")
            await self.pg_pool.close()
            logger.info("✅ PostgreSQL pool closed")

        # Final statistics
        logger.info("=" * 80)
        logger.info("📊 SHUTDOWN STATISTICS")
        logger.info(f"  Ticks saved: {self.ticks_saved}")
        logger.info(f"  ClickHouse candles: {self.candles_saved_clickhouse}")
        logger.info(f"  External data: {self.external_data_saved}")
        logger.info(f"  Total processed: {self.ticks_saved + self.candles_saved_clickhouse + self.external_data_saved}")
        if self.retry_queue:
            retry_stats = self.retry_queue.get_stats()
            logger.info(f"  Retry queue stats:")
            logger.info(f"    - Total retried: {retry_stats.get('total_retried', 0)}")
            logger.info(f"    - Success rate: {retry_stats.get('success_rate', 0):.1f}%")
            logger.info(f"    - Failed to DLQ: {retry_stats.get('total_failed_to_dlq', 0)}")
            logger.info(f"    - Dropped (overflow): {retry_stats.get('total_dropped', 0)}")
        logger.info("=" * 80)
        logger.info("✅ Data Bridge stopped gracefully")

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
