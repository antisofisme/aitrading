# Central Hub - Multi-Tenant Updates
## Enhanced Messaging Configuration

**Version:** 2.0
**Status:** ✅ Configuration Updated (Ready for Implementation)
**Date:** 2025-01-11

---

## 📋 Overview

Central Hub telah disesuaikan untuk mendukung arsitektur hybrid NATS+Kafka multi-tenant. Dokumen ini menjelaskan konfigurasi yang sudah diupdate dan API yang perlu ditambahkan.

---

## ✅ Current State (Phase 1)

### What Already Exists:

**Infrastructure Monitoring:**
```yaml
# infrastructure.yaml
✅ NATS health check (port 4222, monitoring 8222)
✅ Kafka health check (port 9092, admin API)
✅ Zookeeper health check (port 2181)
✅ Service dependency mapping
```

**Messaging Configs:**
```
✅ messaging/nats.json - Basic NATS setup
✅ messaging/kafka.json - Basic Kafka setup
✅ messaging/zookeeper.json - Zookeeper config
```

**Status:** Works for single-tenant market data processing

---

## 📦 Updated Configs

### 1. NATS Configuration (Updated)

**File:** `shared/static/messaging/nats.json`

**New Subject Patterns:**

| Domain | Pattern | Example | Purpose |
|--------|---------|---------|---------|
| **Market Data** | `market.{symbol}.tick` | `market.EURUSD.tick` | Live forex quotes |
| | `market.{symbol}.{tf}` | `market.EURUSD.5m` | OHLCV candles |
| | `market.{symbol}.price` | `market.EURUSD.price` | Price request/reply |
| **Signals** | `signals.{strategy}.{symbol}` | `signals.scalping.EURUSD` | AI predictions |
| | `signals.alerts.{type}` | `signals.alerts.breakout` | Market alerts |
| **Indicators** | `indicators.{type}.{symbol}` | `indicators.rsi.EURUSD` | Technical indicators |
| **System** | `system.health.{service}` | `system.health.data-bridge` | Health monitoring |

**Key Features:**
```json
{
  "streams": {
    "market_data_stream": {
      "max_age": 300000,        // 5 minutes (ephemeral)
      "max_msgs": 10000000,     // High throughput
      "storage": "memory"       // In-memory only
    },
    "signals_stream": {
      "max_age": 3600000,       // 1 hour
      "max_msgs": 1000000,
      "storage": "memory"
    }
  },
  "permissions": {
    "live-collector": {
      "publish": ["market.>", "signals.>"],
      "subscribe": []
    },
    "data-bridge": {
      "subscribe": ["market.>", "signals.>"]
    }
  }
}
```

---

### 2. Kafka Configuration (Updated)

**File:** `shared/static/messaging/kafka.json`

**New Topics (User Domain):**

| Topic | Partitions | Retention | Purpose |
|-------|------------|-----------|---------|
| `user.auth` | 3 | 90 days | Login, logout, session |
| `user.settings` | 3 | Infinite (compacted) | Account settings (event sourcing) |
| `user.commands` | 6 | **7 years** | Trading commands (compliance) |
| `user.trades` | 6 | **7 years** | Trade executions (FINRA, MiFID II) |
| `user.mt5_status` | 3 | 30 days | MT5 balance, equity, margin |
| `user.risk_alerts` | 3 | 1 year | Stop-outs, margin calls |
| `user.transactions` | 3 | **10 years** | Deposits, withdrawals (SOX) |
| `user.backtests` | 3 | 90 days | Backtest results |

**Key Features:**
```json
{
  "partitioning_strategy": {
    "description": "Partition by user_id for isolation",
    "key_serializer": "string",
    "example": "hash(user_id) % num_partitions",
    "benefits": [
      "Ordering guarantee per user",
      "Data isolation (never mixed)",
      "Parallel processing",
      "Load balancing"
    ]
  },
  "compliance": {
    "FINRA_4511": {
      "retention": "7 years",
      "topics": ["user.commands", "user.trades"]
    },
    "MiFID_II": {
      "retention": "7 years",
      "topics": ["user.trades", "system.audit"]
    },
    "SOX": {
      "retention": "10 years",
      "topics": ["user.transactions"]
    }
  },
  "consumer_groups": {
    "trading_engine": ["user.commands"],
    "audit_service": ["user.trades", "user.transactions"],
    "websocket_{user_id}": ["user.trades", "user.mt5_status"]
  }
}
```

---

## 🔧 Required Changes

### Change 1: Update Config Loader

**File:** `base/core/config_manager.py`

**Current:**
```python
def get_messaging_config(self, system: str) -> dict:
    """Load messaging config (nats, kafka, zookeeper)"""
    config_file = f"messaging/{system}.json"
    return self._load_config(config_file)
```

