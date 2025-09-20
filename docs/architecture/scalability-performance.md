# AI Trading System - Scalability and Performance Recommendations

## Executive Summary

This document provides comprehensive recommendations for designing a scalable and high-performance AI trading system capable of handling high-frequency trading scenarios while maintaining low latency and high reliability.

## Performance Requirements Analysis

### 1. Latency Requirements

#### Critical Path Latencies
```
Market Data → Decision → Execution: < 200ms total
├── Data Collection: < 10ms
├── Data Processing: < 20ms
├── Feature Computation: < 30ms
├── ML Inference: < 50ms
├── Decision Logic: < 20ms
├── Risk Validation: < 10ms
├── Order Routing: < 30ms
└── Network Transit: < 30ms
```

#### Service-Level Latency Targets
- **P50**: < 100ms end-to-end
- **P95**: < 200ms end-to-end
- **P99**: < 500ms end-to-end
- **P99.9**: < 1000ms end-to-end

### 2. Throughput Requirements

#### Data Processing
- **Market Data Ingestion**: 100,000 ticks/second
- **Feature Computation**: 50,000 calculations/second
- **Predictions**: 10,000 predictions/second
- **Order Processing**: 1,000 orders/second

#### Concurrent Users
- **Active Traders**: 100 concurrent users
- **Dashboard Users**: 500 concurrent users
- **API Consumers**: 1,000 concurrent connections

## Horizontal Scaling Strategy

### 1. Microservices Scaling Patterns

#### Auto-scaling Configuration
```yaml
# hpa.yaml - Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: prediction-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: prediction-service
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: prediction_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

#### Service Mesh for Load Distribution
```yaml
# istio-virtual-service.yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: prediction-service
spec:
  hosts:
  - prediction-service
  http:
  - match:
    - headers:
        priority:
          exact: "high"
    route:
    - destination:
        host: prediction-service
        subset: high-performance
      weight: 100
  - route:
    - destination:
        host: prediction-service
        subset: standard
      weight: 80
    - destination:
        host: prediction-service
        subset: gpu-enabled
      weight: 20
```

### 2. Database Scaling Strategy

#### Time Series Database Scaling (InfluxDB)
```yaml
# influxdb-cluster.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: influxdb-config
data:
  influxdb.conf: |
    [meta]
      dir = "/var/lib/influxdb/meta"
      retention-autocreate = true
      logging-enabled = true

    [data]
      dir = "/var/lib/influxdb/data"
      wal-dir = "/var/lib/influxdb/wal"
      series-id-set-cache-size = 100

    [coordinator]
      write-timeout = "10s"
      max-concurrent-queries = 0
      query-timeout = "0s"
      log-queries-after = "0s"
      max-select-point = 0
      max-select-series = 0
      max-select-buckets = 0

    [retention]
      enabled = true
      check-interval = "30m"

    [http]
      enabled = true
      bind-address = ":8086"
      auth-enabled = false
      log-enabled = true
      write-tracing = false
      pprof-enabled = true
      https-enabled = false
      max-row-limit = 0
      max-connection-limit = 0
      shared-secret = ""
      realm = "InfluxDB"
      unix-socket-enabled = false
      bind-socket = "/var/run/influxdb.sock"
```

#### PostgreSQL Scaling with Citus
```sql
-- Distributed PostgreSQL setup
SELECT create_distributed_table('trades', 'symbol');
SELECT create_distributed_table('positions', 'account_id');
SELECT create_distributed_table('market_data_summary', 'symbol');

-- Create reference tables for static data
SELECT create_reference_table('symbols');
SELECT create_reference_table('strategies');

-- Optimize for time-series queries
CREATE INDEX CONCURRENTLY trades_symbol_time_idx
ON trades (symbol, executed_at DESC)
WHERE executed_at > NOW() - INTERVAL '30 days';

-- Partition historical data
CREATE TABLE trades_archive (
    LIKE trades INCLUDING ALL
) PARTITION BY RANGE (executed_at);

