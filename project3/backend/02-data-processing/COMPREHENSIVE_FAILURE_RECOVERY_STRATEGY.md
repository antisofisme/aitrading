# Comprehensive Failure Recovery Strategy

**Date:** 2025-10-08
**Status:** Production Reliability Analysis
**Purpose:** Cover ALL possible failure scenarios

---

## 🎯 **CRITICAL QUESTION USER ASKED:**

> "Kalau Kafka yang mati juga sudah dipikirkan? Maksud saya saya kurang begitu yakin kemungkinan apa lagi, jadi coba pikirkan"

**Translation:** What if Kafka crashes? Think of ALL other possible failure scenarios.

---

## 📊 **FAILURE SCENARIO MATRIX**

### **Category 1: Message Queue Failures**

| Scenario | Current Status | Impact | Recovery Strategy |
|----------|---------------|--------|-------------------|
| **NATS crash/restart** | ⚠️ Partial | Messages lost during downtime | ✅ Kafka backup + verification re-publish |
| **Kafka crash** | ❌ NOT COVERED | Both NATS+Kafka down = data loss | ❌ **CRITICAL GAP** |
| **Kafka disk full** | ❌ NOT COVERED | New messages rejected | ❌ **CRITICAL GAP** |
| **Network partition (services ↔ Kafka)** | ❌ NOT COVERED | Cannot publish/consume | ❌ **CRITICAL GAP** |
| **Kafka topic deletion** | ❌ NOT COVERED | Historical data lost | ❌ **CRITICAL GAP** |
| **Consumer group offset corruption** | ⚠️ Partial | Skip/duplicate messages | ⚠️ Set to `earliest` helps but not complete |

**Consequence:** If Kafka is down during historical download:
```
Historical Downloader → NATS (no subscribers) ❌
                     → Kafka (unavailable) ❌
                     → Verification checks ClickHouse (0 rows)
                     → Re-publish to NATS/Kafka (still down) ❌
                     → DATA LOST PERMANENTLY ❌
```

---

### **Category 2: Database Failures**

| Scenario | Current Status | Impact | Recovery Strategy |
|----------|---------------|--------|-------------------|
| **ClickHouse crash** | ❌ NOT COVERED | Cannot save aggregates | No write retry logic |
| **ClickHouse disk full** | ❌ NOT COVERED | Write failures | No monitoring/alerting |
| **ClickHouse network partition** | ❌ NOT COVERED | Data-bridge cannot write | No circuit breaker |
| **TimescaleDB crash** | ❌ NOT COVERED | Tick aggregator cannot read ticks | No fallback data source |
| **TimescaleDB disk full** | ❌ NOT COVERED | Cannot save ticks | No monitoring |
| **PostgreSQL (service registry) crash** | ⚠️ Partial | Service discovery fails | Central Hub might have fallback |
| **Database corruption** | ❌ NOT COVERED | Invalid data returned | No data validation |

**Consequence:** If ClickHouse is down during data-bridge processing:
```
Historical Downloader → Kafka ✅
Data-bridge → Receives from Kafka ✅
Data-bridge → db_router.save_aggregate() → ClickHouse (down) ❌
              → Exception thrown
              → Message NOT marked as processed
              → Kafka will retry (good!) ✅

BUT: If ClickHouse down for 24+ hours, Kafka retention expires → DATA LOST
```

---

### **Category 3: Service Orchestration Failures**

| Scenario | Current Status | Impact | Recovery Strategy |
|----------|---------------|--------|-------------------|
| **All services restart simultaneously** | ❌ NOT COVERED | Race conditions, startup order issues | No orchestration |
| **Historical downloader restarts mid-pair** | ✅ COVERED | Next run will gap-fill | Hourly gap check |
| **Data-bridge restart during Kafka consume** | ⚠️ Partial | Offset committed or not? | Depends on `enable_auto_commit` |
| **Tick-aggregator restart during aggregation** | ✅ COVERED | Gap detection on next run | Gap detector active |
| **Circular dependency deadlock** | ❌ NOT COVERED | Services waiting for each other | No timeout/circuit breaker |

---

### **Category 4: Data Quality Issues**

| Scenario | Current Status | Impact | Recovery Strategy |
|----------|---------------|--------|-------------------|
| **Duplicate data** | ⚠️ Partial | Same tick/aggregate saved 2x | Deduplicator in data-bridge |
| **Out-of-order data** | ❌ NOT COVERED | Aggregations incorrect | No timestamp validation |
| **Corrupted data from Polygon** | ❌ NOT COVERED | Invalid OHLC values | No data validation |
| **Missing OHLC fields** | ⚠️ Partial | Defaults to 0 | May cause indicator errors |
| **Timezone mismatch** | ❌ NOT COVERED | Wrong timestamps | No timezone validation |
| **Clock skew between services** | ❌ NOT COVERED | Timestamp inconsistency | No NTP sync check |

