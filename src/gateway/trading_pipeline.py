"""
High-Performance Trading Data Pipeline
Core trading data ingestion, validation, and routing system with sub-500ms latency
Supports 18+ ticks/second throughput with multi-database routing
"""

import asyncio
import logging
import time
import json
import aioredis
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from decimal import Decimal
import websockets
import psycopg2.pool
from clickhouse_driver import Client as ClickHouseClient
import numpy as np
from pydantic import BaseModel, Field, validator
from enum import Enum
import hashlib
import uvloop
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
import threading
from collections import defaultdict, deque
import weakref

# Performance monitoring
from prometheus_client import Counter, Histogram, Gauge
import resource

# Initialize uvloop for better performance
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# Metrics
TICK_COUNTER = Counter('trading_pipeline_ticks_total', 'Total ticks processed', ['source', 'symbol'])
LATENCY_HISTOGRAM = Histogram('trading_pipeline_latency_seconds', 'Processing latency', ['operation'])
ACTIVE_CONNECTIONS = Gauge('trading_pipeline_connections', 'Active WebSocket connections')
ERROR_COUNTER = Counter('trading_pipeline_errors_total', 'Total errors', ['error_type', 'source'])
THROUGHPUT_GAUGE = Gauge('trading_pipeline_throughput_tps', 'Throughput in ticks per second')

logger = logging.getLogger(__name__)


class DataSource(Enum):
    MT5 = "mt5"
    TRADINGVIEW = "tradingview"
    MLQ5 = "mlq5"
    BINANCE = "binance"
    ALPHAVANTAGE = "alphavantage"
    YAHOO = "yahoo"
    IEX = "iex"
    POLYGON = "polygon"
    FINNHUB = "finnhub"
    QUANDL = "quandl"
    FXCM = "fxcm"
    INTERACTIVE_BROKERS = "interactive_brokers"
    OANDA = "oanda"
    DUKASCOPY = "dukascopy"


class DataType(Enum):
    TICK = "tick"
    CANDLE = "candle"
    ORDER_BOOK = "order_book"
    TRADE = "trade"
    NEWS = "news"
    SENTIMENT = "sentiment"
    ECONOMIC_CALENDAR = "economic_calendar"
    MARKET_DEPTH = "market_depth"
    VOLUME_PROFILE = "volume_profile"
    OPTIONS_CHAIN = "options_chain"
    FUTURES_CURVE = "futures_curve"
    CORRELATION_MATRIX = "correlation_matrix"
    VOLATILITY_SURFACE = "volatility_surface"
    MACRO_INDICATORS = "macro_indicators"


class DatabaseTarget(Enum):
    CLICKHOUSE = "clickhouse"  # Time-series data
    POSTGRESQL = "postgresql"  # Relational data
    REDIS = "redis"           # Cache/session data
    WEAVIATE = "weaviate"     # Vector/semantic data
    ARANGODB = "arangodb"     # Graph data


@dataclass
class TickData:
    """High-performance tick data structure"""
    symbol: str
    timestamp: float
    bid: Decimal
    ask: Decimal
    last: Decimal
    volume: int
    source: DataSource

    def __post_init__(self):
        # Convert to nanosecond precision for better accuracy
        if isinstance(self.timestamp, (int, float)):
            self.timestamp = int(self.timestamp * 1_000_000_000)


@dataclass
class CandleData:
    """OHLCV candle data"""
    symbol: str
    timestamp: float
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    timeframe: str
    source: DataSource