**Enhanced Version:**
```python
def get_messaging_config(self, system: str) -> dict:
    """
    Load messaging config (now supports multi-tenant)

    Args:
        system: nats, kafka, zookeeper
    """
    config_file = f"messaging/{system}.json"
    return self._load_config(config_file)

def get_nats_subjects(self, domain: str = None) -> dict:
    """
    Get NATS subject patterns for specific domain

    Args:
        domain: market_data, signals, indicators, system
    Returns:
        Subject patterns dict
    """
    config = self.get_messaging_config("nats")
    subjects = config.get("subjects", {})

    if domain:
        return subjects.get(domain, {})
    return subjects

def get_kafka_topics(self, domain: str = None) -> dict:
    """
    Get Kafka topics for specific domain

    Args:
        domain: user_domain, system_domain
    Returns:
        Topic configurations dict
    """
    config = self.get_messaging_config("kafka")
    topics = config.get("topics", {})

    if domain:
        return topics.get(domain, {})
    return topics
```

---

### Change 2: Add Multi-Tenant Database Routing

**File:** `shared/components/data_manager/router.py`

**New Feature: User-Specific Database Routing**

```python
class DataRouter:
    """
    Smart data routing for multi-database architecture
    Routes operations to optimal database based on use case

    Phase 1: Market data (TimescaleDB + ClickHouse)
    Phase 2: Multi-tenant (add user-specific routing)
    """

    # Existing methods...

    # NEW for Phase 2:
    async def save_user_event(self, user_id: str, event_type: str, event_data: dict):
        """
        Save user-specific event (Phase 2)
        Routes to user-specific partition in database

        Args:
            user_id: User identifier
            event_type: Event type (login, trade, settings, etc.)
            event_data: Event payload
        """
        await self._ensure_initialized()

        try:
            # Route to user-specific table/partition
            conn = await self.pool_manager.get_timescale_connection()

            try:
                # Insert with user_id for partitioning
                await conn.execute("""
                    INSERT INTO user_events (
                        user_id, event_type, event_data, timestamp
                    ) VALUES ($1, $2, $3, NOW())
                """, user_id, event_type, json.dumps(event_data))

            finally:
                await self.pool_manager.release_timescale_connection(conn)

        except Exception as e:
            raise QueryExecutionError("timescale", "INSERT user_event", str(e))

    async def get_user_data(self, user_id: str, data_type: str, limit: int = 100):
        """
        Get user-specific data (Phase 2)
        Ensures data isolation per user

        Args:
            user_id: User identifier
            data_type: Data type (trades, settings, alerts, etc.)
            limit: Max records to return
        """
        await self._ensure_initialized()

        # Security: Enforce user_id filter (data isolation)
        conn = await self.pool_manager.get_timescale_connection()

        try:
            rows = await conn.fetch(f"""
                SELECT * FROM user_{data_type}
                WHERE user_id = $1
                ORDER BY timestamp DESC
                LIMIT $2
            """, user_id, limit)

            return [dict(row) for row in rows]

        finally:
            await self.pool_manager.release_timescale_connection(conn)
```

---

### Change 3: Update Service Discovery API

**File:** `base/api/routes/config.py`

**New Endpoints for Phase 2:**

```python
@router.get("/messaging/nats/subjects")
async def get_nats_subjects(domain: str = None):
    """
    Get NATS subject patterns

    Query params:
        domain: market_data, signals, indicators, system (optional)

    Returns:
        Subject patterns for specified domain or all domains
    """
    config_manager = get_config_manager()
    subjects = config_manager.get_nats_subjects(domain)

    return {
        "status": "success",
        "domain": domain or "all",
        "subjects": subjects
    }

@router.get("/messaging/kafka/topics")
async def get_kafka_topics(domain: str = None):
    """
    Get Kafka topic configurations

    Query params:
        domain: user_domain, system_domain (optional)

    Returns:
        Topic configs for specified domain or all domains
    """
    config_manager = get_config_manager()
    topics = config_manager.get_kafka_topics(domain)

    return {
        "status": "success",
        "domain": domain or "all",
        "topics": topics
    }

@router.get("/messaging/kafka/consumer-groups")
async def get_kafka_consumer_groups():
    """
    Get pre-defined Kafka consumer group configurations

    Returns:
        Consumer group configs for all services
    """
    config_manager = get_config_manager()
    config = config_manager.get_messaging_config("kafka")

    return {
        "status": "success",
        "consumer_groups": config.get("consumer_groups", {})
    }
```

---

### Change 4: Add Multi-Tenant Health Checks

**File:** `base/api/routes/health.py`

**Enhanced Health Check for Kafka Topics:**

```python
@router.get("/health/kafka/topics")
async def health_check_kafka_topics():
    """
    Check Kafka topic health (Phase 2)
    Verifies all required topics exist with correct config
    """
    from kafka.admin import KafkaAdminClient, NewTopic

    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=["suho-kafka:9092"],
            request_timeout_ms=10000
        )

        # Get expected topics from config
        config_manager = get_config_manager()
        kafka_config = config_manager.get_messaging_config("kafka")
        expected_topics = kafka_config.get("topics", {})

        # List existing topics
        existing_topics = admin_client.list_topics()

        # Check each expected topic
        results = {}
        for domain, topics in expected_topics.items():
            for topic_name, topic_config in topics.items():
                topic = topic_config.get("name")
                exists = topic in existing_topics

                results[topic] = {
                    "exists": exists,
                    "domain": domain,
                    "expected_partitions": topic_config.get("partitions"),
                    "expected_retention": topic_config.get("retention_ms"),
                    "status": "healthy" if exists else "missing"
                }

        all_healthy = all(r["status"] == "healthy" for r in results.values())

        return {
            "status": "healthy" if all_healthy else "degraded",
            "topics": results,
            "total": len(results),
            "healthy": sum(1 for r in results.values() if r["status"] == "healthy"),
            "missing": sum(1 for r in results.values() if r["status"] == "missing")
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
```