CREATE TABLE trades_2024_q1 PARTITION OF trades_archive
FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');
```

#### Redis Cluster Configuration
```yaml
# redis-cluster.yaml
apiVersion: redis.redis.opstreelabs.in/v1beta1
kind: RedisCluster
metadata:
  name: trading-redis-cluster
spec:
  clusterSize: 6
  persistenceEnabled: true
  clusterVersion: v7
  redisExporter:
    enabled: true
  storage:
    volumeClaimTemplate:
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 100Gi
        storageClassName: fast-ssd
  resources:
    requests:
      memory: "8Gi"
      cpu: "2000m"
    limits:
      memory: "16Gi"
      cpu: "4000m"
```

### 3. Kafka Scaling for Data Streaming

#### Kafka Cluster Configuration
```yaml
# kafka-cluster.yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: trading-kafka
spec:
  kafka:
    version: 3.6.0
    replicas: 6
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
      - name: tls
        port: 9093
        type: internal
        tls: true
    config:
      offsets.topic.replication.factor: 3
      transaction.state.log.replication.factor: 3
      transaction.state.log.min.isr: 2
      default.replication.factor: 3
      min.insync.replicas: 2
      inter.broker.protocol.version: "3.6"
      # Performance optimizations
      num.network.threads: 8
      num.io.threads: 16
      socket.send.buffer.bytes: 102400
      socket.receive.buffer.bytes: 102400
      socket.request.max.bytes: 104857600
      num.partitions: 12
      num.recovery.threads.per.data.dir: 2
      log.retention.hours: 168
      log.segment.bytes: 1073741824
      log.retention.check.interval.ms: 300000
      log.cleanup.policy: delete
    storage:
      type: jbod
      volumes:
      - id: 0
        type: persistent-claim
        size: 500Gi
        storageClass: fast-ssd
        deleteClaim: false
    resources:
      requests:
        memory: 8Gi
        cpu: 2000m
      limits:
        memory: 16Gi
        cpu: 4000m
  zookeeper:
    replicas: 3
    storage:
      type: persistent-claim
      size: 10Gi
      storageClass: fast-ssd
    resources:
      requests:
        memory: 2Gi
        cpu: 500m
      limits:
        memory: 4Gi
        cpu: 1000m
  entityOperator:
    topicOperator: {}
    userOperator: {}
```

## Vertical Scaling Optimizations

### 1. CPU Optimization

#### CPU Affinity and NUMA Optimization
```yaml
# high-performance-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: execution-service-hft
spec:
  replicas: 2
  selector:
    matchLabels:
      app: execution-service-hft
  template:
    metadata:
      labels:
        app: execution-service-hft
    spec:
      nodeSelector:
        node-type: high-cpu
      containers:
      - name: execution-service
        image: trading/execution-service:latest
        resources:
          requests:
            memory: "4Gi"
            cpu: "2000m"
          limits:
            memory: "8Gi"
            cpu: "4000m"
        env:
        - name: GOMAXPROCS
          value: "4"
        - name: CPU_AFFINITY
          value: "0-3"
        securityContext:
          capabilities:
            add:
            - SYS_NICE  # For process priority
        volumeMounts:
        - name: hugepages
          mountPath: /dev/hugepages
      volumes:
      - name: hugepages
        emptyDir:
          medium: HugePages-2Mi
      tolerations:
      - key: "high-performance"
        operator: "Equal"
        value: "true"
        effect: "NoSchedule"
```

#### Go Service CPU Optimization
```go
// High-performance Go service configuration
package main

import (
    "runtime"
    "runtime/debug"
    "syscall"
    "unsafe"
)

func optimizeForPerformance() {
    // Set GC target percentage lower for consistent latency
    debug.SetGCPercent(20)

    // Set max threads to optimize for CPU cores
    runtime.GOMAXPROCS(runtime.NumCPU())

    // Disable GC for critical sections
    runtime.GC()
    debug.SetGCPercent(-1) // Disable GC temporarily

    // Memory allocation optimizations
    debug.SetMemoryLimit(8 << 30) // 8GB memory limit

    // CPU affinity (Linux specific)
    setCPUAffinity()
}

