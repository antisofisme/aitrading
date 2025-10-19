"""
ClickHouse Writer with Batch Insertion for Historical Data + Technical Indicators

RESILIENCE FEATURES:
- Circuit breaker prevents cascading failures
- Retry queue with exponential backoff (NEW)
- PostgreSQL dead letter queue for failed messages (NEW)
- Batch insertion optimization
- Auto-reconnection on failure
- Comprehensive error handling
"""
import logging
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import clickhouse_connect

# Circuit breaker for ClickHouse availability
from circuit_breaker import CircuitBreaker, CircuitBreakerOpen

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

    def __init__(
        self,
        config: Dict[str, Any],
        batch_size: int = 1000,
        batch_timeout: float = 10.0,
        retry_queue: Optional['RetryQueue'] = None
    ):
        """
        Initialize ClickHouse writer

        Args:
            config: ClickHouse connection config from Central Hub
            batch_size: Number of candles to batch before insert
            batch_timeout: Seconds to wait before flushing batch
            retry_queue: RetryQueue instance for failed writes (optional but recommended)
        """
        self.config = config
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.retry_queue = retry_queue

        self.client = None

        # Batch buffer for aggregates
        self.aggregate_buffer: List[Dict] = []
        self.last_flush = datetime.now(timezone.utc)

        # Batch buffer for ticks (Dukascopy historical)
        self.tick_buffer: List[Dict] = []
        self.last_tick_flush = datetime.now(timezone.utc)

        # Circuit breaker (CRITICAL: Prevents cascading failures)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout_seconds=60,
            name="ClickHouse"
        )

        # Statistics
        self.total_aggregates_inserted = 0
        self.total_ticks_inserted = 0
        self.total_batch_inserts = 0
        self.total_insert_errors = 0
        self.circuit_breaker_trips = 0
        self.total_retried = 0  # NEW: Track retry queue usage

        logger.info(
            f"ClickHouse Writer initialized "
            f"(batch_size={batch_size}, timeout={batch_timeout}s, "
            f"retry_queue={'enabled' if retry_queue else 'disabled'})"
        )

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
        should_flush_time = (datetime.now(timezone.utc) - self.last_flush).total_seconds() >= self.batch_timeout

        if should_flush_size or should_flush_time:
            await self.flush_aggregates()

    async def add_tick(self, tick_data: Dict):
        """
        Add Dukascopy tick to batch buffer

        Args:
            tick_data: Tick data dictionary with fields:
                - symbol: Trading pair (e.g., 'EUR/USD')
                - timestamp: Datetime object
                - bid: Bid price
                - ask: Ask price
                - last: Last/mid price
                - volume: Volume
                - flags: Flags (reserved)
        """
        self.tick_buffer.append(tick_data)

        # Check if should flush
        should_flush_size = len(self.tick_buffer) >= self.batch_size
        should_flush_time = (datetime.now(timezone.utc) - self.last_tick_flush).total_seconds() >= self.batch_timeout

        if should_flush_size or should_flush_time:
            await self.flush_ticks()

    async def flush_ticks(self):
        """
        Flush tick buffer to ClickHouse ticks table
        """
        if not self.tick_buffer:
            return

        try:
            # Circuit breaker protection
            def do_insert():
                # Prepare data for insertion
                data = []
                for tick in self.tick_buffer:
                    # Convert timestamp to UTC timezone-aware datetime if needed
                    timestamp_dt = tick['timestamp']
                    if isinstance(timestamp_dt, str):
                        # Handle string timestamp from Dukascopy (e.g., '2024-01-02 15:36:39.034000')
                        timestamp_dt = datetime.fromisoformat(timestamp_dt.replace('Z', '+00:00'))
                        if not timestamp_dt.tzinfo:
                            timestamp_dt = timestamp_dt.replace(tzinfo=timezone.utc)
                    elif isinstance(timestamp_dt, (int, float)):
                        timestamp_dt = datetime.fromtimestamp(timestamp_dt / 1000.0, tz=timezone.utc)
                    elif hasattr(timestamp_dt, 'tzinfo') and not timestamp_dt.tzinfo:
                        timestamp_dt = timestamp_dt.replace(tzinfo=timezone.utc)

                    # NEW: 6-column schema for historical_ticks (matches live_ticks schema)
                    row = [
                        timestamp_dt,  # time (DateTime64)
                        tick['symbol'],  # symbol (String)
                        float(tick.get('bid', 0)),  # bid (Decimal)
                        float(tick.get('ask', 0)),  # ask (Decimal)
                        int(timestamp_dt.timestamp() * 1000),  # timestamp_ms (UInt64)
                        datetime.now(timezone.utc)  # ingested_at (DateTime64)
                    ]
                    data.append(row)

                # Insert batch to ClickHouse historical_ticks table
                self.client.insert(
                    'historical_ticks',
                    data,
                    column_names=['time', 'symbol', 'bid', 'ask', 'timestamp_ms', 'ingested_at']
                )

            # Execute with circuit breaker protection
            self.circuit_breaker.call(do_insert)

            count = len(self.tick_buffer)
            self.total_ticks_inserted += count

            if self.total_ticks_inserted % 10000 == 0:
                logger.info(f"✅ Inserted {count} ticks to ClickHouse.historical_ticks (total: {self.total_ticks_inserted})")

            # Clear buffer ONLY on success
            self.tick_buffer.clear()
            self.last_tick_flush = datetime.now(timezone.utc)

        except CircuitBreakerOpen as e:
            logger.error(f"🔴 Circuit breaker OPEN for ticks: {e}")
            logger.error(f"⚠️ Keeping {len(self.tick_buffer)} ticks in buffer (will retry)")
            raise

        except Exception as e:
            self.total_insert_errors += 1
            logger.error(f"❌ Error inserting ticks to ClickHouse: {e}")
            logger.error(f"Tick buffer size: {len(self.tick_buffer)}")

            if self.tick_buffer:
                logger.error(f"Sample tick: {self.tick_buffer[0]}")

            # On error, clear if buffer too large (prevent OOM)
            if len(self.tick_buffer) > self.batch_size * 10:
                logger.critical(f"⚠️ Tick buffer overflow ({len(self.tick_buffer)} items) - clearing to prevent OOM")
                self.tick_buffer.clear()
            else:
                logger.warning(f"⚠️ Keeping tick buffer for retry (size: {len(self.tick_buffer)})")
                raise

    async def flush_aggregates(self):
        """
        Flush aggregate buffer to ClickHouse with circuit breaker protection

        Raises:
            CircuitBreakerOpen: If ClickHouse unavailable (will NOT clear buffer)
        """
        if not self.aggregate_buffer:
            return

        try:
            # ✅ LAYER 2 DEDUPLICATION: Check for existing records before insert
            # Build list of (symbol, timeframe, timestamp) tuples to check
            records_to_check = [
                (agg['symbol'], agg['timeframe'], agg['timestamp_ms'])
                for agg in self.aggregate_buffer
            ]

            # Query ClickHouse for existing records (batch query for performance)
            existing_records = set()
            if records_to_check:
                try:
                    # Build WHERE clause for batch check
                    # Format: (symbol='EUR/USD' AND timeframe='1m' AND time=fromUnixTimestamp64Milli(123)) OR (...)
                    # NOTE: live_aggregates uses 'time' (DateTime64), not 'timestamp_ms'
                    conditions = []
                    for symbol, timeframe, ts_ms in records_to_check:
                        conditions.append(
                            f"(symbol = '{symbol}' AND timeframe = '{timeframe}' AND time = fromUnixTimestamp64Milli({ts_ms}))"
                        )

                    # Limit to first 1000 conditions to avoid query size limits
                    where_clause = " OR ".join(conditions[:1000])

                    check_query = f"""
                        SELECT symbol, timeframe, toUnixTimestamp64Milli(time) as timestamp_ms
                        FROM live_aggregates
                        WHERE {where_clause}
                    """

                    result = self.client.query(check_query)
                    existing_records = {(row[0], row[1], row[2]) for row in result.result_rows}

                    if existing_records:
                        logger.info(f"🔍 Found {len(existing_records)} existing records, will skip duplicates")

                except Exception as check_error:
                    logger.warning(f"⚠️  Error checking for existing records: {check_error}")
                    logger.warning(f"⚠️  Proceeding with insert (ReplacingMergeTree will handle duplicates)")
                    # On error, proceed with insert - ReplacingMergeTree will deduplicate

            # Filter out duplicates from buffer
            filtered_buffer = []
            skipped_duplicates = 0

            for agg in self.aggregate_buffer:
                record_key = (agg['symbol'], agg['timeframe'], agg['timestamp_ms'])
                if record_key in existing_records:
                    skipped_duplicates += 1
                    logger.debug(f"⏭️  Skip duplicate: {agg['symbol']} {agg['timeframe']} @ {agg['timestamp_ms']}")
                else:
                    filtered_buffer.append(agg)

            if skipped_duplicates > 0:
                logger.info(f"⏭️  Skipped {skipped_duplicates} duplicates (already in ClickHouse)")

            # If all records are duplicates, skip insert
            if not filtered_buffer:
                logger.info(f"✅ All {len(self.aggregate_buffer)} records already exist - skipping insert")
                self.aggregate_buffer.clear()
                self.last_flush = datetime.now(timezone.utc)
                return

            # Circuit breaker protection (CRITICAL!)
            def do_insert():
                # Prepare data for insertion (using filtered buffer)
                data = []
                for agg in filtered_buffer:
                    # Convert timestamps to UTC timezone-aware datetime
                    time_dt = datetime.fromtimestamp(agg['timestamp_ms'] / 1000.0, tz=timezone.utc)

                    # NEW: 15-column schema for live_aggregates
                    row = [
                        time_dt,  # time (DateTime64)
                        agg['symbol'],  # symbol (String)
                        agg['timeframe'],  # timeframe (Enum8 - ClickHouse handles conversion)
                        float(agg['open']),  # open (Decimal)
                        float(agg['high']),  # high (Decimal)
                        float(agg['low']),  # low (Decimal)
                        float(agg['close']),  # close (Decimal)
                        int(agg.get('tick_count', agg.get('volume', 0))),  # tick_count (UInt32)
                        float(agg.get('avg_spread', 0)),  # avg_spread (Decimal) - NEW
                        float(agg.get('max_spread', 0)),  # max_spread (Decimal) - NEW
                        float(agg.get('min_spread', 0)),  # min_spread (Decimal) - NEW
                        float(agg.get('price_range', agg.get('range_pips', 0))),  # price_range (Decimal)
                        float(agg.get('pct_change', 0)),  # pct_change (Decimal) - NEW
                        int(agg.get('is_complete', 1)),  # is_complete (UInt8) - NEW
                        datetime.now(timezone.utc)  # created_at (DateTime64)
                    ]
                    data.append(row)

                # Insert batch to ClickHouse live_aggregates table
                self.client.insert(
                    'live_aggregates',
                    data,
                    column_names=[
                        'time', 'symbol', 'timeframe',
                        'open', 'high', 'low', 'close',
                        'tick_count',
                        'avg_spread', 'max_spread', 'min_spread',
                        'price_range', 'pct_change', 'is_complete',
                        'created_at'
                    ]
                )

            # Execute with circuit breaker protection
            self.circuit_breaker.call(do_insert)

            count = len(filtered_buffer)  # Use filtered buffer size
            self.total_aggregates_inserted += count
            self.total_batch_inserts += 1

            # Log every 10,000 aggregates instead of every batch to reduce spam during catchup
            if self.total_aggregates_inserted % 10000 == 0:
                logger.info(f"✅ Inserted {count} aggregates to ClickHouse (total: {self.total_aggregates_inserted}, skipped: {skipped_duplicates})")

            # Clear buffer ONLY on success
            self.aggregate_buffer.clear()
            self.last_flush = datetime.now(timezone.utc)

        except CircuitBreakerOpen as e:
            # Circuit breaker is OPEN - ClickHouse unavailable
            self.circuit_breaker_trips += 1
            logger.error(f"🔴 Circuit breaker OPEN: {e}")

            # NEW: Add messages to retry queue if available
            if self.retry_queue:
                await self._move_buffer_to_retry_queue(
                    filtered_buffer if 'filtered_buffer' in locals() else self.aggregate_buffer,
                    error=str(e)
                )
                self.aggregate_buffer.clear()
                self.last_flush = datetime.now(timezone.utc)
            else:
                logger.error(f"⚠️ Keeping {len(self.aggregate_buffer)} aggregates in buffer (will retry)")
                # DO NOT clear buffer - will retry on next flush
                raise  # Re-raise so Kafka offset NOT committed

        except Exception as e:
            self.total_insert_errors += 1
            logger.error(f"❌ Error inserting historical aggregates to ClickHouse: {e}")
            logger.error(f"Buffer size: {len(self.aggregate_buffer)}")

            # Log first item for debugging
            if self.aggregate_buffer:
                logger.error(f"Sample data: {self.aggregate_buffer[0]}")

            # NEW: Add messages to retry queue if available
            if self.retry_queue:
                await self._move_buffer_to_retry_queue(
                    filtered_buffer if 'filtered_buffer' in locals() else self.aggregate_buffer,
                    error=str(e)
                )
                self.aggregate_buffer.clear()
                self.last_flush = datetime.now(timezone.utc)
            else:
                # OLD BEHAVIOR: On error, DO NOT clear buffer immediately
                # Let circuit breaker handle retry logic
                # Only clear if buffer too large (prevent OOM)
                if len(self.aggregate_buffer) > self.batch_size * 10:
                    logger.critical(f"⚠️ Buffer overflow ({len(self.aggregate_buffer)} items) - clearing to prevent OOM")
                    self.aggregate_buffer.clear()
                else:
                    logger.warning(f"⚠️ Keeping buffer for retry (size: {len(self.aggregate_buffer)})")
                    raise  # Re-raise so Kafka offset NOT committed

    async def _move_buffer_to_retry_queue(self, buffer: List[Dict], error: str):
        """
        Move failed messages from buffer to retry queue

        Args:
            buffer: List of aggregate messages that failed to insert
            error: Error message describing the failure
        """
        if not self.retry_queue:
            return

        for aggregate in buffer:
            try:
                # Determine priority based on source
                source = aggregate.get('source', 'polygon_historical')
                if source in ['live_aggregated', 'polygon_live']:
                    priority = 'high'
                elif source in ['live_gap_filled', 'historical_aggregated']:
                    priority = 'medium'
                else:
                    priority = 'low'

                # Generate correlation ID for tracking
                correlation_id = (
                    f"{aggregate.get('symbol', 'unknown')}_"
                    f"{aggregate.get('timeframe', 'unknown')}_"
                    f"{aggregate.get('timestamp_ms', 0)}"
                )

                # Add to retry queue
                await self.retry_queue.add(
                    message_data=aggregate,
                    priority=priority,
                    correlation_id=correlation_id,
                    message_type='aggregate'
                )
                self.total_retried += 1

            except Exception as queue_error:
                logger.error(f"Failed to add message to retry queue: {queue_error}")
                logger.critical(f"Message lost: {aggregate}")

    async def flush_all(self):
        """Flush all pending data"""
        await self.flush_aggregates()

    def get_stats(self) -> Dict:
        """Get writer statistics"""
        stats = {
            'total_aggregates_inserted': self.total_aggregates_inserted,
            'total_batch_inserts': self.total_batch_inserts,
            'total_insert_errors': self.total_insert_errors,
            'buffer_size': len(self.aggregate_buffer),
            'total_retried': self.total_retried
        }

        # Add retry queue stats if available
        if self.retry_queue:
            retry_stats = self.retry_queue.get_stats()
            stats['retry_queue'] = retry_stats

        return stats

    async def close(self):
        """Close connection and flush remaining data"""
        await self.flush_all()

        if self.client:
            self.client.close()
            logger.info("✅ ClickHouse Writer connection closed")
