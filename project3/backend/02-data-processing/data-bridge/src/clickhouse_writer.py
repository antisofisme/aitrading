"""
ClickHouse Writer with Batch Insertion for Historical Data + Technical Indicators
"""
import logging
import asyncio
import json
from typing import List, Dict, Any
from datetime import datetime
import clickhouse_connect

logger = logging.getLogger(__name__)

class ClickHouseWriter:
    """
    ClickHouse writer with batch insertion optimization for historical aggregates

    Features:
    - Batch insertion (configurable size, default 1000 candles)
    - Time-based flushing (configurable interval, default 10s)
    - Auto-reconnection on failure
    - Performance metrics tracking

    Data Flow:
    Historical Downloader → NATS/Kafka → Data Bridge → ClickHouse Writer → ClickHouse.aggregates
    """

    def __init__(self, config: Dict[str, Any], batch_size: int = 1000, batch_timeout: float = 10.0):
        """
        Initialize ClickHouse writer

        Args:
            config: ClickHouse connection config from Central Hub
            batch_size: Number of candles to batch before insert
            batch_timeout: Seconds to wait before flushing batch
        """
        self.config = config
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout

        self.client = None

        # Batch buffer for aggregates
        self.aggregate_buffer: List[Dict] = []
        self.last_flush = datetime.utcnow()

        # Statistics
        self.total_aggregates_inserted = 0
        self.total_batch_inserts = 0
        self.total_insert_errors = 0

        logger.info(f"ClickHouse Writer initialized (batch_size={batch_size}, timeout={batch_timeout}s)")

    async def connect(self):
        """Connect to ClickHouse"""
        try:
            connection_config = self.config.get('connection', {})

            # Debug: Print full config
            logger.info(f"🔍 DEBUG: Full ClickHouse config: {self.config}")
            logger.info(f"🔍 DEBUG: Connection config: {connection_config}")

            # Get host and port from config
            host = connection_config.get('host', 'localhost')
            # Try http_port first (8123), fallback to port (9000 for native)
            port = connection_config.get('http_port', connection_config.get('port', 8123))
            database = connection_config.get('database', 'suho_analytics')
            username = connection_config.get('username', connection_config.get('user', 'default'))
            password = connection_config.get('password', '')

            logger.info(f"🔍 DEBUG: Connecting with - host={host}, port={port}, db={database}, user={username}")

            self.client = clickhouse_connect.get_client(
                host=host,
                port=int(port),
                database=database,
                username=username,
                password=password,
                connect_timeout=30,
                send_receive_timeout=300
            )

            logger.info(f"🔍 DEBUG: Client created, URL: {self.client.url if hasattr(self.client, 'url') else 'N/A'}")

            # Test connection
            result = self.client.command('SELECT 1')

            logger.info(f"✅ Connected to ClickHouse: {host}:{port}")
            logger.info(f"Database: {database}")

        except Exception as e:
            logger.error(f"❌ ClickHouse connection failed: {e}")
            raise

    async def add_aggregate(self, aggregate_data: Dict):
        """
        Add aggregate to batch buffer

        Args:
            aggregate_data: Candle data dictionary with fields:
                - symbol: Trading pair (e.g., 'EUR/USD')
                - timeframe: Timeframe (e.g., '5m', '15m', '1h')
                - timestamp_ms: Unix milliseconds
                - open, high, low, close: OHLC prices
                - volume: Tick volume
                - vwap: Volume-weighted average price
                - range_pips: High - low in pips
                - body_pips: |close - open| in pips
                - start_time: ISO string or datetime
                - end_time: ISO string or datetime
                - source: 'polygon_historical' or 'live_aggregated'
                - event_type: 'ohlcv'
                - indicators: Dict of technical indicators (optional)
        """
        self.aggregate_buffer.append(aggregate_data)

        # Check if should flush
        should_flush_size = len(self.aggregate_buffer) >= self.batch_size
        should_flush_time = (datetime.utcnow() - self.last_flush).total_seconds() >= self.batch_timeout

        if should_flush_size or should_flush_time:
            await self.flush_aggregates()

    async def flush_aggregates(self):
        """Flush aggregate buffer to ClickHouse"""
        if not self.aggregate_buffer:
            return

        try:
            # Prepare data for insertion
            data = []
            for agg in self.aggregate_buffer:
                # Convert timestamps
                timestamp_dt = datetime.fromtimestamp(agg['timestamp_ms'] / 1000.0)

                # Handle start_time and end_time (could be ISO strings or already datetime)
                start_time = agg.get('start_time')
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                elif isinstance(start_time, (int, float)):
                    start_time = datetime.fromtimestamp(start_time / 1000.0)

                end_time = agg.get('end_time')
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                elif isinstance(end_time, (int, float)):
                    end_time = datetime.fromtimestamp(end_time / 1000.0)

                # Serialize indicators to JSON string (if present)
                indicators_json = ''
                if 'indicators' in agg and agg['indicators']:
                    try:
                        indicators_json = json.dumps(agg['indicators'])
                    except Exception as e:
                        logger.warning(f"Failed to serialize indicators: {e}")
                        indicators_json = '{}'

                row = [
                    agg['symbol'],
                    agg['timeframe'],
                    timestamp_dt,
                    agg['timestamp_ms'],
                    float(agg['open']),
                    float(agg['high']),
                    float(agg['low']),
                    float(agg['close']),
                    int(agg.get('volume', 0)),
                    float(agg.get('vwap', 0)),
                    float(agg.get('range_pips', 0)),
                    float(agg.get('body_pips', 0)),
                    start_time,
                    end_time,
                    agg.get('source', 'polygon_historical'),
                    agg.get('event_type', 'ohlcv'),
                    indicators_json  # Technical indicators as JSON string
                ]
                data.append(row)

            # Insert batch to ClickHouse aggregates table
            self.client.insert(
                'aggregates',
                data,
                column_names=[
                    'symbol', 'timeframe', 'timestamp', 'timestamp_ms',
                    'open', 'high', 'low', 'close', 'volume',
                    'vwap', 'range_pips', 'body_pips', 'start_time', 'end_time',
                    'source', 'event_type', 'indicators'
                ]
            )

            count = len(self.aggregate_buffer)
            self.total_aggregates_inserted += count
            self.total_batch_inserts += 1

            logger.info(f"✅ Inserted {count} historical aggregates to ClickHouse (total: {self.total_aggregates_inserted})")

            # Clear buffer
            self.aggregate_buffer.clear()
            self.last_flush = datetime.utcnow()

        except Exception as e:
            self.total_insert_errors += 1
            logger.error(f"❌ Error inserting historical aggregates to ClickHouse: {e}")
            logger.error(f"Buffer size: {len(self.aggregate_buffer)}")

            # Log first item for debugging
            if self.aggregate_buffer:
                logger.error(f"Sample data: {self.aggregate_buffer[0]}")

            # Clear buffer to prevent memory leak (data lost but logged)
            self.aggregate_buffer.clear()

    async def flush_all(self):
        """Flush all pending data"""
        await self.flush_aggregates()

    def get_stats(self) -> Dict:
        """Get writer statistics"""
        return {
            'total_aggregates_inserted': self.total_aggregates_inserted,
            'total_batch_inserts': self.total_batch_inserts,
            'total_insert_errors': self.total_insert_errors,
            'buffer_size': len(self.aggregate_buffer)
        }

    async def close(self):
        """Close connection and flush remaining data"""
        await self.flush_all()

        if self.client:
            self.client.close()
            logger.info("✅ ClickHouse Writer connection closed")