func setCPUAffinity() {
    // Bind to specific CPU cores for consistent performance
    var cpuSet uintptr = 0x0F // Bind to cores 0-3
    _, _, errno := syscall.Syscall(
        syscall.SYS_SCHED_SETAFFINITY,
        uintptr(0), // Current process
        unsafe.Sizeof(cpuSet),
        uintptr(unsafe.Pointer(&cpuSet)),
    )
    if errno != 0 {
        log.Printf("Failed to set CPU affinity: %v", errno)
    }
}
```

### 2. Memory Optimization

#### Memory Pool Implementation
```go
// memory_pool.go - Custom memory pool for high-frequency allocations
package pools

import (
    "sync"
)

type ObjectPool struct {
    pool sync.Pool
    new  func() interface{}
}

func NewObjectPool(newFunc func() interface{}) *ObjectPool {
    return &ObjectPool{
        pool: sync.Pool{
            New: newFunc,
        },
        new: newFunc,
    }
}

func (p *ObjectPool) Get() interface{} {
    return p.pool.Get()
}

func (p *ObjectPool) Put(obj interface{}) {
    p.pool.Put(obj)
}

// Specific pools for trading objects
var (
    MarketDataPool = NewObjectPool(func() interface{} {
        return &MarketData{}
    })

    OrderPool = NewObjectPool(func() interface{} {
        return &Order{}
    })

    PredictionPool = NewObjectPool(func() interface{} {
        return &Prediction{}
    })
)

// Usage example in high-frequency code
func ProcessMarketData(rawData []byte) {
    // Get object from pool instead of allocating
    md := MarketDataPool.Get().(*MarketData)
    defer MarketDataPool.Put(md)

    // Reset object state
    md.Reset()

    // Process data
    if err := md.UnmarshalBinary(rawData); err != nil {
        return
    }

    // Use the market data...
}
```

#### Python Memory Optimization
```python
# memory_optimized_predictor.py
import numpy as np
from numba import jit, njit
import psutil
import gc
from concurrent.futures import ThreadPoolExecutor
import threading

class MemoryOptimizedPredictor:
    def __init__(self, max_memory_gb=8):
        self.max_memory_bytes = max_memory_gb * 1024 * 1024 * 1024
        self.feature_buffer = None
        self.prediction_buffer = None
        self.thread_local = threading.local()

        # Pre-allocate buffers
        self._allocate_buffers()

        # Set up memory monitoring
        self._setup_memory_monitoring()

    def _allocate_buffers(self):
        """Pre-allocate buffers to avoid runtime allocation"""
        # Feature buffer for batch predictions
        self.feature_buffer = np.zeros((10000, 100), dtype=np.float32)

        # Prediction buffer
        self.prediction_buffer = np.zeros(10000, dtype=np.float32)

        # Thread-local buffers for concurrent processing
        self.thread_local.temp_buffer = np.zeros(100, dtype=np.float32)

    @njit(cache=True)  # Numba JIT compilation for speed
    def _compute_features_numba(self, prices, volumes, output):
        """Numba-optimized feature computation"""
        n = len(prices)
        for i in range(20, n):
            # Moving averages
            output[i, 0] = np.mean(prices[i-20:i])
            output[i, 1] = np.mean(prices[i-5:i])

            # Volatility
            output[i, 2] = np.std(prices[i-20:i])

            # Volume features
            output[i, 3] = np.mean(volumes[i-20:i])
            output[i, 4] = volumes[i] / output[i, 3] if output[i, 3] > 0 else 0

    def predict_batch(self, market_data_batch):
        """Memory-efficient batch prediction"""
        batch_size = len(market_data_batch)

        # Check memory usage
        if self._check_memory_usage():
            gc.collect()  # Force garbage collection if needed

        # Use pre-allocated buffer
        if batch_size <= self.feature_buffer.shape[0]:
            features = self.feature_buffer[:batch_size]
            predictions = self.prediction_buffer[:batch_size]
        else:
            # Fallback to new allocation for large batches
            features = np.zeros((batch_size, 100), dtype=np.float32)
            predictions = np.zeros(batch_size, dtype=np.float32)

        # Extract features using Numba
        for i, data in enumerate(market_data_batch):
            self._compute_features_numba(
                data['prices'],
                data['volumes'],
                features[i:i+1]
            )

        # Model inference
        predictions = self.model.predict(features)

        return predictions

    def _check_memory_usage(self):
        """Check if memory usage exceeds threshold"""
        process = psutil.Process()
        memory_usage = process.memory_info().rss
        return memory_usage > self.max_memory_bytes * 0.8