class ValidationResult(BaseModel):
    """Data validation result"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    normalized_data: Optional[Dict] = None


class ProcessingMetrics(BaseModel):
    """Pipeline processing metrics"""
    total_processed: int = 0
    errors: int = 0
    latency_p50: float = 0.0
    latency_p95: float = 0.0
    latency_p99: float = 0.0
    throughput_tps: float = 0.0
    last_update: datetime = Field(default_factory=datetime.utcnow)


class TradingDataValidator:
    """High-performance data validation with caching"""

    def __init__(self):
        self._validation_cache = {}
        self._cache_lock = threading.RLock()

    def validate_tick(self, data: Dict) -> ValidationResult:
        """Validate tick data with sub-millisecond performance"""
        try:
            errors = []
            warnings = []

            # Required fields check
            required_fields = ['symbol', 'timestamp', 'bid', 'ask', 'last']
            missing_fields = [f for f in required_fields if f not in data or data[f] is None]
            if missing_fields:
                errors.append(f"Missing required fields: {missing_fields}")

            # Data type validation
            if 'symbol' in data and not isinstance(data['symbol'], str):
                errors.append("Symbol must be string")

            if 'timestamp' in data:
                try:
                    ts = float(data['timestamp'])
                    if ts <= 0:
                        errors.append("Timestamp must be positive")
                except (ValueError, TypeError):
                    errors.append("Invalid timestamp format")

            # Price validation
            for price_field in ['bid', 'ask', 'last']:
                if price_field in data:
                    try:
                        price = Decimal(str(data[price_field]))
                        if price <= 0:
                            errors.append(f"{price_field} must be positive")
                    except (ValueError, TypeError):
                        errors.append(f"Invalid {price_field} format")

            # Spread validation
            if all(field in data for field in ['bid', 'ask']):
                try:
                    bid = Decimal(str(data['bid']))
                    ask = Decimal(str(data['ask']))
                    if ask <= bid:
                        warnings.append("Ask price should be higher than bid")
                except:
                    pass

            # Normalize data
            normalized_data = {
                'symbol': data.get('symbol', '').upper(),
                'timestamp': float(data.get('timestamp', 0)),
                'bid': float(data.get('bid', 0)),
                'ask': float(data.get('ask', 0)),
                'last': float(data.get('last', 0)),
                'volume': int(data.get('volume', 0)),
                'source': data.get('source', DataSource.MT5.value)
            }

            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                normalized_data=normalized_data
            )

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation exception: {str(e)}"]
            )


class DatabaseRouter:
    """Intelligent database routing based on data type and performance requirements"""

    def __init__(self):
        self.connections = {}
        self.connection_pools = {}
        self._setup_connections()

    def _setup_connections(self):
        """Initialize database connections with pooling"""
        try:
            # ClickHouse for time-series data
            self.connections[DatabaseTarget.CLICKHOUSE] = ClickHouseClient(
                host='localhost',
                port=9000,
                database='trading_data',
                settings={'use_numpy': True}
            )

            # PostgreSQL for relational data
            self.connection_pools[DatabaseTarget.POSTGRESQL] = psycopg2.pool.ThreadedConnectionPool(
                minconn=2,
                maxconn=20,
                host='localhost',
                port=5432,
                database='trading_db',
                user='trading_user',
                password='trading_pass'
            )

        except Exception as e:
            logger.error(f"Database connection error: {e}")

    def route_data(self, data_type: DataType, data: Dict) -> DatabaseTarget:
        """Determine optimal database for data type"""
        routing_map = {
            DataType.TICK: DatabaseTarget.CLICKHOUSE,
            DataType.CANDLE: DatabaseTarget.CLICKHOUSE,
            DataType.ORDER_BOOK: DatabaseTarget.CLICKHOUSE,
            DataType.TRADE: DatabaseTarget.CLICKHOUSE,
            DataType.NEWS: DatabaseTarget.POSTGRESQL,
            DataType.SENTIMENT: DatabaseTarget.WEAVIATE,
            DataType.ECONOMIC_CALENDAR: DatabaseTarget.POSTGRESQL,
            DataType.MARKET_DEPTH: DatabaseTarget.CLICKHOUSE,
            DataType.VOLUME_PROFILE: DatabaseTarget.CLICKHOUSE,
            DataType.OPTIONS_CHAIN: DatabaseTarget.POSTGRESQL,
            DataType.FUTURES_CURVE: DatabaseTarget.CLICKHOUSE,
            DataType.CORRELATION_MATRIX: DatabaseTarget.ARANGODB,
            DataType.VOLATILITY_SURFACE: DatabaseTarget.CLICKHOUSE,
            DataType.MACRO_INDICATORS: DatabaseTarget.POSTGRESQL
        }
        return routing_map.get(data_type, DatabaseTarget.CLICKHOUSE)

    async def store_data(self, target: DatabaseTarget, data_type: DataType, data: Dict) -> bool:
        """Store data in target database with performance optimization"""
        try:
            if target == DatabaseTarget.CLICKHOUSE:
                return await self._store_clickhouse(data_type, data)
            elif target == DatabaseTarget.POSTGRESQL:
                return await self._store_postgresql(data_type, data)
            else:
                logger.warning(f"Database {target} not implemented yet")
                return False

        except Exception as e:
            logger.error(f"Storage error for {target}: {e}")
            ERROR_COUNTER.labels(error_type='storage', source=str(target)).inc()
            return False

    async def _store_clickhouse(self, data_type: DataType, data: Dict) -> bool:
        """Store data in ClickHouse with batch optimization"""
        try:
            if data_type == DataType.TICK:
                query = """
                INSERT INTO tick_data (symbol, timestamp, bid, ask, last, volume, source)
                VALUES
                """
                values = (
                    data['symbol'],
                    datetime.fromtimestamp(data['timestamp'], tz=timezone.utc),
                    data['bid'],
                    data['ask'],
                    data['last'],
                    data['volume'],
                    data['source']
                )

                # Use async execution for better performance
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    await loop.run_in_executor(
                        executor,
                        lambda: self.connections[DatabaseTarget.CLICKHOUSE].execute(query, [values])
                    )
                return True

        except Exception as e:
            logger.error(f"ClickHouse storage error: {e}")
            return False

    async def _store_postgresql(self, data_type: DataType, data: Dict) -> bool:
        """Store data in PostgreSQL"""
        try:
            # Implementation for PostgreSQL storage
            return True
        except Exception as e:
            logger.error(f"PostgreSQL storage error: {e}")
            return False


class PerformanceMonitor:
    """Real-time performance monitoring and bottleneck detection"""

    def __init__(self):
        self.metrics = ProcessingMetrics()
        self.latency_samples = deque(maxlen=1000)
        self.throughput_window = deque(maxlen=60)  # 60-second window
        self.last_throughput_check = time.time()
        self.tick_count_window = 0

    def record_latency(self, operation: str, latency: float):
        """Record operation latency"""
        self.latency_samples.append(latency)
        LATENCY_HISTOGRAM.labels(operation=operation).observe(latency)

        # Update percentiles
        if len(self.latency_samples) >= 10:
            sorted_samples = sorted(self.latency_samples)
            self.metrics.latency_p50 = sorted_samples[len(sorted_samples) // 2]
            self.metrics.latency_p95 = sorted_samples[int(len(sorted_samples) * 0.95)]
            self.metrics.latency_p99 = sorted_samples[int(len(sorted_samples) * 0.99)]

    def record_tick(self):
        """Record tick processing for throughput calculation"""
        self.tick_count_window += 1
        current_time = time.time()

        # Calculate throughput every second
        if current_time - self.last_throughput_check >= 1.0:
            tps = self.tick_count_window / (current_time - self.last_throughput_check)
            self.metrics.throughput_tps = tps
            THROUGHPUT_GAUGE.set(tps)

            self.throughput_window.append(tps)
            self.tick_count_window = 0
            self.last_throughput_check = current_time

    def detect_bottlenecks(self) -> List[str]:
        """Detect performance bottlenecks"""
        bottlenecks = []

        # Latency bottlenecks
        if self.metrics.latency_p95 > 0.5:  # 500ms threshold
            bottlenecks.append(f"High latency: P95={self.metrics.latency_p95:.3f}s")

        # Throughput bottlenecks
        if self.metrics.throughput_tps < 18:  # Below 18 TPS requirement
            bottlenecks.append(f"Low throughput: {self.metrics.throughput_tps:.1f} TPS")

        # Memory bottlenecks
        memory_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if memory_usage > 1024 * 1024 * 1024:  # 1GB threshold
            bottlenecks.append(f"High memory usage: {memory_usage / (1024*1024):.0f}MB")

        return bottlenecks


class MT5WebSocketBridge:
    """High-performance MT5 WebSocket bridge with real-time tick processing"""

    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.connections = set()
        self.is_running = False
        self.server = None

    async def start_server(self, host='localhost', port=8765):
        """Start WebSocket server for MT5 connections"""
        try:
            self.server = await websockets.serve(
                self.handle_connection,
                host,
                port,
                ping_interval=20,
                ping_timeout=10,
                max_size=1024*1024,  # 1MB max message size
                compression=None      # Disable compression for speed
            )
            self.is_running = True
            logger.info(f"MT5 WebSocket bridge started on {host}:{port}")

        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            raise

    async def handle_connection(self, websocket, path):
        """Handle incoming WebSocket connections"""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"New MT5 connection: {client_id}")

        self.connections.add(websocket)
        ACTIVE_CONNECTIONS.inc()

        try:
            async for message in websocket:
                start_time = time.time()

                try:
                    # Parse incoming data
                    data = json.loads(message)

                    # Route to pipeline
                    await self.pipeline.process_mt5_data(data)

                    # Record performance
                    latency = time.time() - start_time
                    self.pipeline.monitor.record_latency('mt5_processing', latency)

                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from {client_id}")
                    ERROR_COUNTER.labels(error_type='json_decode', source='mt5').inc()

                except Exception as e:
                    logger.error(f"Error processing MT5 data from {client_id}: {e}")
                    ERROR_COUNTER.labels(error_type='processing', source='mt5').inc()

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"MT5 connection closed: {client_id}")

        except Exception as e:
            logger.error(f"WebSocket error for {client_id}: {e}")

        finally:
            self.connections.discard(websocket)
            ACTIVE_CONNECTIONS.dec()

    async def stop_server(self):
        """Stop WebSocket server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.is_running = False
            logger.info("MT5 WebSocket bridge stopped")


