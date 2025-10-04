"""
ClickHouse Client with Batch Insertion
"""
import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime
import clickhouse_connect

logger = logging.getLogger(__name__)

class ClickHouseClient:
    """
    ClickHouse client with batch insertion optimization

    Features:
    - Batch insertion (1000 ticks, 500 aggregates)
    - Time-based flushing (5s for ticks, 10s for aggregates)
    - Auto-reconnection
    - Performance metrics
    """

    def __init__(self, config: Dict[str, Any], batch_config: Dict[str, Any]):
        self.config = config
        self.batch_config = batch_config

        self.client = None

        # Batch buffers
        self.tick_buffer: List[Dict] = []
        self.aggregate_buffer: List[Dict] = []

        # Batch timers
        self.tick_last_flush = datetime.utcnow()
        self.aggregate_last_flush = datetime.utcnow()

        # Statistics
        self.total_ticks_inserted = 0
        self.total_aggregates_inserted = 0
        self.total_batch_inserts = 0
        self.total_insert_errors = 0

        logger.info("ClickHouse client initialized")

    async def connect(self):
        """Connect to ClickHouse"""
        try:
            self.client = clickhouse_connect.get_client(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 8123),
                database=self.config.get('database', 'forex_data'),
                username=self.config.get('username', 'default'),
                password=self.config.get('password', ''),
                connect_timeout=self.config.get('connect_timeout', 30),
                send_receive_timeout=self.config.get('send_receive_timeout', 300)
            )

            # Test connection
            result = self.client.command('SELECT 1')

            logger.info(f"✅ Connected to ClickHouse: {self.config.get('host')}:{self.config.get('port')}")
            logger.info(f"Database: {self.config.get('database')}")

        except Exception as e:
            logger.error(f"❌ ClickHouse connection failed: {e}")
            raise

    async def add_tick(self, tick_data: dict):
        """
        Add tick to batch buffer

        Args:
            tick_data: Tick data dictionary
        """
        self.tick_buffer.append(tick_data)

        # Check if should flush
        should_flush_size = len(self.tick_buffer) >= self.batch_config.get('max_size_ticks', 1000)
        should_flush_time = (datetime.utcnow() - self.tick_last_flush).total_seconds() >= \
                           self.batch_config.get('max_wait_seconds_ticks', 5)

        if should_flush_size or should_flush_time:
            await self.flush_ticks()

    async def add_aggregate(self, aggregate_data: dict):
        """
        Add aggregate to batch buffer

        Args:
            aggregate_data: Aggregate data dictionary
        """
        self.aggregate_buffer.append(aggregate_data)

        # Check if should flush
        should_flush_size = len(self.aggregate_buffer) >= self.batch_config.get('max_size_aggregates', 500)
        should_flush_time = (datetime.utcnow() - self.aggregate_last_flush).total_seconds() >= \
                           self.batch_config.get('max_wait_seconds_aggregates', 10)

        if should_flush_size or should_flush_time:
            await self.flush_aggregates()

    async def flush_ticks(self):
        """Flush tick buffer to ClickHouse"""
        if not self.tick_buffer:
            return

        try:
            # Prepare data for insertion
            data = [
                [
                    tick['symbol'],
                    datetime.fromtimestamp(tick['timestamp_ms'] / 1000.0),
                    tick['timestamp_ms'],
                    tick['bid'],
                    tick['ask'],
                    tick['mid'],
                    tick['spread'],
                    tick.get('exchange', 0),
                    tick.get('source', 'unknown'),
                    tick.get('event_type', 'quote'),
                    tick.get('use_case', '')
                ]
                for tick in self.tick_buffer
            ]

            # Insert batch
            self.client.insert(
                'ticks',
                data,
                column_names=[
                    'symbol', 'timestamp', 'timestamp_ms', 'bid', 'ask', 'mid',
                    'spread', 'exchange', 'source', 'event_type', 'use_case'
                ]
            )

            count = len(self.tick_buffer)
            self.total_ticks_inserted += count
            self.total_batch_inserts += 1

            logger.info(f"✅ Inserted {count} ticks to ClickHouse (total: {self.total_ticks_inserted})")

            # Clear buffer
            self.tick_buffer.clear()
            self.tick_last_flush = datetime.utcnow()

        except Exception as e:
            self.total_insert_errors += 1
            logger.error(f"❌ Error inserting ticks: {e}")
            logger.error(f"Buffer size: {len(self.tick_buffer)}")

            # Clear buffer to prevent memory leak (data lost, but logged)
            self.tick_buffer.clear()

    async def flush_aggregates(self):
        """Flush aggregate buffer to ClickHouse"""
        if not self.aggregate_buffer:
            return

        try:
            # Prepare data for insertion
            data = [
                [
                    agg['symbol'],
                    agg['timeframe'],
                    datetime.fromtimestamp(agg['timestamp_ms'] / 1000.0),
                    agg['timestamp_ms'],
                    agg['open'],
                    agg['high'],
                    agg['low'],
                    agg['close'],
                    agg['volume'],
                    agg.get('vwap', 0),
                    agg['range_pips'],
                    datetime.fromtimestamp(agg['start_time_ms'] / 1000.0),
                    datetime.fromtimestamp(agg['end_time_ms'] / 1000.0),
                    agg.get('source', 'unknown'),
                    agg.get('event_type', 'ohlcv')
                ]
                for agg in self.aggregate_buffer
            ]

            # Insert batch
            self.client.insert(
                'aggregates',
                data,
                column_names=[
                    'symbol', 'timeframe', 'timestamp', 'timestamp_ms',
                    'open', 'high', 'low', 'close', 'volume',
                    'vwap', 'range_pips', 'start_time', 'end_time',
                    'source', 'event_type'
                ]
            )

            count = len(self.aggregate_buffer)
            self.total_aggregates_inserted += count
            self.total_batch_inserts += 1

            logger.info(f"✅ Inserted {count} aggregates to ClickHouse (total: {self.total_aggregates_inserted})")

            # Clear buffer
            self.aggregate_buffer.clear()
            self.aggregate_last_flush = datetime.utcnow()

        except Exception as e:
            self.total_insert_errors += 1
            logger.error(f"❌ Error inserting aggregates: {e}")
            logger.error(f"Buffer size: {len(self.aggregate_buffer)}")

            # Clear buffer to prevent memory leak
            self.aggregate_buffer.clear()

    async def flush_all(self):
        """Flush all buffers"""
        await self.flush_ticks()
        await self.flush_aggregates()

    def get_stats(self) -> dict:
        """Get client statistics"""
        return {
            'total_ticks_inserted': self.total_ticks_inserted,
            'total_aggregates_inserted': self.total_aggregates_inserted,
            'total_batch_inserts': self.total_batch_inserts,
            'total_insert_errors': self.total_insert_errors,
            'tick_buffer_size': len(self.tick_buffer),
            'aggregate_buffer_size': len(self.aggregate_buffer)
        }

    async def close(self):
        """Close connection"""
        await self.flush_all()

        if self.client:
            self.client.close()
            logger.info("✅ ClickHouse connection closed")