```

### 3. Network Optimization

#### gRPC Connection Optimization
```go
// grpc_client_optimized.go
package client

import (
    "context"
    "crypto/tls"
    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials"
    "google.golang.org/grpc/keepalive"
    "time"
)

func NewOptimizedGRPCClient(address string) (*grpc.ClientConn, error) {
    // Keep-alive parameters for long-lived connections
    kacp := keepalive.ClientParameters{
        Time:                10 * time.Second, // Send pings every 10 seconds
        Timeout:             time.Second,      // Wait 1 second for ping ack
        PermitWithoutStream: true,             // Send pings even without active streams
    }

    // Connection options for high performance
    opts := []grpc.DialOption{
        grpc.WithKeepaliveParams(kacp),
        grpc.WithDefaultCallOptions(
            grpc.MaxCallRecvMsgSize(4*1024*1024), // 4MB max message size
            grpc.MaxCallSendMsgSize(4*1024*1024),
        ),
        grpc.WithInitialWindowSize(1024*1024),     // 1MB initial window
        grpc.WithInitialConnWindowSize(1024*1024), // 1MB connection window
        grpc.WithWriteBufferSize(32*1024),         // 32KB write buffer
        grpc.WithReadBufferSize(32*1024),          // 32KB read buffer
    }

    // TLS optimization for production
    if useTLS {
        config := &tls.Config{
            ServerName:         "trading.example.com",
            InsecureSkipVerify: false,
            // Optimize TLS handshake
            NextProtos:   []string{"h2"},
            MinVersion:   tls.VersionTLS12,
            CipherSuites: []uint16{
                tls.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
                tls.TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305,
            },
        }
        opts = append(opts, grpc.WithTransportCredentials(credentials.NewTLS(config)))
    } else {
        opts = append(opts, grpc.WithInsecure())
    }

    return grpc.Dial(address, opts...)
}

// Connection pooling for multiple connections
type GRPCConnectionPool struct {
    connections []*grpc.ClientConn
    current     int64
    size        int
}

func NewGRPCConnectionPool(address string, size int) (*GRPCConnectionPool, error) {
    pool := &GRPCConnectionPool{
        connections: make([]*grpc.ClientConn, size),
        size:        size,
    }

    for i := 0; i < size; i++ {
        conn, err := NewOptimizedGRPCClient(address)
        if err != nil {
            return nil, err
        }
        pool.connections[i] = conn
    }

    return pool, nil
}

func (p *GRPCConnectionPool) GetConnection() *grpc.ClientConn {
    // Round-robin selection
    idx := atomic.AddInt64(&p.current, 1) % int64(p.size)
    return p.connections[idx]
}
```

## Database Performance Optimization

### 1. InfluxDB Performance Tuning

#### Retention Policies and Continuous Queries
```sql
-- InfluxDB retention and downsampling strategy
CREATE RETENTION POLICY "one_minute" ON "trading_data" DURATION 7d REPLICATION 1 DEFAULT;
CREATE RETENTION POLICY "five_minutes" ON "trading_data" DURATION 30d REPLICATION 1;
CREATE RETENTION POLICY "one_hour" ON "trading_data" DURATION 365d REPLICATION 1;
CREATE RETENTION POLICY "one_day" ON "trading_data" DURATION 2000d REPLICATION 1;

-- Continuous queries for downsampling
CREATE CONTINUOUS QUERY "cq_5min_mean" ON "trading_data"
BEGIN
  SELECT mean("bid"), mean("ask"), mean("volume"), max("high"), min("low")
  INTO "trading_data"."five_minutes"."market_data_5min"
  FROM "trading_data"."one_minute"."market_data"
  GROUP BY time(5m), "symbol"