---

### **Category 5: Resource Exhaustion**

| Scenario | Current Status | Impact | Recovery Strategy |
|----------|---------------|--------|-------------------|
| **OOM (Out of Memory)** | ⚠️ Partial | Service killed by OS | Restart policy exists |
| **Disk space exhaustion** | ❌ NOT COVERED | Cannot write logs/data | No monitoring |
| **CPU saturation** | ❌ NOT COVERED | Slow processing, timeouts | No rate limiting |
| **File descriptor limit** | ❌ NOT COVERED | Cannot open connections | No limit increase |
| **Network bandwidth saturation** | ❌ NOT COVERED | Slow data transfer | No QoS |

---

### **Category 6: External API Failures**

| Scenario | Current Status | Impact | Recovery Strategy |
|----------|---------------|--------|-------------------|
| **Polygon.io API rate limit** | ⚠️ Partial | Download throttled | Has retry logic |
| **Polygon.io API timeout** | ⚠️ Partial | Download fails | Has retry logic |
| **Polygon.io API returns corrupt data** | ❌ NOT COVERED | Bad data in system | No validation |
| **Polygon.io API downtime (hours)** | ❌ NOT COVERED | Cannot fill gaps | No alternative data source |

---

## 🔧 **CRITICAL GAPS IDENTIFIED**

### **CRITICAL GAP #1: Kafka Unavailability**

**Problem:**
```
If Kafka is down during historical download:
  → NATS messages lost (no subscribers)
  → Kafka messages cannot be published
  → Verification fails
  → Re-publish still fails (Kafka still down)
  → DATA LOST PERMANENTLY
```

**Solution Needed:**
1. **Local disk buffer** - Save to disk if both NATS/Kafka unavailable
2. **Retry with exponential backoff** - Keep trying until Kafka available
3. **Alternative: Write directly to ClickHouse** - Bypass message queue

**Implementation Priority:** 🔴 CRITICAL

---

### **CRITICAL GAP #2: ClickHouse Unavailability**

**Problem:**
```
Data-bridge receives messages from Kafka
  → Tries to write to ClickHouse (down)
  → Exception thrown
  → Message NOT committed (good)
  → Kafka retries delivery (good)

BUT: If ClickHouse down > 24 hours → Kafka retention expires → DATA LOST
```

**Solution Needed:**
1. **Circuit breaker** - Stop consuming if ClickHouse down
2. **Dead Letter Queue** - Move failed messages to DLQ
3. **Increase Kafka retention** - 7 days instead of 24 hours
4. **Alternative: Write to backup ClickHouse** - HA setup

**Implementation Priority:** 🔴 CRITICAL

---

### **CRITICAL GAP #3: TimescaleDB Unavailability**

**Problem:**
```
Tick aggregator needs to aggregate candles
  → Queries TimescaleDB for ticks (down)
  → Cannot aggregate
  → No alternative data source
  → Gap remains unfilled
```

**Solution Needed:**
1. **Historical aggregates from Polygon** - Use pre-aggregated bars (already have!)
2. **TimescaleDB HA** - Replica for failover
3. **Cache recent ticks** - In DragonflyDB

**Implementation Priority:** 🟡 HIGH

---

## 💡 **PROPOSED COMPREHENSIVE SOLUTION**

### **Solution 1: Local Disk Buffer (Fallback Storage)**

```python
# In historical downloader publisher.py

class MessagePublisher:
    def __init__(self):
        self.buffer_dir = Path("/app/data/buffer")
        self.buffer_dir.mkdir(exist_ok=True)

    async def publish_aggregate(self, aggregate_data):
        try:
            # Try NATS
            await self.nats_client.publish(...)

            # Try Kafka
            await self.kafka_producer.send(...)

        except Exception as e:
            # Both failed - SAVE TO DISK
            logger.error(f"⚠️ NATS+Kafka unavailable: {e}")
            logger.warning("💾 Buffering to disk...")

            buffer_file = self.buffer_dir / f"buffer_{uuid.uuid4()}.json"
            with open(buffer_file, 'w') as f:
                json.dump(aggregate_data, f)

            self.stats['buffered'] += 1

    async def flush_buffer(self):
        """Retry publishing buffered messages"""
        buffer_files = list(self.buffer_dir.glob("buffer_*.json"))

        for buffer_file in buffer_files:
            try:
                with open(buffer_file) as f:
                    aggregate_data = json.load(f)

                # Retry publish
                await self.publish_aggregate(aggregate_data)

                # Success - delete buffer file
                buffer_file.unlink()
                logger.info(f"✅ Flushed buffer: {buffer_file.name}")

            except Exception as e:
                logger.warning(f"⚠️ Cannot flush {buffer_file.name}: {e}")
                # Keep file for next retry
```