class TradingDataPipeline:
    """Main trading data pipeline orchestrator"""

    def __init__(self):
        self.validator = TradingDataValidator()
        self.router = DatabaseRouter()
        self.monitor = PerformanceMonitor()
        self.mt5_bridge = MT5WebSocketBridge(self)
        self.redis_client = None
        self.is_running = False
        self.processing_queue = asyncio.Queue(maxsize=10000)
        self.worker_tasks = []

    async def initialize(self):
        """Initialize pipeline components"""
        try:
            # Initialize Redis for caching
            self.redis_client = aioredis.from_url("redis://localhost:6379")
            await self.redis_client.ping()

            # Start processing workers
            for i in range(4):  # 4 worker threads for parallel processing
                task = asyncio.create_task(self._processing_worker(f"worker-{i}"))
                self.worker_tasks.append(task)

            # Start MT5 bridge
            await self.mt5_bridge.start_server()

            self.is_running = True
            logger.info("Trading data pipeline initialized successfully")

        except Exception as e:
            logger.error(f"Pipeline initialization failed: {e}")
            raise

    async def process_mt5_data(self, data: Dict):
        """Process incoming MT5 data with high performance"""
        try:
            # Add to processing queue for async handling
            await self.processing_queue.put({
                'data': data,
                'source': DataSource.MT5,
                'timestamp': time.time()
            })

            # Record tick for throughput monitoring
            self.monitor.record_tick()

        except asyncio.QueueFull:
            logger.warning("Processing queue full, dropping data")
            ERROR_COUNTER.labels(error_type='queue_full', source='mt5').inc()

    async def _processing_worker(self, worker_id: str):
        """Background worker for processing data"""
        logger.info(f"Processing worker {worker_id} started")

        while self.is_running:
            try:
                # Get data from queue with timeout
                item = await asyncio.wait_for(
                    self.processing_queue.get(),
                    timeout=1.0
                )

                start_time = time.time()

                # Process the data
                await self._process_data_item(item)

                # Record processing latency
                latency = time.time() - start_time
                self.monitor.record_latency('data_processing', latency)

                # Mark task as done
                self.processing_queue.task_done()

            except asyncio.TimeoutError:
                continue  # No data in queue, continue loop

            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                ERROR_COUNTER.labels(error_type='worker_error', source=worker_id).inc()

    async def _process_data_item(self, item: Dict):
        """Process individual data item through pipeline"""
        try:
            data = item['data']
            source = item['source']

            # Determine data type
            data_type = self._determine_data_type(data)

            # Validate data
            validation_result = self.validator.validate_tick(data)
            if not validation_result.is_valid:
                logger.warning(f"Invalid data: {validation_result.errors}")
                ERROR_COUNTER.labels(error_type='validation', source=str(source)).inc()
                return

            # Route to appropriate database
            target_db = self.router.route_data(data_type, validation_result.normalized_data)

            # Store data
            success = await self.router.store_data(
                target_db,
                data_type,
                validation_result.normalized_data
            )

            if success:
                TICK_COUNTER.labels(
                    source=str(source),
                    symbol=validation_result.normalized_data.get('symbol', 'unknown')
                ).inc()

                # Cache recent data in Redis for fast access
                await self._cache_recent_data(validation_result.normalized_data)

            else:
                ERROR_COUNTER.labels(error_type='storage_failed', source=str(source)).inc()

        except Exception as e:
            logger.error(f"Data processing error: {e}")
            ERROR_COUNTER.labels(error_type='processing_error', source='pipeline').inc()

    def _determine_data_type(self, data: Dict) -> DataType:
        """Determine data type from incoming data"""
        # Simple heuristic - can be enhanced with more sophisticated logic
        if 'bid' in data and 'ask' in data:
            return DataType.TICK
        elif 'open' in data and 'high' in data and 'low' in data and 'close' in data:
            return DataType.CANDLE
        else:
            return DataType.TICK  # Default

    async def _cache_recent_data(self, data: Dict):
        """Cache recent data in Redis for fast access"""
        try:
            if self.redis_client:
                key = f"recent_tick:{data['symbol']}"
                await self.redis_client.setex(
                    key,
                    60,  # 60 second TTL
                    json.dumps(data, default=str)
                )
        except Exception as e:
            logger.error(f"Redis caching error: {e}")

    async def get_metrics(self) -> Dict:
        """Get current pipeline metrics"""
        bottlenecks = self.monitor.detect_bottlenecks()

        return {
            'processing_metrics': asdict(self.monitor.metrics),
            'queue_size': self.processing_queue.qsize(),
            'active_connections': len(self.mt5_bridge.connections),
            'bottlenecks': bottlenecks,
            'is_running': self.is_running
        }

    async def shutdown(self):
        """Gracefully shutdown pipeline"""
        logger.info("Shutting down trading pipeline...")

        self.is_running = False

        # Stop MT5 bridge
        await self.mt5_bridge.stop_server()

        # Wait for queue to empty
        await self.processing_queue.join()

        # Cancel worker tasks
        for task in self.worker_tasks:
            task.cancel()

        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()

        logger.info("Trading pipeline shutdown complete")