END;

CREATE CONTINUOUS QUERY "cq_1h_mean" ON "trading_data"
BEGIN
  SELECT mean("bid"), mean("ask"), sum("volume"), max("high"), min("low")
  INTO "trading_data"."one_hour"."market_data_1h"
  FROM "trading_data"."five_minutes"."market_data_5min"
  GROUP BY time(1h), "symbol"
END;
```

#### Batch Writing Optimization
```go
// influxdb_batch_writer.go
package database

import (
    "context"
    "time"
    influxdb2 "github.com/influxdata/influxdb-client-go/v2"
    "github.com/influxdata/influxdb-client-go/v2/api"
)

type BatchWriter struct {
    client    influxdb2.Client
    writeAPI  api.WriteAPIBlocking
    batchSize int
    flushInt  time.Duration
    buffer    []*influxdb2.Point
    ticker    *time.Ticker
}

func NewBatchWriter(client influxdb2.Client, org, bucket string) *BatchWriter {
    bw := &BatchWriter{
        client:    client,
        writeAPI:  client.WriteAPIBlocking(org, bucket),
        batchSize: 1000,  // Write in batches of 1000 points
        flushInt:  1 * time.Second,  // Flush every second
        buffer:    make([]*influxdb2.Point, 0, 1000),
    }

    // Start flush ticker
    bw.ticker = time.NewTicker(bw.flushInt)
    go bw.flushRoutine()

    return bw
}

func (bw *BatchWriter) WritePoint(point *influxdb2.Point) {
    bw.buffer = append(bw.buffer, point)

    if len(bw.buffer) >= bw.batchSize {
        bw.flush()
    }
}

func (bw *BatchWriter) flush() {
    if len(bw.buffer) == 0 {
        return
    }

    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    err := bw.writeAPI.WritePoints(ctx, bw.buffer...)
    if err != nil {
        log.Printf("Error writing batch to InfluxDB: %v", err)
        return
    }

    // Clear buffer
    bw.buffer = bw.buffer[:0]
}

func (bw *BatchWriter) flushRoutine() {
    for range bw.ticker.C {
        bw.flush()
    }
}
```

### 2. PostgreSQL Performance Optimization

#### Optimized Schema Design
```sql
-- Partitioned tables for high-volume data
CREATE TABLE trades_partitioned (
    id BIGSERIAL,
    symbol VARCHAR(10) NOT NULL,
    side trade_side NOT NULL,
    quantity DECIMAL(18,8) NOT NULL,
    price DECIMAL(18,8) NOT NULL,
    executed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    pnl DECIMAL(18,8),
    strategy_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) PARTITION BY RANGE (executed_at);

-- Create monthly partitions
CREATE TABLE trades_2024_01 PARTITION OF trades_partitioned
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE trades_2024_02 PARTITION OF trades_partitioned
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Optimized indexes
CREATE INDEX CONCURRENTLY trades_symbol_time_idx
ON trades_partitioned (symbol, executed_at DESC)
INCLUDE (price, quantity, pnl);

CREATE INDEX CONCURRENTLY trades_strategy_time_idx
ON trades_partitioned (strategy_id, executed_at DESC)
WHERE strategy_id IS NOT NULL;

-- Materialized views for common queries
CREATE MATERIALIZED VIEW daily_pnl AS
SELECT
    DATE(executed_at) as trade_date,
    symbol,
    strategy_id,
    SUM(pnl) as daily_pnl,
    COUNT(*) as trade_count,
    AVG(price) as avg_price
FROM trades_partitioned
WHERE executed_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(executed_at), symbol, strategy_id;

CREATE UNIQUE INDEX ON daily_pnl (trade_date, symbol, strategy_id);

-- Refresh materialized view automatically
CREATE OR REPLACE FUNCTION refresh_daily_pnl()
RETURNS trigger AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_pnl;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trades_refresh_trigger
    AFTER INSERT OR UPDATE OR DELETE ON trades_partitioned
    FOR EACH STATEMENT
    EXECUTE FUNCTION refresh_daily_pnl();