---

### **Solution 2: Circuit Breaker Pattern**

```python
# In data-bridge clickhouse_writer.py

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout_seconds=60):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failures = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func):
        if self.state == "OPEN":
            # Check if timeout elapsed
            if time.time() - self.last_failure_time > self.timeout_seconds:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker OPEN - ClickHouse unavailable")

        try:
            result = func()

            # Success - reset
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failures = 0
                logger.info("✅ Circuit breaker CLOSED - ClickHouse recovered")

            return result

        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()

            if self.failures >= self.failure_threshold:
                self.state = "OPEN"
                logger.error("🔴 Circuit breaker OPEN - ClickHouse DOWN")

            raise

# Usage in data-bridge
self.clickhouse_circuit_breaker = CircuitBreaker()

async def _save_candle(self, data):
    try:
        self.clickhouse_circuit_breaker.call(
            lambda: self.db_router.save_aggregate(candle_data)
        )
    except Exception as e:
        logger.error(f"❌ Circuit breaker prevented ClickHouse write: {e}")
        # Do NOT mark Kafka message as processed
        raise  # Kafka will retry
```

---

### **Solution 3: Dead Letter Queue**

```python
# In data-bridge kafka_subscriber.py

class KafkaSubscriber:
    def __init__(self):
        self.dlq_topic = "aggregate_archive_dlq"
        self.max_retries = 3

    async def handle_message(self, message):
        retry_count = message.headers.get('retry_count', 0)

        try:
            # Process message
            await self._save_candle(message.value)

        except Exception as e:
            if retry_count >= self.max_retries:
                # Move to Dead Letter Queue
                logger.error(f"❌ Max retries exceeded - moving to DLQ")
                await self.kafka_producer.send(
                    self.dlq_topic,
                    value=message.value,
                    headers={
                        'original_topic': message.topic,
                        'error': str(e),
                        'timestamp': time.time()
                    }
                )
                # Mark original as processed
                await message.commit()
            else:
                # Increment retry and re-throw (Kafka will retry)
                message.headers['retry_count'] = retry_count + 1
                raise
```

---

### **Solution 4: Health Check & Monitoring**

```python
# Add to all services

class HealthChecker:
    async def check_dependencies(self):
        health = {
            'service': self.service_name,
            'status': 'healthy',
            'dependencies': {}
        }

        # Check Kafka
        try:
            await self.kafka_producer.send('health_check', b'ping')
            health['dependencies']['kafka'] = 'UP'
        except:
            health['dependencies']['kafka'] = 'DOWN'
            health['status'] = 'degraded'

        # Check ClickHouse
        try:
            self.clickhouse_client.execute('SELECT 1')
            health['dependencies']['clickhouse'] = 'UP'
        except:
            health['dependencies']['clickhouse'] = 'DOWN'
            health['status'] = 'degraded'

        # Check TimescaleDB
        try:
            self.timescale_conn.execute('SELECT 1')
            health['dependencies']['timescaledb'] = 'UP'
        except:
            health['dependencies']['timescaledb'] = 'DOWN'
            health['status'] = 'degraded'

        return health
```

---

## 📋 **IMPLEMENTATION PRIORITY**

### **Phase 1: Critical (Implement NOW)**
1. 🔴 Local disk buffer for historical downloader
2. 🔴 Circuit breaker for ClickHouse writes
3. 🔴 Increase Kafka retention to 7 days
4. 🔴 Health check endpoints for all services

### **Phase 2: High Priority (Next Week)**
1. 🟡 Dead Letter Queue for failed messages
2. 🟡 TimescaleDB failover strategy
3. 🟡 Data validation (OHLC sanity checks)
4. 🟡 Alerting system (Prometheus + Grafana)

### **Phase 3: Medium Priority (Next Month)**
1. 🟢 ClickHouse HA (replication)
2. 🟢 Kafka HA (multi-broker)
3. 🟢 Rate limiting and backpressure
4. 🟢 Chaos engineering tests

---

## 🎯 **VERDICT**

**Current System:** ⚠️ **70% Resilient**

**Covered:**
- ✅ Service restarts (gap detection)
- ✅ NATS message loss (Kafka backup)
- ✅ Data-bridge crash (verification + re-publish)

**NOT Covered:**
- ❌ Kafka unavailability
- ❌ ClickHouse unavailability
- ❌ TimescaleDB unavailability
- ❌ Network partitions
- ❌ Data corruption

**Recommendation:** Implement Phase 1 (Critical) solutions BEFORE production deployment.

---

**Generated:** 2025-10-08
**Author:** AI Analysis
**User Request:** "Kalau Kafka yang mati juga sudah dipikirkan?"