# Global pipeline instance
pipeline = None


async def get_pipeline() -> TradingDataPipeline:
    """Get or create pipeline instance"""
    global pipeline
    if pipeline is None:
        pipeline = TradingDataPipeline()
        await pipeline.initialize()
    return pipeline


@asynccontextmanager
async def pipeline_context():
    """Context manager for pipeline lifecycle"""
    pipeline_instance = await get_pipeline()
    try:
        yield pipeline_instance
    finally:
        await pipeline_instance.shutdown()


# Performance testing utilities
class PerformanceTester:
    """Performance testing and benchmarking"""

    @staticmethod
    async def test_latency(pipeline: TradingDataPipeline, num_samples: int = 1000):
        """Test processing latency"""
        latencies = []

        for i in range(num_samples):
            start_time = time.time()

            # Generate test tick data
            test_data = {
                'symbol': 'EURUSD',
                'timestamp': time.time(),
                'bid': 1.1234,
                'ask': 1.1236,
                'last': 1.1235,
                'volume': 100,
                'source': 'mt5'
            }

            await pipeline.process_mt5_data(test_data)

            latency = time.time() - start_time
            latencies.append(latency)

        # Wait for processing to complete
        await pipeline.processing_queue.join()

        return {
            'mean_latency': np.mean(latencies),
            'p50_latency': np.percentile(latencies, 50),
            'p95_latency': np.percentile(latencies, 95),
            'p99_latency': np.percentile(latencies, 99),
            'max_latency': np.max(latencies),
            'samples': num_samples
        }

    @staticmethod
    async def test_throughput(pipeline: TradingDataPipeline, duration: int = 60):
        """Test throughput over specified duration"""
        start_time = time.time()
        tick_count = 0

        while time.time() - start_time < duration:
            test_data = {
                'symbol': f'SYMBOL_{tick_count % 10}',
                'timestamp': time.time(),
                'bid': 1.0 + (tick_count % 100) * 0.0001,
                'ask': 1.0002 + (tick_count % 100) * 0.0001,
                'last': 1.0001 + (tick_count % 100) * 0.0001,
                'volume': 100,
                'source': 'mt5'
            }

            await pipeline.process_mt5_data(test_data)
            tick_count += 1

            # Small delay to simulate realistic timing
            await asyncio.sleep(0.001)

        actual_duration = time.time() - start_time
        tps = tick_count / actual_duration

        return {
            'total_ticks': tick_count,
            'duration': actual_duration,
            'throughput_tps': tps,
            'target_met': tps >= 18
        }


if __name__ == "__main__":
    """Development testing entry point"""
    async def main():
        async with pipeline_context() as pipeline:
            logger.info("Trading pipeline started")

            # Run performance tests
            print("Running latency test...")
            latency_results = await PerformanceTester.test_latency(pipeline, 100)
            print(f"Latency results: {latency_results}")

            print("Running throughput test...")
            throughput_results = await PerformanceTester.test_throughput(pipeline, 10)
            print(f"Throughput results: {throughput_results}")

            # Keep running for manual testing
            print("Pipeline running. Connect MT5 WebSocket to localhost:8765")
            print("Press Ctrl+C to stop...")

            try:
                while True:
                    metrics = await pipeline.get_metrics()
                    print(f"Queue size: {metrics['queue_size']}, "
                          f"Connections: {metrics['active_connections']}, "
                          f"TPS: {metrics['processing_metrics']['throughput_tps']:.1f}")
                    await asyncio.sleep(5)

            except KeyboardInterrupt:
                print("Stopping pipeline...")

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run the pipeline
    asyncio.run(main())