```

#### Connection Pool Optimization
```go
// postgres_pool.go
package database

import (
    "context"
    "time"
    "github.com/jackc/pgx/v5/pgxpool"
)

func NewOptimizedPostgresPool(databaseURL string) (*pgxpool.Pool, error) {
    config, err := pgxpool.ParseConfig(databaseURL)
    if err != nil {
        return nil, err
    }

    // Connection pool optimization
    config.MaxConns = 100                    // Maximum connections
    config.MinConns = 10                     // Minimum connections
    config.MaxConnLifetime = time.Hour       // Connection lifetime
    config.MaxConnIdleTime = 30 * time.Minute // Idle timeout
    config.HealthCheckPeriod = time.Minute   // Health check interval

    // Connection-level optimizations
    config.ConnConfig.RuntimeParams["application_name"] = "trading-system"
    config.ConnConfig.RuntimeParams["search_path"] = "trading,public"

    // Performance tuning
    config.ConnConfig.RuntimeParams["shared_preload_libraries"] = "pg_stat_statements"
    config.ConnConfig.RuntimeParams["log_statement"] = "none"
    config.ConnConfig.RuntimeParams["log_min_duration_statement"] = "1000" // Log slow queries

    return pgxpool.NewWithConfig(context.Background(), config)
}

// Optimized transaction handling
func ExecuteInTransaction(ctx context.Context, pool *pgxpool.Pool, fn func(tx pgx.Tx) error) error {
    tx, err := pool.BeginTx(ctx, pgx.TxOptions{
        IsoLevel:   pgx.ReadCommitted,
        AccessMode: pgx.ReadWrite,
    })
    if err != nil {
        return err
    }
    defer tx.Rollback(ctx)

    if err := fn(tx); err != nil {
        return err
    }

    return tx.Commit(ctx)
}
```

## Caching Strategy

### 1. Multi-Level Caching Architecture

```python
# multi_level_cache.py
import asyncio
import hashlib
import json
from typing import Any, Optional, Dict
import redis.asyncio as redis
import aiocache
from aiocache import Cache
from aiocache.serializers import JsonSerializer

