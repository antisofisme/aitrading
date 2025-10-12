"""
NATS Publisher for Aggregated Data
Publishes OHLCV candles to NATS (Hybrid Architecture: NATS for market data)

RESILIENCE FEATURES:
- Circuit breaker pattern (5 failures → OPEN for 30s)
- PostgreSQL fallback queue when NATS unavailable
- Automatic retry with exponential backoff
- State transition monitoring and logging
"""
import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from nats.aio.client import Client as NATS
import asyncpg

from circuit_breaker import CircuitBreaker, CircuitState

logger = logging.getLogger(__name__)

class AggregatePublisher:
    """
    Publishes aggregated OHLCV data to NATS with circuit breaker

    Hybrid Architecture:
    - NATS: Market data (ticks, aggregates) ← THIS SERVICE
    - Kafka: User events only

    Flow:
    Aggregator → NATS → Data Bridge → ClickHouse
                  ↓ (if circuit OPEN)
            PostgreSQL Queue → Retry Worker → NATS

    Resilience:
    - Circuit breaker prevents cascading failures
    - PostgreSQL queue stores messages when NATS down
    - Automatic retry with exponential backoff
    """

    # Query timeout settings
    QUERY_TIMEOUT_SHORT = 10.0  # 10 seconds for simple queries
    QUERY_TIMEOUT_MEDIUM = 30.0  # 30 seconds for aggregations
    QUERY_TIMEOUT_LONG = 60.0  # 60 seconds for complex queries

    # Slow query threshold for logging
    SLOW_QUERY_THRESHOLD = 5.0  # Log queries > 5 seconds

    def __init__(
        self,
        nats_config: Dict[str, Any],
        kafka_config: Dict[str, Any] = None,
        db_config: Dict[str, Any] = None
    ):
        self.nats_config = nats_config
        self.db_config = db_config
        self.nats: NATS = None
        self.db_pool: Optional[asyncpg.Pool] = None

        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30,
            monitoring_window=60,
            on_state_change=self._on_circuit_state_change
        )

        # Statistics
        self.nats_publish_count = 0
        self.fallback_queue_count = 0
        self.retry_success_count = 0

        # Query performance statistics
        self.query_stats = {
            'total_queries': 0,
            'slow_queries': 0,
            'timeout_errors': 0,
            'total_duration': 0.0
        }

        logger.info("Aggregate Publisher initialized (NATS-only with Circuit Breaker)")
        logger.info(f"Circuit Breaker: threshold=5, timeout=30s")

    async def _execute_query_with_timeout(
        self,
        conn,
        query: str,
        *args,
        timeout: float = 30.0,
        query_name: str = "unknown",
        fetch: bool = True
    ):
        """
        Execute query with timeout and performance logging

        Args:
            conn: AsyncPG connection
            query: SQL query string
            args: Query parameters
            timeout: Timeout in seconds
            query_name: Name for logging
            fetch: If True, use conn.fetch(), otherwise use conn.execute()

        Returns:
            Query results (if fetch=True) or None (if fetch=False)

        Raises:
            asyncio.TimeoutError: If query exceeds timeout
        """
        start_time = time.time()

        try:
            # Execute with timeout
            if fetch:
                result = await asyncio.wait_for(
                    conn.fetch(query, *args),
                    timeout=timeout
                )
            else:
                result = await asyncio.wait_for(
                    conn.execute(query, *args),
                    timeout=timeout
                )

            # Log slow queries
            duration = time.time() - start_time
            if duration > self.SLOW_QUERY_THRESHOLD:
                logger.warning(
                    f"🐌 Slow query '{query_name}': {duration:.2f}s "
                    f"(threshold: {self.SLOW_QUERY_THRESHOLD}s)"
                )
            else:
                logger.debug(f"✅ Query '{query_name}': {duration:.2f}s")

            # Update statistics
            self._update_query_stats(duration, timed_out=False)

            return result

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            logger.error(
                f"❌ Query timeout '{query_name}' after {duration:.2f}s "
                f"(limit: {timeout}s)\nQuery: {query[:200]}..."
            )
            self._update_query_stats(duration, timed_out=True)
            raise
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"❌ Query error '{query_name}' after {duration:.2f}s: {e}"
            )
            raise

    def _update_query_stats(self, duration: float, timed_out: bool = False):
        """Update query performance statistics"""
        self.query_stats['total_queries'] += 1
        self.query_stats['total_duration'] += duration

        if duration > self.SLOW_QUERY_THRESHOLD:
            self.query_stats['slow_queries'] += 1

        if timed_out:
            self.query_stats['timeout_errors'] += 1

    def get_query_stats(self):
        """Get query performance statistics"""
        total = self.query_stats['total_queries']
        if total == 0:
            return self.query_stats

        avg_duration = self.query_stats['total_duration'] / total
        slow_pct = (self.query_stats['slow_queries'] / total) * 100

        return {
            **self.query_stats,
            'avg_duration_seconds': round(avg_duration, 2),
            'slow_query_percentage': round(slow_pct, 1)
        }

    def _on_circuit_state_change(self, old_state: CircuitState, new_state: CircuitState):
        """
        Callback for circuit breaker state changes

        Args:
            old_state: Previous circuit state
            new_state: New circuit state
        """
        logger.info(f"🔄 Circuit Breaker State: {old_state.value} → {new_state.value}")

        if new_state == CircuitState.OPEN:
            logger.warning("⚠️ NATS circuit OPEN - Messages will be queued to PostgreSQL")
        elif new_state == CircuitState.CLOSED:
            logger.info("✅ NATS circuit CLOSED - Normal publishing resumed")
            # Trigger retry of queued messages
            asyncio.create_task(self._retry_queued_messages())

    async def connect(self):
        """Connect to NATS cluster and PostgreSQL"""
        try:
            # Connect to NATS cluster
            self.nats = NATS()

            # Parse cluster URLs from config (supports both formats)
            # Format 1: cluster_urls array (preferred)
            # Format 2: comma-separated url string (legacy)
            cluster_urls = self.nats_config.get('cluster_urls')
            if cluster_urls:
                servers = cluster_urls
            else:
                url_config = self.nats_config.get('url', 'nats://localhost:4222')
                servers = url_config.split(',') if ',' in url_config else [url_config]

            await self.nats.connect(
                servers=servers,
                max_reconnect_attempts=self.nats_config.get('max_reconnect_attempts', -1),
                reconnect_time_wait=self.nats_config.get('reconnect_time_wait', 2),
                ping_interval=self.nats_config.get('ping_interval', 120),
                # Cluster event callbacks
                reconnected_cb=self._on_reconnect,
                disconnected_cb=self._on_disconnect,
                error_cb=self._on_error,
            )

            logger.info(f"✅ Connected to NATS cluster: {servers}")
            logger.info(f"📡 Active server: {self.nats.connected_url}")

            # Connect to PostgreSQL for fallback queue
            if self.db_config:
                self.db_pool = await asyncpg.create_pool(
                    host=self.db_config['host'],
                    port=self.db_config['port'],
                    database=self.db_config['database'],
                    user=self.db_config['user'],
                    password=self.db_config['password'],
                    min_size=2,
                    max_size=5
                )
                logger.info(f"✅ Connected to PostgreSQL: {self.db_config['host']}")
            else:
                logger.warning("⚠️ No database config - fallback queue disabled")

        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            raise

    async def _on_reconnect(self):
        """Called when reconnected to another NATS node"""
        logger.info(f"🔄 NATS reconnected to: {self.nats.connected_url}")

    async def _on_disconnect(self):
        """Called when disconnected from NATS node"""
        logger.warning(f"⚠️ NATS disconnected")

    async def _on_error(self, error):
        """Called on NATS connection error"""
        logger.error(f"❌ NATS error: {error}")

    async def publish_aggregate(self, aggregate_data: Dict[str, Any]):
        """
        Publish aggregated OHLCV data with circuit breaker

        Args:
            aggregate_data: OHLCV candle data
                {
                    'symbol': 'EUR/USD',
                    'timeframe': '5m',
                    'timestamp_ms': 1706198400000,
                    'open': 1.0850,
                    'high': 1.0855,
                    'low': 1.0848,
                    'close': 1.0852,
                    'volume': 1234,
                    'vwap': 1.0851,
                    'range_pips': 0.70,
                    'body_pips': 0.20,
                    'start_time': '2024-01-25T10:00:00+00:00',
                    'end_time': '2024-01-25T10:05:00+00:00',
                    'source': 'live_aggregated',
                    'event_type': 'ohlcv'
                }
        """
        symbol = aggregate_data.get('symbol', '').replace('/', '')  # EUR/USD → EURUSD
        timeframe = aggregate_data.get('timeframe', '5m')

        # NATS subject pattern: bars.EURUSD.5m
        subject_pattern = self.nats_config.get('subjects', {}).get('aggregates', 'bars.{symbol}.{timeframe}')
        subject = subject_pattern.format(symbol=symbol, timeframe=timeframe)

        # Add metadata
        aggregate_data['_source'] = 'live_aggregated'
        aggregate_data['_subject'] = subject

        message = json.dumps(aggregate_data).encode('utf-8')

        # Try to publish through circuit breaker
        success, result = await self.circuit_breaker.call_async(
            self._publish_to_nats,
            subject,
            message
        )

        if success:
            self.nats_publish_count += 1

            if self.nats_publish_count % 50 == 0:
                cb_stats = self.circuit_breaker.get_stats()
                logger.info(f"✅ {symbol} {timeframe} | "
                           f"NATS: {self.nats_publish_count} | "
                           f"Circuit: {cb_stats['state'].upper()} | "
                           f"Queued: {self.fallback_queue_count}")

        else:
            # Circuit is OPEN or publish failed
            if self.circuit_breaker.is_open:
                logger.debug(f"⚠️ Circuit OPEN - Queueing {symbol} {timeframe} to PostgreSQL")
            else:
                logger.warning(f"⚠️ NATS publish failed for {symbol} {timeframe}: {result}")

            # Fallback: Save to PostgreSQL queue
            await self._save_to_fallback_queue(subject, aggregate_data, symbol, timeframe)

    async def _publish_to_nats(self, subject: str, message: bytes):
        """
        Internal method to publish to NATS

        Args:
            subject: NATS subject
            message: Encoded message

        Raises:
            Exception: If publish fails
        """
        await self.nats.publish(subject, message)

    async def _save_to_fallback_queue(
        self,
        subject: str,
        payload: Dict[str, Any],
        symbol: str,
        timeframe: str
    ):
        """
        Save failed message to PostgreSQL fallback queue

        Args:
            subject: NATS subject
            payload: Message payload (OHLCV data)
            symbol: Trading symbol
            timeframe: Timeframe
        """
        if not self.db_pool:
            logger.error("❌ Cannot save to fallback queue - no database connection")
            return

        try:
            # Calculate next retry time (exponential backoff)
            next_retry = datetime.utcnow() + timedelta(seconds=30)

            async with self.db_pool.acquire() as conn:
                await self._execute_query_with_timeout(
                    conn,
                    """
                    INSERT INTO nats_message_queue
                    (subject, payload, symbol, timeframe, event_type, next_retry_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    subject,
                    json.dumps(payload),
                    symbol,
                    timeframe,
                    payload.get('event_type', 'ohlcv'),
                    next_retry,
                    timeout=self.QUERY_TIMEOUT_SHORT,
                    query_name="insert_fallback_queue",
                    fetch=False
                )

            self.fallback_queue_count += 1

            if self.fallback_queue_count % 10 == 1:
                logger.info(f"💾 Queued to PostgreSQL: {symbol} {timeframe} "
                           f"(total: {self.fallback_queue_count})")

        except Exception as e:
            logger.error(f"❌ Failed to save to fallback queue: {e}")

    async def _retry_queued_messages(self):
        """
        Retry publishing messages from PostgreSQL queue

        Called automatically when circuit breaker transitions to CLOSED
        """
        if not self.db_pool:
            return

        try:
            logger.info("♻️ Retrying queued messages from PostgreSQL...")

            async with self.db_pool.acquire() as conn:
                # Get pending messages ready for retry
                rows = await self._execute_query_with_timeout(
                    conn,
                    """
                    SELECT id, subject, payload, symbol, timeframe, retry_count
                    FROM nats_message_queue
                    WHERE status = 'pending'
                      AND (next_retry_at IS NULL OR next_retry_at <= NOW())
                      AND retry_count < max_retries
                    ORDER BY created_at ASC
                    LIMIT 100
                    """,
                    timeout=self.QUERY_TIMEOUT_SHORT,
                    query_name="fetch_pending_messages"
                )

                if not rows:
                    logger.debug("No queued messages to retry")
                    return

                success_count = 0
                fail_count = 0

                for row in rows:
                    msg_id = row['id']
                    subject = row['subject']
                    payload = json.loads(row['payload'])
                    retry_count = row['retry_count']

                    # Mark as processing
                    await self._execute_query_with_timeout(
                        conn,
                        """
                        UPDATE nats_message_queue
                        SET status = 'processing'
                        WHERE id = $1
                        """,
                        msg_id,
                        timeout=self.QUERY_TIMEOUT_SHORT,
                        query_name="mark_processing",
                        fetch=False
                    )

                    # Try to publish
                    try:
                        message = json.dumps(payload).encode('utf-8')
                        await self.nats.publish(subject, message)

                        # Success - mark as published
                        await self._execute_query_with_timeout(
                            conn,
                            """
                            UPDATE nats_message_queue
                            SET status = 'success',
                                published_at = NOW(),
                                retry_count = retry_count + 1
                            WHERE id = $1
                            """,
                            msg_id,
                            timeout=self.QUERY_TIMEOUT_SHORT,
                            query_name="mark_success",
                            fetch=False
                        )

                        success_count += 1
                        self.retry_success_count += 1

                    except Exception as e:
                        # Failed - update retry count and next retry time
                        next_retry = datetime.utcnow() + timedelta(
                            seconds=min(300, 30 * (2 ** retry_count))  # Exponential backoff, max 5 min
                        )

                        # Check if exceeded max retries
                        new_retry_count = retry_count + 1
                        new_status = 'failed' if new_retry_count >= 5 else 'pending'

                        await self._execute_query_with_timeout(
                            conn,
                            """
                            UPDATE nats_message_queue
                            SET status = $1,
                                retry_count = $2,
                                next_retry_at = $3,
                                error_message = $4
                            WHERE id = $5
                            """,
                            new_status,
                            new_retry_count,
                            next_retry,
                            str(e)[:500],
                            msg_id,
                            timeout=self.QUERY_TIMEOUT_SHORT,
                            query_name="mark_failed",
                            fetch=False
                        )

                        fail_count += 1

                logger.info(f"♻️ Retry complete: {success_count} success, {fail_count} failed")

        except Exception as e:
            logger.error(f"❌ Error retrying queued messages: {e}")

    async def close(self):
        """Close NATS and PostgreSQL connections"""
        if self.nats:
            await self.nats.close()
            logger.info("✅ NATS connection closed")

        if self.db_pool:
            await self.db_pool.close()
            logger.info("✅ PostgreSQL connection closed")

    def get_stats(self) -> Dict[str, Any]:
        """Get publisher statistics"""
        query_stats = self.get_query_stats()
        stats = {
            'nats_publish_count': self.nats_publish_count,
            'fallback_queue_count': self.fallback_queue_count,
            'retry_success_count': self.retry_success_count,
            'query_performance': query_stats
        }

        # Add circuit breaker stats
        cb_stats = self.circuit_breaker.get_stats()
        stats['circuit_breaker'] = {
            'state': cb_stats['state'],
            'total_failures': cb_stats['total_failures'],
            'total_successes': cb_stats['total_successes'],
            'state_transitions': cb_stats['state_transitions']
        }

        return stats