---

## 📊 Implementation Strategy

### Using Updated Configs

**Step 1: Config Files (✅ Complete)**

```bash
✅ messaging/nats.json - Updated with multi-tenant patterns
✅ messaging/kafka.json - Updated with user domain topics
```

**Step 2: Central Hub API Updates (Pending)**

```python
# Add new methods to config_manager.py
✅ get_nats_subjects(domain)
✅ get_kafka_topics(domain)
```

**Step 3: Service Integration**

Services can query Central Hub for correct config:

```python
# Example: Trading Engine service
import requests

# Get Kafka topics for user domain
response = requests.get(
    "http://central-hub:7000/api/config/messaging/kafka/topics",
    params={"domain": "user_domain"}
)
user_topics = response.json()["topics"]

# Use topics from Central Hub (single source of truth)
kafka_consumer = KafkaConsumer(
    user_topics["commands"]["name"],  # "user.commands"
    bootstrap_servers=["kafka:9092"],
    group_id="trading-engine"
)
```

---

## 🔑 Key Benefits

### 1. Single Source of Truth ✅

**Before (scattered configs):**
```
Service A: hardcoded "trading-orders" topic
Service B: hardcoded "user-trades" topic
Service C: hardcoded "market.data" subject
```

**After (Central Hub):**
```
All services query Central Hub for configs
→ Change once in Central Hub
→ All services automatically updated
```

### 2. Version Management ✅

```
Phase 1 configs: Current production (NATS market data)
Phase 2 configs: Multi-tenant (NATS + Kafka hybrid)

Services can upgrade independently using feature flags
```

### 3. Compliance Built-In ✅

```json
{
  "user.trades": {
    "retention_ms": 220903200000,  // 7 years (FINRA)
    "description": "Trade executions - compliance ready"
  }
}
```

Compliance requirements are config-driven, not hardcoded!

### 4. Easy Service Discovery ✅

New services can discover messaging infrastructure:

```python
# What topics are available?
GET /api/config/messaging/kafka/topics

# What NATS subjects can I subscribe to?
GET /api/config/messaging/nats/subjects?domain=market_data

# Which consumer group should I use?
GET /api/config/messaging/kafka/consumer-groups
```

---

## 📅 Implementation Timeline

| Week | Task | Status |
|------|------|--------|
| **Week 1** | Create Phase 2 config files | ✅ Complete |
| **Week 2** | Update config_manager.py | 📋 Pending |
| **Week 3** | Add new API endpoints | 📋 Pending |
| **Week 4** | Update service discovery | 📋 Pending |
| **Week 5** | Testing & validation | 📋 Pending |
| **Week 6** | Documentation update | 📋 Pending |

**Target:** Q2 2025 (after Phase 1 complete)

---

## 📝 Checklist: Central Hub Phase 2 Readiness

### Configuration Files:
- [x] Update `nats.json` with enhanced subject patterns
- [x] Update `kafka.json` with user domain topics
- [x] Document compliance requirements

### Code Updates:
- [ ] Add `get_nats_subjects()` method to config_manager.py
- [ ] Add `get_kafka_topics()` method to config_manager.py
- [ ] Add `get_user_data()` in DataRouter (when needed)
- [ ] Add `save_user_event()` in DataRouter (when needed)

### API Endpoints:
- [ ] Add `/api/config/messaging/nats/subjects`
- [ ] Add `/api/config/messaging/kafka/topics`
- [ ] Add `/api/config/messaging/kafka/consumer-groups`
- [ ] Add `/api/health/kafka/topics`

### Testing:
- [ ] Test config loading with new structure
- [ ] Test new API endpoints
- [ ] Test health checks for Kafka topics
- [ ] Test multi-tenant isolation

### Documentation:
- [x] Create multi-tenant update guide (this document)
- [x] Update messaging configs
- [ ] Update Central Hub README
- [ ] Update API documentation

---

## 🚀 Next Steps

1. **Complete Phase 1** (current core system) ← Focus here first
2. **Implement API methods** (get_nats_subjects, get_kafka_topics)
3. **Add new endpoints** (when multi-tenant features needed)
4. **Test multi-tenant isolation** (when implementing user services)

---

**Status:** ✅ Configs Updated | 📋 API Implementation Pending
**Dependencies:** Phase 1 core system must be stable first
**Impact:** Foundation ready for multi-tenant architecture

---

*Configs are ready and updated. API implementation can wait until multi-tenant features are actually needed.*