class MultiLevelCache:
    def __init__(self):
        # L1: In-memory cache (fastest)
        self.l1_cache = Cache(Cache.MEMORY, serializer=JsonSerializer())

        # L2: Redis cache (fast, shared)
        self.l2_cache = redis.Redis(
            host='redis-cluster',
            port=6379,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
            retry_on_timeout=True,
            max_connections=100
        )

        # Cache TTLs
        self.l1_ttl = 30    # 30 seconds
        self.l2_ttl = 300   # 5 minutes

    async def get(self, key: str) -> Optional[Any]:
        """Get value from multi-level cache"""
        # Try L1 cache first
        try:
            value = await self.l1_cache.get(key)
            if value is not None:
                return value
        except Exception as e:
            logging.warning(f"L1 cache error: {e}")

        # Try L2 cache
        try:
            value_str = await self.l2_cache.get(key)
            if value_str:
                value = json.loads(value_str)
                # Populate L1 cache
                await self.l1_cache.set(key, value, ttl=self.l1_ttl)
                return value
        except Exception as e:
            logging.warning(f"L2 cache error: {e}")

        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in multi-level cache"""
        ttl = ttl or self.l2_ttl

        # Set in both caches
        try:
            await asyncio.gather(
                self.l1_cache.set(key, value, ttl=min(ttl, self.l1_ttl)),
                self.l2_cache.setex(key, ttl, json.dumps(value))
            )
        except Exception as e:
            logging.error(f"Cache set error: {e}")

    async def invalidate(self, pattern: str = None) -> None:
        """Invalidate cache entries"""
        if pattern:
            # Pattern-based invalidation
            try:
                keys = await self.l2_cache.keys(pattern)
                if keys:
                    await self.l2_cache.delete(*keys)
            except Exception as e:
                logging.error(f"Cache invalidation error: {e}")

        # Clear L1 cache
        await self.l1_cache.clear()

# Feature cache implementation
class FeatureCache(MultiLevelCache):
    def __init__(self):
        super().__init__()
        self.l1_ttl = 10   # Very short TTL for features
        self.l2_ttl = 60   # 1 minute for L2

    def _make_feature_key(self, symbol: str, timestamp: int, feature_set: str) -> str:
        """Create consistent cache key for features"""
        return f"features:{symbol}:{timestamp}:{feature_set}"

    async def get_features(self, symbol: str, timestamp: int, feature_set: str) -> Optional[Dict]:
        """Get features from cache"""
        key = self._make_feature_key(symbol, timestamp, feature_set)
        return await self.get(key)

    async def set_features(self, symbol: str, timestamp: int, feature_set: str, features: Dict) -> None:
        """Cache computed features"""
        key = self._make_feature_key(symbol, timestamp, feature_set)
        await self.set(key, features)

# Prediction cache with confidence-based TTL
class PredictionCache(MultiLevelCache):
    def __init__(self):
        super().__init__()

    def _calculate_ttl(self, confidence: float) -> int:
        """Calculate TTL based on prediction confidence"""
        # Higher confidence = longer cache time
        base_ttl = 30
        confidence_multiplier = min(confidence * 2, 3.0)
        return int(base_ttl * confidence_multiplier)

    async def cache_prediction(self, model_id: str, feature_hash: str,
                             prediction: Dict, confidence: float) -> None:
        """Cache prediction with confidence-based TTL"""
        key = f"prediction:{model_id}:{feature_hash}"
        ttl = self._calculate_ttl(confidence)

        cached_data = {
            'prediction': prediction,
            'confidence': confidence,
            'cached_at': time.time()
        }

        await self.set(key, cached_data, ttl=ttl)
```

### 2. Cache Warming and Preloading

```python
# cache_warmer.py
import asyncio
from typing import List
import schedule
import time

class CacheWarmer:
    def __init__(self, feature_cache: FeatureCache, prediction_cache: PredictionCache):
        self.feature_cache = feature_cache
        self.prediction_cache = prediction_cache
        self.active_symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']

    async def warm_feature_cache(self):
        """Pre-compute and cache features for active symbols"""
        current_time = int(time.time())

        # Warm cache for last 100 time periods
        for symbol in self.active_symbols:
            for i in range(100):
                timestamp = current_time - (i * 60)  # 1-minute intervals

                # Check if features are already cached
                cached = await self.feature_cache.get_features(
                    symbol, timestamp, 'technical_indicators'
                )

                if cached is None:
                    # Compute and cache features
                    features = await self.compute_features(symbol, timestamp)
                    await self.feature_cache.set_features(
                        symbol, timestamp, 'technical_indicators', features
                    )

    async def warm_prediction_cache(self):
        """Pre-generate predictions for likely feature combinations"""
        # Get recent feature combinations that are frequently requested
        common_features = await self.get_common_feature_combinations()

        for features in common_features:
            feature_hash = self.hash_features(features)

            # Check if prediction is cached
            key = f"prediction:ensemble:{feature_hash}"
            cached = await self.prediction_cache.get(key)

            if cached is None:
                # Generate prediction
                prediction = await self.generate_prediction(features)
                await self.prediction_cache.cache_prediction(
                    'ensemble', feature_hash, prediction, prediction['confidence']
                )

    def start_warming_schedule(self):
        """Start scheduled cache warming"""
        # Warm feature cache every 5 minutes
        schedule.every(5).minutes.do(lambda: asyncio.create_task(self.warm_feature_cache()))

        # Warm prediction cache every 10 minutes
        schedule.every(10).minutes.do(lambda: asyncio.create_task(self.warm_prediction_cache()))

        # Run scheduler
        while True:
            schedule.run_pending()
            time.sleep(1)
```

This comprehensive scalability and performance guide provides the foundation for building a high-performance AI trading system capable of handling demanding trading scenarios while maintaining low latency and high reliability.