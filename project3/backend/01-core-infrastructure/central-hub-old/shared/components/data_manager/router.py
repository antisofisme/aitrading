"""
Data Router - Smart Routing Logic
Main entry point for all database operations
Phase 1: TimescaleDB + DragonflyDB with smart routing
"""
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import TickData, CandleData, HealthCheckResponse
from .pools import get_pool_manager
from .cache import MultiLevelCache
from .exceptions import (
    QueryExecutionError,
    ValidationError,
    RoutingError
)


class DataRouter:
    """
    Smart data routing for multi-database architecture
    Routes operations to optimal database based on use case
    """

    def __init__(self):
        self.pool_manager = None
        self.cache = None
        self._initialized = False

    async def initialize(self):
        """Initialize router with connection pools and cache"""
        if self._initialized:
            return

        # Get pool manager (singleton)
        self.pool_manager = await get_pool_manager()

        # Initialize multi-level cache
        dragonfly_client = self.pool_manager.get_dragonfly_client()
        self.cache = MultiLevelCache(dragonfly_client, l1_max_size=1000, l1_ttl=60)

        self._initialized = True

    async def _ensure_initialized(self):
        """Ensure router is initialized before operations"""
        if not self._initialized:
            await self.initialize()

    # ============================================================================
    # WRITE OPERATIONS
    # ============================================================================

    async def save_tick(self, tick_data: TickData):
        """
        Save tick data with deduplication
        Route: TimescaleDB (primary) + DragonflyDB (cache latest)

        Deduplication Strategy:
        - Check if (symbol, timestamp) already exists before insert
        - Skip insert if duplicate found
        - Prevents 23.7% duplication issue
        """
        await self._ensure_initialized()

        try:
            # Validate data
            if not isinstance(tick_data, TickData):
                raise ValidationError("TickData", ["Invalid data type"])

            # ✅ LAYER 2 DEDUPLICATION: Check existence before insert
            conn = await self.pool_manager.get_timescale_connection()
            try:
                # Check if tick already exists
                existing = await conn.fetchval("""
                    SELECT 1 FROM market_ticks
                    WHERE symbol = $1
                      AND time = to_timestamp($2/1000.0)
                    LIMIT 1
                """, tick_data.symbol, tick_data.timestamp)

                if existing:
                    # Skip duplicate insert
                    # logger.debug(f"⏭️  Skip duplicate tick: {tick_data.symbol} @ {tick_data.timestamp}")
                    return  # Exit early

                # Insert only if not duplicate
                await conn.execute("""
                    INSERT INTO market_ticks (
                        time, tenant_id, symbol, bid, ask, mid, spread,
                        source, event_type, timestamp_ms
                    ) VALUES (to_timestamp($1/1000.0), $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """, tick_data.timestamp, 'system', tick_data.symbol,
                    tick_data.bid, tick_data.ask, tick_data.mid, tick_data.spread,
                    tick_data.source, 'quote', tick_data.timestamp)
            finally:
                await self.pool_manager.release_timescale_connection(conn)

            # Cache latest tick (L1 + L2)
            cache_key = f"tick:latest:{tick_data.symbol}"
            await self.cache.set(
                cache_key,
                tick_data.dict(),
                l1_ttl=60,    # 1 minute in L1
                l2_ttl=3600   # 1 hour in L2
            )

        except Exception as e:
            raise QueryExecutionError("timescale", "INSERT tick", str(e))

    async def save_candle(self, candle_data: CandleData):
        """
        Save candle data
        Route: TimescaleDB (primary) + DragonflyDB (cache latest)
        Phase 2 will add: ClickHouse (analytics)
        """
        await self._ensure_initialized()

        try:
            # Validate data
            if not isinstance(candle_data, CandleData):
                raise ValidationError("CandleData", ["Invalid data type"])

            # Save to TimescaleDB
            conn = await self.pool_manager.get_timescale_connection()
            try:
                await conn.execute("""
                    INSERT INTO candles (
                        symbol, timeframe, timestamp, timestamp_ms,
                        open, high, low, close, volume, vwap, range_pips,
                        num_trades, start_time, end_time, source, event_type
                    ) VALUES ($1, $2, to_timestamp($3/1000.0), $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                """, candle_data.symbol, candle_data.timeframe, candle_data.timestamp,
                    candle_data.timestamp_ms, candle_data.open, candle_data.high,
                    candle_data.low, candle_data.close, candle_data.volume,
                    candle_data.vwap, candle_data.range_pips, candle_data.num_trades,
                    candle_data.start_time, candle_data.end_time,
                    candle_data.source, candle_data.event_type)
            finally:
                await self.pool_manager.release_timescale_connection(conn)

            # Cache latest candles
            cache_key = f"candle:latest:{candle_data.symbol}:{candle_data.timeframe}"
            await self.cache.set(
                cache_key,
                candle_data.dict(),
                l1_ttl=60,
                l2_ttl=3600
            )

            # Invalidate candle list cache
            await self.cache.invalidate_pattern(
                f"candle:latest:{candle_data.symbol}:{candle_data.timeframe}:*"
            )

        except Exception as e:
            raise QueryExecutionError("timescale", "INSERT candle", str(e))

    async def save_candles_bulk(self, candles: List[CandleData]):
        """
        Bulk save candles (optimized for historical data import)
        Route: TimescaleDB (primary)
        Phase 2 will add: ClickHouse (bulk analytics)
        """
        await self._ensure_initialized()

        if not candles:
            return

        try:
            conn = await self.pool_manager.get_timescale_connection()
            try:
                # Prepare bulk insert data
                values = [
                    (c.symbol, c.timeframe, c.timestamp, c.timestamp_ms,
                     c.open, c.high, c.low, c.close, c.volume,
                     c.vwap, c.range_pips, c.num_trades,
                     c.start_time, c.end_time, c.source, c.event_type)
                    for c in candles
                ]

                # Bulk insert
                await conn.executemany("""
                    INSERT INTO candles (
                        symbol, timeframe, timestamp, timestamp_ms,
                        open, high, low, close, volume, vwap, range_pips,
                        num_trades, start_time, end_time, source, event_type
                    ) VALUES ($1, $2, to_timestamp($3/1000.0), $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                """, values)

            finally:
                await self.pool_manager.release_timescale_connection(conn)

        except Exception as e:
            raise QueryExecutionError("timescale", "BULK INSERT candles", str(e))

    # ============================================================================
    # READ OPERATIONS
    # ============================================================================

    async def get_latest_tick(self, symbol: str) -> Optional[TickData]:
        """
        Get latest tick for symbol
        Route: DragonflyDB (cache) → TimescaleDB (fallback)
        """
        await self._ensure_initialized()

        cache_key = f"tick:latest:{symbol}"

        # Try cache first
        cached = await self.cache.get(cache_key)
        if cached:
            return TickData(**cached)

        # Cache miss - query database
        try:
            conn = await self.pool_manager.get_timescale_connection()
            try:
                row = await conn.fetchrow("""
                    SELECT * FROM ticks
                    WHERE symbol = $1
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, symbol)

                if row:
                    tick_dict = dict(row)
                    # Cache for next time
                    await self.cache.set(cache_key, tick_dict, l1_ttl=60, l2_ttl=3600)
                    return TickData(**tick_dict)

            finally:
                await self.pool_manager.release_timescale_connection(conn)

        except Exception as e:
            raise QueryExecutionError("timescale", "SELECT latest tick", str(e))

        return None

    async def get_latest_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100
    ) -> List[CandleData]:
        """
        Get latest N candles
        Route: DragonflyDB (cache) → TimescaleDB (fallback)
        Phase 2 will add: ClickHouse optimization
        """
        await self._ensure_initialized()

        cache_key = f"candle:latest:{symbol}:{timeframe}:{limit}"

        # Try cache first
        cached = await self.cache.get(cache_key)
        if cached:
            return [CandleData(**c) for c in cached]

        # Cache miss - query database
        try:
            conn = await self.pool_manager.get_timescale_connection()
            try:
                rows = await conn.fetch("""
                    SELECT * FROM candles
                    WHERE symbol = $1 AND timeframe = $2
                    ORDER BY timestamp DESC
                    LIMIT $3
                """, symbol, timeframe, limit)

                if rows:
                    candles_dict = [dict(row) for row in rows]
                    # Cache for next time
                    await self.cache.set(cache_key, candles_dict, l1_ttl=60, l2_ttl=3600)
                    return [CandleData(**c) for c in candles_dict]

            finally:
                await self.pool_manager.release_timescale_connection(conn)

        except Exception as e:
            raise QueryExecutionError("timescale", "SELECT latest candles", str(e))

        return []

    # ============================================================================
    # HEALTH & MONITORING
    # ============================================================================

    async def health_check(self) -> HealthCheckResponse:
        """Health check for all databases and cache"""
        await self._ensure_initialized()

        # Database health
        db_health = await self.pool_manager.health_check_all()

        # Cache stats
        cache_stats = await self.cache.get_stats()

        return HealthCheckResponse(
            status="healthy" if all(v == "healthy" for v in db_health.values()) else "degraded",
            databases=db_health,
            connection_pools={
                "timescale": "active",
                "dragonfly": "active"
            },
            cache=cache_stats,
            timestamp=int(datetime.utcnow().timestamp() * 1000)
        )
